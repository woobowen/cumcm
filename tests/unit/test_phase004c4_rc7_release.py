from __future__ import annotations

import copy
import importlib.util
import sys

import pytest


def _module(repo_root):
    path = repo_root / "scripts/check_phase004c4_rc7_release.py"
    spec = importlib.util.spec_from_file_location("phase004c4_rc7_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _snapshot(module):
    value = {
        "schema_version": "phase-004c4-rc7-candidate/v1",
        "candidate_status": "PASS",
        "implementation_commit": module.IMPLEMENTATION_COMMIT,
        "evidence_subject_commit": "a" * 40,
        "target_versions": {"project": module.PROJECT_VERSION, "skill": module.SKILL_VERSION},
        "contract_versions": module.CONTRACT_VERSIONS,
        "checks": {
            check_id: {"status": "PASS", "passed": count, "failed": 0}
            for check_id, count in module.REQUIRED_CHECKS.items()
        },
        "evidence": {"fixture": {"path": "fixture", "sha256": "b" * 64}},
        "verification_receipts": {"fixture": {"path": "fixture", "sha256": "b" * 64}},
        "invariants": {
            "formal_skill_count": 1,
            "third_party_integrated": False,
            "historical_mutation_count": 0,
            "answer_leakage_count": 0,
            "secret_count": 0,
            "problem_hardcoding_count": 0,
            "heldout_2025_access_count": 0,
        },
    }
    for check_id in (
        "historical_read_only",
        "anti_hardcoding",
        "skill_discovery",
        "leakage",
        "secrets",
        "strict",
        "local_ci",
        "full_pytest",
    ):
        value["checks"][check_id] = {"status": "PASS"}
    value["candidate_snapshot_hash"] = module._canonical_hash(value)
    return value


def test_rc7_candidate_snapshot_passes_without_live_state(repo_root) -> None:
    module = _module(repo_root)
    assert module.evaluate_candidate_snapshot(_snapshot(module)) == {
        "status": "PASS",
        "reason_codes": [],
    }


@pytest.mark.parametrize(
    ("field", "mutation", "reason"),
    [
        (
            "target_versions",
            lambda value: value.update(skill="0.2.0-competition-rc6"),
            "RC7_CANDIDATE_VERSION_INVALID",
        ),
        (
            "checks",
            lambda value: value["full_pytest"].update(status="BLOCK"),
            "RC7_CANDIDATE_CHECK_INVALID:full_pytest",
        ),
        (
            "invariants",
            lambda value: value.update(third_party_integrated=True),
            "RC7_CANDIDATE_INVARIANTS_INVALID",
        ),
    ],
)
def test_rc7_candidate_snapshot_mutations_fail_closed(repo_root, field, mutation, reason) -> None:
    module = _module(repo_root)
    value = copy.deepcopy(_snapshot(module))
    mutation(value[field])
    value["candidate_snapshot_hash"] = module._canonical_hash(
        {key: item for key, item in value.items() if key != "candidate_snapshot_hash"}
    )
    result = module.evaluate_candidate_snapshot(value)
    assert result["status"] == "BLOCK"
    assert reason in result["reason_codes"]
