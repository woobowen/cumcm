from __future__ import annotations

import math

from experiments.shadow_prototypes.common.r1_interface import (
    R1CaseInput,
    boundary_json,
    sha256_boundary_json,
)


def test_untrusted_boundary_snapshot_is_deterministic_for_nonfinite_numbers() -> None:
    payload = {"scores": [math.nan, math.inf, -math.inf]}
    first = boundary_json(payload)
    second = boundary_json(payload)

    assert first == second
    assert b'"__invalid_nonfinite_number__":"NaN"' in first
    assert b'"__invalid_nonfinite_number__":"+Infinity"' in first
    assert b'"__invalid_nonfinite_number__":"-Infinity"' in first


def test_shadow_case_can_transport_nonfinite_input_without_accepting_it() -> None:
    payload = {"score": math.nan}
    case = R1CaseInput(
        case_id="R1-NAN-BOUNDARY",
        component_id="leakage-safe-model-comparison-gate",
        payload=payload,
        input_hash=sha256_boundary_json(payload),
    )

    assert math.isnan(case.payload["score"])
    assert case.input_hash == sha256_boundary_json(case.payload)
