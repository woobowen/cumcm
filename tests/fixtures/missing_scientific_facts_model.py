"""Negative legacy-style model without generation facts.

execute writes development metrics only. A later hash-bound `--final-evaluation` writes
`runs/<run>/sealed_test.json` without mutating Development `output.json`.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


def _development_output(candidate_id: str, score: float, output: Path) -> dict:
    return {
        "candidate_id": candidate_id,
        "status": "SUCCESS",
        "validation_metrics": {"loss": score},
        "final_metrics": {"loss": score},
        "claim_scope": "Bounded project-original authorized final-evaluation fixture.",
        "requirement_claims": {
            "REQ-A": {
                "claim_id": "CLAIM-REQ-A",
                "claim_text": "Bounded result for requirement A.",
                "evidence_artifact_ids": [str(output)],
            },
            "REQ-B": {
                "claim_id": "CLAIM-REQ-B",
                "claim_text": "Bounded result for requirement B.",
                "evidence_artifact_ids": [str(output)],
            },
        },
        "figure_ready_data": [{"figure_id": "P0-02-FINAL", "series": [score]}],
        "uncertainty": {"status": "BOUNDED"},
        "limitations": ["Development grouped OOS; Final test is a separate authorized sidecar."],
        "evaluation_boundary": "DEVELOPMENT_GROUPED_OOS",
        "held_out_test_valid": False,
        "test_access_status": "NOT_AUTHORIZED",
        "test_access_count": 0,
        "test_access": {
            "status": "NOT_AUTHORIZED",
            "count": 0,
            "authorized": False,
            "used_for_selection": False,
        },
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root")
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
    score = {"BASE": 2.0, "CAND": 1.0}[args.candidate_id]
    output = _development_output(args.candidate_id, score, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
