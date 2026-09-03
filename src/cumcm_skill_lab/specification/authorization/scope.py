"""Validate the specification-only, experimental shadow prototype boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import read_json, read_yaml, sha256_json
from cumcm_skill_lab.specification.architecture_validator import (
    BASELINE_ID,
    validate_architecture_candidates,
)
from cumcm_skill_lab.specification.implementation_embargo import (
    r3_shadow_authorized,
    verify_embargo,
)

from .evidence_freeze import verify_input_freeze

SCOPE_PATH = Path("specifications/shadow_prototype_scope.yaml")
SCOPE_SCHEMA_PATH = Path("contracts/shadow_prototype_scope.schema.json")
ACCEPTED_SCOPE = "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"
ALLOWED_PATHS = {
    "experiments/shadow_prototypes/arch_w1/",
    "experiments/shadow_prototypes/arch_k1/",
    "experiments/shadow_prototypes/common/",
    "evals/results/phase-002d-r3/",
}
REQUIRED_PROHIBITED_PATHS = {
    ".agents/skills/cumcm-modeling-evidence/",
    "state/project_state.json",
    "contracts/",
    "benchmark-vault/",
    "evals/results/phase-002d-r2/",
    ".cache/upstream/",
}
PROHIBITED_SCOPES = {
    "FORMAL_SKILL_IMPLEMENTATION",
    "FORMAL_INTEGRATION",
    "PRODUCTION_READY",
    "DIRECT_REUSE",
    "ARCHITECTURE_SELECTED",
    "PHASE_003_INTEGRATION",
}


def validate_scope_value(root: Path, value: dict[str, Any]) -> list[str]:
    errors = [
        f"SHADOW_SCOPE_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(read_json(root / SCOPE_SCHEMA_PATH)).iter_errors(value)
    ]
    body = dict(value)
    recorded_hash = body.pop("scope_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("SHADOW_SCOPE_HASH_MISMATCH")
    candidates = validate_architecture_candidates(root)
    if value.get("candidate_ids") != candidates.get("candidate_ids"):
        errors.append("SHADOW_SCOPE_CANDIDATE_SET_MISMATCH")
    if value.get("baseline", {}).get("architecture_id") != BASELINE_ID:
        errors.append("SHADOW_SCOPE_BASELINE_MISSING")
    if value.get("selected_architecture") is not None:
        errors.append("SHADOW_SCOPE_ARCHITECTURE_PRESELECTED")
    if value.get("accepted_scope") != ACCEPTED_SCOPE:
        errors.append("SHADOW_SCOPE_ESCALATION")
    allowed = set(value.get("allowed_paths", []))
    denied = set(value.get("prohibited_paths", []))
    if allowed != ALLOWED_PATHS:
        errors.append("SHADOW_SCOPE_PATH_ALLOWLIST_MISMATCH")
    if not denied >= REQUIRED_PROHIBITED_PATHS:
        errors.append("SHADOW_SCOPE_PATH_DENYLIST_INCOMPLETE")
    if allowed & denied or any(path.startswith("benchmark-vault/") for path in allowed):
        errors.append("SHADOW_SCOPE_PATH_BOUNDARY_OVERLAP")
    if not set(value.get("prohibited_scopes", [])) >= PROHIBITED_SCOPES:
        errors.append("SHADOW_SCOPE_PROHIBITED_SCOPE_MISSING")
    if value.get("phase003_prohibited") is not True:
        errors.append("SHADOW_SCOPE_PHASE003_LEAKAGE")
    state = value.get("state_isolation", {})
    if (
        state.get("formal_state_write_allowed") is not False
        or state.get("private_state_required") is not True
    ):
        errors.append("SHADOW_SCOPE_FORMAL_STATE_WRITE_ALLOWED")
    vault = value.get("vault_isolation", {})
    if any(
        vault.get(field) is not False
        for field in (
            "hidden_seed_read_allowed",
            "hidden_oracle_read_allowed",
            "hidden_oracle_prompt_allowed",
            "tracked_hidden_values_allowed",
            "os_enforced_verified",
        )
    ):
        errors.append("SHADOW_SCOPE_HIDDEN_VAULT_ACCESS_ALLOWED")
    runtime = value.get("runtime_isolation", {})
    if any(
        runtime.get(field) is not False
        for field in (
            "formal_skill_auto_discovery",
            "production_workflow_callable",
            "third_party_code_allowed",
            "third_party_execution_allowed",
            "license_block_released",
        )
    ):
        errors.append("SHADOW_SCOPE_RUNTIME_ISOLATION_BROKEN")
    confinement = value.get("path_confinement", {})
    if confinement.get("status") != "UNVERIFIED_BLOCKS_FILE_WRITES_AND_EXECUTION" or any(
        confinement.get(field) is not True
        for field in (
            "canonical_root_required",
            "no_follow_required",
            "shared_inode_forbidden",
            "rename_swap_defense_required",
            "pre_post_protected_hash_required",
        )
    ):
        errors.append("SHADOW_SCOPE_PATH_CONFINEMENT_GATE_INCOMPLETE")
    dependency = value.get("dependency_policy", {})
    if (
        dependency.get("status") != "UNVERIFIED_BLOCKS_FILE_WRITES_AND_EXECUTION"
        or dependency.get("project_owned_allowlist_required") is not True
        or dependency.get("isolated_interpreter_no_site_packages_required") is not True
        or dependency.get("loaded_artifact_provenance_required") is not True
        or any(
            dependency.get(field) is not False
            for field in ("dynamic_import_allowed", "subprocess_allowed", "network_allowed")
        )
    ):
        errors.append("SHADOW_SCOPE_DEPENDENCY_GATE_INCOMPLETE")
    callability = value.get("callability_policy", {})
    if (
        callability.get("status") != "UNVERIFIED_BLOCKS_EXECUTION"
        or callability.get("shadow_only_runner_capability_required") is not True
        or any(
            callability.get(field) is not False
            for field in (
                "production_registry_entry_allowed",
                "formal_skill_import_allowed",
                "normal_cli_dispatch_allowed",
                "production_subprocess_call_allowed",
            )
        )
    ):
        errors.append("SHADOW_SCOPE_CALLABILITY_GATE_INCOMPLETE")
    output = value.get("output_policy", {})
    if (
        output.get("status") != "POLICY_ONLY_BLOCKS_OUTPUT_UNTIL_ENFORCED"
        or output.get("root") != "evals/results/phase-002d-r3/"
        or output.get("content_addressed_run_id_required") is not True
        or output.get("shadow_origin_marker_required") is not True
        or output.get("allowed_suffixes") != [".json"]
        or output.get("formal_artifact_kinds_allowed") != []
        or any(
            output.get(field) is not False
            for field in ("executable_allowed", "links_allowed", "formal_discovery_allowed")
        )
    ):
        errors.append("SHADOW_SCOPE_OUTPUT_GATE_INCOMPLETE")
    stages = value.get("execution_stages", {})
    if (
        stages.get("prototype_build") != "CONDITIONAL_ON_FILE_AND_DEPENDENCY_GATES"
        or stages.get("deterministic_stage1") != "CONDITIONAL_ON_ALL_RUNTIME_GATES"
        or stages.get("model_stage2") != "PROHIBITED_PENDING_NEW_FROZEN_AUTHORIZATION"
        or stages.get("final_stage3") != "PROHIBITED_PENDING_NEW_FROZEN_AUTHORIZATION"
        or stages.get("model_starts_authorized") != 0
        or stages.get("hidden_benchmark_use_authorized") is not False
    ):
        errors.append("SHADOW_SCOPE_EXECUTION_STAGE_ESCALATION")
    future = value.get("future_runtime_gate", {})
    if (
        future.get("current_status") != "NOT_SATISFIED_EXECUTION_PROHIBITED"
        or future.get("actual_runtime_evidence_present") is not False
        or future.get("unknown_cost_disposition") != "EVIDENCE_INSUFFICIENT"
        or set(future.get("required_before_model_stage2", []))
        != {"R2A-PCD-001", "R2A-PCD-002", "R2A-PCD-003"}
    ):
        errors.append("SHADOW_SCOPE_FUTURE_RUNTIME_GATE_INCOMPLETE")
    rollback = value.get("rollback", {})
    if (
        rollback.get("strategy") != "DELETE_ISOLATED_SHADOW_TREES"
        or rollback.get("historical_artifact_mutation_allowed") is not False
        or rollback.get("disposable_workspace_required") is not True
        or rollback.get("all_refs_absence_verification_required") is not True
        or any(
            rollback.get(field) is not False
            for field in ("git_tracking_allowed", "git_commit_allowed", "git_push_allowed")
        )
    ):
        errors.append("SHADOW_SCOPE_ROLLBACK_NOT_ISOLATED")
    prohibited_existing_roots = (
        root / "experiments/shadow_prototypes",
        root / "evals/results/phase-002d-r3",
    )
    if not r3_shadow_authorized(root) and any(path.exists() for path in prohibited_existing_roots):
        errors.append("SHADOW_SCOPE_PROTOTYPE_IMPLEMENTATION_ALREADY_EXISTS")
    errors.extend(verify_input_freeze(root))
    errors.extend(verify_embargo(root))
    return sorted(set(errors))


def validate_shadow_prototype_scope(root: Path) -> dict[str, Any]:
    if not (root / SCOPE_PATH).is_file():
        return {"status": "FAIL", "errors": ["SHADOW_SCOPE_MISSING"]}
    value = read_yaml(root / SCOPE_PATH)
    errors = validate_scope_value(root, value)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "scope_id": value.get("scope_id"),
        "scope_hash": value.get("scope_hash"),
        "accepted_scope": value.get("accepted_scope"),
        "candidate_ids": value.get("candidate_ids", []),
        "selected_architecture": value.get("selected_architecture"),
        "implementation_created": value.get("implementation_created"),
        "prototype_executed": value.get("prototype_executed"),
    }
