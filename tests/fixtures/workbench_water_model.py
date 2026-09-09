"""Original finite water case: prefix regression, dynamic programming and stock balance."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    ).hexdigest()


def supply(demand, containers, baseline):
    """Unbounded purchase with finite positive costs; cap oversupply by largest container."""
    if baseline:
        counts = [math.ceil(demand / containers[0]["litres"]), 0]
    else:
        limit = demand + max(c["litres"] for c in containers)
        states = {0: (0, [0, 0])}
        for amount in range(limit + 1):
            if amount not in states:
                continue
            cost, previous = states[amount]
            for index, container in enumerate(containers):
                next_amount = amount + container["litres"]
                if next_amount > limit:
                    continue
                new = previous.copy()
                new[index] += 1
                candidate = (cost + container["cost"], new)
                if next_amount not in states or candidate < states[next_amount]:
                    states[next_amount] = candidate
        _, counts = min(value for amount, value in states.items() if amount >= demand)
    quantity = sum(n * c["litres"] for n, c in zip(counts, containers, strict=True))
    cost = sum(n * c["cost"] for n, c in zip(counts, containers, strict=True))
    return counts, quantity, cost


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    def content(path):
        return json.loads((args.case_root / path).read_text())["content"]

    raw = json.loads((args.case_root / "data/raw/input.json").read_text())
    plan = content("experiments/experiment_plan.json")
    requirements = content("problem/problem_requirements.json")["requirements"]
    sources = content("research/source_ledger.json")["sources"]
    temporal = plan.get("temporal_design")
    rows = {r["observation_id"]: r for r in raw.get("observations", [])}
    ends = {}
    for sample in (temporal or {}).get("samples", []):
        prefix = [rows[k] for k in sample["feature_observation_ids"]]
        tx = sum(r["observed_at"] for r in prefix) / len(prefix)
        ty = sum(r["value"] for r in prefix) / len(prefix)
        slope = sum((r["observed_at"] - tx) * (r["value"] - ty) for r in prefix) / sum(
            (r["observed_at"] - tx) ** 2 for r in prefix
        )
        end = (raw["threshold"] - ty) / slope + tx
        if raw["kind"] == "prediction" and args.candidate_id == "BASE":
            end += raw["baseline_delay"]
        ends[sample["sample_id"]] = end
    remaining = [
        ends[s["sample_id"]] - s["origin"]
        for s in (temporal or {}).get("samples", [])
        if s["split"] == "FORECAST"
    ]
    demand = (
        math.ceil(remaining[0] * raw["flow_litres_per_minute"] - 1e-9)
        if remaining
        else raw["fixed_demand_litres"]
    )
    counts, quantity, cost = supply(demand, raw["containers"], args.candidate_id == "BASE")
    if raw.get("fault") == "INFEASIBLE":
        counts, quantity, cost = [0, 0], 0, 0
    balance = [quantity - min(t, demand) for t in range(demand + 1)]
    metrics, samples, accounting, facts, claims = {}, {}, {}, {}, {}
    uncertainty = {"kind": "UNCALIBRATED_POINT_ESTIMATE", "calibrated": False}
    for requirement in requirements:
        rid = requirement["requirement_id"]
        metric, definition = next(iter(requirement["metric_contracts"].items()))
        evidence = None
        if "prediction_spec" in requirement:
            records = [
                {
                    "sample_id": s["sample_id"],
                    "target": definition["target"],
                    "unit": definition["target_unit"],
                    "origin": s["origin"],
                    "predicted_end_time": ends[s["sample_id"]],
                    "observed_end_time": rows[s["target_observation_id"]]["observed_at"],
                }
                for s in temporal["samples"]
                if s["split"] == "VALIDATION"
            ]
            score = sum(
                abs(r["predicted_end_time"] - r["observed_end_time"])
                / (r["observed_end_time"] - r["origin"])
                * 100
                for r in records
            ) / len(records)
            evidence = {
                "prediction_spec_sha256": digest(requirement["prediction_spec"]),
                "temporal_design_sha256": digest(temporal),
                "empirical_accuracy_verified": False,
                "predictions": [
                    {
                        "sample_id": s["sample_id"],
                        "entity_id": s["entity_id"],
                        "origin": s["origin"],
                        "target": requirement["prediction_spec"]["target_field"],
                        "value": ends[s["sample_id"]] - s["origin"],
                    }
                    for s in temporal["samples"]
                    if s["split"] == "FORECAST"
                ],
                "historical_validation": {
                    "sample_ids": [r["sample_id"] for r in records],
                    "metric_ids": [metric],
                },
                "uncertainty": uncertainty,
            }
            method = "PREDICTION"
        else:
            score = cost if definition["target"] == "purchase_cost" else balance[-1]
            records = [
                {
                    "sample_id": "ALLOCATION",
                    "target": definition["target"],
                    "unit": definition["target_unit"],
                    "value": score,
                }
            ]
            method = "OPTIMIZATION"
        metrics[metric], samples[metric] = score, records
        accounting[metric] = {
            "value": score,
            "included_count": len(records),
            "excluded_sample_ids": [],
        }
        facts[rid] = {
            "generation_method": method,
            "source_ids": [s["source_id"] for s in sources],
            "scope": {
                "fields": requirement["minimum_data_fields"],
                "time": requirement["required_time_scope"],
                "entities": requirement["required_entity_scope"],
            },
            "metric_values": {metric: score},
            "assumption_artifact_sha256": hashlib.sha256(
                (args.case_root / "models/assumptions_and_symbols.json").read_bytes()
            ).hexdigest(),
            **({"prediction_evidence": evidence} if evidence else {}),
        }
        claims[rid] = {
            "claim_id": f"CLAIM-{rid}",
            "claim_text": f"Bounded result for {rid}.",
            "evidence_artifact_ids": ["runs/" + args.output.parent.name + "/output.json"],
        }
    main_metric = plan["metric"]
    if plan["metric_definitions"][main_metric]["formula"] == "ABSOLUTE_RELATIVE_ERROR":
        sensitivity = sum(
            abs(r["predicted_end_time"] + 1 - r["observed_end_time"])
            / (r["observed_end_time"] - r["origin"])
            * 100
            for r in samples[main_metric]
        ) / len(samples[main_metric])
    else:
        sensitivity = supply(demand + 1, raw["containers"], args.candidate_id == "BASE")[2]
    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": metrics,
        "final_metrics": metrics,
        "claim_scope": "Original finite water scenario; no real-world forecast accuracy claim.",
        "requirement_claims": claims,
        "scientific_evidence": facts,
        "metric_definitions": plan["metric_definitions"],
        "metric_samples": samples,
        "metric_accounting": accounting,
        "temporal_lineage": temporal,
        "allocation": {
            "counts": counts,
            "quantity_litres": quantity,
            "cost": cost,
            "demand_litres": demand,
            "balance_litres": balance,
        },
        "figure_ready_data": [{"minute": t, "litres": b} for t, b in enumerate(balance)],
        "uncertainty": uncertainty,
        "limitations": [
            "Synthetic trajectory; no calibrated interval or external effectiveness.",
            "Integer purchase assumes positive prices and unlimited identical stock.",
        ],
        "robustness_evidence": {
            "metric": main_metric,
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "DEMAND_PLUS_ONE_OR_END_PLUS_ONE",
                    "metric": main_metric,
                    "result": sensitivity,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": [
                "Nonlinear future trend, purchase shortage and zero denominator are outside scope."
            ],
        },
    }
    args.output.write_text(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
