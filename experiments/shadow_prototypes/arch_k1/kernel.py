"""Thin adapter over the four deterministic shadow evidence kernels."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    ShadowDecision,
    ShadowEvidence,
    ShadowRunResult,
    build_result,
    deep_freeze,
    sha256_json,
)

from .claim_support import evaluate_claim_support
from .lifecycle import evaluate_lifecycle
from .model_comparison import evaluate_model_comparison
from .reproducibility import evaluate_reproducibility

KernelFunction = Callable[
    [Mapping[str, Any], Mapping[str, Any]],
    tuple[bool | None, tuple[str, ...], dict[str, Any]],
]
KERNELS: dict[str, KernelFunction] = {
    "accepted-versus-done-workflow-state": evaluate_lifecycle,
    "claim-evidence-support-gate": evaluate_claim_support,
    "hash-bound-reproducibility-manifest": evaluate_reproducibility,
    "leakage-safe-model-comparison-gate": evaluate_model_comparison,
}


def _state_boundary(isolated_state: Mapping[str, Any]) -> tuple[str, ...]:
    if not isinstance(isolated_state, Mapping):
        return ("K1_STATE_BUNDLE_MALFORMED",)
    reasons: list[str] = []
    allowed_keys = {
        "truth_source",
        "formal_state_writes_allowed",
        "trusted_run_ids",
        "trusted_stage_hashes",
        "trusted_gate_hashes",
        "trusted_artifact_hashes",
        "trusted_run_bindings",
        "trusted_manifest_hashes",
        "trusted_dependency_graph",
        "trusted_dependency_graph_hash",
        "trusted_challenge_hashes",
        "trusted_disposition_hashes",
        "trusted_repro_manifest_hashes",
        "trusted_capture_hashes",
        "comparison_policy",
        "trusted_candidates",
        "trusted_seeds",
        "trusted_candidate_freeze_hash",
        "trusted_metric_freeze_hash",
        "trusted_comparison_design_hash",
        "trusted_access_genesis",
        "trusted_access_heads",
        "trusted_model_freeze_hash",
        "trusted_pretest_decision_hash",
        "trusted_test_set_id",
        "exposed_test_set_ids",
    }
    if isolated_state.get("truth_source") != "state/project_state.json":
        reasons.append("K1_SINGLE_STATE_TRUTH_REQUIRED")
    if isolated_state.get("formal_state_writes_allowed") is not False:
        reasons.append("K1_FORMAL_STATE_WRITE_BOUNDARY_INVALID")
    if set(isolated_state) - allowed_keys:
        reasons.append("K1_SECOND_STATE_OR_LEDGER_AUTHORITY_REJECTED")
    return tuple(reasons)


class DeterministicEvidenceKernel:
    architecture_id = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"

    def evaluate_case(
        self,
        case_input: ShadowCaseInput,
        isolated_state: Mapping[str, Any],
        run_context: ShadowContext,
    ) -> ShadowRunResult:
        if run_context.architecture_id != self.architecture_id:
            raise ValueError("K1_CONTEXT_ARCHITECTURE_MISMATCH")
        terminal_status = "COMPLETED"
        boundary_reasons = _state_boundary(isolated_state)
        if run_context.stage not in {
            "PUBLIC_VALIDATION",
            "STAGE1_DETERMINISTIC",
            "STAGE2_MODEL",
            "DETERMINISTIC_ABLATION",
        }:
            decision = ShadowDecision("BLOCK", ("K1_NON_SHADOW_EXECUTION_STAGE_REJECTED",))
            diagnostics = {}
        elif case_input.component_id not in COMPONENT_IDS:
            decision = ShadowDecision("BLOCK", ("K1_UNKNOWN_COMPONENT",))
            diagnostics: dict[str, Any] = {}
        elif case_input.component_id not in run_context.enabled_components:
            decision = ShadowDecision(
                "ABSTAIN",
                ("K1_COMPONENT_DISABLED_BY_FROZEN_ABLATION",),
                {case_input.component_id: "DISABLED"},
            )
            diagnostics = {}
        elif boundary_reasons:
            decision = ShadowDecision(
                "BLOCK",
                boundary_reasons,
                {case_input.component_id: "BLOCK"},
            )
            diagnostics = {}
        else:
            try:
                passed, reasons, diagnostics = KERNELS[case_input.component_id](
                    case_input.payload, isolated_state
                )
            except Exception as exc:  # noqa: BLE001 - fail-closed kernel boundary
                passed = False
                reasons = ("K1_MALFORMED_INPUT_FAIL_CLOSED",)
                diagnostics = {"sanitized_exception": type(exc).__name__}
                terminal_status = "FAILED_RETAINED"
            decision = ShadowDecision(
                "PASS" if passed is True else ("ABSTAIN" if passed is None else "BLOCK"),
                reasons or ("K1_ALL_DETERMINISTIC_CHECKS_PASS",),
                {
                    case_input.component_id: (
                        "PASS" if passed is True else ("ABSTAIN" if passed is None else "BLOCK")
                    )
                },
            )
        evidence = ShadowEvidence(
            evidence_id=f"{run_context.run_id}:deterministic-kernel",
            evidence_type="SHADOW_DETERMINISTIC_KERNEL_RESULT",
            run_id=run_context.run_id,
            current=True,
            supports=(case_input.component_id,) if decision.outcome == "PASS" else (),
            contradicts=(case_input.component_id,) if decision.outcome == "BLOCK" else (),
            payload={"reason_codes": list(decision.reason_codes)},
        )
        component_artifact_hash = sha256_json(
            {
                "component_id": case_input.component_id,
                "outcome": decision.outcome,
                "reason_codes": sorted(decision.reason_codes),
                "diagnostics": diagnostics,
            }
        )
        return build_result(
            context=run_context,
            case_input=case_input,
            decision=decision,
            evidence=(evidence,),
            artifact_hashes={"component_result": component_artifact_hash},
            diagnostics={
                **diagnostics,
                "implementation_kind": "DETERMINISTIC_EVIDENCE_KERNEL",
                "formal_state_writes": 0,
                "state_truth_sources": 1,
                "formal_skill_count": 1,
                "hidden_vault_accesses": 0,
                "third_party_executions": 0,
            },
            terminal_status=terminal_status,
        )


def evaluate_composed_evidence_package(
    component_payloads: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    """Compose all four kernels in dependency order and propagate the first failure."""
    if not isinstance(component_payloads, Mapping) or set(component_payloads) != set(COMPONENT_IDS):
        return False, ("K1_COMPOSITION_INPUT_INVALID",), {"component_results": {}}
    frozen_state = deep_freeze(isolated_state)
    order = (
        "hash-bound-reproducibility-manifest",
        "leakage-safe-model-comparison-gate",
        "claim-evidence-support-gate",
        "accepted-versus-done-workflow-state",
    )
    component_results: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    blocked = False
    for component_id in order:
        if blocked:
            component_results[component_id] = {
                "status": "BLOCKED_BY_PREDECESSOR",
                "reason_codes": ["K1_COMPOSITION_PREDECESSOR_FAILED"],
            }
            continue
        payload = component_payloads.get(component_id)
        if not isinstance(payload, Mapping):
            passed: bool | None = False
            component_reasons = ("K1_COMPOSITION_COMPONENT_INPUT_INVALID",)
            diagnostics: dict[str, Any] = {}
        else:
            try:
                passed, component_reasons, diagnostics = KERNELS[component_id](
                    deep_freeze(payload), frozen_state
                )
            except Exception as exc:  # noqa: BLE001 - composition is fail closed
                passed = False
                component_reasons = ("K1_COMPOSITION_MALFORMED_INPUT_FAIL_CLOSED",)
                diagnostics = {"sanitized_exception": type(exc).__name__}
        status = "PASS" if passed is True else "ABSTAIN" if passed is None else "BLOCK"
        component_results[component_id] = {
            "status": status,
            "reason_codes": list(component_reasons),
            "diagnostics": diagnostics,
        }
        if passed is not True:
            blocked = True
            reasons.extend(component_reasons or ("K1_COMPOSITION_COMPONENT_FAILED",))
    package = {
        "schema_version": "shadow-component-evidence-package/v1",
        "architecture_id": DeterministicEvidenceKernel.architecture_id,
        "formal": False,
        "component_results": component_results,
        "status": "ELIGIBLE" if not reasons else "REJECTED",
    }
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {"evidence_package": package, "evidence_package_hash": sha256_json(package)},
    )


__all__ = ["DeterministicEvidenceKernel", "evaluate_composed_evidence_package"]
