#!/usr/bin/env python3
"""Check the three isolated RC4 C-target Development regressions."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "evals/results/phase-004c-c-batch"
RC4_COMMIT = "297cad0a29c659b18484d4f3b67d69a942ad415c"
RC4_TREE = "d041ca38de030ae04813ef02dbe12f7f2b7a1c22"
CASES = {
    "CUMCM-2022-C-DEVELOPMENT-BATCH-001": {
        "case_id": "CUMCM-2022-C-DEVELOPMENT-RC4-REGRESSION",
        "attempt": 2,
        "selected": "HELLINGER_KNN_COMPLETE",
        "requirements": 13,
        "perturbations": 2,
        "prior_attempts": 1,
    },
    "CUMCM-2021-C-DEVELOPMENT-BATCH-002": {
        "case_id": "CUMCM-2021-C-DEVELOPMENT-RC4-REGRESSION",
        "attempt": 1,
        "selected": "BASELINE_MEAN_GREEDY",
        "requirements": 17,
        "perturbations": 3,
        "prior_attempts": 0,
    },
    "CUMCM-2020-C-DEVELOPMENT-BATCH-003": {
        "case_id": "CUMCM-2020-C-DEVELOPMENT-RC4-REGRESSION",
        "attempt": 2,
        "selected": "RANDOM_FOREST_SCENARIO_ALLOCATOR",
        "requirements": 6,
        "perturbations": 3,
        "prior_attempts": 1,
    },
}
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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commit_exists(commit: Any) -> bool:
    if not isinstance(commit, str):
        return False
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        ).returncode
        == 0
    )


def validate_record(
    tracked_case_id: str, expected: dict[str, Any], *, verify_workspaces: bool
) -> list[str]:
    errors: list[str] = []
    path = RESULT_ROOT / tracked_case_id / "rc4/development_regression_evidence.json"
    if not path.is_file():
        return [f"RC4_BATCH_REGRESSION_EVIDENCE_MISSING:{tracked_case_id}"]
    record = load_json(path)
    skill = record.get("skill", {})
    preflight = record.get("output_contract_preflight", {})
    stages = record.get("stage_status")
    runs = record.get("runs")
    prior = record.get("preserved_prior_attempts")
    if (
        record.get("schema_version") != "1.0.0"
        or record.get("artifact_type") != "c_target_rc4_development_regression_evidence"
        or record.get("case_id") != expected["case_id"]
        or record.get("source_first_run_case_id") != tracked_case_id
        or record.get("evidence_class") != "DEVELOPMENT_REGRESSION_NOT_BLIND_NOT_VALIDATION"
        or record.get("answer_access_status") != "UNLOCKED_AFTER_FIRST_RUN"
        or record.get("attempt_number") != expected["attempt"]
    ):
        errors.append(f"RC4_BATCH_REGRESSION_IDENTITY_INVALID:{tracked_case_id}")
    freeze = record.get("first_run_freeze", {})
    freeze_path = ROOT / str(freeze.get("path", ""))
    if (
        not freeze_path.is_file()
        or freeze.get("sha256") != file_hash(freeze_path)
        or not str(freeze_path).endswith("first_run_freeze.v2.json")
    ):
        errors.append(f"RC4_BATCH_REGRESSION_FIRST_RUN_BINDING_INVALID:{tracked_case_id}")
    if (
        skill.get("version") != "0.2.0-competition-rc4"
        or skill.get("candidate_implementation_commit") != RC4_COMMIT
        or skill.get("git_tree_sha1") != RC4_TREE
        or not commit_exists(skill.get("execution_code_commit"))
    ):
        errors.append(f"RC4_BATCH_REGRESSION_SKILL_BINDING_INVALID:{tracked_case_id}")
    if preflight != {
        "status": "PASS",
        "reason_codes": ["RC_OUTPUT_CONTRACT_VALID"],
        "path": "experiments/selected_output_contract_probe.json",
    }:
        errors.append(f"RC4_BATCH_REGRESSION_PREFLIGHT_INVALID:{tracked_case_id}")
    if (
        not isinstance(stages, list)
        or [item.get("stage") for item in stages if isinstance(item, dict)] != list(STAGES)
        or any(not isinstance(item, dict) or item.get("status") != "PASS" for item in stages)
    ):
        errors.append(f"RC4_BATCH_REGRESSION_STAGE_SET_INVALID:{tracked_case_id}")
    if (
        record.get("requirements_total") != expected["requirements"]
        or record.get("requirements_with_output_claims") != expected["requirements"]
        or not isinstance(runs, list)
        or len(runs) != 3
        or record.get("valid_run_count") != 3
        or record.get("failed_run_count") != 0
        or any(item.get("outcome") != "SUCCESS" for item in runs if isinstance(item, dict))
        or record.get("baseline_success") is not True
        or record.get("selected_candidate_id") != expected["selected"]
        or not isinstance(record.get("selected_validation_score"), (int, float))
        or isinstance(record.get("selected_validation_score"), bool)
        or record.get("robustness_perturbation_count") != expected["perturbations"]
        or record.get("claim_gate") != "PASS"
        or record.get("handoff_gate") != "PASS"
        or record.get("terminal_state") != "READY_FOR_PAPER_HANDOFF"
        or record.get("universal_hard_failure") is not False
    ):
        errors.append(f"RC4_BATCH_REGRESSION_OUTCOME_INVALID:{tracked_case_id}")
    if (
        not isinstance(prior, list)
        or len(prior) != expected["prior_attempts"]
        or any(item.get("preserved") is not True for item in prior if isinstance(item, dict))
    ):
        errors.append(f"RC4_BATCH_REGRESSION_RECOVERY_LEDGER_INVALID:{tracked_case_id}")
    if any(
        record.get(name) != expected_value
        for name, expected_value in (
            ("api_calls", 0),
            ("third_party_executions", 0),
            ("model_training", False),
        )
    ):
        errors.append(f"RC4_BATCH_REGRESSION_SCOPE_INVALID:{tracked_case_id}")
    if verify_workspaces:
        workspace = ROOT / str(record.get("workspace_relative", ""))
        state_path = workspace / "case_state.json"
        if (
            not state_path.is_file()
            or load_json(state_path).get("state") != "READY_FOR_PAPER_HANDOFF"
            or len(list((workspace / "runs").glob("*/manifest.json"))) != 3
            or not (workspace / "handoff/modeling_to_paper.json").is_file()
        ):
            errors.append(f"RC4_BATCH_REGRESSION_WORKSPACE_INVALID:{tracked_case_id}")
        for item in prior if isinstance(prior, list) else []:
            prior_workspace = ROOT / str(item.get("workspace_relative", ""))
            if not prior_workspace.is_dir() or not (prior_workspace / "case_state.json").is_file():
                errors.append(f"RC4_BATCH_REGRESSION_PRIOR_NOT_PRESERVED:{tracked_case_id}")
    return errors


def evaluate(*, verify_workspaces: bool = False) -> dict[str, Any]:
    errors = [
        error
        for tracked_case_id, expected in CASES.items()
        for error in validate_record(tracked_case_id, expected, verify_workspaces=verify_workspaces)
    ]
    tracked_raw = subprocess.run(
        ["git", "ls-files", ".cache/official_inputs"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked_raw.returncode != 0 or tracked_raw.stdout.strip():
        errors.append("RC4_BATCH_REGRESSION_RAW_TRACKING_INVALID")
    errors = sorted(set(errors))
    return {
        "case_count": len(CASES),
        "verify_workspaces": verify_workspaces,
        "error_count": len(errors),
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--verify-workspaces", action="store_true")
    args = parser.parse_args()
    result = evaluate(verify_workspaces=args.verify_workspaces)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
