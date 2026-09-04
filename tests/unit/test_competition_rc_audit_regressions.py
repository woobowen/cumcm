from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def case_cli(repo_root: Path):
    path = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("cumcm_case_audit_regression", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_rejects_missing_input_fake_commit_and_incomplete_code_tree(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "case"
    output = case_root / "runs/RUN-A/output.json"
    case_cli.write_json(output, {"value": 1})
    output_hash = case_cli.file_hash(output)
    freezes = {"candidate_set": "1" * 64, "metric": "2" * 64, "seed_schedule": "3" * 64}
    configuration = {"candidate_id": "A", "seed": 7}
    manifest = {
        "run_id": "RUN-A",
        "input_files": [{"path": "data/raw/missing.json", "sha256": "4" * 64}],
        "input_hash": case_cli.canonical_hash(["4" * 64]),
        "code_commit": "TEST-COMMIT",
        "code_files": [
            {
                "scope": "SKILL_ROOT",
                "path": "scripts/missing.py",
                "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/missing.py",
                "sha256": "5" * 64,
            }
        ],
        "code_tree_hash": case_cli.canonical_hash(["5" * 64]),
        "configuration": configuration,
        "configuration_hash": case_cli.canonical_hash(configuration),
        "random_seed": 7,
        "argv": ["model.py"],
        "cwd_policy": "CASE_ROOT_RELATIVE",
        "environment_allowlist": {"PYTHONHASHSEED": "0"},
        "output_files": [{"path": "runs/RUN-A/output.json", "sha256": output_hash}],
        "output_hash": case_cli.canonical_hash([output_hash]),
        "outcome": "SUCCESS",
        "failure": None,
        "supersession": None,
        "trusted_capture": True,
        "freeze_bindings": freezes,
        "decision_hash": "7" * 64,
    }

    result = case_cli.validate_manifest(manifest, case_root=case_root, trusted_freezes=freezes)

    assert result.accepted is False
    assert {
        "RC_MANIFEST_INPUT_MISSING",
        "RC_MANIFEST_GIT_COMMIT_INVALID",
        "RC_MANIFEST_CODE_MISSING",
    } <= set(result.reason_codes)
    changed_configuration = copy.deepcopy(manifest)
    changed_configuration["configuration"]["seed"] = 8
    changed_result = case_cli.validate_manifest(
        changed_configuration, case_root=case_root, trusted_freezes=freezes
    )
    assert "RC_MANIFEST_CONFIGURATION_HASH_MISMATCH" in changed_result.reason_codes


def test_comparison_rejects_empty_freezes_and_missing_baseline_attempt(case_cli) -> None:
    candidates = ["BASE", "CAND"]
    comparison = {
        "candidate_ids": candidates,
        "baseline_id": "BASE",
        "splits": {"train": [1], "validation": [2], "test": [3]},
        "metric": "MAE",
        "metric_direction": "MIN",
        "random_seeds": [7],
        "attempts": [
            {
                "candidate_id": "CAND",
                "run_id": "RUN-CAND",
                "random_seed": 7,
                "outcome": "SUCCESS",
                "validation_score": 1.0,
            }
        ],
        "selected_candidate_id": "CAND",
        "freeze_bindings": {},
        "leakage_checks": {
            "test_used_for_candidate_generation": False,
            "test_used_for_feature_selection": False,
            "test_used_for_threshold_selection": False,
            "future_information": False,
            "group_overlap": False,
            "target_in_features": False,
            "time_order_valid": True,
        },
        "test_access": {"authorized": True, "count": 1, "used_for_selection": False},
    }

    result = case_cli.validate_comparison(comparison, {})

    assert result.accepted is False
    assert {
        "RC_COMPARISON_UNTRUSTED_FREEZE",
        "RC_COMPARISON_ATTEMPT_MATRIX_INCOMPLETE",
        "RC_COMPARISON_BASELINE_SUCCESS_MISSING",
    } <= set(result.reason_codes)


def test_manifest_rejects_existing_but_mismatched_git_commit(case_cli, tmp_path: Path) -> None:
    case_root = tmp_path / "prediction"
    case_cli.run_smoke(case_root, "AUDIT-COMMIT-001", "prediction", False)
    final = case_cli.read_artifact(case_root, "final_result")["content"]
    manifest_path = case_root / "runs" / final["run_id"] / "manifest.json"
    manifest = case_cli.load_json(manifest_path)
    manifest["code_commit"] = "23e6b4aa4f4e1003ef782be7317479ed98e558aa"

    result = case_cli.validate_manifest(
        manifest,
        case_root=case_root,
        trusted_freezes=case_cli.trusted_freezes(case_root),
    )

    assert result.accepted is False
    assert "RC_MANIFEST_CODE_COMMIT_MISMATCH" in result.reason_codes


def test_state_jump_and_sensitive_extension_are_rejected_without_echo(
    repo_root: Path, case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "case"
    state = case_cli.initialize_case(case_root, "AUDIT-STATE-001", "general")
    state["state"] = "EVIDENCE_VALIDATED"
    state["api_key"] = "SYNTHETIC_STATUS_SECRET_CANARY"
    case_cli.write_json(case_root / "case_state.json", state)
    cli = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"

    result = subprocess.run(
        [sys.executable, str(cli), "status", "--case-root", str(case_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "SYNTHETIC_STATUS_SECRET_CANARY" not in result.stdout
    assert "RC_SECRET_FIELD_REJECTED" in json.loads(result.stdout)["reason_codes"]


def test_manual_state_jump_cannot_reach_handoff(case_cli, tmp_path: Path) -> None:
    case_root = tmp_path / "case"
    state = case_cli.initialize_case(case_root, "AUDIT-JUMP-001", "general")
    state["state"] = "EVIDENCE_VALIDATED"
    state["last_gate"] = "GATE_CLAIM_EVIDENCE"
    case_cli.write_json(case_root / "case_state.json", state)

    with pytest.raises(ValueError, match="RC_CASE_STATE_HISTORY_INVALID"):
        case_cli.advance_once(case_root)


@pytest.mark.parametrize("kind", ["prediction", "optimization"])
def test_smoke_consumes_bound_inputs_and_raw_mutation_is_stale(
    case_cli, tmp_path: Path, kind: str
) -> None:
    case_root = tmp_path / kind
    result = case_cli.run_smoke(case_root, f"AUDIT-{kind.upper()}-001", kind, False)
    state = case_cli.load_state(case_root)
    audit = case_cli.read_artifact(case_root, "data_audit")["content"]
    raw_relative = sorted(audit.get("raw_data_hashes", audit["data_hashes"]))[0]
    selected_run = case_cli.read_artifact(case_root, "final_result")["content"]["run_id"]
    manifest = case_cli.load_json(case_root / "runs" / selected_run / "manifest.json")

    assert result["final_state"] == "READY_FOR_PAPER_HANDOFF"
    assert raw_relative in state["evidence_bindings"]
    assert raw_relative in {item["path"] for item in manifest["input_files"]}
    assert len(manifest["code_files"]) == 2
    if kind == "prediction":
        processed = "data/processed/prediction_clean.json"
        assert processed in {item["path"] for item in manifest["input_files"]}
        assert audit["processing_lineage"]["imputed_times"] == [5]
        assert audit["processing_lineage"]["outlier_times"] == [6]

    raw_path = case_root / raw_relative
    changed = copy.deepcopy(case_cli.load_json(raw_path))
    if isinstance(changed, list):
        changed[0]["target"] = -999
    else:
        changed["capacity"]["labor"] = 999
    case_cli.write_json(raw_path, changed)

    stale = case_cli.stale_check(case_root, mutate=False)
    assert stale.status == "STALE"
    assert "RC_UPSTREAM_DEPENDENCY_STALE" in stale.reason_codes
