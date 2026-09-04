from __future__ import annotations

import copy
import math
from dataclasses import replace
from pathlib import Path

import pytest

from cumcm_skill_lab.shadow_validation.runner_r1 import run_case_r1
from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.arch_k1.revision_r1 import (
    ARCHITECTURE_ID,
    DeterministicEvidenceKernelRevisionR1,
    evaluate_claim_support_r1,
    evaluate_composed_evidence_package_r1,
    evaluate_model_comparison_r1,
    evaluate_reproducibility_r1,
    verified_run_record_r1,
)
from experiments.shadow_prototypes.common.interface import ShadowContext, sha256_json, thaw
from experiments.shadow_prototypes.common.public_cases import (
    load_public_cases,
    public_isolated_state,
)
from experiments.shadow_prototypes.common.r1_interface import R1CaseInput, sha256_boundary_json


def _payloads(repo_root: Path) -> dict[str, dict[str, object]]:
    return {
        component_id: thaw(
            next(
                case
                for case in load_public_cases(repo_root)
                if case.component_id == component_id and case.case_class == "valid control"
            ).payload
        )
        for component_id in COMPONENT_IDS
    }


def _case(repo_root: Path, component_id: str) -> R1CaseInput:
    payload = _payloads(repo_root)[component_id]
    return R1CaseInput(
        case_id=f"R1-{component_id}",
        component_id=component_id,
        payload=payload,
        input_hash=sha256_boundary_json(payload),
    )


def _context(tmp_path: Path, case: R1CaseInput) -> ShadowContext:
    return ShadowContext(
        run_id=f"K1-R1-{case.case_id}",
        architecture_id=ARCHITECTURE_ID,
        stage="PUBLIC_VALIDATION",
        output_dir=tmp_path / case.case_id,
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=COMPONENT_IDS,
    )


def _normalized_composition(
    repo_root: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    payloads = _payloads(repo_root)
    state = public_isolated_state()
    output_hash = payloads["hash-bound-reproducibility-manifest"]["manifest"]["output_hash"]
    claim_payload = payloads["claim-evidence-support-gate"]
    claim_payload["claim"]["output_hash"] = output_hash
    evidence = claim_payload["evidence"][0]
    evidence["output_hash"] = output_hash
    evidence["artifact_body"]["output_hash"] = output_hash
    artifact_hash = sha256_json(evidence["artifact_body"])
    evidence["artifact_hash"] = artifact_hash
    evidence["registry_hash"] = sha256_json(
        {"locator": evidence["locator"], "artifact_hash": artifact_hash}
    )
    state["trusted_artifact_hashes"] = {evidence["locator"]: artifact_hash}
    state["trusted_run_bindings"] = {
        "run-public-1": {
            **state["trusted_run_bindings"]["run-public-1"],
            "output_hash": output_hash,
        }
    }
    return payloads, state


@pytest.mark.parametrize("stage", [None, [], {}, "PRODUCTION", "FORMAL"])
def test_k1_r1_malformed_stage_is_structured_fail_closed(
    repo_root: Path, tmp_path: Path, stage: object
) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    context = replace(_context(tmp_path, case), stage=stage)

    result, unchanged = run_case_r1(
        repo_root, ARCHITECTURE_ID, case, public_isolated_state(), context
    )

    assert result.decision.outcome == "BLOCK"
    assert result.decision.reason_codes
    assert result.diagnostics["accepted"] is False
    assert result.diagnostics["final"] is False
    assert unchanged is True


def test_k1_r1_null_and_wrong_context_never_escape(repo_root: Path) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    kernel = DeterministicEvidenceKernelRevisionR1()

    for context in (None, 17, {}, []):
        result = kernel.evaluate_case(case, public_isolated_state(), context)
        assert result.decision.outcome == "BLOCK"
        assert "K1_R1_CONTEXT_MALFORMED" in result.decision.reason_codes
        assert result.diagnostics["accepted"] is False


def test_k1_r1_malformed_enabled_components_is_rejected(repo_root: Path, tmp_path: Path) -> None:
    case = _case(repo_root, "accepted-versus-done-workflow-state")
    context = replace(_context(tmp_path, case), enabled_components=None)

    result = DeterministicEvidenceKernelRevisionR1().evaluate_case(
        case, public_isolated_state(), context
    )

    assert result.decision.outcome == "BLOCK"
    assert "K1_R1_ENABLED_COMPONENTS_MALFORMED" in result.decision.reason_codes


@pytest.mark.parametrize("score", [True, "0.8", math.nan, math.inf, -math.inf])
def test_k1_r1_scores_are_strict_real_finite(repo_root: Path, score: object) -> None:
    payload = _payloads(repo_root)["leakage-safe-model-comparison-gate"]
    payload["validation_scores"] = {"a": score, "b": 0.7}

    passed, reasons, _ = evaluate_model_comparison_r1(payload, public_isolated_state())

    assert passed is False
    assert "K1_R1_SCORE_TYPE_OR_FINITE_INVALID" in reasons


@pytest.mark.parametrize(
    "splits",
    [None, {}, {"train": [], "validation": ["v"], "test": ["t"]}, {"train": [[]]}],
)
def test_k1_r1_split_validation_is_recursive_and_fail_closed(
    repo_root: Path, splits: object
) -> None:
    payload = _payloads(repo_root)["leakage-safe-model-comparison-gate"]
    payload["splits"] = splits

    passed, reasons, _ = evaluate_model_comparison_r1(payload, public_isolated_state())

    assert passed is False
    assert "K1_R1_SPLIT_STRUCTURE_INVALID" in reasons


def test_k1_r1_unbound_verified_run_decision_is_rejected(repo_root: Path) -> None:
    payload = _payloads(repo_root)["claim-evidence-support-gate"]
    payload["verified_run_manifest"]["decision_id"] = "attacker-decision"

    passed, reasons, diagnostics = evaluate_claim_support_r1(payload, public_isolated_state())

    assert passed is False
    assert "K1_R1_UNBOUND_VERIFIED_RUN_DECISION" in reasons
    assert diagnostics["disposition"] == "REJECTED"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("private_key", "SYNTHETIC_VALUE_ALPHA"),
        ("private-key", "SYNTHETIC_VALUE_BRAVO"),
        ("PRIVATE_KEY", "SYNTHETIC_VALUE_CHARLIE"),
        ("refreshToken", "SYNTHETIC_VALUE_DELTA"),
        ("Bearer-Token", "SYNTHETIC_VALUE_ECHO"),
        ("scratch", "\\\\server\\private\\run"),
        ("scratch", "C:\\Users\\private\\run"),
        ("scratch", "~/private/run"),
        ("scratch", "scheme://user:password@host/resource"),
        ("scratch", "${HOME}/private/run"),
    ],
)
def test_k1_r1_recursive_secret_and_private_path_scan_redacts_values(
    repo_root: Path, key: str, value: str
) -> None:
    payload = _payloads(repo_root)["hash-bound-reproducibility-manifest"]
    payload["nested"] = {"items": [{key: value}]}

    passed, reasons, diagnostics = evaluate_reproducibility_r1(payload, public_isolated_state())

    assert passed is False
    assert "K1_R1_SENSITIVE_VALUE_REDACTED_AND_REJECTED" in reasons
    assert diagnostics["private_fields_redacted"] == 1
    assert value not in str(diagnostics)


def test_k1_r1_arbitrary_valid_freeze_hash_is_not_trusted(repo_root: Path) -> None:
    payload = _payloads(repo_root)["hash-bound-reproducibility-manifest"]
    payload["manifest"]["freeze_bindings"] = {"candidate_set": "a" * 64}

    passed, reasons, _ = evaluate_reproducibility_r1(payload, public_isolated_state())

    assert passed is False
    assert "K1_R1_REPRO_FREEZE_REGISTRY_MISMATCH" in reasons


@pytest.mark.parametrize(
    ("freeze_hash", "reason"),
    [
        ("unknown", "K1_R1_REPRO_FREEZE_HASH_INVALID"),
        ("a" * 64, "K1_R1_REPRO_FREEZE_HASH_NOT_TRUSTED"),
    ],
)
def test_k1_r1_top_level_freeze_reference_requires_trusted_registry(
    repo_root: Path, freeze_hash: str, reason: str
) -> None:
    payload = _payloads(repo_root)["hash-bound-reproducibility-manifest"]
    payload["freeze_hash"] = freeze_hash

    passed, reasons, _ = evaluate_reproducibility_r1(payload, public_isolated_state())

    assert passed is False
    assert reason in reasons


def test_k1_r1_complete_v2_manifest_binds_capture_files_and_freeze_registry(
    repo_root: Path,
) -> None:
    payload = _payloads(repo_root)["hash-bound-reproducibility-manifest"]
    manifest = payload["manifest"]
    freeze_hash = "b" * 64
    manifest.update(
        {
            "manifest_version": "k1-repro/v2",
            "input_files": [{"path": "inputs/data.json", "sha256": manifest["input_hash"]}],
            "code_tree_hash": "c" * 64,
            "config_content_hash": manifest["config_hash"],
            "cwd_policy": "REPOSITORY_RELATIVE_ONLY",
            "environment_allowlist": {"PYTHONHASHSEED": "0"},
            "output_files": [{"path": "outputs/result.json", "sha256": manifest["output_hash"]}],
            "failure": {"class": "NONE", "message_hash": None},
            "supersession": {"superseded": False, "superseded_by": None},
            "freeze_bindings": {"candidate_set": freeze_hash},
        }
    )
    state = public_isolated_state()
    state["trusted_freeze_registry"] = {"candidate_set": freeze_hash}
    state["trusted_repro_manifest_hashes"] = {"run-public-1": sha256_json(manifest)}

    passed, reasons, diagnostics = evaluate_reproducibility_r1(payload, state)

    assert passed is True, reasons
    assert reasons == ()
    assert diagnostics["trusted_freezes_verified"] is True


def test_k1_r1_exact_verified_run_record_binds_every_result_hash() -> None:
    binding = {
        "run_id": "run-exact-1",
        "run_manifest_hash": "1" * 64,
        "input_hash": "2" * 64,
        "code_hash": "3" * 64,
        "configuration_hash": "4" * 64,
        "output_hash": "5" * 64,
        "decision_hash": "6" * 64,
        "evidence_artifact_ids": ["evidence-exact-1"],
    }
    record = {
        **binding,
        "authority": "existing-native-run-ledger",
        "status": "PASS",
        "current": True,
        "current_status": "CURRENT",
        "superseded": False,
        "audited": True,
    }
    record["record_hash"] = sha256_json(record)
    state = {
        "trusted_run_ids": [binding["run_id"]],
        "trusted_verified_run_hashes": {binding["run_id"]: record["record_hash"]},
    }

    assert verified_run_record_r1(record, state, expected_binding=binding) is True

    tampered = {**record, "decision_hash": "7" * 64}
    assert verified_run_record_r1(tampered, state, expected_binding=binding) is False


def test_k1_r1_exact_claim_binds_manifest_config_decision_and_evidence_set(
    repo_root: Path,
) -> None:
    payloads, state = _normalized_composition(repo_root)
    payload = payloads["claim-evidence-support-gate"]
    claim = payload["claim"]
    exact = {
        "run_id": claim["run_id"],
        "run_manifest_hash": "a" * 64,
        "input_hash": claim["input_hash"],
        "code_hash": "b" * 64,
        "configuration_hash": "c" * 64,
        "output_hash": claim["output_hash"],
        "decision_hash": "d" * 64,
        "evidence_artifact_ids": ["evidence-1"],
    }
    claim.update(exact)
    state["trusted_run_bindings"][claim["run_id"]].update(exact)
    record = {
        **payload["verified_run_manifest"],
        **exact,
        "current_status": "CURRENT",
        "superseded": False,
    }
    record["record_hash"] = sha256_json(record)
    payload["verified_run_manifest"] = record
    state["trusted_verified_run_hashes"] = {claim["run_id"]: record["record_hash"]}

    passed, reasons, diagnostics = evaluate_claim_support_r1(payload, state)

    assert passed is True, reasons
    assert reasons == ()
    assert diagnostics["exact_verified_run_bound"] is True

    tampered = copy.deepcopy(payload)
    tampered["verified_run_manifest"]["decision_hash"] = "e" * 64
    passed, reasons, _ = evaluate_claim_support_r1(tampered, state)
    assert passed is False
    assert "K1_R1_UNBOUND_VERIFIED_RUN_DECISION" in reasons


@pytest.mark.parametrize("outcome", ["FAILED", "PARTIAL", "SUPERSEDED", "STALE"])
def test_k1_r1_non_success_attempts_are_retained_but_never_ranked(
    repo_root: Path, outcome: str
) -> None:
    payload = _payloads(repo_root)["leakage-safe-model-comparison-gate"]
    payload["attempts"][0]["outcome"] = outcome
    payload["ranked_run_ids"] = [payload["attempts"][0]["run_id"]]

    passed, reasons, diagnostics = evaluate_model_comparison_r1(payload, public_isolated_state())

    assert passed is False
    assert "K1_R1_NON_SUCCESS_ATTEMPT_SCORED" in reasons
    assert diagnostics["reliability_denominator"] == 4
    assert diagnostics["ranking_attempt_count"] == 3


@pytest.mark.parametrize(
    ("state_change", "kwargs", "reason"),
    [
        ({"truth_source": "shadow/second.json"}, {}, "K1_R1_SINGLE_STATE_TRUTH_REQUIRED"),
        ({"formal_state_writes_allowed": True}, {}, "K1_R1_FORMAL_STATE_WRITE_PROHIBITED"),
        ({"second_truth": "shadow/state.json"}, {}, "K1_R1_EXTRA_STATE_AUTHORITY_REJECTED"),
        ({}, {"stage": "PRODUCTION"}, "K1_R1_COMPOSITION_STAGE_BOUNDARY_REJECTED"),
        ({}, {"writer": "MAIN_AGENT"}, "K1_R1_COMPOSITION_WRITER_NOT_AUTHORIZED"),
    ],
)
def test_k1_r1_composer_enforces_state_and_stage_boundary(
    repo_root: Path,
    state_change: dict[str, object],
    kwargs: dict[str, object],
    reason: str,
) -> None:
    state = {**public_isolated_state(), **state_change}
    passed, reasons, diagnostics = evaluate_composed_evidence_package_r1(
        _payloads(repo_root), state, **kwargs
    )

    assert passed is False
    assert reason in reasons
    assert diagnostics["accepted"] is False
    assert diagnostics["final"] is False
    assert diagnostics["ready_for_paper"] is False


def test_k1_r1_composer_rejects_cross_component_output_mismatch(repo_root: Path) -> None:
    passed, reasons, diagnostics = evaluate_composed_evidence_package_r1(
        _payloads(repo_root), public_isolated_state()
    )

    assert passed is False
    assert "K1_R1_COMPOSITION_OUTPUT_HASH_MISMATCH" in reasons
    assert diagnostics["ready_for_paper"] is False


def test_k1_r1_composer_emits_complete_contract_for_bound_lineage(repo_root: Path) -> None:
    payloads, state = _normalized_composition(repo_root)

    passed, reasons, diagnostics = evaluate_composed_evidence_package_r1(payloads, state)

    contract = __import__("json").loads(
        (repo_root / "contracts/modeling_to_paper.schema.json").read_text(encoding="utf-8")
    )
    package = diagnostics["evidence_package"]
    assert passed is True, reasons
    assert reasons == ()
    assert set(package) == set(contract["required"])
    assert package["contract_version"] == "modeling-to-paper/v1"
    assert package["approved_by"] == ["MACHINE_TECHNICAL_GATE:K1_R1_COMPOSITION"]
    assert diagnostics["proposal_eligible"] is True
    assert diagnostics["accepted"] is False
    assert diagnostics["final"] is False


def test_k1_r1_repro_stale_propagates_transitively_with_dependency_chain(
    repo_root: Path,
) -> None:
    payloads, state = _normalized_composition(repo_root)
    payloads = copy.deepcopy(payloads)
    payloads["hash-bound-reproducibility-manifest"]["trusted_capture"]["input_content"] = {
        "mutated": True
    }

    passed, reasons, diagnostics = evaluate_composed_evidence_package_r1(payloads, state)

    results = diagnostics["evidence_package"]["component_results"]
    assert passed is False
    assert any("STALE" in reason or "MUTATION" in reason for reason in reasons)
    for component_id in (
        "leakage-safe-model-comparison-gate",
        "claim-evidence-support-gate",
        "accepted-versus-done-workflow-state",
    ):
        assert results[component_id]["status"] == "STALE"
        assert results[component_id]["dependency_chain"][0] == (
            "hash-bound-reproducibility-manifest"
        )
    assert diagnostics["accepted"] is False
    assert diagnostics["ready_for_paper"] is False
