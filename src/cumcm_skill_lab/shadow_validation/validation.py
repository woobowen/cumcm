"""Scope and interface validation for isolated R3 prototypes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from experiments.shadow_prototypes import ARCHITECTURE_IDS, COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import ShadowContext, verify_result_hash
from experiments.shadow_prototypes.common.public_cases import (
    load_public_cases,
    public_isolated_state,
)

from .runner import run_case


def validate_prototypes(root: Path, architecture_ids: tuple[str, ...]) -> dict[str, object]:
    errors: list[str] = []
    executions = 0
    if any(item not in ARCHITECTURE_IDS for item in architecture_ids):
        errors.append("UNFROZEN_ARCHITECTURE_REQUESTED")
    cases = load_public_cases(root)
    if len(cases) != 16 or {case.component_id for case in cases} != set(COMPONENT_IDS):
        errors.append("PUBLIC_CASE_CATALOG_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="cumcm-shadow-validation-") as directory:
        for architecture_id in architecture_ids:
            for index, case in enumerate(cases):
                context = ShadowContext(
                    run_id=f"R3-VALIDATE-{architecture_id}-{index:02d}",
                    architecture_id=architecture_id,
                    stage="PUBLIC_VALIDATION",
                    output_dir=Path(directory) / architecture_id / case.case_id,
                    timeout_seconds=30,
                    operation_budget=100,
                    enabled_components=COMPONENT_IDS,
                )
                try:
                    result, unchanged = run_case(
                        root,
                        architecture_id,
                        case,
                        public_isolated_state(),
                        context,
                        persist=False,
                    )
                except (ImportError, ModuleNotFoundError, ValueError) as exc:
                    errors.append(f"PROTOTYPE_EXECUTION_FAILED:{architecture_id}:{exc}")
                    break
                executions += 1
                if not unchanged:
                    errors.append(f"RAW_INPUT_MUTATED:{architecture_id}:{case.case_id}")
                if not verify_result_hash(result):
                    errors.append(f"RESULT_HASH_INVALID:{architecture_id}:{case.case_id}")
                if result.decision.outcome in {"FINAL", "FORMALLY_INTEGRATED"}:
                    errors.append(f"FORMAL_OUTCOME_EMITTED:{architecture_id}:{case.case_id}")
                if int(result.diagnostics.get("formal_state_writes", 0)) != 0:
                    errors.append(f"FORMAL_STATE_WRITE:{architecture_id}:{case.case_id}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "architecture_ids": list(architecture_ids),
        "case_count": len(cases),
        "execution_count": executions,
        "errors": sorted(set(errors)),
    }


__all__ = ["validate_prototypes"]
