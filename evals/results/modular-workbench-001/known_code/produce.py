"""Known 2016 Q3 interface exercise: prior-state scale/affine transfer, no target truth."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def compute(index, design, candidate, shift=0):
    rows = {r["observation_id"]: r for r in index["observations"]}
    curves, histories, forecasts = {}, [], []
    for sample in design["samples"]:
        first = rows[sample["feature_observation_ids"][0]]
        state = int(first["observation_id"].split("-")[0][1:])
        features = sample["feature_observation_ids"]
        if features != [f"S{state}-U{j}" for j in range(len(features))]:
            raise ValueError("KNOWN_Q3_FEATURE_PREFIX_IDENTITY_INVALID")
        actual_fit_ids = [f"S{s}-U{j}" for s in range(state) for j in range(301)] + features
        for field in ("preprocess_fit_observation_ids", "model_fit_observation_ids"):
            if set(sample[field]) != set(actual_fit_ids) or len(sample[field]) != len(
                actual_fit_ids
            ):
                raise ValueError("KNOWN_Q3_ACTUAL_FIT_LINEAGE_MISMATCH")
        prior = np.array([[rows[f"S{s}-U{j}"]["value"] for j in range(301)] for s in range(state)])
        reference = prior.mean(axis=0)
        prefix = np.array([rows[k]["value"] for k in sample["feature_observation_ids"]]) + shift
        x = reference[: len(prefix)]
        if candidate == "BASELINE":
            a, b = 0.0, float(x @ prefix / (x @ x))
        else:
            a, b = np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), prefix, rcond=None)[0]
        curve = (a + b * reference).tolist()
        curves[sample["sample_id"]] = curve
        end = state * 10000 + curve[-1]
        if sample["split"] == "VALIDATION":
            histories.append(
                {
                    "sample_id": sample["sample_id"],
                    "target": "remaining_time",
                    "unit": "min",
                    "origin": sample["origin"],
                    "predicted_end_time": end,
                    "observed_end_time": rows[sample["target_observation_id"]]["observed_at"],
                }
            )
        else:
            forecasts.append(
                {
                    "sample_id": sample["sample_id"],
                    "entity_id": sample["entity_id"],
                    "origin": sample["origin"],
                    "target": "future_remaining_time",
                    "value": end - sample["origin"],
                }
            )
    score = sum(
        abs(r["predicted_end_time"] - r["observed_end_time"])
        / (r["observed_end_time"] - r["origin"])
        for r in histories
    ) / len(histories)
    return curves, histories, forecasts, score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    def content(relative):
        return json.loads((args.case_root / relative).read_text())["content"]

    plan = content("experiments/experiment_plan.json")
    req = content("problem/problem_requirements.json")["requirements"][0]
    design = plan["temporal_design"]
    index = json.loads((args.case_root / design["index_path"]).read_text())
    curves, history, forecasts, score = compute(index, design, args.candidate_id)
    shifted_curves, _, _, sensitivity = compute(index, design, args.candidate_id, shift=1)
    metrics = {"q3_remaining_MRE": score, "q3_remaining_min": forecasts[0]["value"]}
    samples = {
        "q3_remaining_MRE": history,
        "q3_remaining_min": [
            {
                "sample_id": forecasts[0]["sample_id"],
                "target": "future_remaining_time",
                "unit": "min",
                "value": forecasts[0]["value"],
            }
        ],
    }
    uncertainty = {"kind": "UNCALIBRATED_POINT_ESTIMATE", "calibrated": False}
    facts = {
        "generation_method": "PREDICTION",
        "source_ids": ["SRC-CUMCM-2016-C-WORKBOOK"],
        "scope": {
            "fields": req["minimum_data_fields"],
            "time": req["required_time_scope"],
            "entities": req["required_entity_scope"],
        },
        "metric_values": metrics,
        "assumption_artifact_sha256": hashlib.sha256(
            (args.case_root / "models/assumptions_and_symbols.json").read_bytes()
        ).hexdigest(),
        "prediction_evidence": {
            "prediction_spec_sha256": digest(req["prediction_spec"]),
            "temporal_design_sha256": digest(design),
            "empirical_accuracy_verified": False,
            "predictions": forecasts,
            "historical_validation": {
                "sample_ids": [r["sample_id"] for r in history],
                "metric_ids": ["q3_remaining_MRE"],
            },
            "uncertainty": uncertainty,
        },
    }
    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": metrics,
        "final_metrics": metrics,
        "claim_scope": (
            "Known Q3 conditional transfer only; Q1/Q2 and whole-problem completion excluded."
        ),
        "requirement_claims": {
            "REQ-Q3": {
                "claim_id": "CLAIM-2016-MODULE-Q3",
                "claim_text": (
                    "State3 remaining time under registered prior-state transfer; "
                    "actual error unknown."
                ),
                "evidence_artifact_ids": ["runs/" + args.output.parent.name + "/output.json"],
            }
        },
        "scientific_evidence": {"REQ-Q3": facts},
        "metric_definitions": plan["metric_definitions"],
        "metric_samples": samples,
        "metric_accounting": {
            k: {"value": v, "included_count": len(samples[k]), "excluded_sample_ids": []}
            for k, v in metrics.items()
        },
        "temporal_lineage": design,
        "curves": curves,
        "shifted_curves": shifted_curves,
        "figure_ready_data": forecasts,
        "uncertainty": uncertainty,
        "limitations": [
            "Known task and prior results, no blind Validation.",
            "Six correlated origins from one battery; future state3 endpoint unknown.",
            "Scale/affine transfer may fail under new aging mechanism; no calibrated interval.",
        ],
        "robustness_evidence": {
            "metric": "q3_remaining_MRE",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "PREFIX_PLUS_ONE_MIN_FIXED_ORIGIN",
                    "metric": "q3_remaining_MRE",
                    "result": sensitivity,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": [
                "Nonpositive remaining time or zero remaining-time denominator rejects."
            ],
        },
    }
    args.output.write_text(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
