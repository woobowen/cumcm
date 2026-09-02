"""Prepare, seal and validate the independent Phase 002D-R2 Decision Audit."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    sha256_json,
)

from .adjudication import (
    DECISION_FILES,
    DECISION_ROOT,
    SHADOW_DECISION_ID,
    validate_decisions,
)
from .architecture_validator import validate_architecture_candidates
from .benchmark_integrity import validate_prospective_benchmark
from .component_validator import validate_component_specifications
from .implementation_embargo import verify_embargo
from .interaction_validator import validate_component_interactions
from .models import COMPONENT_IDS, CREATED_AT, RESULT_ROOT, verify_input_freeze
from .provenance_validator import PROVENANCE_ROOT, validate_clean_room_provenance
from .replay import REPLAY_PATH, validate_replay
from .threshold_validator import validate_thresholds
from .vault_manifest import check_benchmark_vault

BUNDLE_PATH = RESULT_ROOT / "decision_audit/input_bundle.json"
AUDIT_PATH = RESULT_ROOT / "decision_audit/audit.json"
RAW_AUDIT_PATH = RESULT_ROOT / "subagent_outputs/decision_auditor.json"
BUNDLE_ID = "PHASE-002D-R2-NATIVE-DECISION-AUDITOR"
AUDIT_ID = "DECISION-AUDIT-PHASE-002D-R2"
AUDITOR_CHECKS = (
    "historical_input_integrity",
    "decision_set_complete",
    "decision_hashes_and_contracts_valid",
    "component_specifications_frozen",
    "accepted_scope_boundaries",
    "single_state_truth",
    "single_formal_skill",
    "architecture_not_selected",
    "benchmark_prospective_and_leakage_safe",
    "vault_private_values_not_read",
    "thresholds_frozen_without_hindsight",
    "implementation_embargo_holds",
    "formal_skill_immutable",
    "clean_room_provenance_passes",
    "authors_disjoint_from_prosecutors",
    "no_third_party_copy_claimed_or_used",
    "all_serious_findings_closed_by_tests",
    "no_majority_vote",
    "no_human_technical_gate",
    "shadow_scope_strict",
    "shadow_retest_prerequisites_truthful",
    "phase003_prohibited",
    "next_route_matches_shadow_decision",
    "offline_replay_stable",
    "decision_order_permutation_stable",
    "evidence_order_permutation_stable",
    "target_label_permutation_stable",
    "seed_manifest_verification_stable",
    "no_model_api_or_prototype_execution",
)


def _decision_values(root: Path) -> list[dict[str, Any]]:
    return [
        read_json(root / DECISION_ROOT / DECISION_FILES[decision_id])
        for decision_id in sorted(DECISION_FILES)
    ]


def evaluate_audit_checks(root: Path) -> dict[str, bool]:
    decisions = _decision_values(root)
    by_id = {item["automated_decision"]["decision_id"]: item for item in decisions}
    shadow = by_id[SHADOW_DECISION_ID]
    authorization = shadow["authorization"]
    replay = read_json(root / REPLAY_PATH)
    provenance = validate_clean_room_provenance(root, check=True)
    role_chain = read_json(root / PROVENANCE_ROOT / "role_chain.json")
    contamination = read_json(root / PROVENANCE_ROOT / "contamination_scan.json")
    closure = read_json(root / RESULT_ROOT / "adversarial_findings/findings.json")
    expected_scopes = {
        "DECISION-COMPONENT-SPECIFICATION-FREEZE-002D-R2": "SPECIFICATION_FROZEN",
        "DECISION-INTERACTION-CONTRACT-002D-R2": "SPECIFICATION_FROZEN",
        "DECISION-ARCHITECTURE-CANDIDATE-SET-002D-R2": "CANDIDATE_SET_FROZEN",
        "DECISION-PROSPECTIVE-BENCHMARK-FREEZE-002D-R2": "BENCHMARK_FROZEN",
        "DECISION-THRESHOLD-POLICY-FREEZE-002D-R2": "POLICY_FROZEN",
        SHADOW_DECISION_ID: None,
    }
    vault = check_benchmark_vault(root)
    interaction = validate_component_interactions(root)
    architecture = validate_architecture_candidates(root)
    checks = {
        "historical_input_integrity": not verify_input_freeze(root),
        "decision_set_complete": set(by_id) == set(DECISION_FILES),
        "decision_hashes_and_contracts_valid": validate_decisions(root, decisions) == [],
        "component_specifications_frozen": (
            validate_component_specifications(root)["status"] == "PASS"
        ),
        "accepted_scope_boundaries": all(
            by_id[decision_id]["phase_scope"] == scope
            for decision_id, scope in expected_scopes.items()
        ),
        "single_state_truth": interaction["status"] == "PASS"
        and interaction["state_truth"] == "state/project_state.json",
        "single_formal_skill": all(
            candidate_id in architecture["candidate_ids"]
            for candidate_id in architecture["candidate_ids"]
        )
        and architecture["status"] == "PASS",
        "architecture_not_selected": architecture["selected_architecture"] is None
        and all(item["architecture_selected"] is False for item in decisions),
        "benchmark_prospective_and_leakage_safe": (
            validate_prospective_benchmark(root)["status"] == "PASS"
        ),
        "vault_private_values_not_read": vault["status"] == "PASS"
        and vault["private_values_read"] is False,
        "thresholds_frozen_without_hindsight": validate_thresholds(root)["status"] == "PASS",
        "implementation_embargo_holds": not verify_embargo(root),
        "formal_skill_immutable": not verify_input_freeze(root),
        "clean_room_provenance_passes": provenance["status"] == "PASS",
        "authors_disjoint_from_prosecutors": (role_chain["authors_disjoint_from_auditors"] is True),
        "no_third_party_copy_claimed_or_used": (
            contamination["restricted_copy_match_count"] == 0
            and all(item["formal_skill_modified"] is False for item in decisions)
        ),
        "all_serious_findings_closed_by_tests": all(
            item["status"] == "CLOSED" and item["unresolved"] is False
            for item in closure["findings"]
        ),
        "no_majority_vote": all(item["majority_vote_used"] is False for item in decisions),
        "no_human_technical_gate": all(
            item["human_technical_gate_used"] is False for item in decisions
        ),
        "shadow_scope_strict": authorization["accepted_scope"] is None
        and authorization["formal_skill_modification_allowed"] is False
        and authorization["prototype_execution_in_r2"] is False,
        "shadow_retest_prerequisites_truthful": (
            authorization["decision"] == "RETEST_REQUIRED"
            and authorization["prerequisites"]["decision_auditor"] is False
            and authorization["prerequisites"]["replay"] is False
        ),
        "phase003_prohibited": authorization["phase003_prohibited"] is True,
        "next_route_matches_shadow_decision": (
            authorization["next_phase_allowed"]
            == "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL"
        ),
        "offline_replay_stable": validate_replay(replay) == [] and replay["stable"] is True,
        "decision_order_permutation_stable": replay["variants"]["decision_order_permutation"],
        "evidence_order_permutation_stable": replay["variants"]["evidence_order_permutation"],
        "target_label_permutation_stable": replay["variants"]["target_label_permutation"],
        "seed_manifest_verification_stable": replay["variants"]["seed_manifest_verification"],
        "no_model_api_or_prototype_execution": all(
            replay[field] == 0
            for field in (
                "model_calls",
                "api_calls",
                "prototype_executions",
                "third_party_executions",
            )
        ),
    }
    if set(checks) != set(AUDITOR_CHECKS):
        raise ValueError("PHASE002D_R2_AUDITOR_CHECK_SET_MISMATCH")
    return checks


def _allowed_paths(root: Path) -> list[str]:
    paths = [
        "GOALS.md",
        "WORKFLOW.md",
        "rules/phase002d_r2_workflow_rules.yaml",
        "contracts/automated_decision.schema.json",
        "contracts/decision_audit.schema.json",
        "contracts/shadow_prototype_authorization.schema.json",
        "state/project_state.json",
        (RESULT_ROOT / "input_freeze_manifest.json").as_posix(),
        (RESULT_ROOT / "implementation_embargo.json").as_posix(),
        (RESULT_ROOT / "adversarial_findings/findings.json").as_posix(),
        (RESULT_ROOT / "test_requests/requests.json").as_posix(),
        (RESULT_ROOT / "test_evidence/evidence.json").as_posix(),
        REPLAY_PATH.as_posix(),
        "specifications/clean_room_provenance.yaml",
        "specifications/interactions/component_interaction_contract.yaml",
        "specifications/architectures/architecture_candidate_set.yaml",
        "evals/prospective/phase-002d-r2/benchmark_protocol.yaml",
        "evals/prospective/phase-002d-r2/sealed_manifest.json",
        "evals/prospective/phase-002d-r2/access_policy.yaml",
        "evals/prospective/phase-002d-r2/metric_registry.yaml",
        "evals/prospective/phase-002d-r2/threshold_policy.yaml",
        "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml",
        "evals/prospective/phase-002d-r2/ablation_policy.yaml",
        "evals/prospective/phase-002d-r2/budget_policy.yaml",
    ]
    paths.extend(f"specifications/components/{component_id}.yaml" for component_id in COMPONENT_IDS)
    paths.extend((DECISION_ROOT / filename).as_posix() for filename in DECISION_FILES.values())
    paths.extend(
        (PROVENANCE_ROOT / name).as_posix()
        for name in (
            "source_completeness.json",
            "role_chain.json",
            "role_access_ledger.json",
            "contamination_scan.json",
            "embargo_scan.json",
        )
    )
    missing = [path for path in paths if not (root / path).is_file()]
    if missing:
        raise ValueError(f"PHASE002D_R2_AUDITOR_INPUT_MISSING:{','.join(missing)}")
    return sorted(paths)


def build_auditor_bundle(root: Path) -> dict[str, Any]:
    paths = _allowed_paths(root)
    source_hashes = {path: file_sha256(root / path) for path in paths}
    evidence_hash = sha256_json(source_hashes)
    input_body = {
        "source_hashes": source_hashes,
        "required_checks": list(AUDITOR_CHECKS),
        "decision_ids": sorted(DECISION_FILES),
    }
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "bundle_id": BUNDLE_ID,
        "role": "DECISION_AUDITOR",
        "round": "FINAL_DECISION_AUDIT",
        "read_only": True,
        "peer_outputs_visible": False,
        "expected_conclusion_visible": False,
        "allowed_file_references": paths,
        "source_hashes": source_hashes,
        "input_bundle_hash": sha256_json(input_body),
        "policy_hash": file_sha256(root / "rules/phase002d_r2_workflow_rules.yaml"),
        "evidence_hash": evidence_hash,
        "decision_ids": sorted(DECISION_FILES),
        "required_checks": list(AUDITOR_CHECKS),
        "output_contract": "contracts/decision_audit.schema.json",
        "output_instruction": (
            "Return exactly one JSON object validating against the decision-audit contract. "
            "Copy bundle_id, bundle_hash, input_bundle_hash, policy_hash, evidence_hash and "
            "decision_ids from this bundle. Use checkpoint_hash as 64 zeros; the main agent "
            "will normalize only that hash. Determine every required check independently."
        ),
        "prohibitions": [
            "no file writes, commits, pushes or formal-state changes",
            "no web, MCP, API keys, nested Codex or third-party execution",
            "no hidden vault, benchmark answers, peer raw outputs or expected conclusion",
            "no majority vote, human technical override or fabricated evidence",
            "no model, prototype or model-in-loop protocol execution",
        ],
        "created_at": CREATED_AT,
    }
    return {**body, "bundle_hash": sha256_json(body)}


def check_or_write_auditor_bundle(root: Path, *, check: bool) -> dict[str, Any]:
    bundle = build_auditor_bundle(root)
    errors = check_or_write(root / BUNDLE_PATH, bundle, check=check)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "input_bundle_hash": bundle["input_bundle_hash"],
        "evidence_hash": bundle["evidence_hash"],
    }


def _seal_raw_audit(root: Path) -> dict[str, Any]:
    raw = deepcopy(read_json(root / RAW_AUDIT_PATH))
    body = dict(raw)
    body.pop("checkpoint_hash", None)
    raw["checkpoint_hash"] = sha256_json(body)
    return raw


def validate_audit(root: Path, audit: dict[str, Any]) -> list[str]:
    errors = [
        f"PHASE002D_R2_DECISION_AUDIT_SCHEMA:{item.message}"
        for item in Draft202012Validator(
            read_json(root / "contracts/decision_audit.schema.json")
        ).iter_errors(audit)
    ]
    bundle = build_auditor_bundle(root)
    for field in (
        "bundle_id",
        "bundle_hash",
        "input_bundle_hash",
        "policy_hash",
        "evidence_hash",
        "decision_ids",
    ):
        expected = bundle[field]
        if audit.get(field) != expected:
            errors.append(f"PHASE002D_R2_DECISION_AUDIT_BINDING_MISMATCH:{field}")
    body = dict(audit)
    checkpoint_hash = body.pop("checkpoint_hash", None)
    if sha256_json(body) != checkpoint_hash:
        errors.append("PHASE002D_R2_DECISION_AUDIT_CHECKPOINT_HASH_MISMATCH")
    deterministic_checks = evaluate_audit_checks(root)
    if set(audit.get("checks", {})) != set(AUDITOR_CHECKS):
        errors.append("PHASE002D_R2_DECISION_AUDIT_CHECK_SET_MISMATCH")
    if audit.get("checks") != deterministic_checks:
        errors.append("PHASE002D_R2_DECISION_AUDIT_DISAGREES_WITH_DETERMINISTIC_EVIDENCE")
    if audit.get("result") == "PASS" and (
        not all(deterministic_checks.values())
        or audit.get("failures")
        or audit.get("blockers")
        or audit.get("replayable") is not True
    ):
        errors.append("PHASE002D_R2_DECISION_AUDIT_FALSE_PASS")
    return sorted(set(errors))


def check_or_write_decision_audit(root: Path, *, check: bool) -> dict[str, Any]:
    bundle_errors = check_or_write(root / BUNDLE_PATH, build_auditor_bundle(root), check=check)
    if not (root / RAW_AUDIT_PATH).is_file():
        return {
            "status": "FAIL",
            "errors": [*bundle_errors, "PHASE002D_R2_RAW_DECISION_AUDIT_MISSING"],
            "audit_id": None,
            "result": None,
        }
    audit = _seal_raw_audit(root)
    errors = [*bundle_errors, *validate_audit(root, audit)]
    errors.extend(check_or_write(root / AUDIT_PATH, audit, check=check))
    return {
        "status": "PASS" if not errors and audit["result"] == "PASS" else "FAIL",
        "errors": sorted(set(errors)),
        "audit_id": audit.get("audit_id"),
        "result": audit.get("result"),
        "checkpoint_hash": audit.get("checkpoint_hash"),
    }


__all__ = [
    "AUDIT_ID",
    "AUDIT_PATH",
    "AUDITOR_CHECKS",
    "BUNDLE_PATH",
    "RAW_AUDIT_PATH",
    "build_auditor_bundle",
    "check_or_write_auditor_bundle",
    "check_or_write_decision_audit",
    "evaluate_audit_checks",
    "validate_audit",
]
