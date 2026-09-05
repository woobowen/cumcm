"First-party accounting/safety checks; no solver or policy imports."

from __future__ import annotations

import math
import random


def check_lane_schedule(events, bays, parameters):
    violations = []
    previous_end = 0.0
    served = 0
    expected_phases = ["ADMIT", "TRANSFER", "BOARD", "CLEAR", "RELEASE"]
    if 2 * bays > parameters["maximum_total_bays"]:
        violations.append("GEOMETRIC_BAY_LIMIT")
    if bays * parameters["bay_pitch_m"] > parameters["lane_length_m"]:
        violations.append("LANE_LENGTH")
    for index, event in enumerate(events):
        if event["batch"] != index or event["passenger_groups"] != 2 * bays:
            violations.append("BATCH_ACCOUNTING")
        if [phase["name"] for phase in event["phases"]] != expected_phases:
            violations.append("PHASE_SEQUENCE")
        if len(event["boarding_seconds"]) != 2 * bays:
            violations.append("BOARDING_ACCOUNTING")
        if any(value <= 0 or not math.isfinite(value) for value in event["boarding_seconds"]):
            violations.append("INVALID_BOARDING_DURATION")
        for phase in event["phases"]:
            start, end = phase["start_s"], phase["end_s"]
            if start < previous_end - 1e-8 or end <= start:
                violations.append("INVALID_OR_OVERLAPPING_PHASE")
            if phase["vehicle_motion"] and phase["pedestrians_in_lane"]:
                violations.append("PEDESTRIAN_VEHICLE_CONFLICT")
            required_motion = phase["name"] in ("ADMIT", "RELEASE")
            required_pedestrians = phase["name"] in ("TRANSFER", "BOARD", "CLEAR")
            if (
                phase["vehicle_motion"] != required_motion
                or phase["pedestrians_in_lane"] != required_pedestrians
            ):
                violations.append("INTERLOCK_FLAGS")
            if phase["name"] == "BOARD" and end - start < max(event["boarding_seconds"]) - 1e-8:
                violations.append("PREMATURE_RELEASE")
            if phase["name"] == "RELEASE":
                minimum = parameters["exit_headway_s"] * bays
                if end - start < minimum - 1e-8:
                    violations.append("EXIT_HEADWAY")
            previous_end = end
        served += event["passenger_groups"]
    return {
        "status": "PASS" if not violations else "FAIL",
        "violations": sorted(set(violations)),
        "recomputed_served_groups": served,
        "recomputed_duration_s": previous_end,
        "scope": ("ABSTRACT_INTERLOCK_AND_GEOMETRY_ONLY_NO_REAL_SAFETY_CERTIFICATION"),
    }


def check_priority_ledger(ledger, parameters, destination_seed, distance_scale):
    violations = []
    available = {i: 0.0 for i in range(parameters["fleet_size"])}
    last = {i: None for i in available}
    used = set()
    incomes = dict.fromkeys(available, 0.0)
    wait_totals = dict.fromkeys(available, 0.0)
    priority_positions = []
    destination_rng = random.Random(destination_seed)
    for index, row in enumerate(ledger):
        driver = row["driver"]
        if driver not in available or row["sequence"] != index:
            violations.append("DISPATCH_IDENTITY")
            continue
        if row["dispatch_min"] < available[driver] - 1e-8:
            violations.append("BUSY_DRIVER_DISPATCHED")
        ready = [item for item, at in available.items() if at <= row["dispatch_min"] + 1e-8]
        if not ready:
            violations.append("NO_AVAILABLE_DRIVER")
            continue
        oldest = min(ready, key=lambda item: (available[item], item))
        ordinary_wait = row["dispatch_min"] - available[oldest]
        if ordinary_wait >= parameters["ordinary_wait_cap_min"] and driver != oldest:
            violations.append("AGING_GUARD_VIOLATED")
        previous = last[driver]
        expected_credit = 0.0
        if previous is not None and previous["distance_km"] <= parameters["short_trip_km"]:
            previous_cycle = previous["return_min"] - previous["dispatch_min"]
            deficit = max(
                0.0,
                parameters["target_net_cny_per_hour"] * previous_cycle / 60
                - previous["net_income_cny"],
            )
            expected_credit = min(
                parameters["credit_cap_min"],
                60 * deficit / parameters["target_net_cny_per_hour"],
            )
        if abs(row["credit_available_min"] - expected_credit) > 1e-8:
            violations.append("CREDIT_ACCOUNTING")
        if row["priority_used"]:
            priority_positions.append(index)
            if previous is None or previous["distance_km"] > parameters["short_trip_km"]:
                violations.append("INELIGIBLE_PRIORITY")
            elif previous["sequence"] in used:
                violations.append("REUSED_PRIORITY")
            elif row["dispatch_min"] - available[driver] > parameters["credit_expiry_min"]:
                violations.append("EXPIRED_PRIORITY")
            else:
                used.add(previous["sequence"])
        distance = row["distance_km"]
        expected_distance = (
            destination_rng.choices(
                parameters["distances_km"], weights=parameters["distance_probabilities"], k=1
            )[0]
            * distance_scale
        )
        if abs(distance - expected_distance) > 1e-8:
            violations.append("DESTINATION_STREAM_REORDERED_OR_CHANGED")
        expected_income = (
            parameters["fare_intercept_cny"]
            + (parameters["fare_per_km_cny"] - 2 * parameters["cost_per_km_cny"]) * distance
        )
        expected_cycle = (
            2 * distance / parameters["speed_km_per_min"] + parameters["turnaround_min"]
        )
        if abs(row["net_income_cny"] - expected_income) > 1e-8:
            violations.append("INCOME_ACCOUNTING")
        if abs(row["return_min"] - row["dispatch_min"] - expected_cycle) > 1e-8:
            violations.append("RETURN_TIME_ACCOUNTING")
        if row["passenger_sequence"] != index:
            violations.append("PASSENGER_REFUSAL_OR_REORDERING")
        incomes[driver] += expected_income
        wait_totals[driver] += row["dispatch_min"] - available[driver]
        available[driver] = row["return_min"]
        last[driver] = row
    for left, right in zip(priority_positions, priority_positions[1:], strict=False):
        if right - left < parameters["priority_spacing_dispatches"]:
            violations.append("ORDINARY_SERVICE_QUOTA")
    return {
        "status": "PASS" if not violations else "FAIL",
        "violations": sorted(set(violations)),
        "recomputed_total_net_cny": sum(incomes.values()),
        "driver_incomes_cny": [incomes[i] for i in sorted(incomes)],
        "driver_end_min": [max(parameters["horizon_min"], available[i]) for i in sorted(available)],
        "driver_wait_min": [wait_totals[i] for i in sorted(wait_totals)],
        "priority_dispatch_count": len(priority_positions),
        "scope": ("EXOGENOUS_DESTINATIONS_NO_REFUSAL_ONE_USE_CREDIT_AGING_AND_QUOTA"),
    }


def check_queue_inverse(cumulative, transformed_times, integrated_targets):
    maximum_error = 0.0
    for time, target in zip(transformed_times, integrated_targets, strict=True):
        index = min(int(time), len(cumulative) - 2)
        if time >= len(cumulative) - 1:
            value = cumulative[-1] + (time - len(cumulative) + 1) * (
                cumulative[-1] - cumulative[-2]
            )
        else:
            value = cumulative[index] + (time - index) * (cumulative[index + 1] - cumulative[index])
        maximum_error = max(maximum_error, abs(value - target))
    return {
        "status": "PASS" if maximum_error < 1e-8 else "FAIL",
        "maximum_integrated_intensity_residual": maximum_error,
        "checked_samples": len(transformed_times),
    }
