from copy import deepcopy

import pytest

from cumcm_skill_lab.adjudication.models import read_json
from cumcm_skill_lab.specification.decision_audit import (
    AUDIT_PATH,
    AUDITOR_CHECKS,
    BUNDLE_PATH,
    RAW_AUDIT_PATH,
    build_auditor_bundle,
    evaluate_audit_checks,
    validate_audit,
)


@pytest.mark.parametrize("check_name", AUDITOR_CHECKS)
def test_deterministic_decision_audit_check_passes(repo_root, check_name):
    assert evaluate_audit_checks(repo_root)[check_name] is True


def test_auditor_bundle_is_hash_bound_and_current(repo_root):
    assert read_json(repo_root / BUNDLE_PATH) == build_auditor_bundle(repo_root)


def test_formal_audit_passes_contract_and_bindings(repo_root):
    audit = read_json(repo_root / AUDIT_PATH)
    assert audit["result"] == "PASS"
    assert audit["replayable"] is True
    assert validate_audit(repo_root, audit) == []


def test_raw_audit_is_preserved_except_checkpoint_normalization(repo_root):
    raw = read_json(repo_root / RAW_AUDIT_PATH)
    formal = read_json(repo_root / AUDIT_PATH)
    raw["checkpoint_hash"] = formal["checkpoint_hash"]
    assert raw == formal


def test_false_pass_mutation_is_rejected(repo_root):
    audit = deepcopy(read_json(repo_root / AUDIT_PATH))
    audit["checks"]["offline_replay_stable"] = False
    assert validate_audit(repo_root, audit)
