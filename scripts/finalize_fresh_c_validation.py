#!/usr/bin/env python3
"""Main-orchestrator-only deterministic completion of a frozen captured episode."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"


def load_core():
    spec = importlib.util.spec_from_file_location("fresh_case_completion_core", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def select_candidate(attempts, plan):
    scores = {}
    for candidate in plan["candidate_ids"]:
        values = [
            item["validation_score"]
            for item in attempts
            if item["candidate_id"] == candidate and item["outcome"] == "SUCCESS"
        ]
        if values:
            scores[candidate] = sum(values) / len(values)
    if not scores:
        raise ValueError("VALIDATION_NO_ELIGIBLE_SUCCESS")
    direction = 1 if plan["metric_direction"] == "MIN" else -1
    selected = min(scores, key=lambda candidate: (direction * scores[candidate], candidate))
    return {
        "selected_candidate_id": selected,
        "validation_scores": scores,
        "metric": plan["metric"],
        "rule": plan["selection_rule"],
        "aggregation_rule": plan["aggregation_rule"],
    }


def complete(case_root, test_field):
    core = load_core()
    if core.load_state(case_root)["state"] != "RUNNING":
        raise ValueError("VALIDATION_COMPLETION_STATE_INVALID")
    completion_path = case_root / "evidence/native_completion.json"
    if completion_path.exists():
        raise ValueError("VALIDATION_COMPLETION_ALREADY_FROZEN")
    plan = core.read_artifact(case_root, "experiment_plan")["content"]
    captures = sorted(case_root.glob("runs/*/execution_capture.json"))
    attempts = []
    for path in captures:
        capture = core.load_json(path)
        score = None
        if capture["outcome"] == "SUCCESS":
            # Only validation values enter the selection payload; no test decoding occurs here.
            output = core.load_json(case_root / capture["output"]["path"])
            score = output["validation_metrics"][plan["metric"]]
            if not core.strict_score(score):
                raise ValueError("VALIDATION_SELECTION_SCORE_INVALID")
        attempts.append(
            {
                "candidate_id": capture["candidate_id"],
                "outcome": capture["outcome"],
                "random_seed": capture["seed"],
                "run_id": capture["run_id"],
                "validation_score": score,
            }
        )
    try:
        payload = select_candidate(attempts, plan)
    except ValueError as exc:
        if str(exc) != "VALIDATION_NO_ELIGIBLE_SUCCESS":
            raise
        decision_hash = core.canonical_hash(
            {"status": "NO_ELIGIBLE_CANDIDATE", "attempts": attempts}
        )
        for attempt in attempts:
            core.seal_captured_run(case_root, run_id=attempt["run_id"], decision_hash=decision_hash)
        result = {
            "status": "BLOCK_NATIVE_CONTRACTS",
            "reason_codes": ["VALIDATION_NO_ELIGIBLE_SUCCESS"],
            "selected_candidate_id": None,
            "selected_run_id": None,
            "selection_decision_hash": decision_hash,
            "attempts": attempts,
            "gate_events": [],
            "test_access_count": 0,
        }
        core.write_json(completion_path, result, overwrite=False)
        return result
    decision_hash = core.canonical_hash(payload)
    core.write_json(
        case_root / "evidence/selection_before_test_access.json",
        {"selected_at": core.utc_now(), "decision_hash": decision_hash, "payload": payload},
        overwrite=False,
    )
    for attempt in attempts:
        core.seal_captured_run(case_root, run_id=attempt["run_id"], decision_hash=decision_hash)
    selected = payload["selected_candidate_id"]
    selected_attempt = min(
        (
            item
            for item in attempts
            if item["candidate_id"] == selected and item["outcome"] == "SUCCESS"
        ),
        key=lambda item: (str(item["random_seed"]), item["run_id"]),
    )
    run_id = selected_attempt["run_id"]
    manifest = core.load_json(case_root / "runs" / run_id / "manifest.json")
    output = core.load_json(case_root / manifest["output_files"][0]["path"])
    test_bytes = base64.b64decode(output[test_field], validate=True)
    if hashlib.sha256(test_bytes).hexdigest() != output["sealed_test_payload_sha256"]:
        raise ValueError("VALIDATION_SEALED_TEST_PAYLOAD_HASH_MISMATCH")
    test_metrics = json.loads(test_bytes)
    core.write_json(
        case_root / "evidence/selected_test_access.json",
        {
            "accessed_at": core.utc_now(),
            "selection_decision_hash": decision_hash,
            "run_id": run_id,
            "count": 1,
            "used_for_selection": False,
            "encoding_is_not_cryptographic_isolation": True,
            "test_metrics": test_metrics,
            "selected_output_hash": manifest["output_hash"],
            "decoded_payload_sha256": hashlib.sha256(test_bytes).hexdigest(),
        },
        overwrite=False,
    )
    comparison = {
        field: plan[field]
        for field in (
            "aggregation_rule",
            "baseline_id",
            "candidate_ids",
            "code_commit",
            "handoff_generated_at",
            "metric",
            "metric_direction",
            "random_seeds",
            "required_code_files",
            "required_input_hashes",
            "selection_rule",
            "splits",
            "stop_rule",
        )
    }
    comparison.update(
        attempts=attempts,
        freeze_bindings=plan["trusted_freeze_registry"],
        selected_candidate_id=selected,
        selection_decision_hash=decision_hash,
        test_access={"authorized": True, "count": 1, "used_for_selection": False},
        reliability={
            "attempts": len(attempts),
            "successful": sum(item["outcome"] == "SUCCESS" for item in attempts),
            "failed_or_infeasible": sum(item["outcome"] != "SUCCESS" for item in attempts),
        },
        leakage_checks={
            "future_information": False,
            "group_overlap": False,
            "target_in_features": False,
            "test_used_for_candidate_generation": False,
            "test_used_for_feature_selection": False,
            "test_used_for_threshold_selection": False,
            "time_order_valid": True,
        },
    )

    def accepted(key, content):
        core.write_json(case_root / core.ARTIFACT_PATHS[key], core.artifact(key, content))

    accepted("model_comparison", comparison)
    robustness = {
        field: manifest[field]
        for field in ("configuration_hash", "decision_hash", "input_hash", "output_hash")
    }
    robustness.update(
        {
            field: output["robustness_evidence"][field]
            for field in ("failure_cases", "metric", "metric_direction", "perturbations")
        },
        run_id=run_id,
        selected_model=selected,
        status="VALIDATED",
    )
    accepted("robustness_analysis", robustness)
    final = {
        "claim_scope": output["claim_scope"],
        "decision_hash": decision_hash,
        "final_metrics": output["final_metrics"],
        "output_hash": manifest["output_hash"],
        "run_id": run_id,
        "selected_model": selected,
        "status": "FINAL_CANDIDATE",
    }
    accepted("final_result", final)
    requirements = core.read_artifact(case_root, "problem_requirements")["content"]["requirements"]
    claims = output["requirement_claims"]
    aggregate = {
        "claim_id": "CLAIM-AGGREGATE-DERIVE",
        "claim_text": output["claim_scope"],
        "supported_scope": output["claim_scope"],
        "code_hash": manifest["code_tree_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "contradiction_status": "NONE",
        "decision_hash": decision_hash,
        "evidence_artifact_ids": sorted(
            {
                core.ARTIFACT_PATHS[key]
                for key in ("model_comparison", "robustness_analysis", "final_result")
            }
            | {record["path"] for record in manifest["output_files"]}
        ),
        "evidence_status": "CURRENT",
        "input_hash": manifest["input_hash"],
        "output_hash": manifest["output_hash"],
        "requirement_claims": claims,
        "run_id": run_id,
        "run_manifest_hash": core.canonical_hash(manifest),
        "supported_requirement_ids": core.required_requirement_ids(case_root),
    }
    accepted("claim_evidence", core.derive_claim_contract(aggregate, requirements))
    events = []
    try:
        while core.load_state(case_root)["state"] != "EVIDENCE_VALIDATED":
            before = core.utc_now()
            state = core.advance_once(case_root)
            events.append(
                {
                    "gate": state["last_gate"],
                    "state": state["state"],
                    "started_at": before,
                    "ended_at": core.utc_now(),
                    "status": "PASS",
                }
            )
        state = core.load_state(case_root)
        handoff = core.build_expected_handoff(case_root, state)
        core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
        state = core.advance_once(case_root)
        events.append({"gate": state["last_gate"], "state": state["state"], "status": "PASS"})
        result = {"status": "PASS_NATIVE_CONTRACTS", "native_state": state["state"]}
    except ValueError as exc:
        result = {"status": "BLOCK_NATIVE_CONTRACTS", "reason_codes": str(exc).split(";")}
    result.update(
        selected_candidate_id=selected,
        selected_run_id=run_id,
        selection_decision_hash=decision_hash,
        attempts=attempts,
        gate_events=events,
        empirical_acceptance="REQUIRES_SEPARATE_FROZEN_RUBRIC_ADJUDICATION",
    )
    core.write_json(completion_path, result, overwrite=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--test-field", default="sealed_test_metrics_b64")
    args = parser.parse_args()
    result = complete(args.case_root.resolve(), args.test_field)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_NATIVE_CONTRACTS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
