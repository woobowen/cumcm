import json
from copy import deepcopy

from cumcm_skill_lab.authorization_c1.candidate_evidence import (
    TEST_EVIDENCE_PATH as C1_TEST_EVIDENCE_PATH,
)
from cumcm_skill_lab.authorization_c1.models import file_sha256
from cumcm_skill_lab.authorization_c2.candidate_evidence import (
    BINDING_FIELDS,
    MUTATION_SPECS,
    PRECONDITIONS_PATH,
    TEST_EVIDENCE_PATH,
    TEST_PLAN_PATH,
    build_preconditions,
    build_test_evidence,
    build_test_plan,
    check_or_write_candidate_evidence_inputs,
    validate_bound_artifact,
)
from cumcm_skill_lab.authorization_c2.candidate_freeze import CANDIDATE_PATH, FREEZE_PATH

DEPENDENCY_TEST_ID = "C1-DET-R2-AUDIT-REPLAY-ACYCLIC-PREREQUISITE-001"


def _read(repo_root, path):
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def test_c2_pre_audit_evidence_is_reproducible(repo_root):
    result = check_or_write_candidate_evidence_inputs(repo_root, check=True)
    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["test_evidence_count"] == result["passed_count"] == 31


def test_c2_preconditions_are_fresh_and_all_pass(repo_root):
    value = _read(repo_root, PRECONDITIONS_PATH)
    assert value == build_preconditions(repo_root)
    assert value["all_required_pass"] is True
    assert value["required_check_count"] == value["passed_check_count"] == 25
    assert value["failed_check_ids"] == []
    assert value["artifact_sequence_index"] == 13


def test_c2_test_plan_is_wholly_regenerated(repo_root):
    value = _read(repo_root, TEST_PLAN_PATH)
    assert value == build_test_plan(repo_root)
    assert value["test_count"] == len(MUTATION_SPECS) == 31
    assert {item["test_id"] for item in value["tests"]} == {item[0] for item in MUTATION_SPECS}
    assert DEPENDENCY_TEST_ID in {item["test_id"] for item in value["tests"]}
    assert value["artifact_sequence_index"] == 14


def test_c2_mutation_evidence_is_candidate_bound_and_all_pass(repo_root):
    evidence = _read(repo_root, TEST_EVIDENCE_PATH)
    freeze = _read(repo_root, FREEZE_PATH)
    plan = _read(repo_root, TEST_PLAN_PATH)
    assert evidence == build_test_evidence(repo_root)
    assert evidence["evidence_count"] == evidence["passed_count"] == 31
    assert evidence["artifact_sequence_index"] == 15
    for item in evidence["test_evidence"]:
        assert item["status"] == "PASS"
        assert item["actual_result"] == "REJECTED"
        assert item["exit_code"] == 1
        assert all(field in item for field in BINDING_FIELDS)
        assert (
            validate_bound_artifact(
                item,
                freeze,
                expected_parent=plan["test_plan_hash"],
                expected_sequence=15,
                hash_field="evidence_hash",
            )
            == []
        )


def test_c1_final_dependency_finding_has_new_deterministic_evidence(repo_root):
    evidence = _read(repo_root, TEST_EVIDENCE_PATH)
    item = next(item for item in evidence["test_evidence"] if item["test_id"] == DEPENDENCY_TEST_ID)
    assert item["expected_error"] == "C1_R2_AUDIT_REPLAY_SEMANTIC_CYCLE"
    assert "C1_R2_AUDIT_REPLAY_SEMANTIC_CYCLE" in item["actual_errors"]
    assert "C1_R2_REPLAY_TO_AUDIT_PREREQUISITE_EDGE_MISSING" in item["actual_errors"]
    assert item["input_observation"]["removed_prerequisite_edge"] == {
        "source": "L2-R2-REPLAY",
        "target": "L3-R2-DECISION-AUDIT",
    }


def test_c2_evidence_code_and_io_are_hashed(repo_root):
    evidence = _read(repo_root, TEST_EVIDENCE_PATH)
    code_hash = file_sha256(
        repo_root / "src/cumcm_skill_lab/authorization_c2/candidate_evidence.py"
    )
    for item in evidence["test_evidence"]:
        assert item["test_code_hash"] == code_hash
        assert len(item["input_hash"]) == len(item["output_hash"]) == 64


def test_c2_evidence_did_not_modify_candidate_or_reuse_c1_set(repo_root):
    freeze = _read(repo_root, FREEZE_PATH)
    c2_evidence = _read(repo_root, TEST_EVIDENCE_PATH)
    c1_evidence = _read(repo_root, C1_TEST_EVIDENCE_PATH)
    assert file_sha256(repo_root / CANDIDATE_PATH) == freeze["candidate_file_sha256"]
    assert c2_evidence["candidate_id"] != c1_evidence["candidate_id"]
    assert c2_evidence["evidence_hash"] != c1_evidence["evidence_hash"]
    assert set(c2_evidence["test_evidence_hashes"]).isdisjoint(c1_evidence["test_evidence_hashes"])


def test_c1_evidence_cannot_be_relabelled_as_c2(repo_root):
    freeze = _read(repo_root, FREEZE_PATH)
    plan = _read(repo_root, TEST_PLAN_PATH)
    c1_item = deepcopy(_read(repo_root, C1_TEST_EVIDENCE_PATH)["test_evidence"][0])
    errors = validate_bound_artifact(
        c1_item,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=15,
    )
    assert "C2_BOUND_CANDIDATE_ID_MISMATCH" in errors
    assert "C2_BOUND_PARENT_ARTIFACT_HASH_MISMATCH" in errors
    assert "C2_BOUND_ARTIFACT_SEQUENCE_MISMATCH" in errors
