import copy

import pytest

from cumcm_skill_lab.adjudication.models import read_yaml, sha256_json
from cumcm_skill_lab.specification.authorization.scope import (
    ACCEPTED_SCOPE,
    ALLOWED_PATHS,
    PROHIBITED_SCOPES,
    SCOPE_PATH,
    validate_scope_value,
    validate_shadow_prototype_scope,
)


def _scope(repo_root):
    return read_yaml(repo_root / SCOPE_PATH)


def _rehash(scope):
    body = copy.deepcopy(scope)
    body.pop("scope_hash", None)
    scope["scope_hash"] = sha256_json(body)


def test_shadow_scope_is_valid(repo_root):
    result = validate_shadow_prototype_scope(repo_root)
    assert result["status"] == "PASS"
    assert result["errors"] == []


def test_shadow_scope_is_specification_only(repo_root):
    scope = _scope(repo_root)
    assert scope["status"] == "SPECIFICATION_ONLY_NOT_IMPLEMENTED"
    assert scope["implementation_created"] is False
    assert scope["prototype_executed"] is False


def test_shadow_scope_accepts_only_experimental_scope(repo_root):
    scope = _scope(repo_root)
    assert scope["accepted_scope"] == ACCEPTED_SCOPE
    assert set(scope["prohibited_scopes"]) == PROHIBITED_SCOPES


def test_shadow_scope_preserves_immutable_baseline(repo_root):
    baseline = _scope(repo_root)["baseline"]
    assert baseline == {
        "architecture_id": "ARCH-S0-RETAIN-SCAFFOLD-ONLY",
        "mode": "IMMUTABLE_BASELINE_ADAPTER",
        "implementation_path": None,
    }


def test_shadow_scope_path_allowlist_is_exact(repo_root):
    assert set(_scope(repo_root)["allowed_paths"]) == ALLOWED_PATHS


def test_shadow_scope_denies_formal_authorities(repo_root):
    denied = set(_scope(repo_root)["prohibited_paths"])
    assert ".agents/skills/cumcm-modeling-evidence/" in denied
    assert "state/project_state.json" in denied
    assert "contracts/" in denied


def test_shadow_scope_denies_hidden_vault_and_historical_results(repo_root):
    denied = set(_scope(repo_root)["prohibited_paths"])
    assert "benchmark-vault/" in denied
    assert "evals/results/phase-002d-r2/" in denied


def test_shadow_scope_rollback_is_delete_only_and_history_preserving(repo_root):
    rollback = _scope(repo_root)["rollback"]
    assert rollback["strategy"] == "DELETE_ISOLATED_SHADOW_TREES"
    assert rollback["formal_state_repair_required"] is False
    assert rollback["historical_artifact_mutation_allowed"] is False


@pytest.mark.parametrize(
    "scope_value",
    [
        "FORMAL_SKILL_IMPLEMENTATION",
        "FORMAL_INTEGRATION",
        "PRODUCTION_READY",
        "DIRECT_REUSE",
        "ARCHITECTURE_SELECTED",
        "PHASE_003_INTEGRATION",
    ],
)
def test_shadow_scope_escalation_is_rejected(repo_root, scope_value):
    scope = _scope(repo_root)
    scope["accepted_scope"] = scope_value
    _rehash(scope)
    assert "SHADOW_SCOPE_ESCALATION" in validate_scope_value(repo_root, scope)


def test_shadow_scope_formal_state_write_is_rejected(repo_root):
    scope = _scope(repo_root)
    scope["state_isolation"]["formal_state_write_allowed"] = True
    _rehash(scope)
    assert "SHADOW_SCOPE_FORMAL_STATE_WRITE_ALLOWED" in validate_scope_value(repo_root, scope)


@pytest.mark.parametrize(
    "field",
    [
        "hidden_seed_read_allowed",
        "hidden_oracle_read_allowed",
        "hidden_oracle_prompt_allowed",
        "tracked_hidden_values_allowed",
        "os_enforced_verified",
    ],
)
def test_shadow_scope_hidden_access_or_claim_is_rejected(repo_root, field):
    scope = _scope(repo_root)
    scope["vault_isolation"][field] = True
    _rehash(scope)
    assert "SHADOW_SCOPE_HIDDEN_VAULT_ACCESS_ALLOWED" in validate_scope_value(repo_root, scope)


@pytest.mark.parametrize(
    "field",
    [
        "formal_skill_auto_discovery",
        "production_workflow_callable",
        "third_party_code_allowed",
        "third_party_execution_allowed",
        "license_block_released",
    ],
)
def test_shadow_scope_runtime_escape_is_rejected(repo_root, field):
    scope = _scope(repo_root)
    scope["runtime_isolation"][field] = True
    _rehash(scope)
    assert "SHADOW_SCOPE_RUNTIME_ISOLATION_BROKEN" in validate_scope_value(repo_root, scope)


def test_shadow_scope_phase003_route_is_rejected(repo_root):
    scope = _scope(repo_root)
    scope["phase003_prohibited"] = False
    _rehash(scope)
    assert "SHADOW_SCOPE_PHASE003_LEAKAGE" in validate_scope_value(repo_root, scope)


def test_shadow_scope_architecture_selection_is_rejected(repo_root):
    scope = _scope(repo_root)
    scope["selected_architecture"] = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
    _rehash(scope)
    assert "SHADOW_SCOPE_ARCHITECTURE_PRESELECTED" in validate_scope_value(repo_root, scope)


def test_shadow_scope_allowlist_expansion_is_rejected(repo_root):
    scope = _scope(repo_root)
    scope["allowed_paths"].append("src/cumcm_skill_lab/")
    _rehash(scope)
    assert "SHADOW_SCOPE_PATH_ALLOWLIST_MISMATCH" in validate_scope_value(repo_root, scope)


def test_shadow_scope_vault_allowlist_overlap_is_rejected(repo_root):
    scope = _scope(repo_root)
    scope["allowed_paths"][0] = "benchmark-vault/"
    _rehash(scope)
    errors = validate_scope_value(repo_root, scope)
    assert "SHADOW_SCOPE_PATH_BOUNDARY_OVERLAP" in errors


def test_shadow_scope_keeps_material_unknowns_explicit(repo_root):
    unknowns = set(_scope(repo_root)["unknowns"])
    assert unknowns == {
        "CLEAN_ROOM_LEGAL_COMPLIANCE_NOT_PROVEN",
        "HIDDEN_VAULT_OS_ISOLATION_NOT_VERIFIED",
        "PROTOTYPE_EFFECTIVENESS_UNMEASURED",
        "MONETARY_COST_UNKNOWN",
    }
