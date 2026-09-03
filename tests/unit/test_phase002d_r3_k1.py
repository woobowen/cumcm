from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from cumcm_skill_lab.shadow_validation.grader import grade_result
from cumcm_skill_lab.shadow_validation.runner import run_case
from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.arch_k1 import DeterministicEvidenceKernel
from experiments.shadow_prototypes.arch_k1.kernel import evaluate_composed_evidence_package
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
        run_id=f"R3-K1-{case.case_id}-{ordinal}",
        architecture_id=DeterministicEvidenceKernel.architecture_id,
        stage="PUBLIC_VALIDATION",
        output_dir=tmp_path / case.case_id / str(ordinal),
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=COMPONENT_IDS,
    )


def _evaluate(
    root: Path,
    tmp_path: Path,
    case: ShadowCaseInput,
    payload: dict[str, object],
    state: dict[str, object] | None = None,
):
    derived = replace(case, payload=payload, input_hash=sha256_json(payload))
    return run_case(
        root,
        DeterministicEvidenceKernel.architecture_id,
        derived,
        state or ISOLATED_STATE,
        _context(tmp_path, derived),
        persist=False,
    )[0]


def _case(root: Path, component_id: str, case_class: str = "valid control") -> ShadowCaseInput:
    return next(
        case
        for case in load_public_cases(root)
        if case.component_id == component_id and case.case_class == case_class
    )


def test_k1_satisfies_all_public_conformance_relations(repo_root: Path, tmp_path: Path) -> None:
    for index, case in enumerate(load_public_cases(repo_root)):
        result, unchanged = run_case(
            repo_root,
            DeterministicEvidenceKernel.architecture_id,
            case,
            ISOLATED_STATE,
            _context(tmp_path, case, index),
            persist=False,
        )
        expected = "PASS" if case.case_class == "valid control" else "BLOCK"
        grade = grade_result(result, {"expected_outcome": expected}, input_unchanged=unchanged)
        assert grade["passed"], (case.case_id, result.decision.reason_codes)
        assert result.diagnostics["formal_state_writes"] == 0
        assert result.diagnostics["state_truth_sources"] == 1
        assert result.diagnostics["hidden_vault_accesses"] == 0


def test_k1_valid_controls_are_stable_under_irrelevant_fields(
    repo_root: Path, tmp_path: Path
) -> None:
    controls = [case for case in load_public_cases(repo_root) if case.case_class == "valid control"]
    for case in controls:
        decisions = []
        for ordinal in range(5):
            result = _evaluate(
                repo_root,
                tmp_path,
                case,
                {**case.payload, "irrelevant_public_control": f"control-{ordinal}"},
            )
            decisions.append((result.decision.outcome, result.decision.reason_codes))
        assert len(set(decisions)) == 1
        assert decisions[0] == ("PASS", ("K1_ALL_DETERMINISTIC_CHECKS_PASS",))


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_k1_disabled_component_abstains_without_fallback(
    repo_root: Path, tmp_path: Path, component_id: str
) -> None:
    case = _case(repo_root, component_id)
    context = replace(
        _context(tmp_path, case),
        enabled_components=tuple(item for item in COMPONENT_IDS if item != component_id),
    )
    result, _ = run_case(
        repo_root,
        DeterministicEvidenceKernel.architecture_id,
        case,
        ISOLATED_STATE,
        context,
        persist=False,
    )
    assert result.decision.outcome == "ABSTAIN"
    assert result.decision.reason_codes == ("K1_COMPONENT_DISABLED_BY_FROZEN_ABLATION",)


def test_k1_rejects_second_state_truth(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    state = {**ISOLATED_STATE, "truth_source": "shadow/second-state.json"}
    result, _ = run_case(
        repo_root,
        DeterministicEvidenceKernel.architecture_id,
        case,
        state,
        _context(tmp_path, case),
        persist=False,
    )
    assert result.decision.outcome == "BLOCK"
    assert "K1_SINGLE_STATE_TRUTH_REQUIRED" in result.decision.reason_codes


def test_k1_lifecycle_preserves_distinct_stages_and_exact_stale_closure(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    missing = list(case.payload["evidenced_stages"][:-1])
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "evidenced_stages": missing, "changed_nodes": ["input"]},
    )
    assert result.decision.outcome == "BLOCK"
    assert {
        "K1_LIFECYCLE_SKIPPED_OR_UNEVIDENCED_STAGE",
        "K1_LIFECYCLE_STALE_DEPENDENCY",
    } <= set(result.decision.reason_codes)
    assert result.diagnostics["stale_nodes"] == ("decision", "input", "run")


def test_k1_lifecycle_rejects_resigned_untrusted_stage_and_gate(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    records = {key: dict(value) for key, value in case.payload["evidence_records"].items()}
    stage = "COMMAND_COMPLETED"
    body = {"stage": stage, "run_id": "forged-run"}
    records[stage].update({"artifact_body": body, "artifact_hash": sha256_json(body)})
    component = "claim-evidence-support-gate"
    gates = {key: dict(value) for key, value in case.payload["upstream_gates"].items()}
    gates[component]["run_id"] = "forged-run"
    gates[component]["artifact_hash"] = sha256_json(
        {
            key: gates[component][key]
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
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "evidence_records": records, "upstream_gates": gates},
    )
    assert result.decision.outcome == "BLOCK"
    assert any(
        code.startswith("K1_LIFECYCLE_STAGE_EVIDENCE_INVALID")
        for code in result.decision.reason_codes
    )
    assert "K1_LIFECYCLE_REQUIRED_GATE_NOT_PASS" in result.decision.reason_codes


def test_k1_claim_support_is_hash_bound_order_invariant_and_duplicate_idempotent(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    item = dict(case.payload["evidence"][0])
    duplicate = {**item, "evidence_id": "duplicate"}
    left = _evaluate(repo_root, tmp_path, case, {**case.payload, "evidence": [item, duplicate]})
    right = _evaluate(repo_root, tmp_path, case, {**case.payload, "evidence": [duplicate, item]})
    assert left.decision.outcome == right.decision.outcome == "PASS"
    assert left.decision.reason_codes == right.decision.reason_codes
    assert left.diagnostics["supporting_evidence"] == right.diagnostics["supporting_evidence"]

    body = {**item["artifact_body"], "bounded_proposition": "forged"}
    forged_hash = sha256_json(body)
    item.update(
        {
            "artifact_body": body,
            "artifact_hash": forged_hash,
            "registry_hash": sha256_json(
                {"locator": item["locator"], "artifact_hash": forged_hash}
            ),
        }
    )
    blocked = _evaluate(repo_root, tmp_path, case, {**case.payload, "evidence": [item]})
    assert blocked.decision.outcome == "BLOCK"
    assert {
        "K1_CLAIM_EVIDENCE_BINDING_INVALID",
        "K1_CLAIM_SEMANTIC_BINDING_INVALID",
        "K1_CLAIM_EXACT_SUPPORT_MISSING",
    } <= set(blocked.decision.reason_codes)


def test_k1_claim_rejects_contradiction_stale_and_causal_overstatement(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    evidence = [{**case.payload["evidence"][0], "contradicts": ["claim-1"], "current": False}]
    claim = {**case.payload["claim"], "claim_type": "CAUSAL"}
    result = _evaluate(
        repo_root, tmp_path, case, {**case.payload, "claim": claim, "evidence": evidence}
    )
    assert {
        "K1_CLAIM_CONTRADICTION",
        "K1_CLAIM_STALE_EVIDENCE",
        "K1_CLAIM_CAUSAL_IDENTIFICATION_INADEQUATE",
    } <= set(result.decision.reason_codes)


def test_k1_reproducibility_is_canonical_and_detects_mutation(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    original = _evaluate(repo_root, tmp_path, case, dict(case.payload))
    reordered_manifest = dict(reversed(list(case.payload["manifest"].items())))
    reordered = _evaluate(
        repo_root, tmp_path, case, {**case.payload, "manifest": reordered_manifest}
    )
    assert original.decision.outcome == reordered.decision.outcome == "PASS"
    assert (
        original.diagnostics["canonical_manifest_hash"]
        == reordered.diagnostics["canonical_manifest_hash"]
    )
    capture = {**case.payload["trusted_capture"], "output_content": {"status": "mutated"}}
    blocked = _evaluate(repo_root, tmp_path, case, {**case.payload, "trusted_capture": capture})
    assert "K1_REPRO_MUTATION_OR_BINDING_MISMATCH" in blocked.decision.reason_codes


def test_k1_reproducibility_retains_failures_and_redacts_private_fields(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    manifest = {**case.payload["manifest"], "outcome": "FAILED"}
    capture = {**case.payload["trusted_capture"], "outcome": "FAILED"}
    payload = {
        **case.payload,
        "manifest": manifest,
        "trusted_capture": capture,
        "api_key": "must-not-appear",
    }
    result = _evaluate(repo_root, tmp_path, case, payload)
    assert result.decision.outcome == "BLOCK"
    assert "K1_REPRO_TERMINAL_NON_SUCCESS_RETAINED:FAILED" in result.decision.reason_codes
    assert result.diagnostics["private_fields_redacted"] == 1
    assert "must-not-appear" not in str(result.to_dict())


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("splits", [], "K1_COMPARISON_SPLIT_INVALID"),
        ("validation_scores", {"a": "nan", "b": 0.7}, "K1_COMPARISON_SCORE_INVALID"),
    ],
)
def test_k1_comparison_malformed_input_is_reason_coded_fail_closed(
    repo_root: Path, tmp_path: Path, field: str, value: object, reason: str
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, field: value})
    assert result.decision.outcome == "BLOCK"
    assert reason in result.decision.reason_codes


def test_k1_comparison_rejects_boolean_scores(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "validation_scores": {"a": True, "b": 0.7}},
    )
    assert result.decision.outcome == "BLOCK"
    assert "K1_COMPARISON_SCORE_INVALID" in result.decision.reason_codes


def test_k1_comparison_rejects_failed_attempt_still_scored(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    attempts = [dict(item) for item in case.payload["attempts"]]
    attempts[0].update({"outcome": "FAILED", "failure_class": "MODEL"})
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "attempts": attempts})
    assert result.decision.outcome == "BLOCK"
    assert "K1_COMPARISON_FAILED_ATTEMPT_SCORED" in result.decision.reason_codes


def test_k1_comparison_enforces_attempt_and_manifest_bijections(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    attempts = [*case.payload["attempts"], dict(case.payload["attempts"][0])]
    manifests = [
        *case.payload["verified_run_manifests"],
        case.payload["verified_run_manifests"][0],
    ]
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "attempts": attempts, "verified_run_manifests": manifests},
    )
    assert {
        "K1_COMPARISON_CANDIDATE_SEED_BIJECTION_INVALID",
        "K1_COMPARISON_RUN_MANIFEST_BIJECTION_INVALID",
    } <= set(result.decision.reason_codes)


def test_k1_comparison_uses_frozen_direction_tolerance_and_tie_key(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {
            **case.payload,
            "metric_direction": "MINIMIZE",
            "selected_candidate_id": "b",
        },
    )
    assert result.decision.outcome == "BLOCK"
    assert {
        "K1_COMPARISON_POLICY_NOT_FROZEN",
        "K1_COMPARISON_SELECTION_MISMATCH",
    } <= set(result.decision.reason_codes)


def test_k1_comparison_rejects_any_early_or_second_test_access(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    first = dict(case.payload["access_events"][0])
    body = {
        "ordinal": 2,
        "kind": "FINAL_TEST_BATCH",
        "after_model_freeze": True,
        "prior_hash": first["event_hash"],
    }
    events = [first, {**body, "event_hash": sha256_json(body)}]
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "access_events": events})
    assert "K1_COMPARISON_FINAL_TEST_COUNT_INVALID" in result.decision.reason_codes


def test_k1_malformed_kernel_exception_is_retained_as_terminal_block(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "evidenced_stages": [{"unhashable": []}]},
    )
    assert result.decision.outcome == "BLOCK"
    assert result.decision.reason_codes


def test_k1_lifecycle_rejects_cyclic_unregistered_or_untrusted_dependency_graph(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    graph = {"input": ["run"], "run": ["input"]}
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "dependency_graph": graph, "dependency_graph_hash": sha256_json(graph)},
    )
    assert result.decision.outcome == "BLOCK"
    assert {
        "K1_LIFECYCLE_UNTRUSTED_DEPENDENCY_GRAPH",
        "K1_LIFECYCLE_DEPENDENCY_GRAPH_INVALID",
    } <= set(result.decision.reason_codes)


@pytest.mark.parametrize("state_name", ["STALE", "AUTOMATED_REJECTED"])
def test_k1_lifecycle_supports_audited_rejection_and_stale_states(
    repo_root: Path, tmp_path: Path, state_name: str
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    disposition = {
        "state": state_name,
        "authority": "existing-state-transition-ledger",
        "audited": True,
        "hard_gate_failure": state_name == "AUTOMATED_REJECTED",
    }
    disposition["artifact_hash"] = sha256_json(disposition)
    state = {
        **ISOLATED_STATE,
        "trusted_disposition_hashes": {state_name: disposition["artifact_hash"]},
    }
    payload = {
        **case.payload,
        "requested_state": state_name,
        "evidenced_stages": [],
        "evidence_records": {},
        "changed_nodes": ["input"] if state_name == "STALE" else [],
        "disposition_record": disposition,
    }
    result = _evaluate(repo_root, tmp_path, case, payload, state)
    assert result.decision.outcome == "PASS"


def test_k1_supported_challenge_requires_finding_test_and_readjudication_records(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    challenge = {"supported": True, "target": "input"}
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "team_challenge": challenge})
    assert result.decision.outcome == "BLOCK"
    assert "K1_LIFECYCLE_CHALLENGE_EVIDENCE_INVALID" in result.decision.reason_codes


def test_k1_rejects_any_second_state_or_ledger_authority(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    state = {**ISOLATED_STATE, "second_truth": "shadow/state.json"}
    result = _evaluate(repo_root, tmp_path, case, dict(case.payload), state)
    assert result.decision.outcome == "BLOCK"
    assert "K1_SECOND_STATE_OR_LEDGER_AUTHORITY_REJECTED" in result.decision.reason_codes


def test_k1_rejects_nonfrozen_claim_type_aliases(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    claim = {**case.payload["claim"], "claim_type": "RESULT"}
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "claim": claim})
    assert result.decision.outcome == "BLOCK"
    assert "K1_CLAIM_TYPE_INVALID" in result.decision.reason_codes


def test_k1_uses_moderate_and_strong_noncompensatory_thresholds(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    evidence = dict(case.payload["evidence"][0])
    body = {**evidence["artifact_body"], "strength": "WEAK"}
    artifact_hash = sha256_json(body)
    evidence.update(
        {
            "strength": "WEAK",
            "artifact_body": body,
            "artifact_hash": artifact_hash,
            "registry_hash": sha256_json(
                {"locator": evidence["locator"], "artifact_hash": artifact_hash}
            ),
        }
    )
    state = {
        **ISOLATED_STATE,
        "trusted_artifact_hashes": {evidence["locator"]: artifact_hash},
    }
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "evidence": [evidence]}, state)
    assert result.decision.outcome == "BLOCK"
    assert "K1_CLAIM_EXACT_SUPPORT_MISSING" in result.decision.reason_codes


def test_k1_indeterminate_semantic_support_returns_abstained(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "semantic_review": {"relation": "ABSTAIN"}},
    )
    assert result.decision.outcome == "ABSTAIN"
    assert result.diagnostics["disposition"] == "ABSTAINED"


def test_k1_claim_artifact_cannot_be_rebound_to_another_run(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    new_run = "a-1729"
    claim = {**case.payload["claim"], "run_id": new_run}
    evidence = [{**case.payload["evidence"][0], "run_id": new_run}]
    comparison = _case(repo_root, "leakage-safe-model-comparison-gate")
    manifest = next(
        item for item in comparison.payload["verified_run_manifests"] if item["run_id"] == new_run
    )
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {
            **case.payload,
            "claim": claim,
            "evidence": evidence,
            "verified_run_manifest": manifest,
        },
    )
    assert result.decision.outcome == "BLOCK"
    assert {
        "K1_CLAIM_TRUSTED_RUN_BINDING_INVALID",
        "K1_CLAIM_SEMANTIC_BINDING_INVALID",
    } <= set(result.decision.reason_codes)


def test_k1_claim_rejects_superseded_revision_and_preserves_contradiction(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "claim-evidence-support-gate")
    evidence = [
        {
            **case.payload["evidence"][0],
            "superseded": True,
            "contradicts": ["claim-1"],
        }
    ]
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "evidence": evidence})
    assert {
        "K1_CLAIM_SUPERSEDED_EVIDENCE",
        "K1_CLAIM_CONTRADICTION",
    } <= set(result.decision.reason_codes)


@pytest.mark.parametrize(
    ("capture_field", "replacement"),
    [
        ("input_content", {"records": [99]}),
        ("code_commit", "3" * 40),
        ("config_content", {"mode": "changed"}),
        ("output_content", {"status": "changed"}),
        ("environment", {"python": "9.9"}),
        ("dependencies", {"project": "changed"}),
    ],
)
def test_k1_repro_rejects_jointly_resigned_untrusted_capture(
    repo_root: Path, tmp_path: Path, capture_field: str, replacement: object
) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    capture = {**case.payload["trusted_capture"], capture_field: replacement}
    manifest = dict(case.payload["manifest"])
    binding_fields = {
        "input_content": "input_hash",
        "code_commit": "code_commit",
        "config_content": "config_hash",
        "output_content": "output_hash",
        "environment": "environment_hash",
        "dependencies": "dependency_hash",
    }
    target = binding_fields[capture_field]
    manifest[target] = replacement if target == "code_commit" else sha256_json(replacement)
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "manifest": manifest, "trusted_capture": capture},
    )
    assert {
        "K1_REPRO_NATIVE_MANIFEST_BINDING_INVALID",
        "K1_REPRO_TRUSTED_CAPTURE_BINDING_INVALID",
    } <= set(result.decision.reason_codes)


def test_k1_repro_enforces_unique_current_manifest_revision_chain(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    manifest = {**case.payload["manifest"], "current": False}
    capture = {**case.payload["trusted_capture"], "current": False}
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "manifest": manifest, "trusted_capture": capture},
    )
    assert "K1_REPRO_REVISION_OR_AUTHORITY_INVALID" in result.decision.reason_codes


def test_k1_canonical_json_rejects_nan_inf_and_ambiguous_values(repo_root: Path) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    with pytest.raises(ValueError, match="Out of range float values"):
        replace(
            case,
            payload={**case.payload, "ambiguous": float("nan")},
            input_hash="0" * 64,
        )


def test_k1_repro_rejects_shell_only_argv(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    command = ["sh", "-c", "printf ok"]
    manifest = {**case.payload["manifest"], "command": command}
    capture = {**case.payload["trusted_capture"], "command": command}
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "manifest": manifest, "trusted_capture": capture},
    )
    assert "K1_REPRO_SHELL_ONLY_ARGV_REJECTED" in result.decision.reason_codes


@pytest.mark.parametrize(
    ("payload_update", "reason"),
    [
        (
            {"client_secret": "synthetic-private-value"},
            "K1_REPRO_PRIVATE_FIELD_REDACTED_AND_REJECTED",
        ),
        ({"cwd": "C:\\private\\run"}, "K1_REPRO_CWD_INVALID"),
        ({"command": ["python", "C:\\private\\runner.py"]}, "K1_REPRO_COMMAND_PATH_REJECTED"),
    ],
)
def test_k1_repro_rejects_extended_private_and_absolute_path_surface(
    repo_root: Path,
    tmp_path: Path,
    payload_update: dict[str, object],
    reason: str,
) -> None:
    case = _case(repo_root, "hash-bound-reproducibility-manifest")
    payload = dict(case.payload)
    if "cwd" in payload_update or "command" in payload_update:
        manifest = {**case.payload["manifest"], **payload_update}
        capture = {**case.payload["trusted_capture"], **payload_update}
        payload.update({"manifest": manifest, "trusted_capture": capture})
    else:
        payload.update(payload_update)
    result = _evaluate(repo_root, tmp_path, case, payload)
    assert result.decision.outcome == "BLOCK"
    assert reason in result.decision.reason_codes


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("candidate_freeze_hash", "z" * 64, "K1_COMPARISON_FREEZE_INVALID"),
        ("metric_freeze_hash", "0" * 64, "K1_COMPARISON_FREEZE_INVALID"),
    ],
)
def test_k1_comparison_rejects_nonhex_or_untrusted_freeze_hash(
    repo_root: Path, tmp_path: Path, field: str, value: str, reason: str
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, field: value})
    assert result.decision.outcome == "BLOCK"
    assert any(code.startswith(reason) for code in result.decision.reason_codes)


def test_k1_comparison_candidate_and_seed_sets_match_frozen_registry_exactly(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    attempts = [item for item in case.payload["attempts"] if item["candidate_id"] == "a"]
    manifests = [
        item for item in case.payload["verified_run_manifests"] if item["run_id"].startswith("a-")
    ]
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {
            **case.payload,
            "frozen_seeds": [1729],
            "validation_scores": {"a": 0.8},
            "attempts": [item for item in attempts if item["seed"] == 1729],
            "verified_run_manifests": [item for item in manifests if item["run_id"] == "a-1729"],
        },
    )
    assert {
        "K1_COMPARISON_CANDIDATE_SET_NOT_FROZEN",
        "K1_COMPARISON_SEED_SCHEDULE_NOT_FROZEN",
    } <= set(result.decision.reason_codes)


def test_k1_comparison_binds_complete_design_bundle(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {**case.payload, "time_order_valid": False},
    )
    assert "K1_COMPARISON_DESIGN_BINDING_INVALID" in result.decision.reason_codes


def test_k1_access_ledger_rejects_rewritten_prefix_against_trusted_head(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate", "gaming attempt")
    original = case.payload["access_events"][-1]
    body = {
        **{key: original[key] for key in original if key != "event_hash"},
        "ordinal": 1,
        "prior_hash": "0" * 64,
    }
    event = {**body, "event_hash": sha256_json(body)}
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "access_events": [event]})
    assert "K1_COMPARISON_ACCESS_HEAD_NOT_TRUSTED" in result.decision.reason_codes


def test_k1_access_event_binds_run_freeze_pretest_and_irreversible_exposure(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    event = dict(case.payload["access_events"][0])
    body = {
        **{key: value for key, value in event.items() if key != "event_hash"},
        "run_id": "a-1729",
    }
    event = {**body, "event_hash": sha256_json(body)}
    state = {**ISOLATED_STATE, "exposed_test_set_ids": [case.payload["test_set_id"]]}
    result = _evaluate(repo_root, tmp_path, case, {**case.payload, "access_events": [event]}, state)
    assert {
        "K1_COMPARISON_ACCESS_EVENT_BINDING_INVALID",
        "K1_COMPARISON_EXPOSED_TEST_SET_REJECTED",
    } <= set(result.decision.reason_codes)


def test_k1_authorized_infrastructure_retry_has_new_manifest_and_retains_failure(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    attempts = [dict(item) for item in case.payload["attempts"]]
    failed = attempts[0]
    failed.update({"outcome": "FAILED", "failure_class": "INFRASTRUCTURE"})
    retry_run = "a-1729-retry-1"
    retry = {
        **failed,
        "run_id": retry_run,
        "outcome": "SUCCESS",
        "failure_class": "NONE",
        "retry": True,
        "infrastructure_failure": True,
        "predecessor_run_id": failed["run_id"],
    }
    attempts.append(retry)
    manifest = {
        "run_id": retry_run,
        "decision_id": f"manifest-decision:{retry_run}",
        "authority": "existing-native-run-ledger",
        "status": "PASS",
        "current": True,
        "audited": True,
        "artifact_hash": sha256_json({"run_id": retry_run, "status": "PASS"}),
    }
    state = {
        **ISOLATED_STATE,
        "trusted_run_ids": [*ISOLATED_STATE["trusted_run_ids"], retry_run],
        "trusted_manifest_hashes": {
            **ISOLATED_STATE["trusted_manifest_hashes"],
            retry_run: manifest["artifact_hash"],
        },
    }
    result = _evaluate(
        repo_root,
        tmp_path,
        case,
        {
            **case.payload,
            "attempts": attempts,
            "verified_run_manifests": [*case.payload["verified_run_manifests"], manifest],
        },
        state,
    )
    assert result.decision.outcome == "PASS"


def test_k1_semantic_set_permutations_preserve_component_artifact_hash(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "leakage-safe-model-comparison-gate")
    original = _evaluate(repo_root, tmp_path, case, dict(case.payload))
    permuted = _evaluate(
        repo_root,
        tmp_path,
        case,
        {
            **case.payload,
            "frozen_seeds": list(reversed(case.payload["frozen_seeds"])),
            "attempts": list(reversed(case.payload["attempts"])),
            "verified_run_manifests": list(reversed(case.payload["verified_run_manifests"])),
        },
    )
    assert original.decision.outcome == permuted.decision.outcome == "PASS"
    assert (
        original.artifact_hashes["component_result"] == permuted.artifact_hashes["component_result"]
    )


def test_k1_rejects_non_shadow_execution_stage(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    context = replace(_context(tmp_path, case), stage="PRODUCTION")
    result, _ = run_case(
        repo_root,
        DeterministicEvidenceKernel.architecture_id,
        case,
        ISOLATED_STATE,
        context,
        persist=False,
    )
    assert result.decision.outcome == "BLOCK"
    assert "K1_NON_SHADOW_EXECUTION_STAGE_REJECTED" in result.decision.reason_codes


def test_k1_malformed_isolated_state_fails_closed(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    result, _ = run_case(
        repo_root,
        DeterministicEvidenceKernel.architecture_id,
        case,
        None,  # type: ignore[arg-type]
        _context(tmp_path, case),
        persist=False,
    )
    assert result.decision.outcome == "BLOCK"
    assert result.decision.reason_codes == ("K1_STATE_BUNDLE_MALFORMED",)


def test_k1_candidate_composes_all_components_and_propagates_failure(repo_root: Path) -> None:
    valid_payloads = {
        component_id: dict(_case(repo_root, component_id).payload) for component_id in COMPONENT_IDS
    }
    passed, reasons, diagnostics = evaluate_composed_evidence_package(
        valid_payloads, ISOLATED_STATE
    )
    assert passed
    assert reasons == ()
    package = diagnostics["evidence_package"]
    assert package["status"] == "ELIGIBLE"
    assert set(package["component_results"]) == set(COMPONENT_IDS)
    assert diagnostics["evidence_package_hash"] == sha256_json(package)

    invalid = {**valid_payloads, "hash-bound-reproducibility-manifest": {}}
    passed, reasons, diagnostics = evaluate_composed_evidence_package(invalid, ISOLATED_STATE)
    assert not passed
    assert reasons
    assert diagnostics["evidence_package"]["status"] == "REJECTED"
    assert (
        diagnostics["evidence_package"]["component_results"]["leakage-safe-model-comparison-gate"][
            "status"
        ]
        == "BLOCKED_BY_PREDECESSOR"
    )


def test_shadow_runner_rejects_persistent_output_outside_phase002d_r3_root(
    repo_root: Path, tmp_path: Path
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    with pytest.raises(ValueError, match="SHADOW_PERSISTENT_OUTPUT_OUTSIDE_R3_ROOT"):
        run_case(
            repo_root,
            DeterministicEvidenceKernel.architecture_id,
            case,
            ISOLATED_STATE,
            _context(tmp_path, case),
            persist=True,
        )
