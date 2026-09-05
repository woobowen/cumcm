"""Pre-second-revision fault cases from the independent Claim contract audit."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "identity_neutral_fixtures", Path(__file__).with_name("test_competition_rc_claim_scope.py")
)
FIXTURES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FIXTURES
SPEC.loader.exec_module(FIXTURES)
core = FIXTURES.core


def test_aggregate_cannot_support_itself(core, tmp_path):
    claim, manifest, final, state = FIXTURES.bundle(core, tmp_path, 2)
    claim["claim_id"] = claim["requirement_claims"]["REQ-N-1"]["claim_id"]
    result = core.validate_claim(claim, manifest, final, case_root=tmp_path, state=state)
    assert not result.accepted
    assert "RC_CLAIM_AGGREGATE_ID_COLLISION" in result.reason_codes


def test_joint_statement_and_final_forgery_cannot_escape_captured_scope(core, tmp_path):
    claim, manifest, final, state = FIXTURES.bundle(core, tmp_path, 2)
    claim["claim_text"] = claim["supported_scope"] = final["claim_scope"] = (
        "Unsupported universal claim."
    )
    result = core.validate_claim(claim, manifest, final, case_root=tmp_path, state=state)
    assert not result.accepted
    assert "RC_CLAIM_FINAL_SCOPE_MISMATCH" in result.reason_codes


@pytest.mark.parametrize(
    "fault",
    [
        "empty_id",
        "empty_scope",
        "duplicate_scope",
        "extra_key",
        "empty_expression",
        "nonstring_expression",
    ],
)
def test_scoped_formula_malformed_records_fail_closed(core, tmp_path, fault):
    _claim, _manifest, _final, state = FIXTURES.bundle(core, tmp_path, 2)
    formula = {"formula_id": "F-LOCAL", "expression": "q=1", "requirements": ["REQ-N-1"]}
    changes = {
        "empty_id": {"formula_id": ""},
        "empty_scope": {"requirements": []},
        "duplicate_scope": {"requirements": ["REQ-N-1", "REQ-N-1"]},
        "extra_key": {"uncaptured_value": 999},
        "empty_expression": {"expression": ""},
        "nonstring_expression": {"expression": 1},
    }
    formula.update(changes[fault])
    content = copy.deepcopy(core.read_artifact(tmp_path, "assumptions_and_symbols")["content"])
    content["formulas"] = [formula]
    path = tmp_path / core.ARTIFACT_PATHS["assumptions_and_symbols"]
    core.write_json(path, core.artifact("assumptions_and_symbols", content))
    state["evidence_bindings"][core.ARTIFACT_PATHS["assumptions_and_symbols"]] = core.file_hash(
        path
    )
    with pytest.raises(ValueError, match="RC_HANDOFF_FORMULA_SCOPE_INVALID"):
        core.build_expected_handoff(tmp_path, state)
