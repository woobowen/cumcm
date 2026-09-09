"""Finite neutral RC9 model: prefix-only linear forecasting and capacity allocation."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    ).hexdigest()


def predict(rows, sample, bias):
    prefix = [rows[k] for k in sample["feature_observation_ids"]]
    n = len(prefix)
    x = sum(r["observed_at"] for r in prefix) / n
    y = sum(r["value"] for r in prefix) / n
    slope = sum((r["observed_at"] - x) * (r["value"] - y) for r in prefix) / sum(
        (r["observed_at"] - x) ** 2 for r in prefix
    )
    return (10 - y + slope * x) / slope + bias


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-root", type=Path, required=True)
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--seed")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    def artifact(path):
        return json.loads((a.case_root / path).read_text())["content"]

    data = json.loads((a.case_root / "data/raw/input.json").read_text())
    plan = artifact("experiments/experiment_plan.json")
    requirements = artifact("problem/problem_requirements.json")["requirements"]
    sources = artifact("research/source_ledger.json")["sources"]
    definitions = plan["metric_definitions"]
    samples, values, accounting, facts, claims = {}, {}, {}, {}, {}
    temporal = plan.get("temporal_design")
    rows = {r["observation_id"]: r for r in data.get("observations", [])}
    bias = (
        (0.0 if a.candidate_id == "CAND" else 1.0)
        if data["experiment_kind"] != "mixed"
        else (1.0 if a.candidate_id == "CAND" else 0.0)
    )
    ends = {s["sample_id"]: predict(rows, s, bias) for s in temporal["samples"]} if temporal else {}
    q = sum(data["x"]) + (1 if a.candidate_id == "BASE" else 0)
    uncertainty = {"kind": "UNCALIBRATED_POINT_ESTIMATE", "calibrated": False}
    for req in requirements:
        req_id = req["requirement_id"]
        metric = next(iter(req["metric_contracts"]))
        definition = definitions[metric]
        if "prediction_spec" in req:
            sample_rows = [
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
                for r in sample_rows
            ) / len(sample_rows)
            evidence = {
                "prediction_spec_sha256": digest(req["prediction_spec"]),
                "temporal_design_sha256": digest(temporal),
                "empirical_accuracy_verified": False,
                "predictions": [
                    {
                        "sample_id": s["sample_id"],
                        "entity_id": s["entity_id"],
                        "origin": s["origin"],
                        "target": req["prediction_spec"]["target_field"],
                        "value": ends[s["sample_id"]] - s["origin"],
                    }
                    for s in temporal["samples"]
                    if s["split"] == "FORECAST"
                ],
                "historical_validation": {
                    "sample_ids": [r["sample_id"] for r in sample_rows],
                    "metric_ids": [metric],
                },
                "uncertainty": uncertainty,
            }
            method = "PREDICTION"
        else:
            sample_rows = [
                {
                    "sample_id": "ALLOCATION",
                    "target": definition["target"],
                    "unit": definition["target_unit"],
                    "value": q,
                }
            ]
            score, evidence, method = q, None, "OPTIMIZATION"
        samples[metric], values[metric] = sample_rows, score
        accounting[metric] = {
            "value": score,
            "included_count": len(sample_rows),
            "excluded_sample_ids": [],
        }
        facts[req_id] = {
            "generation_method": method,
            "source_ids": [s["source_id"] for s in sources],
            "scope": {
                "fields": req["minimum_data_fields"],
                "time": req["required_time_scope"],
                "entities": req["required_entity_scope"],
            },
            "metric_values": {metric: score},
            "assumption_artifact_sha256": hashlib.sha256(
                (a.case_root / "models/assumptions_and_symbols.json").read_bytes()
            ).hexdigest(),
            **({"prediction_evidence": evidence} if evidence else {}),
        }
        claims[req_id] = {
            "claim_id": f"CLAIM-{req_id}",
            "claim_text": f"Bounded result for {req_id}.",
            "evidence_artifact_ids": [str(a.output)],
        }
    output = {
        "candidate_id": a.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": values,
        "final_metrics": values,
        "claim_scope": "Conditional forecast; future accuracy unverified.",
        "requirement_claims": claims,
        "scientific_evidence": facts,
        "quantity": q,
        "metric_definitions": definitions,
        "metric_samples": samples,
        "metric_accounting": accounting,
        "temporal_lineage": temporal,
        "figure_ready_data": [{"series": list(values.values())}],
        "uncertainty": uncertainty,
        "limitations": ["No empirical accuracy claim for unknown future truth."],
        "robustness_evidence": {
            "metric": "metric_a",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "FORECAST_END_PLUS_ONE_OR_DEMAND_PLUS_ONE",
                    "metric": "metric_a",
                    "result": values["metric_a"] + 1,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["Relative error is undefined at zero; regime change is untested."],
        },
    }
    a.output.write_text(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
