#!/usr/bin/env python3
"""Validate the single neutral RC4 candidate and its RC3 evidence lineage."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "evals/results/phase-004c-c-batch/rc4/candidate_freeze.json"
MATRIX = ROOT / "evals/results/phase-004c-c-batch/cross_case_failure_matrix.json"
SKILL_ROOT = ".agents/skills/cumcm-modeling-evidence"
RC3_COMMIT = "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
RC3_TREE = "a4551c8aa0b6b119823f6ce9df3f0f948339bb33"
RC4_COMMIT = "297cad0a29c659b18484d4f3b67d69a942ad415c"
RC4_TREE = "d041ca38de030ae04813ef02dbe12f7f2b7a1c22"
AUTHORIZED_FAILURE = "C004C-CROSS-OUTPUT-CONTRACT-PREFLIGHT-001"
FORMAL_FILES = {
    f"{SKILL_ROOT}/SKILL.md",
    f"{SKILL_ROOT}/VERSION",
    f"{SKILL_ROOT}/scripts/cumcm_case.py",
    f"{SKILL_ROOT}/scripts/synthetic_cases.py",
    f"{SKILL_ROOT}/templates/case_state.json",
    f"{SKILL_ROOT}/workflows/experiment_design.md",
    f"{SKILL_ROOT}/workflows/model_execution.md",
}
NEUTRAL_TEST_FILES = {
    "tests/unit/test_competition_rc_case_executor.py",
    "tests/unit/test_competition_rc_output_contract.py",
    "tests/unit/test_competition_rc_skill.py",
}
FORBIDDEN_ADDED_TERMS = (
    "2020 C",
    "2021 C",
    "2022 C",
    "古代玻璃制品的成分分析与鉴别",
    "生产企业原材料的订购与运输",
    "中小微企业的信贷决策",
    "供应商数",
    "企业数",
    "玻璃类别",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, check=False, capture_output=True, text=True
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def evaluate() -> dict[str, Any]:
    freeze = load_json(FREEZE)
    matrix = load_json(MATRIX)
    source = freeze.get("source_decision", {})
    source_skill = freeze.get("source_skill", {})
    candidate = freeze.get("candidate_skill", {})
    change = freeze.get("change_set", {})
    delivery = freeze.get("delivery", {})
    changed = set(
        git_output(
            "diff",
            "--name-only",
            RC3_COMMIT,
            RC4_COMMIT,
            "--",
            SKILL_ROOT,
            *sorted(NEUTRAL_TEST_FILES),
        ).splitlines()
    )
    added_diff = git_output("diff", "--unified=0", RC3_COMMIT, RC4_COMMIT, "--", SKILL_ROOT)
    added_lines = "\n".join(
        line[1:]
        for line in added_diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    authorized = [
        item
        for item in matrix.get("findings", [])
        if isinstance(item, dict) and item.get("decision") == "AUTHORIZE_SINGLE_RC4_CHANGE_SET"
    ]
    checks = {
        "identity": freeze.get("schema_version") == "1.0.0"
        and freeze.get("artifact_type") == "c_target_rc4_candidate_freeze"
        and freeze.get("candidate_id") == "C-TARGET-RC4-CANDIDATE-001",
        "candidate_not_release": freeze.get("formal_release") is False
        and freeze.get("status")
        == "CANDIDATE_IMPLEMENTED_FOCUSED_TESTS_PASS_RELEASE_PENDING_UNIFIED_REGRESSION",
        "single_revision_cycle": freeze.get("revision_cycle") == 1
        and freeze.get("maximum_revision_cycles") == 2,
        "authorized_lineage": len(authorized) == 1
        and authorized[0].get("failure_id") == AUTHORIZED_FAILURE
        and source.get("failure_id") == AUTHORIZED_FAILURE
        and source.get("decision") == "AUTHORIZE_SINGLE_RC4_CHANGE_SET"
        and source.get("matrix_sha256") == sha256(MATRIX),
        "rc3_identity": source_skill.get("version") == "0.2.0-competition-rc3"
        and source_skill.get("release_commit") == RC3_COMMIT
        and source_skill.get("git_tree_sha1") == RC3_TREE
        and git_output("rev-parse", f"{RC3_COMMIT}:{SKILL_ROOT}") == RC3_TREE,
        "rc4_identity": candidate.get("version") == "0.2.0-competition-rc4"
        and candidate.get("implementation_commit") == RC4_COMMIT
        and candidate.get("git_tree_sha1") == RC4_TREE
        and git_output("rev-parse", f"{RC4_COMMIT}:{SKILL_ROOT}") == RC4_TREE,
        "one_change_set": change.get("count") == 1
        and change.get("preflight_is_result") is False
        and change.get("preflight_ranking_eligible") is False
        and change.get("preflight_values_are_placeholders") is True
        and change.get("preflight_hash_bound_to_case_state") is True
        and change.get("invalid_execute_output_retained") is True,
        "no_scope_expansion": change.get("case_specific_branches") == 0
        and change.get("second_state_truth_added") is False
        and change.get("third_party_integration_added") is False,
        "exact_changed_files": changed == FORMAL_FILES | NEUTRAL_TEST_FILES
        and set(freeze.get("changed_formal_skill_files", [])) == FORMAL_FILES
        and set(freeze.get("changed_neutral_test_files", [])) == NEUTRAL_TEST_FILES,
        "anti_hardcoding": not any(term in added_lines for term in FORBIDDEN_ADDED_TERMS)
        and freeze.get("anti_hardcoding", {}).get("result") == "PASS",
        "one_formal_skill": len(list((ROOT / ".agents/skills").glob("*/SKILL.md"))) == 1
        and candidate.get("formal_skill_count") == 1,
        "focused_tests": freeze.get("focused_validation", {}).get("focused_tests")
        == {"passed": 21, "failed": 0},
        "remote_receipt": delivery.get("branch") == "feat/phase004c-c-target-batch-generalization"
        and delivery.get("remote") == "origin"
        and delivery.get("remote_sha") == RC4_COMMIT,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "candidate_id": freeze.get("candidate_id"),
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "ok": not failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
