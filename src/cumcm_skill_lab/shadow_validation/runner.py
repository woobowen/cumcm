"""Uniform offline runner for the three isolated shadow architecture arms."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from experiments.shadow_prototypes.common.interface import (
    PROHIBITED_FORMAL_OUTCOMES,
    ShadowCaseInput,
    ShadowContext,
    ShadowRunResult,
    canonical_json,
    deep_freeze,
    thaw,
    verify_result_hash,
)

from .io import write_json_atomic

ARCHITECTURE_LOADERS = {
    "ARCH-S0-RETAIN-SCAFFOLD-ONLY": (
        "experiments.shadow_prototypes.arch_s0.adapter",
        "ScaffoldOnlyAdapter",
    ),
    "ARCH-W1-WORKFLOW-ONLY-GUARDS": (
        "experiments.shadow_prototypes.arch_w1.adapter",
        "WorkflowGuardAdapter",
    ),
    "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL": (
        "experiments.shadow_prototypes.arch_k1.kernel",
        "DeterministicEvidenceKernel",
    ),
}
PROHIBITED_OUTPUT_PARTS = {
    ".agents",
    "benchmark-vault",
    "state",
    "phase-002",
    "phase-002a",
    "phase-002b",
    "phase-002c",
    "phase-002d",
    "phase-002d-r1",
    "phase-002d-r2",
    "phase-002d-r2a",
    "phase-002d-r2a-c1",
}


def load_architecture(architecture_id: str) -> Any:
    try:
        module_name, class_name = ARCHITECTURE_LOADERS[architecture_id]
    except KeyError as exc:
        raise ValueError(f"UNKNOWN_SHADOW_ARCHITECTURE:{architecture_id}") from exc
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls()


def _validate_output_dir(root: Path, output_dir: Path, *, persist: bool) -> None:
    resolved = output_dir.resolve()
    formal_targets = [
        (root / ".agents/skills/cumcm-modeling-evidence").resolve(),
        (root / "state").resolve(),
        (root / "benchmark-vault").resolve(),
    ]
    if any(resolved == target or target in resolved.parents for target in formal_targets):
        raise ValueError("SHADOW_OUTPUT_TARGET_PROHIBITED")
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError:
        if persist:
            raise ValueError("SHADOW_PERSISTENT_OUTPUT_OUTSIDE_R3_ROOT") from None
        return
    if any(part in PROHIBITED_OUTPUT_PARTS for part in relative.parts):
        raise ValueError("SHADOW_OUTPUT_TARGET_PROHIBITED")
    if persist:
        allowed_root = (root / "evals/results/phase-002d-r3").resolve()
        if resolved != allowed_root and allowed_root not in resolved.parents:
            raise ValueError("SHADOW_PERSISTENT_OUTPUT_OUTSIDE_R3_ROOT")


def _contains_formal_outcome(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_formal_outcome(item) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_formal_outcome(item) for item in value)
    return isinstance(value, str) and value in PROHIBITED_FORMAL_OUTCOMES


def run_case(
    root: Path,
    architecture_id: str,
    case_input: ShadowCaseInput,
    isolated_state: Mapping[str, Any],
    context: ShadowContext,
    *,
    persist: bool = True,
) -> tuple[ShadowRunResult, bool]:
    if context.architecture_id != architecture_id:
        raise ValueError("RUN_CONTEXT_ARCHITECTURE_MISMATCH")
    _validate_output_dir(root, context.output_dir, persist=persist)
    before = canonical_json(case_input.payload)
    architecture = load_architecture(architecture_id)
    result = architecture.evaluate_case(case_input, deep_freeze(isolated_state), context)
    unchanged = before == canonical_json(case_input.payload)
    if result.architecture_id != architecture_id or result.run_id != context.run_id:
        raise ValueError("SHADOW_RESULT_BINDING_MISMATCH")
    if result.case_id != case_input.case_id:
        raise ValueError("SHADOW_RESULT_CASE_BINDING_MISMATCH")
    if result.input_hash != case_input.input_hash:
        raise ValueError("SHADOW_RESULT_INPUT_BINDING_MISMATCH")
    decision_projection = {
        "outcome": result.decision.outcome,
        "component_results": thaw(result.decision.component_results),
        "proposed_actions": [
            {"action_type": action.action_type, "payload": thaw(action.payload)}
            for action in result.decision.proposed_actions
        ],
    }
    if _contains_formal_outcome(decision_projection):
        raise ValueError("FORMAL_OUTCOME_PROHIBITED")
    if not verify_result_hash(result):
        raise ValueError("SHADOW_RESULT_HASH_MISMATCH")
    if persist:
        write_json_atomic(context.output_dir / "result.json", result.to_dict())
    return result, unchanged


__all__ = ["ARCHITECTURE_LOADERS", "load_architecture", "run_case"]
