from __future__ import annotations

import json
from pathlib import Path

import pytest

from cumcm_skill_lab.shadow_validation.grader import grade_result
from cumcm_skill_lab.shadow_validation.input_freeze import verify_input_freeze
from cumcm_skill_lab.shadow_validation.runner import run_case
from cumcm_skill_lab.specification.implementation_embargo import verify_embargo
from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.arch_s0 import ScaffoldOnlyAdapter
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    ShadowDecision,
    canonical_json,
    verify_result_hash,
)
from experiments.shadow_prototypes.common.public_cases import load_public_cases


def _context(tmp_path: Path, case_id: str) -> ShadowContext:
    return ShadowContext(
        run_id=f"R3-TEST-{case_id}",
        architecture_id=ScaffoldOnlyAdapter.architecture_id,
        stage="PUBLIC_VALIDATION",
        output_dir=tmp_path / case_id,
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=COMPONENT_IDS,
    )


def test_shadow_case_input_is_deeply_read_only() -> None:
    source = {"nested": {"items": [1, 2]}}
    case = ShadowCaseInput("case", COMPONENT_IDS[0], source, "a" * 64)
    source["nested"]["items"].append(3)
    assert canonical_json(case.payload) == b'{"nested":{"items":[1,2]}}'
    with pytest.raises(TypeError):
        case.payload["new"] = True  # type: ignore[index]


def test_s0_is_format_only_and_records_all_missing_capabilities(
    repo_root: Path, tmp_path: Path
) -> None:
    case = load_public_cases(repo_root)[0]
    result, unchanged = run_case(
        repo_root,
        ScaffoldOnlyAdapter.architecture_id,
        case,
        {},
        _context(tmp_path, case.case_id),
        persist=False,
    )
    assert unchanged
    assert result.decision.outcome == "ABSTAIN"
    assert result.decision.component_results == {
        component_id: "NOT_IMPLEMENTED" for component_id in COMPONENT_IDS
    }
    assert result.diagnostics["adapter_kind"] == "FORMAT_ONLY"
    assert verify_result_hash(result)


def test_runner_writes_only_to_isolated_output(repo_root: Path, tmp_path: Path) -> None:
    case = load_public_cases(repo_root)[0]
    context = _context(tmp_path, case.case_id)
    result, _ = run_case(repo_root, ScaffoldOnlyAdapter.architecture_id, case, {}, context)
    stored = json.loads((context.output_dir / "result.json").read_text(encoding="utf-8"))
    assert stored["result_hash"] == result.result_hash
    prohibited = _context(repo_root / "state", case.case_id)
    with pytest.raises(ValueError, match="SHADOW_OUTPUT_TARGET_PROHIBITED"):
        run_case(
            repo_root,
            ScaffoldOnlyAdapter.architecture_id,
            case,
            {},
            prohibited,
        )


def test_grader_emits_sanitized_class_only(repo_root: Path, tmp_path: Path) -> None:
    case = load_public_cases(repo_root)[0]
    result, unchanged = run_case(
        repo_root,
        ScaffoldOnlyAdapter.architecture_id,
        case,
        {},
        _context(tmp_path, case.case_id),
        persist=False,
    )
    grade = grade_result(
        result,
        {"expected_outcome": "PASS", "hidden_seed": 123},
        input_unchanged=unchanged,
    )
    assert grade["sanitized_failure_class"] == "ABSTENTION"
    assert "hidden_seed" not in grade


def test_shadow_decision_rejects_formal_final() -> None:
    with pytest.raises(ValueError, match="SHADOW_OUTCOME_NOT_ALLOWED"):
        ShadowDecision("FINAL", ("NARRATIVE_ONLY",))


def test_r3_freeze_and_embargo_are_valid(repo_root: Path) -> None:
    assert verify_input_freeze(repo_root) == []
    assert verify_embargo(repo_root) == []
