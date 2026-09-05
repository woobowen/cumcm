#!/usr/bin/env python3
"""Fail-closed consistency check for the formal CUMCM Skill release surfaces."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT_VERSION = "0.3.0-competition-rc6"
SKILL_VERSION = "0.2.0-competition-rc6"
RELEASE_MANIFEST = "evals/results/phase-004c3/rc6_release.json"
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+-competition-rc\d+$")


def result(status: str, *reason_codes: str) -> dict[str, Any]:
    return {"status": status, "reason_codes": sorted(set(reason_codes))}


def evaluate_release_snapshot(snapshot: Any) -> dict[str, Any]:
    """Evaluate a caller-supplied release snapshot without filesystem access."""
    if not isinstance(snapshot, dict):
        return result("BLOCK", "RC_RELEASE_SNAPSHOT_INVALID")
    codes: set[str] = set()

    project = snapshot.get("project_version")
    manifest_project = snapshot.get("manifest_project_version")
    if not isinstance(project, str) or VERSION_PATTERN.fullmatch(project) is None:
        codes.add("RC_RELEASE_VERSION_FORMAT_INVALID")
    elif project != PROJECT_VERSION:
        codes.add("RC_RELEASE_PROJECT_VERSION_MISMATCH")
    if manifest_project != PROJECT_VERSION:
        codes.add("RC_RELEASE_PROJECT_VERSION_MISMATCH")

    field_codes = {
        "skill_version_file": "RC_RELEASE_SKILL_VERSION_MISMATCH",
        "skill_metadata_version": "RC_RELEASE_SKILL_METADATA_VERSION_MISMATCH",
        "runner_version": "RC_RELEASE_RUNNER_VERSION_MISMATCH",
        "manifest_skill_version": "RC_RELEASE_MANIFEST_VERSION_MISMATCH",
        "state_skill_version": "RC_RELEASE_STATE_VERSION_MISMATCH",
    }
    for field, mismatch_code in field_codes.items():
        value = snapshot.get(field)
        if field == "skill_version_file" and value is None:
            codes.add("RC_RELEASE_SKILL_VERSION_MISSING")
        elif not isinstance(value, str) or VERSION_PATTERN.fullmatch(value) is None:
            codes.add("RC_RELEASE_VERSION_FORMAT_INVALID")
        elif value != SKILL_VERSION:
            codes.add(mismatch_code)

    changelog = snapshot.get("changelog_versions")
    if (
        not isinstance(changelog, list)
        or PROJECT_VERSION not in changelog
        or SKILL_VERSION not in changelog
    ):
        codes.add("RC_RELEASE_CHANGELOG_VERSION_MISMATCH")
    discovered = snapshot.get("discovered_skill_versions")
    if not isinstance(discovered, list) or discovered != [SKILL_VERSION]:
        codes.add("RC_RELEASE_DISCOVERED_SKILL_VERSION_MISMATCH")
    history = snapshot.get("blocked_history_records")
    if not isinstance(history, list) or "RC5_VERSION_FILE_MISMATCH" not in history:
        codes.add("RC_RELEASE_HISTORY_BLOCKED_RECORD_MISSING")
    return result("BLOCK", *codes) if codes else result("PASS")


def _read_text(relative: str) -> str | None:
    path = ROOT / relative
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _read_json(relative: str) -> dict[str, Any]:
    text = _read_text(relative)
    if text is None:
        return {}
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _extract(pattern: str, text: str | None) -> str | None:
    match = re.search(pattern, text or "", re.MULTILINE)
    return match.group(1) if match else None


def build_repository_snapshot() -> dict[str, Any]:
    """Read only the declared release surfaces; historical artifacts stay immutable."""
    skill_text = _read_text(".agents/skills/cumcm-modeling-evidence/SKILL.md")
    runner_text = _read_text(".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py")
    changelog_text = _read_text("CHANGELOG.md") or ""
    manifest = _read_json(RELEASE_MANIFEST)
    state = _read_json("state/project_state.json")
    discovered: list[str] = []
    for path in sorted((ROOT / ".agents/skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if "Capability: `COMPETITION_RC`" not in text:
            continue
        version = _extract(r"^Version: `([^`]+)`$", text)
        if version is not None:
            discovered.append(version)
    changelog_versions = re.findall(
        r"(?:^##\s+|`)(\d+\.\d+\.\d+-competition-rc\d+)(?:\s|`)",
        changelog_text,
        re.MULTILINE,
    )
    blocked_record = _read_text("evals/results/phase-004c2/rc5_release_acceptance_block.json")
    blocked_history_records = (
        ["RC5_VERSION_FILE_MISMATCH"]
        if blocked_record and "RC5_VERSION_FILE_MISMATCH" in blocked_record
        else []
    )
    return {
        "project_version": _read_text("VERSION"),
        "manifest_project_version": manifest.get("project_version"),
        "skill_version_file": _read_text(".agents/skills/cumcm-modeling-evidence/VERSION"),
        "skill_metadata_version": _extract(r"^Version: `([^`]+)`$", skill_text),
        "runner_version": _extract(r'^VERSION = "([^"]+)"$', runner_text),
        "manifest_skill_version": manifest.get("skill_version"),
        "state_skill_version": state.get("active_skill_version"),
        "changelog_versions": changelog_versions,
        "discovered_skill_versions": discovered,
        "blocked_history_records": blocked_history_records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="read and verify repository state")
    args = parser.parse_args(argv)
    if not args.check:
        parser.error("--check is required")
    snapshot = build_repository_snapshot()
    outcome = evaluate_release_snapshot(snapshot)
    print(
        json.dumps(
            {"check": "skill_release_consistency", **outcome, "snapshot": snapshot},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if outcome["status"] == "PASS" else 3


if __name__ == "__main__":
    sys.exit(main())
