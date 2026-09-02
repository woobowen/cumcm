from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.expansion.closure import build_closure, validate_closure
from cumcm_skill_lab.expansion.models import read_json


def test_insufficient_evidence_locks_phase002d_adjudication(repo_root):
    value = build_closure(repo_root)
    assert value["status"] == "LOCKED_EVIDENCE_INSUFFICIENT"
    assert value["automated_decision_ids"] == []


def test_native_subagents_were_not_started(repo_root):
    assert build_closure(repo_root)["native_subagents_started"] is False


def test_decision_auditor_and_replay_are_not_fabricated(repo_root):
    value = build_closure(repo_root)
    assert value["decision_auditor"] == "NOT_RUN_PRECONDITION_FAILED"
    assert value["decision_replay"] == "NOT_RUN_PRECONDITION_FAILED"


def test_incomplete_route_only_allows_same_phase(repo_root):
    value = build_closure(repo_root)
    assert value["route_replay"] == "PASS"
    assert value["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D"
    assert value["phase_003_allowed"] is False
    assert value["phase_003_started"] is False


def test_closure_record_uses_phase002d_contract(repo_root):
    value = build_closure(repo_root)
    schema = read_json(repo_root / "contracts/phase002d_decision.schema.json")
    Draft202012Validator(schema).validate(value)
    assert validate_closure(repo_root, value) == []


def test_closure_hash_mutation_fails_closed(repo_root):
    value = deepcopy(build_closure(repo_root))
    value["record_hash"] = "0" * 64
    assert "PHASE002D_CLOSURE_HASH_MISMATCH" in validate_closure(repo_root, value)


def test_phase003_unlock_is_rejected(repo_root):
    value = deepcopy(build_closure(repo_root))
    value["phase_003_allowed"] = True
    assert "PHASE003_ILLEGALLY_UNLOCKED" in validate_closure(repo_root, value)


def test_sufficiency_would_require_m8_instead_of_locked_record(repo_root, monkeypatch):
    from cumcm_skill_lab.expansion import closure

    original = closure.read_json

    def fake_read(path):
        value = original(path)
        if path.name == "evidence_sufficiency.json":
            value = dict(value)
            value["result"] = "SUFFICIENT"
        return value

    monkeypatch.setattr(closure, "read_json", fake_read)
    with pytest.raises(RuntimeError, match="PHASE002D_M8_REQUIRED"):
        closure.build_closure(repo_root)
