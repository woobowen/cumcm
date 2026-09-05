#!/usr/bin/env python3
"""Reproduce Auditor 1 RC6 release blockers without mutating the Skill or a case."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
CONTROLLER_PATH = ROOT / "scripts/finalize_fresh_c_validation.py"
AUDITED_COMMIT = "bf82bf4b03fb0bbd55e7ed3d010cfb6ae1352a09"
HEX_A = "a" * 64
HEX_B = "b" * 64


def load_core():
    spec = importlib.util.spec_from_file_location("phase004c3_auditor1_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise ValueError("RC6_CORE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement(requirement_id: str = "R-A") -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "role": "PRIMARY",
        "required_evidence_classes": ["ACQUIRED_EMPIRICAL"],
        "allowed_evidence_classes": ["ACQUIRED_EMPIRICAL"],
        "minimum_data_fields": ["x"],
        "required_time_scope": ["T-A", "T-B"],
        "required_entity_scope": ["E-A"],
        "external_data_allowed": False,
        "external_data_required": False,
        "simulation_substitution_allowed": False,
        "partial_completion_allowed": False,
        "dependency_requirements": [],
        "completion_rule": "ALL_REQUIRED_EVIDENCE",
    }


def source(
    source_id: str = "S-A",
    *,
    fields: list[str] | None = None,
    times: list[str] | None = None,
    entities: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "supports_requirement_ids": ["R-A"],
        "evidence_class": "ACQUIRED_EMPIRICAL",
        "provenance": "REGISTERED_ORIGIN",
        "authority": "PRIMARY_PROVIDER",
        "retrieval_time": "T-RETRIEVED",
        "license_or_usage_status": "ALLOWED",
        "geographic_scope": ["G-A"],
        "time_scope": times if times is not None else ["T-A", "T-B"],
        "entity_scope": entities if entities is not None else ["E-A"],
        "field_schema": fields if fields is not None else ["x"],
        "hash": HEX_A,
        "freshness": "CURRENT_FOR_SCOPE",
        "limitations": [],
    }


def run(
    run_id: str,
    requirement_ids: list[str],
    output_ids: list[str],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "outcome": "SUCCESS",
        "sealed": True,
        "current": True,
        "supported_requirement_ids": requirement_ids,
        "selected_output_ids": output_ids,
        "metric_ids": ["M-A"],
        "input_hash": HEX_A,
        "scenario_hash": HEX_A,
        "policy_exposure": 1,
    }


def selection_payload(mode: str = "PER_REQUIREMENT") -> dict[str, Any]:
    return {
        "requirements": [
            {
                "requirement_id": "R-A",
                "selection_metric": "M-A",
                "selection_direction": "MIN",
                "dependency_requirements": [],
                "cross_requirement_constraints": [],
            },
            {
                "requirement_id": "R-B",
                "selection_metric": "M-A",
                "selection_direction": "MIN",
                "dependency_requirements": [],
                "cross_requirement_constraints": [],
            },
        ],
        "runs": [run("RUN-A", ["R-A"], ["OUT-A"]), run("RUN-B", ["R-B"], ["OUT-B"])],
        "selection": {
            "selection_mode": mode,
            "requirement_to_run_map": {"R-A": ["RUN-A"], "R-B": ["RUN-B"]},
            "requirement_to_output_map": {"R-A": ["OUT-A"], "R-B": ["OUT-B"]},
            "shared_input_hashes": [HEX_A],
            "shared_scenario_hashes": [HEX_A],
            "compatibility_checks": ["INPUT", "SCENARIO", "CONSTRAINTS"],
            "cross_requirement_constraints": [],
            "aggregate_objective": "DECLARED_TRADEOFF",
            "tradeoff_rule": "REQUIREMENT_LOCAL_METRICS",
            "limitations": [],
        },
    }


def semantic_payload() -> dict[str, Any]:
    return {
        "claim": {
            "claim_id": "C-A",
            "requirement_id": "R-A",
            "claim_type": "DESCRIPTIVE",
            "statement": "Bounded statement",
            "scope": {"fields": ["x"], "time": ["T-A"], "entities": ["E-A"]},
            "evidence_class": "PROVIDED_EMPIRICAL",
            "selected_run_ids": ["RUN-A"],
            "selected_output_ids": ["OUT-A"],
            "metric_ids": ["M-A"],
            "comparator_ids": [],
            "support_predicates": {"scope_bounded": True},
            "uncertainty": {"status": "BOUNDED"},
            "counter_evidence": [],
            "limitations": ["LIMIT-A"],
            "claim_strength": "BOUNDED",
            "status": "SUPPORTED",
        },
        "runs": [run("RUN-A", ["R-A"], ["OUT-A"])],
        "outputs": [{"output_id": "OUT-A", "metric_ids": ["M-A"]}],
        "comparators": [],
        "validation": {},
    }


def changed(value: dict[str, Any], mutator: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    mutator(result)
    return result


def probes(core) -> list[tuple[str, str, dict[str, Any], Callable[[Any], dict[str, Any]]]]:
    external_forbidden = {
        "requirements": [requirement()],
        "sources": [source()],
        "acquisition_plans": [],
        "aggregate_completion_claimed": False,
    }
    planned = requirement()
    planned["external_data_allowed"] = True
    planned["external_data_required"] = True
    incomplete_plan = {
        "requirements": [planned],
        "sources": [],
        "acquisition_plans": [{"requirement_id": "R-A", "status": "PLANNED"}],
        "aggregate_completion_claimed": False,
    }
    split_scope = {
        "requirements": [requirement()],
        "sources": [
            source("S-FIELD-TIME", entities=["E-B"]),
            source("S-ENTITY", fields=["y"], entities=["E-A"]),
        ],
        "acquisition_plans": [],
        "aggregate_completion_claimed": False,
    }

    dependent = selection_payload()
    dependent["requirements"][1]["dependency_requirements"] = ["R-A"]
    missing_hashes = selection_payload("JOINT_PORTFOLIO")
    for item in missing_hashes["runs"]:
        item.pop("input_hash")
        item.pop("scenario_hash")
    declared_hash_mismatch = selection_payload("JOINT_PORTFOLIO")
    declared_hash_mismatch["selection"]["shared_input_hashes"] = [HEX_B]
    declared_hash_mismatch["selection"]["shared_scenario_hashes"] = [HEX_B]

    bad_status = changed(
        semantic_payload(),
        lambda item: item["runs"][0].update(outcome="FAILED", sealed=False, current=False),
    )
    wrong_requirement = changed(
        semantic_payload(),
        lambda item: item["runs"][0].update(supported_requirement_ids=["R-B"]),
    )
    wrong_output_owner = changed(
        semantic_payload(),
        lambda item: item["runs"][0].update(selected_output_ids=["OUT-B"]),
    )
    missing_metric = changed(semantic_payload(), lambda item: item["claim"].update(metric_ids=[]))
    unbounded_scope = changed(
        semantic_payload(),
        lambda item: item["claim"].update(support_predicates={"scope_bounded": False}),
    )
    wrong_aggregate_claim = changed(
        semantic_payload(),
        lambda item: item.update(
            aggregate={
                "primary_requirement_ids": ["R-A"],
                "supported_requirement_ids": ["R-A"],
                "requirement_claim_ids": {"R-A": "C-WRONG"},
            }
        ),
    )
    invalid_compatibility = {
        "kind": "UNKNOWN_KIND",
        "legacy_contract_version": "claim-evidence/v999",
        "requirement_ids": ["R-A"],
        "run_outcomes": ["SUCCESS"],
        "handoff_status": "COMPLETE",
        "ordered_claim_ids": ["C-A", "C-B"],
        "permuted_claim_ids": ["C-A", "C-C"],
    }
    return [
        (
            "DATA_EXTERNAL_SOURCE_FORBIDDEN",
            "BLOCK",
            external_forbidden,
            core.evaluate_data_sufficiency,
        ),
        (
            "DATA_ACQUISITION_PLAN_INCOMPLETE",
            "BLOCK",
            incomplete_plan,
            core.evaluate_data_sufficiency,
        ),
        ("DATA_SCOPE_NOT_CONJUNCTIVE", "BLOCK", split_scope, core.evaluate_data_sufficiency),
        ("SELECTION_DEPENDENCY_SPLIT", "BLOCK", dependent, core.validate_requirement_selection),
        (
            "SELECTION_PORTFOLIO_HASHES_MISSING",
            "BLOCK",
            missing_hashes,
            core.validate_requirement_selection,
        ),
        (
            "SELECTION_DECLARED_HASH_MISMATCH",
            "BLOCK",
            declared_hash_mismatch,
            core.validate_requirement_selection,
        ),
        ("SEMANTIC_RUN_INELIGIBLE", "BLOCK", bad_status, core.validate_semantic_claim_support),
        (
            "SEMANTIC_WRONG_REQUIREMENT",
            "BLOCK",
            wrong_requirement,
            core.validate_semantic_claim_support,
        ),
        (
            "SEMANTIC_OUTPUT_NOT_OWNED",
            "BLOCK",
            wrong_output_owner,
            core.validate_semantic_claim_support,
        ),
        ("SEMANTIC_METRIC_MISSING", "BLOCK", missing_metric, core.validate_semantic_claim_support),
        (
            "SEMANTIC_SCOPE_UNBOUNDED",
            "BLOCK",
            unbounded_scope,
            core.validate_semantic_claim_support,
        ),
        (
            "SEMANTIC_AGGREGATE_WRONG_CLAIM",
            "BLOCK",
            wrong_aggregate_claim,
            core.validate_semantic_claim_support,
        ),
        (
            "COMPATIBILITY_UNKNOWN_AND_NONPERMUTATION",
            "BLOCK",
            invalid_compatibility,
            core.validate_evidence_compatibility,
        ),
    ]


def evaluate() -> dict[str, Any]:
    core = load_core()
    results = []
    for probe_id, expected_status, payload, evaluator in probes(core):
        actual = evaluator(payload)
        results.append(
            {
                "probe_id": probe_id,
                "payload_sha256": canonical_sha256(payload),
                "expected_safe_status": expected_status,
                "actual": actual,
                "defect_reproduced": actual.get("status") != expected_status,
            }
        )
    controller = CONTROLLER_PATH.read_text(encoding="utf-8")
    controller_checks = {
        "hardcoded_global_joint": '"selection_mode": "GLOBAL_JOINT"' in controller,
        "hardcoded_descriptive_claim": '"claim_type": "DESCRIPTIVE"' in controller,
        "hardcoded_provided_empirical": '"evidence_class": "PROVIDED_EMPIRICAL"' in controller,
        "hardcoded_positive_policy_exposure": '"policy_exposure": 1' in controller,
        "single_run_mapped_to_all_requirements": (
            "requirement_id: [run_id] for requirement_id in requirement_ids" in controller
        ),
    }
    all_reproduced = all(item["defect_reproduced"] for item in results) and all(
        controller_checks.values()
    )
    return {
        "schema_version": "1.0.0",
        "audit_id": "PHASE-004C3-AUDITOR-1-RC6-RELEASE-EVIDENCE-001",
        "audited_commit": AUDITED_COMMIT,
        "status": "PASS" if all_reproduced else "ERROR",
        "release_verdict": "BLOCK" if all_reproduced else "UNRESOLVED",
        "reason_codes": [
            "RC6_COMPATIBILITY_GATE_VACUOUS",
            "RC6_DATA_SUFFICIENCY_ACQUISITION_FAIL_OPEN",
            "RC6_PER_REQUIREMENT_PIPELINE_NOT_EFFECTIVE",
            "RC6_SELECTION_GATE_FAIL_OPEN_PORTFOLIO_BINDING",
            "RC6_SEMANTIC_GATE_FAIL_OPEN_BINDING",
        ],
        "probe_count": len(results),
        "reproduced_probe_count": sum(item["defect_reproduced"] for item in results),
        "probes": results,
        "controller_checks": controller_checks,
        "core_sha256": sha256(CORE_PATH),
        "controller_sha256": sha256(CONTROLLER_PATH),
        "formal_revision_cycles_used": 2,
        "formal_revision_cycles_remaining": 0,
        "third_cycle_permitted": False,
        "fresh_validation_input_accessed": False,
        "held_out_2025_accessed": False,
        "writes_performed_by_auditor": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args(argv)
    outcome = evaluate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0 if outcome["status"] == "PASS" and outcome["release_verdict"] == "BLOCK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
