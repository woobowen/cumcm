"""Shared-interface adapter for the W1 workflow-only guard prototype."""

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
)

from .guards import (
    claim_checklist,
    comparison_checklist,
    reproducibility_checklist,
    workflow_checklist,
)

Guard = Callable[
    [Mapping[str, Any], Mapping[str, Any]], tuple[bool, tuple[str, ...], dict[str, Any]]
]
GUARDS: dict[str, Guard] = {
    "accepted-versus-done-workflow-state": workflow_checklist,
    "claim-evidence-support-gate": claim_checklist,
    "hash-bound-reproducibility-manifest": reproducibility_checklist,
    "leakage-safe-model-comparison-gate": comparison_checklist,
}


class WorkflowGuardAdapter:
    architecture_id = "ARCH-W1-WORKFLOW-ONLY-GUARDS"

    def evaluate_case(
        self,
        case_input: ShadowCaseInput,
        isolated_state: Mapping[str, Any],
        run_context: ShadowContext,
    ) -> ShadowRunResult:
        if run_context.architecture_id != self.architecture_id:
            raise ValueError("W1_CONTEXT_ARCHITECTURE_MISMATCH")
        terminal_status = "COMPLETED"
        if case_input.component_id not in COMPONENT_IDS:
            decision = ShadowDecision("BLOCK", ("W1_UNKNOWN_COMPONENT",))
            diagnostics: dict[str, Any] = {}
        elif case_input.component_id not in run_context.enabled_components:
            decision = ShadowDecision(
                "ABSTAIN",
                ("W1_COMPONENT_DISABLED_BY_FROZEN_ABLATION",),
                {case_input.component_id: "DISABLED"},
            )
            diagnostics = {}
        else:
            try:
                passed, reasons, diagnostics = GUARDS[case_input.component_id](
                    case_input.payload, isolated_state
                )
            except (KeyError, TypeError, ValueError) as exc:
                passed = False
                reasons = ("W1_MALFORMED_INPUT_FAIL_CLOSED",)
                diagnostics = {"sanitized_exception": type(exc).__name__}
                terminal_status = "FAILED"
            decision = ShadowDecision(
                "PASS" if passed else ("ERROR" if terminal_status == "FAILED" else "BLOCK"),
                reasons or ("W1_ALL_WORKFLOW_CHECKS_PASS",),
                {case_input.component_id: "PASS" if passed else "BLOCK"},
            )
        evidence = ShadowEvidence(
            evidence_id=f"{run_context.run_id}:workflow-checklist",
            evidence_type="SHADOW_CHECKLIST_RESULT",
            run_id=run_context.run_id,
            current=True,
            supports=(case_input.component_id,) if decision.outcome == "PASS" else (),
            contradicts=(case_input.component_id,) if decision.outcome == "BLOCK" else (),
            payload={"reason_codes": list(decision.reason_codes)},
        )
        return build_result(
            context=run_context,
            case_input=case_input,
            decision=decision,
            evidence=(evidence,),
            diagnostics={
                **diagnostics,
                "implementation_kind": "STATELESS_WORKFLOW_CHECKLIST",
                "formal_state_writes": 0,
                "state_truth_sources": 1,
                "formal_skill_count": 1,
                "hidden_vault_accesses": 0,
                "third_party_executions": 0,
            },
            terminal_status=terminal_status,
        )


__all__ = ["WorkflowGuardAdapter"]
