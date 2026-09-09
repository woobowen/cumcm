"""Independent exact arithmetic over exported original inputs; never imports model/checker."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path


def recompute(path):
    packet = json.loads(path.read_text())
    records = packet["records"]
    for record in records.values():
        if hashlib.sha256(record["raw_utf8"].encode()).hexdigest() != record["raw_sha256"]:
            raise ValueError("RAW_RECORD_HASH_MISMATCH")
        if json.loads(record["raw_utf8"]) != record["content"]:
            raise ValueError("RAW_RECORD_CONTENT_MISMATCH")
    raw = records["input"]["content"]
    plan = records["experiment_plan"]["content"]["content"]
    requirements = records["problem_requirements"]["content"]["content"]["requirements"]
    observations = {r["observation_id"]: r for r in raw["observations"]}
    temporal = plan.get("temporal_design", {"samples": []})
    residuals, details = [], []
    for key, item in records.items():
        if not key.startswith("output:"):
            continue
        value = item["content"]
        candidate = value["candidate_id"]
        ends = {}
        for sample in temporal["samples"]:
            rows = [observations[k] for k in sample["feature_observation_ids"]]
            left, right = rows[0], rows[-1]
            t0, t1 = [Fraction(str(r["observed_at"])) for r in (left, right)]
            v0, v1 = [Fraction(str(r["value"])) for r in (left, right)]
            slope = (v1 - v0) / (t1 - t0)
            assert all(
                Fraction(str(r["value"])) == v0 + slope * (Fraction(str(r["observed_at"])) - t0)
                for r in rows
            )
            end = t0 + (Fraction(str(raw["threshold"])) - v0) / slope
            if raw["kind"] == "prediction" and candidate == "BASE":
                end += Fraction(str(raw["baseline_delay"]))
            ends[sample["sample_id"]] = end
        remaining = [
            ends[s["sample_id"]] - Fraction(str(s["origin"]))
            for s in temporal["samples"]
            if s["split"] == "FORECAST"
        ]
        demand = (
            math.ceil(remaining[0] * Fraction(str(raw["flow_litres_per_minute"])))
            if remaining
            else raw["fixed_demand_litres"]
        )
        base_count = math.ceil(demand / 3)
        candidates = [
            (4 * a + 7 * b, a, b)
            for a in range(base_count + 1)
            for b in range((4 * base_count) // 7 + 1)
            if 3 * a + 5 * b >= demand
        ]
        cost, a, b = (4 * base_count, base_count, 0) if candidate == "BASE" else min(candidates)
        quantity = 3 * a + 5 * b
        allocation = value["allocation"]
        for actual, expected in zip(
            allocation["counts"]
            + [allocation["quantity_litres"], allocation["cost"], allocation["demand_litres"]]
            + allocation["balance_litres"],
            [a, b, quantity, cost, demand] + [quantity - t for t in range(demand + 1)],
            strict=True,
        ):
            residuals.append(abs(actual - expected))
        for requirement in requirements:
            metric, definition = next(iter(requirement["metric_contracts"].items()))
            if "prediction_spec" in requirement:
                errors = [
                    abs(
                        ends[s["sample_id"]]
                        - Fraction(str(observations[s["target_observation_id"]]["observed_at"]))
                    )
                    / (
                        Fraction(str(observations[s["target_observation_id"]]["observed_at"]))
                        - Fraction(str(s["origin"]))
                    )
                    * 100
                    for s in temporal["samples"]
                    if s["split"] == "VALIDATION"
                ]
                expected = sum(errors) / len(errors)
                supplied = value["scientific_evidence"][requirement["requirement_id"]][
                    "prediction_evidence"
                ]["predictions"]
                for row, truth in zip(supplied, remaining, strict=True):
                    residuals.append(abs(row["value"] - float(truth)))
            else:
                expected = cost if definition["target"] == "purchase_cost" else quantity - demand
            residuals.append(abs(value["final_metrics"][metric] - float(expected)))
        details.append(
            {
                "run_id": key.removeprefix("output:"),
                "conditional_remaining_min": [float(r) for r in remaining],
                "demand_litres": demand,
                "counts": [a, b],
                "cost_yuan": cost,
            }
        )
    if not residuals or max(residuals) > 1e-6:
        raise ValueError("INDEPENDENT_NUMERIC_MISMATCH")
    return {
        "kind": raw["kind"],
        "max_abs_residual": max(residuals),
        "numeric_values_checked": len(residuals),
        "results": details,
        "scientific_limit": (
            "Exact synthetic affine case only; no observed forecast truth or generalization"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", nargs="+", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            {"producer_imported": False, "results": [recompute(p) for p in args.packets]},
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
