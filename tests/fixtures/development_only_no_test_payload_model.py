"""Development-only model: honest execute output has no sealed-test payload."""

from __future__ import annotations

import argparse
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
    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": {"loss": score},
        "final_metrics": {"loss": score},
        "claim_scope": "Bounded project-original development-only controller fixture.",
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
        "figure_ready_data": [{"figure_id": "P0-01-FINALIZATION", "series": [score]}],
        "uncertainty": {"status": "BOUNDED"},
        "limitations": ["Development grouped OOS only; no authorized sealed test."],
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
    sources = json.loads((Path(args.case_root) / "research/source_ledger.json").read_text())[
        "content"
    ]["sources"]
    output["scientific_evidence"] = {}
    for req in output["requirement_claims"]:
        relevant = [source for source in sources if req in source["supports_requirement_ids"]]
        output["scientific_evidence"][req] = {
            "generation_method": "DESCRIPTIVE_STATISTIC",
            "source_ids": [source["source_id"] for source in relevant],
            "scope": {
                dimension: sorted(set().union(*(set(source[key]) for source in relevant)))
                for dimension, key in (
                    ("fields", "field_schema"),
                    ("time", "time_scope"),
                    ("entities", "entity_scope"),
                )
            },
            "metric_values": output["validation_metrics"],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
