"""Fail-closed runner for versioned Competition RC1 architecture revisions."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import (
    PROHIBITED_FORMAL_OUTCOMES,
    ShadowContext,
    ShadowDecision,
    ShadowEvidence,
    ShadowRunResult,
    build_result,
    deep_freeze,
    thaw,
    verify_result_hash,
)
from experiments.shadow_prototypes.common.r1_interface import R1CaseInput, boundary_json

from .io import write_json_atomic

K1 = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
W1 = "ARCH-W1-WORKFLOW-ONLY-GUARDS"


def load_architecture_revision(architecture_id: str) -> Any:
    if architecture_id == K1:
        from experiments.shadow_prototypes.arch_k1.revision_r1 import (
            DeterministicEvidenceKernelRevisionR1,
        )

        return DeterministicEvidenceKernelRevisionR1()
    if architecture_id == W1:
        from experiments.shadow_prototypes.arch_w1.revision_r1 import WorkflowGuardRevisionR1

        return WorkflowGuardRevisionR1()
    raise ValueError("R1_UNKNOWN_ARCHITECTURE")


def _contains_formal_outcome(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_formal_outcome(item) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_formal_outcome(item) for item in value)
    return isinstance(value, str) and value in PROHIBITED_FORMAL_OUTCOMES


def _safe_context(architecture_id: str, context: Any) -> ShadowContext:
    if isinstance(context, ShadowContext):
        run_id = (
            context.run_id if isinstance(context.run_id, str) and context.run_id else "R1-BLOCK"
        )
        output_dir = context.output_dir if isinstance(context.output_dir, Path) else Path(".")
    else:
        run_id = "R1-BLOCK"
        output_dir = Path(".")
    return ShadowContext(
        run_id=run_id,
        architecture_id=architecture_id,
        stage="PUBLIC_VALIDATION",
        output_dir=output_dir,
        timeout_seconds=1,
        operation_budget=1,
        enabled_components=(),
    )


def _context_reasons(architecture_id: str, context: Any) -> tuple[str, ...]:
    if not isinstance(context, ShadowContext):
        return ("R1_CONTEXT_RECORD_INVALID",)
    reasons: list[str] = []
    if not isinstance(context.run_id, str) or not context.run_id:
        reasons.append("R1_CONTEXT_RUN_ID_INVALID")
    if context.architecture_id != architecture_id:
        reasons.append("R1_CONTEXT_ARCHITECTURE_MISMATCH")
    if not isinstance(context.stage, str) or not context.stage:
        reasons.append("R1_CONTEXT_STAGE_INVALID")
    if not isinstance(context.output_dir, Path):
        reasons.append("R1_CONTEXT_OUTPUT_DIR_INVALID")
    for value, code in (
        (context.timeout_seconds, "R1_CONTEXT_TIMEOUT_INVALID"),
        (context.operation_budget, "R1_CONTEXT_OPERATION_BUDGET_INVALID"),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            reasons.append(code)
    components = context.enabled_components
    if (
        not isinstance(components, tuple)
        or any(not isinstance(item, str) or item not in COMPONENT_IDS for item in components)
        or len(set(components)) != len(components)
    ):
        reasons.append("R1_CONTEXT_ENABLED_COMPONENTS_INVALID")
    return tuple(sorted(set(reasons)))


def _blocked_result(
    architecture_id: str,
    case_input: R1CaseInput,
    context: Any,
    reasons: tuple[str, ...],
) -> ShadowRunResult:
    safe = _safe_context(architecture_id, context)
    decision = ShadowDecision(
        "BLOCK",
        reasons or ("R1_PUBLIC_BOUNDARY_REJECTED",),
        {case_input.component_id: "BLOCK"},
    )
    evidence = ShadowEvidence(
        evidence_id=f"{safe.run_id}:r1-fail-closed",
        evidence_type="R1_FAIL_CLOSED_RESULT",
        run_id=safe.run_id,
        current=True,
        contradicts=(case_input.component_id,),
        payload={"reason_codes": list(decision.reason_codes)},
    )
    return build_result(
        context=safe,
        case_input=case_input,
        decision=decision,
        evidence=(evidence,),
        diagnostics={
            "accepted": False,
            "final": False,
            "unhandled_exception": False,
            "formal_state_writes": 0,
            "state_truth_sources": 1,
            "hidden_vault_accesses": 0,
            "third_party_executions": 0,
        },
        terminal_status="REJECTED",
    )


def _validate_output(root: Path, output_dir: Path, persist: bool) -> tuple[str, ...]:
    if not persist:
        return ()
    resolved = output_dir.resolve()
    allowed = (root / "evals/results/phase-003f-r1/gate_runs").resolve()
    if resolved != allowed and allowed not in resolved.parents:
        return ("R1_PERSISTENT_OUTPUT_OUTSIDE_GATE_ROOT",)
    return ()


def run_case_r1(
    root: Path,
    architecture_id: str,
    case_input: R1CaseInput,
    isolated_state: Any,
    context: Any,
    *,
    persist: bool = False,
) -> tuple[ShadowRunResult, bool]:
    """Run an R1 candidate with structured rejection for every untrusted boundary failure."""
    before = boundary_json(case_input.payload)
    context_errors = _context_reasons(architecture_id, context)
    state_errors = () if isinstance(isolated_state, Mapping) else ("R1_ISOLATED_STATE_INVALID",)
    output_errors = (
        _validate_output(root, context.output_dir, persist)
        if isinstance(context, ShadowContext) and isinstance(context.output_dir, Path)
        else ()
    )
    if context_errors or state_errors or output_errors:
        result = _blocked_result(
            architecture_id,
            case_input,
            context,
            tuple(sorted(set((*context_errors, *state_errors, *output_errors)))),
        )
        return result, before == boundary_json(case_input.payload)
    try:
        architecture = load_architecture_revision(architecture_id)
        result = architecture.evaluate_case(case_input, deep_freeze(isolated_state), context)
        decision_projection = {
            "outcome": result.decision.outcome,
            "component_results": thaw(result.decision.component_results),
            "proposed_actions": [
                thaw(action.payload) for action in result.decision.proposed_actions
            ],
        }
        if result.architecture_id != architecture_id or result.run_id != context.run_id:
            raise ValueError("R1_RESULT_RUN_BINDING_MISMATCH")
        if result.case_id != case_input.case_id or result.input_hash != case_input.input_hash:
            raise ValueError("R1_RESULT_INPUT_BINDING_MISMATCH")
        if _contains_formal_outcome(decision_projection):
            raise ValueError("R1_FORMAL_OUTCOME_PROHIBITED")
        if not verify_result_hash(result):
            raise ValueError("R1_RESULT_HASH_MISMATCH")
    except Exception as exc:  # noqa: BLE001 - the public R1 boundary is fail closed
        result = _blocked_result(
            architecture_id,
            case_input,
            context,
            ("R1_CANDIDATE_EXCEPTION_FAIL_CLOSED", f"R1_EXCEPTION_TYPE_{type(exc).__name__}"),
        )
    unchanged = before == boundary_json(case_input.payload)
    if persist:
        write_json_atomic(context.output_dir / "result.json", result.to_dict())
    return result, unchanged


__all__ = ["K1", "W1", "load_architecture_revision", "run_case_r1"]
