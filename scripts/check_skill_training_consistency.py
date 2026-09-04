#!/usr/bin/env python3
"""Check active Skill state and Development/Validation case isolation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "benchmarks/case_registry.yaml"
SKILL = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/SKILL.md"
STATE = REPO_ROOT / "state/project_state.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
EXPECTED_VERSION = "0.2.0-competition-rc2"
ALLOWED_CASE_VERSIONS = {"0.2.0-competition-rc1", EXPECTED_VERSION}
REQUIRED_FIELDS = {
    "case_id",
    "set_type",
    "problem_source",
    "problem_hash",
    "data_hashes",
    "answer_access_status",
    "first_run_status",
    "skill_version",
    "skill_commit",
    "model",
    "reasoning",
    "start_time",
    "freeze_time",
    "unlock_time",
    "generalizable_failures",
    "problem_specific_findings",
}
SET_TYPES = {"DEVELOPMENT", "VALIDATION", "HELD_OUT", "STRESS"}
ANSWER_STATES = {"SEALED", "UNLOCKED_AFTER_FIRST_RUN", "PERMANENTLY_DEVELOPMENT"}
RUN_STATES = {"NOT_STARTED", "IN_PROGRESS", "FROZEN"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def check() -> dict[str, Any]:
    errors: list[str] = []
    state = json.loads(STATE.read_text(encoding="utf-8"))
    skill_text = SKILL.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    registry = load_yaml(REGISTRY)
    if state.get("active_skill_version") != EXPECTED_VERSION:
        errors.append("PROJECT_STATE_SKILL_VERSION_MISMATCH")
    if state.get("skill_capability_status") != "COMPETITION_RC":
        errors.append("PROJECT_STATE_CAPABILITY_MISMATCH")
    if EXPECTED_VERSION not in skill_text:
        errors.append("FORMAL_SKILL_VERSION_MISMATCH")
    if EXPECTED_VERSION not in changelog:
        errors.append("CHANGELOG_VERSION_MISSING")
    skills = list((REPO_ROOT / ".agents/skills").glob("*/SKILL.md"))
    if len(skills) != 1 or skills[0].parent.name != "cumcm-modeling-evidence":
        errors.append("FORMAL_SKILL_COUNT_INVALID")
    declared_fields = registry.get("required_case_fields")
    if not isinstance(declared_fields, list) or set(declared_fields) != REQUIRED_FIELDS:
        errors.append("REGISTRY_FIELD_CONTRACT_INVALID")
    cases = registry.get("cases")
    if not isinstance(cases, list):
        errors.append("REGISTRY_CASES_INVALID")
        cases = []
    ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict) or not set(case) >= REQUIRED_FIELDS:
            errors.append("CASE_REQUIRED_FIELDS_MISSING")
            continue
        case_id = case.get("case_id")
        ids.append(str(case_id))
        if case.get("set_type") not in SET_TYPES:
            errors.append(f"CASE_SET_TYPE_INVALID:{case_id}")
        if case.get("answer_access_status") not in ANSWER_STATES:
            errors.append(f"CASE_ANSWER_STATUS_INVALID:{case_id}")
        if case.get("first_run_status") not in RUN_STATES:
            errors.append(f"CASE_FIRST_RUN_STATUS_INVALID:{case_id}")
        if case.get("skill_version") not in ALLOWED_CASE_VERSIONS:
            errors.append(f"CASE_SKILL_VERSION_MISMATCH:{case_id}")
        if not GIT_SHA.fullmatch(str(case.get("skill_commit", ""))):
            errors.append(f"CASE_SKILL_COMMIT_INVALID:{case_id}")
        if not HEX64.fullmatch(str(case.get("problem_hash", ""))):
            errors.append(f"CASE_PROBLEM_HASH_INVALID:{case_id}")
        data_hashes = case.get("data_hashes")
        if not isinstance(data_hashes, dict) or any(
            not HEX64.fullmatch(str(value)) for value in data_hashes.values()
        ):
            errors.append(f"CASE_DATA_HASH_INVALID:{case_id}")
        if case.get("set_type") in {"VALIDATION", "HELD_OUT"} and (
            case.get("answer_access_status") != "SEALED" or case.get("unlock_time") is not None
        ):
            errors.append(f"VALIDATION_OR_HELD_OUT_POLLUTED:{case_id}")
        if case.get("answer_access_status") != "SEALED" and case.get("set_type") != "DEVELOPMENT":
            errors.append(f"UNSEALED_CASE_NOT_DEVELOPMENT:{case_id}")
        if case.get("first_run_status") == "FROZEN":
            evidence = case.get("first_run_evidence")
            if not isinstance(evidence, dict):
                errors.append(f"FIRST_RUN_EVIDENCE_MISSING:{case_id}")
            elif evidence.get("skill_commit") != case.get("skill_commit"):
                errors.append(f"FIRST_RUN_SKILL_COMMIT_MISMATCH:{case_id}")
            if not case.get("freeze_time"):
                errors.append(f"FIRST_RUN_FREEZE_TIME_MISSING:{case_id}")
        if not isinstance(case.get("generalizable_failures"), list) or not isinstance(
            case.get("problem_specific_findings"), list
        ):
            errors.append(f"CASE_FINDINGS_INVALID:{case_id}")
    if len(ids) != len(set(ids)):
        errors.append("CASE_ID_DUPLICATE")
    return {
        "ok": not errors,
        "error_count": len(errors),
        "errors": sorted(errors),
        "case_count": len(cases),
        "formal_skill_count": len(skills),
        "skill_version": EXPECTED_VERSION,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = check()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
