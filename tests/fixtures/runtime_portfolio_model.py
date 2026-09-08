"""Project-original dynamic neutral model for runtime portfolio E2E cases."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--final-evaluation", action="store_true")
    parser.add_argument("--authorization-hash")
    parser.add_argument("--final-output", type=Path)
    args = parser.parse_args()
    if args.final_evaluation:
        if not args.authorization_hash or args.final_output is None:
            return 2
        test_payload = json.dumps({"selected": args.candidate_id}, sort_keys=True).encode()
        payload = {
            "run_id": None,
            "authorization_hash": args.authorization_hash,
            "sealed_test_metrics_b64": base64.b64encode(test_payload).decode(),
            "sealed_test_payload_sha256": hashlib.sha256(test_payload).hexdigest(),
        }
        args.final_output.parent.mkdir(parents=True, exist_ok=True)
        args.final_output.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return 0
    requirement_artifact = json.loads(
        (args.case_root / "problem/problem_requirements.json").read_text(encoding="utf-8")
    )
    requirement_ids = [
        item["requirement_id"]
        for item in requirement_artifact["content"]["requirements"]
        if item.get("role", "PRIMARY") == "PRIMARY"
    ]
    base_values = {"BASE": [1.0, 4.0, 3.0, 2.0], "CAND": [2.0, 1.0, 1.0, 3.0]}
    values = {
        f"metric_{chr(ord('a') + index)}": value
        for index, value in enumerate(base_values[args.candidate_id][: len(requirement_ids)])
    }
    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": values,
        "final_metrics": values,
        "claim_scope": "Bounded project-original neutral runtime scope.",
        "requirement_claims": {
            requirement_id: {
                "claim_id": f"CLAIM-{requirement_id}",
                "claim_text": f"Bounded result for {requirement_id}.",
                "evidence_artifact_ids": [str(args.output)],
            }
            for requirement_id in requirement_ids
        },
        "figure_ready_data": [{"figure_id": "NEUTRAL", "series": list(values.values())}],
        "uncertainty": {"status": "BOUNDED"},
        "limitations": ["Project-original deterministic neutral fixture."],
        "robustness_evidence": {
            "metric": "metric_a",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "SHIFT",
                    "metric": "metric_a",
                    "result": values["metric_a"] + 0.1,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["Fixture does not establish external validity."],
        },
    }
    sources = json.loads(
        (args.case_root / "research/source_ledger.json").read_text(encoding="utf-8")
    )["content"]["sources"]
    assumption_path = args.case_root / "models/assumptions_and_symbols.json"
    output["scientific_evidence"] = {}
    for index, requirement in enumerate(requirement_artifact["content"]["requirements"]):
        requirement_id = requirement["requirement_id"]
        relevant = [s for s in sources if requirement_id in s["supports_requirement_ids"]]
        if not any(s["evidence_class"] == "SIMULATION" for s in relevant):
            continue
        metric = f"metric_{chr(ord('a') + index)}"
        output["scientific_evidence"][requirement_id] = {
            "generation_method": "CONDITIONAL_SIMULATION",
            "source_ids": [s["source_id"] for s in relevant],
            "scope": {
                "fields": requirement["minimum_data_fields"],
                "time": requirement["required_time_scope"],
                "entities": requirement["required_entity_scope"],
            },
            "metric_values": {metric: values[metric]},
            "assumption_artifact_sha256": hashlib.sha256(assumption_path.read_bytes()).hexdigest(),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
