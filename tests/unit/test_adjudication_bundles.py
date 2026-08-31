from copy import deepcopy

import pytest

from cumcm_skill_lab.adjudication.bundles.builder import build_role
from cumcm_skill_lab.adjudication.bundles.completeness import completeness_errors
from cumcm_skill_lab.adjudication.bundles.role_views import ROLE_ORDER
from cumcm_skill_lab.adjudication.bundles.size_budget import (
    MAX_ESTIMATED_TOKENS,
    MAX_NORMALIZED_BYTES,
    enforce_size_budget,
    measure_bundle,
)


@pytest.mark.parametrize("role", ROLE_ORDER)
def test_each_role_bundle_is_complete_and_bounded(repo_root, role):
    files, manifest = build_role(repo_root, role)
    assert manifest["role"] == role
    assert manifest["measurement"]["normalized_bytes"] <= MAX_NORMALIZED_BYTES
    assert manifest["measurement"]["estimated_tokens"] <= MAX_ESTIMATED_TOKENS
    assert manifest["recovery_excluded_count"] == 5
    assert len(manifest["blocker_ids"]) == 13
    assert manifest["files"]["output_schema.json"]["sha256"] == manifest["output_schema_hash"]


def test_role_views_are_specific(repo_root):
    correctness, _ = build_role(repo_root, "CORRECTNESS_JUDGE")
    engineering, _ = build_role(repo_root, "ENGINEERING_REPRODUCIBILITY_JUDGE")
    assert correctness["eligible_evidence.json"]["evidence_sections"] == [
        "eligibility",
        "coverage",
        "oracles",
    ]
    assert engineering["eligible_evidence.json"]["evidence_sections"] == [
        "eligibility",
        "process",
    ]
    assert correctness != engineering


@pytest.mark.parametrize("role", ROLE_ORDER)
def test_every_role_retains_all_blockers(repo_root, role):
    files, manifest = build_role(repo_root, role)
    visible = {
        item["finding_id"]
        for item in files["findings.json"]["findings"]
        if item["severity"] == "BLOCKER"
    }
    assert visible == set(manifest["blocker_ids"])


@pytest.mark.parametrize("role", ROLE_ORDER)
def test_recovery_is_explicitly_excluded_in_every_bundle(repo_root, role):
    files, _ = build_role(repo_root, role)
    excluded = files["excluded_evidence.json"]
    assert excluded["recovery_policy"] == "GAP_EVIDENCE_ONLY"
    assert len(excluded["recovery_records"]) == 5
    assert all(item["ranking_eligible"] is False for item in excluded["recovery_records"])


def test_bundle_hash_and_order_are_stable(repo_root):
    first_files, first_manifest = build_role(repo_root, "CORRECTNESS_JUDGE")
    second_files, second_manifest = build_role(repo_root, "CORRECTNESS_JUDGE")
    assert first_files == second_files
    assert first_manifest == second_manifest


def test_bundle_is_identity_free(repo_root):
    files, _ = build_role(repo_root, "BLIND_DISSENT_JUDGE")
    text = str(files).lower()
    for marker in ("yushui", "handsomezr", "no_project_modeling_skill", "woobowen"):
        assert marker not in text


def test_peer_outputs_are_not_exposed_to_blind_roles(repo_root):
    for role in ROLE_ORDER[:4]:
        files, _ = build_role(repo_root, role)
        assert files["dependencies.json"] == {"required": [], "ready": True, "records": []}
        assert files["bundle_index.json"]["peer_outputs_visible"] is False


def test_meta_waits_for_four_role_outputs(repo_root):
    files, manifest = build_role(repo_root, "EVIDENCE_META_ADJUDICATOR")
    assert manifest["dependencies_ready"] is False
    assert files["dependencies.json"]["required"] == list(ROLE_ORDER[:4])


def test_auditor_waits_for_meta_and_decisions(repo_root):
    files, manifest = build_role(repo_root, "DECISION_AUDITOR")
    assert manifest["dependencies_ready"] is False
    status = {item["role"]: item["status"] for item in files["dependencies.json"]["records"]}
    assert status["EVIDENCE_META_ADJUDICATOR"] == "PENDING"
    assert status["AUTOMATED_DECISIONS"] == "PENDING"


def test_missing_blocker_fails_completeness(repo_root):
    files, manifest = build_role(repo_root, "CORRECTNESS_JUDGE")
    mutated = deepcopy(files)
    missing = manifest["blocker_ids"][0]
    mutated["findings.json"]["findings"] = [
        item for item in mutated["findings.json"]["findings"] if item["finding_id"] != missing
    ]
    assert f"BLOCKER_MISSING:{missing}" in completeness_errors(
        mutated, set(manifest["blocker_ids"])
    )


def test_identity_injection_fails_completeness(repo_root):
    files, manifest = build_role(repo_root, "CORRECTNESS_JUDGE")
    mutated = deepcopy(files)
    mutated["role_task.json"]["injected"] = "YUSHUI"
    assert "IDENTITY_LEAK:YUSHUI" in completeness_errors(mutated, set(manifest["blocker_ids"]))


def test_measurement_is_deterministic():
    first = {"a.json": {"b": 2, "a": 1}}
    second = {"a.json": {"a": 1, "b": 2}}
    assert measure_bundle(first) == measure_bundle(second)


def test_byte_budget_excess_fails_closed():
    with pytest.raises(ValueError, match="BUNDLE_BYTE_BUDGET_EXCEEDED"):
        enforce_size_budget({"oversize.json": "x" * (MAX_NORMALIZED_BYTES + 1)})
