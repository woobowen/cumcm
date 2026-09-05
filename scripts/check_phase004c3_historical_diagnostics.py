#!/usr/bin/env python3
"""Read-only RC6 diagnostics over frozen 2019/2024 Validation evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
CASE_2019 = ROOT / "evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002"
CASE_2024 = ROOT / "evals/results/phase-004c-c-validation"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"NON_OBJECT:{path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_core():
    spec = importlib.util.spec_from_file_location("phase004c3_diagnostic_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise ValueError("RC6_CORE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def nested_priority_count(value: Any) -> int | None:
    if isinstance(value, dict):
        if "priority_dispatch_count" in value:
            count = value["priority_dispatch_count"]
            return count if isinstance(count, int) and not isinstance(count, bool) else None
        for item in value.values():
            found = nested_priority_count(item)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = nested_priority_count(item)
            if found is not None:
                return found
    return None


def evaluate() -> dict[str, Any]:
    core = load_core()
    decision_2019_path = CASE_2019 / "validation/DECISION-C-TARGET-VALIDATION-004C2.json"
    audit_2019_path = CASE_2019 / "data/data_audit.json"
    selected_output_path = CASE_2019 / "runs/RUN-BASELINE_STATIC_FCFS-101/output.json"
    decision_2019 = load_json(decision_2019_path)
    audit_2019 = load_json(audit_2019_path)["content"]
    selected_output = load_json(selected_output_path)
    priority_count = nested_priority_count(selected_output.get("question_4"))

    empirical_preflight = core.evaluate_data_sufficiency(
        {
            "requirements": [
                {
                    "requirement_id": "REQ-Q2",
                    "role": "PRIMARY",
                    "required_evidence_classes": [
                        "PROVIDED_EMPIRICAL",
                        "ACQUIRED_EMPIRICAL",
                    ],
                    "allowed_evidence_classes": [
                        "PROVIDED_EMPIRICAL",
                        "ACQUIRED_EMPIRICAL",
                    ],
                    "minimum_data_fields": ["observations"],
                    "required_time_scope": ["OBSERVATION_PERIOD"],
                    "required_entity_scope": ["NAMED_ENTITY"],
                    "external_data_allowed": True,
                    "external_data_required": True,
                    "simulation_substitution_allowed": False,
                    "partial_completion_allowed": True,
                    "dependency_requirements": ["REQ-Q1"],
                    "completion_rule": "ALL_REQUIRED_EVIDENCE",
                }
            ],
            "sources": [
                {
                    "source_id": "FROZEN-SCENARIO-ASSUMPTIONS",
                    "supports_requirement_ids": ["REQ-Q2"],
                    "evidence_class": "SIMULATION",
                    "provenance": "PROSPECTIVE_MODEL_ASSUMPTIONS",
                    "authority": "FROZEN_CASE_ARTIFACT",
                    "retrieval_time": "FROZEN_BEFORE_RUN",
                    "license_or_usage_status": "ALLOWED",
                    "geographic_scope": [],
                    "time_scope": ["OBSERVATION_PERIOD"],
                    "entity_scope": ["NAMED_ENTITY"],
                    "field_schema": ["observations"],
                    "hash": audit_2019["processed_data_hashes"][
                        "experiments/scenario_assumptions.json"
                    ],
                    "freshness": "CURRENT_FOR_FROZEN_SCENARIO",
                    "limitations": ["Not empirical observations."],
                }
            ],
            "acquisition_plans": [],
            "aggregate_completion_claimed": False,
        }
    )
    policy_semantic = core.validate_semantic_claim_support(
        {
            "claim": {
                "claim_id": "CLAIM-2019C-Q4",
                "requirement_id": "REQ-Q4",
                "claim_type": "POLICY_EVALUATION",
                "statement": "Frozen bounded policy-evaluation statement.",
                "scope": {"fields": [], "time": [], "entities": []},
                "evidence_class": "SIMULATION",
                "selected_run_ids": ["RUN-BASELINE_STATIC_FCFS-101"],
                "selected_output_ids": ["OUT-Q4"],
                "metric_ids": ["income_rate_gini"],
                "comparator_ids": ["CMP-FROZEN-CONTROL"],
                "support_predicates": {
                    "policy_executed": False,
                    "policy_exposure_positive": False,
                    "comparator_present": True,
                    "benefit_recorded": True,
                    "cost_recorded": True,
                    "scope_bounded": True,
                },
                "uncertainty": {"status": "BOUNDED"},
                "counter_evidence": [],
                "limitations": ["Frozen selected baseline has zero priority exposure."],
                "claim_strength": "BOUNDED",
                "status": "SUPPORTED",
            },
            "runs": [
                {
                    "run_id": "RUN-BASELINE_STATIC_FCFS-101",
                    "outcome": "SUCCESS",
                    "sealed": True,
                    "current": True,
                    "supported_requirement_ids": ["REQ-Q4"],
                    "selected_output_ids": ["OUT-Q4"],
                    "metric_ids": ["income_rate_gini"],
                    "input_hash": "a" * 64,
                    "scenario_hash": "a" * 64,
                    "policy_exposure": priority_count,
                }
            ],
            "outputs": [{"output_id": "OUT-Q4", "metric_ids": ["income_rate_gini"]}],
            "comparators": [
                {"comparator_id": "CMP-FROZEN-CONTROL", "metric_ids": ["income_rate_gini"]}
            ],
            "validation": {},
        }
    )

    decision_2024_path = CASE_2024 / "DECISION-C-TARGET-VALIDATION-004C.json"
    terminal_2024_path = CASE_2024 / "terminal_validation_freeze.json"
    decision_2024 = load_json(decision_2024_path)
    terminal_2024 = load_json(terminal_2024_path)
    selected_2024 = terminal_2024["models_and_selection"]
    requirement_ids_2024 = terminal_2024["requirement_result"]["requirement_ids"]
    bounded_2024 = core.validate_semantic_claim_support(
        {
            "claim": {
                "claim_id": "CLAIM-2024C-BOUNDED-DIAGNOSTIC",
                "requirement_id": requirement_ids_2024[0],
                "claim_type": "DESCRIPTIVE",
                "statement": "Frozen selected output has bounded captured results.",
                "scope": {"fields": [], "time": [], "entities": []},
                "evidence_class": "PROVIDED_EMPIRICAL",
                "selected_run_ids": [selected_2024["selected_run_id"]],
                "selected_output_ids": ["OUT-FROZEN-SELECTED"],
                "metric_ids": [selected_2024["metric"]],
                "comparator_ids": [],
                "support_predicates": {"scope_bounded": True},
                "uncertainty": {"status": "BOUNDED"},
                "counter_evidence": [],
                "limitations": ["Diagnostic replay does not change the frozen verdict."],
                "claim_strength": "BOUNDED",
                "status": "SUPPORTED",
            },
            "runs": [
                {
                    "run_id": selected_2024["selected_run_id"],
                    "outcome": "SUCCESS",
                    "sealed": True,
                    "current": True,
                    "supported_requirement_ids": requirement_ids_2024,
                    "selected_output_ids": ["OUT-FROZEN-SELECTED"],
                    "metric_ids": [selected_2024["metric"]],
                    "input_hash": "b" * 64,
                    "scenario_hash": "b" * 64,
                    "policy_exposure": 1,
                }
            ],
            "outputs": [
                {"output_id": "OUT-FROZEN-SELECTED", "metric_ids": [selected_2024["metric"]]}
            ],
            "comparators": [],
            "validation": {"counter_evidence_detected": False},
        }
    )
    legacy_2024 = core.validate_evidence_compatibility(
        {
            "kind": "MULTI_REQUIREMENT_CLAIM_V2",
            "legacy_contract_version": "claim-evidence/v2",
            "requirement_ids": requirement_ids_2024,
            "run_outcomes": [item["outcome"] for item in terminal_2024["run_records"]],
            "handoff_status": "COMPLETE",
            "ordered_claim_ids": requirement_ids_2024,
            "permuted_claim_ids": list(reversed(requirement_ids_2024)),
        }
    )

    checks = {
        "2019_old_verdict_preserved": decision_2019.get("status")
        == "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT",
        "2019_empirical_gap_is_pre_execution_block": empirical_preflight
        == {
            "status": "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            "reason_codes": ["RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM"],
        },
        "2019_selected_policy_exposure_is_zero": priority_count == 0,
        "2019_policy_claim_rejected": policy_semantic
        == {
            "status": "BLOCK",
            "reason_codes": ["RC_POLICY_CLAIM_NO_POLICY_EXPOSURE"],
        },
        "2024_old_verdict_preserved": decision_2024.get("status")
        == "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT",
        "2024_bounded_semantic_view_passes": bounded_2024 == {"status": "PASS", "reason_codes": []},
        "2024_v2_compatibility_passes": legacy_2024 == {"status": "PASS", "reason_codes": []},
        "no_historical_workspace_write": True,
        "no_new_model_run": True,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "1.0.0",
        "diagnostic_id": "PHASE-004C3-RC6-HISTORICAL-DIAGNOSTIC-001",
        "status": "PASS" if not failed else "BLOCK",
        "classification": "READ_ONLY_DERIVED_NO_VALIDATION_CREDIT",
        "checks": checks,
        "failed_checks": failed,
        "diagnostics": {
            "2019_data_sufficiency": empirical_preflight,
            "2019_policy_claim": policy_semantic,
            "2019_priority_exposure": priority_count,
            "2024_bounded_claim": bounded_2024,
            "2024_legacy_compatibility": legacy_2024,
        },
        "source_hashes": {
            str(decision_2019_path.relative_to(ROOT)): sha256(decision_2019_path),
            str(audit_2019_path.relative_to(ROOT)): sha256(audit_2019_path),
            str(selected_output_path.relative_to(ROOT)): sha256(selected_output_path),
            str(decision_2024_path.relative_to(ROOT)): sha256(decision_2024_path),
            str(terminal_2024_path.relative_to(ROOT)): sha256(terminal_2024_path),
        },
        "historical_verdicts_changed": False,
        "historical_files_written": [],
        "new_model_runs": 0,
        "validation_credit": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args(argv)
    outcome = evaluate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0 if outcome["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
