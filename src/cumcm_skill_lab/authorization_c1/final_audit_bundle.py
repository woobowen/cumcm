"""Build and validate the exact-candidate L8 final-audit bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from cumcm_skill_lab.historical_compat import (
    competition_rc_successor,
    git_repository_file_hashes,
)
from cumcm_skill_lab.specification.authorization.models import repository_file_hashes, tree_hash
from cumcm_skill_lab.specification.implementation_embargo import verify_embargo

from .candidate_evidence import (
    CLOSURE_PATH,
    POST_EVIDENCE_PROSECUTOR_PATH,
    PRECONDITIONS_PATH,
    TEST_EVIDENCE_PATH,
    TEST_PLAN_PATH,
    candidate_binding,
    validate_bound_artifact,
    validate_candidate_evidence_chain,
    validate_exact_candidate_bundle,
)
from .candidate_freeze import CANDIDATE_PATH, FREEZE_PATH, validate_candidate_freeze
from .input_freeze import validate_input_freeze
from .models import INPUT_FREEZE_PATH, RESULT_ROOT, check_or_write_json, file_sha256, sha256_json

BUNDLE_PATH = RESULT_ROOT / "final_audit_bundle/bundle-c1.json"
R2_DECISION_PATHS = (
    "evals/results/phase-002d-r2/automated_decisions/component_specification_freeze.json",
    "evals/results/phase-002d-r2/automated_decisions/interaction_contract.json",
    "evals/results/phase-002d-r2/automated_decisions/architecture_candidate_set.json",
    "evals/results/phase-002d-r2/automated_decisions/prospective_benchmark_freeze.json",
    "evals/results/phase-002d-r2/automated_decisions/threshold_policy_freeze.json",
)
R2_AUDIT_PATH = "evals/results/phase-002d-r2/decision_audit/audit.json"
R2_REPLAY_PATH = "evals/results/phase-002d-r2/replay/replay.json"
R2_EMBARGO_PATH = "evals/results/phase-002d-r2/implementation_embargo.json"
DEPENDENCY_PATH = "evals/results/phase-002d-r2a/authorization_dependency_graph.json"
SCOPE_PATH = "specifications/shadow_prototype_scope.yaml"
HISTORICAL_PATH = RESULT_ROOT / "historical_verification/record.json"
SCHEMA_PATH = RESULT_ROOT / "schema_resolution/record.json"
COMPATIBILITY_PATH = RESULT_ROOT / "compatibility_tests/closure.json"
AUDIT_OUTPUT_PATHS = (
    RESULT_ROOT / "subagent_outputs/historical_freeze_semantics_auditor.json",
    RESULT_ROOT / "subagent_outputs/schema_version_compatibility_auditor.json",
    RESULT_ROOT / "subagent_outputs/candidate_binding_prosecutor.json",
    POST_EVIDENCE_PROSECUTOR_PATH,
)
ALLOWED_PATHS = (
    CANDIDATE_PATH.as_posix(),
    FREEZE_PATH.as_posix(),
    PRECONDITIONS_PATH.as_posix(),
    TEST_PLAN_PATH.as_posix(),
    TEST_EVIDENCE_PATH.as_posix(),
    CLOSURE_PATH.as_posix(),
    INPUT_FREEZE_PATH.as_posix(),
    HISTORICAL_PATH.as_posix(),
    SCHEMA_PATH.as_posix(),
    COMPATIBILITY_PATH.as_posix(),
    DEPENDENCY_PATH,
    SCOPE_PATH,
    *R2_DECISION_PATHS,
    R2_AUDIT_PATH,
    R2_REPLAY_PATH,
    R2_EMBARGO_PATH,
    *(path.as_posix() for path in AUDIT_OUTPUT_PATHS),
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"C1_FINAL_BUNDLE_YAML_OBJECT_REQUIRED:{path.as_posix()}")
    return value


def _prerequisite_errors(root: Path) -> list[str]:
    errors: list[str] = []
    freeze = _read_json(root / FREEZE_PATH)
    errors.extend(validate_candidate_freeze(root, freeze))
    errors.extend(validate_candidate_evidence_chain(root))
    input_freeze = _read_json(root / INPUT_FREEZE_PATH)
    errors.extend(validate_input_freeze(root, input_freeze))
    historical = _read_json(root / HISTORICAL_PATH)
    schema = _read_json(root / SCHEMA_PATH)
    compatibility = _read_json(root / COMPATIBILITY_PATH)
    closure = _read_json(root / CLOSURE_PATH)
    if historical.get("result") != "PASS":
        errors.append("C1_FINAL_BUNDLE_HISTORICAL_COMPATIBILITY_NOT_PASS")
    if schema.get("result") != "PASS":
        errors.append("C1_FINAL_BUNDLE_SCHEMA_COMPATIBILITY_NOT_PASS")
    if compatibility.get("result") != "PASS" or compatibility.get(
        "unresolved_compatibility_blockers"
    ):
        errors.append("C1_FINAL_BUNDLE_COMPATIBILITY_CLOSURE_NOT_PASS")
    if closure.get("result") != "PASS" or closure.get("unresolved_findings"):
        errors.append("C1_FINAL_BUNDLE_CANDIDATE_CLOSURE_NOT_PASS")
    if not closure.get("candidate_prosecutor_review", {}).get("serious_findings_closed"):
        errors.append("C1_FINAL_BUNDLE_PROSECUTOR_FINDINGS_NOT_CLOSED")
    errors.extend(verify_embargo(root))
    skill_hash = tree_hash(
        git_repository_file_hashes(root, (Path(".agents/skills/cumcm-modeling-evidence"),))
        if competition_rc_successor(root)
        else repository_file_hashes(root, (Path(".agents/skills/cumcm-modeling-evidence"),))
    )
    if skill_hash != input_freeze["protected_bindings"]["formal_skill_tree_hash"]:
        errors.append("C1_FINAL_BUNDLE_FORMAL_SKILL_HASH_CHANGED")
    for path in R2_DECISION_PATHS:
        if _read_json(root / path)["automated_decision"]["decision"] != "AUTOMATED_ACCEPTED":
            errors.append(f"C1_FINAL_BUNDLE_R2_DECISION_NOT_PASS:{path}")
    if _read_json(root / R2_AUDIT_PATH).get("result") != "PASS":
        errors.append("C1_FINAL_BUNDLE_R2_AUDIT_NOT_PASS")
    if _read_json(root / R2_REPLAY_PATH).get("stable") is not True:
        errors.append("C1_FINAL_BUNDLE_R2_REPLAY_NOT_STABLE")
    scope = _read_yaml(root / SCOPE_PATH)
    if (
        scope.get("selected_architecture") is not None
        or scope.get("implementation_created") is not False
        or scope.get("prototype_executed") is not False
        or scope.get("phase003_prohibited") is not True
    ):
        errors.append("C1_FINAL_BUNDLE_SCOPE_BOUNDARY_INVALID")
    return sorted(set(errors))


def build_final_audit_bundle(root: Path) -> dict[str, Any]:
    input_freeze = _read_json(root / INPUT_FREEZE_PATH)
    freeze = _read_json(root / FREEZE_PATH)
    preconditions = _read_json(root / PRECONDITIONS_PATH)
    plan = _read_json(root / TEST_PLAN_PATH)
    evidence = _read_json(root / TEST_EVIDENCE_PATH)
    closure = _read_json(root / CLOSURE_PATH)
    graph = _read_json(root / DEPENDENCY_PATH)
    scope = _read_yaml(root / SCOPE_PATH)
    historical = _read_json(root / HISTORICAL_PATH)
    schema = _read_json(root / SCHEMA_PATH)
    compatibility = _read_json(root / COMPATIBILITY_PATH)
    r2_replay = _read_json(root / R2_REPLAY_PATH)
    r2_decisions = {
        Path(path).stem: _read_json(root / path)["decision_hash"] for path in R2_DECISION_PATHS
    }
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "bundle_id": "PHASE-002D-R2A-C1-FINAL-SHADOW-AUTHORIZATION-AUDIT-BUNDLE-001",
        **candidate_binding(freeze),
        "candidate_path": CANDIDATE_PATH.as_posix(),
        "parent_artifact_hash": closure["closure_hash"],
        "artifact_sequence_index": 9,
        "input_freeze_hash": input_freeze["manifest_hash"],
        "dependency_graph_hash": graph["graph_hash"],
        "preconditions_hash": preconditions["preconditions_hash"],
        "test_plan_hash": plan["test_plan_hash"],
        "test_evidence_set_hash": evidence["evidence_hash"],
        "test_evidence_hashes": evidence["test_evidence_hashes"],
        "closure_hash": closure["closure_hash"],
        "scope_hash": scope["scope_hash"],
        "r2_prerequisite_decision_hashes": r2_decisions,
        "r2_audit_file_sha256": file_sha256(root / R2_AUDIT_PATH),
        "r2_replay_hash": r2_replay["replay_hash"],
        "historical_compatibility_record_hash": historical["record_hash"],
        "schema_resolution_record_hash": schema["record_hash"],
        "compatibility_closure_hash": compatibility["closure_hash"],
        "implementation_embargo_file_sha256": file_sha256(root / R2_EMBARGO_PATH),
        "formal_skill_tree_hash": input_freeze["protected_bindings"]["formal_skill_tree_hash"],
        "predecessor_audit_output_hashes": {
            path.stem: _read_json(root / path)["output_hash"] for path in AUDIT_OUTPUT_PATHS
        },
        "unresolved_findings": [],
        "allowed_paths": list(ALLOWED_PATHS),
        "path_hashes": {path: file_sha256(root / path) for path in ALLOWED_PATHS},
        "review_requirements": [
            "EXACT_CANDIDATE_BYTE_BINDING",
            "CANONICAL_HASH_BINDING",
            "EVIDENCE_TEMPORAL_HASH_ORDER",
            "WRONG_CANDIDATE_EVIDENCE",
            "HISTORY_MUTATION",
            "SCHEMA_VERSION_MISMATCH",
            "DEPENDENCY_CYCLE",
            "SCOPE_CREEP",
            "HIDDEN_VAULT_LEAKAGE",
            "FORMAL_SKILL_MODIFICATION",
            "PROTOTYPE_IMPLEMENTATION",
            "ARCHITECTURE_SELECTION",
            "PHASE_003_ROUTE",
            "THIRD_PARTY_INTEGRATION",
            "MAJORITY_VOTE",
            "HARDCODED_DECISION",
            "UNRESOLVED_FINDING",
            "REPLAY_PREREQUISITES",
        ],
        "constraints": {
            "read_only": True,
            "peer_output_access": "FROZEN_PREDECESSORS_ONLY",
            "writes_allowed": False,
            "nested_codex_allowed": False,
            "web_allowed": False,
            "mcp_allowed": False,
            "api_allowed": False,
            "majority_vote_allowed": False,
            "expected_conclusion_visible": False,
            "abstention_allowed": False,
            "allowed_verdicts": ["PASS", "FAIL", "RETEST_REQUIRED"],
        },
    }
    body["bundle_hash"] = sha256_json(body)
    return body


def validate_final_audit_bundle(root: Path, value: dict[str, Any]) -> list[str]:
    errors = _prerequisite_errors(root)
    freeze = _read_json(root / FREEZE_PATH)
    closure = _read_json(root / CLOSURE_PATH)
    errors.extend(
        validate_bound_artifact(
            value,
            freeze,
            expected_parent=closure["closure_hash"],
            expected_sequence=9,
            hash_field="bundle_hash",
        )
    )
    errors.extend(
        validate_exact_candidate_bundle(value, (root / CANDIDATE_PATH).read_bytes(), freeze)
    )
    for path in value.get("allowed_paths", []):
        target = root / path
        if not target.is_file() or value.get("path_hashes", {}).get(path) != file_sha256(target):
            errors.append(f"C1_FINAL_BUNDLE_PATH_HASH_MISMATCH:{path}")
    if value != build_final_audit_bundle(root):
        errors.append("C1_FINAL_BUNDLE_NOT_REPRODUCIBLE")
    return sorted(set(errors))


def check_or_write_final_audit_bundle(root: Path, *, check: bool) -> dict[str, Any]:
    bundle = build_final_audit_bundle(root)
    errors = _prerequisite_errors(root)
    errors.extend(check_or_write_json(root / BUNDLE_PATH, bundle, check=check))
    if not errors:
        errors.extend(validate_final_audit_bundle(root, _read_json(root / BUNDLE_PATH)))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "candidate_id": bundle["candidate_id"],
        "candidate_file_sha256": bundle["candidate_file_sha256"],
        "canonical_candidate_hash": bundle["canonical_candidate_hash"],
        "candidate_freeze_hash": bundle["candidate_freeze_hash"],
        "artifact_sequence_index": bundle["artifact_sequence_index"],
    }


__all__ = [
    "ALLOWED_PATHS",
    "BUNDLE_PATH",
    "build_final_audit_bundle",
    "check_or_write_final_audit_bundle",
    "validate_final_audit_bundle",
]
