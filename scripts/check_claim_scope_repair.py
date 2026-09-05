#!/usr/bin/env python3
"""Offline verification of bounded Claim repair, preserved history and RC5 freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path("evals/results/phase-004c2")
SKILL = ".agents/skills/cumcm-modeling-evidence"
BASE = "f3812dcd0b1c1bb76224168454719dd3eb112801"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def evaluate(root=ROOT):
    errors = []
    preflight = read(root / RESULTS / "preflight.json")
    for path, expected in preflight["historical_file_hashes"].items():
        if not (root / path).is_file() or digest(root / path) != expected:
            errors.append("HISTORICAL_EVIDENCE_DRIFT:" + path)
    for name in ("neutral_test_freeze", "neutral_formula_scope_freeze", "neutral_identity_freeze"):
        freeze = read(root / RESULTS / (name + ".json"))
        if digest(root / freeze["test_file"]) != freeze["test_sha256"]:
            errors.append("NEUTRAL_EXPECTATIONS_DRIFT:" + name)
    old_registry = yaml.safe_load(
        subprocess.check_output(
            ["git", "show", f"{BASE}:benchmarks/case_registry.yaml"],
            cwd=root,
            text=True,
        )
    )
    registry = yaml.safe_load((root / "benchmarks/case_registry.yaml").read_text())
    if registry["held_out_reservations"] != old_registry["held_out_reservations"]:
        errors.append("HELDOUT_RESERVATION_DRIFT")
    old_case = next(
        item for item in old_registry["cases"] if item["case_id"] == "CUMCM-2024-C-VALIDATION-001"
    )
    current_case = next(
        item for item in registry["cases"] if item["case_id"] == old_case["case_id"]
    )
    if current_case != old_case:
        errors.append("OLD_VALIDATION_REGISTRY_DRIFT")
    if len(list((root / ".agents/skills").glob("*/SKILL.md"))) != 1:
        errors.append("FORMAL_SKILL_COUNT_INVALID")
    anti = read(root / RESULTS / "anti_hardcoding.json")
    if anti["status"] != "PASS" or not all(anti["preserved_functions"].values()):
        errors.append("RC5_SCOPE_OR_HARDCODING_INVALID")
    release_path = root / RESULTS / "rc5_release.json"
    if release_path.is_file():
        release = read(release_path)
        actual_files = set(
            subprocess.check_output(["git", "ls-files", SKILL], cwd=root, text=True).splitlines()
        )
        if actual_files != set(release["skill_file_hashes"]):
            errors.append("RC5_RELEASE_FILE_SET_DRIFT")
        for path, expected in release["skill_file_hashes"].items():
            if not (root / path).is_file() or digest(root / path) != expected:
                errors.append("RC5_RELEASE_SKILL_DRIFT:" + path)
        tree = subprocess.check_output(
            ["git", "rev-parse", f"{release['implementation_commit']}:{SKILL}"], cwd=root, text=True
        ).strip()
        if tree != release["skill_tree"]:
            errors.append("RC5_RELEASE_COMMIT_TREE_MISMATCH")
        for path, expected in release["evidence_hashes"].items():
            if not (root / path).is_file() or digest(root / path) != expected:
                errors.append("RC5_RELEASE_EVIDENCE_DRIFT:" + path)
        if (
            release["skill_version"] != "0.2.0-competition-rc5"
            or release["claim_contract_version"] != "claim-evidence/v2"
        ):
            errors.append("RC5_RELEASE_IDENTITY_INVALID")
        if read(root / RESULTS / "claim_contract_audit.json")["status"] != "PASS":
            errors.append("RC5_AUDITOR_NOT_PASS")
    return {
        "ok": not errors,
        "errors": errors,
        "error_count": len(errors),
        "old_validation_unchanged": current_case == old_case,
        "held_out_unchanged": registry["held_out_reservations"]
        == old_registry["held_out_reservations"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
