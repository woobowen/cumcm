from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from cumcm_skill_lab.shadow_validation.grader import grade_result
from cumcm_skill_lab.shadow_validation.runner import run_case
from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.arch_w1 import WorkflowGuardAdapter
from experiments.shadow_prototypes.arch_w1.guards import comparison_checklist
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    sha256_json,
)
from experiments.shadow_prototypes.common.public_cases import (
    load_public_cases,
    public_isolated_state,
)

ISOLATED_STATE = public_isolated_state()


def _context(tmp_path: Path, case: ShadowCaseInput, ordinal: int = 0) -> ShadowContext:
    return ShadowContext(
        run_id=f"R3-W1-{case.case_id}-{ordinal}",
        architecture_id=WorkflowGuardAdapter.architecture_id,
        stage="PUBLIC_VALIDATION",
        output_dir=tmp_path / case.case_id / str(ordinal),
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=COMPONENT_IDS,
    )


def _expected(case: ShadowCaseInput) -> str:
    return "PASS" if case.case_class == "valid control" else "BLOCK"


def _evaluate_payload(
    repo_root: Path, tmp_path: Path, case: ShadowCaseInput, payload: dict[str, object]
):
    derived = replace(case, payload=payload, input_hash=sha256_json(payload))
    return run_case(
        repo_root,
        WorkflowGuardAdapter.architecture_id,
        derived,
        ISOLATED_STATE,
        _context(tmp_path, derived),
        persist=False,
    )[0]


def test_w1_passes_corrected_public_controls_and_blocks_adversarial_cases(
    repo_root: Path, tmp_path: Path
) -> None:
    for index, case in enumerate(load_public_cases(repo_root)):
        result, unchanged = run_case(
            repo_root,
            WorkflowGuardAdapter.architecture_id,
            case,
            ISOLATED_STATE,
            _context(tmp_path, case, index),
            persist=False,
        )
        grade = grade_result(
            result, {"expected_outcome": _expected(case)}, input_unchanged=unchanged
        )
        assert grade["passed"], (case.case_id, result.decision.reason_codes)
        assert result.diagnostics["formal_state_writes"] == 0
        assert result.diagnostics["state_truth_sources"] == 1


def test_shadow_case_input_hash_matches_canonical_runtime_payload(repo_root: Path) -> None:
    for case in load_public_cases(repo_root):
        assert case.input_hash == sha256_json(case.payload)
        assert case.source_commitment_hash is not None


def test_w1_valid_controls_tolerate_irrelevant_fields(repo_root: Path, tmp_path: Path) -> None:
    controls = [case for case in load_public_cases(repo_root) if case.case_class == "valid control"]
    for repeat in range(5):
        for case in controls:
            payload = {**case.payload, "irrelevant_public_control": f"control-{repeat}"}
            derived = replace(
                case,
                payload=payload,
                input_hash=sha256_json(payload),
                case_id=f"{case.case_id}-NEG-{repeat}",
            )
            result, _ = run_case(
                repo_root,
                WorkflowGuardAdapter.architecture_id,
                derived,
                ISOLATED_STATE,
                _context(tmp_path, derived, repeat),
                persist=False,
            )
            assert result.decision.outcome == _expected(case)


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_w1_disabled_component_abstains_without_fallback(
    repo_root: Path, tmp_path: Path, component_id: str
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == component_id and item.case_class == "valid control"
    )
    context = replace(
        _context(tmp_path, case),
        enabled_components=tuple(item for item in COMPONENT_IDS if item != component_id),
    )
    result, _ = run_case(
        repo_root,
        WorkflowGuardAdapter.architecture_id,
        case,
        ISOLATED_STATE,
        context,
        persist=False,
    )
    assert result.decision.outcome == "ABSTAIN"
    assert result.decision.reason_codes == ("W1_COMPONENT_DISABLED_BY_FROZEN_ABLATION",)


def test_w1_claim_evidence_order_is_invariant(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "claim-evidence-support-gate" and item.case_class == "valid control"
    )
    evidence = list(case.payload["evidence"])
    extra = {
        **evidence[0],
        "evidence_id": "irrelevant",
    }
    decisions = []
    for ordered in (evidence + [extra], [extra] + evidence):
        result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "evidence": ordered})
        decisions.append((result.decision.outcome, result.decision.reason_codes))
    assert decisions[0] == decisions[1]
    assert decisions[0][0] == "PASS"


def test_w1_supported_challenge_proposes_exact_stale_closure(
    repo_root: Path, tmp_path: Path
) -> None:
    case = load_public_cases(repo_root)[0]
    payload = {**case.payload, "team_challenge": {"supported": True, "target": "input"}}
    result = _evaluate_payload(repo_root, tmp_path, case, payload)
    assert result.decision.outcome == "BLOCK"
    assert "W1_WORKFLOW_SUPPORTED_CHALLENGE_STALE" in result.decision.reason_codes
    assert result.diagnostics["stale_nodes"] == ("decision", "input", "run")


def test_w1_claim_scope_mismatch_blocks_despite_support_marker(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "claim-evidence-support-gate" and item.case_class == "valid control"
    )
    evidence = [{**case.payload["evidence"][0], "scope": "DIFFERENT_SCOPE"}]
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "evidence": evidence})
    assert result.decision.outcome == "BLOCK"
    assert "W1_CLAIM_EXACT_SUPPORT_MISSING" in result.decision.reason_codes


def test_w1_missing_reference_blocks_even_with_another_valid_reference(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "claim-evidence-support-gate" and item.case_class == "valid control"
    )
    evidence = [case.payload["evidence"][0], {"evidence_id": "missing", "registered": False}]
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "evidence": evidence})
    assert result.decision.outcome == "BLOCK"
    assert "W1_CLAIM_EVIDENCE_NOT_REGISTERED" in result.decision.reason_codes


def test_w1_manifest_rejects_shell_string_private_path_and_missing_environment(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "hash-bound-reproducibility-manifest"
        and item.case_class == "valid control"
    )
    manifest = dict(case.payload["manifest"])
    manifest.update({"command": "sh -c arbitrary", "cwd": "/" + "private"})
    manifest.pop("environment_hash")
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "manifest": manifest})
    assert result.decision.outcome == "BLOCK"
    assert {
        "W1_MANIFEST_REQUIRED_BINDING_MISSING",
        "W1_MANIFEST_ARGV_REQUIRED",
        "W1_MANIFEST_CWD_UNSAFE",
    } <= set(result.decision.reason_codes)


def test_w1_manifest_recomputes_bound_bytes_instead_of_trusting_observed(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "hash-bound-reproducibility-manifest"
        and item.case_class == "valid control"
    )
    capture = {**case.payload["trusted_capture"], "output_content": {"status": "mutated"}}
    result = _evaluate_payload(
        repo_root, tmp_path, case, {**case.payload, "trusted_capture": capture}
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_MANIFEST_BINDING_MISMATCH" in result.decision.reason_codes


def test_w1_comparison_rejects_unscheduled_retry_and_nontraining_transform(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    attempts = [{**case.payload["attempts"][0], "seed": 9999, "retry": True}]
    result = _evaluate_payload(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "attempts": attempts, "transform_fit_scope": "validation"},
    )
    assert result.decision.outcome == "BLOCK"
    assert {
        "W1_COMPARISON_TRANSFORM_LEAKAGE",
        "W1_COMPARISON_UNSCHEDULED_OR_NONTERMINAL_ATTEMPT",
        "W1_COMPARISON_UNAUTHORIZED_RETRY",
    } <= set(result.decision.reason_codes)


def test_w1_comparison_rejects_additional_test_access(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "gaming attempt"
    )
    result = _evaluate_payload(repo_root, tmp_path, case, dict(case.payload))
    assert result.decision.outcome == "BLOCK"
    assert "W1_COMPARISON_PREMATURE_TEST_ACCESS" in result.decision.reason_codes


@pytest.mark.parametrize(
    ("component_id", "field", "value"),
    [
        ("accepted-versus-done-workflow-state", "dependency_graph", {"input": None}),
        ("leakage-safe-model-comparison-gate", "access_events", ["malformed"]),
    ],
)
def test_w1_malformed_input_returns_reason_coded_terminal_result(
    repo_root: Path, tmp_path: Path, component_id: str, field: str, value: object
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == component_id and item.case_class == "valid control"
    )
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, field: value})
    assert result.decision.outcome == "BLOCK"
    assert result.decision.reason_codes


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("splits", [], "W1_COMPARISON_SPLIT_INVALID"),
        ("splits", None, "W1_COMPARISON_SPLIT_INVALID"),
        ("splits", "invalid", "W1_COMPARISON_SPLIT_INVALID"),
        (
            "splits",
            {"train": [[]], "validation": ["v"], "test": ["t"]},
            "W1_COMPARISON_SPLIT_INVALID",
        ),
        ("validation_scores", {"a": "invalid", "b": None}, "W1_COMPARISON_NO_VALID_CANDIDATE"),
        ("validation_scores", {}, "W1_COMPARISON_NO_VALID_CANDIDATE"),
    ],
)
def test_w1_comparison_malformed_variants_fail_closed(
    repo_root: Path,
    tmp_path: Path,
    field: str,
    value: object,
    reason: str,
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, field: value})
    assert result.decision.outcome == "BLOCK"
    assert reason in result.decision.reason_codes
    assert result.terminal_status in {"COMPLETED", "FAILED_RETAINED"}


@pytest.mark.parametrize("score", [float("nan"), float("inf"), float("-inf")])
def test_w1_nonfinite_scores_are_reason_coded_before_canonical_capture(
    repo_root: Path, score: float
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    passed, reasons, _ = comparison_checklist(
        {**case.payload, "validation_scores": {"a": score, "b": 0.7}}, ISOLATED_STATE
    )
    assert not passed
    assert "W1_COMPARISON_NONFINITE_SELECTION_METRIC" in reasons


def test_w1_empty_tie_set_path_fails_closed_without_index_error(repo_root: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    malformed_state = {
        **ISOLATED_STATE,
        "comparison_policy": {
            **ISOLATED_STATE["comparison_policy"],
            "tie_tolerance": float("nan"),
        },
    }
    passed, reasons, _ = comparison_checklist(dict(case.payload), malformed_state)
    assert not passed
    assert "W1_COMPARISON_POLICY_INVALID" in reasons


def test_w1_required_component_dependencies_are_noncompensatory(
    repo_root: Path, tmp_path: Path
) -> None:
    case = load_public_cases(repo_root)[0]
    payload = {
        **case.payload,
        "upstream_gates": {
            **case.payload["upstream_gates"],
            "leakage-safe-model-comparison-gate": {
                **case.payload["upstream_gates"]["leakage-safe-model-comparison-gate"],
                "outcome": "BLOCK",
            },
        },
    }
    result = _evaluate_payload(repo_root, tmp_path, case, payload)
    assert result.decision.outcome == "BLOCK"
    assert "W1_WORKFLOW_REQUIRED_GATE_NOT_PASS" in result.decision.reason_codes


def test_w1_claim_rejects_path_escape_and_causal_claim_without_identification(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "claim-evidence-support-gate" and item.case_class == "valid control"
    )
    evidence = [{**case.payload["evidence"][0], "locator": "../../vault/escape.json"}]
    claim = {**case.payload["claim"], "claim_type": "CAUSAL"}
    result = _evaluate_payload(
        repo_root, tmp_path, case, {**case.payload, "claim": claim, "evidence": evidence}
    )
    assert result.decision.outcome == "BLOCK"
    assert {
        "W1_CLAIM_EVIDENCE_LOCATOR_UNSAFE",
        "W1_CLAIM_EVIDENCE_REGISTRY_MISMATCH",
        "W1_CLAIM_CAUSAL_SUPPORT_INADEQUATE",
    } <= set(result.decision.reason_codes)


def test_w1_manifest_rejects_unknown_outcome(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "hash-bound-reproducibility-manifest"
        and item.case_class == "valid control"
    )
    manifest = {**case.payload["manifest"], "outcome": "UNKNOWN_VALUE"}
    capture = {**case.payload["trusted_capture"], "outcome": "UNKNOWN_VALUE"}
    result = _evaluate_payload(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "manifest": manifest, "trusted_capture": capture},
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_MANIFEST_OUTCOME_NOT_SUCCESS:UNKNOWN_VALUE" in result.decision.reason_codes


def test_w1_comparison_requires_complete_candidate_seed_matrix(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    attempts = list(case.payload["attempts"][:-1])
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "attempts": attempts})
    assert result.decision.outcome == "BLOCK"
    assert "W1_COMPARISON_CANDIDATE_SEED_MATRIX_INCOMPLETE" in result.decision.reason_codes


def test_w1_final_test_requires_after_model_freeze_true(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    event_body = {
        "ordinal": 1,
        "kind": "FINAL_TEST_BATCH",
        "after_model_freeze": False,
        "prior_hash": "0" * 64,
    }
    events = [{**event_body, "event_hash": sha256_json(event_body)}]
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "access_events": events})
    assert result.decision.outcome == "BLOCK"
    assert "W1_COMPARISON_PREMATURE_TEST_ACCESS" in result.decision.reason_codes


def test_w1_supported_challenge_ignores_unrelated_branch(repo_root: Path, tmp_path: Path) -> None:
    case = load_public_cases(repo_root)[0]
    payload = {
        **case.payload,
        "dependency_graph": {
            "input": ["run"],
            "run": ["decision"],
            "unrelated": ["leaf"],
        },
        "team_challenge": {"supported": True, "target": "input"},
    }
    result = _evaluate_payload(repo_root, tmp_path, case, payload)
    assert result.diagnostics["stale_nodes"] == ("decision", "input", "run")


def test_w1_interactions_bind_run_decision_and_audit_hashes(
    repo_root: Path, tmp_path: Path
) -> None:
    case = load_public_cases(repo_root)[0]
    gate = dict(case.payload["upstream_gates"]["claim-evidence-support-gate"])
    gate["run_id"] = "attacker-run"
    upstream = {**case.payload["upstream_gates"], "claim-evidence-support-gate": gate}
    result = _evaluate_payload(
        repo_root, tmp_path, case, {**case.payload, "upstream_gates": upstream}
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_WORKFLOW_REQUIRED_GATE_NOT_PASS" in result.decision.reason_codes


def test_shadow_case_input_rejects_payload_hash_mismatch(repo_root: Path) -> None:
    case = load_public_cases(repo_root)[0]
    with pytest.raises(ValueError, match="SHADOW_CASE_INPUT_HASH_MISMATCH"):
        replace(case, input_hash="0" * 64)


def test_w1_privacy_filter_allows_benign_words(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "hash-bound-reproducibility-manifest"
        and item.case_class == "valid control"
    )
    baseline = _evaluate_payload(repo_root, tmp_path, case, dict(case.payload))
    payload = {**case.payload, "token_budget": 0, "secretariat_label": "public"}
    result = _evaluate_payload(repo_root, tmp_path, case, payload)
    assert result.decision.outcome == baseline.decision.outcome == "PASS"
    assert "W1_MANIFEST_PRIVATE_FIELD_REJECTED" not in result.decision.reason_codes


def test_w1_claim_semantics_are_derived_from_hashed_artifact_body(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "claim-evidence-support-gate" and item.case_class == "valid control"
    )
    evidence = dict(case.payload["evidence"][0])
    body = {**evidence["artifact_body"], "bounded_proposition": "A forged proposition."}
    forged_hash = sha256_json(body)
    evidence.update(
        {
            "artifact_body": body,
            "artifact_hash": forged_hash,
            "registry_hash": sha256_json(
                {"locator": evidence["locator"], "artifact_hash": forged_hash}
            ),
        }
    )
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "evidence": [evidence]})
    assert result.decision.outcome == "BLOCK"
    assert {
        "W1_CLAIM_EVIDENCE_HASH_INVALID",
        "W1_CLAIM_EVIDENCE_SEMANTIC_BINDING_MISMATCH",
        "W1_CLAIM_EXACT_SUPPORT_MISSING",
    } <= set(result.decision.reason_codes)


def test_w1_rejects_reforged_untrusted_gate_record(repo_root: Path, tmp_path: Path) -> None:
    case = load_public_cases(repo_root)[0]
    component = "claim-evidence-support-gate"
    gate = {**case.payload["upstream_gates"][component], "run_id": "attacker-run"}
    gate["artifact_hash"] = sha256_json(
        {
            key: gate[key]
            for key in (
                "component_id",
                "decision_id",
                "run_id",
                "authority",
                "outcome",
                "current",
                "audited",
            )
        }
    )
    upstream = {**case.payload["upstream_gates"], component: gate}
    result = _evaluate_payload(
        repo_root, tmp_path, case, {**case.payload, "upstream_gates": upstream}
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_WORKFLOW_REQUIRED_GATE_NOT_PASS" in result.decision.reason_codes


def test_w1_stage_records_bind_authority_and_hashed_body(repo_root: Path, tmp_path: Path) -> None:
    case = load_public_cases(repo_root)[0]
    records = {key: dict(value) for key, value in case.payload["evidence_records"].items()}
    stage = "COMMAND_COMPLETED"
    body = {"stage": stage, "run_id": "attacker-run"}
    records[stage].update({"artifact_body": body, "artifact_hash": sha256_json(body)})
    result = _evaluate_payload(
        repo_root, tmp_path, case, {**case.payload, "evidence_records": records}
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_WORKFLOW_STAGE_HASH_INVALID" in result.decision.reason_codes


def test_w1_comparison_rejects_duplicate_or_extra_attempt(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    attempts = [*case.payload["attempts"], dict(case.payload["attempts"][0])]
    result = _evaluate_payload(repo_root, tmp_path, case, {**case.payload, "attempts": attempts})
    assert result.decision.outcome == "BLOCK"
    assert "W1_COMPARISON_CANDIDATE_SEED_MATRIX_INCOMPLETE" in result.decision.reason_codes


def test_w1_comparison_requires_exact_manifest_attempt_bijection(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    manifests = [*case.payload["verified_run_manifests"], case.payload["verified_run_manifests"][0]]
    result = _evaluate_payload(
        repo_root, tmp_path, case, {**case.payload, "verified_run_manifests": manifests}
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_COMPARISON_VERIFIED_RUNS_REQUIRED" in result.decision.reason_codes


def test_w1_comparison_applies_frozen_metric_direction_and_tie_rule(
    repo_root: Path, tmp_path: Path
) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "leakage-safe-model-comparison-gate"
        and item.case_class == "valid control"
    )
    payload = {
        **case.payload,
        "metric_direction": "MINIMIZE",
        "selected_candidate_id": "b",
        "selected_candidate_matches_validation": True,
    }
    result = _evaluate_payload(repo_root, tmp_path, case, payload)
    assert result.decision.outcome == "BLOCK"
    assert {
        "W1_COMPARISON_POLICY_NOT_FROZEN",
        "W1_COMPARISON_SELECTION_MISMATCH",
    } <= set(result.decision.reason_codes)


def test_w1_manifest_requires_nonempty_registered_run_id(repo_root: Path, tmp_path: Path) -> None:
    case = next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == "hash-bound-reproducibility-manifest"
        and item.case_class == "valid control"
    )
    manifest = {**case.payload["manifest"], "run_id": ""}
    capture = {**case.payload["trusted_capture"], "run_id": ""}
    result = _evaluate_payload(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "manifest": manifest, "trusted_capture": capture},
    )
    assert result.decision.outcome == "BLOCK"
    assert "W1_MANIFEST_REGISTERED_RUN_REQUIRED" in result.decision.reason_codes
