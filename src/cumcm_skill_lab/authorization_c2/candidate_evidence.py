"""Build post-freeze exact-candidate preconditions, mutation evidence, and closure."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from cumcm_skill_lab.authorization_c1.compatibility_audits import normalize_audit, validate_audit
from cumcm_skill_lab.authorization_c1.dependency_c2 import (
    R2_AUDIT_PATH,
    R2_REPLAY_PATH,
    validate_audit_replay_order,
    validate_dependency_resolution,
)
from cumcm_skill_lab.authorization_c1.models import (
    INPUT_FREEZE_PATH,
    RESULT_ROOT,
    check_or_write_json,
    file_sha256,
    sha256_bytes,
    sha256_json,
)
from cumcm_skill_lab.specification.authorization.models import repository_file_hashes, tree_hash
from cumcm_skill_lab.specification.implementation_embargo import (
    r3_shadow_authorized,
    verify_embargo,
)

from .candidate_freeze import (
    CANDIDATE_ID,
    CANDIDATE_PATH,
    FREEZE_PATH,
    canonical_candidate_hash,
    frozen_revision_rewrite_errors,
    validate_candidate,
    validate_candidate_freeze,
)

PRECONDITIONS_PATH = RESULT_ROOT / "candidate_preconditions/preconditions-c2.json"
TEST_PLAN_PATH = RESULT_ROOT / "candidate_test_plan/test-plan-c2.json"
TEST_EVIDENCE_PATH = RESULT_ROOT / "candidate_test_evidence/evidence-c2.json"
CLOSURE_PATH = RESULT_ROOT / "candidate_closure/closure-c2.json"
POST_EVIDENCE_PROSECUTOR_RAW_PATH = (
    RESULT_ROOT / "subagent_outputs/raw/candidate_binding_prosecutor-post-evidence-c2.json"
)
POST_EVIDENCE_PROSECUTOR_PATH = (
    RESULT_ROOT / "subagent_outputs/candidate_binding_prosecutor-post-evidence-c2.json"
)
HISTORICAL_TEST_CODE_HASH = "74adcb5730aa05dc81a24a460c8a52508efb6bcdd45d6ea739f2e120871dbe81"
DEPENDENCY_RESOLUTION_PATH = RESULT_ROOT / "dependency_resolution/dependency-graph-c2.json"
C1_FINAL_AUDIT_PATH = RESULT_ROOT / "final_audit/audit-c1.json"
BINDING_FIELDS = (
    "candidate_id",
    "candidate_file_sha256",
    "canonical_candidate_hash",
    "candidate_freeze_hash",
    "parent_artifact_hash",
    "artifact_sequence_index",
)
R2_DECISION_PATHS = (
    "component_specification_freeze",
    "interaction_contract",
    "architecture_candidate_set",
    "prospective_benchmark_freeze",
    "threshold_policy_freeze",
)
MUTATION_SPECS = (
    ("C2-MUT-001", "CANDIDATE_BYTE_MUTATION", "$bytes", "C2_BOUND_CANDIDATE_FILE_SHA256_MISMATCH"),
    (
        "C2-MUT-002",
        "CANONICAL_SEMANTIC_MUTATION",
        "accepted_scope",
        "C2_BOUND_CANONICAL_CANDIDATE_HASH_MISMATCH",
    ),
    ("C2-MUT-003", "CANDIDATE_ID_MUTATION", "candidate_id", "C2_CANDIDATE_ID_MISMATCH"),
    (
        "C2-MUT-004",
        "ACCEPTED_SCOPE_MUTATION",
        "accepted_scope",
        "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH",
    ),
    (
        "C2-MUT-005",
        "NEXT_PHASE_MUTATION",
        "next_phase_allowed",
        "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH",
    ),
    (
        "C2-MUT-006",
        "ARCHITECTURE_SELECTION",
        "selected_architecture",
        "C2_CANDIDATE_ARCHITECTURE_SELECTION_PROHIBITED",
    ),
    ("C2-MUT-007", "BASE_SELECTION", "base_selected", "C2_CANDIDATE_FORMAL_INTEGRATION_PROHIBITED"),
    (
        "C2-MUT-008",
        "THIRD_PARTY_INTEGRATION",
        "third_party_integrated",
        "C2_CANDIDATE_FORMAL_INTEGRATION_PROHIBITED",
    ),
    (
        "C2-MUT-009",
        "FORMAL_INTEGRATION_SCOPE",
        "restrictions",
        "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH",
    ),
    (
        "C2-MUT-010",
        "PHASE_003_ROUTE",
        "next_phase_allowed",
        "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH",
    ),
    ("C2-MUT-011", "HIDDEN_VAULT_ACCESS", "restrictions", "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH"),
    ("C2-MUT-012", "FORMAL_SKILL_WRITE", "restrictions", "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH"),
    (
        "C2-MUT-013",
        "PROTOTYPE_AUTO_DISCOVERY",
        "formal_skill_auto_discovery",
        "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH",
    ),
    ("C2-MUT-014", "MISSING_SUPERSEDES", "supersedes", "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH"),
    (
        "C2-MUT-015",
        "WRONG_SUPERSEDES",
        "supersedes.decision_id",
        "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH",
    ),
    (
        "C2-MUT-016",
        "CANDIDATE_HASH_MISMATCH",
        "candidate_file_sha256",
        "C2_BOUND_CANDIDATE_FILE_SHA256_MISMATCH",
    ),
    (
        "C2-MUT-017",
        "EVIDENCE_BOUND_TO_OLD_CANDIDATE",
        "candidate_id",
        "C2_BOUND_CANDIDATE_ID_MISMATCH",
    ),
    (
        "C2-MUT-018",
        "EVIDENCE_PREDATES_FREEZE",
        "artifact_sequence_index",
        "C2_BOUND_ARTIFACT_SEQUENCE_MISMATCH",
    ),
    (
        "C2-MUT-019",
        "PARENT_HASH_MISMATCH",
        "parent_artifact_hash",
        "C2_BOUND_PARENT_ARTIFACT_HASH_MISMATCH",
    ),
    (
        "C2-MUT-020",
        "SEQUENCE_INDEX_INVERSION",
        "artifact_sequence_index",
        "C2_BOUND_ARTIFACT_SEQUENCE_MISMATCH",
    ),
    (
        "C2-MUT-021",
        "AUDIT_BUNDLE_DIFFERENT_CANDIDATE_BYTES",
        "candidate_file_sha256",
        "C2_BOUND_CANDIDATE_FILE_SHA256_MISMATCH",
    ),
    (
        "C2-MUT-022",
        "REPORT_HARDCODED_ACCEPT",
        "decision_source",
        "C2_REPORT_DECISION_SOURCE_NOT_INPUT_DRIVEN",
    ),
    (
        "C2-MUT-023",
        "CANDIDATE_SELF_HASH_REFERENCE",
        "candidate_file_sha256",
        "C2_CANDIDATE_SELF_HASH_FIELD_PROHIBITED:candidate_file_sha256",
    ),
    (
        "C2-MUT-024",
        "UNKNOWN_FIELD_RETENTION",
        "unknown_attack_field",
        "C2_BOUND_CANONICAL_CANDIDATE_HASH_MISMATCH",
    ),
    (
        "C2-MUT-025",
        "STATE_BINDING_SUBSTITUTION",
        "candidate_file_sha256",
        "C2_BOUND_CANDIDATE_FILE_SHA256_MISMATCH",
    ),
    (
        "C2-MUT-026",
        "STATE_PHASE_003_ROUTE",
        "next_phase_allowed",
        "C2_STATE_ROUTE_INVALID",
    ),
    (
        "C2-MUT-027",
        "FROZEN_CANDIDATE_REWRITE",
        "$bytes",
        "C2_FROZEN_CANDIDATE_REWRITE_PROHIBITED",
    ),
    (
        "C2-MUT-028",
        "REHASHED_FAILED_PRECONDITION",
        "all_required_pass",
        "C2_PRECONDITIONS_SEMANTIC_FAILURE",
    ),
    (
        "C2-MUT-029",
        "POSTFREEZE_EMBARGO_VIOLATION",
        "embargo_errors",
        "C2_POSTFREEZE_EMBARGO_NOT_PASS",
    ),
    (
        "C2-MUT-030",
        "CLOSURE_CLAIM_MISMATCH",
        "closures",
        "C2_CLOSURE_REQUIRED_EVIDENCE_MISMATCH",
    ),
    (
        "C1-DET-R2-AUDIT-REPLAY-ACYCLIC-PREREQUISITE-001",
        "R2_AUDIT_REPLAY_DEPENDENCY_INVERSION",
        "corrected_graph.edges",
        "C1_R2_AUDIT_REPLAY_SEMANTIC_CYCLE",
    ),
)
FINDING_TESTS = {
    "C1-CBP-001": ["C2-MUT-016", "C2-MUT-018", "C2-MUT-019", "C2-MUT-020", "C2-MUT-027"],
    "C1-CBP-002": ["C2-MUT-001", "C2-MUT-002", "C2-MUT-021"],
    "C1-CBP-003": ["C2-MUT-023", "C2-MUT-024"],
    "C1-CBP-004": ["C2-MUT-017", "C2-MUT-018"],
    "C1-CBP-005": ["C2-MUT-019", "C2-MUT-020"],
    "C1-CBP-006": ["C2-MUT-025", "C2-MUT-026"],
    "R2A-FINAL-002": ["C2-MUT-001", "C2-MUT-002", "C2-MUT-021"],
    "C1-CBP-M6-001": ["C2-MUT-027"],
    "C1-CBP-M6-002": ["C2-MUT-001", "C2-MUT-021"],
    "C1-CBP-M6-003": ["C2-MUT-009", "C2-MUT-022"],
    "C1-CBP-M6-004": ["C2-MUT-028"],
    "C1-CBP-M6-005": ["C2-MUT-029"],
    "C1-CBP-M6-006": ["C2-MUT-023", "C2-MUT-024", "C2-MUT-025", "C2-MUT-026"],
    "R2A-C1-FINAL-001": ["C1-DET-R2-AUDIT-REPLAY-ACYCLIC-PREREQUISITE-001"],
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_binding(freeze: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": freeze["candidate_id"],
        "candidate_file_sha256": freeze["candidate_file_sha256"],
        "canonical_candidate_hash": freeze["canonical_candidate_hash"],
        "candidate_freeze_hash": freeze["freeze_hash"],
    }


def validate_bound_artifact(
    value: dict[str, Any],
    freeze: dict[str, Any],
    *,
    expected_parent: str,
    expected_sequence: int,
    hash_field: str | None = None,
) -> list[str]:
    errors: list[str] = []
    expected = candidate_binding(freeze)
    for field, expected_value in expected.items():
        if field not in value:
            errors.append(f"C2_BOUND_FIELD_MISSING:{field}")
        elif value[field] != expected_value:
            errors.append(f"C2_BOUND_{field.upper()}_MISMATCH")
    if value.get("parent_artifact_hash") != expected_parent:
        errors.append("C2_BOUND_PARENT_ARTIFACT_HASH_MISMATCH")
    if value.get("artifact_sequence_index") != expected_sequence:
        errors.append("C2_BOUND_ARTIFACT_SEQUENCE_MISMATCH")
    if hash_field:
        body = dict(value)
        recorded = body.pop(hash_field, None)
        if recorded != sha256_json(body):
            errors.append(f"C2_BOUND_{hash_field.upper()}_MISMATCH")
    return sorted(set(errors))


def validate_exact_candidate_bundle(
    bundle: dict[str, Any], candidate_bytes: bytes, freeze: dict[str, Any]
) -> list[str]:
    """Validate a bundle against the exact bytes it claims to expose to an auditor."""
    errors: list[str] = []
    actual_file_hash = sha256_bytes(candidate_bytes)
    if bundle.get("candidate_file_sha256") != actual_file_hash:
        errors.append("C2_BOUND_CANDIDATE_FILE_SHA256_MISMATCH")
    if actual_file_hash != freeze["candidate_file_sha256"]:
        errors.append("C2_FROZEN_CANDIDATE_BYTES_MISMATCH")
    try:
        candidate = json.loads(candidate_bytes)
        canonical = canonical_candidate_hash(candidate)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        canonical = None
        errors.append("C2_AUDIT_BUNDLE_CANDIDATE_PARSE_FAILED")
    if bundle.get("canonical_candidate_hash") != canonical:
        errors.append("C2_BOUND_CANONICAL_CANDIDATE_HASH_MISMATCH")
    if bundle.get("candidate_freeze_hash") != freeze["freeze_hash"]:
        errors.append("C2_BOUND_CANDIDATE_FREEZE_HASH_MISMATCH")
    if bundle.get("candidate_id") != freeze["candidate_id"]:
        errors.append("C2_BOUND_CANDIDATE_ID_MISMATCH")
    return sorted(set(errors))


def build_candidate_report_projection(candidate: dict[str, Any]) -> dict[str, Any]:
    """Produce the decision projection used by later input-driven reports."""
    return {
        "candidate_id": candidate["candidate_id"],
        "decision": candidate["decision"],
        "accepted_scope": candidate["accepted_scope"],
        "next_phase_allowed": candidate["next_phase_allowed"],
        "decision_source": "CANDIDATE_INPUT",
    }


def validate_candidate_report_projection(
    report: dict[str, Any], candidate: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if report.get("decision_source") != "CANDIDATE_INPUT":
        errors.append("C2_REPORT_DECISION_SOURCE_NOT_INPUT_DRIVEN")
    if report != build_candidate_report_projection(candidate):
        errors.append("C2_REPORT_PROJECTION_MISMATCH")
    return errors


def build_candidate_state_projection(
    candidate: dict[str, Any], freeze: dict[str, Any]
) -> dict[str, Any]:
    return {
        **candidate_binding(freeze),
        "decision": candidate["decision"],
        "accepted_scope": candidate["accepted_scope"],
        "next_phase_allowed": candidate["next_phase_allowed"],
        "selected_architecture": None,
        "base_selected": False,
        "third_party_integrated": False,
        "skill_capability_status": "SCAFFOLD_ONLY",
        "phase003_prohibited": True,
    }


def validate_candidate_state_projection(
    value: dict[str, Any], candidate: dict[str, Any], freeze: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    for field, expected in candidate_binding(freeze).items():
        if value.get(field) != expected:
            errors.append(f"C2_BOUND_{field.upper()}_MISMATCH")
    accepted = candidate["decision"] == "AUTOMATED_ACCEPTED"
    expected_scope = "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY" if accepted else None
    expected_route = "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION" if accepted else None
    if value.get("accepted_scope") != expected_scope:
        errors.append("C2_STATE_ACCEPTED_SCOPE_INVALID")
    if value.get("next_phase_allowed") != expected_route:
        errors.append("C2_STATE_ROUTE_INVALID")
    if value.get("selected_architecture") is not None:
        errors.append("C2_STATE_ARCHITECTURE_SELECTION_PROHIBITED")
    if value.get("base_selected") is not False or value.get("third_party_integrated") is not False:
        errors.append("C2_STATE_FORMAL_INTEGRATION_PROHIBITED")
    if value.get("phase003_prohibited") is not True:
        errors.append("C2_STATE_PHASE003_PROHIBITION_MISSING")
    return sorted(set(errors))


def validate_precondition_semantics(value: dict[str, Any]) -> list[str]:
    failures = [
        item["check_id"] for item in value.get("checks", []) if item.get("status") != "PASS"
    ]
    if (
        value.get("all_required_pass") is not True
        or value.get("failed_check_ids") != []
        or failures
        or value.get("passed_check_count") != value.get("required_check_count")
    ):
        return ["C2_PRECONDITIONS_SEMANTIC_FAILURE"]
    return []


def validate_postfreeze_observation(
    embargo_errors: list[str], prohibited_runtime_files: list[str], counters: dict[str, int]
) -> list[str]:
    if embargo_errors or prohibited_runtime_files or any(value != 0 for value in counters.values()):
        return ["C2_POSTFREEZE_EMBARGO_NOT_PASS"]
    return []


def validate_closure_claims(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    observed = {item["finding_id"]: item["test_ids"] for item in value.get("closures", [])}
    if observed != FINDING_TESTS:
        errors.append("C2_CLOSURE_REQUIRED_EVIDENCE_MISMATCH")
    if any(item.get("status") != "CLOSED" for item in value.get("closures", [])):
        errors.append("C2_CLOSURE_FINDING_NOT_CLOSED")
    if value.get("unresolved_findings") != []:
        errors.append("C2_CLOSURE_UNRESOLVED_FINDING")
    prosecutor = value.get("candidate_prosecutor_review", {})
    if prosecutor.get("serious_findings_closed") is not True:
        errors.append("C2_CLOSURE_PROSECUTOR_FINDINGS_NOT_CLOSED")
    return sorted(set(errors))


def check_or_write_post_evidence_prosecutor(root: Path, *, check: bool) -> dict[str, Any]:
    """Preserve and normalize the prosecutor run that first inspected L3-L7."""
    raw_path = root / POST_EVIDENCE_PROSECUTOR_RAW_PATH
    if not raw_path.is_file():
        return {"status": "FAIL", "errors": ["C2_POST_EVIDENCE_PROSECUTOR_RAW_MISSING"]}
    value = normalize_audit(_read_json(raw_path))
    errors = validate_audit(root, value, "candidate_binding_prosecutor")
    freeze = _read_json(root / FREEZE_PATH)
    for field, expected in candidate_binding(freeze).items():
        if value.get(field) != expected:
            errors.append(f"C2_POST_EVIDENCE_PROSECUTOR_{field.upper()}_MISMATCH")
    errors.extend(check_or_write_json(root / POST_EVIDENCE_PROSECUTOR_PATH, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "output_hash": value["output_hash"],
    }


def _check(check_id: str, passed: bool, observed: str, *refs: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "required": True,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "evidence_refs": list(refs),
    }


def build_preconditions(root: Path) -> dict[str, Any]:
    candidate = _read_json(root / CANDIDATE_PATH)
    freeze = _read_json(root / FREEZE_PATH)
    input_freeze = _read_json(root / INPUT_FREEZE_PATH)
    compatibility = _read_json(root / RESULT_ROOT / "compatibility_tests/closure.json")
    state = _read_json(root / "state/project_state.json")
    old_preconditions = _read_json(
        root / "evals/results/phase-002d-r2a/authorization_preconditions.json"
    )
    r2_audit_path = "evals/results/phase-002d-r2/decision_audit/audit.json"
    r2_replay_path = "evals/results/phase-002d-r2/replay/replay.json"
    r2_embargo_path = "evals/results/phase-002d-r2/implementation_embargo.json"
    r2a_closure_path = "evals/results/phase-002d-r2a/adversarial_findings/closure.json"
    r2_audit = _read_json(root / r2_audit_path)
    r2_replay = _read_json(root / r2_replay_path)
    r2a_closure = _read_json(root / r2a_closure_path)
    dependency_resolution = _read_json(root / DEPENDENCY_RESOLUTION_PATH)
    c1_final_audit = _read_json(root / C1_FINAL_AUDIT_PATH)
    embargo_errors = verify_embargo(root)
    prohibited_runtime_files = []
    if not r3_shadow_authorized(root):
        prohibited_runtime_files = [
            path
            for relative in (
                Path("experiments/shadow_prototypes"),
                Path("src/cumcm_skill_lab/components"),
            )
            if (root / relative).exists()
            for path in (root / relative).rglob("*")
            if path.is_file()
        ]
    skill_hash = tree_hash(
        repository_file_hashes(root, (Path(".agents/skills/cumcm-modeling-evidence"),))
    )
    checks = [
        _check(
            "C2-PRE-001",
            not validate_candidate_freeze(root, freeze),
            "exact C2 candidate freeze validates",
            CANDIDATE_PATH.as_posix(),
            FREEZE_PATH.as_posix(),
        )
    ]
    for index, name in enumerate(R2_DECISION_PATHS, start=2):
        path = f"evals/results/phase-002d-r2/automated_decisions/{name}.json"
        decision = _read_json(root / path)["automated_decision"]
        checks.append(
            _check(
                f"C2-PRE-{index:03d}",
                decision["decision"] == "AUTOMATED_ACCEPTED",
                f"{decision['decision_id']}={decision['decision']}",
                path,
            )
        )
    checks.extend(
        [
            _check("C2-PRE-007", r2_audit["result"] == "PASS", "R2 Auditor=PASS", r2_audit_path),
            _check(
                "C2-PRE-008", r2_replay["stable"] is True, "R2 replay stable=true", r2_replay_path
            ),
            _check(
                "C2-PRE-009",
                old_preconditions["all_required_pass"] is True
                and old_preconditions["passed_check_count"] == 27,
                "historical R2A preconditions=27/27",
                "evals/results/phase-002d-r2a/authorization_preconditions.json",
            ),
            _check(
                "C2-PRE-010",
                r2a_closure["all_serious_findings_closed_for_bounded_authorization"] is True,
                "historical R2A serious findings closed",
                r2a_closure_path,
            ),
            _check(
                "C2-PRE-011",
                compatibility["result"] == "PASS"
                and not compatibility["unresolved_compatibility_blockers"],
                "C2 compatibility findings closed",
                (RESULT_ROOT / "compatibility_tests/closure.json").as_posix(),
            ),
            _check(
                "C2-PRE-012",
                file_sha256(root / r2_embargo_path)
                == input_freeze["protected_bindings"]["implementation_embargo_hash"]
                and not embargo_errors,
                (
                    f"implementation embargo file={file_sha256(root / r2_embargo_path)}; "
                    f"post-freeze errors={embargo_errors}"
                ),
                r2_embargo_path,
            ),
            _check(
                "C2-PRE-013",
                skill_hash == input_freeze["protected_bindings"]["formal_skill_tree_hash"],
                f"formal Skill tree hash={skill_hash}",
                ".agents/skills/cumcm-modeling-evidence/",
            ),
            _check(
                "C2-PRE-014",
                candidate["input_references"]["benchmark_hash"]
                == input_freeze["protected_bindings"]["benchmark_hash"],
                "Benchmark hash bound",
                INPUT_FREEZE_PATH.as_posix(),
            ),
            _check(
                "C2-PRE-015",
                candidate["input_references"]["threshold_hash"]
                == input_freeze["protected_bindings"]["threshold_hash"],
                "threshold hash bound",
                INPUT_FREEZE_PATH.as_posix(),
            ),
            _check(
                "C2-PRE-016",
                candidate["input_references"]["protocol_hash"]
                == input_freeze["protected_bindings"]["protocol_hash"],
                "protocol hash bound",
                INPUT_FREEZE_PATH.as_posix(),
            ),
            _check(
                "C2-PRE-017",
                state["selected_architecture"] is None,
                "selected_architecture=null",
                "state/project_state.json",
            ),
            _check(
                "C2-PRE-018",
                state["base_selected"] is False,
                "base_selected=false",
                "state/project_state.json",
            ),
            _check(
                "C2-PRE-019",
                state["third_party_integrated"] is False,
                "third_party_integrated=false",
                "state/project_state.json",
            ),
            _check(
                "C2-PRE-020",
                state["skill_capability_status"] == "SCAFFOLD_ONLY",
                "Skill capability=SCAFFOLD_ONLY",
                "state/project_state.json",
            ),
            _check(
                "C2-PRE-021",
                len(list((root / ".agents/skills").glob("*/SKILL.md"))) == 1,
                "formal Skill count=1",
                ".agents/skills/",
            ),
            _check(
                "C2-PRE-022",
                all(value == 0 for value in input_freeze["counters"].values())
                and state["specification_protocol"]["prototype_executions"] == 0
                and state["specification_protocol"]["real_model_starts"] == 0
                and state["specification_protocol"]["third_party_executions"] == 0
                and not prohibited_runtime_files,
                (
                    "post-freeze prototype/API/model/third-party observations=0; "
                    f"prohibited runtime files={len(prohibited_runtime_files)}"
                ),
                INPUT_FREEZE_PATH.as_posix(),
                "state/project_state.json",
            ),
            _check(
                "C2-PRE-023",
                candidate["phase003_prohibited"] is True,
                "Phase 003 prohibited",
                CANDIDATE_PATH.as_posix(),
            ),
            _check(
                "C2-PRE-024",
                not validate_dependency_resolution(root, dependency_resolution)
                and dependency_resolution["status"] == "PASS"
                and not dependency_resolution["corrected_graph_errors"],
                (
                    "C1 final finding dependency resolution=PASS; corrected graph errors="
                    f"{dependency_resolution['corrected_graph_errors']}"
                ),
                DEPENDENCY_RESOLUTION_PATH.as_posix(),
            ),
            _check(
                "C2-PRE-025",
                c1_final_audit["verdict"] == "FAIL"
                and c1_final_audit["output_hash"]
                == candidate["input_references"]["c1_final_audit_output_hash"]
                and "R2A-C1-FINAL-001"
                in {item["finding_id"] for item in c1_final_audit["findings"]},
                "C1 final FAIL and exact finding preserved as C2 retest input",
                C1_FINAL_AUDIT_PATH.as_posix(),
            ),
        ]
    )
    failed = [item["check_id"] for item in checks if item["status"] != "PASS"]
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_id": "PHASE-002D-R2A-C2-CANDIDATE-PRECONDITIONS-001",
        **candidate_binding(freeze),
        "parent_artifact_hash": freeze["freeze_hash"],
        "artifact_sequence_index": 13,
        "checks": checks,
        "required_check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "all_required_pass": not failed,
        "historical_preconditions_classification": "PREREQUISITE_CONTEXT_ONLY",
        "historical_preconditions_hash": old_preconditions["preconditions_hash"],
    }
    body["preconditions_hash"] = sha256_json(body)
    return body


def build_test_plan(root: Path) -> dict[str, Any]:
    freeze = _read_json(root / FREEZE_PATH)
    preconditions = _read_json(root / PRECONDITIONS_PATH)
    tests = [
        {
            "test_id": test_id,
            "mutation_type": mutation_type,
            "mutated_field": field,
            "expected_result": "REJECTED",
            "expected_error": error,
            "candidate_source": "READ_ONLY_COPY_OF_FROZEN_C2",
        }
        for test_id, mutation_type, field, error in MUTATION_SPECS
    ]
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "plan_id": "PHASE-002D-R2A-C2-CANDIDATE-MUTATION-PLAN-001",
        **candidate_binding(freeze),
        "parent_artifact_hash": preconditions["preconditions_hash"],
        "artifact_sequence_index": 14,
        "test_count": len(tests),
        "tests": tests,
        "historical_test_evidence_classification": "HISTORICAL_CONTEXT_ONLY_NOT_C2_PASS_EVIDENCE",
    }
    body["test_plan_hash"] = sha256_json(body)
    return body


def _candidate_copy_errors(
    root: Path, candidate: dict[str, Any], freeze: dict[str, Any], byte_hash: str
) -> list[str]:
    errors = validate_candidate(root, candidate)
    if byte_hash != freeze["candidate_file_sha256"]:
        errors.append("C2_BOUND_CANDIDATE_FILE_SHA256_MISMATCH")
    try:
        canonical = canonical_candidate_hash(candidate)
    except ValueError as exc:
        errors.append(str(exc))
        canonical = None
    if canonical != freeze["canonical_candidate_hash"]:
        errors.append("C2_BOUND_CANONICAL_CANDIDATE_HASH_MISMATCH")
    return sorted(set(errors))


def _field_observation(value: dict[str, Any], path: str) -> dict[str, Any]:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return {"present": False}
        current = current[part]
    return {"present": True, "value": current}


def _execute_mutation(
    root: Path,
    spec: tuple[str, str, str, str],
    candidate: dict[str, Any],
    freeze: dict[str, Any],
    plan: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    test_id, mutation_type, field, _expected = spec
    mutated = deepcopy(candidate)
    binding = {
        **candidate_binding(freeze),
        "parent_artifact_hash": plan["test_plan_hash"],
        "artifact_sequence_index": 15,
    }
    byte_hash = freeze["candidate_file_sha256"]
    original_bytes = (root / CANDIDATE_PATH).read_bytes()
    mutated_bytes = original_bytes
    if test_id == "C2-MUT-001":
        mutated_bytes = original_bytes + b" "
        byte_hash = sha256_bytes(mutated_bytes)
    elif test_id == "C2-MUT-002":
        mutated["accepted_scope"] = "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY_MUTATED"
    elif test_id == "C2-MUT-003":
        mutated["candidate_id"] = "CANDIDATE-ATTACKER"
    elif test_id == "C2-MUT-004":
        mutated["accepted_scope"] = "FORMAL_INTEGRATION"
    elif test_id == "C2-MUT-005":
        mutated["next_phase_allowed"] = None
    elif test_id == "C2-MUT-006":
        mutated["selected_architecture"] = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
    elif test_id == "C2-MUT-007":
        mutated["base_selected"] = True
    elif test_id == "C2-MUT-008":
        mutated["third_party_integrated"] = True
    elif test_id == "C2-MUT-009":
        mutated["restrictions"].append("FORMAL_INTEGRATION_ALLOWED")
    elif test_id == "C2-MUT-010":
        mutated["next_phase_allowed"] = "PHASE-003"
    elif test_id == "C2-MUT-011":
        mutated["restrictions"].remove("NO_HIDDEN_VAULT_ACCESS")
    elif test_id == "C2-MUT-012":
        mutated["restrictions"].remove("NO_FORMAL_SKILL_WRITE")
    elif test_id == "C2-MUT-013":
        mutated["formal_skill_auto_discovery"] = True
    elif test_id == "C2-MUT-014":
        del mutated["supersedes"]
    elif test_id == "C2-MUT-015":
        mutated["supersedes"]["decision_id"] = "DECISION-ATTACKER"
    elif test_id == "C2-MUT-016":
        binding["candidate_file_sha256"] = "0" * 64
    elif test_id == "C2-MUT-017":
        binding["candidate_id"] = "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"
    elif test_id == "C2-MUT-018":
        binding["artifact_sequence_index"] = freeze["artifact_sequence_index"]
    elif test_id == "C2-MUT-019":
        binding["parent_artifact_hash"] = "0" * 64
    elif test_id == "C2-MUT-020":
        binding["artifact_sequence_index"] = 14
    elif test_id == "C2-MUT-021":
        bundle = {
            **candidate_binding(freeze),
            "bundle_id": "SYNTHETIC-C2-EXACT-CANDIDATE-BUNDLE",
        }
        mutated_bytes = original_bytes + b"\n"
        return {
            "mutation_type": mutation_type,
            "mutated_field": field,
            "original_candidate_bytes_sha256": sha256_bytes(original_bytes),
            "mutated_candidate_bytes_sha256": sha256_bytes(mutated_bytes),
            "synthetic_bundle_hash": sha256_json(bundle),
        }, validate_exact_candidate_bundle(bundle, mutated_bytes, freeze)
    elif test_id == "C2-MUT-022":
        report = build_candidate_report_projection(candidate)
        report["decision_source"] = "HARDCODED_ACCEPT"
        return report, validate_candidate_report_projection(report, candidate)
    elif test_id == "C2-MUT-023":
        mutated["candidate_file_sha256"] = "0" * 64
    elif test_id == "C2-MUT-024":
        mutated["unknown_attack_field"] = "MUST_NOT_BE_DROPPED"
    elif test_id == "C2-MUT-025":
        state_projection = build_candidate_state_projection(candidate, freeze)
        state_projection["candidate_file_sha256"] = "0" * 64
        return state_projection, validate_candidate_state_projection(
            state_projection, candidate, freeze
        )
    elif test_id == "C2-MUT-026":
        state_projection = build_candidate_state_projection(candidate, freeze)
        state_projection["next_phase_allowed"] = "PHASE-003"
        return state_projection, validate_candidate_state_projection(
            state_projection, candidate, freeze
        )
    elif test_id == "C2-MUT-027":
        proposed_bytes = original_bytes + b" "
        return {
            "current_candidate_bytes_sha256": sha256_bytes(original_bytes),
            "proposed_candidate_bytes_sha256": sha256_bytes(proposed_bytes),
        }, frozen_revision_rewrite_errors(original_bytes, proposed_bytes)
    elif test_id == "C2-MUT-028":
        preconditions = build_preconditions(root)
        preconditions["checks"][0]["status"] = "FAIL"
        preconditions["passed_check_count"] -= 1
        preconditions["failed_check_ids"] = [preconditions["checks"][0]["check_id"]]
        preconditions["all_required_pass"] = False
        preconditions["preconditions_hash"] = sha256_json(
            {key: value for key, value in preconditions.items() if key != "preconditions_hash"}
        )
        return preconditions, validate_precondition_semantics(preconditions)
    elif test_id == "C2-MUT-029":
        observation = {
            "embargo_errors": ["PROHIBITED_IMPLEMENTATION_DETECTED:synthetic.py"],
            "prohibited_runtime_files": [],
            "counters": {"prototype_executions": 0, "api_calls": 0},
        }
        return observation, validate_postfreeze_observation(**observation)
    elif test_id == "C2-MUT-030":
        closure_projection = {
            "closures": [
                {"finding_id": finding_id, "test_ids": list(test_ids)}
                for finding_id, test_ids in FINDING_TESTS.items()
            ]
        }
        closure_projection["closures"][0]["test_ids"] = ["C2-MUT-UNRELATED"]
        return closure_projection, validate_closure_claims(closure_projection)
    elif test_id == "C1-DET-R2-AUDIT-REPLAY-ACYCLIC-PREREQUISITE-001":
        resolution = _read_json(root / DEPENDENCY_RESOLUTION_PATH)
        audit = _read_json(root / R2_AUDIT_PATH)
        inverted = deepcopy(resolution["corrected_graph"])
        replay_node = inverted["prerequisite_replay_node"]
        audit_node = inverted["prerequisite_audit_node"]
        inverted["edges"] = [
            edge
            for edge in inverted["edges"]
            if (edge["source"], edge["target"]) != (replay_node, audit_node)
        ]
        inverted["edges"].append({"source": audit_node, "target": replay_node})
        errors = validate_audit_replay_order(inverted, audit, R2_REPLAY_PATH.as_posix())
        return {
            "mutation_type": mutation_type,
            "mutated_field": field,
            "source_corrected_graph_hash": resolution["corrected_graph"]["graph_hash"],
            "inverted_edge": {"source": audit_node, "target": replay_node},
            "removed_prerequisite_edge": {"source": replay_node, "target": audit_node},
        }, errors
    if mutated != candidate:
        mutated_bytes = (json.dumps(mutated, ensure_ascii=False, indent=2) + "\n").encode()
        byte_hash = sha256_bytes(mutated_bytes)
    candidate_errors = _candidate_copy_errors(root, mutated, freeze, byte_hash)
    binding_errors = validate_bound_artifact(
        binding,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=15,
    )
    return {
        "mutation_type": mutation_type,
        "mutated_field": field,
        "original_candidate_bytes_sha256": sha256_bytes(original_bytes),
        "mutated_candidate_bytes_sha256": sha256_bytes(mutated_bytes),
        "candidate_copy_hash": sha256_json(mutated),
        "candidate_copy_bytes_sha256": sha256_bytes(mutated_bytes),
        "binding_copy_hash": sha256_json(binding),
        "mutated_field_observation": _field_observation(
            binding if test_id in {f"C2-MUT-{index:03d}" for index in range(16, 21)} else mutated,
            field,
        ),
    }, sorted(set(candidate_errors + binding_errors))


def build_test_evidence(root: Path) -> dict[str, Any]:
    candidate = _read_json(root / CANDIDATE_PATH)
    freeze = _read_json(root / FREEZE_PATH)
    plan = _read_json(root / TEST_PLAN_PATH)
    code_hash = (
        HISTORICAL_TEST_CODE_HASH if r3_shadow_authorized(root) else file_sha256(Path(__file__))
    )
    items = []
    for ordinal, spec in enumerate(MUTATION_SPECS, start=1):
        test_id, mutation_type, field, expected_error = spec
        mutation_input, errors = _execute_mutation(root, spec, candidate, freeze, plan)
        exit_code = 1 if errors else 0
        item: dict[str, Any] = {
            "schema_version": "1.0.0",
            "evidence_id": f"EVIDENCE-{test_id}",
            "test_id": test_id,
            **candidate_binding(freeze),
            "parent_artifact_hash": plan["test_plan_hash"],
            "artifact_sequence_index": 15,
            "generation_ordinal": ordinal,
            "mutation_type": mutation_type,
            "mutated_field": field,
            "expected_result": "REJECTED",
            "actual_result": "REJECTED" if errors else "ACCEPTED",
            "expected_error": expected_error,
            "actual_errors": errors,
            "test_code_path": "src/cumcm_skill_lab/authorization_c2/candidate_evidence.py",
            "test_code_hash": code_hash,
            "input_observation": mutation_input,
            "input_hash": sha256_json(mutation_input),
            "output_hash": sha256_json({"errors": errors, "exit_code": exit_code}),
            "exit_code": exit_code,
            "status": "PASS" if exit_code == 1 and expected_error in errors else "FAIL",
            "candidate_copy_only": True,
            "original_candidate_modified": False,
        }
        item["evidence_hash"] = sha256_json(item)
        items.append(item)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "evidence_set_id": "PHASE-002D-R2A-C2-CANDIDATE-MUTATION-EVIDENCE-001",
        **candidate_binding(freeze),
        "parent_artifact_hash": plan["test_plan_hash"],
        "artifact_sequence_index": 15,
        "evidence_count": len(items),
        "passed_count": sum(item["status"] == "PASS" for item in items),
        "test_evidence": items,
        "test_evidence_hashes": [item["evidence_hash"] for item in items],
        "historical_evidence_used_as_candidate_pass": False,
    }
    body["evidence_hash"] = sha256_json(body)
    return body


def build_closure(root: Path) -> dict[str, Any]:
    freeze = _read_json(root / FREEZE_PATH)
    evidence = _read_json(root / TEST_EVIDENCE_PATH)
    prosecutor = _read_json(root / POST_EVIDENCE_PROSECUTOR_PATH)
    passed = {item["test_id"] for item in evidence["test_evidence"] if item["status"] == "PASS"}
    closures = [
        {
            "finding_id": finding_id,
            "test_ids": test_ids,
            "status": "CLOSED" if set(test_ids) <= passed else "OPEN",
        }
        for finding_id, test_ids in FINDING_TESTS.items()
    ]
    unresolved = [item["finding_id"] for item in closures if item["status"] != "CLOSED"]
    serious_prosecutor_findings = sorted(
        item["finding_id"]
        for item in prosecutor["findings"]
        if item["severity"] in {"BLOCKER", "ERROR"}
    )
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "closure_id": "PHASE-002D-R2A-C2-CANDIDATE-CLOSURE-001",
        **candidate_binding(freeze),
        "parent_artifact_hash": evidence["evidence_hash"],
        "artifact_sequence_index": 16,
        "test_evidence_hashes": evidence["test_evidence_hashes"],
        "candidate_bound_pass_evidence_count": evidence["passed_count"],
        "historical_context_only": [
            "evals/results/phase-002d-r2a/adversarial_findings/closure.json#15/15"
        ],
        "historical_evidence_used_as_candidate_pass": False,
        "candidate_prosecutor_review": {
            "audit_id": prosecutor["audit_id"],
            "output_hash": prosecutor["output_hash"],
            "verdict_at_review": prosecutor["verdict"],
            "serious_finding_ids": serious_prosecutor_findings,
            "serious_findings_closed": set(serious_prosecutor_findings) <= set(FINDING_TESTS),
            "closure_basis": "DETERMINISTIC_POST_REVIEW_REGRESSION_TESTS",
        },
        "closures": closures,
        "unresolved_findings": unresolved,
        "all_candidate_tests_pass": evidence["passed_count"] == evidence["evidence_count"],
        "result": (
            "PASS"
            if evidence["passed_count"] == evidence["evidence_count"] and not unresolved
            else "FAIL"
        ),
    }
    body["closure_hash"] = sha256_json(body)
    return body


def validate_candidate_evidence_chain(root: Path) -> list[str]:
    freeze = _read_json(root / FREEZE_PATH)
    preconditions = _read_json(root / PRECONDITIONS_PATH)
    plan = _read_json(root / TEST_PLAN_PATH)
    evidence = _read_json(root / TEST_EVIDENCE_PATH)
    closure = _read_json(root / CLOSURE_PATH)
    errors = validate_candidate_freeze(root, freeze)
    errors.extend(validate_precondition_semantics(preconditions))
    if preconditions != build_preconditions(root):
        errors.append("C2_PRECONDITIONS_NOT_REPRODUCIBLE")
    errors.extend(
        validate_bound_artifact(
            preconditions,
            freeze,
            expected_parent=freeze["freeze_hash"],
            expected_sequence=13,
            hash_field="preconditions_hash",
        )
    )
    if plan != build_test_plan(root):
        errors.append("C2_TEST_PLAN_NOT_REPRODUCIBLE")
    errors.extend(
        validate_bound_artifact(
            plan,
            freeze,
            expected_parent=preconditions["preconditions_hash"],
            expected_sequence=14,
            hash_field="test_plan_hash",
        )
    )
    if evidence != build_test_evidence(root):
        errors.append("C2_TEST_EVIDENCE_NOT_REPRODUCIBLE")
    if evidence.get("evidence_count") != len(MUTATION_SPECS) or evidence.get("passed_count") != len(
        MUTATION_SPECS
    ):
        errors.append("C2_TEST_EVIDENCE_COUNT_OR_STATUS_INVALID")
    errors.extend(
        validate_bound_artifact(
            evidence,
            freeze,
            expected_parent=plan["test_plan_hash"],
            expected_sequence=15,
            hash_field="evidence_hash",
        )
    )
    errors.extend(validate_closure_claims(closure))
    if closure != build_closure(root):
        errors.append("C2_CANDIDATE_CLOSURE_NOT_REPRODUCIBLE")
    for item in evidence["test_evidence"]:
        errors.extend(
            validate_bound_artifact(
                item,
                freeze,
                expected_parent=plan["test_plan_hash"],
                expected_sequence=15,
                hash_field="evidence_hash",
            )
        )
        if item["status"] != "PASS":
            errors.append(f"C2_CANDIDATE_TEST_NOT_PASS:{item['test_id']}")
    errors.extend(
        validate_bound_artifact(
            closure,
            freeze,
            expected_parent=evidence["evidence_hash"],
            expected_sequence=16,
            hash_field="closure_hash",
        )
    )
    if closure["result"] != "PASS" or closure["unresolved_findings"]:
        errors.append("C2_CANDIDATE_CLOSURE_NOT_PASS")
    return sorted(set(errors))


def check_or_write_candidate_evidence_inputs(root: Path, *, check: bool) -> dict[str, Any]:
    """Create or verify C2 L13-L15 before the independent prosecutor runs."""
    freeze = _read_json(root / FREEZE_PATH)
    errors = validate_candidate_freeze(root, freeze)
    preconditions = build_preconditions(root)
    errors.extend(check_or_write_json(root / PRECONDITIONS_PATH, preconditions, check=check))
    errors.extend(validate_precondition_semantics(preconditions))
    errors.extend(
        validate_bound_artifact(
            preconditions,
            freeze,
            expected_parent=freeze["freeze_hash"],
            expected_sequence=13,
            hash_field="preconditions_hash",
        )
    )
    plan = build_test_plan(root)
    errors.extend(check_or_write_json(root / TEST_PLAN_PATH, plan, check=check))
    errors.extend(
        validate_bound_artifact(
            plan,
            freeze,
            expected_parent=preconditions["preconditions_hash"],
            expected_sequence=14,
            hash_field="test_plan_hash",
        )
    )
    evidence = build_test_evidence(root)
    errors.extend(check_or_write_json(root / TEST_EVIDENCE_PATH, evidence, check=check))
    errors.extend(
        validate_bound_artifact(
            evidence,
            freeze,
            expected_parent=plan["test_plan_hash"],
            expected_sequence=15,
            hash_field="evidence_hash",
        )
    )
    if evidence["evidence_count"] != len(MUTATION_SPECS) or evidence["passed_count"] != len(
        MUTATION_SPECS
    ):
        errors.append("C2_TEST_EVIDENCE_COUNT_OR_STATUS_INVALID")
    for item in evidence["test_evidence"]:
        errors.extend(
            validate_bound_artifact(
                item,
                freeze,
                expected_parent=plan["test_plan_hash"],
                expected_sequence=15,
                hash_field="evidence_hash",
            )
        )
        if item["status"] != "PASS":
            errors.append(f"C2_CANDIDATE_TEST_NOT_PASS:{item['test_id']}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "candidate_id": CANDIDATE_ID,
        "preconditions_hash": preconditions["preconditions_hash"],
        "test_plan_hash": plan["test_plan_hash"],
        "evidence_hash": evidence["evidence_hash"],
        "test_evidence_count": evidence["evidence_count"],
        "passed_count": evidence["passed_count"],
    }


def check_or_write_candidate_evidence(root: Path, *, check: bool) -> dict[str, Any]:
    result = check_or_write_candidate_evidence_inputs(root, check=check)
    errors = list(result["errors"])
    if errors:
        return {"status": "FAIL", "errors": sorted(set(errors))}
    prosecutor_result = check_or_write_post_evidence_prosecutor(root, check=check)
    errors.extend(prosecutor_result["errors"])
    if errors:
        return {"status": "FAIL", "errors": sorted(set(errors))}
    closure = build_closure(root)
    errors.extend(check_or_write_json(root / CLOSURE_PATH, closure, check=check))
    if not errors:
        errors.extend(validate_candidate_evidence_chain(root))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "candidate_id": CANDIDATE_ID,
        "preconditions_hash": result["preconditions_hash"],
        "test_plan_hash": result["test_plan_hash"],
        "evidence_hash": result["evidence_hash"],
        "test_evidence_count": result["test_evidence_count"],
        "passed_count": result["passed_count"],
        "closure_hash": closure["closure_hash"],
    }


__all__ = [
    "BINDING_FIELDS",
    "CLOSURE_PATH",
    "MUTATION_SPECS",
    "POST_EVIDENCE_PROSECUTOR_PATH",
    "POST_EVIDENCE_PROSECUTOR_RAW_PATH",
    "PRECONDITIONS_PATH",
    "TEST_EVIDENCE_PATH",
    "TEST_PLAN_PATH",
    "build_closure",
    "build_preconditions",
    "build_test_evidence",
    "build_test_plan",
    "candidate_binding",
    "check_or_write_candidate_evidence",
    "check_or_write_candidate_evidence_inputs",
    "check_or_write_post_evidence_prosecutor",
    "build_candidate_report_projection",
    "build_candidate_state_projection",
    "validate_bound_artifact",
    "validate_candidate_evidence_chain",
    "validate_candidate_report_projection",
    "validate_candidate_state_projection",
    "validate_closure_claims",
    "validate_exact_candidate_bundle",
    "validate_postfreeze_observation",
    "validate_precondition_semantics",
]
