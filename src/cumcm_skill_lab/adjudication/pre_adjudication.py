"""Freeze Phase 002C inputs and emit the deterministic pre-adjudication record."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .evidence_freeze import verify_manifest as verify_phase002_freeze
from .evidence_sufficiency import collect_evidence_items, compute_evidence_sufficiency
from .models import (
    check_or_write,
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
)
from .recovery_freeze import verify_manifest as verify_phase002b_freeze
from .recovery_record import check_incomplete_recovery
from .short_circuit import evaluate_short_circuit

RESULT_ROOT = Path("evals/results/phase-002c")
FREEZE_PATH = RESULT_ROOT / "input_freeze_manifest.json"
SUFFICIENCY_PATH = RESULT_ROOT / "pre_adjudication/evidence_sufficiency.json"
PRE_RECORD_PATH = RESULT_ROOT / "pre_adjudication/pre_adjudication_record.json"
CONFIG_PATH = Path("adjudication/configs/phase-002c.yaml")
POLICY_PATH = Path("adjudication/policies/phase-002c.yaml")

SCORING_CODE_PATHS = (
    "src/cumcm_skill_lab/adjudication/eligibility.py",
    "src/cumcm_skill_lab/adjudication/evidence_sufficiency.py",
    "src/cumcm_skill_lab/adjudication/pre_adjudication.py",
    "src/cumcm_skill_lab/adjudication/short_circuit.py",
    "src/cumcm_skill_lab/adjudication/phase_routing.py",
    "src/cumcm_skill_lab/adjudication/phase002c_records.py",
)
REPORTING_CODE_PATHS = (
    "src/cumcm_skill_lab/adjudication/phase002c_reporting.py",
    "src/cumcm_skill_lab/report_generation.py",
)
ADJUDICATION_CODE_PATHS = (
    "src/cumcm_skill_lab/adjudication/native_subagent_audits.py",
    "src/cumcm_skill_lab/adjudication/phase002c_audit.py",
    "src/cumcm_skill_lab/adjudication/phase002c_replay.py",
)
RULE_CONTRACT_PATHS = (
    "rules/pre_adjudication_rules.yaml",
    "rules/native_subagent_audit_rules.yaml",
    "contracts/evidence_sufficiency.schema.json",
    "contracts/pre_adjudication_record.schema.json",
    "contracts/subagent_audit.schema.json",
    "contracts/phase_route.schema.json",
    "contracts/automated_decision.schema.json",
    "contracts/decision_audit.schema.json",
)
AGENT_CONFIG_PATHS = (
    ".codex/agents/evidence_sufficiency_auditor.toml",
    ".codex/agents/adjudication_policy_prosecutor.toml",
    ".codex/agents/dissent_and_cost_auditor.toml",
    ".codex/agents/reproducibility_auditor.toml",
    ".codex/agents/automated_decision_auditor.toml",
)
HARD_GATE_INPUT_PATHS = (
    "research/upstream_candidates/manifest.yaml",
    "research/upstream_candidates/dynamic_reviews/package_safety_review.json",
)
ELIGIBILITY_INPUT_PATHS = (
    "evals/results/phase-002a/eligibility/classification.json",
    "evals/results/phase-002a/oracle_correctness/oracles.json",
    "evals/results/phase-002a/process_evidence/process.json",
    "evals/results/phase-002a/recovery_gap_evidence/recovery.json",
)
TRANSPORT_FAILURE_PATHS = (
    "evals/results/phase-002a/runtime/blind_failure_001.json",
    "evals/results/phase-002a/runtime/blind_failure_002.json",
    "evals/results/phase-002a/runtime/blind_failure_003.json",
    "evals/results/phase-002b/transport_diagnostics/correctness_attempt_001.json",
    "evals/results/phase-002b/transport_diagnostics/correctness_attempt_002.json",
)


def _deep_merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(parent)
    for key, value in child.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def resolve_config(root: Path) -> dict[str, Any]:
    child = read_yaml(root / CONFIG_PATH)
    parent_path = child.get("extends")
    if not isinstance(parent_path, str):
        raise ValueError("PHASE002C_CONFIG_PARENT_MISSING")
    parent = read_yaml(root / parent_path)
    return _deep_merge(parent, child)


def resolve_policy(root: Path) -> dict[str, Any]:
    child = read_yaml(root / POLICY_PATH)
    parent_path = child.get("extends")
    if not isinstance(parent_path, str):
        raise ValueError("PHASE002C_POLICY_PARENT_MISSING")
    parent = read_yaml(root / parent_path)
    body = {
        "policy_id": child["policy_id"],
        "version": child["version"],
        "frozen_at": child["frozen_at"],
        "extends": parent_path,
        "parent_policy_id": parent["policy_id"],
        "parent_policy_version": parent["version"],
        "parent_policy_hash": parent["policy_hash"],
        "evidence_hierarchy": parent["evidence_hierarchy"],
        "decision_order": child["execution_order"],
        "hard_gates": parent["hard_gates"],
        "balanced_case_minimum": parent["balanced_case_minimum"],
        "minimum_repeats": parent["minimum_repeats"],
        "decision_statuses": parent["decision_statuses"],
        "thresholds_unchanged": child["thresholds_unchanged"],
        "short_circuit": child["short_circuit"],
        "semantic_judges_conditional": child["semantic_judges_conditional"],
        "recovery_policy": child["recovery_policy"],
        "accepted_scope_limits": child["accepted_scope_limits"],
    }
    body["policy_hash"] = sha256_json(body)
    recorded = child.get("policy_hash")
    if recorded not in {body["policy_hash"], "PLACEHOLDER_RESOLVED_BY_IMPLEMENTATION"}:
        raise ValueError("PHASE002C_POLICY_HASH_MISMATCH")
    return body


def _evidence_files_on_disk(root: Path) -> list[str]:
    paths: list[str] = []
    for relative in (
        "evals/results/phase-002",
        "evals/results/phase-002a",
        "evals/results/phase-002b",
    ):
        paths.extend(
            path.relative_to(root).as_posix()
            for path in (root / relative).rglob("*")
            if path.is_file()
        )
    return sorted(paths)


def historical_freeze_errors(root: Path) -> list[str]:
    errors = verify_phase002_freeze(root)
    errors.extend(verify_phase002b_freeze(root))
    errors.extend(check_incomplete_recovery(root))
    return sorted(set(errors))


def build_input_freeze(root: Path) -> dict[str, Any]:
    errors = historical_freeze_errors(root)
    if errors:
        raise ValueError("INPUT_FREEZE_BROKEN:" + ",".join(errors))
    config = resolve_config(root)
    policy = resolve_policy(root)
    phase002a = read_json(root / "evals/results/phase-002a/evidence_freeze_manifest.json")
    phase002b = read_json(root / "evals/results/phase-002b/recovery_manifest.json")
    evidence_files = _evidence_files_on_disk(root)
    body = {
        "schema_version": "1.0.0",
        "freeze_id": "PHASE-002C-INPUT-FREEZE",
        "phase": "PHASE-AUTOMATED-EVIDENCE-SUFFICIENCY-002C",
        "created_at": policy["frozen_at"],
        "state_subject_commit": config["state_subject_commit"],
        "phase002_score_freeze_hash": file_sha256(
            root / "evals/results/phase-002/score_freeze.json"
        ),
        "phase002a_freeze_hash": phase002a["freeze_hash"],
        "phase002b_input_freeze_hash": phase002b["input_freeze_hash"],
        "phase002b_recovery_manifest_hash": file_sha256(
            root / "evals/results/phase-002b/recovery_manifest.json"
        ),
        "config_hash": sha256_json(config),
        "config_file_hash": file_sha256(root / CONFIG_PATH),
        "policy_hash": policy["policy_hash"],
        "policy_file_hash": file_sha256(root / POLICY_PATH),
        "eligibility_input_hashes": {
            path: file_sha256(root / path) for path in ELIGIBILITY_INPUT_PATHS
        },
        "scoring_code_hashes": {path: file_sha256(root / path) for path in SCORING_CODE_PATHS},
        "reporting_code_hashes": {path: file_sha256(root / path) for path in REPORTING_CODE_PATHS},
        "adjudication_code_hashes": {
            path: file_sha256(root / path) for path in ADJUDICATION_CODE_PATHS
        },
        "rule_contract_hashes": {path: file_sha256(root / path) for path in RULE_CONTRACT_PATHS},
        "agent_config_hashes": {path: file_sha256(root / path) for path in AGENT_CONFIG_PATHS},
        "hard_gate_input_hashes": {
            path: file_sha256(root / path) for path in HARD_GATE_INPUT_PATHS
        },
        "transport_failure_evidence_hashes": {
            path: file_sha256(root / path) for path in TRANSPORT_FAILURE_PATHS
        },
        "tracked_evidence_files": {path: file_sha256(root / path) for path in evidence_files},
        "tracked_evidence_file_count": len(evidence_files),
        "historical_freezes_valid": True,
    }
    body["evidence_hash"] = sha256_json(body["tracked_evidence_files"])
    body["freeze_hash"] = sha256_json(body)
    return body


def verify_input_freeze(root: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    errors = historical_freeze_errors(root)
    path = root / FREEZE_PATH
    if manifest is None:
        if not path.is_file():
            return [*errors, "PHASE002C_INPUT_FREEZE_MISSING"]
        manifest = read_json(path)
    body = dict(manifest)
    recorded_hash = body.pop("freeze_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("PHASE002C_FREEZE_HASH_MISMATCH")
    for relative, expected in manifest.get("tracked_evidence_files", {}).items():
        candidate = root / relative
        if not candidate.is_file():
            errors.append(f"PHASE002C_INPUT_MISSING:{relative}")
        elif file_sha256(candidate) != expected:
            errors.append(f"PHASE002C_INPUT_MUTATED:{relative}")
    current_files = _evidence_files_on_disk(root)
    frozen_files = sorted(manifest.get("tracked_evidence_files", {}))
    if current_files != frozen_files or len(current_files) != manifest.get(
        "tracked_evidence_file_count"
    ):
        errors.append("PHASE002C_EVIDENCE_INVENTORY_MISMATCH")
    for group in (
        "eligibility_input_hashes",
        "scoring_code_hashes",
        "reporting_code_hashes",
        "adjudication_code_hashes",
        "rule_contract_hashes",
        "agent_config_hashes",
        "hard_gate_input_hashes",
        "transport_failure_evidence_hashes",
    ):
        for relative, expected in manifest.get(group, {}).items():
            candidate = root / relative
            if not candidate.is_file() or file_sha256(candidate) != expected:
                errors.append(f"PHASE002C_BOUND_HASH_MISMATCH:{group}:{relative}")
    if manifest.get("policy_hash") != resolve_policy(root)["policy_hash"]:
        errors.append("PHASE002C_POLICY_HASH_MISMATCH")
    if manifest.get("config_hash") != sha256_json(resolve_config(root)):
        errors.append("PHASE002C_CONFIG_HASH_MISMATCH")
    if manifest.get("policy_file_hash") != file_sha256(root / POLICY_PATH):
        errors.append("PHASE002C_POLICY_FILE_HASH_MISMATCH")
    if manifest.get("config_file_hash") != file_sha256(root / CONFIG_PATH):
        errors.append("PHASE002C_CONFIG_FILE_HASH_MISMATCH")
    return sorted(set(errors))


def evaluate_comparative_hard_gates(
    *,
    no_direct_adoption: bool,
    normalized_contamination_safe: bool,
    no_third_party_execution: bool,
    evaluation_scope_only: bool,
) -> dict[str, bool]:
    """Apply every inherited hard-gate name to sanitized comparison scope."""
    return {
        "license": no_direct_adoption,
        "answer_contamination": normalized_contamination_safe,
        "security": no_third_party_execution,
        "second_state_source": no_direct_adoption and no_third_party_execution,
        "second_orchestrator": no_direct_adoption and no_third_party_execution,
        "scope_conflict": evaluation_scope_only,
    }


def build_comparative_hard_gates(root: Path) -> list[dict[str, Any]]:
    review = read_json(
        root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
    )
    config = resolve_config(root)
    candidate_arms = [item for item in review["arms"] if item.get("candidate_id")]
    expected_candidate_ids = set(config["direct_adoption_targets"].values())
    observed_candidate_ids = [item["candidate_id"] for item in candidate_arms]
    candidate_coverage_complete = (
        bool(candidate_arms)
        and len(observed_candidate_ids) == len(set(observed_candidate_ids))
        and set(observed_candidate_ids) == expected_candidate_ids
    )
    values = evaluate_comparative_hard_gates(
        no_direct_adoption=candidate_coverage_complete
        and all(item.get("direct_adoption_eligible") is False for item in candidate_arms),
        normalized_contamination_safe=candidate_coverage_complete
        and all(
            str(item.get("contamination_status", "")).startswith("PASS") for item in candidate_arms
        ),
        no_third_party_execution=candidate_coverage_complete
        and review.get("third_party_code_executed") is False
        and review.get("candidate_dependencies_installed") is False,
        evaluation_scope_only=candidate_coverage_complete
        and review.get("review_status") == "COMPLETE_FOR_EVALUATION_ONLY",
    )
    return [
        {
            "target": "SANITIZED_COMPARATIVE_EVALUATION",
            "gate": name,
            "passed": passed,
            "evidence_refs": [
                "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
            ],
        }
        for name, passed in values.items()
    ]


def recovery_exclusion_passed(items: list[dict[str, Any]]) -> bool:
    return all(item.get("ranking_eligible") is False for item in items)


def build_pre_adjudication(root: Path, freeze: dict[str, Any]) -> tuple[dict, dict]:
    policy = resolve_policy(root)
    config = resolve_config(root)
    items = collect_evidence_items(root)
    recovery_items = [item for item in items if item["classification"] == "RECOVERY_AFFECTED"]
    recovery_excluded = recovery_exclusion_passed(recovery_items)
    no_not_run_as_zero = all(
        not (item["completion_status"] == "NOT_RUN" and item["ranking_eligible"]) for item in items
    )
    provisional = compute_evidence_sufficiency(
        items,
        balanced_case_minimum=policy["balanced_case_minimum"],
        minimum_repeats=policy["minimum_repeats"],
        frozen_evidence_valid=True,
        mandatory_hard_gates_passed=True,
        input_freeze_id=freeze["freeze_id"],
        input_freeze_hash=freeze["freeze_hash"],
        policy_id=policy["policy_id"],
        policy_hash=policy["policy_hash"],
    )
    gates = [
        {
            "target": "COMPARATIVE_SELECTION",
            "gate": "freeze_integrity",
            "passed": True,
            "evidence_refs": [freeze["freeze_id"]],
        },
        {
            "target": "COMPARATIVE_SELECTION",
            "gate": "task_input_hash_consistency",
            "passed": provisional["task_hash_consistency"]["passed"],
            "evidence_refs": ["EVIDENCE-SUFFICIENCY-PHASE-002C"],
        },
        {
            "target": "COMPARATIVE_SELECTION",
            "gate": "recovery_exclusion",
            "passed": recovery_excluded,
            "evidence_refs": ["RECOVERY-EXCLUSION-PHASE-002A"],
        },
        {
            "target": "COMPARATIVE_SELECTION",
            "gate": "not_run_not_zero",
            "passed": no_not_run_as_zero,
            "evidence_refs": ["ELIGIBILITY-PHASE-002A"],
        },
        *build_comparative_hard_gates(root),
    ]
    hard_gates_passed = all(item["passed"] for item in gates)
    sufficiency = compute_evidence_sufficiency(
        items,
        balanced_case_minimum=policy["balanced_case_minimum"],
        minimum_repeats=policy["minimum_repeats"],
        frozen_evidence_valid=True,
        mandatory_hard_gates_passed=hard_gates_passed,
        input_freeze_id=freeze["freeze_id"],
        input_freeze_hash=freeze["freeze_hash"],
        policy_id=policy["policy_id"],
        policy_hash=policy["policy_hash"],
    )
    action = evaluate_short_circuit(sufficiency)
    pre_record = {
        "record_id": "PRE-ADJUDICATION-PHASE-002C",
        "phase": config["phase"],
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["freeze_hash"],
        "config_hash": freeze["config_hash"],
        "policy_hash": policy["policy_hash"],
        "hard_gates": gates,
        "evidence_sufficiency_id": sufficiency["sufficiency_id"],
        "evidence_sufficiency_result": sufficiency["result"],
        **action,
        "created_at": policy["frozen_at"],
    }
    pre_record["record_hash"] = sha256_json(pre_record)
    _validate(root, "evidence_sufficiency", sufficiency)
    _validate(root, "pre_adjudication_record", pre_record)
    return sufficiency, pre_record


def write_pre_adjudication(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    if check:
        errors.extend(verify_input_freeze(root))
        if errors:
            return {
                "status": "INPUT_FREEZE_BROKEN",
                "errors": errors,
                "decision": "STALE",
                "semantic_judges_status": "BLOCKED",
                "ranking_status": "PROHIBITED",
                "next_phase_candidate": None,
            }
        freeze = read_json(root / FREEZE_PATH)
    else:
        freeze = build_input_freeze(root)
        errors.extend(check_or_write(root / FREEZE_PATH, freeze, check=False))
    sufficiency, pre_record = build_pre_adjudication(root, freeze)
    errors.extend(check_or_write(root / SUFFICIENCY_PATH, sufficiency, check=check))
    errors.extend(check_or_write(root / PRE_RECORD_PATH, pre_record, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "freeze_hash": freeze["freeze_hash"],
        "evidence_hash": freeze["evidence_hash"],
        "sufficiency_result": sufficiency["result"],
        "decision": pre_record["decision"],
        "balanced_case_count": sufficiency["actual"]["balanced_case_count"],
        "independent_repeats": sufficiency["actual"]["independent_repeats"],
        "semantic_judges_status": pre_record["semantic_judges_status"],
    }


def _validate(root: Path, contract: str, value: dict[str, Any]) -> None:
    schema = read_json(root / f"contracts/{contract}.schema.json")
    Draft202012Validator(schema).validate(value)
