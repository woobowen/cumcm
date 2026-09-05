from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def skill_root(repo_root: Path) -> Path:
    return repo_root / ".agents/skills/cumcm-modeling-evidence"


@pytest.fixture
def case_cli(skill_root: Path):
    path = skill_root / "scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("cumcm_case_output_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_output(status: str = "SUCCESS") -> dict:
    value = {
        "candidate_id": "GENERIC-CANDIDATE",
        "status": status,
        "final_metrics": {"primary_loss": 0.25},
        "claim_scope": "Evidence is limited to the bound inputs and registered split.",
        "requirement_claims": {
            "REQ-N-1": {
                "claim_id": "CLAIM-N-1",
                "claim_text": "The primary quantity was computed from bound inputs.",
                "evidence_artifact_ids": ["runs/RUN-GENERIC/output.json"],
            },
            "REQ-N-2": {
                "claim_id": "CLAIM-N-2",
                "claim_text": "The result includes a bounded perturbation check.",
                "evidence_artifact_ids": ["runs/RUN-GENERIC/output.json"],
            },
        },
        "figure_ready_data": [{"figure_id": "GENERIC-FIGURE", "series": [0.25]}],
        "uncertainty": {"scope": "registered perturbations", "quantified": True},
        "limitations": ["No external-validity claim is made."],
        "robustness_evidence": {
            "metric": "primary_loss",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "GENERIC-SHIFT",
                    "metric": "primary_loss",
                    "result": 0.3,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["A structural shift can invalidate the estimate."],
        },
    }
    if status == "CONTRACT_PROBE":
        value.update(
            {
                "probe_only": True,
                "ranking_eligible": False,
                "result_values_are_placeholders": True,
            }
        )
    return value


def test_generic_prediction_and_optimization_shapes_pass_same_contract(case_cli) -> None:
    prediction = valid_output()
    optimization = valid_output()
    optimization["final_metrics"] = {"objective": 12.0, "constraint_residual": 0.0}
    optimization["figure_ready_data"] = [{"table_id": "GENERIC-PLAN", "rows": [1]}]
    for value in (prediction, optimization):
        before = copy.deepcopy(value)
        result = case_cli.validate_selected_output_contract(
            value,
            expected_candidate_id="GENERIC-CANDIDATE",
            required_requirement_ids=["REQ-N-1", "REQ-N-2"],
        )
        assert result.accepted is True
        assert value == before


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda value: value.pop("final_metrics"), "RC_OUTPUT_CONTRACT_REQUIRED_FIELDS_MISSING"),
        (
            lambda value: value.update(final_metrics={"primary_loss": math.nan}),
            "RC_OUTPUT_CONTRACT_NONFINITE_OR_NONJSON",
        ),
        (
            lambda value: value.update(requirement_claims={}),
            "RC_OUTPUT_CONTRACT_REQUIREMENT_CLAIMS_INVALID",
        ),
        (
            lambda value: value["robustness_evidence"].update(perturbations=[]),
            "RC_OUTPUT_CONTRACT_ROBUSTNESS_INVALID",
        ),
        (
            lambda value: value.update(figure_ready_data=[]),
            "RC_OUTPUT_CONTRACT_FIGURE_DATA_INVALID",
        ),
        (
            lambda value: value.update(uncertainty={}),
            "RC_OUTPUT_CONTRACT_UNCERTAINTY_INVALID",
        ),
        (
            lambda value: value.update(limitations=[]),
            "RC_OUTPUT_CONTRACT_LIMITATIONS_INVALID",
        ),
    ],
)
def test_output_contract_failures_block_without_mutation(case_cli, mutation, reason: str) -> None:
    value = valid_output()
    mutation(value)
    before = copy.deepcopy(value)
    result = case_cli.validate_selected_output_contract(
        value,
        required_requirement_ids=["REQ-N-1", "REQ-N-2"],
    )
    assert result.accepted is False
    assert reason in result.reason_codes
    assert value == before


def test_probe_identity_is_mandatory_and_probe_is_not_a_success_result(case_cli) -> None:
    probe = valid_output("CONTRACT_PROBE")
    accepted = case_cli.validate_selected_output_contract(
        probe,
        required_requirement_ids=["REQ-N-1", "REQ-N-2"],
        allow_probe=True,
    )
    assert accepted.accepted is True
    assert not case_cli.validate_selected_output_contract(
        probe,
        required_requirement_ids=["REQ-N-1", "REQ-N-2"],
    ).accepted
    del probe["ranking_eligible"]
    rejected = case_cli.validate_selected_output_contract(
        probe,
        required_requirement_ids=["REQ-N-1", "REQ-N-2"],
        allow_probe=True,
    )
    assert rejected.reason_codes == ("RC_OUTPUT_CONTRACT_PROBE_IDENTITY_INVALID",)


def test_preflight_cli_is_read_only_and_restricted_to_models_proposed(
    case_cli, skill_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case_root = tmp_path / "case"
    case_cli.initialize_case(case_root, "GENERIC-PREFLIGHT-001", "prediction")
    raw_path = case_root / "data/raw/generic.json"
    case_cli.write_json(raw_path, [{"x": 1}], overwrite=False)

    def accepted(key: str, content: dict) -> None:
        case_cli.write_json(
            case_root / case_cli.ARTIFACT_PATHS[key],
            case_cli.artifact(key, content),
        )

    accepted(
        "problem_requirements",
        {
            "contract_version": "requirement-evidence/v1",
            "case_id": "GENERIC-PREFLIGHT-001",
            "requirements": [
                {
                    "requirement_id": requirement_id,
                    "text": text,
                    "role": "PRIMARY",
                    "required_evidence_classes": ["PROVIDED_EMPIRICAL"],
                    "allowed_evidence_classes": ["PROVIDED_EMPIRICAL"],
                    "minimum_data_fields": ["x"],
                    "required_time_scope": ["SCOPE"],
                    "required_entity_scope": ["ENTITY"],
                    "external_data_allowed": False,
                    "external_data_required": False,
                    "simulation_substitution_allowed": False,
                    "partial_completion_allowed": False,
                    "dependency_requirements": [],
                    "completion_rule": "ALL_REQUIRED_EVIDENCE",
                }
                for requirement_id, text in (
                    ("REQ-N-1", "estimate"),
                    ("REQ-N-2", "stress"),
                )
            ],
        },
    )
    case_cli.advance_once(case_root)
    case_cli.advance_once(case_root)
    accepted("research_plan", {"mode": "FIRST_RUN", "external_search": False})
    accepted(
        "source_ledger",
        {
            "contract_version": "requirement-evidence/v1",
            "sources": [
                {
                    "source_id": "SRC-N-1",
                    "supports_requirement_ids": ["REQ-N-1", "REQ-N-2"],
                    "evidence_class": "PROVIDED_EMPIRICAL",
                    "provenance": "FIRST_PARTY_FIXTURE",
                    "authority": "TEST_OWNER",
                    "retrieval_time": "FROZEN",
                    "license_or_usage_status": "ALLOWED",
                    "geographic_scope": [],
                    "time_scope": ["SCOPE"],
                    "entity_scope": ["ENTITY"],
                    "field_schema": ["x"],
                    "hash": case_cli.file_hash(raw_path),
                    "freshness": "CURRENT_FOR_SCOPE",
                    "limitations": [],
                }
            ],
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    case_cli.advance_once(case_root)
    accepted("assumptions_and_symbols", {"assumptions": ["bounded"]})
    accepted(
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": {"data/raw/generic.json": case_cli.file_hash(raw_path)},
        },
    )
    case_cli.advance_once(case_root)
    accepted(
        "model_candidates",
        {
            "candidates": [
                {"candidate_id": "GENERIC-BASELINE", "baseline": True},
                {"candidate_id": "GENERIC-CANDIDATE", "baseline": False},
            ]
        },
    )
    accepted(
        "data_sufficiency",
        {
            "contract_version": "data-sufficiency/v1",
            "requirements": case_cli.read_artifact(case_root, "problem_requirements")["content"][
                "requirements"
            ],
            "sources": case_cli.read_artifact(case_root, "source_ledger")["content"]["sources"],
            "acquisition_plans": [],
            "aggregate_completion_claimed": False,
            "requirement_assessments": [
                {
                    "requirement_id": requirement_id,
                    "data_sufficiency_status": "SUFFICIENT",
                    "missing_fields": [],
                    "missing_entities": [],
                    "missing_time_scope": [],
                    "candidate_sources": ["SRC-N-1"],
                    "acquisition_cost": "NONE",
                    "acquisition_time": "NONE",
                    "allowed_substitutions": [],
                    "forbidden_substitutions": ["SIMULATION"],
                    "affected_downstream_stages": [],
                }
                for requirement_id in ("REQ-N-1", "REQ-N-2")
            ],
        },
    )
    case_cli.advance_once(case_root)
    requirements = case_cli.read_artifact(case_root, "problem_requirements")["content"][
        "requirements"
    ]
    probe = valid_output("CONTRACT_PROBE")
    probe["requirement_claims"] = {
        item["requirement_id"]: {
            "claim_id": f"CLAIM-PROBE-{index}",
            "claim_text": "Generic placeholder claim.",
            "evidence_artifact_ids": ["experiments/selected_output_contract_probe.json"],
        }
        for index, item in enumerate(requirements, start=1)
    }
    probe_path = case_root / "experiments/selected_output_contract_probe.json"
    case_cli.write_json(probe_path, probe, overwrite=False)
    before_state = hashlib.sha256((case_root / "case_state.json").read_bytes()).hexdigest()
    before_runs = sorted((case_root / "runs").iterdir())
    completed = subprocess.run(
        [
            sys.executable,
            str(skill_root / "scripts/cumcm_case.py"),
            "preflight-output",
            "--case-root",
            str(case_root),
            "--path",
            "experiments/selected_output_contract_probe.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["accepted"] is True
    assert result["result_recorded"] is False
    assert hashlib.sha256((case_root / "case_state.json").read_bytes()).hexdigest() == before_state
    assert sorted((case_root / "runs").iterdir()) == before_runs
    blocked_path = probe_path.with_name("blocked_probe.json")
    blocked_probe = copy.deepcopy(probe)
    blocked_probe["uncertainty"] = {}
    case_cli.write_json(blocked_path, blocked_probe, overwrite=False)
    blocked_result, _ = case_cli.preflight_output_contract(case_root, blocked_path)
    assert blocked_result.reason_codes == ("RC_OUTPUT_CONTRACT_UNCERTAINTY_INVALID",)
    accepted("experiment_plan", {"preregistered": True, "execution_prepared": True})
    monkeypatch.setattr(case_cli, "trusted_freezes", lambda root: {})
    state = case_cli.advance_once(case_root)
    relative = "experiments/selected_output_contract_probe.json"
    assert state["state"] == "EXPERIMENT_PLAN_VALIDATED"
    assert state["evidence_bindings"][relative] == case_cli.file_hash(probe_path)
