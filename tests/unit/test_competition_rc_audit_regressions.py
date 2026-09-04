from __future__ import annotations

import copy
import importlib.util
import json
import math
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
    assert stale.dependency_chain
    case_cli.stale_check(case_root, mutate=True)
    frozen_state = (case_root / "case_state.json").read_bytes()
    repeated = case_cli.stale_check(case_root, mutate=True)
    assert repeated.dependency_chain == stale.dependency_chain
    assert (case_root / "case_state.json").read_bytes() == frozen_state


def test_claim_scope_and_registered_evidence_are_exactly_bound(case_cli, tmp_path: Path) -> None:
    case_root = tmp_path / "prediction"
    case_cli.run_smoke(case_root, "AUDIT-CLAIM-001", "prediction", False)
    state = case_cli.load_state(case_root)
    claim = case_cli.read_artifact(case_root, "claim_evidence")["content"]
    final = case_cli.read_artifact(case_root, "final_result")["content"]
    manifest = case_cli.load_json(case_root / "runs" / claim["run_id"] / "manifest.json")

    overbroad = copy.deepcopy(claim)
    overbroad["claim_text"] = "This model is universally optimal for all problems"
    overbroad["supported_scope"] = overbroad["claim_text"]
    result = case_cli.validate_claim(
        overbroad,
        manifest,
        final,
        case_root=case_root,
        state=state,
    )
    assert result.accepted is False
    assert "RC_CLAIM_FINAL_SCOPE_MISMATCH" in result.reason_codes

    nonexistent = copy.deepcopy(claim)
    nonexistent["evidence_artifact_ids"] = ["DOES-NOT-EXIST"]
    result = case_cli.validate_claim(
        nonexistent,
        manifest,
        final,
        case_root=case_root,
        state=state,
    )
    assert result.accepted is False
    assert {
        "RC_CLAIM_EVIDENCE_REGISTRY_MISMATCH",
        "RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING",
    } <= set(result.reason_codes)


def test_comparison_decision_scores_splits_and_run_ledger_are_exactly_bound(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "prediction"
    case_cli.run_smoke(case_root, "AUDIT-COMPARISON-001", "prediction", False)
    comparison = case_cli.read_artifact(case_root, "model_comparison")["content"]
    freezes = case_cli.trusted_freezes(case_root)

    missing = copy.deepcopy(comparison)
    missing.pop("selection_decision_hash")
    assert (
        "RC_COMPARISON_DECISION_HASH_MISMATCH"
        in case_cli.validate_comparison(missing, freezes, case_root=case_root).reason_codes
    )

    fabricated = copy.deepcopy(comparison)
    fabricated["attempts"][0]["validation_score"] = 0.0
    fabricated["selected_candidate_id"] = fabricated["baseline_id"]
    fabricated["selection_decision_hash"] = case_cli.canonical_hash(
        {
            "selected_candidate_id": fabricated["baseline_id"],
            "validation_scores": {
                item["candidate_id"]: item["validation_score"] for item in fabricated["attempts"]
            },
            "metric": fabricated["metric"],
            "rule": fabricated["selection_rule"],
            "aggregation_rule": fabricated["aggregation_rule"],
        }
    )
    reasons = case_cli.validate_comparison(fabricated, freezes, case_root=case_root).reason_codes
    assert "RC_COMPARISON_SCORE_OUTPUT_MISMATCH" in reasons
    assert "RC_COMPARISON_MANIFEST_DECISION_MISMATCH" in reasons

    swapped = copy.deepcopy(comparison)
    swapped["splits"]["validation"], swapped["splits"]["test"] = (
        swapped["splits"]["test"],
        swapped["splits"]["validation"],
    )
    assert (
        "RC_COMPARISON_UNTRUSTED_FREEZE"
        in case_cli.validate_comparison(swapped, freezes, case_root=case_root).reason_codes
    )

    source_manifest = next(case_root.glob("runs/*/manifest.json"))
    hidden = case_cli.load_json(source_manifest)
    hidden["run_id"] = "RUN-HIDDEN-RETRY"
    case_cli.write_json(case_root / "runs/RUN-HIDDEN-RETRY/manifest.json", hidden)
    assert (
        "RC_COMPARISON_RUN_LEDGER_NOT_EXACT"
        in case_cli.validate_comparison(comparison, freezes, case_root=case_root).reason_codes
    )


def test_final_result_selected_run_metrics_and_scope_are_exactly_bound(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "optimization"
    case_cli.run_smoke(case_root, "AUDIT-FINAL-001", "optimization", False)
    comparison = case_cli.read_artifact(case_root, "model_comparison")["content"]
    final = case_cli.read_artifact(case_root, "final_result")["content"]
    changed = copy.deepcopy(final)
    changed["selected_model"] = comparison["baseline_id"]
    changed["final_metrics"]["profit"] += 1
    result = case_cli.validate_final_result(
        changed,
        comparison,
        case_root=case_root,
    )
    assert result.accepted is False
    assert {
        "RC_FINAL_RESULT_SELECTION_BINDING_MISMATCH",
        "RC_FINAL_RESULT_METRICS_OR_SCOPE_MISMATCH",
    } <= set(result.reason_codes)


@pytest.mark.parametrize(
    "field,replacement",
    [
        ("selected_models", [{"candidate_id": "FABRICATED"}]),
        ("sources", [{"source_id": "FABRICATED"}]),
        (
            "validation_results",
            {
                "comparison_decision_hash": "0" * 64,
                "selected_model": "FABRICATED",
                "test_used_for_selection": True,
            },
        ),
        ("robustness_results", {"status": "FABRICATED"}),
        ("result_tables", [{"table_id": "FABRICATED", "rows": []}]),
        ("figure_ready_data", [{"figure_id": "FABRICATED", "series": []}]),
    ],
)
def test_handoff_all_paper_facts_are_canonically_bound(
    case_cli, tmp_path: Path, field: str, replacement
) -> None:
    case_root = tmp_path / field
    case_cli.run_smoke(case_root, f"AUDIT-HANDOFF-{field.upper()}", "prediction", False)
    handoff = case_cli.load_json(case_root / case_cli.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    handoff[field] = replacement
    result = case_cli.validate_handoff(
        handoff,
        case_root=case_root,
        state=case_cli.load_state(case_root),
    )
    assert result.accepted is False
    assert "RC_HANDOFF_CANONICAL_BINDING_MISMATCH" in result.reason_codes


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("path", "/private/run"),
        ("path", "/etc/shadow"),
        ("path", "${HOME}/private/run"),
        ("path", "~other/.ssh/id_rsa"),
        ("secret", "SYNTHETIC_SECRET_CANARY"),
        ("token", "SYNTHETIC_TOKEN_CANARY"),
    ],
)
def test_formal_sensitive_scan_matches_selected_k1(case_cli, key: str, value: str) -> None:
    findings = case_cli.sensitive_findings({"nested": {"items": [{key: value}]}})
    assert findings
    assert value not in str(findings)


def test_public_status_converts_malformed_nested_state_to_structured_block(
    repo_root: Path, case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "case"
    state = case_cli.initialize_case(case_root, "AUDIT-MALFORMED-STATE", "general")
    state["history"][-1] = 7
    case_cli.write_json(case_root / "case_state.json", state)
    cli = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"

    result = subprocess.run(
        [sys.executable, str(cli), "status", "--case-root", str(case_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode != 0
    assert payload["status"] == "BLOCK"
    assert payload["accepted"] is False
    assert payload["final"] is False
    assert "Traceback" not in result.stderr


def test_component_and_isolated_state_boundaries_are_exact(case_cli) -> None:
    for components in (["BOGUS"], [next(iter(case_cli.COMPONENT_IDS))] * 2):
        result = case_cli.boundary_validate(
            {},
            {
                "stage": "PROBLEM_INTAKE",
                "enabled_components": components,
                "execution_scope": "CASE",
            },
        )
        assert "RC_CONTEXT_ENABLED_COMPONENTS_INVALID" in result.reason_codes

    context = {
        "writer": "modeling_orchestrator",
        "formal_project_state_write": False,
        "second_state_truth": False,
        "execution_scope": "CASE",
        "state_path": "case_state.json",
    }
    context["isolated_state_binding_hash"] = case_cli.canonical_hash(context)
    assert case_cli.validate_state_boundary(context).accepted is True
    context["extra_state_authority"] = True
    assert (
        "RC_EXTRA_OR_MISSING_STATE_AUTHORITY_REJECTED"
        in case_cli.validate_state_boundary(context).reason_codes
    )


def test_general_case_final_and_handoff_use_generic_evidence_contract(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "general"

    def accepted(key: str, content: dict) -> None:
        case_cli.write_json(
            case_root / case_cli.ARTIFACT_PATHS[key], case_cli.artifact(key, content)
        )

    requirements = [{"requirement_id": "REQ-G-1", "text": "generic evidence"}]
    accepted("problem_requirements", {"requirements": requirements})
    accepted(
        "source_ledger",
        {"sources": [{"source_id": "SRC-GENERIC", "kind": "PROJECT_ORIGINAL"}]},
    )
    accepted(
        "assumptions_and_symbols",
        {
            "assumptions": ["generic assumption"],
            "symbols": {"q": "quality"},
            "formulas": ["q=score"],
        },
    )
    accepted(
        "data_audit",
        {"raw_immutable": True, "data_hashes": {"data/raw/generic.json": "1" * 64}},
    )
    candidates = [
        {"candidate_id": "G-BASE", "baseline": True},
        {"candidate_id": "G-CAND", "baseline": False},
    ]
    accepted("model_candidates", {"candidates": candidates})
    accepted(
        "experiment_plan",
        {"handoff_generated_at": "2026-09-04T00:00:00Z"},
    )
    comparison = {
        "selected_candidate_id": "G-CAND",
        "selection_decision_hash": "2" * 64,
        "attempts": [
            {
                "candidate_id": "G-CAND",
                "run_id": "RUN-G-CAND",
                "outcome": "SUCCESS",
                "random_seed": 17,
                "validation_score": 1.0,
            }
        ],
        "test_access": {"used_for_selection": False},
    }
    accepted("model_comparison", comparison)
    robustness = {
        "status": "VALIDATED",
        "perturbations": [{"name": "generic", "quality": 9.0}],
        "failure_cases": ["generic limitation"],
    }
    accepted("robustness_analysis", robustness)
    output_relative = "runs/RUN-G-CAND/output.json"
    output = {
        "candidate_id": "G-CAND",
        "validation_metrics": {"custom_loss": 1.0},
        "final_metrics": {"quality": 9.0},
        "claim_scope": "generic frozen evidence",
        "figure_ready_data": [{"figure_id": "GENERIC_QUALITY", "series": [{"quality": 9.0}]}],
        "limitations": ["generic synthetic contract only"],
        "uncertainty": {"scope": "deterministic", "quantified": True},
        "requirement_claims": {
            "REQ-G-1": {
                "claim_id": "CLAIM-G-1",
                "claim_text": "generic frozen evidence",
                "evidence_artifact_ids": [output_relative],
            }
        },
    }
    case_cli.write_json(case_root / output_relative, output)
    output_file_hash = case_cli.file_hash(case_root / output_relative)
    manifest = {
        "run_id": "RUN-G-CAND",
        "output_hash": case_cli.canonical_hash([output_file_hash]),
        "decision_hash": "2" * 64,
        "configuration": {"candidate_id": "G-CAND", "seed": 17},
        "output_files": [{"path": output_relative, "sha256": output_file_hash}],
    }
    case_cli.write_json(case_root / "runs/RUN-G-CAND/manifest.json", manifest)
    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": "G-CAND",
        "run_id": "RUN-G-CAND",
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
        "final_metrics": output["final_metrics"],
        "claim_scope": output["claim_scope"],
    }
    accepted("final_result", final)
    claim = {
        "claim_id": "CLAIM-G-1",
        "claim_text": output["claim_scope"],
        "supported_scope": output["claim_scope"],
        "run_id": manifest["run_id"],
        "run_manifest_hash": case_cli.canonical_hash(manifest),
        "input_hash": "3" * 64,
        "code_hash": "4" * 64,
        "configuration_hash": "5" * 64,
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
        "evidence_artifact_ids": [output_relative],
        "supported_requirement_ids": ["REQ-G-1"],
        "requirement_claims": output["requirement_claims"],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    accepted("claim_evidence", claim)

    assert case_cli.validate_final_result(final, comparison, case_root=case_root).accepted is True
    state = {"case_kind": "general", "evidence_bindings": {}}
    expected = case_cli.build_expected_handoff(case_root, state)
    for key in (
        "problem_requirements",
        "source_ledger",
        "assumptions_and_symbols",
        "data_audit",
        "model_candidates",
        "experiment_plan",
        "model_comparison",
        "robustness_analysis",
        "final_result",
        "claim_evidence",
    ):
        relative = case_cli.ARTIFACT_PATHS[key]
        state["evidence_bindings"][relative] = case_cli.file_hash(case_root / relative)
    result = case_cli.validate_handoff(expected, case_root=case_root, state=state)
    assert result.accepted is True
    assert expected["final_metrics"] == {"quality": 9.0}


def test_direct_validators_fail_closed_on_nested_enum_type_fuzz(case_cli, tmp_path: Path) -> None:
    case_root = tmp_path / "prediction"
    case_cli.run_smoke(case_root, "AUDIT-TYPE-FUZZ", "prediction", False)
    comparison = case_cli.read_artifact(case_root, "model_comparison")["content"]
    freezes = case_cli.trusted_freezes(case_root)
    mutations = (
        lambda value: value.update(candidate_ids=[[]]),
        lambda value: value.update(random_seeds=[[]]),
        lambda value: value.update(metric_direction=[]),
    )
    for mutate in mutations:
        value = copy.deepcopy(comparison)
        mutate(value)
        before = copy.deepcopy(value)
        result = case_cli.validate_comparison(value, freezes)
        assert result.accepted is False
        assert value == before
    boundary = case_cli.boundary_validate(
        {},
        {
            "stage": "PROBLEM_INTAKE",
            "enabled_components": sorted(case_cli.COMPONENT_IDS),
            "execution_scope": [],
        },
    )
    assert boundary.accepted is False
    state = case_cli.initialize_case(tmp_path / "state", "AUDIT-TYPE-STATE", "general")
    state["state"] = []
    assert case_cli.validate_case_state(state).accepted is False
    manifest = case_cli.load_json(next(case_root.glob("runs/*/manifest.json")))
    manifest["outcome"] = []
    assert (
        case_cli.validate_manifest(manifest, case_root=case_root, trusted_freezes=freezes).accepted
        is False
    )


@pytest.mark.parametrize(
    "split_name,value",
    [("train", float("nan")), ("validation", float("inf")), ("test", float("-inf"))],
)
def test_direct_comparison_validator_blocks_nonfinite_split_values_without_raising(
    case_cli, tmp_path: Path, split_name: str, value: float
) -> None:
    case_root = tmp_path / split_name
    case_cli.run_smoke(case_root, "AUDIT-NONFINITE-SPLIT", "prediction", False)
    comparison = case_cli.read_artifact(case_root, "model_comparison")["content"]
    comparison["splits"][split_name] = [value]
    before = copy.deepcopy(comparison)

    result = case_cli.validate_comparison(
        comparison,
        case_cli.trusted_freezes(case_root),
        case_root=case_root,
    )

    assert result.accepted is False
    assert "RC_COMPARISON_NONFINITE_OR_NONJSON" in result.reason_codes
    assert comparison == before


def test_direct_state_and_claim_validators_block_nested_nonfinite_values(
    case_cli, tmp_path: Path
) -> None:
    context = {
        "writer": "modeling_orchestrator",
        "formal_project_state_write": False,
        "second_state_truth": False,
        "execution_scope": "CASE",
        "state_path": "case_state.json",
        "isolated_state_binding_hash": "0" * 64,
        "unexpected": float("nan"),
    }
    state_result = case_cli.validate_state_boundary(context)
    assert state_result.accepted is False
    assert "RC_STATE_CONTEXT_NONFINITE_OR_NONJSON" in state_result.reason_codes
    assert math.isnan(context["unexpected"])

    case_root = tmp_path / "claim"
    case_cli.run_smoke(case_root, "AUDIT-NONFINITE-CLAIM", "prediction", False)
    state = case_cli.load_state(case_root)
    claim = case_cli.read_artifact(case_root, "claim_evidence")["content"]
    final = case_cli.read_artifact(case_root, "final_result")["content"]
    manifest = case_cli.load_json(case_root / "runs" / claim["run_id"] / "manifest.json")
    manifest["unexpected"] = {"score": float("nan")}
    claim_result = case_cli.validate_claim(
        claim,
        manifest,
        final,
        case_root=case_root,
        state=state,
    )
    assert claim_result.accepted is False
    assert "RC_CLAIM_MANIFEST_NONFINITE_OR_NONJSON" in claim_result.reason_codes
    assert math.isnan(manifest["unexpected"]["score"])


@pytest.mark.parametrize(
    "field,replacement",
    [
        ("attempts", True),
        ("candidate_ids", True),
        ("random_seeds", True),
        ("random_seeds", "bad"),
    ],
)
def test_direct_comparison_validator_never_raises_on_container_type_fuzz(
    case_cli, tmp_path: Path, field: str, replacement: object
) -> None:
    case_root = tmp_path / f"prediction-{field}-{type(replacement).__name__}"
    case_cli.run_smoke(case_root, "AUDIT-CONTAINER-TYPE-FUZZ", "prediction", False)
    comparison = case_cli.read_artifact(case_root, "model_comparison")["content"]
    comparison[field] = replacement
    before = copy.deepcopy(comparison)

    result = case_cli.validate_comparison(
        comparison,
        case_cli.trusted_freezes(case_root),
        case_root=case_root,
    )

    assert result.accepted is False
    assert comparison == before


@pytest.mark.parametrize("claim_id", [None, 0, True, [], {}, "bad"])
def test_claim_validator_rejects_invalid_claim_ids(
    case_cli, tmp_path: Path, claim_id: object
) -> None:
    case_root = tmp_path / f"claim-{type(claim_id).__name__}"
    case_cli.run_smoke(case_root, "AUDIT-CLAIM-ID-FUZZ", "prediction", False)
    state = case_cli.load_state(case_root)
    claim = case_cli.read_artifact(case_root, "claim_evidence")["content"]
    final = case_cli.read_artifact(case_root, "final_result")["content"]
    manifest = case_cli.load_json(case_root / "runs" / claim["run_id"] / "manifest.json")
    claim["claim_id"] = claim_id

    result = case_cli.validate_claim(
        claim,
        manifest,
        final,
        case_root=case_root,
        state=state,
    )

    assert result.accepted is False
    assert "RC_CLAIM_ID_INVALID" in result.reason_codes


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_candidates",
        "unregistered_candidates",
        "string_seed",
        "duplicate_seeds",
        "overlapping_splits",
        "empty_splits",
        "empty_metric",
    ],
)
def test_experiment_plan_gate_rejects_invalid_recomputed_freezes(
    case_cli, tmp_path: Path, mutation: str
) -> None:
    case_root = tmp_path / mutation
    case_cli.run_smoke(case_root, "AUDIT-PLAN-GATE", "prediction", False)
    state = case_cli.load_state(case_root)
    history = state["history"][:6]
    evidence = {relative for record in history for relative in record["evidence"]}
    state.update(
        state="MODELS_PROPOSED",
        last_gate="GATE_MODEL_PORTFOLIO",
        history=history,
        evidence_bindings={
            relative: digest
            for relative, digest in state["evidence_bindings"].items()
            if relative in evidence
        },
    )
    case_cli.write_json(case_root / "case_state.json", state)
    plan_path = case_root / case_cli.ARTIFACT_PATHS["experiment_plan"]
    plan_record = case_cli.load_json(plan_path)
    plan = plan_record["content"]
    if mutation == "duplicate_candidates":
        plan["candidate_ids"] = ["P-BASELINE-MEAN", "P-BASELINE-MEAN"]
    elif mutation == "unregistered_candidates":
        plan["candidate_ids"] = ["UNREGISTERED-BASE", "UNREGISTERED-CANDIDATE"]
        plan["baseline_id"] = "UNREGISTERED-BASE"
    elif mutation == "string_seed":
        plan["random_seeds"] = ["20260904"]
    elif mutation == "duplicate_seeds":
        plan["random_seeds"] = [20260904, 20260904]
    elif mutation == "overlapping_splits":
        plan["splits"]["test"] = [plan["splits"]["validation"][0]]
    elif mutation == "empty_splits":
        plan["splits"] = {"train": [], "validation": [], "test": []}
    elif mutation == "empty_metric":
        plan["metric"] = ""
    plan["trusted_freeze_registry"] = {
        "candidate_set": case_cli.canonical_hash(plan["candidate_ids"]),
        "metric": case_cli.canonical_hash(
            {
                "name": plan["metric"],
                "direction": plan["metric_direction"],
                "aggregation_rule": plan["aggregation_rule"],
                "selection_rule": plan["selection_rule"],
            }
        ),
        "seed_schedule": case_cli.canonical_hash(plan["random_seeds"]),
        "split_assignment": case_cli.canonical_hash(plan["splits"]),
        "baseline": case_cli.canonical_hash(plan["baseline_id"]),
        "input_set": case_cli.canonical_hash(plan["required_input_hashes"]),
        "execution_policy": case_cli.canonical_hash(
            {
                "stop_rule": plan["stop_rule"],
                "handoff_generated_at": plan["handoff_generated_at"],
            }
        ),
    }
    plan_record["content_hash"] = case_cli.canonical_hash(plan)
    case_cli.write_json(plan_path, plan_record)

    with pytest.raises(ValueError, match="RC_TRUSTED_FREEZE_REGISTRY_MISSING"):
        case_cli.advance_once(case_root)


def test_run_inputs_must_exactly_match_preregistered_audited_input_set(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "input-lineage"
    case_cli.run_smoke(case_root, "AUDIT-INPUT-LINEAGE", "prediction", False)
    state = case_cli.load_state(case_root)
    history = state["history"][:8]
    evidence = {relative for record in history for relative in record["evidence"]}
    state.update(
        state="RUNNING",
        last_gate="GATE_EXECUTION_AUTHORIZED",
        history=history,
        evidence_bindings={
            relative: digest
            for relative, digest in state["evidence_bindings"].items()
            if relative in evidence
        },
    )
    case_cli.write_json(case_root / "case_state.json", state)
    unrelated = "problem/problem_requirements.json"
    unrelated_hash = case_cli.file_hash(case_root / unrelated)
    for manifest_path in case_root.glob("runs/*/manifest.json"):
        manifest = case_cli.load_json(manifest_path)
        manifest["input_files"] = [{"path": unrelated, "sha256": unrelated_hash}]
        manifest["input_hash"] = case_cli.canonical_hash([unrelated_hash])
        case_cli.write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="RC_MANIFEST_INPUT_FREEZE_MISMATCH"):
        case_cli.advance_once(case_root)


def test_robustness_gate_requires_selected_run_and_output_evidence(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "robustness-lineage"
    case_cli.run_smoke(case_root, "AUDIT-ROBUSTNESS-LINEAGE", "prediction", False)
    state = case_cli.load_state(case_root)
    history = state["history"][:10]
    evidence = {relative for record in history for relative in record["evidence"]}
    state.update(
        state="RUN_VALIDATED",
        last_gate="GATE_REPRODUCIBILITY_MANIFEST",
        history=history,
        evidence_bindings={
            relative: digest
            for relative, digest in state["evidence_bindings"].items()
            if relative in evidence
        },
    )
    case_cli.write_json(case_root / "case_state.json", state)
    robustness_path = case_root / case_cli.ARTIFACT_PATHS["robustness_analysis"]
    fabricated = case_cli.artifact(
        "robustness_analysis",
        {
            "status": "VALIDATED",
            "perturbations": [{"unrelated": "fabricated"}],
            "failure_cases": [],
        },
    )
    case_cli.write_json(robustness_path, fabricated)

    with pytest.raises(ValueError, match="RC_ROBUSTNESS_"):
        case_cli.advance_once(case_root)


def test_requirement_traceability_uses_distinct_output_bound_claims(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "requirements"
    case_cli.run_smoke(case_root, "AUDIT-REQUIREMENT-CLAIMS", "prediction", False)
    handoff = case_cli.load_json(case_root / "handoff/modeling_to_paper.json")
    claim = case_cli.read_artifact(case_root, "claim_evidence")["content"]
    trace = handoff["requirement_traceability"]

    assert set(trace) == {"REQ-P-1", "REQ-P-2", "REQ-P-3"}
    assert len(set(trace.values())) == 3
    assert set(handoff["claim_evidence"]) == set(trace.values())

    tampered = copy.deepcopy(claim)
    tampered["requirement_claims"]["REQ-P-2"] = tampered["requirement_claims"]["REQ-P-1"]
    final = case_cli.read_artifact(case_root, "final_result")["content"]
    manifest = case_cli.load_json(case_root / "runs" / claim["run_id"] / "manifest.json")
    result = case_cli.validate_claim(
        tampered,
        manifest,
        final,
        case_root=case_root,
        state=case_cli.load_state(case_root),
    )
    assert result.accepted is False
    assert "RC_CLAIM_REQUIREMENT_COVERAGE_INVALID" in result.reason_codes


@pytest.mark.parametrize("freeze_hash", ["unknown", "a" * 64])
def test_manifest_rejects_unregistered_top_level_freeze_reference(
    case_cli, tmp_path: Path, freeze_hash: str
) -> None:
    case_root = tmp_path / freeze_hash[:8]
    case_cli.run_smoke(case_root, "AUDIT-FREEZE-REFERENCE", "prediction", False)
    manifest = case_cli.load_json(next(case_root.glob("runs/*/manifest.json")))
    manifest["freeze_hash"] = freeze_hash
    result = case_cli.validate_manifest(
        manifest,
        case_root=case_root,
        trusted_freezes=case_cli.trusted_freezes(case_root),
    )
    assert result.accepted is False
    assert "RC_MANIFEST_ADDITIONAL_FIELDS_REJECTED" in result.reason_codes


def test_post_ready_case_root_code_mutation_reports_chain_without_state_write(
    repo_root: Path, case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "prediction"
    case_cli.run_smoke(case_root, "AUDIT-CODE-STALE", "prediction", False)
    copied_code = case_root / "code/model.py"
    copied_code.parent.mkdir(parents=True)
    copied_code.write_bytes((repo_root / "THIRD_PARTY_NOTICES.md").read_bytes())
    state_path = case_root / "case_state.json"
    state = case_cli.load_state(case_root)
    for manifest_path in case_root.glob("runs/*/manifest.json"):
        manifest = case_cli.load_json(manifest_path)
        manifest["code_files"].append(
            {
                "scope": "CASE_ROOT",
                "path": "code/model.py",
                "repository_path": "THIRD_PARTY_NOTICES.md",
                "sha256": case_cli.file_hash(copied_code),
            }
        )
        manifest["code_tree_hash"] = case_cli.canonical_hash(
            [item["sha256"] for item in manifest["code_files"]]
        )
        case_cli.write_json(manifest_path, manifest)
        relative = str(manifest_path.relative_to(case_root))
        state["evidence_bindings"][relative] = case_cli.file_hash(manifest_path)
    case_cli.write_json(state_path, state)
    assert case_cli.stale_check(case_root, mutate=False).accepted is True

    copied_code.write_text("mutated code dependency\n", encoding="utf-8")
    state_before = state_path.read_bytes()
    result = case_cli.stale_check(case_root, mutate=False)
    assert result.status == "STALE"
    assert result.dependency_chain
    assert all(path.endswith("manifest.json") for path in result.dependency_chain)
    assert state_path.read_bytes() == state_before
