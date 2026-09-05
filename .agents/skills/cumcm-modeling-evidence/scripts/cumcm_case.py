#!/usr/bin/env python3
"""离线、确定性的 CUMCM Competition RC case 编排器。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "0.2.0-competition-rc7"
CAPABILITY = "COMPETITION_RC"
ASSURANCE = "PUBLIC_DETERMINISTIC_AND_TWO_END_TO_END_SMOKES"
ARCHITECTURE = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
TRUSTED_EXECUTION_CODE_PATHS = (
    "scripts/cumcm_case.py",
    "scripts/synthetic_cases.py",
)

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_GATE = 3
EXIT_STALE = 4
EXIT_STATE = 5
EXIT_IO = 6

STAGES = (
    "PROBLEM_INTAKE",
    "REQUIREMENT_DECOMPOSITION",
    "RESEARCH_AND_SOURCE_PLANNING",
    "ASSUMPTION_AND_SYMBOL_DEFINITION",
    "DATA_AUDIT",
    "MODEL_PORTFOLIO_GENERATION",
    "BASELINE_DEFINITION",
    "EXPERIMENT_DESIGN",
    "IMPLEMENTATION_AND_EXECUTION",
    "MODEL_COMPARISON",
    "ROBUSTNESS_AND_SENSITIVITY",
    "FINAL_RUN",
    "CLAIM_EVIDENCE_VALIDATION",
    "MODELING_TO_PAPER_HANDOFF",
)

COMPONENT_IDS = {
    "accepted-versus-done-workflow-state",
    "claim-evidence-support-gate",
    "hash-bound-reproducibility-manifest",
    "leakage-safe-model-comparison-gate",
}

STATES = (
    "CREATED",
    "INTAKE_COMPLETE",
    "REQUIREMENTS_VALIDATED",
    "SOURCES_PLANNED",
    "DATA_AUDITED",
    "MODELS_PROPOSED",
    "EXPERIMENT_PLAN_VALIDATED",
    "RUNNING",
    "RUN_COMPLETED",
    "RUN_VALIDATED",
    "ROBUSTNESS_VALIDATED",
    "FINAL_CANDIDATE",
    "EVIDENCE_VALIDATED",
    "READY_FOR_PAPER_HANDOFF",
)
TERMINAL_STATES = {"STALE", "REJECTED"}

CASE_DIRS = (
    "problem",
    "research",
    "data/raw",
    "data/processed",
    "models",
    "experiments",
    "runs",
    "results",
    "evidence",
    "handoff",
    "state",
)

ARTIFACT_PATHS = {
    "problem_requirements": "problem/problem_requirements.json",
    "research_plan": "research/research_plan.json",
    "source_ledger": "research/source_ledger.json",
    "assumptions_and_symbols": "models/assumptions_and_symbols.json",
    "data_audit": "data/data_audit.json",
    "data_sufficiency": "data/data_sufficiency.json",
    "model_candidates": "models/model_candidates.json",
    "experiment_plan": "experiments/experiment_plan.json",
    "model_comparison": "results/model_comparison.json",
    "requirement_selection": "results/requirement_selection.json",
    "robustness_analysis": "results/robustness.json",
    "claim_evidence": "evidence/claim_evidence.json",
    "semantic_claim_support": "evidence/semantic_claim_support.json",
    "final_result": "results/final_result.json",
    "modeling_to_paper_handoff": "handoff/modeling_to_paper.json",
}

TEMPLATE_FILES = {
    **{key: f"{key}.json" for key in ARTIFACT_PATHS},
    "robustness_analysis": "robustness_analysis.json",
    "modeling_to_paper_handoff": "modeling_to_paper_handoff.json",
}

REQUIRED_HANDOFF_FIELDS = {
    "contract_version",
    "problem_requirements",
    "requirement_traceability",
    "data_dictionary",
    "data_quality_report",
    "assumptions",
    "symbols",
    "formulas",
    "sources",
    "selected_models",
    "final_runs",
    "final_metrics",
    "result_tables",
    "figure_ready_data",
    "validation_results",
    "robustness_results",
    "uncertainty",
    "failure_cases",
    "limitations",
    "claim_evidence",
    "reproduction",
    "generated_at",
    "approved_by",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
WINDOWS_ABS = re.compile(r"^[A-Za-z]:[\\/]")
CREDENTIAL_URL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/@\s]+:[^/@\s]+@")
ENV_PATH = re.compile(r"^(?:\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|%[A-Za-z_][A-Za-z0-9_]*%)")
SENSITIVE_KEYS = {
    "apikey",
    "accesstoken",
    "bearertoken",
    "browserstate",
    "clientsecret",
    "credential",
    "credentials",
    "hiddenreasoning",
    "password",
    "passwd",
    "privatekey",
    "privatepath",
    "rawtrace",
    "refreshtoken",
    "secret",
    "secretkey",
    "token",
}

STATE_FIELDS = {
    "schema_version",
    "case_id",
    "case_kind",
    "skill_version",
    "capability",
    "architecture",
    "state",
    "last_gate",
    "evidence_bindings",
    "history",
}

TRANSITION_GATES = {
    "CREATED": "INIT",
    "INTAKE_COMPLETE": "GATE_PROBLEM_INTAKE",
    "REQUIREMENTS_VALIDATED": "GATE_REQUIREMENT_COVERAGE",
    "SOURCES_PLANNED": "GATE_SOURCE_PLAN",
    "DATA_AUDITED": "GATE_ASSUMPTIONS_AND_DATA",
    "MODELS_PROPOSED": "GATE_MODEL_PORTFOLIO",
    "EXPERIMENT_PLAN_VALIDATED": "GATE_EXPERIMENT_PLAN",
    "RUNNING": "GATE_EXECUTION_AUTHORIZED",
    "RUN_COMPLETED": "GATE_RUN_COMPLETION",
    "RUN_VALIDATED": "GATE_REPRODUCIBILITY_MANIFEST",
    "ROBUSTNESS_VALIDATED": "GATE_COMPARISON_AND_ROBUSTNESS",
    "FINAL_CANDIDATE": "GATE_FINAL_RUN",
    "EVIDENCE_VALIDATED": "GATE_CLAIM_EVIDENCE",
    "READY_FOR_PAPER_HANDOFF": "GATE_MODELING_TO_PAPER",
}


@dataclass(frozen=True)
class GateResult:
    status: str
    reason_codes: tuple[str, ...]
    accepted: bool = False
    final: bool = False
    dependency_chain: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "status": self.status,
            "accepted": self.accepted,
            "final": self.final,
            "reason_codes": list(self.reason_codes),
        }
        if self.dependency_chain:
            value["dependency_chain"] = list(self.dependency_chain)
        return value


def passed(code: str) -> GateResult:
    return GateResult("PASS", (code,), accepted=True)


def blocked(*codes: str, status: str = "BLOCK") -> GateResult:
    return GateResult(status, tuple(sorted(set(codes))))


def contract_result(status: str, *reason_codes: str) -> dict[str, Any]:
    """Return the small, deterministic result shared by the RC6 pure gates."""
    return {"status": status, "reason_codes": sorted(set(reason_codes))}


EMPIRICAL_EVIDENCE_CLASSES = {
    "PROVIDED_EMPIRICAL",
    "ACQUIRED_EMPIRICAL",
    "DERIVED_EMPIRICAL",
}
EVIDENCE_CLASSES = EMPIRICAL_EVIDENCE_CLASSES | {
    "SIMULATION",
    "THEORETICAL",
    "ASSUMPTION",
    "EXPERT_JUDGMENT",
    "UNKNOWN",
}

ACQUISITION_PLAN_FIELDS = {
    "requirement_id",
    "required_fields",
    "required_time_scope",
    "required_entity_scope",
    "authoritative_source_candidates",
    "acquisition_method",
    "provenance_plan",
    "license_or_usage_plan",
    "validation_plan",
    "time_budget",
    "fallback_disposition",
}
SOURCE_COMPOSITION_FIELDS = {
    "composition_id",
    "source_ids",
    "join_keys",
    "join_cardinality",
    "entity_alignment",
    "time_alignment",
    "field_ownership",
    "deduplication_policy",
    "conflict_resolution",
    "provenance",
    "composition_hash",
}


def _string_set(value: Any) -> set[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return set(value)


def _source_provenance_complete(source: dict[str, Any]) -> bool:
    required_text = (
        "source_id",
        "provenance",
        "authority",
        "retrieval_time",
        "license_or_usage_status",
        "hash",
        "freshness",
    )
    return (
        all(isinstance(source.get(key), str) and source.get(key) for key in required_text)
        and source.get("license_or_usage_status") not in {"UNKNOWN", "PROHIBITED"}
        and HEX64.fullmatch(str(source.get("hash", ""))) is not None
        and all(
            _string_set(source.get(key)) is not None
            for key in ("geographic_scope", "time_scope", "entity_scope", "field_schema")
        )
        and isinstance(source.get("limitations"), list)
    )


def _complete_acquisition_plan(plan: Any, requirement: dict[str, Any]) -> bool:
    if not isinstance(plan, dict) or not set(plan) >= ACQUISITION_PLAN_FIELDS:
        return False
    list_fields = (
        "required_fields",
        "required_time_scope",
        "required_entity_scope",
        "authoritative_source_candidates",
    )
    text_fields = tuple(ACQUISITION_PLAN_FIELDS - set(list_fields) - {"requirement_id"})
    return (
        plan.get("requirement_id") == requirement.get("requirement_id")
        and all(
            _string_set(plan.get(field)) is not None and plan.get(field) for field in list_fields
        )
        and all(isinstance(plan.get(field), str) and plan.get(field) for field in text_fields)
        and set(plan["required_fields"]) == set(requirement.get("minimum_data_fields") or [])
        and set(plan["required_time_scope"]) == set(requirement.get("required_time_scope") or [])
        and set(plan["required_entity_scope"])
        == set(requirement.get("required_entity_scope") or [])
    )


def _validated_composition_sources(
    composition: Any,
    source_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]] | None:
    if not isinstance(composition, dict) or set(composition) != SOURCE_COMPOSITION_FIELDS:
        return None
    source_ids = composition.get("source_ids")
    body = {key: value for key, value in composition.items() if key != "composition_hash"}
    if (
        not isinstance(composition.get("composition_id"), str)
        or not composition["composition_id"]
        or _string_set(source_ids) is None
        or not source_ids
        or len(source_ids) != len(set(source_ids))
        or any(source_id not in source_index for source_id in source_ids)
        or _string_set(composition.get("join_keys")) is None
        or not composition.get("join_keys")
        or not isinstance(composition.get("field_ownership"), dict)
        or not composition.get("field_ownership")
        or any(
            not isinstance(composition.get(field), str) or not composition.get(field)
            for field in (
                "join_cardinality",
                "entity_alignment",
                "time_alignment",
                "deduplication_policy",
                "conflict_resolution",
                "provenance",
            )
        )
        or composition.get("entity_alignment") not in {"EXACT", "VERIFIED_CROSSWALK"}
        or composition.get("time_alignment") not in {"EXACT", "VERIFIED_RESAMPLING"}
        or not HEX64.fullmatch(str(composition.get("composition_hash", "")))
        or composition.get("composition_hash") != canonical_hash(body)
    ):
        return None
    return [source_index[source_id] for source_id in source_ids]


def validate_runtime_requirements(requirements: Any) -> dict[str, Any]:
    """Validate the explicit requirement/evidence contract used by completion."""
    if not isinstance(requirements, list) or not requirements:
        return contract_result("BLOCK", "RC_REQUIREMENT_CONTRACT_INVALID")
    identifiers: set[str] = set()
    codes: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            codes.add("RC_REQUIREMENT_CONTRACT_INVALID")
            continue
        requirement_id = requirement.get("requirement_id")
        required = _string_set(requirement.get("required_evidence_classes"))
        allowed = _string_set(requirement.get("allowed_evidence_classes"))
        if (
            not isinstance(requirement_id, str)
            or not requirement_id
            or requirement_id in identifiers
            or requirement.get("role", "PRIMARY") not in {"PRIMARY", "AUXILIARY"}
            or not required
            or allowed is None
            or not required <= allowed <= EVIDENCE_CLASSES
            or any(
                _string_set(requirement.get(field)) is None
                for field in (
                    "minimum_data_fields",
                    "required_time_scope",
                    "required_entity_scope",
                    "dependency_requirements",
                )
            )
            or any(
                not isinstance(requirement.get(field), bool)
                for field in (
                    "external_data_allowed",
                    "external_data_required",
                    "simulation_substitution_allowed",
                    "partial_completion_allowed",
                )
            )
            or not isinstance(requirement.get("completion_rule"), str)
            or not requirement.get("completion_rule")
        ):
            codes.add("RC_REQUIREMENT_CONTRACT_INVALID")
            continue
        identifiers.add(requirement_id)
    if identifiers:
        for requirement in requirements:
            dependencies = (
                requirement.get("dependency_requirements") if isinstance(requirement, dict) else []
            )
            if isinstance(dependencies, list) and set(dependencies) - identifiers:
                codes.add("RC_REQUIREMENT_DEPENDENCY_UNKNOWN")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def validate_runtime_sources(sources: Any, requirement_ids: Any) -> dict[str, Any]:
    """Reject unregistered, unknown, duplicate or provenance-incomplete sources."""
    if not isinstance(sources, list) or not isinstance(requirement_ids, list):
        return contract_result("BLOCK", "RC_SOURCE_EVIDENCE_REGISTRY_INVALID")
    known = set(requirement_ids)
    source_ids: set[str] = set()
    codes: set[str] = set()
    for source in sources:
        source_id = source.get("source_id") if isinstance(source, dict) else None
        supports = source.get("supports_requirement_ids") if isinstance(source, dict) else None
        if (
            not isinstance(source, dict)
            or not isinstance(source_id, str)
            or not source_id
            or source_id in source_ids
            or _string_set(supports) is None
            or set(supports) - known
            or source.get("evidence_class") not in EVIDENCE_CLASSES
        ):
            codes.add("RC_SOURCE_EVIDENCE_REGISTRY_INVALID")
            continue
        source_ids.add(source_id)
        if not _source_provenance_complete(source):
            codes.add("RC_DATA_PROVENANCE_INCOMPLETE")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def evaluate_data_sufficiency(payload: Any) -> dict[str, Any]:
    """Evaluate requirement-level data sufficiency before expensive modeling.

    This is intentionally a pure gate.  It distinguishes evidence class, source
    provenance and scope, and never promotes UNKNOWN or simulation evidence to
    empirical support.
    """
    original = copy.deepcopy(payload)
    if not isinstance(payload, dict):
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_INPUT_INVALID")
    requirements = payload.get("requirements")
    sources = payload.get("sources")
    plans = payload.get("acquisition_plans")
    if not isinstance(requirements, list) or not requirements or not isinstance(sources, list):
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_INPUT_INVALID")
    if not isinstance(plans, list):
        return contract_result("BLOCK", "RC_DATA_ACQUISITION_PLAN_INVALID")

    codes: set[str] = set()
    strict_runtime = "coverage_mode_by_requirement" in payload or "source_compositions" in payload
    coverage_modes = payload.get("coverage_mode_by_requirement")
    compositions = payload.get("source_compositions")
    if strict_runtime and (
        not isinstance(coverage_modes, dict) or not isinstance(compositions, list)
    ):
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_INPUT_INVALID")
    source_index = {
        item.get("source_id"): item
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    composition_index = {
        item.get("composition_id"): item
        for item in compositions or []
        if isinstance(item, dict) and isinstance(item.get("composition_id"), str)
    }
    requirement_ids: set[str] = set()
    incomplete: list[tuple[dict[str, Any], str]] = []
    acquisition_required = False
    for requirement in requirements:
        if not isinstance(requirement, dict):
            codes.add("RC_DATA_SUFFICIENCY_INPUT_INVALID")
            continue
        requirement_id = requirement.get("requirement_id")
        if (
            not isinstance(requirement_id, str)
            or not requirement_id
            or requirement_id in requirement_ids
        ):
            codes.add("RC_DATA_SUFFICIENCY_INPUT_INVALID")
            continue
        requirement_ids.add(requirement_id)
        if requirement.get("role", "PRIMARY") != "PRIMARY":
            continue
        required_classes = _string_set(requirement.get("required_evidence_classes"))
        allowed_classes = _string_set(requirement.get("allowed_evidence_classes"))
        required_fields = _string_set(requirement.get("minimum_data_fields"))
        required_time = _string_set(requirement.get("required_time_scope"))
        required_entities = _string_set(requirement.get("required_entity_scope"))
        if (
            not required_classes
            or allowed_classes is None
            or not required_classes <= EVIDENCE_CLASSES
            or not allowed_classes <= EVIDENCE_CLASSES
            or not required_classes <= allowed_classes
            or required_fields is None
            or required_time is None
            or required_entities is None
            or not isinstance(requirement.get("external_data_allowed"), bool)
            or not isinstance(requirement.get("external_data_required"), bool)
            or not isinstance(requirement.get("simulation_substitution_allowed"), bool)
            or not isinstance(requirement.get("partial_completion_allowed"), bool)
            or _string_set(requirement.get("dependency_requirements")) is None
            or not isinstance(requirement.get("completion_rule"), str)
            or not requirement.get("completion_rule")
        ):
            codes.add("RC_DATA_SUFFICIENCY_INPUT_INVALID")
            continue

        relevant = [
            item
            for item in sources
            if isinstance(item, dict)
            and requirement_id in (item.get("supports_requirement_ids") or [])
        ]
        if (
            strict_runtime
            and requirement.get("external_data_allowed") is False
            and any(item.get("evidence_class") == "ACQUIRED_EMPIRICAL" for item in relevant)
        ):
            codes.add("RC_EXTERNAL_DATA_POLICY_FORBIDDEN")
            incomplete.append((requirement, "EXTERNAL_DATA_FORBIDDEN"))
            continue
        matching_plans = [
            item
            for item in plans
            if isinstance(item, dict) and item.get("requirement_id") == requirement_id
        ]
        if (
            strict_runtime
            and requirement.get("external_data_required") is True
            and (
                len(matching_plans) != 1
                or not _complete_acquisition_plan(matching_plans[0], requirement)
            )
        ):
            codes.add("RC_DATA_ACQUISITION_PLAN_INCOMPLETE")
            incomplete.append((requirement, "PLAN_INCOMPLETE"))
            continue
        if any(not _source_provenance_complete(item) for item in relevant):
            codes.add("RC_DATA_PROVENANCE_INCOMPLETE")
            incomplete.append((requirement, "PROVENANCE"))
            continue

        class_matches = [
            item
            for item in relevant
            if item.get("evidence_class") in required_classes
            and item.get("evidence_class") in allowed_classes
        ]
        if not class_matches:
            observed_classes = {item.get("evidence_class") for item in relevant}
            empirical_required = bool(required_classes & EMPIRICAL_EVIDENCE_CLASSES)
            if empirical_required and "SIMULATION" in observed_classes:
                codes.add("RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM")
                incomplete.append((requirement, "EVIDENCE_CLASS"))
                continue
            if relevant:
                codes.add("RC_REQUIREMENT_EVIDENCE_CLASS_INSUFFICIENT")
                incomplete.append((requirement, "EVIDENCE_CLASS"))
                continue

            external = requirement.get("external_data_required") is True
            if external and not matching_plans:
                codes.add("RC_DATA_ACQUISITION_PLAN_MISSING")
                incomplete.append((requirement, "PLAN_MISSING"))
            elif external and any(item.get("status") == "PLANNED" for item in matching_plans):
                acquisition_required = True
                incomplete.append((requirement, "ACQUISITION"))
            else:
                codes.add("RC_REQUIREMENT_EMPIRICAL_DATA_MISSING")
                incomplete.append((requirement, "DATA_MISSING"))
            continue

        coverage_sources = class_matches
        if strict_runtime:
            coverage = coverage_modes.get(requirement_id)
            if not isinstance(coverage, dict):
                codes.add("RC_DATA_SOURCE_COMPOSITION_UNREGISTERED")
                incomplete.append((requirement, "COVERAGE_UNREGISTERED"))
                continue
            mode = coverage.get("mode")
            if mode == "SINGLE_SOURCE":
                source_id = coverage.get("source_id")
                selected_source = source_index.get(source_id)
                if selected_source not in class_matches:
                    codes.add("RC_DATA_SOURCE_COMPOSITION_UNREGISTERED")
                    incomplete.append((requirement, "COVERAGE_UNREGISTERED"))
                    continue
                coverage_sources = [selected_source]
            elif mode == "REGISTERED_COMPOSITION":
                composition = composition_index.get(coverage.get("composition_id"))
                selected_sources = _validated_composition_sources(composition, source_index)
                if selected_sources is None or any(
                    item not in class_matches for item in selected_sources
                ):
                    codes.add("RC_DATA_SOURCE_COMPOSITION_INVALID")
                    incomplete.append((requirement, "COMPOSITION_INVALID"))
                    continue
                ownership = composition.get("field_ownership")
                if set(ownership) != required_fields or any(
                    owner not in {item["source_id"] for item in selected_sources}
                    for owner in ownership.values()
                ):
                    codes.add("RC_DATA_SOURCE_COMPOSITION_INVALID")
                    incomplete.append((requirement, "COMPOSITION_INVALID"))
                    continue
                coverage_sources = selected_sources
            else:
                codes.add("RC_DATA_SOURCE_COMPOSITION_UNREGISTERED")
                incomplete.append((requirement, "COVERAGE_UNREGISTERED"))
                continue

        fields_ok = required_fields <= set().union(
            *(_string_set(item.get("field_schema")) or set() for item in coverage_sources)
        )
        time_ok = required_time <= set.intersection(
            *(_string_set(item.get("time_scope")) or set() for item in coverage_sources)
        )
        entities_ok = required_entities <= set.intersection(
            *(_string_set(item.get("entity_scope")) or set() for item in coverage_sources)
        )
        if not fields_ok:
            codes.add("RC_REQUIREMENT_MINIMUM_FIELDS_INSUFFICIENT")
        if not time_ok:
            codes.add("RC_REQUIREMENT_TIME_SCOPE_INSUFFICIENT")
        if not entities_ok:
            codes.add("RC_REQUIREMENT_ENTITY_SCOPE_INSUFFICIENT")
        if not (fields_ok and time_ok and entities_ok):
            incomplete.append((requirement, "SCOPE"))

    if payload != original:
        return contract_result("BLOCK", "RC_INPUT_MUTATION_DETECTED")
    hard_block = {
        "RC_DATA_SUFFICIENCY_INPUT_INVALID",
        "RC_DATA_PROVENANCE_INCOMPLETE",
        "RC_DATA_ACQUISITION_PLAN_INVALID",
        "RC_DATA_ACQUISITION_PLAN_MISSING",
        "RC_DATA_ACQUISITION_PLAN_INCOMPLETE",
        "RC_DATA_SOURCE_COMPOSITION_INVALID",
        "RC_DATA_SOURCE_COMPOSITION_UNREGISTERED",
        "RC_EXTERNAL_DATA_POLICY_FORBIDDEN",
    }
    if codes & hard_block:
        return contract_result("BLOCK", *codes)
    if not incomplete:
        return contract_result("SUFFICIENT")
    if payload.get("aggregate_completion_claimed") is True:
        return contract_result("BLOCK", "RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE")
    if acquisition_required and not (codes - {"RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE"}):
        return contract_result("ACQUISITION_REQUIRED")
    if any(item.get("partial_completion_allowed") is True for item, _ in incomplete) and len(
        incomplete
    ) < len(
        [
            item
            for item in requirements
            if isinstance(item, dict) and item.get("role", "PRIMARY") == "PRIMARY"
        ]
    ):
        return contract_result("PARTIAL", "RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE")
    return contract_result("UNSATISFIABLE_WITH_CURRENT_INPUTS", *codes)


def validate_requirement_selection(payload: Any) -> dict[str, Any]:
    """Validate global, per-requirement, or compatible portfolio selection."""
    original = copy.deepcopy(payload)
    if not isinstance(payload, dict):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    requirements = payload.get("requirements")
    runs = payload.get("runs")
    selection = payload.get("selection")
    if (
        not isinstance(requirements, list)
        or not requirements
        or not isinstance(runs, list)
        or not isinstance(selection, dict)
    ):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    mode = selection.get("selection_mode")
    if mode not in {"GLOBAL_JOINT", "PER_REQUIREMENT", "JOINT_PORTFOLIO"}:
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_MODE_INVALID")
    run_map = selection.get("requirement_to_run_map")
    output_map = selection.get("requirement_to_output_map")
    if not isinstance(run_map, dict) or not isinstance(output_map, dict):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    run_index = {
        item.get("run_id"): item
        for item in runs
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    codes: set[str] = set()
    selected_runs: list[dict[str, Any]] = []
    requirement_ids: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, dict) or not isinstance(
            requirement.get("requirement_id"), str
        ):
            codes.add("RC_REQUIREMENT_SELECTION_INPUT_INVALID")
            continue
        requirement_id = requirement["requirement_id"]
        requirement_ids.append(requirement_id)
        selected_run_ids = run_map.get(requirement_id)
        selected_output_ids = output_map.get(requirement_id)
        if not isinstance(selected_run_ids, list) or not selected_run_ids:
            codes.add("RC_REQUIREMENT_SELECTED_RUN_MISSING")
            continue
        if not isinstance(selected_output_ids, list) or not selected_output_ids:
            codes.add("RC_REQUIREMENT_SELECTED_OUTPUT_MISSING")
            continue
        requirement_runs = [run_index.get(run_id) for run_id in selected_run_ids]
        if any(item is None for item in requirement_runs):
            codes.add("RC_REQUIREMENT_SELECTED_RUN_MISSING")
            continue
        semantic_mismatch = any(
            isinstance(item, dict)
            and requirement_id not in (item.get("supported_requirement_ids") or [])
            for item in requirement_runs
        )
        for item in requirement_runs:
            assert isinstance(item, dict)
            selected_runs.append(item)
            if (
                item.get("outcome") != "SUCCESS"
                or item.get("sealed") is not True
                or item.get("current") is not True
            ):
                codes.add("RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS")
            if requirement_id not in (item.get("supported_requirement_ids") or []):
                codes.add("RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH")
            if (
                requirement.get("selection_metric") not in (item.get("metric_ids") or [])
                and not semantic_mismatch
            ):
                codes.add("RC_SELECTION_METRIC_REQUIREMENT_MISMATCH")
        if semantic_mismatch:
            continue
        available_outputs = {
            output_id
            for item in requirement_runs
            if isinstance(item, dict)
            for output_id in (item.get("selected_output_ids") or [])
        }
        if not set(selected_output_ids) <= available_outputs:
            codes.add("RC_REQUIREMENT_SELECTED_OUTPUT_MISSING")

    if mode == "GLOBAL_JOINT":
        global_run_ids = {
            run_id for ids in run_map.values() if isinstance(ids, list) for run_id in ids
        }
        if len(global_run_ids) != 1:
            codes.add("RC_GLOBAL_SELECTION_REQUIREMENT_COVERAGE_INSUFFICIENT")
        else:
            global_run = run_index.get(next(iter(global_run_ids)))
            expected_outputs = {
                output_id
                for ids in output_map.values()
                if isinstance(ids, list)
                for output_id in ids
            }
            if (
                not isinstance(global_run, dict)
                or not set(requirement_ids)
                <= set(global_run.get("supported_requirement_ids") or [])
                or not expected_outputs <= set(global_run.get("selected_output_ids") or [])
            ):
                codes.discard("RC_REQUIREMENT_SELECTED_OUTPUT_MISSING")
                codes.add("RC_GLOBAL_SELECTION_REQUIREMENT_COVERAGE_INSUFFICIENT")
    if mode == "JOINT_PORTFOLIO" and payload.get("contract_version") != "requirement-selection/v1":
        unique_runs = {item.get("run_id"): item for item in selected_runs}.values()
        input_hashes = {item.get("input_hash") for item in unique_runs}
        scenario_hashes = {item.get("scenario_hash") for item in unique_runs}
        constraints = selection.get("cross_requirement_constraints")
        conflict = not isinstance(constraints, list) or any(
            not isinstance(item, dict) or item.get("status") == "CONFLICT"
            for item in constraints or []
        )
        if len(input_hashes) != 1 or len(scenario_hashes) != 1 or conflict:
            codes.add("RC_PORTFOLIO_CROSS_REQUIREMENT_INCONSISTENT")
    if payload != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def validate_semantic_claim_support(payload: Any) -> dict[str, Any]:
    """Check bounded, machine-verifiable predicates for one semantic Claim."""
    original = copy.deepcopy(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("claim"), dict):
        return contract_result("BLOCK", "RC_SEMANTIC_CLAIM_INPUT_INVALID")
    claim = payload["claim"]
    runs = payload.get("runs")
    outputs = payload.get("outputs")
    comparators = payload.get("comparators")
    validation = payload.get("validation")
    if (
        not isinstance(runs, list)
        or not isinstance(outputs, list)
        or not isinstance(comparators, list)
        or not isinstance(validation, dict)
    ):
        return contract_result("BLOCK", "RC_SEMANTIC_CLAIM_INPUT_INVALID")
    codes: set[str] = set()
    claim_type = claim.get("claim_type")
    predicates = claim.get("support_predicates")
    if claim_type not in {
        "DESCRIPTIVE",
        "EMPIRICAL",
        "PREDICTIVE",
        "COMPARATIVE",
        "POLICY_EVALUATION",
        "FEASIBILITY",
        "OPTIMALITY",
        "CAUSAL",
        "SIMULATION_CONDITIONAL",
    } or not isinstance(predicates, dict):
        codes.add("RC_SEMANTIC_CLAIM_INPUT_INVALID")
        predicates = {}
    run_ids = claim.get("selected_run_ids")
    output_ids = claim.get("selected_output_ids")
    metric_ids = claim.get("metric_ids")
    run_index = {item.get("run_id"): item for item in runs if isinstance(item, dict)}
    output_index = {item.get("output_id"): item for item in outputs if isinstance(item, dict)}
    selected_runs = [run_index.get(item) for item in run_ids] if isinstance(run_ids, list) else []
    selected_outputs = (
        [output_index.get(item) for item in output_ids] if isinstance(output_ids, list) else []
    )
    if not selected_runs or any(item is None for item in selected_runs):
        codes.add("RC_REQUIREMENT_SELECTED_RUN_MISSING")
    if not selected_outputs or any(item is None for item in selected_outputs):
        codes.add("RC_REQUIREMENT_SELECTED_OUTPUT_MISSING")
    if isinstance(metric_ids, list) and any(
        not set(metric_ids) <= set(item.get("metric_ids") or [])
        for item in selected_outputs
        if isinstance(item, dict)
    ):
        codes.add("RC_CLAIM_METRIC_BINDING_MISMATCH")
    if claim_type == "EMPIRICAL" and claim.get("evidence_class") not in EMPIRICAL_EVIDENCE_CLASSES:
        codes.add("RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM")
    if (
        claim_type == "SIMULATION_CONDITIONAL"
        and predicates.get("registered_assumptions_bound") is not True
    ):
        codes.add("RC_SIMULATION_CONDITIONAL_ASSUMPTIONS_MISSING")
    comparator_ids = claim.get("comparator_ids")
    comparator_index = {
        item.get("comparator_id"): item for item in comparators if isinstance(item, dict)
    }
    if claim_type in {"COMPARATIVE", "POLICY_EVALUATION"} and (
        not isinstance(comparator_ids, list)
        or not comparator_ids
        or any(item not in comparator_index for item in comparator_ids)
    ):
        code = (
            "RC_POLICY_CLAIM_COMPARATOR_MISSING"
            if claim_type == "POLICY_EVALUATION"
            else "RC_COMPARATIVE_CLAIM_COMPARATOR_MISSING"
        )
        codes.add(code)
    if claim_type == "COMPARATIVE" and (
        predicates.get("comparable_inputs") is not True
        or predicates.get("common_metric") is not True
    ):
        codes.add("RC_COMPARATIVE_CLAIM_NOT_COMPARABLE")
    if claim_type == "POLICY_EVALUATION":
        if not selected_runs or any(
            not isinstance(item, dict)
            or not isinstance(item.get("policy_exposure"), (int, float))
            or isinstance(item.get("policy_exposure"), bool)
            or item.get("policy_exposure", 0) <= 0
            for item in selected_runs
        ):
            codes.add("RC_POLICY_CLAIM_NO_POLICY_EXPOSURE")
        if not all(
            predicates.get(key) is True for key in ("policy_executed", "policy_exposure_positive")
        ):
            codes.add("RC_POLICY_CLAIM_NO_POLICY_EXPOSURE")
        if not all(predicates.get(key) is True for key in ("benefit_recorded", "cost_recorded")):
            codes.add("RC_POLICY_CLAIM_BENEFIT_COST_MISSING")
    if (
        claim_type == "FEASIBILITY"
        and predicates.get("independent_constraint_recalculation") is not True
    ):
        codes.add("RC_FEASIBILITY_INDEPENDENT_RECALC_MISSING")
    if (
        claim_type == "OPTIMALITY"
        and claim.get("claim_strength") == "GLOBAL_OPTIMUM"
        and predicates.get("global_optimality_certificate") is not True
    ):
        codes.add("RC_OPTIMALITY_CERTIFICATE_MISSING")
    if claim_type == "CAUSAL" and predicates.get("causal_identification_design") is not True:
        codes.add("RC_CAUSAL_IDENTIFICATION_MISSING")
    if claim_type == "PREDICTIVE" and not all(
        predicates.get(key) is True for key in ("validation_boundary_frozen", "held_out_test_valid")
    ):
        codes.add("RC_PREDICTIVE_VALIDATION_MISSING")
    if validation.get("counter_evidence_detected") is True and not claim.get("counter_evidence"):
        codes.add("RC_CLAIM_COUNTER_EVIDENCE_UNRESOLVED")
    aggregate = payload.get("aggregate")
    if aggregate is not None and (
        not isinstance(aggregate, dict)
        or set(aggregate.get("primary_requirement_ids") or [])
        != set(aggregate.get("supported_requirement_ids") or [])
        or set((aggregate.get("requirement_claim_ids") or {}).keys())
        != set(aggregate.get("primary_requirement_ids") or [])
    ):
        codes.add("RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE")
    if (
        claim.get("status") != "SUPPORTED"
        or not isinstance(claim.get("limitations"), list)
        or not isinstance(claim.get("scope"), dict)
    ):
        codes.add("RC_SEMANTIC_CLAIM_INPUT_INVALID")
    if payload != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def validate_evidence_compatibility(payload: Any) -> dict[str, Any]:
    """Preserve deterministic RC4/RC5 artifact behavior under the RC6 gates."""
    original = copy.deepcopy(payload)
    if not isinstance(payload, dict):
        return contract_result("BLOCK", "RC_EVIDENCE_COMPATIBILITY_INPUT_INVALID")
    outcomes = payload.get("run_outcomes")
    if not isinstance(outcomes, list) or any(item != "SUCCESS" for item in outcomes):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS")
    if payload.get("handoff_status") == "PARTIAL":
        return contract_result("PARTIAL", "RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE")
    if payload.get("handoff_status") != "COMPLETE":
        return contract_result("BLOCK", "RC_EVIDENCE_COMPATIBILITY_INPUT_INVALID")
    if payload != original:
        return contract_result("BLOCK", "RC_INPUT_MUTATION_DETECTED")
    return contract_result("PASS")


RUNTIME_COMPATIBILITY_KINDS = {
    "RUN_PORTFOLIO_V1",
    "REQUIREMENT_ORDER_PERMUTATION_V1",
    "SINGLE_RUN_V1",
}
RUNTIME_COMPATIBILITY_VERSIONS = {"compatibility/v1"}


def validate_runtime_run_eligibility(
    selection_record: Any,
    semantic_record: Any,
    manifest_registry: Any,
) -> dict[str, Any]:
    """Bind selected run status to sealed manifests without inferring semantic coverage."""
    if (
        not isinstance(selection_record, dict)
        or not isinstance(semantic_record, dict)
        or not isinstance(manifest_registry, dict)
        or not manifest_registry
    ):
        return contract_result("BLOCK", "RC_ACTUAL_RUN_REGISTRY_MISSING")
    selection = selection_record.get("selection")
    if not isinstance(selection, dict) or not isinstance(
        selection.get("requirement_to_run_map"), dict
    ):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    selected_ids = {
        run_id
        for run_ids in selection["requirement_to_run_map"].values()
        if isinstance(run_ids, list)
        for run_id in run_ids
        if isinstance(run_id, str)
    }
    selection_runs = {
        item.get("run_id"): item
        for item in selection_record.get("runs", [])
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    semantic_runs = {
        item.get("run_id"): item
        for item in semantic_record.get("runs", [])
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    codes: set[str] = set()
    for run_id in selected_ids:
        manifest = manifest_registry.get(run_id)
        descriptors = (selection_runs.get(run_id), semantic_runs.get(run_id))
        if not isinstance(manifest, dict) or any(
            not isinstance(item, dict) for item in descriptors
        ):
            codes.add("RC_REQUIREMENT_SELECTED_RUN_MISSING")
            continue
        if (
            manifest.get("outcome") != "SUCCESS"
            or manifest.get("trusted_capture") is not True
            or manifest.get("supersession") is not None
            or any(
                item.get("outcome") != "SUCCESS"
                or item.get("sealed") is not True
                or item.get("current") is not True
                for item in descriptors
            )
        ):
            codes.add("RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def _valid_dependency_bridge(
    bridge: Any,
    *,
    dependency_id: str,
    dependent_id: str,
    upstream_run_ids: list[str],
    downstream_run_ids: list[str],
) -> bool:
    required = {
        "dependency_requirement_id",
        "dependent_requirement_id",
        "upstream_run_ids",
        "downstream_run_ids",
        "input_hash",
        "scenario_hash",
        "lineage_hash",
    }
    if not isinstance(bridge, dict) or set(bridge) != required:
        return False
    body = {key: value for key, value in bridge.items() if key != "lineage_hash"}
    return (
        bridge.get("dependency_requirement_id") == dependency_id
        and bridge.get("dependent_requirement_id") == dependent_id
        and bridge.get("upstream_run_ids") == upstream_run_ids
        and bridge.get("downstream_run_ids") == downstream_run_ids
        and HEX64.fullmatch(str(bridge.get("input_hash", ""))) is not None
        and HEX64.fullmatch(str(bridge.get("scenario_hash", ""))) is not None
        and bridge.get("lineage_hash") == canonical_hash(body)
    )


def validate_runtime_selection_compatibility(
    selection_record: Any,
    manifest_registry: Any,
    *,
    scenario_hash: Any,
) -> dict[str, Any]:
    """Validate selected portfolios against the actual sealed manifest registry."""
    if not isinstance(selection_record, dict) or not isinstance(manifest_registry, dict):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    requirements = selection_record.get("requirements")
    runs = selection_record.get("runs")
    selection = selection_record.get("selection")
    if (
        not isinstance(requirements, list)
        or not requirements
        or not isinstance(runs, list)
        or not isinstance(selection, dict)
        or not manifest_registry
    ):
        return contract_result("BLOCK", "RC_ACTUAL_RUN_REGISTRY_MISSING")
    mode = selection.get("selection_mode")
    if mode not in {"GLOBAL_JOINT", "PER_REQUIREMENT", "JOINT_PORTFOLIO"}:
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_MODE_INVALID")
    run_map = selection.get("requirement_to_run_map")
    output_map = selection.get("requirement_to_output_map")
    if not isinstance(run_map, dict) or not isinstance(output_map, dict):
        return contract_result("BLOCK", "RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    run_index = {
        item.get("run_id"): item
        for item in runs
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    selected_ids = {
        run_id
        for run_ids in run_map.values()
        if isinstance(run_ids, list)
        for run_id in run_ids
        if isinstance(run_id, str)
    }
    codes: set[str] = set()
    actual_input_hashes: set[str] = set()
    actual_scenario_hashes: set[str] = set()
    for run_id in selected_ids:
        declared = run_index.get(run_id)
        manifest = manifest_registry.get(run_id)
        if not isinstance(declared, dict) or not isinstance(manifest, dict):
            codes.add("RC_ACTUAL_RUN_REGISTRY_MISSING")
            continue
        declared_hashes = (
            declared.get("input_hash"),
            declared.get("scenario_hash"),
            declared.get("configuration_hash"),
        )
        if any(HEX64.fullmatch(str(item or "")) is None for item in declared_hashes):
            codes.add("RC_SELECTION_PORTFOLIO_HASHES_MISSING")
            continue
        manifest_scenario_hash = manifest.get("scenario_hash")
        if HEX64.fullmatch(str(manifest_scenario_hash or "")) is None:
            codes.add("RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND")
            continue
        actual_input_hashes.add(str(manifest.get("input_hash")))
        actual_scenario_hashes.add(str(manifest_scenario_hash))
        if (
            declared["input_hash"] != manifest.get("input_hash")
            or declared["scenario_hash"] != manifest_scenario_hash
            or declared["configuration_hash"] != manifest.get("configuration_hash")
        ):
            codes.add("RC_SELECTION_PORTFOLIO_HASH_MISMATCH")
        if manifest_scenario_hash != scenario_hash:
            codes.add("RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND")

    shared_inputs = selection.get("shared_input_hashes")
    shared_scenarios = selection.get("shared_scenario_hashes")
    if mode == "JOINT_PORTFOLIO":
        if (
            not isinstance(shared_inputs, list)
            or not shared_inputs
            or not isinstance(shared_scenarios, list)
            or not shared_scenarios
            or any(HEX64.fullmatch(str(item)) is None for item in shared_inputs + shared_scenarios)
        ):
            codes.add("RC_SELECTION_PORTFOLIO_HASHES_MISSING")
        elif (
            set(shared_inputs) != actual_input_hashes
            or set(shared_scenarios) != actual_scenario_hashes
        ):
            codes.add("RC_SELECTION_PORTFOLIO_HASH_MISMATCH")

    compatibility = selection.get("compatibility")
    if not isinstance(compatibility, dict):
        codes.add("RC_EVIDENCE_COMPATIBILITY_KIND_INVALID")
    else:
        ordered = compatibility.get("ordered_ids")
        permuted = compatibility.get("permuted_ids")
        if compatibility.get("kind") not in RUNTIME_COMPATIBILITY_KINDS:
            codes.add("RC_EVIDENCE_COMPATIBILITY_KIND_INVALID")
        if compatibility.get("version") not in RUNTIME_COMPATIBILITY_VERSIONS:
            codes.add("RC_EVIDENCE_COMPATIBILITY_VERSION_INVALID")
        if (
            not isinstance(ordered, list)
            or not isinstance(permuted, list)
            or len(ordered) != len(set(ordered))
            or len(permuted) != len(set(permuted))
            or set(ordered) != set(permuted)
        ):
            codes.add("RC_EVIDENCE_COMPATIBILITY_PERMUTATION_INVALID")

    bridges = selection.get("dependency_bridges")
    if not isinstance(bridges, list):
        codes.add("RC_SELECTION_DEPENDENCY_BRIDGE_MISSING")
        bridges = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        dependent_id = requirement.get("requirement_id")
        downstream_ids = run_map.get(dependent_id)
        for dependency_id in requirement.get("dependency_requirements") or []:
            upstream_ids = run_map.get(dependency_id)
            if (
                isinstance(upstream_ids, list)
                and isinstance(downstream_ids, list)
                and upstream_ids != downstream_ids
                and not any(
                    _valid_dependency_bridge(
                        bridge,
                        dependency_id=dependency_id,
                        dependent_id=dependent_id,
                        upstream_run_ids=upstream_ids,
                        downstream_run_ids=downstream_ids,
                    )
                    for bridge in bridges
                )
            ):
                codes.add("RC_SELECTION_DEPENDENCY_BRIDGE_MISSING")
    constraints = selection.get("cross_requirement_constraints")
    if not isinstance(constraints, list) or any(
        not isinstance(item, dict) or item.get("status") == "CONFLICT" for item in constraints or []
    ):
        codes.add("RC_PORTFOLIO_CROSS_REQUIREMENT_INCONSISTENT")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def validate_runtime_semantic_claims(
    record: Any,
    selection_record: Any,
    manifest_registry: Any,
    output_registry: Any,
    requirements: Any,
    sources: Any,
) -> dict[str, Any]:
    """Cross-bind semantic Claims to requirements, Runs, outputs, metrics and sources."""
    if not all(
        isinstance(item, expected)
        for item, expected in (
            (record, dict),
            (selection_record, dict),
            (manifest_registry, dict),
            (output_registry, dict),
            (requirements, list),
            (sources, list),
        )
    ):
        return contract_result("BLOCK", "RC_SEMANTIC_CLAIM_INPUT_INVALID")
    claims = record.get("claims")
    semantic_runs = {
        item.get("run_id"): item
        for item in record.get("runs", [])
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    outputs = {
        item.get("output_id"): item
        for item in record.get("outputs", [])
        if isinstance(item, dict) and isinstance(item.get("output_id"), str)
    }
    requirement_index = {
        item.get("requirement_id"): item
        for item in requirements
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    selection_requirements = {
        item.get("requirement_id"): item
        for item in selection_record.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    selection = selection_record.get("selection") or {}
    run_map = selection.get("requirement_to_run_map") or {}
    output_map = selection.get("requirement_to_output_map") or {}
    codes: set[str] = set()
    if not isinstance(claims, list) or not claims:
        return contract_result("BLOCK", "RC_SEMANTIC_CLAIM_BUNDLE_INVALID")
    for claim in claims:
        if not isinstance(claim, dict):
            codes.add("RC_SEMANTIC_CLAIM_INPUT_INVALID")
            continue
        requirement_id = claim.get("requirement_id")
        requirement = requirement_index.get(requirement_id)
        if not isinstance(requirement, dict):
            codes.add("RC_CLAIM_REQUIREMENT_UNKNOWN")
            continue
        run_ids = claim.get("selected_run_ids")
        output_ids = claim.get("selected_output_ids")
        metric_ids = claim.get("metric_ids")
        if run_ids != run_map.get(requirement_id):
            codes.add("RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH")
        if output_ids != output_map.get(requirement_id):
            codes.add("RC_REQUIREMENT_SELECTED_OUTPUT_NOT_OWNED")
        selected_runs = [semantic_runs.get(item) for item in run_ids or []]
        if not selected_runs or any(
            not isinstance(item, dict)
            or requirement_id not in (item.get("supported_requirement_ids") or [])
            for item in selected_runs
        ):
            codes.add("RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH")
        for output_id in output_ids or []:
            output = outputs.get(output_id)
            if (
                not isinstance(output, dict)
                or output.get("owner_run_id") not in (run_ids or [])
                or output.get("requirement_id") != requirement_id
            ):
                codes.add("RC_REQUIREMENT_SELECTED_OUTPUT_NOT_OWNED")
                continue
            run_output = output_registry.get(output.get("owner_run_id"))
            if not isinstance(run_output, dict) or requirement_id not in (
                run_output.get("requirement_claims") or {}
            ):
                codes.add("RC_REQUIREMENT_SELECTED_OUTPUT_NOT_OWNED")
        selection_metric = (selection_requirements.get(requirement_id) or {}).get(
            "selection_metric"
        )
        if (
            not isinstance(metric_ids, list)
            or not metric_ids
            or not isinstance(selection_metric, str)
            or selection_metric not in metric_ids
            or any(
                selection_metric not in (outputs.get(output_id) or {}).get("metric_ids", [])
                for output_id in output_ids or []
            )
            or any(
                selection_metric
                not in {
                    *(output_registry.get(run_id) or {}).get("validation_metrics", {}),
                    *(output_registry.get(run_id) or {}).get("final_metrics", {}),
                }
                for run_id in run_ids or []
            )
        ):
            codes.add("RC_CLAIM_METRIC_BINDING_MISSING")
        scope = claim.get("scope")
        if (
            not isinstance(scope, dict)
            or any(not _string_set(scope.get(key)) for key in ("fields", "time", "entities"))
            or (claim.get("support_predicates") or {}).get("scope_bounded") is not True
        ):
            codes.add("RC_CLAIM_SCOPE_UNBOUNDED")
        evidence_class = claim.get("evidence_class")
        if evidence_class not in (requirement.get("allowed_evidence_classes") or []) or not any(
            isinstance(source, dict)
            and requirement_id in (source.get("supports_requirement_ids") or [])
            and source.get("evidence_class") == evidence_class
            for source in sources
        ):
            codes.add("RC_CLAIM_EVIDENCE_CLASS_INVALID")
        outcome = validate_semantic_claim_support(
            {
                "claim": claim,
                "runs": record.get("runs"),
                "outputs": record.get("outputs"),
                "comparators": record.get("comparators"),
                "validation": record.get("validation"),
            }
        )
        codes.update(outcome.get("reason_codes", []))
        if claim.get("claim_type") == "POLICY_EVALUATION":
            comparator_ids = claim.get("comparator_ids")
            for run_id in run_ids or []:
                run_output = output_registry.get(run_id)
                policy_registry = (
                    run_output.get("policy_evidence") if isinstance(run_output, dict) else None
                )
                policy_evidence = (
                    policy_registry.get(requirement_id)
                    if isinstance(policy_registry, dict)
                    else None
                )
                semantic_run = semantic_runs.get(run_id)
                if (
                    not isinstance(policy_evidence, dict)
                    or set(policy_evidence)
                    != {"policy_exposure", "comparator_ids", "benefit", "cost"}
                    or not strict_score(policy_evidence.get("policy_exposure"))
                    or policy_evidence.get("policy_exposure", 0) <= 0
                    or policy_evidence.get("comparator_ids") != comparator_ids
                    or not isinstance(policy_evidence.get("benefit"), dict)
                    or not contains_strict_score(policy_evidence.get("benefit"))
                    or not isinstance(policy_evidence.get("cost"), dict)
                    or not contains_strict_score(policy_evidence.get("cost"))
                    or not isinstance(semantic_run, dict)
                    or semantic_run.get("policy_exposure") != policy_evidence.get("policy_exposure")
                ):
                    codes.add("RC_POLICY_OUTPUT_EVIDENCE_MISSING")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


def validate_runtime_aggregate_mapping(record: Any, primary_ids: Any) -> dict[str, Any]:
    """Require an exact, duplicate-free requirement-to-Claim aggregate mapping."""
    if not isinstance(record, dict) or not isinstance(primary_ids, list):
        return contract_result("BLOCK", "RC_AGGREGATE_CLAIM_MAPPING_INVALID")
    aggregate = record.get("aggregate")
    claims = record.get("claims")
    if not isinstance(aggregate, dict) or not isinstance(claims, list):
        return contract_result("BLOCK", "RC_AGGREGATE_CLAIM_MAPPING_INVALID")
    claim_map = {
        claim.get("requirement_id"): claim.get("claim_id")
        for claim in claims
        if isinstance(claim, dict)
    }
    expected = set(primary_ids)
    declared_primary = aggregate.get("primary_requirement_ids")
    supported = aggregate.get("supported_requirement_ids")
    mapping = aggregate.get("requirement_claim_ids")
    valid = (
        isinstance(declared_primary, list)
        and isinstance(supported, list)
        and len(declared_primary) == len(set(declared_primary))
        and len(supported) == len(set(supported))
        and set(declared_primary) == expected
        and set(supported) == expected
        and isinstance(mapping, dict)
        and set(mapping) == expected
        and mapping == claim_map
        and len(set(mapping.values())) == len(mapping)
    )
    return (
        contract_result("PASS")
        if valid
        else contract_result("BLOCK", "RC_AGGREGATE_CLAIM_MAPPING_INVALID")
    )


def _selected_runtime_run_ids(selection_record: dict[str, Any]) -> list[str]:
    selection = selection_record.get("selection")
    run_map = selection.get("requirement_to_run_map") if isinstance(selection, dict) else None
    if not isinstance(run_map, dict):
        raise ValueError("RC_REQUIREMENT_SELECTION_INPUT_INVALID")
    run_ids = {
        run_id
        for values in run_map.values()
        if isinstance(values, list)
        for run_id in values
        if isinstance(run_id, str)
    }
    if not run_ids:
        raise ValueError("RC_REQUIREMENT_SELECTED_RUN_MISSING")
    return sorted(run_ids)


def build_runtime_final_result(
    selection_record: dict[str, Any],
    semantic_record: dict[str, Any],
    manifest_registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Derive a multi-Run Final only from explicit selection and validated manifests."""
    selected_run_ids = _selected_runtime_run_ids(selection_record)
    selection = selection_record["selection"]
    run_map = selection["requirement_to_run_map"]
    output_map = selection["requirement_to_output_map"]
    run_records = {
        item.get("run_id"): item
        for item in selection_record.get("runs", [])
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    requirement_records = {
        item.get("requirement_id"): item
        for item in selection_record.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    semantic_claims = {
        item.get("requirement_id"): item
        for item in semantic_record.get("claims", [])
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    decision_hashes = {
        manifest_registry.get(run_id, {}).get("decision_hash") for run_id in selected_run_ids
    }
    if len(decision_hashes) != 1 or HEX64.fullmatch(str(next(iter(decision_hashes), ""))) is None:
        raise ValueError("RC_FINALIZATION_DECISION_LINEAGE_INVALID")
    decision_hash = next(iter(decision_hashes))
    run_bindings: dict[str, dict[str, Any]] = {}
    for run_id in selected_run_ids:
        manifest = manifest_registry.get(run_id)
        declared = run_records.get(run_id)
        if not isinstance(manifest, dict) or not isinstance(declared, dict):
            raise ValueError("RC_ACTUAL_RUN_REGISTRY_MISSING")
        requirement_ids = sorted(
            requirement_id for requirement_id, ids in run_map.items() if run_id in ids
        )
        output_ids = sorted(
            {
                output_id
                for requirement_id in requirement_ids
                for output_id in output_map.get(requirement_id, [])
            }
        )
        run_bindings[run_id] = {
            "manifest_hash": canonical_hash(manifest),
            "input_hash": manifest.get("input_hash"),
            "scenario_hash": declared.get("scenario_hash"),
            "configuration_hash": manifest.get("configuration_hash"),
            "output_hash": manifest.get("output_hash"),
            "requirement_ids": requirement_ids,
            "output_ids": output_ids,
        }
    requirement_results = {
        requirement_id: {
            "selected_run_ids": run_map.get(requirement_id),
            "selected_output_ids": output_map.get(requirement_id),
            "metric_ids": [record.get("selection_metric")],
            "claim_id": (semantic_claims.get(requirement_id) or {}).get("claim_id"),
        }
        for requirement_id, record in sorted(requirement_records.items())
    }
    limitations = selection.get("limitations")
    if not isinstance(limitations, list):
        raise ValueError("RC_FINALIZATION_LIMITATIONS_INVALID")
    return {
        "contract_version": "final-result/v2",
        "status": "FINAL_CANDIDATE",
        "selection_mode": selection.get("selection_mode"),
        "decision_hash": decision_hash,
        "selected_run_ids": selected_run_ids,
        "run_bindings": run_bindings,
        "requirement_results": requirement_results,
        "aggregate_status": "COMPLETE",
        "limitations": limitations,
    }


def build_runtime_claim_evidence(
    final_result: dict[str, Any],
    selection_record: dict[str, Any],
    semantic_record: dict[str, Any],
    manifest_registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Derive exact per-requirement Claim bindings without semantic defaults."""
    del selection_record
    bindings: dict[str, dict[str, Any]] = {}
    for claim in semantic_record.get("claims", []):
        if not isinstance(claim, dict):
            raise ValueError("RC_SEMANTIC_CLAIM_INPUT_INVALID")
        requirement_id = claim.get("requirement_id")
        run_ids = claim.get("selected_run_ids")
        if not isinstance(requirement_id, str) or not isinstance(run_ids, list) or not run_ids:
            raise ValueError("RC_SEMANTIC_CLAIM_INPUT_INVALID")
        bindings[requirement_id] = {
            "claim_id": claim.get("claim_id"),
            "requirement_id": requirement_id,
            "claim_type": claim.get("claim_type"),
            "selected_run_ids": run_ids,
            "selected_output_ids": claim.get("selected_output_ids"),
            "metric_ids": claim.get("metric_ids"),
            "evidence_class": claim.get("evidence_class"),
            "scope_hash": canonical_hash(claim.get("scope")),
            "manifest_hashes": {
                run_id: canonical_hash(manifest_registry[run_id]) for run_id in run_ids
            },
            "output_hashes": {
                run_id: manifest_registry[run_id].get("output_hash") for run_id in run_ids
            },
        }
    aggregate = semantic_record.get("aggregate")
    if not isinstance(aggregate, dict):
        raise ValueError("RC_AGGREGATE_CLAIM_MAPPING_INVALID")
    aggregate_body = {
        "primary_requirement_ids": aggregate.get("primary_requirement_ids"),
        "supported_requirement_ids": aggregate.get("supported_requirement_ids"),
        "requirement_claim_ids": aggregate.get("requirement_claim_ids"),
    }
    return {
        "contract_version": "claim-evidence/runtime-v3",
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
        "decision_hash": final_result.get("decision_hash"),
        "claims": bindings,
        "aggregate": {
            "claim_id": "CLAIM-AGGREGATE-" + canonical_hash(aggregate_body)[:24].upper(),
            **aggregate_body,
        },
    }


def validate_runtime_finalization(
    final_result: Any,
    claim_evidence: Any,
    selection_record: Any,
    semantic_record: Any,
    manifest_registry: Any,
) -> dict[str, Any]:
    """Require Final and Claim evidence to equal their canonical multi-Run derivation."""
    if not all(
        isinstance(item, dict)
        for item in (
            final_result,
            claim_evidence,
            selection_record,
            semantic_record,
            manifest_registry,
        )
    ):
        return contract_result("BLOCK", "RC_FINALIZATION_AUTHORITATIVE_ARTIFACT_INVALID")
    try:
        expected_final = build_runtime_final_result(
            selection_record,
            semantic_record,
            manifest_registry,
        )
        expected_claim = build_runtime_claim_evidence(
            expected_final,
            selection_record,
            semantic_record,
            manifest_registry,
        )
    except (KeyError, TypeError, ValueError):
        return contract_result("BLOCK", "RC_FINALIZATION_AUTHORITATIVE_ARTIFACT_INVALID")
    codes: set[str] = set()
    if final_result != expected_final:
        codes.add("RC_FINAL_RESULT_PORTFOLIO_BINDING_INVALID")
    if claim_evidence != expected_claim:
        codes.add("RC_CLAIM_RUNTIME_BINDING_INVALID")
    return contract_result("BLOCK", *codes) if codes else contract_result("PASS")


DATA_SUFFICIENCY_STATUSES = {
    "SUFFICIENT",
    "ACQUISITION_REQUIRED",
    "PARTIAL",
    "UNSATISFIABLE_WITH_CURRENT_INPUTS",
    "UNKNOWN",
}
DATA_ASSESSMENT_FIELDS = {
    "requirement_id",
    "data_sufficiency_status",
    "missing_fields",
    "missing_entities",
    "missing_time_scope",
    "candidate_sources",
    "acquisition_cost",
    "acquisition_time",
    "allowed_substitutions",
    "forbidden_substitutions",
    "affected_downstream_stages",
}


def validate_data_sufficiency_record(
    record: Any,
    *,
    requirements: Any | None = None,
    sources: Any | None = None,
) -> dict[str, Any]:
    """Validate the persisted v1 preflight and its requirement-level explanations."""
    if not isinstance(record, dict) or record.get("contract_version") != "data-sufficiency/v1":
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_RECORD_INVALID")
    if requirements is not None and record.get("requirements") != requirements:
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_REQUIREMENT_BINDING_MISMATCH")
    if sources is not None and record.get("sources") != sources:
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_SOURCE_BINDING_MISMATCH")
    outcome = evaluate_data_sufficiency(record)
    assessments = record.get("requirement_assessments")
    primary_ids = {
        item.get("requirement_id")
        for item in record.get("requirements", [])
        if isinstance(item, dict) and item.get("role", "PRIMARY") == "PRIMARY"
    }
    if (
        not isinstance(assessments, list)
        or len(assessments) != len(primary_ids)
        or {item.get("requirement_id") for item in assessments if isinstance(item, dict)}
        != primary_ids
        or any(
            not isinstance(item, dict)
            or set(item) != DATA_ASSESSMENT_FIELDS
            or item.get("data_sufficiency_status") not in DATA_SUFFICIENCY_STATUSES
            or any(
                not isinstance(item.get(field), list)
                for field in (
                    "missing_fields",
                    "missing_entities",
                    "missing_time_scope",
                    "candidate_sources",
                    "allowed_substitutions",
                    "forbidden_substitutions",
                    "affected_downstream_stages",
                )
            )
            or not isinstance(item.get("acquisition_cost"), str)
            or not isinstance(item.get("acquisition_time"), str)
            for item in assessments
        )
    ):
        return contract_result("BLOCK", "RC_DATA_SUFFICIENCY_ASSESSMENT_INVALID")
    return outcome


def validate_semantic_claim_bundle(record: Any) -> dict[str, Any]:
    """Validate every Claim in a persisted claim-evidence/v3 semantic bundle."""
    if not isinstance(record, dict) or record.get("contract_version") != "claim-evidence/v3":
        return contract_result("BLOCK", "RC_SEMANTIC_CLAIM_BUNDLE_INVALID")
    claims = record.get("claims")
    if not isinstance(claims, list) or not claims:
        return contract_result("BLOCK", "RC_SEMANTIC_CLAIM_BUNDLE_INVALID")
    codes: set[str] = set()
    statuses: list[str] = []
    for claim in claims:
        outcome = validate_semantic_claim_support(
            {
                "claim": claim,
                "runs": record.get("runs"),
                "outputs": record.get("outputs"),
                "comparators": record.get("comparators"),
                "validation": record.get("validation"),
                "aggregate": record.get("aggregate"),
            }
        )
        statuses.append(str(outcome.get("status")))
        codes.update(outcome.get("reason_codes", []))
    return (
        contract_result("BLOCK", *codes)
        if any(item != "PASS" for item in statuses)
        else contract_result("PASS")
    )


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def assert_json_safe(value: Any, location: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {location}")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"non-string key at {location}")
            assert_json_safe(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_json_safe(item, f"{location}[{index}]")
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError(f"non-JSON value at {location}")


def canonical_bytes(value: Any) -> bytes:
    assert_json_safe(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit_exists(commit: str) -> bool:
    if not isinstance(commit, str) or not GIT_SHA.fullmatch(commit):
        return False
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def current_git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = completed.stdout.strip()
    if not git_commit_exists(commit):
        raise ValueError("RC_GIT_COMMIT_UNAVAILABLE")
    return commit


def git_blob_hash(commit: str, repository_path: str) -> str | None:
    path = relative_case_path(REPO_ROOT, repository_path)
    if path is None:
        return None
    normalized = str(path.relative_to(REPO_ROOT))
    completed = subprocess.run(
        ["git", "show", f"{commit}:{normalized}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    return hashlib.sha256(completed.stdout).hexdigest()


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def sensitive_findings(value: Any) -> set[str]:
    findings: set[str] = set()

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                normalized = normalize_key(str(key))
                if normalized in SENSITIVE_KEYS:
                    findings.add("RC_SECRET_FIELD_REJECTED")
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        elif isinstance(item, str):
            normalized_path = item.replace("\\", "/")
            if (
                item.startswith(("/", "~", "\\\\"))
                or normalized_path.startswith("//")
                or WINDOWS_ABS.match(item)
                or ENV_PATH.match(item)
                or ".." in normalized_path.split("/")
            ):
                findings.add("RC_PRIVATE_ABSOLUTE_PATH_REJECTED")
            if CREDENTIAL_URL.match(item):
                findings.add("RC_CREDENTIAL_URL_REJECTED")
            if re.search(
                r"(?i)(bearer\s+[a-z0-9._-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
                item,
            ):
                findings.add("RC_SECRET_VALUE_REJECTED")

    walk(value)
    return findings


def boundary_validate(payload: Any, context: Any) -> GateResult:
    original = copy.deepcopy((payload, context))
    codes: set[str] = set()
    try:
        assert_json_safe(payload)
        assert_json_safe(context)
    except (TypeError, ValueError):
        codes.add("RC_BOUNDARY_NONFINITE_OR_NONJSON")
    if not isinstance(payload, dict):
        codes.add("RC_BOUNDARY_PAYLOAD_INVALID")
    if not isinstance(context, dict):
        codes.add("RC_CONTEXT_INVALID")
    else:
        if set(context) != {"stage", "enabled_components", "execution_scope"}:
            codes.add("RC_CONTEXT_FIELDS_INVALID")
        if context.get("stage") not in STAGES:
            codes.add("RC_CONTEXT_STAGE_INVALID")
        components = context.get("enabled_components")
        if (
            not isinstance(components, list)
            or not components
            or not all(isinstance(item, str) and item for item in components)
            or len(set(components)) != len(components)
            or any(item not in COMPONENT_IDS for item in components)
        ):
            codes.add("RC_CONTEXT_ENABLED_COMPONENTS_INVALID")
        if context.get("execution_scope") != "CASE":
            codes.add("RC_CONTEXT_EXECUTION_SCOPE_PROHIBITED")
    codes.update(sensitive_findings(payload))
    if (payload, context) != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_BOUNDARY_VALID")


def write_json(path: Path, value: Any, *, overwrite: bool = True) -> None:
    assert_json_safe(value)
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def artifact(kind: str, content: dict[str, Any], *, status: str = "ACCEPTED") -> dict[str, Any]:
    return {
        "artifact_type": kind,
        "status": status,
        "content_hash": canonical_hash(content),
        "content": content,
    }


def validate_artifact(value: Any, kind: str) -> GateResult:
    if not isinstance(value, dict):
        return blocked("RC_ARTIFACT_RECORD_INVALID")
    if value.get("artifact_type") != kind:
        return blocked("RC_ARTIFACT_TYPE_MISMATCH")
    if value.get("status") != "ACCEPTED":
        return blocked("RC_ARTIFACT_NOT_ACCEPTED")
    if set(value) != {"artifact_type", "status", "content_hash", "content"}:
        return blocked("RC_ARTIFACT_RECORD_FIELDS_INVALID")
    content = value.get("content")
    if not isinstance(content, dict):
        return blocked("RC_ARTIFACT_CONTENT_INVALID")
    try:
        actual_hash = canonical_hash(content)
    except (TypeError, ValueError):
        return blocked("RC_ARTIFACT_CONTENT_NONFINITE_OR_NONJSON")
    if value.get("content_hash") != actual_hash:
        return blocked("RC_ARTIFACT_HASH_MISMATCH")
    findings = sensitive_findings(value)
    return blocked(*findings) if findings else passed("RC_ARTIFACT_ACCEPTED")


def strict_score(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def contains_strict_score(value: Any) -> bool:
    if strict_score(value):
        return True
    if isinstance(value, dict):
        return any(contains_strict_score(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_strict_score(item) for item in value)
    return False


def validate_selected_output_contract(
    output: Any,
    *,
    expected_candidate_id: str | None = None,
    required_requirement_ids: list[str] | None = None,
    allow_probe: bool = False,
) -> GateResult:
    """Validate the downstream evidence contract shared by all successful case outputs."""

    original = copy.deepcopy(output)
    codes: set[str] = set()
    if not isinstance(output, dict):
        return blocked("RC_OUTPUT_CONTRACT_INVALID")
    try:
        assert_json_safe(output)
    except (TypeError, ValueError):
        codes.add("RC_OUTPUT_CONTRACT_NONFINITE_OR_NONJSON")
    codes.update(sensitive_findings(output))

    candidate_id = output.get("candidate_id")
    if (
        not isinstance(candidate_id, str)
        or not candidate_id
        or (expected_candidate_id is not None and candidate_id != expected_candidate_id)
    ):
        codes.add("RC_OUTPUT_CONTRACT_CANDIDATE_INVALID")

    if allow_probe:
        if (
            output.get("status") != "CONTRACT_PROBE"
            or output.get("probe_only") is not True
            or output.get("ranking_eligible") is not False
            or output.get("result_values_are_placeholders") is not True
        ):
            codes.add("RC_OUTPUT_CONTRACT_PROBE_IDENTITY_INVALID")
    elif output.get("status") != "SUCCESS":
        codes.add("RC_OUTPUT_CONTRACT_STATUS_INVALID")

    required = {
        "final_metrics",
        "claim_scope",
        "requirement_claims",
        "figure_ready_data",
        "uncertainty",
        "limitations",
        "robustness_evidence",
    }
    if not required <= set(output):
        codes.add("RC_OUTPUT_CONTRACT_REQUIRED_FIELDS_MISSING")

    final_metrics = output.get("final_metrics")
    if (
        not isinstance(final_metrics, dict)
        or not final_metrics
        or not contains_strict_score(final_metrics)
    ):
        codes.add("RC_OUTPUT_CONTRACT_FINAL_METRICS_INVALID")
    if not isinstance(output.get("claim_scope"), str) or not output.get("claim_scope"):
        codes.add("RC_OUTPUT_CONTRACT_CLAIM_SCOPE_INVALID")

    requirement_claims = output.get("requirement_claims")
    expected_requirements_valid = required_requirement_ids is None or (
        bool(required_requirement_ids)
        and all(isinstance(item, str) and item for item in required_requirement_ids)
        and len(set(required_requirement_ids)) == len(required_requirement_ids)
    )
    if not expected_requirements_valid:
        codes.add("RC_OUTPUT_CONTRACT_REQUIREMENT_REGISTRY_INVALID")
    if (
        not isinstance(requirement_claims, dict)
        or not requirement_claims
        or (
            required_requirement_ids is not None
            and set(requirement_claims) != set(required_requirement_ids)
        )
    ):
        codes.add("RC_OUTPUT_CONTRACT_REQUIREMENT_CLAIMS_INVALID")
    else:
        claim_ids: set[str] = set()
        for requirement_id, record in requirement_claims.items():
            if (
                not isinstance(requirement_id, str)
                or not requirement_id
                or not isinstance(record, dict)
                or set(record) != {"claim_id", "claim_text", "evidence_artifact_ids"}
            ):
                codes.add("RC_OUTPUT_CONTRACT_REQUIREMENT_CLAIMS_INVALID")
                continue
            claim_id = record.get("claim_id")
            evidence_ids = record.get("evidence_artifact_ids")
            if (
                not isinstance(claim_id, str)
                or not re.fullmatch(r"CLAIM-[A-Z0-9][A-Z0-9_-]{0,63}", claim_id)
                or claim_id in claim_ids
                or not isinstance(record.get("claim_text"), str)
                or not record.get("claim_text")
                or not isinstance(evidence_ids, list)
                or not evidence_ids
                or not all(isinstance(item, str) and item for item in evidence_ids)
                or len(set(evidence_ids)) != len(evidence_ids)
            ):
                codes.add("RC_OUTPUT_CONTRACT_REQUIREMENT_CLAIMS_INVALID")
            else:
                claim_ids.add(claim_id)

    figure_ready_data = output.get("figure_ready_data")
    if (
        not isinstance(figure_ready_data, list)
        or not figure_ready_data
        or not all(isinstance(item, dict) and item for item in figure_ready_data)
    ):
        codes.add("RC_OUTPUT_CONTRACT_FIGURE_DATA_INVALID")
    uncertainty = output.get("uncertainty")
    if not isinstance(uncertainty, dict) or not uncertainty:
        codes.add("RC_OUTPUT_CONTRACT_UNCERTAINTY_INVALID")
    limitations = output.get("limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or not all(isinstance(item, str) and item for item in limitations)
    ):
        codes.add("RC_OUTPUT_CONTRACT_LIMITATIONS_INVALID")

    robustness = output.get("robustness_evidence")
    if not isinstance(robustness, dict) or set(robustness) != {
        "metric",
        "metric_direction",
        "perturbations",
        "failure_cases",
    }:
        codes.add("RC_OUTPUT_CONTRACT_ROBUSTNESS_INVALID")
    else:
        metric = robustness.get("metric")
        perturbations = robustness.get("perturbations")
        if (
            not isinstance(metric, str)
            or not metric
            or robustness.get("metric_direction") not in ("MIN", "MAX")
            or not isinstance(perturbations, list)
            or not perturbations
        ):
            codes.add("RC_OUTPUT_CONTRACT_ROBUSTNESS_INVALID")
        else:
            perturbation_ids: set[str] = set()
            for item in perturbations:
                if not isinstance(item, dict) or set(item) != {
                    "perturbation_id",
                    "metric",
                    "result",
                    "evidence",
                }:
                    codes.add("RC_OUTPUT_CONTRACT_ROBUSTNESS_INVALID")
                    continue
                perturbation_id = item.get("perturbation_id")
                if (
                    not isinstance(perturbation_id, str)
                    or not perturbation_id
                    or perturbation_id in perturbation_ids
                    or item.get("metric") != metric
                    or not strict_score(item.get("result"))
                    or item.get("evidence") != "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS"
                ):
                    codes.add("RC_OUTPUT_CONTRACT_ROBUSTNESS_INVALID")
                else:
                    perturbation_ids.add(perturbation_id)
        failures = robustness.get("failure_cases")
        if (
            not isinstance(failures, list)
            or not failures
            or not all(isinstance(item, str) and item for item in failures)
        ):
            codes.add("RC_OUTPUT_CONTRACT_ROBUSTNESS_INVALID")

    if output != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_OUTPUT_CONTRACT_VALID")


def requirement_roles(requirements: Any) -> dict[str, str]:
    """Old traces default to PRIMARY; auxiliary roles never satisfy the primary gate."""
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("RC_OUTPUT_CONTRACT_REQUIREMENT_REGISTRY_INVALID")
    roles: dict[str, str] = {}
    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError("RC_OUTPUT_CONTRACT_REQUIREMENT_REGISTRY_INVALID")
        identifier = item.get("requirement_id")
        role = item.get("role", "PRIMARY")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in roles
            or role not in ("PRIMARY", "OPTIONAL", "DIAGNOSTIC", "SUPPORTING")
        ):
            raise ValueError("RC_OUTPUT_CONTRACT_REQUIREMENT_REGISTRY_INVALID")
        roles[identifier] = role
    if "PRIMARY" not in roles.values():
        raise ValueError("RC_OUTPUT_CONTRACT_REQUIREMENT_REGISTRY_INVALID")
    return roles


def required_requirement_ids(case_root: Path) -> list[str]:
    requirements = read_artifact(case_root, "problem_requirements")["content"].get("requirements")
    return sorted(key for key, role in requirement_roles(requirements).items() if role == "PRIMARY")


def preflight_output_contract(case_root: Path, probe_path: Path) -> tuple[GateResult, str]:
    state = load_state(case_root)
    if state.get("state") != "MODELS_PROPOSED":
        return blocked("RC_OUTPUT_CONTRACT_PREFLIGHT_STATE_INVALID"), ""
    resolved = (
        probe_path.resolve() if probe_path.is_absolute() else (case_root / probe_path).resolve()
    )
    try:
        relative = resolved.relative_to(case_root.resolve())
    except ValueError:
        return blocked("RC_OUTPUT_CONTRACT_PREFLIGHT_PATH_INVALID"), ""
    if not relative.parts or relative.parts[0] != "experiments" or not resolved.is_file():
        return blocked("RC_OUTPUT_CONTRACT_PREFLIGHT_PATH_INVALID"), str(relative)
    try:
        output = load_json(resolved)
    except (OSError, json.JSONDecodeError, ValueError):
        return blocked("RC_OUTPUT_CONTRACT_PREFLIGHT_JSON_INVALID"), str(relative)
    return (
        validate_selected_output_contract(
            output,
            required_requirement_ids=required_requirement_ids(case_root),
            allow_probe=True,
        ),
        str(relative),
    )


def relative_case_path(case_root: Path, value: str) -> Path | None:
    if (
        not isinstance(value, str)
        or not value
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        return None
    candidate = (case_root / value).resolve()
    try:
        candidate.relative_to(case_root.resolve())
    except ValueError:
        return None
    return candidate


def validate_manifest(
    manifest: Any,
    *,
    case_root: Path | None = None,
    trusted_freezes: dict[str, str] | None = None,
) -> GateResult:
    original = copy.deepcopy(manifest)
    codes: set[str] = set()
    try:
        assert_json_safe(manifest)
    except (TypeError, ValueError):
        codes.add("RC_MANIFEST_NONFINITE_OR_NONJSON")
    if not isinstance(manifest, dict):
        return blocked("RC_MANIFEST_INVALID")
    required = {
        "run_id",
        "input_files",
        "input_hash",
        "code_commit",
        "code_files",
        "code_tree_hash",
        "configuration",
        "configuration_hash",
        "random_seed",
        "argv",
        "cwd_policy",
        "environment_allowlist",
        "output_files",
        "output_hash",
        "outcome",
        "failure",
        "supersession",
        "trusted_capture",
        "freeze_bindings",
        "decision_hash",
    }
    allowed = required | {"capture_record", "scenario_hash"}
    if set(manifest) != required:
        if not required <= set(manifest):
            codes.add("RC_MANIFEST_REQUIRED_BINDING_MISSING")
        if set(manifest) - allowed:
            codes.add("RC_MANIFEST_ADDITIONAL_FIELDS_REJECTED")
    if not isinstance(manifest.get("run_id"), str) or not manifest.get("run_id"):
        codes.add("RC_MANIFEST_RUN_ID_INVALID")
    for name in (
        "input_hash",
        "code_tree_hash",
        "configuration_hash",
        "output_hash",
        "decision_hash",
    ):
        if not HEX64.fullmatch(str(manifest.get(name, ""))):
            codes.add(f"RC_MANIFEST_HASH_INVALID:{name}")
    if "scenario_hash" in manifest and not HEX64.fullmatch(str(manifest.get("scenario_hash", ""))):
        codes.add("RC_MANIFEST_HASH_INVALID:scenario_hash")
    commit = manifest.get("code_commit")
    if not isinstance(commit, str) or not git_commit_exists(commit):
        codes.add("RC_MANIFEST_GIT_COMMIT_INVALID")
    configuration = manifest.get("configuration")
    if not isinstance(configuration, dict):
        codes.add("RC_MANIFEST_CONFIGURATION_INVALID")
    else:
        try:
            if manifest.get("configuration_hash") != canonical_hash(configuration):
                codes.add("RC_MANIFEST_CONFIGURATION_HASH_MISMATCH")
        except (TypeError, ValueError):
            codes.add("RC_MANIFEST_CONFIGURATION_INVALID")
    seed = manifest.get("random_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        codes.add("RC_MANIFEST_SEED_INVALID")
    argv = manifest.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
        codes.add("RC_MANIFEST_ARGV_INVALID")
    if manifest.get("cwd_policy") != "CASE_ROOT_RELATIVE":
        codes.add("RC_MANIFEST_CWD_POLICY_INVALID")
    environment = manifest.get("environment_allowlist")
    if not isinstance(environment, dict) or set(environment) - {"PYTHONHASHSEED", "TZ"}:
        codes.add("RC_MANIFEST_ENVIRONMENT_INVALID")
    outcome = manifest.get("outcome")
    allowed_outcomes = ("SUCCESS", "FAILED", "PARTIAL", "SUPERSEDED", "STALE", "INFEASIBLE")
    if outcome not in allowed_outcomes:
        codes.add("RC_MANIFEST_OUTCOME_INVALID")
    elif outcome != "SUCCESS":
        codes.add(f"RC_MANIFEST_NOT_SUCCESS:{outcome}")
    if manifest.get("trusted_capture") is not True:
        codes.add("RC_MANIFEST_TRUSTED_CAPTURE_REQUIRED")
    if not isinstance(manifest.get("failure"), (dict, type(None))):
        codes.add("RC_MANIFEST_FAILURE_INVALID")
    if not isinstance(manifest.get("supersession"), (dict, type(None))):
        codes.add("RC_MANIFEST_SUPERSESSION_INVALID")
    outcome_evidence_invalid = (
        (
            outcome == "SUCCESS"
            and (manifest.get("failure") is not None or manifest.get("supersession") is not None)
        )
        or (
            outcome in ("FAILED", "PARTIAL", "INFEASIBLE")
            and (
                not isinstance(manifest.get("failure"), dict)
                or not manifest.get("failure")
                or manifest.get("supersession") is not None
            )
        )
        or (
            outcome in ("SUPERSEDED", "STALE")
            and (
                not isinstance(manifest.get("supersession"), dict)
                or not manifest.get("supersession")
            )
        )
    )
    if outcome_evidence_invalid:
        codes.add("RC_MANIFEST_OUTCOME_EVIDENCE_INCONSISTENT")
    codes.update(sensitive_findings(manifest))
    bindings = manifest.get("freeze_bindings")
    if (
        not isinstance(bindings, dict)
        or not bindings
        or trusted_freezes is None
        or bindings != trusted_freezes
    ):
        codes.add("RC_MANIFEST_UNTRUSTED_FREEZE")
    input_files = manifest.get("input_files")
    declared_input_registry: dict[str, Any] = {}
    if not isinstance(input_files, list) or not input_files:
        codes.add("RC_MANIFEST_INPUT_FILES_INVALID")
    elif case_root is not None:
        input_hashes: list[str] = []
        input_paths: set[str] = set()
        for record in input_files:
            if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
                codes.add("RC_MANIFEST_INPUT_RECORD_INVALID")
                continue
            relative = record.get("path")
            path = relative_case_path(case_root, relative)
            if not isinstance(relative, str) or relative in input_paths:
                codes.add("RC_MANIFEST_INPUT_RECORD_INVALID")
                continue
            input_paths.add(relative)
            declared_input_registry[relative] = record.get("sha256")
            if path is None or not path.is_file():
                codes.add("RC_MANIFEST_INPUT_MISSING")
                continue
            actual = file_hash(path)
            input_hashes.append(actual)
            if record.get("sha256") != actual:
                codes.add("RC_MANIFEST_INPUT_MUTATION")
        if input_hashes and manifest.get("input_hash") != canonical_hash(input_hashes):
            codes.add("RC_MANIFEST_INPUT_HASH_MISMATCH")
    try:
        declared_input_freeze = (
            canonical_hash(declared_input_registry) if declared_input_registry else None
        )
    except (TypeError, ValueError):
        declared_input_freeze = None
    if (
        not isinstance(trusted_freezes, dict)
        or not declared_input_registry
        or trusted_freezes.get("input_set") != declared_input_freeze
    ):
        codes.add("RC_MANIFEST_INPUT_FREEZE_MISMATCH")
    code_files = manifest.get("code_files")
    if not isinstance(code_files, list) or not code_files:
        codes.add("RC_MANIFEST_CODE_FILES_INVALID")
    else:
        code_hashes: list[str] = []
        code_paths: set[tuple[str, str]] = set()
        for record in code_files:
            if not isinstance(record, dict) or set(record) != {
                "scope",
                "path",
                "repository_path",
                "sha256",
            }:
                codes.add("RC_MANIFEST_CODE_RECORD_INVALID")
                continue
            scope = record.get("scope")
            relative = record.get("path")
            repository_path = record.get("repository_path")
            root = SKILL_ROOT if scope == "SKILL_ROOT" else case_root
            identity = (str(scope), str(relative))
            if scope not in ("SKILL_ROOT", "CASE_ROOT") or identity in code_paths:
                codes.add("RC_MANIFEST_CODE_RECORD_INVALID")
                continue
            code_paths.add(identity)
            path = relative_case_path(root, relative) if root is not None else None
            if path is None or not path.is_file():
                codes.add("RC_MANIFEST_CODE_MISSING")
                continue
            actual = file_hash(path)
            code_hashes.append(actual)
            if record.get("sha256") != actual:
                codes.add("RC_MANIFEST_CODE_MUTATION")
            expected_repository_path = f".agents/skills/cumcm-modeling-evidence/{relative}"
            if (
                not isinstance(repository_path, str)
                or (scope == "SKILL_ROOT" and repository_path != expected_repository_path)
                or git_blob_hash(str(commit), repository_path) != actual
            ):
                codes.add("RC_MANIFEST_CODE_COMMIT_MISMATCH")
        if code_hashes and manifest.get("code_tree_hash") != canonical_hash(code_hashes):
            codes.add("RC_MANIFEST_CODE_TREE_HASH_MISMATCH")
    try:
        declared_code_freeze = canonical_hash(code_files) if isinstance(code_files, list) else None
        declared_commit_freeze = canonical_hash(commit) if isinstance(commit, str) else None
    except (TypeError, ValueError):
        declared_code_freeze = None
        declared_commit_freeze = None
    if (
        not isinstance(trusted_freezes, dict)
        or trusted_freezes.get("code_set") != declared_code_freeze
        or trusted_freezes.get("code_commit") != declared_commit_freeze
    ):
        codes.add("RC_MANIFEST_CODE_FREEZE_MISMATCH")
    output_files = manifest.get("output_files")
    if not isinstance(output_files, list) or not output_files:
        codes.add("RC_MANIFEST_OUTPUT_FILES_INVALID")
    elif case_root is not None:
        hashes: list[str] = []
        output_paths: set[str] = set()
        for record in output_files:
            if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
                codes.add("RC_MANIFEST_OUTPUT_RECORD_INVALID")
                continue
            relative = record.get("path")
            path = relative_case_path(case_root, relative)
            if not isinstance(relative, str) or relative in output_paths:
                codes.add("RC_MANIFEST_OUTPUT_RECORD_INVALID")
                continue
            output_paths.add(relative)
            if path is None or not path.is_file():
                codes.add("RC_MANIFEST_OUTPUT_MISSING")
                continue
            actual = file_hash(path)
            hashes.append(actual)
            if record.get("sha256") != actual:
                codes.add("RC_MANIFEST_OUTPUT_MUTATION")
        if hashes and manifest.get("output_hash") != canonical_hash(hashes):
            codes.add("RC_MANIFEST_OUTPUT_HASH_MISMATCH")
    has_case_code = isinstance(code_files, list) and any(
        isinstance(record, dict) and record.get("scope") == "CASE_ROOT" for record in code_files
    )
    capture_binding = manifest.get("capture_record")
    if has_case_code:
        capture_result = validate_execution_capture(
            capture_binding,
            manifest,
            case_root=case_root,
        )
        codes.update(capture_result.reason_codes if not capture_result.accepted else ())
    elif capture_binding is not None:
        codes.add("RC_EXECUTION_CAPTURE_UNEXPECTED")
    if manifest != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_REPRODUCIBILITY_MANIFEST_VALID")


def parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def validate_execution_capture(
    binding: Any,
    manifest: dict[str, Any],
    *,
    case_root: Path | None,
) -> GateResult:
    codes: set[str] = set()
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        return blocked("RC_EXECUTION_CAPTURE_BINDING_INVALID")
    if case_root is None:
        return blocked("RC_EXECUTION_CAPTURE_CONTEXT_MISSING")
    run_id = manifest.get("run_id")
    expected_path = f"runs/{run_id}/execution_capture.json"
    capture_path = relative_case_path(case_root, binding.get("path"))
    if binding.get("path") != expected_path or capture_path is None or not capture_path.is_file():
        return blocked("RC_EXECUTION_CAPTURE_MISSING")
    if binding.get("sha256") != file_hash(capture_path):
        codes.add("RC_EXECUTION_CAPTURE_MUTATION")
    try:
        capture = load_json(capture_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return blocked("RC_EXECUTION_CAPTURE_INVALID")
    required = {
        "schema_version",
        "capture_mode",
        "runner_version",
        "run_id",
        "candidate_id",
        "seed",
        "started_at",
        "ended_at",
        "elapsed_seconds",
        "exit_code",
        "argv",
        "environment_allowlist",
        "stdout",
        "stderr",
        "output",
        "outcome",
        "failure",
        "freeze_bindings",
        "input_files",
        "code_files",
        "code_commit",
        "configuration",
        "configuration_hash",
    }
    allowed = required | {"scenario_hash"}
    if not isinstance(capture, dict) or not required <= set(capture) or set(capture) - allowed:
        return blocked("RC_EXECUTION_CAPTURE_FIELDS_INVALID")
    configuration = manifest.get("configuration")
    relational_bindings = {
        "run_id": run_id,
        "candidate_id": configuration.get("candidate_id")
        if isinstance(configuration, dict)
        else None,
        "seed": manifest.get("random_seed"),
        "argv": manifest.get("argv"),
        "environment_allowlist": manifest.get("environment_allowlist"),
        "outcome": manifest.get("outcome"),
        "failure": manifest.get("failure"),
        "freeze_bindings": manifest.get("freeze_bindings"),
        "input_files": manifest.get("input_files"),
        "code_files": manifest.get("code_files"),
        "code_commit": manifest.get("code_commit"),
        "configuration": configuration,
        "configuration_hash": manifest.get("configuration_hash"),
    }
    if "scenario_hash" in manifest:
        relational_bindings["scenario_hash"] = manifest.get("scenario_hash")
    if any(capture.get(key) != value for key, value in relational_bindings.items()):
        codes.add("RC_EXECUTION_CAPTURE_MANIFEST_MISMATCH")
    if "scenario_hash" in capture and not HEX64.fullmatch(str(capture.get("scenario_hash", ""))):
        codes.add("RC_EXECUTION_CAPTURE_SCENARIO_HASH_INVALID")
    if (
        capture.get("schema_version") != "1.0.0"
        or capture.get("capture_mode") != "CONTROLLED_CASE_SUBPROCESS"
        or capture.get("runner_version") != VERSION
    ):
        codes.add("RC_EXECUTION_CAPTURE_IDENTITY_INVALID")
    started = parse_utc_timestamp(capture.get("started_at"))
    ended = parse_utc_timestamp(capture.get("ended_at"))
    elapsed = capture.get("elapsed_seconds")
    if (
        started is None
        or ended is None
        or ended < started
        or not strict_score(elapsed)
        or float(elapsed) < 0
    ):
        codes.add("RC_EXECUTION_CAPTURE_TIMING_INVALID")
    exit_code = capture.get("exit_code")
    outcome = capture.get("outcome")
    if (
        not isinstance(exit_code, int)
        or isinstance(exit_code, bool)
        or (exit_code == 0) != (outcome == "SUCCESS")
    ):
        codes.add("RC_EXECUTION_CAPTURE_EXIT_OUTCOME_MISMATCH")
    for stream in ("stdout", "stderr"):
        record = capture.get(stream)
        if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
            codes.add(f"RC_EXECUTION_CAPTURE_{stream.upper()}_INVALID")
            continue
        path = relative_case_path(case_root, record.get("path"))
        if (
            path is None
            or Path(str(record.get("path"))).parts[:2] != ("runs", str(run_id))
            or not path.is_file()
            or record.get("sha256") != file_hash(path)
        ):
            codes.add(f"RC_EXECUTION_CAPTURE_{stream.upper()}_MUTATION")
    output = capture.get("output")
    manifest_outputs = manifest.get("output_files")
    if (
        not isinstance(output, dict)
        or set(output) != {"path", "sha256"}
        or not isinstance(manifest_outputs, list)
        or manifest_outputs != [output]
    ):
        codes.add("RC_EXECUTION_CAPTURE_OUTPUT_MISMATCH")
    return blocked(*codes) if codes else passed("RC_EXECUTION_CAPTURE_VALID")


def validate_comparison(
    comparison: Any,
    trusted_freezes: dict[str, str] | None = None,
    *,
    case_root: Path | None = None,
) -> GateResult:
    original = copy.deepcopy(comparison)
    codes: set[str] = set()
    comparison_json_safe = True
    try:
        assert_json_safe(comparison)
    except (TypeError, ValueError):
        comparison_json_safe = False
        codes.add("RC_COMPARISON_NONFINITE_OR_NONJSON")
    if not isinstance(comparison, dict):
        return blocked("RC_COMPARISON_INVALID")
    allowed_fields = {
        "aggregation_rule",
        "attempts",
        "baseline_id",
        "candidate_ids",
        "code_commit",
        "freeze_bindings",
        "handoff_generated_at",
        "leakage_checks",
        "metric",
        "metric_direction",
        "random_seeds",
        "reliability",
        "required_code_files",
        "required_input_hashes",
        "selected_candidate_id",
        "selection_decision_hash",
        "selection_rule",
        "splits",
        "stop_rule",
        "test_access",
    }
    if set(comparison) != allowed_fields:
        codes.add("RC_COMPARISON_FIELDS_INVALID")
    codes.update(sensitive_findings(comparison))
    candidates = comparison.get("candidate_ids")
    candidate_items = candidates if isinstance(candidates, list) else []
    baseline = comparison.get("baseline_id")
    if not isinstance(candidates, list) or not candidates:
        codes.add("RC_COMPARISON_EMPTY_CANDIDATE_SET")
    elif not all(isinstance(item, str) and item for item in candidates) or len(
        set(candidates)
    ) != len(candidates):
        codes.add("RC_COMPARISON_CANDIDATE_SET_INVALID")
    if not isinstance(baseline, str) or baseline not in candidate_items:
        codes.add("RC_COMPARISON_BASELINE_MISSING")
    splits = comparison.get("splits")
    if not isinstance(splits, dict) or set(splits) != {"train", "validation", "test"}:
        codes.add("RC_COMPARISON_SPLIT_INVALID")
    else:
        split_sets: list[set[Any]] = []
        for values in splits.values():
            if not isinstance(values, list) or not values:
                codes.add("RC_COMPARISON_EMPTY_SPLIT")
                break
            try:
                split_sets.append(set(values))
            except TypeError:
                codes.add("RC_COMPARISON_SPLIT_INVALID")
        if len(split_sets) == 3 and any(
            split_sets[left] & split_sets[right]
            for left in range(3)
            for right in range(left + 1, 3)
        ):
            codes.add("RC_COMPARISON_SPLIT_OVERLAP")
    flags = comparison.get("leakage_checks")
    false_flags = {
        "test_used_for_candidate_generation",
        "test_used_for_feature_selection",
        "test_used_for_threshold_selection",
        "future_information",
        "group_overlap",
        "target_in_features",
    }
    if not isinstance(flags, dict):
        codes.add("RC_COMPARISON_LEAKAGE_CHECKS_MISSING")
    else:
        for name in false_flags:
            if flags.get(name) is not False:
                codes.add(f"RC_COMPARISON_LEAKAGE:{name}")
        if flags.get("time_order_valid") is not True:
            codes.add("RC_COMPARISON_TIME_LEAKAGE")
    access = comparison.get("test_access")
    if not isinstance(access, dict) or access.get("authorized") is not True:
        codes.add("RC_COMPARISON_UNAUTHORIZED_TEST_ACCESS")
    else:
        if access.get("count") != 1:
            codes.add("RC_COMPARISON_TEST_ACCESS_COUNT_INVALID")
        if access.get("used_for_selection") is not False:
            codes.add("RC_COMPARISON_TEST_USED_FOR_SELECTION")
    bindings = comparison.get("freeze_bindings")
    direction = comparison.get("metric_direction")
    metric = comparison.get("metric")
    aggregation_rule = comparison.get("aggregation_rule")
    selection_rule = comparison.get("selection_rule")
    seeds = comparison.get("random_seeds")
    seed_items = seeds if isinstance(seeds, list) else []
    required_inputs = comparison.get("required_input_hashes")
    required_code_files = comparison.get("required_code_files")
    code_commit = comparison.get("code_commit")
    required_code_valid = (
        isinstance(required_code_files, list)
        and bool(required_code_files)
        and isinstance(code_commit, str)
        and GIT_SHA.fullmatch(code_commit) is not None
        and all(
            isinstance(record, dict)
            and set(record) == {"scope", "path", "repository_path", "sha256"}
            and record.get("scope") in ("SKILL_ROOT", "CASE_ROOT")
            and isinstance(record.get("path"), str)
            and isinstance(record.get("repository_path"), str)
            and HEX64.fullmatch(str(record.get("sha256", ""))) is not None
            for record in required_code_files
        )
    )
    stop_rule = comparison.get("stop_rule")
    handoff_generated_at = comparison.get("handoff_generated_at")
    execution_policy_valid = (
        isinstance(stop_rule, str)
        and bool(stop_rule.strip())
        and isinstance(handoff_generated_at, str)
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", handoff_generated_at) is not None
    )
    required_inputs_valid = (
        isinstance(required_inputs, dict)
        and bool(required_inputs)
        and all(
            isinstance(relative, str)
            and relative_case_path(Path("."), relative) is not None
            and HEX64.fullmatch(str(digest))
            for relative, digest in required_inputs.items()
        )
    )
    derived_freezes: dict[str, str] | None = None
    if (
        isinstance(candidates, list)
        and candidates
        and isinstance(metric, str)
        and metric
        and direction in ("MIN", "MAX")
        and aggregation_rule == "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
        and selection_rule == ("ARGMIN_THEN_ID" if direction == "MIN" else "ARGMAX_THEN_ID")
        and isinstance(seeds, list)
        and seeds
        and all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds)
        and len(set(seeds)) == len(seeds)
        and required_inputs_valid
        and required_code_valid
        and execution_policy_valid
        and comparison_json_safe
    ):
        derived_freezes = {
            "candidate_set": canonical_hash(candidates),
            "metric": canonical_hash(
                {
                    "name": metric,
                    "direction": direction,
                    "aggregation_rule": aggregation_rule,
                    "selection_rule": selection_rule,
                }
            ),
            "seed_schedule": canonical_hash(seeds),
            "split_assignment": canonical_hash(splits),
            "baseline": canonical_hash(baseline),
            "input_set": canonical_hash(required_inputs),
            "execution_policy": canonical_hash(
                {
                    "stop_rule": stop_rule,
                    "handoff_generated_at": handoff_generated_at,
                }
            ),
            "code_set": canonical_hash(required_code_files),
            "code_commit": canonical_hash(code_commit),
        }
    else:
        codes.add("RC_COMPARISON_FREEZE_INPUT_INVALID")
    if (
        not isinstance(bindings, dict)
        or not bindings
        or trusted_freezes is None
        or bindings != trusted_freezes
        or derived_freezes is None
        or bindings != derived_freezes
    ):
        codes.add("RC_COMPARISON_UNTRUSTED_FREEZE")
    attempts = comparison.get("attempts")
    successful_scores: dict[str, list[float]] = {}
    attempt_keys: set[tuple[str, int]] = set()
    if not isinstance(attempts, list) or not attempts:
        codes.add("RC_COMPARISON_ATTEMPT_LEDGER_INVALID")
    else:
        for attempt in attempts:
            if not isinstance(attempt, dict):
                codes.add("RC_COMPARISON_ATTEMPT_LEDGER_INVALID")
                continue
            score = attempt.get("validation_score")
            outcome = attempt.get("outcome")
            candidate_id = attempt.get("candidate_id")
            run_id = attempt.get("run_id")
            random_seed = attempt.get("random_seed")
            if (
                not isinstance(candidate_id, str)
                or candidate_id not in candidate_items
                or not isinstance(run_id, str)
                or not run_id
                or not isinstance(random_seed, int)
                or isinstance(random_seed, bool)
                or random_seed not in seed_items
                or (candidate_id, random_seed) in attempt_keys
            ):
                codes.add("RC_COMPARISON_ATTEMPT_BINDING_INVALID")
                continue
            attempt_keys.add((candidate_id, random_seed))
            if outcome == "SUCCESS":
                if not strict_score(score):
                    codes.add("RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID")
                elif isinstance(candidate_id, str):
                    successful_scores.setdefault(candidate_id, []).append(float(score))
            elif score is not None:
                codes.add("RC_COMPARISON_NON_SUCCESS_ATTEMPT_SCORED")
            if case_root is not None and isinstance(run_id, str) and run_id:
                manifest_path = case_root / "runs" / run_id / "manifest.json"
                if not manifest_path.is_file():
                    codes.add("RC_COMPARISON_RUN_MANIFEST_MISSING")
                    continue
                try:
                    manifest = load_json(manifest_path)
                except (OSError, json.JSONDecodeError, ValueError):
                    codes.add("RC_COMPARISON_RUN_MANIFEST_INVALID")
                    continue
                manifest_result = validate_manifest(
                    manifest,
                    case_root=case_root,
                    trusted_freezes=trusted_freezes,
                )
                allowed_non_success = (
                    isinstance(manifest, dict)
                    and manifest.get("outcome")
                    in ("FAILED", "PARTIAL", "SUPERSEDED", "STALE", "INFEASIBLE")
                    and set(manifest_result.reason_codes)
                    == {f"RC_MANIFEST_NOT_SUCCESS:{manifest.get('outcome')}"}
                )
                if not manifest_result.accepted and not allowed_non_success:
                    codes.add("RC_COMPARISON_RUN_MANIFEST_INVALID")
                configuration = manifest.get("configuration", {})
                if (
                    manifest.get("run_id") != run_id
                    or manifest.get("random_seed") != random_seed
                    or manifest.get("outcome") != outcome
                    or not isinstance(configuration, dict)
                    or configuration.get("candidate_id") != candidate_id
                    or configuration.get("seed") != random_seed
                ):
                    codes.add("RC_COMPARISON_RUN_BINDING_MISMATCH")
                output_files = manifest.get("output_files")
                if not isinstance(output_files, list) or len(output_files) != 1:
                    codes.add("RC_COMPARISON_RUN_OUTPUT_INVALID")
                    continue
                output_relative = output_files[0].get("path")
                output_path = relative_case_path(case_root, output_relative)
                if output_path is None or not output_path.is_file():
                    codes.add("RC_COMPARISON_RUN_OUTPUT_INVALID")
                    continue
                try:
                    output = load_json(output_path)
                except (OSError, json.JSONDecodeError, ValueError):
                    codes.add("RC_COMPARISON_RUN_OUTPUT_INVALID")
                    continue
                if not isinstance(output, dict) or output.get("candidate_id") != candidate_id:
                    codes.add("RC_COMPARISON_RUN_OUTPUT_BINDING_MISMATCH")
                    continue
                expected_score: Any = None
                if outcome == "SUCCESS":
                    metrics = output.get("validation_metrics")
                    if (
                        not isinstance(metric, str)
                        or not isinstance(metrics, dict)
                        or not strict_score(metrics.get(metric))
                    ):
                        codes.add("RC_COMPARISON_RUN_OUTPUT_METRIC_INVALID")
                    else:
                        expected_score = float(metrics[metric])
                if outcome == "SUCCESS" and (
                    expected_score is None
                    or not strict_score(score)
                    or float(score) != expected_score
                ):
                    codes.add("RC_COMPARISON_SCORE_OUTPUT_MISMATCH")
    expected_attempts = (
        {(candidate, seed) for candidate in candidate_items for seed in seed_items}
        if isinstance(candidates, list)
        and all(isinstance(candidate, str) for candidate in candidates)
        and isinstance(seeds, list)
        and all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds)
        else set()
    )
    if attempt_keys != expected_attempts:
        codes.add("RC_COMPARISON_ATTEMPT_MATRIX_INCOMPLETE")
    aggregated_scores = {
        candidate: sum(values) / len(values)
        for candidate, values in successful_scores.items()
        if values
    }
    if isinstance(baseline, str) and baseline not in aggregated_scores:
        codes.add("RC_COMPARISON_BASELINE_SUCCESS_MISSING")
    selected = comparison.get("selected_candidate_id")
    decision_fields_valid = (
        comparison_json_safe
        and isinstance(metric, str)
        and bool(metric)
        and isinstance(aggregation_rule, str)
        and aggregation_rule == "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
        and isinstance(selection_rule, str)
        and selection_rule
    )
    if aggregated_scores and direction in ("MIN", "MAX") and decision_fields_valid:
        target = (
            min(aggregated_scores.values())
            if direction == "MIN"
            else max(aggregated_scores.values())
        )
        expected = min(key for key, value in aggregated_scores.items() if value == target)
        if selected != expected:
            codes.add("RC_COMPARISON_SELECTION_MISMATCH")
        decision_payload = {
            "selected_candidate_id": expected,
            "validation_scores": aggregated_scores,
            "metric": metric,
            "rule": selection_rule,
            "aggregation_rule": aggregation_rule,
        }
        selection_decision_hash = comparison.get("selection_decision_hash")
        if not HEX64.fullmatch(
            str(selection_decision_hash or "")
        ) or selection_decision_hash != canonical_hash(decision_payload):
            codes.add("RC_COMPARISON_DECISION_HASH_MISMATCH")
        if case_root is not None and isinstance(attempts, list):
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    continue
                manifest_path = (
                    case_root / "runs" / str(attempt.get("run_id", "")) / "manifest.json"
                )
                if manifest_path.is_file():
                    manifest = load_json(manifest_path)
                    if manifest.get("decision_hash") != selection_decision_hash:
                        codes.add("RC_COMPARISON_MANIFEST_DECISION_MISMATCH")
    else:
        codes.add("RC_COMPARISON_METRIC_OR_SUCCESS_SET_INVALID")
    if case_root is not None:
        try:
            audited_inputs = read_artifact(case_root, "data_audit")["content"].get("data_hashes")
        except (OSError, ValueError, json.JSONDecodeError):
            audited_inputs = None
        if not required_inputs_valid or required_inputs != audited_inputs:
            codes.add("RC_COMPARISON_INPUT_LINEAGE_MISMATCH")
        try:
            frozen_plan = read_artifact(case_root, "experiment_plan")["content"]
        except (OSError, ValueError, json.JSONDecodeError):
            frozen_plan = None
        if (
            not required_code_valid
            or not isinstance(frozen_plan, dict)
            or required_code_files != frozen_plan.get("required_code_files")
            or code_commit != frozen_plan.get("code_commit")
        ):
            codes.add("RC_COMPARISON_CODE_LINEAGE_MISMATCH")
        attempt_items = attempts if isinstance(attempts, list) else []
        ledger_run_ids = {
            attempt.get("run_id")
            for attempt in attempt_items
            if isinstance(attempt, dict) and isinstance(attempt.get("run_id"), str)
        }
        manifest_run_ids = {path.parent.name for path in case_root.glob("runs/*/manifest.json")}
        if ledger_run_ids != manifest_run_ids:
            codes.add("RC_COMPARISON_RUN_LEDGER_NOT_EXACT")
        reliability = comparison.get("reliability")
        expected_reliability = {
            "attempts": len(attempt_items),
            "successful": sum(
                isinstance(attempt, dict) and attempt.get("outcome") == "SUCCESS"
                for attempt in attempt_items
            ),
            "failed_or_infeasible": sum(
                isinstance(attempt, dict) and attempt.get("outcome") != "SUCCESS"
                for attempt in attempt_items
            ),
        }
        if reliability != expected_reliability:
            codes.add("RC_COMPARISON_RELIABILITY_DENOMINATOR_MISMATCH")
        try:
            candidate_records = read_artifact(case_root, "model_candidates")["content"].get(
                "candidates"
            )
        except ValueError:
            candidate_records = None
        if not isinstance(candidate_records, list):
            codes.add("RC_COMPARISON_CANDIDATE_REGISTRY_INVALID")
        else:
            registered_ids = [
                item.get("candidate_id") for item in candidate_records if isinstance(item, dict)
            ]
            registered_baselines = [
                item.get("candidate_id")
                for item in candidate_records
                if isinstance(item, dict) and item.get("baseline") is True
            ]
            if registered_ids != candidates or registered_baselines != [baseline]:
                codes.add("RC_COMPARISON_CANDIDATE_REGISTRY_MISMATCH")
    if comparison != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_LEAKAGE_SAFE_COMPARISON_VALID")


def validate_final_result(
    final_result: Any,
    comparison: Any,
    *,
    case_root: Path,
) -> GateResult:
    original = copy.deepcopy((final_result, comparison))
    codes: set[str] = set()
    if not isinstance(final_result, dict) or not isinstance(comparison, dict):
        return blocked("RC_FINAL_RESULT_INVALID")
    required = {
        "status",
        "selected_model",
        "run_id",
        "output_hash",
        "decision_hash",
        "final_metrics",
        "claim_scope",
    }
    if set(final_result) != required:
        codes.add("RC_FINAL_RESULT_FIELDS_INVALID")
    selected = comparison.get("selected_candidate_id")
    attempts = comparison.get("attempts")
    selected_attempts = (
        sorted(
            [
                attempt
                for attempt in attempts
                if isinstance(attempt, dict)
                and attempt.get("candidate_id") == selected
                and attempt.get("outcome") == "SUCCESS"
            ],
            key=lambda item: (str(item.get("random_seed")), str(item.get("run_id"))),
        )
        if isinstance(attempts, list)
        else []
    )
    if (
        final_result.get("status") != "FINAL_CANDIDATE"
        or final_result.get("selected_model") != selected
        or not selected_attempts
        or final_result.get("run_id") != selected_attempts[0].get("run_id")
        or final_result.get("decision_hash") != comparison.get("selection_decision_hash")
    ):
        codes.add("RC_FINAL_RESULT_SELECTION_BINDING_MISMATCH")
    manifest_path = case_root / "runs" / str(final_result.get("run_id", "")) / "manifest.json"
    try:
        manifest: Any = load_json(manifest_path) if manifest_path.is_file() else None
    except (OSError, ValueError, json.JSONDecodeError):
        manifest = None
    if not isinstance(manifest, dict):
        codes.add("RC_FINAL_RESULT_MANIFEST_MISSING")
    else:
        configuration = manifest.get("configuration")
        if (
            manifest.get("run_id") != final_result.get("run_id")
            or manifest.get("output_hash") != final_result.get("output_hash")
            or manifest.get("decision_hash") != final_result.get("decision_hash")
            or not isinstance(configuration, dict)
            or configuration.get("candidate_id") != selected
        ):
            codes.add("RC_FINAL_RESULT_MANIFEST_BINDING_MISMATCH")
        output_files = manifest.get("output_files")
        output_path: Path | None = None
        if isinstance(output_files, list) and len(output_files) == 1:
            output_path = relative_case_path(case_root, output_files[0].get("path"))
        if output_path is None or not output_path.is_file():
            codes.add("RC_FINAL_RESULT_OUTPUT_MISSING")
        else:
            try:
                output = load_json(output_path)
            except (OSError, ValueError, json.JSONDecodeError):
                output = None
            if not isinstance(output, dict) or output.get("candidate_id") != selected:
                codes.add("RC_FINAL_RESULT_OUTPUT_BINDING_MISMATCH")
            else:
                expected_metrics = output.get("final_metrics")
                expected_scope = output.get("claim_scope")
                if (
                    not isinstance(expected_metrics, dict)
                    or not expected_metrics
                    or not isinstance(expected_scope, str)
                    or not expected_scope
                ):
                    codes.add("RC_FINAL_RESULT_EVIDENCE_CONTRACT_INVALID")
                elif (
                    final_result.get("final_metrics") != expected_metrics
                    or final_result.get("claim_scope") != expected_scope
                ):
                    codes.add("RC_FINAL_RESULT_METRICS_OR_SCOPE_MISMATCH")
    if (final_result, comparison) != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_FINAL_RESULT_EXACTLY_BOUND")


def validate_robustness(
    robustness: Any,
    comparison: Any,
    *,
    case_root: Path,
) -> GateResult:
    original = copy.deepcopy((robustness, comparison))
    codes: set[str] = set()
    if not isinstance(robustness, dict) or not isinstance(comparison, dict):
        return blocked("RC_ROBUSTNESS_EVIDENCE_INVALID")
    required = {
        "status",
        "selected_model",
        "run_id",
        "input_hash",
        "configuration_hash",
        "output_hash",
        "decision_hash",
        "metric",
        "metric_direction",
        "perturbations",
        "failure_cases",
    }
    if set(robustness) != required:
        codes.add("RC_ROBUSTNESS_FIELDS_INVALID")
    selected = comparison.get("selected_candidate_id")
    attempts = comparison.get("attempts")
    selected_attempts = (
        sorted(
            [
                attempt
                for attempt in attempts
                if isinstance(attempt, dict)
                and attempt.get("candidate_id") == selected
                and attempt.get("outcome") == "SUCCESS"
            ],
            key=lambda item: (str(item.get("random_seed")), str(item.get("run_id"))),
        )
        if isinstance(attempts, list)
        else []
    )
    expected_run_id = selected_attempts[0].get("run_id") if selected_attempts else None
    if (
        robustness.get("status") != "VALIDATED"
        or not isinstance(selected, str)
        or robustness.get("selected_model") != selected
        or not isinstance(expected_run_id, str)
        or robustness.get("run_id") != expected_run_id
        or robustness.get("decision_hash") != comparison.get("selection_decision_hash")
    ):
        codes.add("RC_ROBUSTNESS_SELECTION_BINDING_MISMATCH")
    metric = robustness.get("metric")
    direction = robustness.get("metric_direction")
    perturbations = robustness.get("perturbations")
    if (
        not isinstance(metric, str)
        or not metric
        or direction not in ("MIN", "MAX")
        or not isinstance(perturbations, list)
        or not perturbations
    ):
        codes.add("RC_ROBUSTNESS_METRIC_OR_PERTURBATIONS_INVALID")
    else:
        perturbation_ids: set[str] = set()
        for item in perturbations:
            if not isinstance(item, dict) or set(item) != {
                "perturbation_id",
                "metric",
                "result",
                "evidence",
            }:
                codes.add("RC_ROBUSTNESS_PERTURBATION_INVALID")
                continue
            perturbation_id = item.get("perturbation_id")
            if (
                not isinstance(perturbation_id, str)
                or not perturbation_id
                or perturbation_id in perturbation_ids
                or item.get("metric") != metric
                or not strict_score(item.get("result"))
                or item.get("evidence") != "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS"
            ):
                codes.add("RC_ROBUSTNESS_PERTURBATION_INVALID")
            else:
                perturbation_ids.add(perturbation_id)
    failures = robustness.get("failure_cases")
    if (
        not isinstance(failures, list)
        or not failures
        or not all(isinstance(item, str) and item for item in failures)
    ):
        codes.add("RC_ROBUSTNESS_FAILURE_CASES_INVALID")
    manifest_path = case_root / "runs" / str(expected_run_id or "") / "manifest.json"
    try:
        manifest = load_json(manifest_path) if manifest_path.is_file() else None
    except (OSError, ValueError, json.JSONDecodeError):
        manifest = None
    if not isinstance(manifest, dict):
        codes.add("RC_ROBUSTNESS_MANIFEST_MISSING")
    else:
        configuration = manifest.get("configuration")
        if (
            robustness.get("input_hash") != manifest.get("input_hash")
            or robustness.get("configuration_hash") != manifest.get("configuration_hash")
            or robustness.get("output_hash") != manifest.get("output_hash")
            or robustness.get("decision_hash") != manifest.get("decision_hash")
            or not isinstance(configuration, dict)
            or configuration.get("candidate_id") != selected
        ):
            codes.add("RC_ROBUSTNESS_RUN_BINDING_MISMATCH")
        output_files = manifest.get("output_files")
        output_path = None
        if isinstance(output_files, list) and len(output_files) == 1:
            output_path = relative_case_path(case_root, output_files[0].get("path"))
        try:
            output = (
                load_json(output_path)
                if output_path is not None and output_path.is_file()
                else None
            )
        except (OSError, ValueError, json.JSONDecodeError):
            output = None
        expected_evidence = output.get("robustness_evidence") if isinstance(output, dict) else None
        observed_evidence = {
            name: robustness.get(name)
            for name in ("metric", "metric_direction", "perturbations", "failure_cases")
        }
        if not isinstance(expected_evidence, dict) or observed_evidence != expected_evidence:
            codes.add("RC_ROBUSTNESS_OUTPUT_EVIDENCE_MISMATCH")
    if (robustness, comparison) != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_ROBUSTNESS_EXACTLY_BOUND")


CLAIM_CONTRACT_VERSION = "claim-evidence/v2"
CLAIM_BINDING_FIELDS = (
    "run_id",
    "run_manifest_hash",
    "input_hash",
    "code_hash",
    "configuration_hash",
    "output_hash",
    "decision_hash",
    "evidence_status",
    "contradiction_status",
)
CLAIM_V2_FIELDS = {
    "contract_version",
    "claim_kind",
    "scope_type",
    "aggregate_scope",
    "supporting_requirement_claim_ids",
    "requirement_bindings",
    "non_primary_requirements",
}


def derive_claim_contract(claim: dict[str, Any], requirements: Any) -> dict[str, Any]:
    """Pure legacy migration: derives a bundle; never rewrites the source artifact."""
    derived = copy.deepcopy(claim)
    if "contract_version" in derived:
        return derived
    roles = requirement_roles(requirements)
    records = derived.get("requirement_claims", {})
    if not isinstance(records, dict) or not all(isinstance(v, dict) for v in records.values()):
        raise ValueError("RC_CLAIM_REQUIREMENT_SUPPORT_INVALID")
    # Aggregate identity depends on canonical lineage and coverage, never list position.
    derived["claim_id"] = (
        "CLAIM-AGGREGATE-"
        + canonical_hash(
            {
                "run_id": derived.get("run_id"),
                "decision_hash": derived.get("decision_hash"),
                "requirements": sorted(records),
            }
        )[:24].upper()
    )
    derived.update(
        contract_version=CLAIM_CONTRACT_VERSION,
        claim_kind="AGGREGATE_FINAL",
        scope_type="REQUIREMENT_UNION",
        aggregate_scope={key: record.get("claim_text") for key, record in records.items()},
        supporting_requirement_claim_ids=[record.get("claim_id") for record in records.values()],
        requirement_bindings={
            key: {
                **{field: derived.get(field) for field in CLAIM_BINDING_FIELDS},
                "claim_kind": "REQUIREMENT",
                "requirement_id": key,
                "status": "ACCEPTED",
            }
            for key in records
        },
        non_primary_requirements={
            key: {"role": role, "status": "NOT_CLAIMED"}
            for key, role in roles.items()
            if role != "PRIMARY"
        },
    )
    return derived


def validate_aggregate_claim(claim: dict[str, Any], requirements: Any) -> set[str]:
    """Exact coverage and scope containment, with no natural-language identity shortcut."""
    codes: set[str] = set()
    try:
        roles = requirement_roles(requirements)
        value = derive_claim_contract(claim, requirements)
    except (KeyError, TypeError, ValueError):
        return {"RC_CLAIM_REQUIREMENT_COVERAGE_INVALID"}
    primary = {key for key, role in roles.items() if role == "PRIMARY"}
    records = value.get("requirement_claims")
    if not isinstance(records, dict):
        return {"RC_CLAIM_PRIMARY_REQUIREMENT_MISSING"}
    if primary - set(records):
        codes.add("RC_CLAIM_PRIMARY_REQUIREMENT_MISSING")
    if set(records) - primary:
        codes.add("RC_CLAIM_PRIMARY_REQUIREMENT_UNKNOWN")
    nested_ids = [
        record.get("claim_id") if isinstance(record, dict) else None for record in records.values()
    ]
    ids_valid = all(isinstance(item, str) and item for item in nested_ids)
    if not ids_valid or len(set(nested_ids)) != len(nested_ids):
        codes.add("RC_CLAIM_PRIMARY_REQUIREMENT_DUPLICATE")
    if value.get("claim_id") in nested_ids:
        codes.add("RC_CLAIM_AGGREGATE_ID_COLLISION")
    coverage = value.get("supported_requirement_ids")
    support = value.get("supporting_requirement_claim_ids")

    def exact_set(items: Any, expected: set[str]) -> bool:
        return (
            isinstance(items, list)
            and all(isinstance(item, str) for item in items)
            and len(items) == len(set(items))
            and set(items) == expected
        )

    if (
        not exact_set(coverage, primary)
        or not ids_valid
        or not exact_set(support, set(nested_ids) if ids_valid else set())
    ):
        codes.add("RC_CLAIM_AGGREGATE_COVERAGE_INVALID")
    expected_scope = {
        key: record.get("claim_text") for key, record in records.items() if isinstance(record, dict)
    }
    if (
        value.get("contract_version") != CLAIM_CONTRACT_VERSION
        or value.get("claim_kind") != "AGGREGATE_FINAL"
        or value.get("scope_type") != "REQUIREMENT_UNION"
        or value.get("aggregate_scope") != expected_scope
    ):
        codes.add("RC_CLAIM_AGGREGATE_SCOPE_OVERREACH")
    expected_auxiliary = {
        key: {"role": role, "status": "NOT_CLAIMED"}
        for key, role in roles.items()
        if role != "PRIMARY"
    }
    if value.get("non_primary_requirements") != expected_auxiliary:
        codes.add("RC_CLAIM_NON_PRIMARY_REQUIREMENT_STATUS_INVALID")
    bindings = value.get("requirement_bindings")
    if not isinstance(bindings, dict) or set(bindings) != primary:
        codes.add("RC_CLAIM_PRIMARY_REQUIREMENT_MISSING")
    else:
        reasons = {
            "output_hash": "RC_CLAIM_OUTPUT_BINDING_MISMATCH",
            "run_manifest_hash": "RC_CLAIM_MANIFEST_HASH_MISMATCH",
            "decision_hash": "RC_CLAIM_FINAL_DECISION_BINDING_MISMATCH",
            "evidence_status": "RC_CLAIM_EVIDENCE_STALE",
            "contradiction_status": "RC_CLAIM_CONTRADICTED",
        }
        for key, binding in bindings.items():
            if not isinstance(binding, dict) or set(binding) != set(CLAIM_BINDING_FIELDS) | {
                "claim_kind",
                "requirement_id",
                "status",
            }:
                codes.add("RC_CLAIM_REQUIREMENT_SUPPORT_INVALID")
                continue
            if (
                binding.get("requirement_id") != key
                or binding.get("claim_kind") != "REQUIREMENT"
                or binding.get("status") != "ACCEPTED"
            ):
                codes.add("RC_CLAIM_REQUIREMENT_SUPPORT_INVALID")
            for field in CLAIM_BINDING_FIELDS:
                if binding.get(field) != claim.get(field):
                    codes.add(reasons.get(field, "RC_CLAIM_RUN_BINDING_MISMATCH"))
            if binding.get("evidence_status") != "CURRENT":
                codes.add("RC_CLAIM_EVIDENCE_STALE")
            if binding.get("contradiction_status") != "NONE":
                codes.add("RC_CLAIM_CONTRADICTED")
    if codes:
        codes.add("RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID")
    return codes


def validate_claim(
    claim: Any,
    manifest: Any | None = None,
    final_result: Any | None = None,
    *,
    case_root: Path | None = None,
    state: dict[str, Any] | None = None,
) -> GateResult:
    original = copy.deepcopy((claim, manifest, final_result))
    codes: set[str] = set()
    if not isinstance(claim, dict):
        return blocked("RC_CLAIM_INVALID")
    required = {
        "claim_id",
        "claim_text",
        "supported_scope",
        "run_id",
        "run_manifest_hash",
        "input_hash",
        "code_hash",
        "configuration_hash",
        "output_hash",
        "decision_hash",
        "evidence_artifact_ids",
        "supported_requirement_ids",
        "requirement_claims",
        "evidence_status",
        "contradiction_status",
    }
    if "contract_version" in claim:
        required |= CLAIM_V2_FIELDS
    if set(claim) != required:
        codes.add("RC_CLAIM_REQUIRED_BINDING_MISSING")
    try:
        assert_json_safe(claim)
    except (TypeError, ValueError):
        codes.add("RC_CLAIM_NONFINITE_OR_NONJSON")
    codes.update(sensitive_findings(claim))
    claim_id = claim.get("claim_id")
    if not isinstance(claim_id, str) or not re.fullmatch(
        r"CLAIM-[A-Z0-9][A-Z0-9_-]{0,63}", claim_id
    ):
        codes.add("RC_CLAIM_ID_INVALID")
    if (
        not isinstance(claim.get("claim_text"), str)
        or not claim.get("claim_text")
        or not isinstance(claim.get("supported_scope"), str)
        or not claim.get("supported_scope")
        or not isinstance(claim.get("run_id"), str)
        or not claim.get("run_id")
    ):
        codes.add("RC_CLAIM_IDENTITY_OR_SCOPE_INVALID")
    for name in (
        "run_manifest_hash",
        "input_hash",
        "code_hash",
        "configuration_hash",
        "output_hash",
        "decision_hash",
    ):
        if not HEX64.fullmatch(str(claim.get(name, ""))):
            codes.add(f"RC_CLAIM_HASH_INVALID:{name}")
    if claim.get("evidence_status") != "CURRENT":
        codes.add("RC_CLAIM_STALE_EVIDENCE")
    if claim.get("contradiction_status") != "NONE":
        codes.add("RC_CLAIM_CONTRADICTED")
    if claim.get("claim_text") != claim.get("supported_scope"):
        codes.add("RC_CLAIM_OVERBROAD_OR_UNSUPPORTED")
    artifacts = claim.get("evidence_artifact_ids")
    if (
        not isinstance(artifacts, list)
        or not artifacts
        or not all(isinstance(item, str) and item for item in artifacts)
        or len(set(artifacts)) != len(artifacts)
    ):
        codes.add("RC_CLAIM_EXACT_SUPPORT_MISSING")
    if manifest is not None:
        if not isinstance(manifest, dict):
            codes.add("RC_CLAIM_MANIFEST_INVALID")
        else:
            bindings = {
                "run_id": "run_id",
                "input_hash": "input_hash",
                "code_hash": "code_tree_hash",
                "configuration_hash": "configuration_hash",
                "output_hash": "output_hash",
                "decision_hash": "decision_hash",
            }
            if any(claim.get(left) != manifest.get(right) for left, right in bindings.items()):
                codes.add("RC_CLAIM_RUN_BINDING_MISMATCH")
            try:
                actual_manifest_hash = canonical_hash(manifest)
            except (TypeError, ValueError):
                actual_manifest_hash = None
                codes.add("RC_CLAIM_MANIFEST_NONFINITE_OR_NONJSON")
            if claim.get("run_manifest_hash") != actual_manifest_hash:
                codes.add("RC_CLAIM_MANIFEST_HASH_MISMATCH")
            if manifest.get("outcome") != "SUCCESS" or manifest.get("supersession") is not None:
                codes.add("RC_CLAIM_RUN_NOT_CURRENT_SUCCESS")
            if manifest.get("trusted_capture") is not True:
                codes.add("RC_CLAIM_RUN_UNSEALED")
    if final_result is not None:
        if not isinstance(final_result, dict) or any(
            claim.get(name) != final_result.get(name)
            for name in ("run_id", "output_hash", "decision_hash")
        ):
            codes.add("RC_CLAIM_FINAL_RESULT_BINDING_MISMATCH")
        elif claim.get("claim_text") != final_result.get("claim_scope") or claim.get(
            "supported_scope"
        ) != final_result.get("claim_scope"):
            codes.add("RC_CLAIM_FINAL_SCOPE_MISMATCH")
    if case_root is None or state is None or not isinstance(manifest, dict):
        codes.add("RC_CLAIM_EVIDENCE_CONTEXT_MISSING")
    else:
        output_files = manifest.get("output_files")
        expected_artifacts = {
            ARTIFACT_PATHS["model_comparison"],
            ARTIFACT_PATHS["robustness_analysis"],
            ARTIFACT_PATHS["final_result"],
        }
        if isinstance(output_files, list):
            expected_artifacts.update(
                item.get("path")
                for item in output_files
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            )
        if (
            not isinstance(artifacts, list)
            or not all(isinstance(item, str) for item in artifacts)
            or set(artifacts) != expected_artifacts
        ):
            codes.add("RC_CLAIM_EVIDENCE_REGISTRY_MISMATCH")
        bindings = state.get("evidence_bindings") if isinstance(state, dict) else None
        if not isinstance(bindings, dict):
            codes.add("RC_CLAIM_STATE_EVIDENCE_INVALID")
        else:
            for relative in artifacts if isinstance(artifacts, list) else []:
                path = relative_case_path(case_root, relative)
                if path is None or not path.is_file() or bindings.get(relative) != file_hash(path):
                    codes.add("RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING")
        try:
            requirements = read_artifact(case_root, "problem_requirements")["content"].get(
                "requirements"
            )
            output_files = manifest.get("output_files")
            selected_output_path = (
                relative_case_path(case_root, output_files[0].get("path"))
                if isinstance(output_files, list) and len(output_files) == 1
                else None
            )
            selected_output = (
                load_json(selected_output_path)
                if selected_output_path is not None and selected_output_path.is_file()
                else None
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            requirements = None
            selected_output = None
        try:
            roles = requirement_roles(requirements)
            requirement_ids = sorted(key for key, role in roles.items() if role == "PRIMARY")
        except (TypeError, ValueError):
            requirement_ids = []
        codes.update(validate_aggregate_claim(claim, requirements))
        if isinstance(selected_output, dict) and (
            claim.get("claim_text") != selected_output.get("claim_scope")
            or claim.get("supported_scope") != selected_output.get("claim_scope")
        ):
            codes.add("RC_CLAIM_FINAL_SCOPE_MISMATCH")
        requirement_claims = claim.get("requirement_claims")
        supported_requirement_ids = claim.get("supported_requirement_ids")
        expected_requirement_claims = (
            selected_output.get("requirement_claims") if isinstance(selected_output, dict) else None
        )
        if (
            not requirement_ids
            or not all(isinstance(item, str) and item for item in requirement_ids)
            or len(set(requirement_ids)) != len(requirement_ids)
            or not isinstance(supported_requirement_ids, list)
            or not all(isinstance(item, str) for item in supported_requirement_ids)
            or len(supported_requirement_ids) != len(set(supported_requirement_ids))
            or set(supported_requirement_ids) != set(requirement_ids)
            or not isinstance(requirement_claims, dict)
            or set(requirement_claims) != set(requirement_ids)
            or requirement_claims != expected_requirement_claims
        ):
            codes.add("RC_CLAIM_REQUIREMENT_COVERAGE_INVALID")
            if requirement_claims != expected_requirement_claims:
                codes.add("RC_CLAIM_OUTPUT_BINDING_MISMATCH")
        else:
            nested_claim_ids: set[str] = set()
            for requirement_id in requirement_ids:
                record = requirement_claims.get(requirement_id)
                if not isinstance(record, dict) or set(record) != {
                    "claim_id",
                    "claim_text",
                    "evidence_artifact_ids",
                }:
                    codes.add("RC_CLAIM_REQUIREMENT_SUPPORT_INVALID")
                    continue
                nested_id = record.get("claim_id")
                nested_text = record.get("claim_text")
                nested_evidence = record.get("evidence_artifact_ids")
                if (
                    not isinstance(nested_id, str)
                    or not re.fullmatch(r"CLAIM-[A-Z0-9][A-Z0-9_-]{0,63}", nested_id)
                    or nested_id in nested_claim_ids
                    or not isinstance(nested_text, str)
                    or not nested_text
                    or not isinstance(nested_evidence, list)
                    or not nested_evidence
                    or not all(isinstance(item, str) and item for item in nested_evidence)
                    or len(set(nested_evidence)) != len(nested_evidence)
                ):
                    codes.add("RC_CLAIM_REQUIREMENT_SUPPORT_INVALID")
                    continue
                nested_claim_ids.add(nested_id)
                for relative in nested_evidence:
                    path = relative_case_path(case_root, relative)
                    if (
                        path is None
                        or not path.is_file()
                        or not isinstance(bindings, dict)
                        or bindings.get(relative) != file_hash(path)
                    ):
                        codes.add("RC_CLAIM_REQUIREMENT_EVIDENCE_NOT_CURRENT")
        if isinstance(bindings, dict):
            # Detect mutations even when a changed file is not explicitly cited by the Claim.
            for relative, digest in bindings.items():
                path = relative_case_path(case_root, relative)
                if path is None or not path.is_file() or file_hash(path) != digest:
                    codes.add("RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING")
        if isinstance(output_files, list):
            hashes = []
            for item in output_files:
                if not isinstance(item, dict):
                    codes.add("RC_CLAIM_OUTPUT_BINDING_MISMATCH")
                    continue
                path = relative_case_path(case_root, item.get("path"))
                if path is None or not path.is_file() or file_hash(path) != item.get("sha256"):
                    codes.add("RC_CLAIM_OUTPUT_BINDING_MISMATCH")
                hashes.append(item.get("sha256"))
            if canonical_hash(hashes) != manifest.get("output_hash"):
                codes.add("RC_CLAIM_OUTPUT_BINDING_MISMATCH")
    if (claim, manifest, final_result) != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_CLAIM_EXACT_SUPPORT_VALID")


def validate_state_boundary(context: Any) -> GateResult:
    if not isinstance(context, dict):
        return blocked("RC_STATE_CONTEXT_INVALID")
    codes: set[str] = set()
    allowed = {
        "writer",
        "formal_project_state_write",
        "second_state_truth",
        "execution_scope",
        "state_path",
        "isolated_state_binding_hash",
    }
    if set(context) != allowed:
        codes.add("RC_EXTRA_OR_MISSING_STATE_AUTHORITY_REJECTED")
    if context.get("writer") != "modeling_orchestrator":
        codes.add("RC_STATE_UNAUTHORIZED_WRITER")
    if context.get("formal_project_state_write") is not False:
        codes.add("RC_FORMAL_STATE_WRITE_PROHIBITED")
    if context.get("second_state_truth") is not False:
        codes.add("RC_SECOND_STATE_TRUTH_PROHIBITED")
    if context.get("execution_scope") != "CASE":
        codes.add("RC_CONTEXT_EXECUTION_SCOPE_PROHIBITED")
    if context.get("state_path") != "case_state.json":
        codes.add("RC_CASE_STATE_BINDING_INVALID")
    body = {key: value for key, value in context.items() if key != "isolated_state_binding_hash"}
    try:
        expected_binding_hash = canonical_hash(body)
    except (TypeError, ValueError):
        expected_binding_hash = None
        codes.add("RC_STATE_CONTEXT_NONFINITE_OR_NONJSON")
    if context.get("isolated_state_binding_hash") != expected_binding_hash:
        codes.add("RC_ISOLATED_STATE_BINDING_INVALID")
    return blocked(*codes) if codes else passed("RC_CASE_STATE_BOUNDARY_VALID")


def normalize_handoff_formulas(formulas: list[Any], requirements: Any) -> list[dict[str, Any]]:
    """Preserve captured formula identity and requirement scope without altering expressions."""
    known = set(requirement_roles(requirements))
    result: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, formula in enumerate(formulas, 1):
        if isinstance(formula, str) and formula.strip():
            record = {"formula_id": f"F-{index:03d}", "expression": formula}
        elif isinstance(formula, dict) and set(formula) == {
            "formula_id",
            "expression",
            "requirements",
        }:
            references = formula.get("requirements")
            if (
                not isinstance(references, list)
                or not references
                or not all(isinstance(item, str) and item for item in references)
                or len(references) != len(set(references))
                or set(references) - known
            ):
                raise ValueError("RC_HANDOFF_FORMULA_SCOPE_INVALID")
            record = copy.deepcopy(formula)
        else:
            raise ValueError("RC_HANDOFF_FORMULA_SCOPE_INVALID")
        if (
            not isinstance(record.get("formula_id"), str)
            or not record["formula_id"].strip()
            or record["formula_id"] in identifiers
            or not isinstance(record.get("expression"), str)
            or not record["expression"].strip()
        ):
            raise ValueError("RC_HANDOFF_FORMULA_SCOPE_INVALID")
        identifiers.add(record["formula_id"])
        result.append(record)
    return result


def build_runtime_handoff(case_root: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical multi-Run handoff from validated runtime artifacts."""
    requirements = read_artifact(case_root, "problem_requirements")["content"]["requirements"]
    sources = read_artifact(case_root, "source_ledger")["content"]["sources"]
    audit = read_artifact(case_root, "data_audit")["content"]
    sufficiency = read_artifact(case_root, "data_sufficiency")["content"]
    assumptions = read_artifact(case_root, "assumptions_and_symbols")["content"]
    candidates = read_artifact(case_root, "model_candidates")["content"]["candidates"]
    plan = read_artifact(case_root, "experiment_plan")["content"]
    comparison = read_artifact(case_root, "model_comparison")["content"]
    selection_record = read_artifact(case_root, "requirement_selection")["content"]
    robustness = read_artifact(case_root, "robustness_analysis")["content"]
    final_result = read_artifact(case_root, "final_result")["content"]
    claim_evidence = read_artifact(case_root, "claim_evidence")["content"]
    semantic = read_artifact(case_root, "semantic_claim_support")["content"]
    selected_run_ids = final_result["selected_run_ids"]
    manifests = {
        run_id: load_json(case_root / "runs" / run_id / "manifest.json")
        for run_id in selected_run_ids
    }
    outputs: dict[str, dict[str, Any]] = {}
    for run_id, manifest in manifests.items():
        output_files = manifest.get("output_files")
        if not isinstance(output_files, list) or len(output_files) != 1:
            raise ValueError("RC_HANDOFF_SELECTED_OUTPUT_INVALID")
        output_path = relative_case_path(case_root, output_files[0].get("path"))
        if output_path is None or not output_path.is_file():
            raise ValueError("RC_HANDOFF_SELECTED_OUTPUT_INVALID")
        output = load_json(output_path)
        if not isinstance(output, dict):
            raise ValueError("RC_HANDOFF_SELECTED_OUTPUT_INVALID")
        outputs[run_id] = output
    selected_candidate_ids = {
        manifests[run_id].get("configuration", {}).get("candidate_id")
        for run_id in selected_run_ids
    }
    selected_models = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and candidate.get("candidate_id") in selected_candidate_ids
    ]
    claims = {
        item["requirement_id"]: item
        for item in semantic["claims"]
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    requirement_traceability = {
        requirement_id: claim["claim_id"] for requirement_id, claim in sorted(claims.items())
    }
    final_metrics = {
        requirement_id: {
            run_id: outputs[run_id]["final_metrics"] for run_id in claim["selected_run_ids"]
        }
        for requirement_id, claim in sorted(claims.items())
    }
    figure_ready_data = [
        {"run_id": run_id, "figures": outputs[run_id]["figure_ready_data"]}
        for run_id in selected_run_ids
    ]
    limitations = sorted(
        {
            limitation
            for output in outputs.values()
            for limitation in output.get("limitations", [])
            if isinstance(limitation, str)
        }
        | {
            limitation
            for claim in claims.values()
            for limitation in claim.get("limitations", [])
            if isinstance(limitation, str)
        }
        | {
            limitation
            for limitation in final_result.get("limitations", [])
            if isinstance(limitation, str)
        }
    )
    formulas = normalize_handoff_formulas(assumptions.get("formulas"), requirements)
    claim_records = {
        claim["claim_id"]: {
            "requirement_id": requirement_id,
            "claim_type": claim["claim_type"],
            "statement": claim["statement"],
            "scope": claim["scope"],
            "selected_run_ids": claim["selected_run_ids"],
            "selected_output_ids": claim["selected_output_ids"],
            "metric_ids": claim["metric_ids"],
            "evidence_class": claim["evidence_class"],
            "status": claim["status"],
            "runtime_binding": claim_evidence["claims"][requirement_id],
        }
        for requirement_id, claim in sorted(claims.items())
    }
    return {
        "contract_version": "modeling-to-paper/v1",
        "problem_requirements": requirements,
        "requirement_traceability": requirement_traceability,
        "data_dictionary": {
            "case_kind": state.get("case_kind"),
            "raw_files": sorted(audit.get("raw_data_hashes", audit["data_hashes"])),
        },
        "data_quality_report": {**copy.deepcopy(audit), "data_sufficiency": sufficiency},
        "assumptions": assumptions["assumptions"],
        "symbols": assumptions["symbols"],
        "formulas": formulas,
        "sources": sources,
        "selected_models": selected_models,
        "final_runs": [
            {
                "run_id": run_id,
                "manifest_hash": canonical_hash(manifests[run_id]),
                "output_hash": manifests[run_id]["output_hash"],
                "requirement_ids": final_result["run_bindings"][run_id]["requirement_ids"],
            }
            for run_id in selected_run_ids
        ],
        "final_metrics": final_metrics,
        "result_tables": [{"table_id": "MODEL_COMPARISON", "rows": comparison["attempts"]}],
        "figure_ready_data": figure_ready_data,
        "validation_results": {
            "data_sufficiency_status": "SUFFICIENT",
            "requirement_selection": selection_record["selection"],
            "semantic_claim_support": semantic,
            "aggregate_claim": claim_evidence["aggregate"],
            "comparison_decision_hash": final_result["decision_hash"],
            "test_used_for_selection": comparison["test_access"]["used_for_selection"],
        },
        "robustness_results": robustness,
        "uncertainty": {
            requirement_id: claim["uncertainty"] for requirement_id, claim in sorted(claims.items())
        },
        "failure_cases": robustness["failure_cases"],
        "limitations": limitations,
        "claim_evidence": claim_records,
        "reproduction": {
            "skill_version": VERSION,
            "architecture": ARCHITECTURE,
            "run_manifest_hashes": {
                run_id: canonical_hash(manifest) for run_id, manifest in sorted(manifests.items())
            },
            "offline": True,
        },
        "generated_at": plan["handoff_generated_at"],
        "approved_by": ["MACHINE_TECHNICAL_GATES"],
    }


def build_expected_handoff(case_root: Path, state: dict[str, Any]) -> dict[str, Any]:
    final_probe = read_artifact(case_root, "final_result")["content"]
    if final_probe.get("contract_version") == "final-result/v2":
        return build_runtime_handoff(case_root, state)
    requirements = read_artifact(case_root, "problem_requirements")["content"]["requirements"]
    audit = read_artifact(case_root, "data_audit")["content"]
    assumptions = read_artifact(case_root, "assumptions_and_symbols")["content"]
    sources = read_artifact(case_root, "source_ledger")["content"]["sources"]
    candidates = read_artifact(case_root, "model_candidates")["content"]["candidates"]
    plan = read_artifact(case_root, "experiment_plan")["content"]
    comparison = read_artifact(case_root, "model_comparison")["content"]
    robustness = read_artifact(case_root, "robustness_analysis")["content"]
    final = read_artifact(case_root, "final_result")["content"]
    claim = read_artifact(case_root, "claim_evidence")["content"]
    requirement_claims = claim["requirement_claims"]
    aggregate = derive_claim_contract(claim, requirements)
    aggregate_codes = validate_aggregate_claim(claim, requirements)
    if aggregate_codes:
        raise ValueError("RC_HANDOFF_CLAIM_COVERAGE_INVALID")
    primary_ids = sorted(
        key for key, role in requirement_roles(requirements).items() if role == "PRIMARY"
    )
    selected = final["selected_model"]
    selected_candidates = [item for item in candidates if item.get("candidate_id") == selected]
    manifest_path = case_root / "runs" / str(final["run_id"]) / "manifest.json"
    manifest = load_json(manifest_path)
    output_files = manifest.get("output_files")
    if not isinstance(output_files, list) or len(output_files) != 1:
        raise ValueError("RC_HANDOFF_SELECTED_OUTPUT_INVALID")
    output_path = relative_case_path(case_root, output_files[0].get("path"))
    if output_path is None or not output_path.is_file():
        raise ValueError("RC_HANDOFF_SELECTED_OUTPUT_INVALID")
    output = load_json(output_path)
    case_kind = state.get("case_kind")
    formulas_raw = assumptions.get("formulas")
    figures = output.get("figure_ready_data") if isinstance(output, dict) else None
    limitations = output.get("limitations") if isinstance(output, dict) else None
    uncertainty = output.get("uncertainty") if isinstance(output, dict) else None
    if (
        not isinstance(formulas_raw, list)
        or not formulas_raw
        or not isinstance(figures, list)
        or not figures
        or not isinstance(limitations, list)
        or not limitations
        or not all(isinstance(item, str) and item for item in limitations)
        or not isinstance(uncertainty, dict)
        or not uncertainty
        or not isinstance(plan.get("handoff_generated_at"), str)
        or not plan["handoff_generated_at"]
    ):
        raise ValueError("RC_HANDOFF_OUTPUT_EVIDENCE_CONTRACT_INVALID")
    formulas = normalize_handoff_formulas(formulas_raw, requirements)
    rc6_validation: dict[str, Any] = {}
    data_quality_report = copy.deepcopy(audit)
    data_sufficiency_path = case_root / ARTIFACT_PATHS["data_sufficiency"]
    selection_path = case_root / ARTIFACT_PATHS["requirement_selection"]
    semantic_path = case_root / ARTIFACT_PATHS["semantic_claim_support"]
    if data_sufficiency_path.is_file():
        data_sufficiency = read_artifact(case_root, "data_sufficiency")["content"]
        sufficiency_result = validate_data_sufficiency_record(
            data_sufficiency,
            requirements=requirements,
            sources=sources,
        )
        if sufficiency_result.get("status") not in {"SUFFICIENT", "PARTIAL"}:
            raise ValueError("RC_HANDOFF_DATA_SUFFICIENCY_INVALID")
        data_quality_report["data_sufficiency"] = data_sufficiency
        rc6_validation["data_sufficiency_status"] = sufficiency_result["status"]
    if selection_path.is_file():
        requirement_selection = read_artifact(case_root, "requirement_selection")["content"]
        if validate_requirement_selection(requirement_selection).get("status") != "PASS":
            raise ValueError("RC_HANDOFF_REQUIREMENT_SELECTION_INVALID")
        rc6_validation["requirement_selection"] = requirement_selection["selection"]
    if semantic_path.is_file():
        semantic_claim_support = read_artifact(case_root, "semantic_claim_support")["content"]
        if validate_semantic_claim_bundle(semantic_claim_support).get("status") != "PASS":
            raise ValueError("RC_HANDOFF_SEMANTIC_CLAIM_SUPPORT_INVALID")
        rc6_validation["semantic_claim_support"] = semantic_claim_support
    return {
        "contract_version": "modeling-to-paper/v1",
        "problem_requirements": requirements,
        "requirement_traceability": {
            requirement_id: requirement_claims[requirement_id]["claim_id"]
            for requirement_id in primary_ids
        },
        "data_dictionary": {
            "case_kind": case_kind,
            "raw_files": sorted(audit.get("raw_data_hashes", audit["data_hashes"])),
        },
        "data_quality_report": data_quality_report,
        "assumptions": assumptions["assumptions"],
        "symbols": assumptions["symbols"],
        "formulas": formulas,
        "sources": sources,
        "selected_models": selected_candidates,
        "final_runs": [
            {
                "run_id": manifest["run_id"],
                "manifest_hash": canonical_hash(manifest),
                "output_hash": manifest["output_hash"],
            }
        ],
        "final_metrics": final["final_metrics"],
        "result_tables": [{"table_id": "MODEL_COMPARISON", "rows": comparison["attempts"]}],
        "figure_ready_data": figures,
        "validation_results": {
            **rc6_validation,
            "comparison_decision_hash": final["decision_hash"],
            "aggregate_claim": {
                "aggregate_claim_id": aggregate["claim_id"],
                "claim_kind": "AGGREGATE_FINAL",
                "contract_version": CLAIM_CONTRACT_VERSION,
                "statement": aggregate["claim_text"],
                "scope_type": aggregate["scope_type"],
                "scope": aggregate["aggregate_scope"],
                "covered_primary_requirement_ids": primary_ids,
                "supporting_requirement_claim_ids": sorted(
                    aggregate["supporting_requirement_claim_ids"]
                ),
                "final_decision_hash": claim["decision_hash"],
                "selected_run_ids": [claim["run_id"]],
                "selected_manifest_hashes": [claim["run_manifest_hash"]],
                "selected_output_hashes": [claim["output_hash"]],
                "limitations": limitations,
                "non_primary_requirements": aggregate["non_primary_requirements"],
                "status": "ACCEPTED",
            },
            "selected_model": selected,
            "test_used_for_selection": comparison["test_access"]["used_for_selection"],
        },
        "robustness_results": robustness,
        "uncertainty": uncertainty,
        "failure_cases": robustness["failure_cases"],
        "limitations": limitations,
        "claim_evidence": {
            record["claim_id"]: {
                "claim_kind": "REQUIREMENT",
                "requirement_id": requirement_id,
                "claim_text": record["claim_text"],
                "scope": record["claim_text"],
                "status": "ACCEPTED",
                "limitations": limitations,
                "run_id": claim["run_id"],
                "run_manifest_hash": claim["run_manifest_hash"],
                "input_hash": claim["input_hash"],
                "code_hash": claim["code_hash"],
                "configuration_hash": claim["configuration_hash"],
                "output_hash": claim["output_hash"],
                "decision_hash": claim["decision_hash"],
                "evidence_artifact_ids": record["evidence_artifact_ids"],
                "evidence_status": claim["evidence_status"],
                "contradiction_status": claim["contradiction_status"],
            }
            for requirement_id, record in requirement_claims.items()
        },
        "reproduction": {
            "skill_version": VERSION,
            "architecture": ARCHITECTURE,
            "run_manifest_hash": canonical_hash(manifest),
            "offline": True,
        },
        "generated_at": plan["handoff_generated_at"],
        "approved_by": ["MACHINE_TECHNICAL_GATES"],
    }


def validate_handoff(
    handoff: Any,
    *,
    case_root: Path | None = None,
    state: dict[str, Any] | None = None,
) -> GateResult:
    if not isinstance(handoff, dict):
        return blocked("RC_HANDOFF_INVALID")
    codes: set[str] = set()
    if REQUIRED_HANDOFF_FIELDS - set(handoff):
        codes.add("RC_HANDOFF_REQUIRED_FIELDS_MISSING")
    if set(handoff) - REQUIRED_HANDOFF_FIELDS:
        codes.add("RC_HANDOFF_ADDITIONAL_FIELDS_REJECTED")
    if handoff.get("contract_version") != "modeling-to-paper/v1":
        codes.add("RC_HANDOFF_CONTRACT_VERSION_INVALID")
    if handoff.get("approved_by") != ["MACHINE_TECHNICAL_GATES"]:
        codes.add("RC_HANDOFF_APPROVAL_SCOPE_INVALID")
    if not isinstance(handoff.get("final_runs"), list) or not handoff.get("final_runs"):
        codes.add("RC_HANDOFF_FINAL_RUNS_MISSING")
    if not isinstance(handoff.get("claim_evidence"), dict) or not handoff.get("claim_evidence"):
        codes.add("RC_HANDOFF_CLAIM_EVIDENCE_MISSING")
    try:
        assert_json_safe(handoff)
    except (TypeError, ValueError):
        codes.add("RC_HANDOFF_NONFINITE_OR_NONJSON")
    codes.update(sensitive_findings(handoff))
    if case_root is None or state is None:
        codes.add("RC_HANDOFF_EVIDENCE_CONTEXT_MISSING")
    else:
        try:
            expected = build_expected_handoff(case_root, state)
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            expected = None
            codes.add("RC_HANDOFF_EVIDENCE_CHAIN_INVALID")
        if handoff != expected:
            codes.add("RC_HANDOFF_CANONICAL_BINDING_MISMATCH")
        expected_paths = {
            ARTIFACT_PATHS["problem_requirements"],
            ARTIFACT_PATHS["source_ledger"],
            ARTIFACT_PATHS["assumptions_and_symbols"],
            ARTIFACT_PATHS["data_audit"],
            ARTIFACT_PATHS["model_candidates"],
            ARTIFACT_PATHS["experiment_plan"],
            ARTIFACT_PATHS["model_comparison"],
            ARTIFACT_PATHS["robustness_analysis"],
            ARTIFACT_PATHS["final_result"],
            ARTIFACT_PATHS["claim_evidence"],
        }
        if (
            isinstance(expected, dict)
            and isinstance(expected.get("reproduction"), dict)
            and "run_manifest_hashes" in expected["reproduction"]
        ):
            expected_paths.update(
                {
                    ARTIFACT_PATHS["data_sufficiency"],
                    ARTIFACT_PATHS["requirement_selection"],
                    ARTIFACT_PATHS["semantic_claim_support"],
                }
            )
        bindings = state.get("evidence_bindings", {})
        if not isinstance(bindings, dict) or expected_paths - set(bindings):
            codes.add("RC_HANDOFF_STATE_EVIDENCE_CHAIN_INVALID")
        else:
            for relative in expected_paths:
                path = case_root / relative
                if not path.is_file() or bindings.get(relative) != file_hash(path):
                    codes.add("RC_HANDOFF_STATE_EVIDENCE_CHAIN_INVALID")
    return blocked(*codes) if codes else passed("RC_MODELING_TO_PAPER_HANDOFF_VALID")


def state_path(case_root: Path) -> Path:
    return case_root / "case_state.json"


def validate_case_state(value: Any) -> GateResult:
    if not isinstance(value, dict):
        return blocked("RC_CASE_STATE_INVALID")
    codes = sensitive_findings(value)
    current = value.get("state")
    allowed_fields = STATE_FIELDS | ({"stale"} if current == "STALE" else set())
    if set(value) != allowed_fields:
        codes.add("RC_CASE_STATE_FIELDS_INVALID")
    if (
        value.get("schema_version") != "1.0.0"
        or not isinstance(value.get("case_id"), str)
        or not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,63}", value.get("case_id", ""))
        or value.get("case_kind") not in ("prediction", "optimization", "general")
        or value.get("skill_version") != VERSION
        or value.get("capability") != CAPABILITY
        or value.get("architecture") != ARCHITECTURE
        or current not in (*STATES, *TERMINAL_STATES)
    ):
        codes.add("RC_CASE_STATE_IDENTITY_INVALID")
    bindings = value.get("evidence_bindings")
    if not isinstance(bindings, dict):
        codes.add("RC_CASE_STATE_EVIDENCE_BINDINGS_INVALID")
        bindings = {}
    else:
        for relative, digest in bindings.items():
            if (
                not isinstance(relative, str)
                or relative_case_path(Path("."), relative) is None
                or not HEX64.fullmatch(str(digest))
            ):
                codes.add("RC_CASE_STATE_EVIDENCE_BINDINGS_INVALID")
    history = value.get("history")
    if not isinstance(history, list) or not history:
        codes.add("RC_CASE_STATE_HISTORY_INVALID")
        history = []
    terminal = current in tuple(TERMINAL_STATES)
    normal_history = history[:-1] if terminal and history else history
    expected_states: list[str] = []
    if normal_history:
        normal_current = (
            normal_history[-1].get("to") if isinstance(normal_history[-1], dict) else None
        )
        if normal_current in STATES:
            expected_states = list(STATES[: STATES.index(normal_current) + 1])
    if len(normal_history) != len(expected_states):
        codes.add("RC_CASE_STATE_HISTORY_INVALID")
    if not terminal and (
        not normal_history
        or not isinstance(normal_history[-1], dict)
        or normal_history[-1].get("to") != current
    ):
        codes.add("RC_CASE_STATE_HISTORY_INVALID")
    evidence_in_history: set[str] = set()
    for index, record in enumerate(normal_history):
        target = expected_states[index] if index < len(expected_states) else None
        previous = (
            expected_states[index - 1] if index and index - 1 < len(expected_states) else None
        )
        if (
            not isinstance(record, dict)
            or set(record) != {"sequence", "from", "to", "gate", "status", "evidence"}
            or record.get("sequence") != index
            or record.get("from") != previous
            or record.get("to") != target
            or record.get("gate") != TRANSITION_GATES.get(str(target))
            or record.get("status") != "PASS"
            or not isinstance(record.get("evidence"), list)
            or not all(isinstance(item, str) for item in record.get("evidence", []))
        ):
            codes.add("RC_CASE_STATE_HISTORY_INVALID")
            continue
        evidence_in_history.update(record["evidence"])
    terminal_record_evidence: list[str] | None = None
    if terminal and history:
        record = history[-1]
        previous = (
            normal_history[-1].get("to")
            if normal_history and isinstance(normal_history[-1], dict)
            else None
        )
        if (
            not isinstance(record, dict)
            or set(record) != {"sequence", "from", "to", "gate", "status", "evidence"}
            or record.get("sequence") != len(history) - 1
            or record.get("from") != previous
            or record.get("to") != current
            or record.get("status") != "BLOCK"
            or not isinstance(record.get("evidence"), list)
            or not all(isinstance(item, str) for item in record.get("evidence", []))
        ):
            codes.add("RC_CASE_STATE_HISTORY_INVALID")
        else:
            terminal_record_evidence = record["evidence"]
            evidence_in_history.update(terminal_record_evidence)
        if current == "STALE" and record.get("gate") != "GATE_STALE_PROPAGATION":
            codes.add("RC_CASE_STATE_HISTORY_INVALID")
    if evidence_in_history - set(bindings):
        codes.add("RC_CASE_STATE_EVIDENCE_CHAIN_INCOMPLETE")
    if history and (
        not isinstance(history[-1], dict) or value.get("last_gate") != history[-1].get("gate")
    ):
        codes.add("RC_CASE_STATE_LAST_GATE_INVALID")
    if current == "STALE":
        stale = value.get("stale")
        dependency_chain = stale.get("dependency_chain") if isinstance(stale, dict) else None
        if (
            not isinstance(stale, dict)
            or set(stale) != {"reason_code", "dependency_chain"}
            or stale.get("reason_code") != "RC_UPSTREAM_DEPENDENCY_STALE"
            or not isinstance(dependency_chain, list)
            or not dependency_chain
            or not all(
                isinstance(relative, str) and relative_case_path(Path("."), relative) is not None
                for relative in dependency_chain
            )
            or dependency_chain != sorted(set(dependency_chain))
            or terminal_record_evidence is None
            or dependency_chain != terminal_record_evidence
        ):
            codes.add("RC_CASE_STATE_STALE_RECORD_INVALID")
    return blocked(*codes) if codes else passed("RC_CASE_STATE_VALID")


def load_state(case_root: Path) -> dict[str, Any]:
    path = state_path(case_root)
    if not path.is_file():
        raise ValueError("RC_CASE_STATE_MISSING")
    value = load_json(path)
    result = validate_case_state(value)
    if not result.accepted:
        raise ValueError(";".join(result.reason_codes))
    return value


def initialize_case(
    case_root: Path,
    case_id: str,
    kind: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,63}", case_id):
        raise ValueError("RC_CASE_ID_INVALID")
    if kind not in {"prediction", "optimization", "general"}:
        raise ValueError("RC_CASE_KIND_INVALID")
    if state_path(case_root).exists():
        raise ValueError("RC_CASE_ALREADY_INITIALIZED")
    state = {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "case_kind": kind,
        "skill_version": VERSION,
        "capability": CAPABILITY,
        "architecture": ARCHITECTURE,
        "state": "CREATED",
        "last_gate": "INIT",
        "evidence_bindings": {},
        "history": [
            {
                "sequence": 0,
                "from": None,
                "to": "CREATED",
                "gate": "INIT",
                "status": "PASS",
                "evidence": [],
            }
        ],
    }
    if not dry_run:
        for relative in CASE_DIRS:
            (case_root / relative).mkdir(parents=True, exist_ok=True)
        write_json(state_path(case_root), state, overwrite=False)
        for key, relative in ARTIFACT_PATHS.items():
            template_path = SKILL_ROOT / "templates" / TEMPLATE_FILES[key]
            value = load_json(template_path)
            if not isinstance(value, dict):
                raise ValueError("RC_BUNDLED_TEMPLATE_INVALID")
            if key == "problem_requirements":
                content = value.get("content")
                if not isinstance(content, dict):
                    raise ValueError("RC_BUNDLED_TEMPLATE_INVALID")
                value = copy.deepcopy(value)
                value["content"]["case_id"] = case_id
            write_json(case_root / relative, value, overwrite=False)
    return state


def read_artifact(case_root: Path, key: str) -> dict[str, Any]:
    value = load_json(case_root / ARTIFACT_PATHS[key])
    result = validate_artifact(value, key)
    if not result.accepted:
        raise ValueError(";".join(result.reason_codes))
    return value


def trusted_freezes(case_root: Path) -> dict[str, str]:
    plan = read_artifact(case_root, "experiment_plan")["content"]
    value = plan.get("trusted_freeze_registry")
    candidate_ids = plan.get("candidate_ids")
    metric = plan.get("metric")
    direction = plan.get("metric_direction")
    aggregation_rule = plan.get("aggregation_rule")
    selection_rule = plan.get("selection_rule")
    baseline_id = plan.get("baseline_id")
    splits = plan.get("splits")
    seeds = plan.get("random_seeds")
    stop_rule = plan.get("stop_rule")
    handoff_generated_at = plan.get("handoff_generated_at")
    required_inputs = plan.get("required_input_hashes")
    required_code_files = plan.get("required_code_files")
    code_commit = plan.get("code_commit")
    audited_inputs = read_artifact(case_root, "data_audit")["content"].get("data_hashes")
    candidate_records = read_artifact(case_root, "model_candidates")["content"].get("candidates")
    registered_ids = (
        [item.get("candidate_id") for item in candidate_records]
        if isinstance(candidate_records, list)
        and all(isinstance(item, dict) for item in candidate_records)
        else []
    )
    registered_baselines = (
        [
            item.get("candidate_id")
            for item in candidate_records
            if isinstance(item, dict) and item.get("baseline") is True
        ]
        if isinstance(candidate_records, list)
        else []
    )
    split_items = list(splits.values()) if isinstance(splits, dict) else []
    split_values_valid = len(split_items) == 3 and all(
        isinstance(items, list)
        and items
        and all((isinstance(item, (str, int)) and not isinstance(item, bool)) for item in items)
        and len(set(items)) == len(items)
        for items in split_items
    )
    splits_disjoint = split_values_valid and not any(
        set(split_items[left]) & set(split_items[right])
        for left in range(3)
        for right in range(left + 1, 3)
    )
    required_code_valid = (
        isinstance(required_code_files, list)
        and bool(required_code_files)
        and isinstance(code_commit, str)
        and git_commit_exists(code_commit)
    )
    code_identities: set[tuple[str, str]] = set()
    core_runner_present = False
    if required_code_valid:
        for record in required_code_files:
            if not isinstance(record, dict) or set(record) != {
                "scope",
                "path",
                "repository_path",
                "sha256",
            }:
                required_code_valid = False
                break
            scope = record.get("scope")
            relative = record.get("path")
            repository_path = record.get("repository_path")
            identity = (str(scope), str(relative))
            root = SKILL_ROOT if scope == "SKILL_ROOT" else case_root
            code_path = relative_case_path(root, relative)
            if (
                scope not in ("SKILL_ROOT", "CASE_ROOT")
                or identity in code_identities
                or code_path is None
                or not code_path.is_file()
                or not isinstance(repository_path, str)
                or not HEX64.fullmatch(str(record.get("sha256", "")))
                or file_hash(code_path) != record.get("sha256")
                or git_blob_hash(code_commit, repository_path) != record.get("sha256")
                or (
                    scope == "SKILL_ROOT"
                    and (
                        relative not in TRUSTED_EXECUTION_CODE_PATHS
                        or repository_path != f".agents/skills/cumcm-modeling-evidence/{relative}"
                    )
                )
            ):
                required_code_valid = False
                break
            if scope == "SKILL_ROOT" and relative == "scripts/cumcm_case.py":
                core_runner_present = True
            code_identities.add(identity)
    required_code_valid = required_code_valid and core_runner_present
    if (
        not isinstance(value, dict)
        or not isinstance(candidate_ids, list)
        or not candidate_ids
        or not all(isinstance(item, str) and item for item in candidate_ids)
        or len(set(candidate_ids)) != len(candidate_ids)
        or candidate_ids != registered_ids
        or not isinstance(metric, str)
        or not metric.strip()
        or direction not in ("MIN", "MAX")
        or aggregation_rule != "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
        or selection_rule != ("ARGMIN_THEN_ID" if direction == "MIN" else "ARGMAX_THEN_ID")
        or not isinstance(baseline_id, str)
        or baseline_id not in candidate_ids
        or registered_baselines != [baseline_id]
        or not isinstance(splits, dict)
        or set(splits) != {"train", "validation", "test"}
        or not split_values_valid
        or not splits_disjoint
        or not isinstance(seeds, list)
        or not seeds
        or not all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds)
        or len(set(seeds)) != len(seeds)
        or not isinstance(stop_rule, str)
        or not stop_rule.strip()
        or not isinstance(handoff_generated_at, str)
        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", handoff_generated_at)
        or not isinstance(required_inputs, dict)
        or not required_inputs
        or required_inputs != audited_inputs
        or not all(
            isinstance(relative, str)
            and relative_case_path(case_root, relative) is not None
            and (case_root / relative).is_file()
            and HEX64.fullmatch(str(digest))
            and file_hash(case_root / relative) == digest
            for relative, digest in required_inputs.items()
        )
        or not required_code_valid
    ):
        raise ValueError("RC_TRUSTED_FREEZE_REGISTRY_MISSING")
    expected = {
        "candidate_set": canonical_hash(candidate_ids),
        "metric": canonical_hash(
            {
                "name": metric,
                "direction": direction,
                "aggregation_rule": aggregation_rule,
                "selection_rule": selection_rule,
            }
        ),
        "seed_schedule": canonical_hash(seeds),
        "split_assignment": canonical_hash(splits),
        "baseline": canonical_hash(baseline_id),
        "input_set": canonical_hash(required_inputs),
        "execution_policy": canonical_hash(
            {
                "stop_rule": stop_rule,
                "handoff_generated_at": handoff_generated_at,
            }
        ),
        "code_set": canonical_hash(required_code_files),
        "code_commit": canonical_hash(code_commit),
    }
    if value != expected:
        raise ValueError("RC_TRUSTED_FREEZE_REGISTRY_INVALID")
    return value


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def execute_case_code(
    case_root: Path,
    *,
    run_id: str,
    candidate_id: str,
    seed: int,
    code_path: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    state = load_state(case_root)
    if state.get("state") != "RUNNING":
        raise ValueError("RC_EXECUTE_STATE_INVALID")
    if not re.fullmatch(r"RUN-[A-Z0-9][A-Z0-9_-]{2,95}", run_id):
        raise ValueError("RC_RUN_ID_INVALID")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("RC_EXECUTION_SEED_INVALID")
    if timeout_seconds < 1 or timeout_seconds > 900:
        raise ValueError("RC_EXECUTION_TIMEOUT_INVALID")
    plan = read_artifact(case_root, "experiment_plan")["content"]
    freezes = trusted_freezes(case_root)
    if candidate_id not in plan["candidate_ids"] or seed not in plan["random_seeds"]:
        raise ValueError("RC_EXECUTION_NOT_PREREGISTERED")
    matches = [
        record
        for record in plan["required_code_files"]
        if isinstance(record, dict)
        and record.get("scope") == "CASE_ROOT"
        and record.get("path") == code_path
    ]
    if len(matches) != 1:
        raise ValueError("RC_CASE_EXECUTION_CODE_NOT_FROZEN")
    resolved_code = relative_case_path(case_root, code_path)
    if resolved_code is None or not resolved_code.is_file():
        raise ValueError("RC_CASE_EXECUTION_CODE_MISSING")
    run_dir = case_root / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(run_dir)
    run_dir.mkdir(parents=True)
    output_relative = f"runs/{run_id}/output.json"
    stdout_relative = f"runs/{run_id}/stdout.txt"
    stderr_relative = f"runs/{run_id}/stderr.txt"
    output_path = case_root / output_relative
    stdout_path = case_root / stdout_relative
    stderr_path = case_root / stderr_relative
    configuration = {"candidate_id": candidate_id, "seed": seed}
    logical_argv = [
        code_path,
        "--case-root",
        ".",
        "--candidate-id",
        candidate_id,
        "--seed",
        str(seed),
        "--output",
        output_relative,
    ]
    environment = {"PYTHONHASHSEED": str(seed), "TZ": "UTC"}
    started_at = utc_now()
    started_clock = time.monotonic()
    failure: dict[str, Any] | None = None
    try:
        completed = subprocess.run(
            [sys.executable, *logical_argv],
            cwd=case_root,
            env=environment,
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
        )
        exit_code = completed.returncode
        stdout_bytes = completed.stdout
        stderr_bytes = completed.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout_bytes = exc.stdout or b""
        stderr_bytes = exc.stderr or b""
        failure = {"reason_code": "RC_EXECUTION_TIMEOUT", "retained": True}
    elapsed_seconds = round(time.monotonic() - started_clock, 6)
    ended_at = utc_now()
    stdout_path.write_bytes(stdout_bytes)
    stderr_path.write_bytes(stderr_bytes)
    if exit_code == 0:
        try:
            output = load_json(output_path)
        except (OSError, json.JSONDecodeError, ValueError):
            output = None
        contract_result = validate_selected_output_contract(
            output,
            expected_candidate_id=candidate_id,
            required_requirement_ids=required_requirement_ids(case_root),
        )
        if not contract_result.accepted:
            exit_code = 65
            failure = {
                "reason_code": "RC_EXECUTION_OUTPUT_CONTRACT_INVALID",
                "reason_codes": list(contract_result.reason_codes),
                "retained": True,
            }
            if not output_path.is_file():
                write_json(
                    output_path,
                    {
                        "candidate_id": candidate_id,
                        "status": "FAILED",
                        "reason_code": "RC_EXECUTION_OUTPUT_CONTRACT_INVALID",
                    },
                )
    else:
        if failure is None:
            failure = {"reason_code": "RC_EXECUTION_NONZERO_EXIT", "retained": True}
        if not output_path.is_file():
            write_json(
                output_path,
                {
                    "candidate_id": candidate_id,
                    "status": "FAILED",
                    "reason_code": failure["reason_code"],
                },
            )
    outcome = "SUCCESS" if exit_code == 0 else "FAILED"
    input_files = [
        {"path": relative, "sha256": digest}
        for relative, digest in sorted(plan["required_input_hashes"].items())
    ]
    scenario_hash = plan.get("scenario_hash")
    if HEX64.fullmatch(str(scenario_hash or "")) is None:
        scenario_hash = canonical_hash([item["sha256"] for item in input_files])
    output_record = {"path": output_relative, "sha256": file_hash(output_path)}
    capture = {
        "schema_version": "1.0.0",
        "capture_mode": "CONTROLLED_CASE_SUBPROCESS",
        "runner_version": VERSION,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "seed": seed,
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_seconds": elapsed_seconds,
        "exit_code": exit_code,
        "argv": logical_argv,
        "environment_allowlist": environment,
        "stdout": {"path": stdout_relative, "sha256": file_hash(stdout_path)},
        "stderr": {"path": stderr_relative, "sha256": file_hash(stderr_path)},
        "output": output_record,
        "outcome": outcome,
        "failure": failure,
        "freeze_bindings": freezes,
        "input_files": input_files,
        "scenario_hash": scenario_hash,
        "code_files": plan["required_code_files"],
        "code_commit": plan["code_commit"],
        "configuration": configuration,
        "configuration_hash": canonical_hash(configuration),
    }
    capture_path = run_dir / "execution_capture.json"
    write_json(capture_path, capture, overwrite=False)
    return {
        "run_id": run_id,
        "outcome": outcome,
        "exit_code": exit_code,
        "capture_path": str(capture_path.relative_to(case_root)),
        "capture_sha256": file_hash(capture_path),
        "output": output_record,
    }


def build_captured_run_manifest(
    case_root: Path, *, run_id: str, decision_hash: str
) -> dict[str, Any]:
    """Build and validate a Run manifest without changing the case workspace."""
    state = load_state(case_root)
    if state.get("state") != "RUNNING":
        raise ValueError("RC_SEAL_RUN_STATE_INVALID")
    if not HEX64.fullmatch(decision_hash):
        raise ValueError("RC_RUN_DECISION_HASH_INVALID")
    capture_path = case_root / "runs" / run_id / "execution_capture.json"
    if not capture_path.is_file():
        raise ValueError("RC_EXECUTION_CAPTURE_MISSING")
    capture = load_json(capture_path)
    if not isinstance(capture, dict):
        raise ValueError("RC_EXECUTION_CAPTURE_INVALID")
    input_files = capture.get("input_files")
    code_files = capture.get("code_files")
    output = capture.get("output")
    if not isinstance(input_files, list) or not isinstance(code_files, list):
        raise ValueError("RC_EXECUTION_CAPTURE_INVALID")
    if not isinstance(output, dict):
        raise ValueError("RC_EXECUTION_CAPTURE_INVALID")
    manifest = {
        "run_id": run_id,
        "input_files": input_files,
        "input_hash": canonical_hash([item["sha256"] for item in input_files]),
        "scenario_hash": capture.get("scenario_hash"),
        "code_commit": capture.get("code_commit"),
        "code_files": code_files,
        "code_tree_hash": canonical_hash([item["sha256"] for item in code_files]),
        "configuration": capture.get("configuration"),
        "configuration_hash": capture.get("configuration_hash"),
        "random_seed": capture.get("seed"),
        "argv": capture.get("argv"),
        "cwd_policy": "CASE_ROOT_RELATIVE",
        "environment_allowlist": capture.get("environment_allowlist"),
        "output_files": [output],
        "output_hash": canonical_hash([output["sha256"]]),
        "outcome": capture.get("outcome"),
        "failure": capture.get("failure"),
        "supersession": None,
        "trusted_capture": True,
        "freeze_bindings": capture.get("freeze_bindings"),
        "decision_hash": decision_hash,
        "capture_record": {
            "path": str(capture_path.relative_to(case_root)),
            "sha256": file_hash(capture_path),
        },
    }
    result = validate_manifest(
        manifest,
        case_root=case_root,
        trusted_freezes=trusted_freezes(case_root),
    )
    allowed_failure = manifest["outcome"] == "FAILED" and set(result.reason_codes) == {
        "RC_MANIFEST_NOT_SUCCESS:FAILED"
    }
    if not result.accepted and not allowed_failure:
        raise ValueError(";".join(result.reason_codes))
    return manifest


def seal_captured_run(case_root: Path, *, run_id: str, decision_hash: str) -> dict[str, Any]:
    manifest_path = case_root / "runs" / run_id / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(manifest_path)
    manifest = build_captured_run_manifest(
        case_root,
        run_id=run_id,
        decision_hash=decision_hash,
    )
    write_json(manifest_path, manifest, overwrite=False)
    return {
        "run_id": run_id,
        "outcome": manifest["outcome"],
        "manifest_path": str(manifest_path.relative_to(case_root)),
        "manifest_sha256": file_hash(manifest_path),
    }


def record_transition(
    case_root: Path,
    state: dict[str, Any],
    next_state: str,
    gate: str,
    evidence: list[str],
    *,
    check: bool,
) -> dict[str, Any]:
    previous = state["state"]
    if previous not in STATES:
        raise ValueError("RC_TERMINAL_STATE_TRANSITION_PROHIBITED")
    index = STATES.index(previous) + 1
    if index >= len(STATES) or STATES[index] != next_state:
        raise ValueError("RC_STATE_TRANSITION_INVALID")
    missing = [path for path in evidence if not (case_root / path).is_file()]
    if missing:
        raise ValueError("RC_TRANSITION_EVIDENCE_MISSING")
    updated = copy.deepcopy(state)
    updated["state"] = next_state
    updated["last_gate"] = gate
    updated["evidence_bindings"].update({path: file_hash(case_root / path) for path in evidence})
    updated["history"].append(
        {
            "sequence": len(updated["history"]),
            "from": previous,
            "to": next_state,
            "gate": gate,
            "status": "PASS",
            "evidence": evidence,
        }
    )
    if not check:
        write_json(state_path(case_root), updated)
    return updated


def advance_once(case_root: Path, *, check: bool = False) -> dict[str, Any]:
    state = load_state(case_root)
    if dependency_mismatches(case_root, state):
        stale_check(case_root, mutate=not check)
        raise ValueError("RC_UPSTREAM_DEPENDENCY_STALE")
    current = state["state"]
    if current == "CREATED":
        content = read_artifact(case_root, "problem_requirements")["content"]
        if content.get("case_id") != state["case_id"] or not content.get("requirements"):
            raise ValueError("RC_INTAKE_REQUIREMENTS_INVALID")
        return record_transition(
            case_root,
            state,
            "INTAKE_COMPLETE",
            "GATE_PROBLEM_INTAKE",
            [ARTIFACT_PATHS["problem_requirements"]],
            check=check,
        )
    if current == "INTAKE_COMPLETE":
        requirements = read_artifact(case_root, "problem_requirements")["content"]["requirements"]
        if not all(isinstance(item, dict) and item.get("requirement_id") for item in requirements):
            raise ValueError("RC_REQUIREMENT_TRACE_INVALID")
        return record_transition(
            case_root,
            state,
            "REQUIREMENTS_VALIDATED",
            "GATE_REQUIREMENT_COVERAGE",
            [ARTIFACT_PATHS["problem_requirements"]],
            check=check,
        )
    if current == "REQUIREMENTS_VALIDATED":
        research = read_artifact(case_root, "research_plan")["content"]
        ledger = read_artifact(case_root, "source_ledger")
        answer_status = ledger["content"].get("answer_access_status")
        unlocked_development_regression = (
            answer_status == "UNLOCKED_AFTER_FIRST_RUN"
            and research.get("mode") == "DEVELOPMENT_REGRESSION"
            and HEX64.fullmatch(str(research.get("first_run_freeze_sha256", ""))) is not None
        )
        if answer_status != "NOT_ACCESSED" and not unlocked_development_regression:
            raise ValueError("RC_ANSWER_ACCESS_PROHIBITED")
        return record_transition(
            case_root,
            state,
            "SOURCES_PLANNED",
            "GATE_SOURCE_PLAN",
            [ARTIFACT_PATHS["research_plan"], ARTIFACT_PATHS["source_ledger"]],
            check=check,
        )
    if current == "SOURCES_PLANNED":
        read_artifact(case_root, "assumptions_and_symbols")
        audit = read_artifact(case_root, "data_audit")["content"]
        if not audit.get("raw_immutable") or not audit.get("data_hashes"):
            raise ValueError("RC_DATA_AUDIT_INVALID")
        data_paths: list[str] = []
        if not isinstance(audit["data_hashes"], dict):
            raise ValueError("RC_DATA_AUDIT_INVALID")
        for relative, expected in audit["data_hashes"].items():
            path = relative_case_path(case_root, relative)
            if path is None or not path.is_file() or file_hash(path) != expected:
                raise ValueError("RC_DATA_AUDIT_HASH_MISMATCH")
            data_paths.append(relative)
        return record_transition(
            case_root,
            state,
            "DATA_AUDITED",
            "GATE_ASSUMPTIONS_AND_DATA",
            [
                ARTIFACT_PATHS["assumptions_and_symbols"],
                ARTIFACT_PATHS["data_audit"],
                *sorted(data_paths),
            ],
            check=check,
        )
    if current == "DATA_AUDITED":
        requirements = read_artifact(case_root, "problem_requirements")["content"].get(
            "requirements"
        )
        sources = read_artifact(case_root, "source_ledger")["content"].get("sources")
        sufficiency = read_artifact(case_root, "data_sufficiency")["content"]
        sufficiency_result = validate_data_sufficiency_record(
            sufficiency,
            requirements=requirements,
            sources=sources,
        )
        if sufficiency_result.get("status") not in {"SUFFICIENT", "PARTIAL"}:
            raise ValueError(";".join(sufficiency_result.get("reason_codes", [])))
        candidates = read_artifact(case_root, "model_candidates")["content"].get("candidates")
        baselines = (
            sum(bool(item.get("baseline")) for item in candidates if isinstance(item, dict))
            if isinstance(candidates, list)
            else 0
        )
        if not isinstance(candidates, list) or len(candidates) < 2 or baselines != 1:
            raise ValueError("RC_MODEL_PORTFOLIO_OR_BASELINE_INVALID")
        return record_transition(
            case_root,
            state,
            "MODELS_PROPOSED",
            "GATE_MODEL_PORTFOLIO",
            [ARTIFACT_PATHS["data_sufficiency"], ARTIFACT_PATHS["model_candidates"]],
            check=check,
        )
    if current == "MODELS_PROPOSED":
        probe_result, probe_relative = preflight_output_contract(
            case_root, Path("experiments/selected_output_contract_probe.json")
        )
        if not probe_result.accepted:
            raise ValueError(";".join(probe_result.reason_codes))
        plan = read_artifact(case_root, "experiment_plan")["content"]
        if not plan.get("preregistered") or not plan.get("execution_prepared"):
            raise ValueError("RC_EXPERIMENT_PLAN_NOT_PREREGISTERED")
        trusted_freezes(case_root)
        return record_transition(
            case_root,
            state,
            "EXPERIMENT_PLAN_VALIDATED",
            "GATE_EXPERIMENT_PLAN",
            [ARTIFACT_PATHS["experiment_plan"], probe_relative],
            check=check,
        )
    if current == "EXPERIMENT_PLAN_VALIDATED":
        return record_transition(
            case_root,
            state,
            "RUNNING",
            "GATE_EXECUTION_AUTHORIZED",
            [ARTIFACT_PATHS["experiment_plan"]],
            check=check,
        )
    if current in {"RUNNING", "RUN_COMPLETED"}:
        manifests = sorted(case_root.glob("runs/*/manifest.json"))
        if not manifests:
            raise ValueError("RC_RUN_MANIFEST_MISSING")
        freezes = trusted_freezes(case_root)
        plan = read_artifact(case_root, "experiment_plan")["content"]
        plan_candidates = plan["candidate_ids"]
        plan_seeds = plan["random_seeds"]
        expected_attempts = {
            (candidate_id, seed) for candidate_id in plan_candidates for seed in plan_seeds
        }
        observed_attempts: set[tuple[str, int]] = set()
        successes: list[Path] = []
        for path in manifests:
            manifest = load_json(path)
            run_id = manifest.get("run_id") if isinstance(manifest, dict) else None
            configuration = manifest.get("configuration") if isinstance(manifest, dict) else None
            candidate_id = (
                configuration.get("candidate_id") if isinstance(configuration, dict) else None
            )
            configured_seed = configuration.get("seed") if isinstance(configuration, dict) else None
            manifest_seed = manifest.get("random_seed") if isinstance(manifest, dict) else None
            attempt_key = (candidate_id, configured_seed)
            if (
                not isinstance(run_id, str)
                or run_id != path.parent.name
                or not isinstance(candidate_id, str)
                or candidate_id not in plan_candidates
                or not isinstance(configured_seed, int)
                or isinstance(configured_seed, bool)
                or configured_seed not in plan_seeds
                or manifest_seed != configured_seed
                or attempt_key in observed_attempts
            ):
                raise ValueError("RC_RUN_FROZEN_ATTEMPT_BINDING_INVALID")
            observed_attempts.add(attempt_key)
            output_files = manifest.get("output_files")
            if not isinstance(output_files, list) or any(
                not isinstance(record, dict)
                or not isinstance(record.get("path"), str)
                or Path(record["path"]).parts[:2] != ("runs", run_id)
                for record in output_files
            ):
                raise ValueError("RC_RUN_OUTPUT_IDENTITY_INVALID")
            result = validate_manifest(
                manifest,
                case_root=case_root,
                trusted_freezes=freezes,
            )
            if result.accepted:
                successes.append(path)
            elif not (
                isinstance(manifest, dict)
                and manifest.get("outcome")
                in {"FAILED", "PARTIAL", "SUPERSEDED", "STALE", "INFEASIBLE"}
                and all(code.startswith("RC_MANIFEST_NOT_SUCCESS:") for code in result.reason_codes)
            ):
                raise ValueError(";".join(result.reason_codes))
        if observed_attempts != expected_attempts:
            raise ValueError("RC_RUN_ATTEMPT_LEDGER_NOT_EXACT")
        if len(successes) < 2:
            raise ValueError("RC_VERIFIED_RUNS_INSUFFICIENT")
        target = "RUN_COMPLETED" if current == "RUNNING" else "RUN_VALIDATED"
        gate = "GATE_RUN_COMPLETION" if current == "RUNNING" else "GATE_REPRODUCIBILITY_MANIFEST"
        evidence = [str(path.relative_to(case_root)) for path in manifests]
        for path in manifests:
            manifest = load_json(path)
            for output_record in manifest.get("output_files", []):
                if isinstance(output_record, dict) and isinstance(output_record.get("path"), str):
                    evidence.append(output_record["path"])
        return record_transition(
            case_root,
            state,
            target,
            gate,
            evidence,
            check=check,
        )
    if current == "RUN_VALIDATED":
        comparison = read_artifact(case_root, "model_comparison")["content"]
        result = validate_comparison(
            comparison,
            trusted_freezes(case_root),
            case_root=case_root,
        )
        if not result.accepted:
            raise ValueError(";".join(result.reason_codes))
        selection = read_artifact(case_root, "requirement_selection")["content"]
        selection_result = validate_requirement_selection(selection)
        if selection_result.get("status") != "PASS":
            raise ValueError(";".join(selection_result.get("reason_codes", [])))
        robustness = read_artifact(case_root, "robustness_analysis")["content"]
        robustness_result = validate_robustness(
            robustness,
            comparison,
            case_root=case_root,
        )
        if not robustness_result.accepted:
            raise ValueError(";".join(robustness_result.reason_codes))
        return record_transition(
            case_root,
            state,
            "ROBUSTNESS_VALIDATED",
            "GATE_COMPARISON_AND_ROBUSTNESS",
            [
                ARTIFACT_PATHS["model_comparison"],
                ARTIFACT_PATHS["requirement_selection"],
                ARTIFACT_PATHS["robustness_analysis"],
            ],
            check=check,
        )
    if current == "ROBUSTNESS_VALIDATED":
        final = read_artifact(case_root, "final_result")["content"]
        comparison = read_artifact(case_root, "model_comparison")["content"]
        if final.get("contract_version") == "final-result/v2":
            selection = read_artifact(case_root, "requirement_selection")["content"]
            semantic = read_artifact(case_root, "semantic_claim_support")["content"]
            claim = read_artifact(case_root, "claim_evidence")["content"]
            selected_run_ids = _selected_runtime_run_ids(selection)
            manifests = {
                run_id: load_json(case_root / "runs" / run_id / "manifest.json")
                for run_id in selected_run_ids
            }
            runtime_result = validate_runtime_finalization(
                final,
                claim,
                selection,
                semantic,
                manifests,
            )
            if runtime_result.get("status") != "PASS":
                raise ValueError(";".join(runtime_result.get("reason_codes", [])))
        else:
            result = validate_final_result(
                final,
                comparison,
                case_root=case_root,
            )
            if not result.accepted:
                raise ValueError(";".join(result.reason_codes))
        return record_transition(
            case_root,
            state,
            "FINAL_CANDIDATE",
            "GATE_FINAL_RUN",
            [ARTIFACT_PATHS["final_result"]],
            check=check,
        )
    if current == "FINAL_CANDIDATE":
        claim = read_artifact(case_root, "claim_evidence")["content"]
        final = read_artifact(case_root, "final_result")["content"]
        semantic = read_artifact(case_root, "semantic_claim_support")["content"]
        if final.get("contract_version") == "final-result/v2":
            selection = read_artifact(case_root, "requirement_selection")["content"]
            selected_run_ids = _selected_runtime_run_ids(selection)
            manifests = {
                run_id: load_json(case_root / "runs" / run_id / "manifest.json")
                for run_id in selected_run_ids
            }
            runtime_result = validate_runtime_finalization(
                final,
                claim,
                selection,
                semantic,
                manifests,
            )
            if runtime_result.get("status") != "PASS":
                raise ValueError(";".join(runtime_result.get("reason_codes", [])))
            manifest_paths = [f"runs/{run_id}/manifest.json" for run_id in selected_run_ids]
        else:
            manifest_path = case_root / "runs" / str(claim.get("run_id", "")) / "manifest.json"
            if not manifest_path.is_file():
                raise ValueError("RC_CLAIM_MANIFEST_MISSING")
            result = validate_claim(
                claim,
                load_json(manifest_path),
                final,
                case_root=case_root,
                state=state,
            )
            if not result.accepted:
                raise ValueError(";".join(result.reason_codes))
            semantic_result = validate_semantic_claim_bundle(semantic)
            if semantic_result.get("status") != "PASS":
                raise ValueError(";".join(semantic_result.get("reason_codes", [])))
            manifest_paths = [str(manifest_path.relative_to(case_root))]
        return record_transition(
            case_root,
            state,
            "EVIDENCE_VALIDATED",
            "GATE_CLAIM_EVIDENCE",
            [
                ARTIFACT_PATHS["claim_evidence"],
                ARTIFACT_PATHS["semantic_claim_support"],
                *manifest_paths,
            ],
            check=check,
        )
    if current == "EVIDENCE_VALIDATED":
        handoff_path = case_root / ARTIFACT_PATHS["modeling_to_paper_handoff"]
        result = validate_handoff(load_json(handoff_path), case_root=case_root, state=state)
        if not result.accepted:
            raise ValueError(";".join(result.reason_codes))
        return record_transition(
            case_root,
            state,
            "READY_FOR_PAPER_HANDOFF",
            "GATE_MODELING_TO_PAPER",
            [ARTIFACT_PATHS["modeling_to_paper_handoff"]],
            check=check,
        )
    raise ValueError("RC_NO_FORWARD_TRANSITION_AVAILABLE")


def dependency_mismatches(case_root: Path, state: dict[str, Any]) -> list[str]:
    mismatches = {
        path
        for path, expected in state.get("evidence_bindings", {}).items()
        if not (case_root / path).is_file() or file_hash(case_root / path) != expected
    }
    manifest_bindings = [
        relative
        for relative in state.get("evidence_bindings", {})
        if len(Path(relative).parts) == 3
        and Path(relative).parts[0] == "runs"
        and Path(relative).name == "manifest.json"
    ]
    if not manifest_bindings:
        return sorted(mismatches)
    try:
        freezes = trusted_freezes(case_root)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        mismatches.add(ARTIFACT_PATHS["experiment_plan"])
        freezes = None
    for relative in manifest_bindings:
        path = Path(relative)
        manifest_path = case_root / path
        if not manifest_path.is_file() or freezes is None:
            mismatches.add(relative)
            continue
        try:
            manifest = load_json(manifest_path)
            result = validate_manifest(
                manifest,
                case_root=case_root,
                trusted_freezes=freezes,
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            mismatches.add(relative)
            continue
        non_success_only = (
            isinstance(manifest, dict)
            and manifest.get("outcome")
            in ("FAILED", "PARTIAL", "SUPERSEDED", "STALE", "INFEASIBLE")
            and set(result.reason_codes) == {f"RC_MANIFEST_NOT_SUCCESS:{manifest.get('outcome')}"}
        )
        if not result.accepted and not non_success_only:
            mismatches.add(relative)
    return sorted(mismatches)


def stale_check(case_root: Path, *, mutate: bool) -> GateResult:
    state = load_state(case_root)
    if state["state"] == "STALE":
        stored_chain = tuple(state["stale"]["dependency_chain"])
        current_chain = tuple(dependency_mismatches(case_root, state))
        if stored_chain != current_chain:
            return GateResult(
                "BLOCK",
                ("RC_CASE_STATE_STALE_CHAIN_MISMATCH",),
                dependency_chain=current_chain,
            )
        return GateResult(
            "STALE",
            ("RC_UPSTREAM_DEPENDENCY_STALE",),
            dependency_chain=stored_chain,
        )
    mismatches = dependency_mismatches(case_root, state)
    if not mismatches:
        return passed("RC_DEPENDENCY_HASHES_CURRENT")
    if mutate:
        updated = copy.deepcopy(state)
        updated["state"] = "STALE"
        updated["last_gate"] = "GATE_STALE_PROPAGATION"
        updated["stale"] = {
            "reason_code": "RC_UPSTREAM_DEPENDENCY_STALE",
            "dependency_chain": sorted(mismatches),
        }
        updated["history"].append(
            {
                "sequence": len(updated["history"]),
                "from": state["state"],
                "to": "STALE",
                "gate": "GATE_STALE_PROPAGATION",
                "status": "BLOCK",
                "evidence": sorted(mismatches),
            }
        )
        write_json(state_path(case_root), updated)
    return GateResult(
        "STALE",
        ("RC_UPSTREAM_DEPENDENCY_STALE",),
        dependency_chain=tuple(sorted(mismatches)),
    )


def emit(payload: dict[str, Any], exit_code: int = EXIT_OK) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return exit_code


def command_result(command: str, result: GateResult, **extra: Any) -> int:
    code = EXIT_OK if result.accepted else (EXIT_STALE if result.status == "STALE" else EXIT_GATE)
    return emit({"command": command, **result.as_dict(), **extra}, code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CUMCM Modeling Evidence Competition RC case CLI（默认离线）"
    )
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="初始化隔离 case workspace")
    init.add_argument("--case-root", type=Path, required=True)
    init.add_argument("--case-id", required=True)
    init.add_argument(
        "--kind",
        choices=("prediction", "optimization", "general"),
        default="general",
    )
    init.add_argument("--dry-run", action="store_true")
    for name in ("status", "validate", "stale-check", "finalize", "handoff"):
        command = subparsers.add_parser(name)
        command.add_argument("--case-root", type=Path, required=True)
        if name != "status":
            command.add_argument("--check", action="store_true")
    manifest = subparsers.add_parser("manifest", help="检查复现 manifest")
    manifest.add_argument("--case-root", type=Path, required=True)
    manifest.add_argument("--path", type=Path, required=True)
    claim = subparsers.add_parser("claim-check", help="检查 Claim 精确绑定")
    claim.add_argument("--case-root", type=Path, required=True)
    claim.add_argument("--path", type=Path)
    data_sufficiency = subparsers.add_parser(
        "data-sufficiency", help="检查 requirement-level 数据与来源充分性"
    )
    data_sufficiency.add_argument("--case-root", type=Path, required=True)
    data_sufficiency.add_argument("--path", type=Path)
    selection = subparsers.add_parser(
        "selection-check", help="检查逐 requirement 或联合 portfolio 选择"
    )
    selection.add_argument("--case-root", type=Path, required=True)
    selection.add_argument("--path", type=Path)
    semantic = subparsers.add_parser("semantic-check", help="检查 claim-evidence/v3 结构化支持谓词")
    semantic.add_argument("--case-root", type=Path, required=True)
    semantic.add_argument("--path", type=Path)
    compare = subparsers.add_parser("compare-check", help="检查无泄漏比较")
    compare.add_argument("--case-root", type=Path, required=True)
    compare.add_argument("--path", type=Path)
    smoke = subparsers.add_parser("smoke", help="运行项目原创合成 E2E")
    smoke.add_argument("--case-root", type=Path, required=True)
    smoke.add_argument("--case-id", required=True)
    smoke.add_argument("--kind", choices=("prediction", "optimization"), required=True)
    smoke.add_argument("--dry-run", action="store_true")
    preflight = subparsers.add_parser(
        "preflight-output",
        help="在实验冻结前校验非结果 selected-output contract probe",
    )
    preflight.add_argument("--case-root", type=Path, required=True)
    preflight.add_argument("--path", type=Path, required=True)
    execute = subparsers.add_parser("execute", help="执行已冻结的 case-local Python 模型")
    execute.add_argument("--case-root", type=Path, required=True)
    execute.add_argument("--run-id", required=True)
    execute.add_argument("--candidate-id", required=True)
    execute.add_argument("--seed", type=int, required=True)
    execute.add_argument("--code-path", required=True)
    execute.add_argument("--timeout-seconds", type=int, default=600)
    seal = subparsers.add_parser("seal-run", help="复核 capture 后生成 Run manifest")
    seal.add_argument("--case-root", type=Path, required=True)
    seal.add_argument("--run-id", required=True)
    seal.add_argument("--decision-hash", required=True)
    return parser


def run_smoke(case_root: Path, case_id: str, kind: str, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"dry_run": True, "case_id": case_id, "kind": kind, "stages": list(STAGES)}
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from synthetic_cases import run_synthetic_case  # noqa: PLC0415

    return run_synthetic_case(sys.modules[__name__], case_root, case_id, kind)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            state = initialize_case(
                args.case_root,
                args.case_id,
                args.kind,
                dry_run=args.dry_run,
            )
            return emit(
                {
                    "command": "init",
                    "status": "PASS",
                    "dry_run": args.dry_run,
                    "state": state,
                }
            )
        if args.command == "status":
            return emit(
                {"command": "status", "status": "PASS", "state": load_state(args.case_root)}
            )
        if args.command == "validate":
            state = advance_once(args.case_root, check=args.check)
            return emit(
                {
                    "command": "validate",
                    "status": "PASS",
                    "check": args.check,
                    "state": state,
                }
            )
        if args.command == "stale-check":
            return command_result(
                "stale-check",
                stale_check(args.case_root, mutate=not args.check),
                check=args.check,
            )
        if args.command in {"finalize", "handoff"}:
            current = load_state(args.case_root)["state"]
            required = (
                "ROBUSTNESS_VALIDATED" if args.command == "finalize" else "EVIDENCE_VALIDATED"
            )
            if current != required:
                raise ValueError(f"RC_{args.command.upper()}_STATE_INVALID")
            state = advance_once(args.case_root, check=args.check)
            return emit(
                {
                    "command": args.command,
                    "status": "PASS",
                    "check": args.check,
                    "state": state,
                }
            )
        if args.command == "manifest":
            path = args.path if args.path.is_absolute() else args.case_root / args.path
            return command_result(
                "manifest",
                validate_manifest(
                    load_json(path),
                    case_root=args.case_root,
                    trusted_freezes=trusted_freezes(args.case_root),
                ),
            )
        if args.command == "data-sufficiency":
            path = args.path or Path(ARTIFACT_PATHS["data_sufficiency"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and "content" in value:
                wrapper_result = validate_artifact(value, "data_sufficiency")
                if not wrapper_result.accepted:
                    return command_result("data-sufficiency", wrapper_result)
                value = value.get("content")
            requirements = read_artifact(args.case_root, "problem_requirements")["content"].get(
                "requirements"
            )
            sources = read_artifact(args.case_root, "source_ledger")["content"].get("sources")
            outcome = validate_data_sufficiency_record(
                value,
                requirements=requirements,
                sources=sources,
            )
            accepted = outcome.get("status") in {"SUFFICIENT", "PARTIAL"}
            return emit(
                {
                    "command": "data-sufficiency",
                    "accepted": accepted,
                    "final": False,
                    **outcome,
                },
                EXIT_OK if accepted else EXIT_GATE,
            )
        if args.command == "selection-check":
            path = args.path or Path(ARTIFACT_PATHS["requirement_selection"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and "content" in value:
                wrapper_result = validate_artifact(value, "requirement_selection")
                if not wrapper_result.accepted:
                    return command_result("selection-check", wrapper_result)
                value = value.get("content")
            outcome = validate_requirement_selection(value)
            accepted = outcome.get("status") == "PASS"
            return emit(
                {
                    "command": "selection-check",
                    "accepted": accepted,
                    "final": False,
                    **outcome,
                },
                EXIT_OK if accepted else EXIT_GATE,
            )
        if args.command == "semantic-check":
            path = args.path or Path(ARTIFACT_PATHS["semantic_claim_support"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and "content" in value:
                wrapper_result = validate_artifact(value, "semantic_claim_support")
                if not wrapper_result.accepted:
                    return command_result("semantic-check", wrapper_result)
                value = value.get("content")
            outcome = validate_semantic_claim_bundle(value)
            accepted = outcome.get("status") == "PASS"
            return emit(
                {
                    "command": "semantic-check",
                    "accepted": accepted,
                    "final": False,
                    **outcome,
                },
                EXIT_OK if accepted else EXIT_GATE,
            )
        if args.command == "compare-check":
            path = args.path or Path(ARTIFACT_PATHS["model_comparison"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and set(value) & {
                "artifact_type",
                "status",
                "content_hash",
                "content",
            }:
                wrapper_result = validate_artifact(value, "model_comparison")
                if not wrapper_result.accepted:
                    return command_result("compare-check", wrapper_result)
                value = value.get("content")
            return command_result(
                "compare-check",
                validate_comparison(
                    value,
                    trusted_freezes(args.case_root),
                    case_root=args.case_root,
                ),
            )
        if args.command == "claim-check":
            path = args.path or Path(ARTIFACT_PATHS["claim_evidence"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and set(value) & {
                "artifact_type",
                "status",
                "content_hash",
                "content",
            }:
                wrapper_result = validate_artifact(value, "claim_evidence")
                if not wrapper_result.accepted:
                    return command_result("claim-check", wrapper_result)
                value = value.get("content")
            if not isinstance(value, dict):
                return command_result("claim-check", blocked("RC_CLAIM_INVALID"))
            manifest_path = args.case_root / "runs" / str(value.get("run_id", "")) / "manifest.json"
            final = read_artifact(args.case_root, "final_result")["content"]
            manifest_value = load_json(manifest_path) if manifest_path.is_file() else None
            return command_result(
                "claim-check",
                validate_claim(
                    value,
                    manifest_value,
                    final,
                    case_root=args.case_root,
                    state=load_state(args.case_root),
                ),
            )
        if args.command == "smoke":
            result = run_smoke(args.case_root, args.case_id, args.kind, args.dry_run)
            return emit({"command": "smoke", "status": "PASS", "result": result})
        if args.command == "preflight-output":
            result, relative = preflight_output_contract(args.case_root, args.path)
            return command_result("preflight-output", result, path=relative, result_recorded=False)
        if args.command == "execute":
            result = execute_case_code(
                args.case_root,
                run_id=args.run_id,
                candidate_id=args.candidate_id,
                seed=args.seed,
                code_path=args.code_path,
                timeout_seconds=args.timeout_seconds,
            )
            return emit({"command": "execute", "status": "PASS", "result": result})
        if args.command == "seal-run":
            result = seal_captured_run(
                args.case_root,
                run_id=args.run_id,
                decision_hash=args.decision_hash,
            )
            return emit({"command": "seal-run", "status": "PASS", "result": result})
    except FileExistsError:
        return emit(
            {
                "command": args.command,
                "status": "BLOCK",
                "accepted": False,
                "final": False,
                "reason_codes": ["RC_IMMUTABLE_OUTPUT_ALREADY_EXISTS"],
            },
            EXIT_IO,
        )
    except (OSError, json.JSONDecodeError) as exc:
        return emit(
            {
                "command": args.command,
                "status": "BLOCK",
                "accepted": False,
                "final": False,
                "reason_codes": [f"RC_IO_OR_JSON_ERROR:{type(exc).__name__}"],
            },
            EXIT_IO,
        )
    except (ImportError, TypeError, ValueError) as exc:
        codes = sorted(set(str(exc).split(";"))) if str(exc) else ["RC_INPUT_INVALID"]
        return emit(
            {
                "command": args.command,
                "status": "BLOCK",
                "accepted": False,
                "final": False,
                "reason_codes": codes,
            },
            EXIT_GATE,
        )
    except Exception:  # pragma: no cover - final public-entry fail-closed boundary
        return emit(
            {
                "command": args.command,
                "status": "BLOCK",
                "accepted": False,
                "final": False,
                "reason_codes": ["RC_INTERNAL_VALIDATION_ERROR"],
            },
            EXIT_GATE,
        )
    return emit(
        {
            "command": args.command,
            "status": "BLOCK",
            "accepted": False,
            "final": False,
            "reason_codes": ["RC_COMMAND_NOT_IMPLEMENTED"],
        },
        EXIT_INPUT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
