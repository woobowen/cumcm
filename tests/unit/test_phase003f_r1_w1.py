from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.arch_w1.composer_r1 import (
    CLAIM,
    COMPARISON,
    LIFECYCLE,
    PACKAGE_FIELDS,
    REPRODUCIBILITY,
    compose_evidence_package,
)
from experiments.shadow_prototypes.arch_w1.revision_r1 import (
    WorkflowGuardRevisionR1,
    comparison_checklist_r1,
)
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    sha256_json,
    thaw,
)
from experiments.shadow_prototypes.common.public_cases import (
    load_public_cases,
    public_isolated_state,
)


def _case(repo_root: Path, component_id: str, case_class: str = "valid control") -> ShadowCaseInput:
    return next(
        item
        for item in load_public_cases(repo_root)
        if item.component_id == component_id and item.case_class == case_class
    )


def _context(tmp_path: Path, case: ShadowCaseInput) -> ShadowContext:
    return ShadowContext(
        run_id=f"003F-R1-W1-{case.case_id}",
        architecture_id=WorkflowGuardRevisionR1.architecture_id,
        stage="PUBLIC_VALIDATION",
        output_dir=tmp_path / case.case_id,
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=COMPONENT_IDS,
    )


def _evaluate(
    repo_root: Path,
    tmp_path: Path,
    component_id: str,
    payload: dict[str, Any],
    *,
    state: Any | None = None,
    context: Any | None = None,
):
    base = _case(repo_root, component_id)
    case = replace(base, payload=payload, input_hash=sha256_json(payload))
    return WorkflowGuardRevisionR1().evaluate_case(
        case,
        public_isolated_state() if state is None else state,
        _context(tmp_path, case) if context is None else context,
    )


def _valid_component_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    return {
        component_id: thaw(_case(repo_root, component_id).payload) for component_id in COMPONENT_IDS
    }


def _coherent_component_payloads_and_state(
    repo_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payloads = _valid_component_payloads(repo_root)
    state = public_isolated_state()
    manifest = payloads[REPRODUCIBILITY]["manifest"]
    claim_payload = payloads[CLAIM]
    claim = claim_payload["claim"]
    claim.update(
        {
            "input_hash": manifest["input_hash"],
            "code_commit": manifest["code_commit"],
            "output_hash": manifest["output_hash"],
        }
    )
    evidence = claim_payload["evidence"][0]
    artifact_body = evidence["artifact_body"]
    for field in ("input_hash", "code_commit", "output_hash"):
        evidence[field] = claim[field]
        artifact_body[field] = claim[field]
    artifact_hash = sha256_json(artifact_body)
    evidence["artifact_hash"] = artifact_hash
    evidence["registry_hash"] = sha256_json(
        {"locator": evidence["locator"], "artifact_hash": artifact_hash}
    )
    state["trusted_artifact_hashes"][evidence["locator"]] = artifact_hash
    state["trusted_run_bindings"][manifest["run_id"]] = {
        "run_id": manifest["run_id"],
        "input_hash": manifest["input_hash"],
        "code_commit": manifest["code_commit"],
        "output_hash": manifest["output_hash"],
        "lineage": claim["lineage"],
    }
    return payloads, state


@pytest.mark.parametrize(
    "context_factory",
    [
        lambda context: replace(context, stage=[]),
        lambda context: replace(context, enabled_components=None),
        lambda context: None,
        lambda context: {"stage": "PUBLIC_VALIDATION"},
        lambda context: replace(context, stage="PRODUCTION"),
    ],
)
def test_w1_r1_malformed_or_formal_context_fails_closed(
    repo_root: Path, tmp_path: Path, context_factory
) -> None:
    case = _case(repo_root, LIFECYCLE)
    context = context_factory(_context(tmp_path, case))
    result = WorkflowGuardRevisionR1().evaluate_case(case, public_isolated_state(), context)
    assert result.decision.outcome == "BLOCK"
    assert result.decision.reason_codes
    assert result.diagnostics["accepted"] is False
    assert result.diagnostics["final"] is False
    assert result.terminal_status == "FAILED_RETAINED"


@pytest.mark.parametrize(
    ("component_id", "field", "value"),
    [
        (LIFECYCLE, "evidenced_stages", None),
        (LIFECYCLE, "changed_nodes", "input"),
        (CLAIM, "claim", None),
        (CLAIM, "evidence", {"forged": True}),
        (REPRODUCIBILITY, "manifest", None),
        (COMPARISON, "splits", None),
        (COMPARISON, "attempts", ["malformed"]),
    ],
)
def test_w1_r1_nested_malformed_payloads_block(
    repo_root: Path,
    tmp_path: Path,
    component_id: str,
    field: str,
    value: Any,
) -> None:
    payload = thaw(_case(repo_root, component_id).payload)
    payload[field] = value
    result = _evaluate(repo_root, tmp_path, component_id, payload)
    assert result.decision.outcome == "BLOCK"
    assert result.decision.reason_codes


def test_w1_r1_verified_run_decision_id_is_exactly_bound(repo_root: Path, tmp_path: Path) -> None:
    payload = thaw(_case(repo_root, CLAIM).payload)
    payload["verified_run_manifest"]["decision_id"] = "attacker-decision"
    result = _evaluate(repo_root, tmp_path, CLAIM, payload)
    assert result.decision.outcome == "BLOCK"
    assert "W1_R1_UNBOUND_VERIFIED_RUN_DECISION" in result.decision.reason_codes


def test_w1_r1_supports_full_verified_decision_registry_and_rejects_tamper(
    repo_root: Path, tmp_path: Path
) -> None:
    payload = thaw(_case(repo_root, CLAIM).payload)
    state = public_isolated_state()
    binding = state["trusted_run_bindings"]["run-public-1"]
    decision_body = {
        "run_id": "run-public-1",
        "decision_id": "manifest-decision:run-public-1",
        "run_manifest_hash": "a" * 64,
        "input_hash": binding["input_hash"],
        "code_hash": binding["code_commit"],
        "configuration_hash": "b" * 64,
        "output_hash": binding["output_hash"],
        "current": True,
        "status": "PASS",
        "evidence_artifact_ids": ["evidence-1"],
    }
    decision = {**decision_body, "decision_hash": sha256_json(decision_body)}
    state["trusted_verified_run_decisions"] = {"run-public-1": decision}
    payload["verified_run_manifest"].update(decision)
    valid = _evaluate(repo_root, tmp_path, CLAIM, payload, state=state)
    assert valid.decision.outcome == "PASS"
    payload["verified_run_manifest"]["output_hash"] = "f" * 64
    tampered = _evaluate(repo_root, tmp_path, CLAIM, payload, state=state)
    assert tampered.decision.outcome == "BLOCK"
    assert "W1_R1_VERIFIED_RUN_EXACT_BINDING_MISMATCH" in tampered.decision.reason_codes


@pytest.mark.parametrize(
    "extra",
    [
        {"nested": {"private-key": "synthetic"}},
        {"nested": [{"refreshToken": "synthetic"}]},
        {"scratch": "\\\\server\\private\\run"},
        {"scratch": "C:\\private\\run"},
        {"scratch": "/private/run"},
        {"environment": "${PRIVATE_KEY}"},
        {"endpoint": "scheme://user:synthetic@host/path"},
    ],
)
def test_w1_r1_manifest_recursively_rejects_sensitive_keys_and_paths(
    repo_root: Path, tmp_path: Path, extra: dict[str, Any]
) -> None:
    payload = {**thaw(_case(repo_root, REPRODUCIBILITY).payload), **extra}
    result = _evaluate(repo_root, tmp_path, REPRODUCIBILITY, payload)
    assert result.decision.outcome == "BLOCK"
    assert "W1_R1_MANIFEST_SENSITIVE_VALUE_REJECTED" in result.decision.reason_codes
    assert "synthetic" not in repr(result.diagnostics)


def test_w1_r1_manifest_rejects_arbitrary_well_formed_freeze_hash(
    repo_root: Path, tmp_path: Path
) -> None:
    payload = thaw(_case(repo_root, REPRODUCIBILITY).payload)
    payload["run_freeze_hash"] = "a" * 64
    result = _evaluate(repo_root, tmp_path, REPRODUCIBILITY, payload)
    assert result.decision.outcome == "BLOCK"
    assert any(
        reason.startswith("W1_R1_UNTRUSTED_FREEZE_HASH") for reason in result.decision.reason_codes
    )


@pytest.mark.parametrize("score", ["0.8", True, float("nan"), float("inf"), float("-inf")])
def test_w1_r1_comparison_requires_finite_non_boolean_real_scores(
    repo_root: Path, score: Any
) -> None:
    payload = thaw(_case(repo_root, COMPARISON).payload)
    payload["validation_scores"] = {"a": score, "b": 0.7}
    passed, reasons, _ = comparison_checklist_r1(payload, public_isolated_state())
    assert not passed
    assert "W1_R1_COMPARISON_SCORE_TYPE_INVALID" in reasons


@pytest.mark.parametrize("outcome", ["FAILED", "PARTIAL", "SUPERSEDED", "STALE"])
def test_w1_r1_non_success_attempt_is_retained_but_never_scored(
    repo_root: Path, tmp_path: Path, outcome: str
) -> None:
    payload = thaw(_case(repo_root, COMPARISON).payload)
    payload["attempts"][0].update({"outcome": outcome, "failure_class": "MODEL_FAILURE"})
    result = _evaluate(repo_root, tmp_path, COMPARISON, payload)
    assert result.decision.outcome == "BLOCK"
    assert "W1_R1_COMPARISON_FAILED_ATTEMPT_SCORED" in result.decision.reason_codes


def test_w1_r1_comparison_requires_trusted_freeze_registry(repo_root: Path, tmp_path: Path) -> None:
    payload = thaw(_case(repo_root, COMPARISON).payload)
    payload.update({"candidate_freeze_hash": "a" * 64, "metric_freeze_hash": "b" * 64})
    result = _evaluate(repo_root, tmp_path, COMPARISON, payload)
    assert result.decision.outcome == "BLOCK"
    assert {
        "W1_R1_COMPARISON_UNTRUSTED_FREEZE:candidate_freeze_hash",
        "W1_R1_COMPARISON_UNTRUSTED_FREEZE:metric_freeze_hash",
    } <= set(result.decision.reason_codes)


@pytest.mark.parametrize(
    "state_mutation",
    [
        {"truth_source": "shadow/second-state.json"},
        {"formal_state_writes_allowed": True},
        {"second_truth": "attacker"},
        {"formal_state_path": "state/project_state.json"},
    ],
)
def test_w1_r1_state_authority_boundary_is_non_bypassable(
    repo_root: Path, tmp_path: Path, state_mutation: dict[str, Any]
) -> None:
    payload = thaw(_case(repo_root, LIFECYCLE).payload)
    state = {**public_isolated_state(), **state_mutation}
    result = _evaluate(repo_root, tmp_path, LIFECYCLE, payload, state=state)
    assert result.decision.outcome == "BLOCK"
    assert any(
        marker in reason
        for reason in result.decision.reason_codes
        for marker in ("STATE", "TRUTH", "AUTHORITY")
    )


def test_w1_r1_composer_rejects_original_cross_component_hash_mismatch(
    repo_root: Path,
) -> None:
    passed, reasons, diagnostics = compose_evidence_package(
        _valid_component_payloads(repo_root), public_isolated_state()
    )
    assert not passed
    assert any("COMPOSITION_RUN_BINDING_MISMATCH" in reason for reason in reasons)
    assert diagnostics["evidence_package"] == {}
    assert diagnostics["accepted"] is False
    assert diagnostics["final"] is False
    assert diagnostics["ready_for_paper"] is False


def test_w1_r1_composer_emits_complete_hash_bound_modeling_package(
    repo_root: Path,
) -> None:
    payloads, state = _coherent_component_payloads_and_state(repo_root)
    passed, reasons, diagnostics = compose_evidence_package(
        payloads, state, generated_at="2026-09-04T00:00:00+08:00"
    )
    package = diagnostics["evidence_package"]
    assert passed, reasons
    assert set(package) == PACKAGE_FIELDS
    assert package["contract_version"] == "modeling-to-paper/v1"
    assert package["final_runs"][0]["output_hash"] == package["claim_evidence"]["output_hash"]
    assert package["approved_by"] == ["MACHINE_TECHNICAL_GATE:W1_R1_COMPONENT_COMPOSITION"]
    assert diagnostics["evidence_package_hash"] == sha256_json(package)
    assert diagnostics["formal_state_writes"] == 0
    assert diagnostics["state_truth_sources"] == 1


@pytest.mark.parametrize("failure_kind", ["stale", "missing"])
def test_w1_r1_composer_propagates_repro_failure_transitively_as_stale(
    repo_root: Path, failure_kind: str
) -> None:
    payloads, state = _coherent_component_payloads_and_state(repo_root)
    if failure_kind == "stale":
        payloads[REPRODUCIBILITY] = thaw(
            _case(repo_root, REPRODUCIBILITY, "stale mutation").payload
        )
    else:
        payloads[REPRODUCIBILITY] = {}
    passed, reasons, diagnostics = compose_evidence_package(payloads, state)
    assert not passed
    results = diagnostics["component_results"]
    assert [results[item]["status"] for item in (COMPARISON, CLAIM, LIFECYCLE)] == [
        "STALE",
        "STALE",
        "STALE",
    ]
    assert results[LIFECYCLE]["dependency_chain"] == [
        REPRODUCIBILITY,
        COMPARISON,
        CLAIM,
        LIFECYCLE,
    ]
    assert any("STALE" in reason for reason in reasons)
    assert diagnostics["evidence_package"] == {}


def test_w1_r1_adapter_does_not_mutate_inputs(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, COMPARISON)
    before = sha256_json(case.payload)
    result = WorkflowGuardRevisionR1().evaluate_case(
        case, public_isolated_state(), _context(tmp_path, case)
    )
    assert result.decision.outcome == "PASS"
    assert sha256_json(case.payload) == before == case.input_hash
