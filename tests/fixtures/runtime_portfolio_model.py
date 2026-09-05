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
    args = parser.parse_args()
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
    test_payload = json.dumps({"selected": args.candidate_id}, sort_keys=True).encode()
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
        "sealed_test_metrics_b64": base64.b64encode(test_payload).decode(),
        "sealed_test_payload_sha256": hashlib.sha256(test_payload).hexdigest(),
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
