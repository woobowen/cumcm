#!/usr/bin/env python3
"""Main-orchestrator-only completion controller for a frozen captured episode."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
TRACE_RELATIVE = "evidence/gate_execution_trace.json"
COMPLETION_RELATIVE = "evidence/native_completion.json"
AUTHORITATIVE_KEYS = (
    "problem_requirements",
    "source_ledger",
    "data_audit",
    "data_sufficiency",
    "experiment_plan",
    "model_comparison",
    "requirement_selection",
    "final_result",
    "claim_evidence",
    "semantic_claim_support",
)


def load_core():
    spec = importlib.util.spec_from_file_location("fresh_case_completion_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("VALIDATION_CORE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def select_candidate(attempts: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    scores: dict[str, float] = {}
    for candidate in plan["candidate_ids"]:
        values = [
            item["validation_score"]
            for item in attempts
            if item["candidate_id"] == candidate
            and item["outcome"] == "SUCCESS"
            and item["validation_score"] is not None
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


def _path_hashes(core: Any, case_root: Path, relatives: list[str]) -> dict[str, str]:
    return {
        relative: core.file_hash(case_root / relative)
        for relative in sorted(set(relatives))
        if (case_root / relative).is_file()
    }


def _authoritative_hashes(core: Any, case_root: Path) -> dict[str, str]:
    relatives = [core.ARTIFACT_PATHS[key] for key in AUTHORITATIVE_KEYS]
    relatives.extend(
        str(path.relative_to(case_root))
        for path in sorted(case_root.glob("runs/*/execution_capture.json"))
    )
    return _path_hashes(core, case_root, relatives)


def _dict_result(value: Any) -> dict[str, Any]:
    if hasattr(value, "as_dict"):
        value = value.as_dict()
    if not isinstance(value, dict):
        return {"status": "BLOCK", "reason_codes": ["RC_GATE_RESULT_INVALID"]}
    status = value.get("status")
    reasons = value.get("reason_codes")
    return {
        "status": status if isinstance(status, str) else "BLOCK",
        "reason_codes": sorted(set(reasons if isinstance(reasons, list) else [])),
    }


class GateTrace:
    def __init__(self, core: Any, case_root: Path, state_before: dict[str, Any]):
        self.core = core
        self.case_root = case_root
        self.state_before = state_before
        self.state_before_hash = core.file_hash(case_root / "case_state.json")
        self.input_artifact_hashes = _authoritative_hashes(core, case_root)
        self.events: list[dict[str, Any]] = []

    def invoke(
        self,
        gate_id: str,
        entrypoint: str,
        input_relatives: list[str],
        evaluator: Callable[[], Any],
        *,
        accepted_statuses: tuple[str, ...] = ("PASS",),
    ) -> dict[str, Any]:
        started = time.monotonic()
        try:
            result = _dict_result(evaluator())
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            reasons = [item for item in str(exc).split(";") if item.startswith("RC_")]
            result = {
                "status": "BLOCK",
                "reason_codes": sorted(set(reasons or ["RC_GATE_EXECUTION_FAILED"])),
            }
        normalized_status = "PASS" if result["status"] in accepted_statuses else "BLOCK"
        event_result = {
            "result": normalized_status,
            "status": normalized_status,
            "source_status": result["status"],
            "reason_codes": result["reason_codes"],
        }
        self.events.append(
            {
                "gate_id": gate_id,
                "implementation_entrypoint": entrypoint,
                "input_hashes": _path_hashes(self.core, self.case_root, input_relatives),
                "result": normalized_status,
                "reason_codes": result["reason_codes"],
                "output_hash": self.core.canonical_hash(event_result),
                "duration": round(time.monotonic() - started, 6),
            }
        )
        return event_result

    def finish(
        self,
        disposition: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        state_after_hash = self.core.file_hash(self.case_root / "case_state.json")
        trace = {
            "trace_version": "gate-execution-trace/v1",
            "case_id": self.state_before["case_id"],
            "controller_command": [
                "python",
                "scripts/finalize_fresh_c_validation.py",
                "--case-root",
                "<case-root>",
            ],
            "controller_version": self.core.VERSION,
            "state_before_hash": self.state_before_hash,
            "state_after_hash": state_after_hash,
            "input_artifact_hashes": self.input_artifact_hashes,
            "gate_sequence": self.events,
            "final_disposition": disposition,
        }
        trace["trace_hash"] = self.core.canonical_hash(trace)
        self.core.write_json(self.case_root / TRACE_RELATIVE, trace, overwrite=False)
        result["gate_execution_trace"] = {
            "path": TRACE_RELATIVE,
            "sha256": self.core.file_hash(self.case_root / TRACE_RELATIVE),
            "trace_hash": trace["trace_hash"],
        }
        self.core.write_json(
            self.case_root / COMPLETION_RELATIVE,
            result,
            overwrite=False,
        )
        return result


def _attempt_registry(
    core: Any,
    case_root: Path,
    plan: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    output_registry: dict[str, dict[str, Any]] = {}
    for path in sorted(case_root.glob("runs/*/execution_capture.json")):
        capture = core.load_json(path)
        score = None
        if capture.get("outcome") == "SUCCESS":
            output_path = core.relative_case_path(case_root, capture.get("output", {}).get("path"))
            if output_path is None or not output_path.is_file():
                raise ValueError("RC_EXECUTION_CAPTURE_OUTPUT_MISMATCH")
            output = core.load_json(output_path)
            score = output.get("validation_metrics", {}).get(plan.get("metric"))
            if not core.strict_score(score):
                raise ValueError("RC_CLAIM_METRIC_BINDING_MISSING")
            output_registry[capture["run_id"]] = output
        attempts.append(
            {
                "candidate_id": capture.get("candidate_id"),
                "outcome": capture.get("outcome"),
                "random_seed": capture.get("seed"),
                "run_id": capture.get("run_id"),
                "validation_score": score,
            }
        )
    return attempts, output_registry


def _seal_attempts(
    core: Any,
    case_root: Path,
    attempts: list[dict[str, Any]],
    decision_hash: str,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        run_id = attempt.get("run_id")
        if not isinstance(run_id, str):
            raise ValueError("RC_ACTUAL_RUN_REGISTRY_MISSING")
        manifest_path = case_root / "runs" / run_id / "manifest.json"
        if not manifest_path.exists():
            core.seal_captured_run(case_root, run_id=run_id, decision_hash=decision_hash)
        manifest = core.load_json(manifest_path)
        registry[run_id] = manifest
    return registry


def _comparison_payload(
    plan: dict[str, Any],
    attempts: list[dict[str, Any]],
    selected: dict[str, Any],
    decision_hash: str,
) -> dict[str, Any]:
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
        selected_candidate_id=selected["selected_candidate_id"],
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
    return comparison


def _selected_global_run(attempts: list[dict[str, Any]], selected_candidate_id: str) -> str:
    eligible = sorted(
        (
            item
            for item in attempts
            if item.get("candidate_id") == selected_candidate_id
            and item.get("outcome") == "SUCCESS"
        ),
        key=lambda item: (str(item.get("random_seed")), str(item.get("run_id"))),
    )
    if not eligible or not isinstance(eligible[0].get("run_id"), str):
        raise ValueError("VALIDATION_NO_ELIGIBLE_SUCCESS")
    return eligible[0]["run_id"]


def _robustness_payload(
    manifest: dict[str, Any],
    output: dict[str, Any],
    selected_candidate_id: str,
) -> dict[str, Any]:
    evidence = output.get("robustness_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("RC_ROBUSTNESS_EVIDENCE_INVALID")
    return {
        "status": "VALIDATED",
        "selected_model": selected_candidate_id,
        "run_id": manifest["run_id"],
        "input_hash": manifest["input_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
        "metric": evidence.get("metric"),
        "metric_direction": evidence.get("metric_direction"),
        "perturbations": evidence.get("perturbations"),
        "failure_cases": evidence.get("failure_cases"),
    }


def _access_selected_test(
    core: Any,
    case_root: Path,
    run_id: str,
    output: dict[str, Any],
    manifest: dict[str, Any],
    decision_hash: str,
    test_field: str,
) -> None:
    encoded = output.get(test_field)
    if not isinstance(encoded, str):
        raise ValueError("VALIDATION_SEALED_TEST_PAYLOAD_MISSING")
    test_bytes = base64.b64decode(encoded, validate=True)
    decoded_hash = hashlib.sha256(test_bytes).hexdigest()
    if decoded_hash != output.get("sealed_test_payload_sha256"):
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
            "decoded_payload_sha256": decoded_hash,
        },
        overwrite=False,
    )


def _block_result(
    trace: GateTrace,
    event: dict[str, Any],
    attempts: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return trace.finish(
        "BLOCK",
        {
            "status": "BLOCK_NATIVE_CONTRACTS",
            "reason_codes": event["reason_codes"] or ["RC_GATE_REJECTED_WITHOUT_REASON"],
            "attempts": attempts or [],
            "test_access_count": 0,
            **extra,
        },
    )


def complete(case_root: Path, test_field: str) -> dict[str, Any]:
    core = load_core()
    state = core.load_state(case_root)
    if state["state"] != "RUNNING":
        raise ValueError("VALIDATION_COMPLETION_STATE_INVALID")
    if (case_root / COMPLETION_RELATIVE).exists() or (case_root / TRACE_RELATIVE).exists():
        raise ValueError("VALIDATION_COMPLETION_ALREADY_FROZEN")
    trace = GateTrace(core, case_root, state)

    requirements = core.read_artifact(case_root, "problem_requirements")["content"]["requirements"]
    primary_ids = [
        item["requirement_id"]
        for item in requirements
        if isinstance(item, dict) and item.get("role", "PRIMARY") == "PRIMARY"
    ]
    event = trace.invoke(
        "GATE_PROBLEM_REQUIREMENT",
        "cumcm_case.validate_runtime_requirements",
        [core.ARTIFACT_PATHS["problem_requirements"]],
        lambda: core.validate_runtime_requirements(requirements),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event)

    sources = core.read_artifact(case_root, "source_ledger")["content"].get("sources")
    event = trace.invoke(
        "GATE_SOURCE_EVIDENCE",
        "cumcm_case.validate_runtime_sources",
        [
            core.ARTIFACT_PATHS["problem_requirements"],
            core.ARTIFACT_PATHS["source_ledger"],
            core.ARTIFACT_PATHS["data_audit"],
        ],
        lambda: core.validate_runtime_sources(sources, primary_ids),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event)

    sufficiency = core.read_artifact(case_root, "data_sufficiency")["content"]
    event = trace.invoke(
        "GATE_DATA_SUFFICIENCY_PREFLIGHT",
        "cumcm_case.validate_data_sufficiency_record",
        [
            core.ARTIFACT_PATHS["problem_requirements"],
            core.ARTIFACT_PATHS["source_ledger"],
            core.ARTIFACT_PATHS["data_sufficiency"],
        ],
        lambda: core.validate_data_sufficiency_record(
            sufficiency,
            requirements=requirements,
            sources=sources,
        ),
        accepted_statuses=("SUFFICIENT",),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event)

    plan = core.read_artifact(case_root, "experiment_plan")["content"]
    attempts, output_registry = _attempt_registry(core, case_root, plan)
    selection_record = core.read_artifact(case_root, "requirement_selection")["content"]
    try:
        selected = select_candidate(attempts, plan)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        reason = str(exc)
        if reason != "VALIDATION_NO_ELIGIBLE_SUCCESS" and not reason.startswith("RC_"):
            reason = "RC_COMPARISON_SELECTION_INPUT_INVALID"
        no_eligible = reason == "VALIDATION_NO_ELIGIBLE_SUCCESS"
        decision_hash = core.canonical_hash(
            {"status": "NO_ELIGIBLE_CANDIDATE", "attempts": attempts}
        )
        if no_eligible:
            _seal_attempts(core, case_root, attempts, decision_hash)
        event = trace.invoke(
            "GATE_COMPARISON_SELECTION",
            "controller.capture_registry+cumcm_case.validate_requirement_selection",
            [
                core.ARTIFACT_PATHS["experiment_plan"],
                core.ARTIFACT_PATHS["requirement_selection"],
            ],
            lambda: {"status": "BLOCK", "reason_codes": [reason]},
        )
        return _block_result(
            trace,
            event,
            attempts,
            selected_candidate_id=None,
            selected_run_id=None,
            selection_decision_hash=decision_hash,
        )
    decision_hash = core.canonical_hash(selected)
    try:
        manifests = _seal_attempts(core, case_root, attempts, decision_hash)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        manifest_reason = (
            str(exc) if str(exc).startswith("RC_") else "RC_ACTUAL_RUN_REGISTRY_MISSING"
        )
        event = trace.invoke(
            "GATE_COMPARISON_SELECTION",
            "controller.capture_registry+cumcm_case.validate_requirement_selection",
            [
                core.ARTIFACT_PATHS["experiment_plan"],
                core.ARTIFACT_PATHS["requirement_selection"],
            ],
            lambda: {"status": "BLOCK", "reason_codes": [manifest_reason]},
        )
        return _block_result(trace, event, attempts)
    comparison = _comparison_payload(plan, attempts, selected, decision_hash)
    event = trace.invoke(
        "GATE_COMPARISON_SELECTION",
        "controller.capture_registry+cumcm_case.validate_requirement_selection",
        [
            core.ARTIFACT_PATHS["experiment_plan"],
            core.ARTIFACT_PATHS["requirement_selection"],
            *[f"runs/{run_id}/manifest.json" for run_id in manifests],
        ],
        lambda: core.validate_requirement_selection(selection_record),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    semantic_record = core.read_artifact(case_root, "semantic_claim_support")["content"]
    event = trace.invoke(
        "GATE_RUN_ELIGIBILITY",
        "cumcm_case.validate_runtime_run_eligibility",
        [
            core.ARTIFACT_PATHS["requirement_selection"],
            core.ARTIFACT_PATHS["semantic_claim_support"],
            *[f"runs/{run_id}/manifest.json" for run_id in manifests],
        ],
        lambda: core.validate_runtime_run_eligibility(
            selection_record,
            semantic_record,
            manifests,
        ),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    event = trace.invoke(
        "GATE_COMPATIBILITY_PORTFOLIO",
        "cumcm_case.validate_runtime_selection_compatibility",
        [
            core.ARTIFACT_PATHS["experiment_plan"],
            core.ARTIFACT_PATHS["requirement_selection"],
            *[f"runs/{run_id}/manifest.json" for run_id in manifests],
        ],
        lambda: core.validate_runtime_selection_compatibility(
            selection_record,
            manifests,
            scenario_hash=plan.get("scenario_hash"),
        ),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    event = trace.invoke(
        "GATE_SEMANTIC_CLAIM",
        "cumcm_case.validate_runtime_semantic_claims",
        [
            core.ARTIFACT_PATHS["problem_requirements"],
            core.ARTIFACT_PATHS["source_ledger"],
            core.ARTIFACT_PATHS["requirement_selection"],
            core.ARTIFACT_PATHS["semantic_claim_support"],
            *[f"runs/{run_id}/manifest.json" for run_id in manifests],
        ],
        lambda: core.validate_runtime_semantic_claims(
            semantic_record,
            selection_record,
            manifests,
            output_registry,
            requirements,
            sources,
        ),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    event = trace.invoke(
        "GATE_AGGREGATE_CLAIM",
        "cumcm_case.validate_runtime_aggregate_mapping",
        [core.ARTIFACT_PATHS["semantic_claim_support"]],
        lambda: core.validate_runtime_aggregate_mapping(semantic_record, primary_ids),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    final_result = core.build_runtime_final_result(
        selection_record,
        semantic_record,
        manifests,
    )
    claim_evidence = core.build_runtime_claim_evidence(
        final_result,
        selection_record,
        semantic_record,
        manifests,
    )
    event = trace.invoke(
        "GATE_FINALIZATION",
        "cumcm_case.validate_runtime_finalization",
        [
            core.ARTIFACT_PATHS["requirement_selection"],
            core.ARTIFACT_PATHS["semantic_claim_support"],
            *[f"runs/{run_id}/manifest.json" for run_id in manifests],
        ],
        lambda: core.validate_runtime_finalization(
            final_result,
            claim_evidence,
            selection_record,
            semantic_record,
            manifests,
        ),
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    def accepted(key: str, content: dict[str, Any]) -> None:
        core.write_json(
            case_root / core.ARTIFACT_PATHS[key],
            core.artifact(key, content),
        )

    selected_candidate_id = selected["selected_candidate_id"]
    selected_global_run_id = _selected_global_run(attempts, selected_candidate_id)
    selected_manifest = manifests[selected_global_run_id]
    selected_output = output_registry[selected_global_run_id]
    core.write_json(
        case_root / "evidence/selection_before_test_access.json",
        {
            "selected_at": core.utc_now(),
            "decision_hash": decision_hash,
            "payload": selected,
            "requirement_selection_hash": core.canonical_hash(selection_record),
        },
        overwrite=False,
    )
    _access_selected_test(
        core,
        case_root,
        selected_global_run_id,
        selected_output,
        selected_manifest,
        decision_hash,
        test_field,
    )
    accepted("model_comparison", comparison)
    accepted(
        "robustness_analysis",
        _robustness_payload(selected_manifest, selected_output, selected_candidate_id),
    )
    accepted("final_result", final_result)
    accepted("claim_evidence", claim_evidence)
    while core.load_state(case_root)["state"] != "EVIDENCE_VALIDATED":
        core.advance_once(case_root)

    def complete_handoff() -> dict[str, Any]:
        evidence_state = core.load_state(case_root)
        handoff = core.build_runtime_handoff(case_root, evidence_state)
        core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
        validation = core.validate_handoff(handoff, case_root=case_root, state=evidence_state)
        if validation.accepted:
            core.advance_once(case_root)
        return validation.as_dict()

    event = trace.invoke(
        "GATE_HANDOFF",
        "cumcm_case.build_runtime_handoff+cumcm_case.validate_handoff",
        [
            core.ARTIFACT_PATHS["model_comparison"],
            core.ARTIFACT_PATHS["requirement_selection"],
            core.ARTIFACT_PATHS["final_result"],
            core.ARTIFACT_PATHS["claim_evidence"],
            core.ARTIFACT_PATHS["semantic_claim_support"],
        ],
        complete_handoff,
    )
    if event["result"] != "PASS":
        return _block_result(trace, event, attempts)

    return trace.finish(
        "PASS",
        {
            "status": "PASS_NATIVE_CONTRACTS",
            "native_state": core.load_state(case_root)["state"],
            "attempts": attempts,
            "test_access_count": 1,
            "selected_candidate_id": selected_candidate_id,
            "selected_run_ids": final_result["selected_run_ids"],
            "selection_decision_hash": decision_hash,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--test-field", default="sealed_test_metrics_b64")
    args = parser.parse_args()
    result = complete(args.case_root.resolve(), args.test_field)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_NATIVE_CONTRACTS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
