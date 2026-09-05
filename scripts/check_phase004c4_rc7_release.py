#!/usr/bin/env python3
"""Two-stage Candidate/Live checker for the Phase 004C4 Competition RC7 release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = Path("evals/results/phase-004c4/rc7_candidate_snapshot.json")
RELEASE_PATH = Path("evals/results/phase-004c4/rc7_release.json")
PROJECT_VERSION = "0.3.0-competition-rc7"
SKILL_VERSION = "0.2.0-competition-rc7"
IMPLEMENTATION_COMMIT = "cd02e61994b906364789c65609de695b6912f1c7"
SKILL_ROOT = Path(".agents/skills/cumcm-modeling-evidence")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+-competition-rc\d+$")
CONTRACT_VERSIONS = {
    "requirement_evidence": "requirement-evidence/v1",
    "data_sufficiency": "data-sufficiency/v1",
    "requirement_selection": "requirement-selection/v1",
    "semantic_claim_support": "claim-evidence/v3",
    "runtime_claim_evidence": "claim-evidence/runtime-v3",
    "final_result": "final-result/v2",
    "modeling_to_paper": "modeling-to-paper/v1",
    "gate_execution_trace": "gate-execution-trace/v1",
}
REQUIRED_CHECKS = {
    "known_actual_controller_probes": 14,
    "adversarial_actual_controller_probes": 6,
    "neutral_actual_controller_e2e": 17,
    "rc6_frozen_neutral": 57,
    "focused_regression_pytest": 239,
    "synthetic_e2e": 2,
    "original_negative_cases": 30,
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def evaluate_candidate_snapshot(snapshot: Any) -> dict[str, Any]:
    """Validate candidate truth without reading live release surfaces."""
    codes: set[str] = set()
    if not isinstance(snapshot, dict):
        return {"status": "BLOCK", "reason_codes": ["RC7_CANDIDATE_SNAPSHOT_INVALID"]}
    payload = dict(snapshot)
    declared_hash = payload.pop("candidate_snapshot_hash", None)
    if declared_hash != _canonical_hash(payload):
        codes.add("RC7_CANDIDATE_SNAPSHOT_HASH_MISMATCH")
    if (
        snapshot.get("schema_version") != "phase-004c4-rc7-candidate/v1"
        or snapshot.get("candidate_status") != "PASS"
        or snapshot.get("implementation_commit") != IMPLEMENTATION_COMMIT
    ):
        codes.add("RC7_CANDIDATE_IDENTITY_INVALID")
    versions = snapshot.get("target_versions")
    if versions != {"project": PROJECT_VERSION, "skill": SKILL_VERSION}:
        codes.add("RC7_CANDIDATE_VERSION_INVALID")
    if not all(VERSION_PATTERN.fullmatch(value) for value in (PROJECT_VERSION, SKILL_VERSION)):
        codes.add("RC7_CANDIDATE_VERSION_INVALID")
    if snapshot.get("contract_versions") != CONTRACT_VERSIONS:
        codes.add("RC7_CANDIDATE_CONTRACT_SET_INVALID")
    checks = snapshot.get("checks")
    if not isinstance(checks, dict):
        codes.add("RC7_CANDIDATE_CHECK_SET_INVALID")
    else:
        for check_id, expected_count in REQUIRED_CHECKS.items():
            record = checks.get(check_id)
            if (
                not isinstance(record, dict)
                or record.get("status") != "PASS"
                or record.get("passed") != expected_count
                or record.get("failed") != 0
            ):
                codes.add(f"RC7_CANDIDATE_CHECK_INVALID:{check_id}")
        for check_id in (
            "historical_read_only",
            "anti_hardcoding",
            "skill_discovery",
            "leakage",
            "secrets",
            "strict",
            "local_ci",
            "full_pytest",
        ):
            if (checks.get(check_id) or {}).get("status") != "PASS":
                codes.add(f"RC7_CANDIDATE_CHECK_INVALID:{check_id}")
    if snapshot.get("invariants") != {
        "formal_skill_count": 1,
        "third_party_integrated": False,
        "historical_mutation_count": 0,
        "answer_leakage_count": 0,
        "secret_count": 0,
        "problem_hardcoding_count": 0,
        "heldout_2025_access_count": 0,
    }:
        codes.add("RC7_CANDIDATE_INVARIANTS_INVALID")
    evidence = snapshot.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        codes.add("RC7_CANDIDATE_EVIDENCE_INVALID")
    return {"status": "BLOCK" if codes else "PASS", "reason_codes": sorted(codes)}


def _verify_path_bindings(records: Any, codes: set[str], prefix: str) -> None:
    if not isinstance(records, dict) or not records:
        codes.add(f"{prefix}_MISSING")
        return
    for record_id, record in records.items():
        path = ROOT / str(record.get("path", "")) if isinstance(record, dict) else ROOT
        if (
            not isinstance(record, dict)
            or not path.is_file()
            or record.get("sha256") != _hash(path)
        ):
            codes.add(f"{prefix}_DRIFT:{record_id}")


def evaluate_candidate_repository() -> dict[str, Any]:
    snapshot = _read_json(ROOT / CANDIDATE_PATH)
    result = evaluate_candidate_snapshot(snapshot)
    codes = set(result["reason_codes"])
    _verify_path_bindings(snapshot.get("evidence"), codes, "RC7_CANDIDATE_EVIDENCE")
    _verify_path_bindings(snapshot.get("verification_receipts"), codes, "RC7_CANDIDATE_RECEIPT")
    subject = snapshot.get("evidence_subject_commit")
    try:
        if not isinstance(subject, str) or _git("cat-file", "-t", subject) != "commit":
            codes.add("RC7_CANDIDATE_SUBJECT_COMMIT_INVALID")
    except subprocess.CalledProcessError:
        codes.add("RC7_CANDIDATE_SUBJECT_COMMIT_INVALID")
    state = _read_json(ROOT / "state/project_state.json")
    if (
        state.get("technical_adjudication_status") != "C_TARGET_RUNTIME_PIPELINE_REPAIR_IN_PROGRESS"
        or state.get("active_skill_version") != "0.2.0-competition-rc5-blocked"
        or (ROOT / "VERSION").read_text(encoding="utf-8").strip() != "0.3.0-competition-rc6"
        or (ROOT / SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        != "0.2.0-competition-rc6"
        or (ROOT / RELEASE_PATH).exists()
    ):
        codes.add("RC7_CANDIDATE_LIVE_STATE_PREMATURE_OR_INVALID")
    return {
        "stage": "candidate",
        "status": "BLOCK" if codes else "PASS",
        "reason_codes": sorted(codes),
    }


def _skill_tree_hash() -> str:
    files = _git("ls-files", str(SKILL_ROOT)).splitlines()
    mapping = {path: _hash(ROOT / path) for path in files if (ROOT / path).is_file()}
    return _canonical_hash(mapping)


def _live_state_is_valid(state: dict[str, Any]) -> bool:
    if state.get("active_skill_version") != SKILL_VERSION:
        return False
    status = state.get("technical_adjudication_status")
    current_case = state.get("current_validation_case")
    valid_cases = {"CUMCM-2018-C-VALIDATION-003", "CUMCM-2017-C-VALIDATION-003F"}
    if status == "C_TARGET_RC7_READY_VALIDATION_PENDING":
        return (
            state.get("subphase") == "RC7-FROZEN-PENDING-FRESH-C-VALIDATION"
            and current_case is None
            and state.get("next_phase_allowed") is None
            and state.get("answer_access_status") == "SEALED_NOT_ACCESSED"
            and state.get("blockers") == []
        )
    if status == "C_TARGET_VALIDATION_IN_PROGRESS":
        return (
            state.get("subphase") == "C-TARGET-FRESH-VALIDATION-IN-PROGRESS"
            and current_case in valid_cases
            and state.get("next_phase_allowed") is None
            and state.get("blockers") == []
        )
    if status == "C_TARGET_VALIDATION_PASSED":
        return (
            state.get("subphase") == "C-TARGET-FRESH-VALIDATION-TERMINAL"
            and current_case in valid_cases
            and state.get("next_phase_allowed") == "PHASE-SKILL-C-TARGET-HELDOUT-004D"
            and state.get("answer_access_status") == "SEALED_AT_TERMINAL_FREEZE"
            and state.get("blockers") == []
        )
    if status in {
        "C_TARGET_VALIDATION_FAILED",
        "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT",
        "C_TARGET_VALIDATION_INCOMPLETE",
    }:
        return (
            state.get("subphase") == "C-TARGET-FRESH-VALIDATION-TERMINAL"
            and current_case in valid_cases
            and state.get("next_phase_allowed") == "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5"
            and state.get("answer_access_status") == "SEALED_AT_TERMINAL_FREEZE"
        )
    if status in {
        "VALIDATION_PREFLIGHT_DISQUALIFIED",
        "VALIDATION_CASE_CONTAMINATED",
        "FIRST_RUN_CONTAMINATION_SUSPECTED",
        "OFFICIAL_INPUTS_REQUIRED",
        "INFRASTRUCTURE_BLOCKED",
        "VALIDATION_CANDIDATE_DRIFT",
    }:
        return (
            state.get("subphase") == "C-TARGET-FRESH-VALIDATION-BLOCKED"
            and state.get("next_phase_allowed") is None
        )
    return False


def evaluate_live_repository() -> dict[str, Any]:
    candidate = _read_json(ROOT / CANDIDATE_PATH)
    release = _read_json(ROOT / RELEASE_PATH)
    candidate_result = evaluate_candidate_snapshot(candidate)
    codes = set(candidate_result["reason_codes"])
    candidate_evidence = candidate.get("evidence")
    live_evidence = dict(candidate_evidence) if isinstance(candidate_evidence, dict) else {}
    frozen_runtime = live_evidence.pop("runtime_core", None)
    _verify_path_bindings(live_evidence, codes, "RC7_CANDIDATE_EVIDENCE")
    try:
        frozen_runtime_bytes = subprocess.check_output(
            [
                "git",
                "show",
                f"{IMPLEMENTATION_COMMIT}:{frozen_runtime['path']}",
            ],
            cwd=ROOT,
        )
        if hashlib.sha256(frozen_runtime_bytes).hexdigest() != frozen_runtime.get("sha256"):
            codes.add("RC7_CANDIDATE_EVIDENCE_DRIFT:runtime_core")
    except (KeyError, TypeError, subprocess.CalledProcessError):
        codes.add("RC7_CANDIDATE_EVIDENCE_DRIFT:runtime_core")
    _verify_path_bindings(candidate.get("verification_receipts"), codes, "RC7_CANDIDATE_RECEIPT")
    required_release_fields = {
        "schema_version",
        "release_status",
        "project_version",
        "skill_version",
        "implementation_commit",
        "skill_tree_hash",
        "runner_hash",
        "contract_versions",
        "actual_controller_probe_hash",
        "auditor_probe_hash",
        "neutral_e2e_hash",
        "historical_regression_hash",
        "pytest_hash",
        "strict_hash",
        "local_ci_hash",
        "candidate_snapshot_hash",
        "release_subject_commit",
    }
    if set(release) != required_release_fields:
        codes.add("RC7_RELEASE_MANIFEST_FIELDS_INVALID")
    if (
        release.get("schema_version") != "phase-004c4-rc7-release/v1"
        or release.get("release_status") != "COMPETITION_RC_RELEASED"
        or release.get("project_version") != PROJECT_VERSION
        or release.get("skill_version") != SKILL_VERSION
        or release.get("implementation_commit") != IMPLEMENTATION_COMMIT
        or release.get("contract_versions") != CONTRACT_VERSIONS
    ):
        codes.add("RC7_RELEASE_MANIFEST_IDENTITY_INVALID")
    if release.get("candidate_snapshot_hash") != _hash(ROOT / CANDIDATE_PATH):
        codes.add("RC7_RELEASE_CANDIDATE_BINDING_INVALID")
    evidence = candidate.get("evidence", {})
    receipts = candidate.get("verification_receipts", {})
    expected_bindings = {
        "actual_controller_probe_hash": (evidence.get("known_actual_controller") or {}).get(
            "sha256"
        ),
        "auditor_probe_hash": (evidence.get("adversarial_actual_controller") or {}).get("sha256"),
        "neutral_e2e_hash": (evidence.get("neutral_actual_controller_e2e") or {}).get("sha256"),
        "historical_regression_hash": (evidence.get("historical_and_auxiliary") or {}).get(
            "sha256"
        ),
        "pytest_hash": (receipts.get("full_pytest") or {}).get("sha256"),
        "strict_hash": (receipts.get("strict") or {}).get("sha256"),
        "local_ci_hash": (receipts.get("local_ci") or {}).get("sha256"),
    }
    if any(release.get(key) != value for key, value in expected_bindings.items()):
        codes.add("RC7_RELEASE_EVIDENCE_BINDING_INVALID")
    runner = ROOT / SKILL_ROOT / "scripts/cumcm_case.py"
    skill_text = (ROOT / SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    state = _read_json(ROOT / "state/project_state.json")
    if (
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() != PROJECT_VERSION
        or (ROOT / SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip() != SKILL_VERSION
        or _extract(r"^Version: `([^`]+)`$", skill_text) != SKILL_VERSION
        or _extract(r'^VERSION = "([^"]+)"$', runner.read_text(encoding="utf-8")) != SKILL_VERSION
        or release.get("runner_hash") != _hash(runner)
        or release.get("skill_tree_hash") != _skill_tree_hash()
    ):
        codes.add("RC7_RELEASE_LIVE_VERSION_OR_TREE_INVALID")
    if not _live_state_is_valid(state):
        codes.add("RC7_RELEASE_LIVE_STATE_INVALID")
    subject = release.get("release_subject_commit")
    try:
        frozen_candidate = subprocess.check_output(
            ["git", "show", f"{subject}:{CANDIDATE_PATH}"], cwd=ROOT
        )
        if hashlib.sha256(frozen_candidate).hexdigest() != _hash(ROOT / CANDIDATE_PATH):
            codes.add("RC7_RELEASE_SUBJECT_BINDING_INVALID")
    except (subprocess.CalledProcessError, TypeError):
        codes.add("RC7_RELEASE_SUBJECT_BINDING_INVALID")
    return {"stage": "live", "status": "BLOCK" if codes else "PASS", "reason_codes": sorted(codes)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("candidate", "live"), required=True)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    result = (
        evaluate_candidate_repository() if args.stage == "candidate" else evaluate_live_repository()
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
