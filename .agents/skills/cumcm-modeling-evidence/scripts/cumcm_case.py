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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VERSION = "0.2.0-competition-rc1"
CAPABILITY = "COMPETITION_RC"
ASSURANCE = "PUBLIC_DETERMINISTIC_AND_TWO_END_TO_END_SMOKES"
ARCHITECTURE = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

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
    "model_candidates": "models/model_candidates.json",
    "experiment_plan": "experiments/experiment_plan.json",
    "model_comparison": "results/model_comparison.json",
    "robustness_analysis": "results/robustness.json",
    "claim_evidence": "evidence/claim_evidence.json",
    "final_result": "results/final_result.json",
    "modeling_to_paper_handoff": "handoff/modeling_to_paper.json",
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
SENSITIVE_PARTS = (
    "apikey",
    "accesstoken",
    "refreshtoken",
    "bearertoken",
    "privatekey",
    "password",
    "passwd",
    "credential",
    "clientsecret",
    "secretkey",
)

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

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "accepted": self.accepted,
            "final": self.final,
            "reason_codes": list(self.reason_codes),
        }


def passed(code: str) -> GateResult:
    return GateResult("PASS", (code,), accepted=True)


def blocked(*codes: str, status: str = "BLOCK") -> GateResult:
    return GateResult(status, tuple(sorted(set(codes))))


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
    if not GIT_SHA.fullmatch(commit):
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
                if any(part in normalized for part in SENSITIVE_PARTS):
                    findings.add("RC_SECRET_FIELD_REJECTED")
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        elif isinstance(item, str):
            if (
                item.startswith(("/home/", "/Users/", "/root/", "~/", "~\\"))
                or item.startswith(("\\\\", "//"))
                or WINDOWS_ABS.match(item)
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
        if context.get("stage") not in STAGES:
            codes.add("RC_CONTEXT_STAGE_INVALID")
        components = context.get("enabled_components")
        if (
            not isinstance(components, list)
            or not components
            or not all(isinstance(item, str) and item for item in components)
        ):
            codes.add("RC_CONTEXT_ENABLED_COMPONENTS_INVALID")
        if context.get("execution_scope") in {"PRODUCTION", "FORMAL"}:
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
    if not required <= set(manifest):
        codes.add("RC_MANIFEST_REQUIRED_BINDING_MISSING")
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
    commit = manifest.get("code_commit")
    if not isinstance(commit, str) or not git_commit_exists(commit):
        codes.add("RC_MANIFEST_GIT_COMMIT_INVALID")
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
    allowed_outcomes = {"SUCCESS", "FAILED", "PARTIAL", "SUPERSEDED", "STALE", "INFEASIBLE"}
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
            if path is None or not path.is_file():
                codes.add("RC_MANIFEST_INPUT_MISSING")
                continue
            actual = file_hash(path)
            input_hashes.append(actual)
            if record.get("sha256") != actual:
                codes.add("RC_MANIFEST_INPUT_MUTATION")
        if input_hashes and manifest.get("input_hash") != canonical_hash(input_hashes):
            codes.add("RC_MANIFEST_INPUT_HASH_MISMATCH")
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
            if scope not in {"SKILL_ROOT", "CASE_ROOT"} or identity in code_paths:
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
    if manifest != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_REPRODUCIBILITY_MANIFEST_VALID")


def validate_comparison(
    comparison: Any,
    trusted_freezes: dict[str, str] | None = None,
) -> GateResult:
    original = copy.deepcopy(comparison)
    codes: set[str] = set()
    try:
        assert_json_safe(comparison)
    except (TypeError, ValueError):
        codes.add("RC_COMPARISON_NONFINITE_OR_NONJSON")
    if not isinstance(comparison, dict):
        return blocked("RC_COMPARISON_INVALID")
    candidates = comparison.get("candidate_ids")
    baseline = comparison.get("baseline_id")
    if not isinstance(candidates, list) or not candidates:
        codes.add("RC_COMPARISON_EMPTY_CANDIDATE_SET")
    elif not all(isinstance(item, str) and item for item in candidates) or len(
        set(candidates)
    ) != len(candidates):
        codes.add("RC_COMPARISON_CANDIDATE_SET_INVALID")
    if not isinstance(baseline, str) or baseline not in (candidates or []):
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
    seeds = comparison.get("random_seeds")
    derived_freezes: dict[str, str] | None = None
    if (
        isinstance(candidates, list)
        and candidates
        and isinstance(metric, str)
        and metric
        and direction in {"MIN", "MAX"}
        and isinstance(seeds, list)
        and seeds
        and all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds)
        and len(set(seeds)) == len(seeds)
    ):
        derived_freezes = {
            "candidate_set": canonical_hash(candidates),
            "metric": canonical_hash({"name": metric, "direction": direction}),
            "seed_schedule": canonical_hash(seeds),
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
    successful: dict[str, float] = {}
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
                or candidate_id not in (candidates or [])
                or not isinstance(run_id, str)
                or not run_id
                or not isinstance(random_seed, int)
                or isinstance(random_seed, bool)
                or random_seed not in (seeds or [])
                or (candidate_id, random_seed) in attempt_keys
            ):
                codes.add("RC_COMPARISON_ATTEMPT_BINDING_INVALID")
                continue
            attempt_keys.add((candidate_id, random_seed))
            if outcome == "SUCCESS":
                if not strict_score(score):
                    codes.add("RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID")
                elif isinstance(candidate_id, str):
                    successful[candidate_id] = float(score)
            elif score is not None:
                codes.add("RC_COMPARISON_NON_SUCCESS_ATTEMPT_SCORED")
    expected_attempts = (
        {(candidate, seed) for candidate in candidates for seed in seeds}
        if isinstance(candidates, list) and isinstance(seeds, list)
        else set()
    )
    if attempt_keys != expected_attempts:
        codes.add("RC_COMPARISON_ATTEMPT_MATRIX_INCOMPLETE")
    if isinstance(baseline, str) and baseline not in successful:
        codes.add("RC_COMPARISON_BASELINE_SUCCESS_MISSING")
    selected = comparison.get("selected_candidate_id")
    if successful and direction in {"MIN", "MAX"}:
        target = min(successful.values()) if direction == "MIN" else max(successful.values())
        expected = min(key for key, value in successful.items() if value == target)
        if selected != expected:
            codes.add("RC_COMPARISON_SELECTION_MISMATCH")
    else:
        codes.add("RC_COMPARISON_METRIC_OR_SUCCESS_SET_INVALID")
    if comparison != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_LEAKAGE_SAFE_COMPARISON_VALID")


def validate_claim(
    claim: Any,
    manifest: Any | None = None,
    final_result: Any | None = None,
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
        "evidence_status",
        "contradiction_status",
    }
    if not required <= set(claim):
        codes.add("RC_CLAIM_REQUIRED_BINDING_MISSING")
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
            if claim.get("run_manifest_hash") != canonical_hash(manifest):
                codes.add("RC_CLAIM_MANIFEST_HASH_MISMATCH")
            if manifest.get("outcome") != "SUCCESS" or manifest.get("supersession") is not None:
                codes.add("RC_CLAIM_RUN_NOT_CURRENT_SUCCESS")
    if final_result is not None and (
        not isinstance(final_result, dict)
        or any(
            claim.get(name) != final_result.get(name)
            for name in ("run_id", "output_hash", "decision_hash")
        )
    ):
        codes.add("RC_CLAIM_FINAL_RESULT_BINDING_MISMATCH")
    if (claim, manifest, final_result) != original:
        codes.add("RC_INPUT_MUTATION_DETECTED")
    return blocked(*codes) if codes else passed("RC_CLAIM_EXACT_SUPPORT_VALID")


def validate_state_boundary(context: Any) -> GateResult:
    if not isinstance(context, dict):
        return blocked("RC_STATE_CONTEXT_INVALID")
    codes: set[str] = set()
    if context.get("writer") != "modeling_orchestrator":
        codes.add("RC_STATE_UNAUTHORIZED_WRITER")
    if context.get("formal_project_state_write") is not False:
        codes.add("RC_FORMAL_STATE_WRITE_PROHIBITED")
    if context.get("second_state_truth") is not False:
        codes.add("RC_SECOND_STATE_TRUTH_PROHIBITED")
    if context.get("execution_scope") in {"PRODUCTION", "FORMAL"}:
        codes.add("RC_CONTEXT_EXECUTION_SCOPE_PROHIBITED")
    if context.get("state_path") != "case_state.json":
        codes.add("RC_CASE_STATE_BINDING_INVALID")
    return blocked(*codes) if codes else passed("RC_CASE_STATE_BOUNDARY_VALID")


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
    if case_root is not None and state is not None:
        final_runs = handoff.get("final_runs")
        claim_evidence = handoff.get("claim_evidence")
        reproduction = handoff.get("reproduction")
        final = read_artifact(case_root, "final_result")["content"]
        claim = read_artifact(case_root, "claim_evidence")["content"]
        expected_run_path = case_root / "runs" / str(final.get("run_id", "")) / "manifest.json"
        manifest = load_json(expected_run_path) if expected_run_path.is_file() else None
        if (
            not isinstance(final_runs, list)
            or len(final_runs) != 1
            or not isinstance(manifest, dict)
        ):
            codes.add("RC_HANDOFF_RUN_BINDING_INVALID")
        else:
            run = final_runs[0]
            expected = {
                "run_id": manifest.get("run_id"),
                "manifest_hash": canonical_hash(manifest),
                "output_hash": manifest.get("output_hash"),
            }
            if run != expected:
                codes.add("RC_HANDOFF_RUN_BINDING_INVALID")
        if claim_evidence != {claim.get("claim_id"): claim}:
            codes.add("RC_HANDOFF_CLAIM_BINDING_INVALID")
        if (
            not isinstance(reproduction, dict)
            or not isinstance(manifest, dict)
            or reproduction.get("run_manifest_hash") != canonical_hash(manifest)
            or reproduction.get("skill_version") != VERSION
            or reproduction.get("architecture") != ARCHITECTURE
            or reproduction.get("offline") is not True
        ):
            codes.add("RC_HANDOFF_REPRODUCTION_BINDING_INVALID")
        if handoff.get("final_metrics") != final.get("final_metrics"):
            codes.add("RC_HANDOFF_FINAL_METRICS_BINDING_INVALID")
        expected_evidence = {
            ARTIFACT_PATHS["claim_evidence"],
            str(expected_run_path.relative_to(case_root)),
        }
        if expected_evidence - set(state.get("evidence_bindings", {})):
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
        or value.get("case_kind") not in {"prediction", "optimization", "general"}
        or value.get("skill_version") != VERSION
        or value.get("capability") != CAPABILITY
        or value.get("architecture") != ARCHITECTURE
        or current not in set(STATES) | TERMINAL_STATES
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
    terminal = current in TERMINAL_STATES
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
        previous = expected_states[index - 1] if index else None
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
    if terminal and history:
        record = history[-1]
        previous = normal_history[-1].get("to") if normal_history else None
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
            evidence_in_history.update(record["evidence"])
        if current == "STALE" and record.get("gate") != "GATE_STALE_PROPAGATION":
            codes.add("RC_CASE_STATE_HISTORY_INVALID")
    if evidence_in_history - set(bindings):
        codes.add("RC_CASE_STATE_EVIDENCE_CHAIN_INCOMPLETE")
    if history and value.get("last_gate") != history[-1].get("gate"):
        codes.add("RC_CASE_STATE_LAST_GATE_INVALID")
    if current == "STALE":
        stale = value.get("stale")
        if (
            not isinstance(stale, dict)
            or set(stale) != {"reason_code", "dependency_chain"}
            or stale.get("reason_code") != "RC_UPSTREAM_DEPENDENCY_STALE"
            or not isinstance(stale.get("dependency_chain"), list)
            or not stale.get("dependency_chain")
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
            value: dict[str, Any]
            if key == "modeling_to_paper_handoff":
                value = {"status": "DRAFT", "template": key}
            else:
                value = artifact(key, {"template": True}, status="DRAFT")
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
    seeds = plan.get("random_seeds")
    if (
        not isinstance(value, dict)
        or not isinstance(candidate_ids, list)
        or not candidate_ids
        or not isinstance(metric, str)
        or direction not in {"MIN", "MAX"}
        or not isinstance(seeds, list)
        or not seeds
    ):
        raise ValueError("RC_TRUSTED_FREEZE_REGISTRY_MISSING")
    expected = {
        "candidate_set": canonical_hash(candidate_ids),
        "metric": canonical_hash({"name": metric, "direction": direction}),
        "seed_schedule": canonical_hash(seeds),
    }
    if value != expected:
        raise ValueError("RC_TRUSTED_FREEZE_REGISTRY_INVALID")
    return value


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
        read_artifact(case_root, "research_plan")
        ledger = read_artifact(case_root, "source_ledger")
        if ledger["content"].get("answer_access_status") != "NOT_ACCESSED":
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
            [ARTIFACT_PATHS["model_candidates"]],
            check=check,
        )
    if current == "MODELS_PROPOSED":
        plan = read_artifact(case_root, "experiment_plan")["content"]
        if not plan.get("preregistered") or not plan.get("execution_prepared"):
            raise ValueError("RC_EXPERIMENT_PLAN_NOT_PREREGISTERED")
        trusted_freezes(case_root)
        return record_transition(
            case_root,
            state,
            "EXPERIMENT_PLAN_VALIDATED",
            "GATE_EXPERIMENT_PLAN",
            [ARTIFACT_PATHS["experiment_plan"]],
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
        successes: list[Path] = []
        for path in manifests:
            manifest = load_json(path)
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
        if len(successes) < 2:
            raise ValueError("RC_VERIFIED_RUNS_INSUFFICIENT")
        target = "RUN_COMPLETED" if current == "RUNNING" else "RUN_VALIDATED"
        gate = "GATE_RUN_COMPLETION" if current == "RUNNING" else "GATE_REPRODUCIBILITY_MANIFEST"
        evidence = [str(path.relative_to(case_root)) for path in manifests]
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
        result = validate_comparison(comparison, trusted_freezes(case_root))
        if not result.accepted:
            raise ValueError(";".join(result.reason_codes))
        for attempt in comparison["attempts"]:
            manifest_path = case_root / "runs" / attempt["run_id"] / "manifest.json"
            if not manifest_path.is_file():
                raise ValueError("RC_COMPARISON_RUN_MANIFEST_MISSING")
            manifest = load_json(manifest_path)
            if (
                manifest.get("run_id") != attempt["run_id"]
                or manifest.get("random_seed") != attempt["random_seed"]
                or manifest.get("outcome") != attempt["outcome"]
            ):
                raise ValueError("RC_COMPARISON_RUN_BINDING_MISMATCH")
        robustness = read_artifact(case_root, "robustness_analysis")["content"]
        if robustness.get("status") != "VALIDATED" or not robustness.get("perturbations"):
            raise ValueError("RC_ROBUSTNESS_EVIDENCE_INVALID")
        return record_transition(
            case_root,
            state,
            "ROBUSTNESS_VALIDATED",
            "GATE_COMPARISON_AND_ROBUSTNESS",
            [ARTIFACT_PATHS["model_comparison"], ARTIFACT_PATHS["robustness_analysis"]],
            check=check,
        )
    if current == "ROBUSTNESS_VALIDATED":
        final = read_artifact(case_root, "final_result")["content"]
        if final.get("status") != "FINAL_CANDIDATE" or not final.get("run_id"):
            raise ValueError("RC_FINAL_CANDIDATE_INVALID")
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
        manifest_path = case_root / "runs" / str(claim.get("run_id", "")) / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("RC_CLAIM_MANIFEST_MISSING")
        result = validate_claim(claim, load_json(manifest_path), final)
        if not result.accepted:
            raise ValueError(";".join(result.reason_codes))
        return record_transition(
            case_root,
            state,
            "EVIDENCE_VALIDATED",
            "GATE_CLAIM_EVIDENCE",
            [ARTIFACT_PATHS["claim_evidence"], str(manifest_path.relative_to(case_root))],
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
    return sorted(
        path
        for path, expected in state.get("evidence_bindings", {}).items()
        if not (case_root / path).is_file() or file_hash(case_root / path) != expected
    )


def stale_check(case_root: Path, *, mutate: bool) -> GateResult:
    state = load_state(case_root)
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
    return blocked("RC_UPSTREAM_DEPENDENCY_STALE", status="STALE")


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
    compare = subparsers.add_parser("compare-check", help="检查无泄漏比较")
    compare.add_argument("--case-root", type=Path, required=True)
    compare.add_argument("--path", type=Path)
    smoke = subparsers.add_parser("smoke", help="运行项目原创合成 E2E")
    smoke.add_argument("--case-root", type=Path, required=True)
    smoke.add_argument("--case-id", required=True)
    smoke.add_argument("--kind", choices=("prediction", "optimization"), required=True)
    smoke.add_argument("--dry-run", action="store_true")
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
        if args.command == "compare-check":
            path = args.path or Path(ARTIFACT_PATHS["model_comparison"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and value.get("artifact_type") == "model_comparison":
                value = value.get("content")
            return command_result(
                "compare-check",
                validate_comparison(value, trusted_freezes(args.case_root)),
            )
        if args.command == "claim-check":
            path = args.path or Path(ARTIFACT_PATHS["claim_evidence"])
            value = load_json(path if path.is_absolute() else args.case_root / path)
            if isinstance(value, dict) and value.get("artifact_type") == "claim_evidence":
                value = value.get("content")
            if not isinstance(value, dict):
                return command_result("claim-check", blocked("RC_CLAIM_INVALID"))
            manifest_path = args.case_root / "runs" / str(value.get("run_id", "")) / "manifest.json"
            final = read_artifact(args.case_root, "final_result")["content"]
            manifest_value = load_json(manifest_path) if manifest_path.is_file() else None
            return command_result(
                "claim-check",
                validate_claim(value, manifest_value, final),
            )
        if args.command == "smoke":
            result = run_smoke(args.case_root, args.case_id, args.kind, args.dry_run)
            return emit({"command": "smoke", "status": "PASS", "result": result})
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
