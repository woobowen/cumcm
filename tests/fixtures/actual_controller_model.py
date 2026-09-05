"""Project-original deterministic model used by actual-controller black-box probes."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    score = {"BASE": 2.0, "CAND": 1.0}[args.candidate_id]
    test_payload = json.dumps({"selected": args.candidate_id}, sort_keys=True).encode()
    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": {"loss": score},
        "final_metrics": {"loss": score},
        "claim_scope": "Bounded project-original controller probe scope.",
        "requirement_claims": {
            "REQ-A": {
                "claim_id": "CLAIM-REQ-A",
                "claim_text": "Bounded result for requirement A.",
                "evidence_artifact_ids": [str(args.output)],
            },
            "REQ-B": {
                "claim_id": "CLAIM-REQ-B",
                "claim_text": "Bounded result for requirement B.",
                "evidence_artifact_ids": [str(args.output)],
            },
        },
        "figure_ready_data": [{"figure_id": "PROBE", "series": [score]}],
        "uncertainty": {"status": "BOUNDED"},
        "limitations": ["Project-original deterministic black-box fixture."],
        "sealed_test_metrics_b64": base64.b64encode(test_payload).decode(),
        "sealed_test_payload_sha256": hashlib.sha256(test_payload).hexdigest(),
        "robustness_evidence": {
            "metric": "loss",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "SHIFT",
                    "metric": "loss",
                    "result": score + 0.1,
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
