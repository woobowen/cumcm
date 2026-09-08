"""RC8 qualification is separate from RC7 history and live activation."""

import copy
import importlib.util
import json
import sys

import pytest


def module(repo_root):
    spec = importlib.util.spec_from_file_location(
        "rc8_release_subject_test", repo_root / "scripts/check_phase004c4_rc7_release.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def snapshot(mod):
    protocol = json.loads((mod.ROOT / mod.RC8_PROTOCOL).read_text())
    candidate = {
        "schema_version": "phase-004c5-rc8-candidate/v1",
        "candidate_id": "CANDIDATE-COMPETITION-RC8-004C5",
        "candidate_status": "PASS",
        "target_versions": {"project": mod.RC8_PROJECT, "skill": mod.RC8_SKILL},
        "contract_versions": mod.CONTRACT_VERSIONS,
        "accepted_scope": "RESEARCH_AND_FRESH_VALIDATION_ELIGIBILITY_ONLY",
        "team_compliance_review": "NOT_RUN",
        "subject_commit": "a" * 40,
        "protocol_sha256": mod._canonical_hash(protocol),
        "implementation_files": {"synthetic_fixture.py": "b" * 64},
        "verification_receipts": {key: {} for key in protocol["required_receipts"]},
    }
    candidate["candidate_snapshot_hash"] = mod._canonical_hash(candidate)
    return candidate, protocol


def test_rc8_snapshot_validation_has_no_live_activation_dependency(repo_root):
    mod = module(repo_root)
    candidate, protocol = snapshot(mod)
    assert mod.evaluate_rc8_candidate_snapshot(candidate, protocol)["status"] == "PASS"


@pytest.mark.parametrize("mutation", ["version", "scope", "subject", "receipt", "protocol", "hash"])
def test_rc8_unknown_identity_or_weakened_qualification_is_rejected(repo_root, mutation):
    mod = module(repo_root)
    candidate, protocol = snapshot(mod)
    if mutation == "version":
        candidate["target_versions"]["skill"] = "0.2.0-competition-rc999"
    elif mutation == "scope":
        candidate["accepted_scope"] = "COMPETITION_WINNER"
    elif mutation == "subject":
        candidate["subject_commit"] = "HEAD"
    elif mutation == "receipt":
        del candidate["verification_receipts"]["native_audit"]
    elif mutation == "protocol":
        protocol = copy.deepcopy(protocol)
        protocol["minimum_full_pytest_passed"] = 0
        candidate["protocol_sha256"] = mod._canonical_hash(protocol)
    if mutation != "hash":
        del candidate["candidate_snapshot_hash"]
        candidate["candidate_snapshot_hash"] = mod._canonical_hash(candidate)
    else:
        candidate["candidate_snapshot_hash"] = "0" * 64
    assert mod.evaluate_rc8_candidate_snapshot(candidate, protocol)["status"] == "BLOCK"


def test_historical_rc7_uses_original_subject_after_current_runtime_changes(repo_root):
    mod = module(repo_root)
    assert mod.evaluate_candidate_repository()["status"] == "PASS"
    assert mod.evaluate_live_repository()["status"] == "PASS"


def test_historical_subject_hash_mismatch_is_not_hidden_by_current_version(repo_root, monkeypatch):
    mod = module(repo_root)
    original = mod._git_blob_hash

    def altered(subject, path):
        if path == ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py":
            return "0" * 64
        return original(subject, path)

    monkeypatch.setattr(mod, "_git_blob_hash", altered)
    assert mod.evaluate_live_repository()["status"] == "BLOCK"


@pytest.mark.parametrize("raw", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_nonfinite_receipt_counts_cannot_qualify(repo_root, tmp_path, raw):
    mod = module(repo_root)
    path = tmp_path / "receipt.json"
    path.write_text('{"passed": ' + raw + "}")
    receipt = mod._read_json(path)
    assert not mod._integer_at_least(receipt.get("passed"), 80)


@pytest.mark.parametrize("value", [True, False, 2000.0, "2000", None, -1, 0, 1999])
def test_full_ci_requires_an_actual_sufficient_integer_count(repo_root, value):
    mod = module(repo_root)
    assert not mod._integer_at_least(value, 2000)
    assert mod._integer_at_least(2000, 2000)
