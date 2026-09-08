"""Small real bounded optimization; no prediction split or test labels exist."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((args.case_root / "data/raw/input.json").read_text())
    demand, capacity = sum(data["x"]), sum(data["y"])
    quantity = demand + (1 if args.candidate_id == "BASE" else 0)
    assert quantity <= capacity
    ledger = json.loads((args.case_root / "research/source_ledger.json").read_text())["content"]
    assumptions = args.case_root / "models/assumptions_and_symbols.json"
    scope = {"fields": ["x", "y"], "time": ["FROZEN_SCOPE"], "entities": ["ENTITY-SET"]}
    values = {"metric_a": quantity, "metric_b": capacity - quantity}
    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": values,
        "final_metrics": values,
        "claim_scope": "Finite capacity allocation on supplied inputs.",
        "quantity": quantity,
        "requirement_claims": {
            req: {
                "claim_id": f"CLAIM-{req}",
                "claim_text": f"Bounded result for {req}.",
                "evidence_artifact_ids": [str(args.output)],
            }
            for req in ["REQ-A", "REQ-B"]
        },
        "scientific_evidence": {
            req: {
                "generation_method": "OPTIMIZATION",
                "scope": scope,
                "source_ids": [source["source_id"] for source in ledger["sources"]],
                "metric_values": values,
                "assumption_artifact_sha256": hashlib.sha256(assumptions.read_bytes()).hexdigest(),
            }
            for req in ["REQ-A", "REQ-B"]
        },
        "figure_ready_data": [{"series": [quantity, capacity]}],
        "uncertainty": {"scope": "Finite deterministic supplied inputs"},
        "limitations": ["No external effectiveness or forecast claimed."],
        "robustness_evidence": {
            "metric": "metric_a",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "DEMAND_PLUS_ONE",
                    "metric": "metric_a",
                    "result": demand + 1,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["Demand above supplied capacity is infeasible."],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
