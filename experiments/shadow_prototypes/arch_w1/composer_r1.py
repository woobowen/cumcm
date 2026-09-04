"""Candidate-owned W1-R1 workflow composition without formal state authority."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import sha256_json, thaw

from .revision_r1 import R1_GUARDS, REVISION_ID, _state_boundary_reasons

REPRODUCIBILITY = "hash-bound-reproducibility-manifest"
COMPARISON = "leakage-safe-model-comparison-gate"
CLAIM = "claim-evidence-support-gate"
LIFECYCLE = "accepted-versus-done-workflow-state"
PIPELINE = (REPRODUCIBILITY, COMPARISON, CLAIM, LIFECYCLE)
DIRECT_DEPENDENT = {
    REPRODUCIBILITY: COMPARISON,
    COMPARISON: CLAIM,
    CLAIM: LIFECYCLE,
}
PACKAGE_FIELDS = frozenset(
    {
        "contract_version",
        "problem_requirements",
        "requirement_traceability",
        "data_dictionary",
        "data_quality_report",
        "assumptions",
        "symbols",
        "formulas",
        "sources",
        "selected_models",
        "final_runs",
        "final_metrics",
        "result_tables",
        "figure_ready_data",
        "validation_results",
        "robustness_results",
        "uncertainty",
        "failure_cases",
        "limitations",
        "claim_evidence",
        "reproduction",
        "generated_at",
        "approved_by",
    }
)


def _component_result(
    status: str,
    reasons: tuple[str, ...] | list[str],
    *,
    dependency_chain: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "status": status,
        "reason_codes": sorted(set(reasons)),
        "dependency_chain": list(dependency_chain),
    }


def _propagate_stale(component_results: dict[str, dict[str, Any]], source: str) -> None:
    chain = [source]
    current = source
    while current in DIRECT_DEPENDENT:
        current = DIRECT_DEPENDENT[current]
        chain.append(current)
        if component_results[current]["status"] == "PASS":
            component_results[current] = _component_result(
                "STALE",
                ["W1_R1_COMPOSITION_UPSTREAM_STALE"],
                dependency_chain=tuple(chain),
            )


def _cross_component_reasons(
    component_payloads: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> list[str]:
    reasons: list[str] = []
    repro_payload = component_payloads.get(REPRODUCIBILITY)
    claim_payload = component_payloads.get(CLAIM)
    workflow_payload = component_payloads.get(LIFECYCLE)
    if not all(
        isinstance(item, Mapping) for item in (repro_payload, claim_payload, workflow_payload)
    ):
        return ["W1_R1_COMPOSITION_COMPONENT_PAYLOAD_INVALID"]
    manifest = repro_payload.get("manifest")
    claim = claim_payload.get("claim")
    verified = claim_payload.get("verified_run_manifest")
    if not all(isinstance(item, Mapping) for item in (manifest, claim, verified)):
        return ["W1_R1_COMPOSITION_RUN_RECORD_INVALID"]
    if any(
        manifest.get(manifest_field) != claim.get(claim_field)
        for manifest_field, claim_field in (
            ("run_id", "run_id"),
            ("input_hash", "input_hash"),
            ("code_commit", "code_commit"),
            ("output_hash", "output_hash"),
        )
    ):
        reasons.append("W1_R1_COMPOSITION_RUN_BINDING_MISMATCH")
    if verified.get("run_id") != manifest.get("run_id"):
        reasons.append("W1_R1_COMPOSITION_VERIFIED_RUN_ID_MISMATCH")
    trusted_manifest_hashes = isolated_state.get("trusted_repro_manifest_hashes", {})
    manifest_hash = sha256_json(manifest)
    if (
        not isinstance(trusted_manifest_hashes, Mapping)
        or trusted_manifest_hashes.get(manifest.get("run_id")) != manifest_hash
    ):
        reasons.append("W1_R1_COMPOSITION_MANIFEST_HASH_UNTRUSTED")
    decision_id = verified.get("decision_id")
    decision_hash = verified.get("decision_hash", verified.get("artifact_hash"))
    if not isinstance(decision_id, str) or not decision_id:
        reasons.append("W1_R1_COMPOSITION_DECISION_ID_MISSING")
    if not isinstance(decision_hash, str) or len(decision_hash) != 64:
        reasons.append("W1_R1_COMPOSITION_DECISION_HASH_MISSING")
    evidence = claim_payload.get("evidence")
    if not isinstance(evidence, (list, tuple)) or not evidence:
        reasons.append("W1_R1_COMPOSITION_EVIDENCE_MISSING")
    else:
        for item in evidence:
            if not isinstance(item, Mapping) or any(
                item.get(field) != claim.get(field)
                for field in ("run_id", "input_hash", "code_commit", "output_hash")
            ):
                reasons.append("W1_R1_COMPOSITION_EVIDENCE_RUN_BINDING_MISMATCH")
                break
    records = workflow_payload.get("evidence_records")
    if not isinstance(records, Mapping) or any(
        not isinstance(record, Mapping)
        or not isinstance(record.get("artifact_body"), Mapping)
        or record["artifact_body"].get("run_id") != manifest.get("run_id")
        for record in records.values()
    ):
        reasons.append("W1_R1_COMPOSITION_LIFECYCLE_RUN_BINDING_MISMATCH")
    return reasons


def _package(
    component_payloads: Mapping[str, Any],
    component_results: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    repro_payload = component_payloads[REPRODUCIBILITY]
    comparison_payload = component_payloads[COMPARISON]
    claim_payload = component_payloads[CLAIM]
    manifest = repro_payload["manifest"]
    claim = claim_payload["claim"]
    verified = claim_payload["verified_run_manifest"]
    evidence = claim_payload["evidence"]
    attempts = comparison_payload["attempts"]
    failed_attempts = [item for item in attempts if item.get("outcome") != "SUCCESS"]
    decision_hash = verified.get("decision_hash", verified["artifact_hash"])
    manifest_hash = sha256_json(manifest)
    package: dict[str, Any] = {
        "contract_version": "modeling-to-paper/v1",
        "problem_requirements": [
            {"requirement_id": component_id, "status": "MACHINE_GATE_PASS"}
            for component_id in COMPONENT_IDS
        ],
        "requirement_traceability": {
            component_id: {
                "status": component_results[component_id]["status"],
                "run_id": manifest["run_id"],
            }
            for component_id in COMPONENT_IDS
        },
        "data_dictionary": {},
        "data_quality_report": {
            "status": "WORKFLOW_PROPOSAL_ONLY",
            "input_hash": manifest["input_hash"],
        },
        "assumptions": [],
        "symbols": {},
        "formulas": [],
        "sources": [],
        "selected_models": [
            {
                "candidate_id": comparison_payload["selected_candidate_id"],
                "selection_policy": {
                    "metric_direction": comparison_payload["metric_direction"],
                    "tie_tolerance": comparison_payload["tie_tolerance"],
                },
            }
        ],
        "final_runs": [
            {
                "run_id": manifest["run_id"],
                "run_manifest_hash": manifest_hash,
                "input_hash": manifest["input_hash"],
                "code_hash": manifest["code_commit"],
                "configuration_hash": manifest["config_hash"],
                "output_hash": manifest["output_hash"],
                "decision_id": verified["decision_id"],
                "decision_hash": decision_hash,
                "current": manifest["current"],
                "outcome": manifest["outcome"],
            }
        ],
        "final_metrics": thaw(comparison_payload["validation_scores"]),
        "result_tables": [],
        "figure_ready_data": [],
        "validation_results": {
            component_id: component_results[component_id]["status"]
            for component_id in COMPONENT_IDS
        },
        "robustness_results": {
            "attempt_count": len(attempts),
            "frozen_seeds": thaw(comparison_payload["frozen_seeds"]),
        },
        "uncertainty": {"status": "NOT_ESTABLISHED_BY_SHADOW_WORKFLOW"},
        "failure_cases": thaw(failed_attempts),
        "limitations": [
            "WORKFLOW_ONLY_PROPOSAL",
            "FORMAL_ACCEPTANCE_REQUIRES_ORCHESTRATOR_GATE",
        ],
        "claim_evidence": {
            "claim_id": claim["claim_id"],
            "run_id": claim["run_id"],
            "output_hash": claim["output_hash"],
            "evidence_artifact_ids": [item["evidence_id"] for item in evidence],
        },
        "reproduction": {
            "revision_id": REVISION_ID,
            "run_id": manifest["run_id"],
            "run_manifest_hash": manifest_hash,
            "command": thaw(manifest["command"]),
            "cwd_policy": manifest["cwd"],
            "environment_hash": manifest["environment_hash"],
            "dependency_hash": manifest["dependency_hash"],
            "output_hash": manifest["output_hash"],
            "decision_hash": decision_hash,
        },
        "generated_at": generated_at,
        "approved_by": ["MACHINE_TECHNICAL_GATE:W1_R1_COMPONENT_COMPOSITION"],
    }
    if set(package) != PACKAGE_FIELDS:
        raise ValueError("W1_R1_INTERNAL_PACKAGE_FIELD_MISMATCH")
    return package


def compose_evidence_package(
    component_payloads: Any,
    isolated_state: Any,
    *,
    generated_at: str = "1970-01-01T00:00:00Z",
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    """Evaluate all W1 checklists and emit a contract-shaped proposal when coherent."""
    global_reasons = _state_boundary_reasons(isolated_state)
    if not isinstance(component_payloads, Mapping):
        global_reasons.append("W1_R1_COMPOSITION_PAYLOAD_SET_INVALID")
    elif set(component_payloads) != set(COMPONENT_IDS):
        global_reasons.append("W1_R1_COMPOSITION_COMPONENT_SET_INVALID")
    if not isinstance(generated_at, str) or not generated_at:
        global_reasons.append("W1_R1_COMPOSITION_GENERATED_AT_INVALID")
    component_results = {
        component_id: _component_result(
            "BLOCK",
            ["W1_R1_COMPOSITION_NOT_EVALUATED"],
        )
        for component_id in COMPONENT_IDS
    }
    if not global_reasons:
        for component_id in PIPELINE:
            passed, reasons, _ = R1_GUARDS[component_id](
                component_payloads[component_id], isolated_state
            )
            status = (
                "PASS"
                if passed
                else ("STALE" if any("STALE" in item for item in reasons) else "BLOCK")
            )
            component_results[component_id] = _component_result(status, reasons)
        if all(item["status"] == "PASS" for item in component_results.values()):
            cross_reasons = _cross_component_reasons(component_payloads, isolated_state)
            if cross_reasons:
                component_results[CLAIM] = _component_result("BLOCK", cross_reasons)
        for component_id in PIPELINE:
            if component_results[component_id]["status"] != "PASS":
                _propagate_stale(component_results, component_id)
    all_passed = not global_reasons and all(
        component_results[component_id]["status"] == "PASS" for component_id in COMPONENT_IDS
    )
    reasons = list(global_reasons)
    for component_id in PIPELINE:
        reasons.extend(
            f"{component_id}:{reason}" for reason in component_results[component_id]["reason_codes"]
        )
    if all_passed:
        evidence_package = _package(
            component_payloads,
            component_results,
            generated_at=generated_at,
        )
        composition_status = "PROPOSAL_READY"
    else:
        evidence_package = {}
        composition_status = "REJECTED"
        if not reasons:
            reasons.append("W1_R1_COMPOSITION_REJECTED")
    diagnostics = {
        "revision_id": REVISION_ID,
        "composition_status": composition_status,
        "accepted": False,
        "final": False,
        "ready_for_paper": False,
        "formal_state_writes": 0,
        "state_truth_sources": 1,
        "component_results": component_results,
        "dependency_chain": max(
            (
                result["dependency_chain"]
                for result in component_results.values()
                if result["dependency_chain"]
            ),
            key=len,
            default=[],
        ),
        "evidence_package": evidence_package,
        "evidence_package_hash": sha256_json(evidence_package),
    }
    return all_passed, tuple(sorted(set(reasons))), diagnostics


__all__ = ["PACKAGE_FIELDS", "PIPELINE", "compose_evidence_package"]
