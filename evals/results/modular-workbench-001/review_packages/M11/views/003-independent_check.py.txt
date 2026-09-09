"""Independent rational endpoint arithmetic and finite enumeration; imports no producer."""

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path


def enumerate_plans(demand, containers):
    feasible = []
    # The all-small feasible plan bounds the optimal cost. Positive integer prices
    # bound each count, so this enumeration covers every potentially better plan.
    upper = math.ceil(demand / containers[0]["litres"]) * containers[0]["cost"]
    for small in range(upper // containers[0]["cost"] + 1):
        for large in range(upper // containers[1]["cost"] + 1):
            litres = small * containers[0]["litres"] + large * containers[1]["litres"]
            cost = small * containers[0]["cost"] + large * containers[1]["cost"]
            if litres >= demand:
                feasible.append((cost, [small, large], litres))
    return min(feasible)


def residual(value, *, relation="EQ", tolerance=1e-8):
    return {"value": value, "limit": 0, "relation": relation, "tolerance": tolerance}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads((args.case_root / "data/raw/input.json").read_text())
    path = args.case_root / "runs" / args.run_id / "output.json"
    output = json.loads(path.read_text())
    plan = json.loads((args.case_root / "experiments/experiment_plan.json").read_text())["content"]
    reqs = json.loads((args.case_root / "problem/problem_requirements.json").read_text())[
        "content"
    ]["requirements"]
    temporal = plan.get("temporal_design")
    rows = {r["observation_id"]: r for r in raw.get("observations", [])}
    ends = {}
    for sample in (temporal or {}).get("samples", []):
        prefix = sorted(
            [rows[k] for k in sample["feature_observation_ids"]], key=lambda r: r["observed_at"]
        )
        first, last = prefix[0], prefix[-1]
        slope = (Fraction(str(last["value"])) - Fraction(str(first["value"]))) / (
            last["observed_at"] - first["observed_at"]
        )
        # The independent endpoint algorithm is equivalent only for this declared
        # exact affine input. Verify every intermediate point, not just endpoints.
        assert all(
            abs(
                float(
                    Fraction(str(r["value"]))
                    - Fraction(str(first["value"]))
                    - slope * (r["observed_at"] - first["observed_at"])
                )
            )
            < 1e-10
            for r in prefix
        )
        end = (
            first["observed_at"]
            + (Fraction(str(raw["threshold"])) - Fraction(str(first["value"]))) / slope
        )
        if raw["kind"] == "prediction" and output["candidate_id"] == "BASE":
            end += raw["baseline_delay"]
        ends[sample["sample_id"]] = float(end)
    forecast = [
        ends[s["sample_id"]] - s["origin"]
        for s in (temporal or {}).get("samples", [])
        if s["split"] == "FORECAST"
    ]
    demand = (
        math.ceil(forecast[0] * raw["flow_litres_per_minute"])
        if forecast
        else raw["fixed_demand_litres"]
    )
    optimum, best_counts, _ = enumerate_plans(demand, raw["containers"])
    counts = output["allocation"]["counts"]
    assert len(counts) == 2 and all(type(n) is int and n >= 0 for n in counts)
    quantity = sum(n * c["litres"] for n, c in zip(counts, raw["containers"], strict=True))
    cost = sum(n * c["cost"] for n, c in zip(counts, raw["containers"], strict=True))
    expected_counts = (
        [math.ceil(demand / raw["containers"][0]["litres"]), 0]
        if output["candidate_id"] == "BASE"
        else best_counts
    )
    vector_residual = max(abs(x - y) for x, y in zip(counts, expected_counts, strict=True))
    allocation = output["allocation"]
    vector_residual = max(
        vector_residual,
        abs(allocation["quantity_litres"] - quantity),
        abs(allocation["cost"] - cost),
        abs(allocation["demand_litres"] - demand),
    )
    expected_balance = [quantity - t for t in range(demand + 1)]
    vector_residual = max(
        vector_residual,
        *(abs(x - y) for x, y in zip(expected_balance, allocation["balance_litres"], strict=True)),
    )
    requirements = {}
    for req in reqs:
        metric, definition = next(iter(req["metric_contracts"].items()))
        error = vector_residual
        if "prediction_spec" in req:
            validation = [s for s in temporal["samples"] if s["split"] == "VALIDATION"]
            errors = []
            for sample, supplied in zip(validation, output["metric_samples"][metric], strict=True):
                truth = rows[sample["target_observation_id"]]["observed_at"]
                assert supplied["sample_id"] == sample["sample_id"]
                error = max(
                    error,
                    abs(supplied["predicted_end_time"] - ends[sample["sample_id"]]),
                    abs(supplied["observed_end_time"] - truth),
                    abs(supplied["origin"] - sample["origin"]),
                )
                errors.append(
                    abs(ends[sample["sample_id"]] - truth) / (truth - sample["origin"]) * 100
                )
            score = sum(errors) / len(errors)
            for supplied in output["scientific_evidence"][req["requirement_id"]][
                "prediction_evidence"
            ]["predictions"]:
                sample = next(
                    s for s in temporal["samples"] if s["sample_id"] == supplied["sample_id"]
                )
                error = max(
                    error, abs(supplied["value"] - ends[sample["sample_id"]] + sample["origin"])
                )
        else:
            score = cost if definition["target"] == "purchase_cost" else quantity - demand
        error = max(error, abs(score - output["final_metrics"][metric]))
        record = {
            "feasible": quantity >= demand,
            "metric_values": {metric: score},
            "constraint_residuals": {"water_coverage": residual(quantity - demand, relation="GE")},
            "recalculation_residuals": {"full_numeric_vector": residual(error)},
        }
        if "prediction_spec" in req:
            record["prediction_evidence"] = output["scientific_evidence"][req["requirement_id"]][
                "prediction_evidence"
            ]
        elif definition["target"] == "purchase_cost":
            record["optimality_certificate"] = {
                "proof_kind": "INDEPENDENT_BOUND",
                "scope": "positive-price integer containers",
                "lower_bound": optimum,
                "upper_bound": cost,
                "objective_value": cost,
                "tolerance": 0,
            }
        requirements[req["requirement_id"]] = record
    main_metric = plan["metric"]
    if plan["metric_definitions"][main_metric]["formula"] == "ABSOLUTE_RELATIVE_ERROR":
        records = output["metric_samples"][main_metric]
        sensitivity = sum(
            abs(ends[r["sample_id"]] + 1 - r["observed_end_time"])
            / (r["observed_end_time"] - r["origin"])
            * 100
            for r in records
        ) / len(records)
    else:
        sensitivity = (
            math.ceil((demand + 1) / raw["containers"][0]["litres"]) * raw["containers"][0]["cost"]
            if output["candidate_id"] == "BASE"
            else enumerate_plans(demand + 1, raw["containers"])[0]
        )
    assert abs(sensitivity - output["robustness_evidence"]["perturbations"][0]["result"]) < 1e-8
    result = {
        "run_id": args.run_id,
        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "requirements": requirements,
        "metric_definitions": plan["metric_definitions"],
        "metric_samples": output["metric_samples"],
        "temporal_lineage": temporal,
    }
    args.output.write_text(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
