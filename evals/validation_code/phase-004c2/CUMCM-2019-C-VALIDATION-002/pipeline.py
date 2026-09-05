"""Independent airport-taxi scenario analysis, authored before the first execution.

All parameters are declared assumptions. No airport observations are available.
Run only through the frozen Skill execute/capture/seal chain after remote pre-run freeze.
"""

from __future__ import annotations

import argparse
import base64
import bisect
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

from independent_checks import check_lane_schedule, check_priority_ledger, check_queue_inverse

CANDIDATES = ("BASELINE_STATIC_FCFS", "PRIMARY_NHPP_CREDIT", "CONTROL_FLUID_AGING")
REQUIREMENTS = ("REQ-Q1", "REQ-Q2", "REQ-Q3", "REQ-Q4")
SCOPES = {
    "REQ-Q1": (
        "假设航班出客过程和收益参数下，比较候客与空返的期望增量"
        "净收益并给出条件决策；未验证真实机场适用性。"
    ),
    "REQ-Q2": (
        "官方输入不含机场及城市实测数据，实际机场方案与实证合理"
        "性检验证据不足；仅提供明确标记的假设情景依赖性分析。"
    ),
    "REQ-Q3": (
        "在明确假设的双车道几何、饱和队列和行人车辆互锁条件下比"
        "较批次上车点配置并复算约束；最优性仅限预注册有限方案集"
        "。"
    ),
    "REQ-Q4": (
        "在假设循环车队和外生目的地序列下评价短途一次性补偿优先"
        "、普通队列配额与老化保护的可行性及收益率分布；不保证真"
        "实收益均衡改善。"
    ),
}
GLOBAL_SCOPE = (
    "四问的假设情景建模与可复算局部证据；REQ-Q2机场和城市实"
    "测数据缺失，不能据此主张全部主问题完成或实际部署有效。"
)
EVIDENCE = {
    "REQ-Q1": ["models/model_candidates.json", "models/assumptions_and_symbols.json"],
    "REQ-Q2": ["data/data_audit.json", "research/source_ledger.json"],
    "REQ-Q3": ["models/model_candidates.json", "models/assumptions_and_symbols.json"],
    "REQ-Q4": ["models/model_candidates.json", "models/assumptions_and_symbols.json"],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean_interval(values):
    average = statistics.fmean(values)
    standard_error = statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {
        "mean": average,
        "standard_error": standard_error,
        "normal_approx_95_interval": [
            average - 1.96 * standard_error,
            average + 1.96 * standard_error,
        ],
        "replicates": len(values),
        "scope": "MONTE_CARLO_ERROR_CONDITIONAL_ON_ASSUMPTIONS",
    }


def quantile(values, probability):
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (position - low) * (ordered[high] - ordered[low])


def stratified_interval(strata):
    average = statistics.fmean(statistics.fmean(values) for values in strata)
    variance = (
        sum(statistics.variance(values) / len(values) for values in strata) / len(strata) ** 2
    )
    standard_error = math.sqrt(variance)
    return {
        "mean": average,
        "standard_error": standard_error,
        "normal_approx_95_interval": [
            average - 1.96 * standard_error,
            average + 1.96 * standard_error,
        ],
        "fixed_state_strata": len(strata),
        "scope": "STRATIFIED_MONTE_CARLO_ERROR_CONDITIONAL_ON_ASSUMPTIONS",
    }


def gini(values):
    ordered = sorted(values)
    total = sum(ordered)
    if total <= 0:
        raise ValueError("NONPOSITIVE_INCOME_GINI_UNDEFINED")
    count = len(ordered)
    return sum((2 * index - count - 1) * value for index, value in enumerate(ordered, 1)) / (
        count * total
    )


def cumulative_intensity(parameters, demand_scale=1.0, delay_min=0):
    rates = []
    for minute in range(parameters["intensity_horizon_min"]):
        rate = parameters["background_groups_per_min"]
        for flight in parameters["assumed_flight_cohorts"]:
            center = flight["exit_center_min"] + delay_min
            width = flight["half_width_min"]
            pulse = max(0.0, 1.0 - abs(minute + 0.5 - center) / width)
            rate += flight["taxi_groups"] * pulse / width
        rates.append(rate * demand_scale)
    cumulative = [0.0]
    for rate in rates:
        cumulative.append(cumulative[-1] + rate)
    return rates, cumulative


def inverse_intensity(cumulative, target):
    if target >= cumulative[-1]:
        return len(cumulative) - 1 + (target - cumulative[-1]) / (cumulative[-1] - cumulative[-2])
    index = max(0, bisect.bisect_right(cumulative, target) - 1)
    return index + (target - cumulative[index]) / (cumulative[index + 1] - cumulative[index])


def draw_distance(rng, parameters):
    return rng.choices(
        parameters["distances_km"], weights=parameters["distance_probabilities"], k=1
    )[0]


def decision_analysis(
    candidate,
    seed,
    parameters,
    demand_scale=1.0,
    delay_min=0,
    cost_scale=1.0,
    evaluation_seed_offset=0,
):
    rates, cumulative = cumulative_intensity(parameters, demand_scale, delay_min)
    unit_cost = parameters["cost_per_km_cny"] * cost_scale
    opportunity = parameters["city_net_cny_per_hour"] / 60
    mean_distance = sum(
        d * p
        for d, p in zip(
            parameters["distances_km"], parameters["distance_probabilities"], strict=True
        )
    )
    mean_margin = (
        parameters["fare_intercept_cny"]
        + (parameters["fare_per_km_cny"] - unit_cost) * mean_distance
    )
    trip_min = mean_distance / parameters["speed_km_per_min"] + parameters["boarding_min"]
    empty_min = parameters["empty_return_km"] / parameters["speed_km_per_min"]
    empty_cost = parameters["empty_return_km"] * unit_cost
    threshold = (mean_margin + empty_cost) / opportunity + empty_min - trip_min
    rows, episode_losses, loss_strata, advantage_strata = [], [], [], []
    all_times, all_targets = [], []
    for state_index, state in enumerate(parameters["decision_states"]):
        start, queue = state["minute"], state["taxis_ahead"]
        shape = queue + 1
        rng_train = random.Random(seed * 1000003 + state_index * 41 + 11)
        train_targets = [
            cumulative[start] + rng_train.gammavariate(shape, 1.0)
            for _ in range(parameters["training_repeats"])
        ]
        train_times = [inverse_intensity(cumulative, target) for target in train_targets]
        if candidate == CANDIDATES[0]:
            average_rate = statistics.fmean(rates[: parameters["static_averaging_window_min"]])
            estimated_wait = shape / average_rate
        elif candidate == CANDIDATES[1]:
            estimated_wait = statistics.fmean(time - start for time in train_times)
        else:
            estimated_wait = inverse_intensity(cumulative, cumulative[start] + shape) - start
        choose_wait = estimated_wait <= threshold
        rng_eval = random.Random(seed * 1000033 + state_index * 73 + 23 + evaluation_seed_offset)
        waits, advantages, losses = [], [], []
        for _ in range(parameters["validation_repeats"]):
            target = cumulative[start] + rng_eval.gammavariate(shape, 1.0)
            time = inverse_intensity(cumulative, target)
            wait = time - start
            distance = draw_distance(rng_eval, parameters)
            margin = (
                parameters["fare_intercept_cny"]
                + (parameters["fare_per_km_cny"] - unit_cost) * distance
            )
            loaded_min = distance / parameters["speed_km_per_min"] + parameters["boarding_min"]
            advantage = margin + empty_cost + opportunity * (empty_min - loaded_min - wait)
            loss = max(advantage, 0.0) - (advantage if choose_wait else 0.0)
            waits.append(wait)
            advantages.append(advantage)
            losses.append(loss)
            episode_losses.append(loss)
            all_times.append(time)
            all_targets.append(target)
        loss_strata.append(losses)
        advantage_strata.append(advantages if choose_wait else [0.0] * len(advantages))
        rows.append(
            {
                "state_id": state["id"],
                "minute": start,
                "taxis_ahead": queue,
                "estimated_wait_min": estimated_wait,
                "wait_threshold_min": threshold,
                "strategy": "A_QUEUE" if choose_wait else "B_EMPTY_RETURN",
                "evaluation_wait_min": mean_interval(waits),
                "evaluation_advantage_wait_over_return_cny": mean_interval(advantages),
                "opportunity_loss_cny": statistics.fmean(losses),
                "probability_wait_advantage_negative": sum(value < 0 for value in advantages)
                / len(advantages),
            }
        )
    check = check_queue_inverse(cumulative, all_times, all_targets)
    if check["status"] != "PASS":
        raise ValueError("QUEUE_INDEPENDENT_CHECK_FAILED")
    return {
        "source_type": "REGISTERED_ASSUMPTION_SCENARIO",
        "rows": rows,
        "opportunity_loss_cny": statistics.fmean(episode_losses),
        "selected_advantage_cny": stratified_interval(advantage_strata),
        "episode_loss_uncertainty": stratified_interval(loss_strata),
        "independent_check": check,
        "threshold_wait_min": threshold,
    }


def lane_schedule(seed, bays, batches, parameters, boarding_scale=1.0):
    rng = random.Random(seed)
    sigma = math.sqrt(math.log1p(parameters["boarding_cv"] ** 2))
    mu = math.log(parameters["boarding_mean_s"] * boarding_scale) - 0.5 * sigma * sigma
    clock = 0.0
    events = []
    for batch in range(batches):
        durations = [rng.lognormvariate(mu, sigma) for _ in range(2 * bays)]
        phases = []
        phase_specs = [
            (
                "ADMIT",
                parameters["admit_fixed_s"] + parameters["admit_headway_s"] * bays,
                True,
                False,
            ),
            (
                "TRANSFER",
                parameters["walk_fixed_s"] + parameters["walk_per_bay_s"] * bays,
                False,
                True,
            ),
            ("BOARD", max(durations), False, True),
            ("CLEAR", parameters["clearance_s"], False, True),
            ("RELEASE", parameters["exit_headway_s"] * bays, True, False),
        ]
        for name, duration, motion, pedestrians in phase_specs:
            phases.append(
                {
                    "name": name,
                    "start_s": clock,
                    "end_s": clock + duration,
                    "vehicle_motion": motion,
                    "pedestrians_in_lane": pedestrians,
                }
            )
            clock += duration
        events.append(
            {
                "batch": batch,
                "bays_per_lane": bays,
                "passenger_groups": 2 * bays,
                "boarding_seconds": durations,
                "phases": phases,
            }
        )
    checked = check_lane_schedule(events, bays, parameters)
    if checked["status"] != "PASS":
        raise ValueError("LANE_INDEPENDENT_CHECK_FAILED")
    throughput = checked["recomputed_served_groups"] * 3600 / checked["recomputed_duration_s"]
    return {
        "bays_per_lane": bays,
        "throughput_groups_per_hour": throughput,
        "events": events,
        "independent_check": checked,
    }


def lane_analysis(candidate, seed, parameters, boarding_scale=1.0, evaluation_seed_offset=0):
    feasible = [
        bays
        for bays in parameters["candidate_bays_per_lane"]
        if bays * parameters["bay_pitch_m"] <= parameters["lane_length_m"]
        and 2 * bays <= parameters["maximum_total_bays"]
    ]
    training = [
        lane_schedule(
            seed * 1009 + 31, bays, parameters["training_batches"], parameters, boarding_scale
        )
        for bays in feasible
    ]
    if candidate == CANDIDATES[0]:
        selected = min(feasible)
    elif candidate == CANDIDATES[1]:
        selected = min(
            training, key=lambda row: (-row["throughput_groups_per_hour"], row["bays_per_lane"])
        )["bays_per_lane"]
    else:
        selected = parameters["control_bays_per_lane"]
    validation = lane_schedule(
        seed * 1013 + 37 + evaluation_seed_offset,
        selected,
        parameters["validation_batches"],
        parameters,
        boarding_scale,
    )
    validation["training_comparison"] = [
        {key: row[key] for key in ("bays_per_lane", "throughput_groups_per_hour")}
        for row in training
    ]
    validation["optimization_scope"] = "FINITE_REGISTERED_BATCH_GEOMETRIES_WITH_SATURATED_QUEUES"
    validation["demand_bound_note"] = (
        "When supply or passenger arrivals are lower than capaci"
        "ty, realized throughput cannot exceed min(capacity, dem"
        "and, supply)."
    )
    return validation


def priority_analysis(candidate, seed, parameters, distance_scale=1.0):
    rng = random.Random(seed * 1019 + 43)
    available = [0.0] * parameters["fleet_size"]
    previous = [None] * parameters["fleet_size"]
    credit = [0.0] * parameters["fleet_size"]
    last_priority = -parameters["priority_spacing_dispatches"]
    clock, ledger = 0.0, []
    while clock < parameters["horizon_min"]:
        ready = [driver for driver, time in enumerate(available) if time <= clock + 1e-8]
        if not ready:
            clock = min(available)
            if clock >= parameters["horizon_min"]:
                break
            continue
        ordinary = min(ready, key=lambda driver: (available[driver], driver))
        driver = ordinary
        priority_used = False
        eligible = [
            item
            for item in ready
            if credit[item] > 0 and clock - available[item] <= parameters["credit_expiry_min"]
        ]
        spacing_ok = len(ledger) - last_priority >= parameters["priority_spacing_dispatches"]
        aging_guard = clock - available[ordinary] >= parameters["ordinary_wait_cap_min"]
        if candidate == CANDIDATES[1] and eligible and spacing_ok and not aging_guard:
            selected = min(
                eligible, key=lambda item: (available[item] - credit[item], available[item], item)
            )
            if available[selected] - credit[selected] < available[ordinary]:
                driver = selected
                priority_used = driver != ordinary
        elif candidate == CANDIDATES[2] and eligible and spacing_ok and not aging_guard:
            # Fixed short-trip promotion is structurally different from deficit-sized credits.
            selected = min(eligible, key=lambda item: (available[item], item))
            if clock - available[selected] >= parameters["control_promotion_after_min"]:
                driver = selected
                priority_used = driver != ordinary
        if priority_used:
            last_priority = len(ledger)
        distance = draw_distance(rng, parameters) * distance_scale
        net_income = (
            parameters["fare_intercept_cny"]
            + (parameters["fare_per_km_cny"] - 2 * parameters["cost_per_km_cny"]) * distance
        )
        cycle = 2 * distance / parameters["speed_km_per_min"] + parameters["turnaround_min"]
        row = {
            "sequence": len(ledger),
            "passenger_sequence": len(ledger),
            "driver": driver,
            "dispatch_min": clock,
            "queue_entry_min": available[driver],
            "wait_min": clock - available[driver],
            "distance_km": distance,
            "net_income_cny": net_income,
            "return_min": clock + cycle,
            "priority_used": priority_used,
            "credit_available_min": credit[driver],
            "previous_trip_sequence": previous[driver],
        }
        ledger.append(row)
        previous[driver] = row["sequence"]
        available[driver] = row["return_min"]
        deficit = max(0.0, parameters["target_net_cny_per_hour"] * cycle / 60 - net_income)
        credit[driver] = (
            min(parameters["credit_cap_min"], 60 * deficit / parameters["target_net_cny_per_hour"])
            if distance <= parameters["short_trip_km"]
            else 0.0
        )
        clock += parameters["dispatch_interval_min"]
    checked = check_priority_ledger(ledger, parameters, seed * 1019 + 43, distance_scale)
    if checked["status"] != "PASS":
        raise ValueError("PRIORITY_INDEPENDENT_CHECK_FAILED")
    rates = [
        income * 60 / end
        for income, end in zip(
            checked["driver_incomes_cny"], checked["driver_end_min"], strict=True
        )
    ]
    return {
        "policy": candidate,
        "ledger": ledger,
        "independent_check": checked,
        "driver_net_cny_per_hour": rates,
        "income_rate_gini": gini(rates),
        "bottom_decile_rate_cny_per_hour": quantile(rates, 0.1),
        "mean_rate_cny_per_hour": statistics.fmean(rates),
        "maximum_queue_wait_min": max(row["wait_min"] for row in ledger),
        "throughput_groups_per_hour": len(ledger) * 60 / parameters["horizon_min"],
        "trips_returning_after_horizon": sum(
            row["return_min"] > parameters["horizon_min"] for row in ledger
        ),
        "tail_accounting": (
            "All assigned trip cashflows and full round-trip time ar"
            "e recognized; per-driver exposure ends at max(dispatch "
            "horizon, last return). No new dispatch after horizon."
        ),
    }


def requirement_claims(output_relative):
    return {
        requirement: {
            "claim_id": f"CLAIM-2019C-{requirement[4:]}",
            "claim_text": SCOPES[requirement],
            "evidence_artifact_ids": [*EVIDENCE[requirement], output_relative],
        }
        for requirement in REQUIREMENTS
    }


def contract_probe(output_relative="experiments/selected_output_contract_probe.json"):
    return {
        "candidate_id": CANDIDATES[0],
        "status": "CONTRACT_PROBE",
        "probe_only": True,
        "ranking_eligible": False,
        "result_values_are_placeholders": True,
        "final_metrics": {"opportunity_loss_cny": 0.0},
        "claim_scope": GLOBAL_SCOPE,
        "requirement_claims": requirement_claims(output_relative),
        "figure_ready_data": [{"table_id": "STRUCTURE_ONLY", "value": 0.0}],
        "uncertainty": {"status": "PLACEHOLDER_NO_EXECUTION"},
        "limitations": ["PROBE_ONLY_NO_RUN_NO_SCORE", "REQ-Q2 empirical data missing"],
        "robustness_evidence": {
            "metric": "opportunity_loss_cny",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "STRUCTURE_ONLY",
                    "metric": "opportunity_loss_cny",
                    "result": 0.0,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["PLACEHOLDER_NO_EXECUTION"],
        },
    }


def execute(candidate, seed, assumptions, output_relative):
    q1 = decision_analysis(candidate, seed, assumptions["q1"])
    q3 = lane_analysis(candidate, seed, assumptions["q3"])
    q4 = priority_analysis(candidate, seed, assumptions["q4"])
    if q4["throughput_groups_per_hour"] > q3["throughput_groups_per_hour"]:
        raise ValueError("CROSS_QUESTION_DISPATCH_EXCEEDS_BOARDING_CAPACITY")
    test_offset = assumptions["sealed_test_evaluation_offset"]
    q1_test = decision_analysis(
        candidate, seed, assumptions["q1"], evaluation_seed_offset=test_offset
    )
    q3_test = lane_analysis(candidate, seed, assumptions["q3"], evaluation_seed_offset=test_offset)
    q4_test = priority_analysis(candidate, seed + test_offset, assumptions["q4"])
    test_evidence = {
        "candidate_id": candidate,
        "seed": seed,
        "split": "RESERVED_TEST_SCENARIOS",
        "source_type": "REGISTERED_ASSUMPTIONS_NOT_OBSERVATIONS",
        "policy_refitted_on_test": False,
        "test_metrics": {
            "opportunity_loss_cny": q1_test["opportunity_loss_cny"],
            "lane_throughput_groups_per_hour": q3_test["throughput_groups_per_hour"],
            "income_rate_gini": q4_test["income_rate_gini"],
        },
        "independent_checks": {
            "q1": q1_test["independent_check"],
            "q3": q3_test["independent_check"],
            "q4": q4_test["independent_check"],
        },
    }
    test_bytes = json.dumps(
        test_evidence, ensure_ascii=False, sort_keys=True, allow_nan=False
    ).encode("utf-8")
    perturbations = []
    q1_sensitivity = []
    for variation in assumptions["robustness"]["q1"]:
        result = decision_analysis(candidate, seed, assumptions["q1"], **variation["arguments"])
        perturbations.append(
            {
                "perturbation_id": variation["id"],
                "metric": "opportunity_loss_cny",
                "result": result["opportunity_loss_cny"],
                "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
            }
        )
        q1_sensitivity.append(
            {
                "id": variation["id"],
                "arguments": variation["arguments"],
                "opportunity_loss_cny": result["opportunity_loss_cny"],
                "strategy_changes": sum(
                    left["strategy"] != right["strategy"]
                    for left, right in zip(q1["rows"], result["rows"], strict=True)
                ),
                "independent_check": result["independent_check"],
            }
        )
    q3_sensitivity = []
    for scale in assumptions["robustness"]["boarding_scales"]:
        result = lane_analysis(candidate, seed, assumptions["q3"], scale)
        q3_sensitivity.append(
            {
                "boarding_scale": scale,
                "bays_per_lane": result["bays_per_lane"],
                "throughput_groups_per_hour": result["throughput_groups_per_hour"],
                "independent_check": result["independent_check"],
            }
        )
    q4_sensitivity = []
    for scale in assumptions["robustness"]["distance_scales"]:
        result = priority_analysis(candidate, seed, assumptions["q4"], scale)
        q4_sensitivity.append(
            {
                "distance_scale": scale,
                "income_rate_gini": result["income_rate_gini"],
                "throughput_groups_per_hour": result["throughput_groups_per_hour"],
                "maximum_queue_wait_min": result["maximum_queue_wait_min"],
                "independent_check": result["independent_check"],
            }
        )
    scope_status = {
        "REQ-Q1": "CONDITIONAL_SCENARIO_EVIDENCE",
        "REQ-Q2": "EMPIRICAL_EVIDENCE_INSUFFICIENT",
        "REQ-Q3": "CONDITIONAL_FINITE_DESIGN_EVIDENCE",
        "REQ-Q4": "CONDITIONAL_POLICY_EVIDENCE",
    }
    return {
        "candidate_id": candidate,
        "seed": seed,
        "status": "SUCCESS",
        "execution_scope": "ASSUMPTION_ONLY_SCENARIO_ANALYSIS",
        "source_type": "NO_AIRPORT_OBSERVATIONS",
        "empirical_data_available": False,
        "empirical_requirement_satisfied": False,
        "primary_completion": {
            requirement: requirement != "REQ-Q2" for requirement in REQUIREMENTS
        },
        "primary_completion_scope": "Q1_Q3_Q4_CONDITIONAL_MODEL_DELIVERABLES_ONLY_Q2_UNFULFILLED",
        "hard_evidence_gaps": ["VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING"],
        "primary_requirement_status": scope_status,
        "claim_scope": GLOBAL_SCOPE,
        "requirement_claims": requirement_claims(output_relative),
        "validation_metrics": {"opportunity_loss_cny": q1["opportunity_loss_cny"]},
        "final_metrics": {
            "opportunity_loss_cny": q1["opportunity_loss_cny"],
            "lane_throughput_groups_per_hour": q3["throughput_groups_per_hour"],
            "income_rate_gini": q4["income_rate_gini"],
            "priority_throughput_groups_per_hour": q4["throughput_groups_per_hour"],
        },
        "question_1": q1,
        "question_2": {
            "status": "EMPIRICAL_EVIDENCE_INSUFFICIENT",
            "observations": [],
            "unfulfilled_primary_acceptance": (
                "Collect airport and city taxi observations; calibrate a"
                "nd validate a named-airport policy."
            ),
            "assumption_sensitivity": q1_sensitivity,
        },
        "question_3": q3,
        "question_4": q4,
        "figure_ready_data": [
            {"table_id": "Q1_CONDITIONAL_DECISIONS", "rows": q1["rows"]},
            {"table_id": "Q3_BAY_CAPACITY", "rows": q3["training_comparison"]},
            {"table_id": "Q4_DRIVER_RATES", "values": q4["driver_net_cny_per_hour"]},
        ],
        "uncertainty": {
            "q1": q1["episode_loss_uncertainty"],
            "q3": (
                "Independent frozen outer seeds and boarding-scale pertu"
                "rbations; no field uncertainty calibration."
            ),
            "q4": (
                "Independent frozen outer seeds and distance-scale pertu"
                "rbations; finite horizon and dispatch-tail accounting e"
                "xplicitly reported."
            ),
            "empirical_parameter_uncertainty": "UNIDENTIFIABLE_WITHOUT_OBSERVATIONS",
        },
        "limitations": [
            (
                "REQ-Q2 missing actual airport and city data is non-comp"
                "ensable and prevents all-primary completion."
            ),
            (
                "Flight cohorts, taxi demand, fares, speeds and geometry"
                " are assumptions; no named-airport estimates."
            ),
            (
                "Q1 assumes independent NHPP party arrivals, FCFS taxis "
                "and linear city opportunity cost; feedback and abandonm"
                "ent excluded."
            ),
            (
                "Q3 optimization is finite registered geometry only, sat"
                "urated queues; real pedestrian safety needs surveyed ge"
                "ometry and site approval."
            ),
            (
                "Q4 priorities cannot remove route randomness or guarant"
                "ee income equality; all drivers and passenger destinati"
                "ons are exogenous."
            ),
            (
                "Selection score evaluates Q1 only; it does not certify "
                "a joint Q1-Q4 optimum or external generalization."
            ),
            (
                "Normal-approximation Monte Carlo intervals describe sim"
                "ulation noise conditional on assumptions, not populatio"
                "n confidence."
            ),
        ],
        "robustness_evidence": {
            "metric": "opportunity_loss_cny",
            "metric_direction": "MIN",
            "perturbations": perturbations,
            "failure_cases": [
                "Real-world empirical validation unavailable.",
                (
                    "Non-NHPP correlated demand or queue abandonment can inv"
                    "alidate wait predictions."
                ),
                ("Unsafe site geometry invalidates the abstract dual-lane design."),
                ("Income fairness improvement is not guaranteed by feasible priority."),
            ],
        },
        "additional_robustness": {"q3": q3_sensitivity, "q4": q4_sensitivity},
        "final_metrics_scope": "VALIDATION_SCENARIO_SUMMARY_NOT_TEST_METRICS",
        "sealed_test_metrics_b64": base64.b64encode(test_bytes).decode("ascii"),
        "sealed_test_payload_sha256": hashlib.sha256(test_bytes).hexdigest(),
        "sealed_test_metadata": {
            "encoding": "BASE64_JSON_POLICY_SEAL_NOT_ENCRYPTION",
            "read_policy": (
                "DECODE_SELECTED_MINIMUM_SEED_ONLY_ONCE_AFTER_SELECTION_DECISION_FREEZE"
            ),
        },
        "test_results_generated_by_frozen_code": True,
        "test_results_disclosed_for_selection": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--candidate-id", choices=CANDIDATES, default=CANDIDATES[0])
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--mode", choices=("execute", "contract-probe", "describe"), default="execute"
    )
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else args.case_root / args.output
    output_relative = output.resolve().relative_to(args.case_root.resolve()).as_posix()
    if output.exists():
        raise FileExistsError("REFUSE_OUTPUT_OVERWRITE")
    if args.mode == "describe":
        payload = {
            "mode": "NON_NUMERICAL_INTERFACE_DESCRIPTION",
            "candidates": CANDIDATES,
            "requirements": REQUIREMENTS,
            "empirical_data_available": False,
        }
    elif args.mode == "contract-probe":
        payload = contract_probe(output_relative)
    else:
        path = args.case_root / "experiments/scenario_assumptions.json"
        assumptions = json.loads(path.read_text(encoding="utf-8"))
        if (
            args.seed not in assumptions["outer_seeds"]
            or assumptions["source_type"] != "REGISTERED_ASSUMPTIONS_NOT_OBSERVATIONS"
        ):
            raise ValueError("UNFROZEN_SCENARIO_CONFIGURATION")
        payload = execute(args.candidate_id, args.seed, assumptions, output_relative)
        payload["assumption_input_sha256"] = digest(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "mode": args.mode,
                "candidate_id": args.candidate_id,
                "status": payload.get("status", "DESCRIBED"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
