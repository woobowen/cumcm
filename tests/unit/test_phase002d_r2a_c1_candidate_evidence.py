import json
from copy import deepcopy

import pytest

from cumcm_skill_lab.authorization_c1 import candidate_evidence as evidence_module
from cumcm_skill_lab.authorization_c1 import candidate_freeze as freeze_module
from cumcm_skill_lab.authorization_c1.candidate_evidence import (
    BINDING_FIELDS,
    CLOSURE_PATH,
    FINDING_TESTS,
    MUTATION_SPECS,
    POST_EVIDENCE_PROSECUTOR_PATH,
    PRECONDITIONS_PATH,
    TEST_EVIDENCE_PATH,
    TEST_PLAN_PATH,
    build_candidate_report_projection,
    build_candidate_state_projection,
    build_closure,
    build_preconditions,
    build_test_evidence,
    build_test_plan,
    validate_bound_artifact,
    validate_candidate_evidence_chain,
    validate_candidate_report_projection,
    validate_candidate_state_projection,
    validate_closure_claims,
    validate_exact_candidate_bundle,
    validate_postfreeze_observation,
    validate_precondition_semantics,
)
from cumcm_skill_lab.authorization_c1.candidate_freeze import (
    CANDIDATE_PATH,
    FREEZE_PATH,
)
from cumcm_skill_lab.authorization_c1.models import file_sha256, sha256_json


def _read(repo_root, path):
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def _artifacts(repo_root):
    return (
        _read(repo_root, FREEZE_PATH),
        _read(repo_root, PRECONDITIONS_PATH),
        _read(repo_root, TEST_PLAN_PATH),
        _read(repo_root, TEST_EVIDENCE_PATH),
        _read(repo_root, CLOSURE_PATH),
    )


def test_candidate_bound_chain_validates(repo_root):
    assert validate_candidate_evidence_chain(repo_root) == []


def test_preconditions_are_fresh_and_all_pass(repo_root):
    value = build_preconditions(repo_root)
    assert value["all_required_pass"] is True
    assert value["required_check_count"] == value["passed_check_count"] == 23
    assert value["historical_preconditions_classification"] == "PREREQUISITE_CONTEXT_ONLY"


def test_test_plan_has_all_required_mutations(repo_root):
    value = build_test_plan(repo_root)
    assert value["test_count"] == len(MUTATION_SPECS) == 30
    assert len({item["test_id"] for item in value["tests"]}) == 30


def test_all_mutation_evidence_passes(repo_root):
    value = build_test_evidence(repo_root)
    assert value["evidence_count"] == value["passed_count"] == 30
    assert all(item["actual_result"] == "REJECTED" for item in value["test_evidence"])
    assert all(item["exit_code"] == 1 for item in value["test_evidence"])


def test_each_l4plus_artifact_has_exact_candidate_binding(repo_root):
    _freeze, preconditions, plan, evidence, closure = _artifacts(repo_root)
    for artifact in (preconditions, plan, evidence, closure, *evidence["test_evidence"]):
        assert all(field in artifact for field in BINDING_FIELDS)


@pytest.mark.parametrize(
    "field",
    [
        "candidate_id",
        "candidate_file_sha256",
        "canonical_candidate_hash",
        "candidate_freeze_hash",
    ],
)
def test_missing_exact_candidate_binding_field_is_rejected(repo_root, field):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence["test_evidence"][0])
    del mutated[field]
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
        hash_field="evidence_hash",
    )
    assert f"C1_BOUND_FIELD_MISSING:{field}" in errors


def test_wrong_candidate_evidence_is_rejected(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence["test_evidence"][0])
    mutated["candidate_id"] = "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_CANDIDATE_ID_MISMATCH" in errors


def test_c1_evidence_cannot_be_relabeled_for_c2(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    c2_freeze = deepcopy(freeze)
    c2_freeze["candidate_id"] = "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2"
    errors = validate_bound_artifact(
        evidence["test_evidence"][0],
        c2_freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_CANDIDATE_ID_MISMATCH" in errors


def test_evidence_predating_candidate_freeze_is_rejected(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence["test_evidence"][0])
    mutated["artifact_sequence_index"] = freeze["artifact_sequence_index"]
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_ARTIFACT_SEQUENCE_MISMATCH" in errors


def test_parent_hash_mismatch_is_rejected(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence)
    mutated["parent_artifact_hash"] = "0" * 64
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_PARENT_ARTIFACT_HASH_MISMATCH" in errors


def test_sequence_inversion_is_rejected(repo_root):
    freeze, preconditions, _plan, _evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(preconditions)
    mutated["artifact_sequence_index"] = freeze["artifact_sequence_index"]
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=freeze["freeze_hash"],
        expected_sequence=5,
    )
    assert "C1_BOUND_ARTIFACT_SEQUENCE_MISMATCH" in errors


def test_candidate_byte_hash_mismatch_is_rejected(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence["test_evidence"][0])
    mutated["candidate_file_sha256"] = "0" * 64
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_CANDIDATE_FILE_SHA256_MISMATCH" in errors


def test_candidate_canonical_hash_mismatch_is_rejected(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence["test_evidence"][0])
    mutated["canonical_candidate_hash"] = "0" * 64
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_CANONICAL_CANDIDATE_HASH_MISMATCH" in errors


def test_candidate_freeze_hash_mismatch_is_rejected(repo_root):
    freeze, _preconditions, plan, evidence, _closure = _artifacts(repo_root)
    mutated = deepcopy(evidence["test_evidence"][0])
    mutated["candidate_freeze_hash"] = "0" * 64
    errors = validate_bound_artifact(
        mutated,
        freeze,
        expected_parent=plan["test_plan_hash"],
        expected_sequence=7,
    )
    assert "C1_BOUND_CANDIDATE_FREEZE_HASH_MISMATCH" in errors


def test_test_code_and_io_hashes_are_recorded(repo_root):
    evidence = _read(repo_root, TEST_EVIDENCE_PATH)
    expected_code_hash = "ece94f78f8fedb9429cedf392ae5ce0af02c85e57c4bee46329aaf198adbe069"
    for item in evidence["test_evidence"]:
        assert item["test_code_hash"] == expected_code_hash
        assert len(item["input_hash"]) == len(item["output_hash"]) == 64


def test_mutations_never_change_frozen_candidate(repo_root):
    freeze = _read(repo_root, FREEZE_PATH)
    build_test_evidence(repo_root)
    assert file_sha256(repo_root / CANDIDATE_PATH) == freeze["candidate_file_sha256"]


def test_closure_closes_prosecutor_and_r2a_final_findings(repo_root):
    closure = build_closure(repo_root)
    assert closure["result"] == "PASS"
    assert closure["unresolved_findings"] == []
    assert {item["finding_id"] for item in closure["closures"]} == set(FINDING_TESTS)
    assert closure["candidate_prosecutor_review"]["verdict_at_review"] == "FAIL"
    assert closure["candidate_prosecutor_review"]["serious_findings_closed"] is True


def test_historical_evidence_is_not_used_as_candidate_pass(repo_root):
    evidence = _read(repo_root, TEST_EVIDENCE_PATH)
    closure = _read(repo_root, CLOSURE_PATH)
    assert evidence["historical_evidence_used_as_candidate_pass"] is False
    assert closure["historical_evidence_used_as_candidate_pass"] is False


def test_frozen_candidate_write_mode_is_write_once(repo_root, tmp_path, monkeypatch):
    candidate_path = tmp_path / "candidate.json"
    freeze_path = tmp_path / "freeze.json"
    monkeypatch.setattr(freeze_module, "CANDIDATE_PATH", candidate_path)
    monkeypatch.setattr(freeze_module, "FREEZE_PATH", freeze_path)
    assert freeze_module.check_or_write_candidate_freeze(repo_root, check=False)["status"] == "PASS"
    frozen_bytes = candidate_path.read_bytes()
    original_builder = freeze_module.build_candidate

    def changed_candidate(root):
        value = original_builder(root)
        value["decision"] = "RETEST_REQUIRED"
        return value

    monkeypatch.setattr(freeze_module, "build_candidate", changed_candidate)
    result = freeze_module.check_or_write_candidate_freeze(repo_root, check=False)
    assert result["status"] == "FAIL"
    assert "C1_FROZEN_CANDIDATE_REWRITE_PROHIBITED" in result["errors"]
    assert candidate_path.read_bytes() == frozen_bytes


def test_byte_and_bundle_mutations_use_distinct_actual_bytes(repo_root):
    evidence = build_test_evidence(repo_root)
    by_id = {item["test_id"]: item for item in evidence["test_evidence"]}
    for test_id in ("C1-MUT-001", "C1-MUT-021"):
        observation = by_id[test_id]["input_observation"]
        assert (
            observation["original_candidate_bytes_sha256"]
            != observation["mutated_candidate_bytes_sha256"]
        )
        assert "C1_BOUND_CANDIDATE_FILE_SHA256_MISMATCH" in by_id[test_id]["actual_errors"]


def test_exact_candidate_bundle_recomputes_candidate_bytes(repo_root):
    freeze = _read(repo_root, FREEZE_PATH)
    candidate_bytes = (repo_root / CANDIDATE_PATH).read_bytes()
    bundle = {
        "candidate_id": freeze["candidate_id"],
        "candidate_file_sha256": freeze["candidate_file_sha256"],
        "canonical_candidate_hash": freeze["canonical_candidate_hash"],
        "candidate_freeze_hash": freeze["freeze_hash"],
    }
    assert validate_exact_candidate_bundle(bundle, candidate_bytes, freeze) == []
    assert "C1_FROZEN_CANDIDATE_BYTES_MISMATCH" in validate_exact_candidate_bundle(
        bundle, candidate_bytes + b"\n", freeze
    )


def test_mutation_declarations_match_executed_targets(repo_root):
    evidence = build_test_evidence(repo_root)
    by_id = {item["test_id"]: item for item in evidence["test_evidence"]}
    restriction_observation = by_id["C1-MUT-009"]["input_observation"]
    assert restriction_observation["mutated_field"] == "restrictions"
    assert (
        "FORMAL_INTEGRATION_ALLOWED"
        in restriction_observation["mutated_field_observation"]["value"]
    )
    report_observation = by_id["C1-MUT-022"]["input_observation"]
    assert report_observation["decision_source"] == "HARDCODED_ACCEPT"
    assert "C1_REPORT_DECISION_SOURCE_NOT_INPUT_DRIVEN" in by_id["C1-MUT-022"]["actual_errors"]


def test_report_projection_is_input_driven(repo_root):
    candidate = _read(repo_root, CANDIDATE_PATH)
    report = build_candidate_report_projection(candidate)
    assert validate_candidate_report_projection(report, candidate) == []
    report["decision"] = "AUTOMATED_REJECTED"
    assert "C1_REPORT_PROJECTION_MISMATCH" in validate_candidate_report_projection(
        report, candidate
    )


def test_rehashed_failed_precondition_is_rejected(repo_root):
    value = build_preconditions(repo_root)
    value["checks"][0]["status"] = "FAIL"
    value["passed_check_count"] -= 1
    value["failed_check_ids"] = [value["checks"][0]["check_id"]]
    value["all_required_pass"] = False
    value["preconditions_hash"] = sha256_json(
        {key: item for key, item in value.items() if key != "preconditions_hash"}
    )
    assert validate_precondition_semantics(value) == ["C1_PRECONDITIONS_SEMANTIC_FAILURE"]


def test_postfreeze_embargo_and_execution_observations_fail_closed():
    assert validate_postfreeze_observation([], [], {"prototype_executions": 0}) == []
    assert validate_postfreeze_observation(
        ["PROHIBITED_IMPLEMENTATION_DETECTED"], [], {"prototype_executions": 0}
    ) == ["C1_POSTFREEZE_EMBARGO_NOT_PASS"]
    assert validate_postfreeze_observation([], ["prototype.py"], {"prototype_executions": 0}) == [
        "C1_POSTFREEZE_EMBARGO_NOT_PASS"
    ]
    assert validate_postfreeze_observation([], [], {"prototype_executions": 1}) == [
        "C1_POSTFREEZE_EMBARGO_NOT_PASS"
    ]


def test_preconditions_recompute_postfreeze_embargo(repo_root, monkeypatch):
    monkeypatch.setattr(
        evidence_module,
        "verify_embargo",
        lambda _root: ["PROHIBITED_IMPLEMENTATION_DETECTED:synthetic.py"],
    )
    value = build_preconditions(repo_root)
    assert value["all_required_pass"] is False
    assert "C1-PRE-012" in value["failed_check_ids"]


def test_closure_claim_substitution_is_rejected(repo_root):
    closure = build_closure(repo_root)
    assert validate_closure_claims(closure) == []
    closure["closures"][0]["test_ids"] = ["C1-MUT-UNRELATED"]
    assert "C1_CLOSURE_REQUIRED_EVIDENCE_MISMATCH" in validate_closure_claims(closure)


def test_state_projection_requires_exact_binding_and_r3_only(repo_root):
    candidate = _read(repo_root, CANDIDATE_PATH)
    freeze = _read(repo_root, FREEZE_PATH)
    state = build_candidate_state_projection(candidate, freeze)
    assert validate_candidate_state_projection(state, candidate, freeze) == []
    state["candidate_file_sha256"] = "0" * 64
    state["next_phase_allowed"] = "PHASE-003"
    errors = validate_candidate_state_projection(state, candidate, freeze)
    assert "C1_BOUND_CANDIDATE_FILE_SHA256_MISMATCH" in errors
    assert "C1_STATE_ROUTE_INVALID" in errors


def test_post_evidence_prosecutor_output_is_bound_and_preserved(repo_root):
    value = _read(repo_root, POST_EVIDENCE_PROSECUTOR_PATH)
    freeze = _read(repo_root, FREEZE_PATH)
    assert value["verdict"] == "FAIL"
    assert value["candidate_file_sha256"] == freeze["candidate_file_sha256"]
    assert value["canonical_candidate_hash"] == freeze["canonical_candidate_hash"]
    assert value["candidate_freeze_hash"] == freeze["freeze_hash"]
    body = dict(value)
    recorded = body.pop("output_hash")
    assert recorded == sha256_json(body)
