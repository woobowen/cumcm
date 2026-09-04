"""Format-only adapter for the unchanged scaffold baseline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    ShadowDecision,
    ShadowRunResult,
    build_result,
)


class ScaffoldOnlyAdapter:
    """Expose the current scaffold through the shared interface without adding guards."""

    architecture_id = "ARCH-S0-RETAIN-SCAFFOLD-ONLY"

    def evaluate_case(
        self,
        case_input: ShadowCaseInput,
        isolated_state: Mapping[str, Any],
        run_context: ShadowContext,
    ) -> ShadowRunResult:
        del isolated_state
        if run_context.architecture_id != self.architecture_id:
            raise ValueError("S0_CONTEXT_ARCHITECTURE_MISMATCH")
        if case_input.component_id not in COMPONENT_IDS:
            decision = ShadowDecision("BLOCK", ("SCAFFOLD_FORMAT_INVALID",))
        else:
            decision = ShadowDecision(
                "ABSTAIN",
                ("SCAFFOLD_ONLY_CAPABILITY_MISSING",),
                {component_id: "NOT_IMPLEMENTED" for component_id in COMPONENT_IDS},
            )
        return build_result(
            context=run_context,
            case_input=case_input,
            decision=decision,
            diagnostics={
                "adapter_kind": "FORMAT_ONLY",
                "missing_capabilities": list(COMPONENT_IDS),
                "formal_state_writes": 0,
                "hidden_vault_accesses": 0,
                "third_party_executions": 0,
            },
        )


__all__ = ["ScaffoldOnlyAdapter"]
