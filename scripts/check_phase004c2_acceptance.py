#!/usr/bin/env python3
"""Check truthful terminal reporting, including unresolved frozen release defects."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "CUMCM-2019-C-VALIDATION-002"


def assess(version_file, release, block, decision, state):
    errors = []
    successor = state.get("phase") in {
        "PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3",
        "PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4",
    }
    historical_version = block.get("version_file_value") if successor else version_file.strip()
    mismatch = historical_version != release["skill_version"]
    historical_blocker_reported = "RC5_VERSION_FILE_MISMATCH" in state.get("blockers", []) or any(
        "RC5_VERSION_FILE_MISMATCH" in item for item in state.get("risks", [])
    )
    if mismatch and not (
        block["finding_id"] == "RC5_VERSION_FILE_MISMATCH"
        and block["status"] == "BLOCK_RELEASE_ACCEPTANCE"
        and block["version_file_value"] == historical_version
        and block["declared_release_version"] == release["skill_version"]
        and decision["release_acceptance"] == "BLOCKED_VERSION_METADATA"
        and historical_blocker_reported
    ):
        errors.append("UNREPORTED_FROZEN_RELEASE_VERSION_MISMATCH")
    terminal_state_matches = (
        state.get("technical_adjudication_status") == decision["status"]
        and state.get("current_validation_case") == CASE_ID
        and state.get("next_phase_allowed") == decision["next_phase_allowed"]
    )
    successor_preserves_terminal = (
        state.get("phase")
        in {
            "PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3",
            "PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4",
        }
        and state.get("previous_validation_cases") == ["CUMCM-2024-C-VALIDATION-001", CASE_ID]
        and "DECISION-C-TARGET-VALIDATION-004C2" in state.get("automated_decision_ids", [])
        and any(
            "2019 C terminal outcome is evidence insufficient" in item
            for item in state.get("risks", [])
        )
    )
    if not terminal_state_matches and not successor_preserves_terminal:
        errors.append("TERMINAL_STATE_DECISION_MISMATCH")
    semantic_gap = any(
        finding["finding_id"] == "SELECTED_Q4_CLAIM_SCOPE_INCOMPLETE"
        for finding in decision["scope_findings"]
    )
    if semantic_gap and (
        decision["facts"]["semantic_requirement_claims_complete"] is not False
        or decision["facts"]["pipeline_pass_requirements"]["requirement_claims_valid"] is not False
        or decision["paper_dispatch_accepted"] is not False
        or decision["next_phase_allowed"] is not None
    ):
        errors.append("SEMANTIC_GAP_FALSELY_REPORTED_AS_COMPLETION")
    return {
        "ok": not errors,
        "errors": errors,
        "release_version_consistent": not mismatch,
        "release_acceptance": "BLOCK" if mismatch else "NO_VERSION_BLOCK",
        "validation_status": decision["status"],
        "meaning": "Reporting consistency only; a PASS does not accept the blocked release.",
    }


def main():
    base = ROOT / "evals/results/phase-004c2"

    def read(path):
        return json.loads(path.read_text())

    result = assess(
        (ROOT / ".agents/skills/cumcm-modeling-evidence/VERSION").read_text(),
        read(base / "rc5_release.json"),
        read(base / "rc5_release_acceptance_block.json"),
        read(base / CASE_ID / "validation/DECISION-C-TARGET-VALIDATION-004C2.json"),
        read(ROOT / "state/project_state.json"),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
