"""Neutral scoped-formula handoff compatibility; original Claim expectations stay frozen."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).with_name("test_competition_rc_claim_scope.py")
SPEC = importlib.util.spec_from_file_location("formula_neutral_fixtures", FIXTURE_PATH)
FIXTURES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FIXTURES
SPEC.loader.exec_module(FIXTURES)
core = FIXTURES.core


@pytest.mark.parametrize(
    "scenario", ["strings", "scoped_objects", "unknown_scope", "duplicate_id", "missing_expression"]
)
def test_formula_scope_handoff(core, tmp_path, scenario):
    root = tmp_path / "case"
    _claim, _manifest, _final, state = FIXTURES.bundle(core, root, 2)
    formulas = [
        {"formula_id": "F-LOCAL", "expression": "q=1", "requirements": ["REQ-N-1"]},
        {"formula_id": "F-JOINT", "expression": "r=q+1", "requirements": ["REQ-N-1", "REQ-N-2"]},
    ]
    if scenario == "strings":
        formulas = ["q=1", "r=q+1"]
    elif scenario == "unknown_scope":
        formulas[0]["requirements"] = ["REQ-UNKNOWN"]
    elif scenario == "duplicate_id":
        formulas[1]["formula_id"] = formulas[0]["formula_id"]
    elif scenario == "missing_expression":
        formulas[0].pop("expression")
    path = root / core.ARTIFACT_PATHS["assumptions_and_symbols"]
    content = core.read_artifact(root, "assumptions_and_symbols")["content"]
    content["formulas"] = formulas
    core.write_json(path, core.artifact("assumptions_and_symbols", content))
    state["evidence_bindings"][core.ARTIFACT_PATHS["assumptions_and_symbols"]] = core.file_hash(
        path
    )
    if scenario in {"strings", "scoped_objects"}:
        handoff = core.build_expected_handoff(root, state)
        assert core.validate_handoff(handoff, case_root=root, state=state).accepted
        if scenario == "scoped_objects":
            assert handoff["formulas"] == formulas
        else:
            assert [item["expression"] for item in handoff["formulas"]] == formulas
    else:
        with pytest.raises(ValueError, match="RC_HANDOFF_FORMULA_SCOPE_INVALID"):
            core.build_expected_handoff(root, state)
