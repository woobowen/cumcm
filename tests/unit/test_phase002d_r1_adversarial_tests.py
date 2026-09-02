from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware.adversarial_tests import build_test_records
from cumcm_skill_lab.failure_aware.models import read_json


def test_every_serious_finding_has_passed_test_evidence(repo_root):
    requests, evidence, closure = build_test_records(
        repo_root, recorded_at="2026-09-02T00:00:00+00:00"
    )
    assert len(requests["requests"]) == len(evidence["evidence"]) == 10
    assert closure["serious_finding_count"] == 10
    assert closure["closed_serious_finding_count"] == 10
    assert closure["all_serious_findings_closed"] is True


def test_generated_requests_and_evidence_reuse_existing_contracts(repo_root):
    requests, evidence, _ = build_test_records(repo_root, recorded_at="2026-09-02T00:00:00+00:00")
    request_schema = read_json(repo_root / "contracts/test_request.schema.json")
    evidence_schema = read_json(repo_root / "contracts/test_evidence.schema.json")
    request_validator = Draft202012Validator(request_schema)
    evidence_validator = Draft202012Validator(evidence_schema)
    assert all(not list(request_validator.iter_errors(item)) for item in requests["requests"])
    assert all(not list(evidence_validator.iter_errors(item)) for item in evidence["evidence"])
