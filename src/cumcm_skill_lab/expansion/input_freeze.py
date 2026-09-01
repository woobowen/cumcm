"""Build and verify the Phase 002D immutable input manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    CONFIG_PATH,
    HISTORICAL_PHASES,
    POLICY_PATH,
    RESULT_ROOT,
    check_or_write,
    file_sha256,
    git_output,
    hashed_body,
    read_json,
    read_yaml,
    sha256_json,
    tree_file_hashes,
)

FREEZE_PATH = RESULT_ROOT / "input_freeze_manifest.json"
BASE_COMMIT = "8dd43cad3bac58ac25fdbb0d412d894d428472ae"
BOUND_CODE_PATHS = (
    "src/cumcm_skill_lab/eval/runner.py",
    "src/cumcm_skill_lab/eval/score_pipeline.py",
    "src/cumcm_skill_lab/eval/scoring.py",
    "src/cumcm_skill_lab/eval/case_generation.py",
)
BOUND_CONTRACT_PATHS = (
    "contracts/eval_observation.schema.json",
    "contracts/eval_run.schema.json",
    "contracts/eval_score.schema.json",
    "contracts/experiment_cohort.schema.json",
)


def _git_historical_integrity(root: Path) -> dict[str, Any]:
    paths = [path.as_posix() for path in HISTORICAL_PHASES]
    changed = git_output(root, "diff", "--name-only", BASE_COMMIT, "--", *paths).splitlines()
    return {
        "reference_commit": BASE_COMMIT,
        "changed_files": sorted(item for item in changed if item),
        "intact": not changed,
    }


def _decision_hashes(root: Path) -> dict[str, str]:
    directory = root / "evals/results/phase-002c/automated_decisions"
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(directory.glob("*.json"))
    }


def _package_hashes(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for arm in ("NO_PROJECT_MODELING_SKILL", "HANDSOMEZR", "YUSHUI"):
        manifest = read_json(root / f".cache/upstream-eval/packages/{arm}/package_manifest.json")
        values[arm] = manifest["package_hash"]
    return values


def build_input_freeze(root: Path) -> dict[str, Any]:
    integrity = _git_historical_integrity(root)
    if not integrity["intact"]:
        raise RuntimeError("INPUT_FREEZE_BROKEN:" + ",".join(integrity["changed_files"]))
    phase002a = read_json(root / "evals/results/phase-002a/evidence_freeze_manifest.json")
    phase002b = read_json(root / "evals/results/phase-002b/recovery_manifest.json")
    phase002c = read_json(root / "evals/results/phase-002c/input_freeze_manifest.json")
    config = read_yaml(root / CONFIG_PATH)
    policy = read_yaml(root / POLICY_PATH)
    fixture_manifest = read_json(root / "evals/fixtures/phase-002/manifest.json")
    policy_paths = (
        CONFIG_PATH.as_posix(),
        POLICY_PATH.as_posix(),
        "rules/workflow_rules.yaml",
        "rules/pre_adjudication_rules.yaml",
    )
    body = {
        "schema_version": "1.0.0",
        "freeze_id": "PHASE-002D-INPUT-FREEZE",
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "created_at": config["frozen_at"],
        "subject_commit": git_output(root, "rev-parse", "HEAD"),
        "phase002_freeze_hash": file_sha256(root / "evals/results/phase-002/score_freeze.json"),
        "phase002a_freeze_hash": phase002a["freeze_hash"],
        "phase002b_recovery_manifest_hash": file_sha256(
            root / "evals/results/phase-002b/recovery_manifest.json"
        ),
        "phase002b_input_freeze_hash": phase002b["input_freeze_hash"],
        "phase002c_input_freeze_hash": phase002c["freeze_hash"],
        "phase002c_automated_decision_hashes": _decision_hashes(root),
        "phase002c_audit_hash": file_sha256(
            root / "evals/results/phase-002c/decision_audit/audit.json"
        ),
        "phase002c_replay_hash": file_sha256(root / "evals/results/phase-002c/replay/replay.json"),
        "historical_tree_hashes": {
            path.as_posix(): sha256_json(tree_file_hashes(root, path)) for path in HISTORICAL_PHASES
        },
        "historical_git_integrity": integrity,
        "case_fixture_rubric_hashes": fixture_manifest["files"],
        "fixture_content_set_hash": fixture_manifest["content_set_hash"],
        "candidate_package_hashes": _package_hashes(root),
        "policy_hashes": {path: file_sha256(root / path) for path in policy_paths},
        "output_schema_hashes": {path: file_sha256(root / path) for path in BOUND_CONTRACT_PATHS},
        "runner_hash": file_sha256(root / "src/cumcm_skill_lab/eval/runner.py"),
        "scorer_hash": file_sha256(root / "src/cumcm_skill_lab/eval/score_pipeline.py"),
        "oracle_hash": file_sha256(root / "src/cumcm_skill_lab/eval/case_generation.py"),
        "bound_code_hashes": {path: file_sha256(root / path) for path in BOUND_CODE_PATHS},
        "codex_cli_version": config["codex_cli_version"],
        "auth_mode": config["auth_mode"],
        "proxy_transport_profile": "PENDING_CALIBRATION_PILOT",
        "model_cohort_policy": policy["model_cohort_policy"],
        "selected_primary_cases": config["primary_cases"],
        "minimum_repeats": config["minimum_repeats"],
        "historical_evidence_immutable": True,
        "scored_runs_started": False,
    }
    return hashed_body(body, "freeze_hash")


def verify_input_freeze(root: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    if manifest is None:
        if not (root / FREEZE_PATH).is_file():
            return ["PHASE002D_INPUT_FREEZE_MISSING"]
        manifest = read_json(root / FREEZE_PATH)
    errors: list[str] = []
    body = dict(manifest)
    recorded = body.pop("freeze_hash", None)
    if sha256_json(body) != recorded:
        errors.append("PHASE002D_FREEZE_HASH_MISMATCH")
    integrity = _git_historical_integrity(root)
    if not integrity["intact"]:
        errors.extend(f"HISTORICAL_INPUT_MUTATED:{path}" for path in integrity["changed_files"])
    for relative, expected in manifest["case_fixture_rubric_hashes"].items():
        if not (root / relative).is_file() or file_sha256(root / relative) != expected:
            errors.append(f"FROZEN_CASE_INPUT_MISMATCH:{relative}")
    for relative, expected in manifest["policy_hashes"].items():
        if not (root / relative).is_file() or file_sha256(root / relative) != expected:
            errors.append(f"FROZEN_POLICY_MISMATCH:{relative}")
    for relative, expected in manifest["output_schema_hashes"].items():
        if not (root / relative).is_file() or file_sha256(root / relative) != expected:
            errors.append(f"FROZEN_SCHEMA_MISMATCH:{relative}")
    for relative, expected in manifest["bound_code_hashes"].items():
        if not (root / relative).is_file() or file_sha256(root / relative) != expected:
            errors.append(f"FROZEN_CODE_MISMATCH:{relative}")
    return sorted(set(errors))


def check_or_write_input_freeze(root: Path, *, check: bool) -> dict[str, Any]:
    if check:
        errors = verify_input_freeze(root)
        manifest = read_json(root / FREEZE_PATH) if (root / FREEZE_PATH).is_file() else {}
    else:
        manifest = build_input_freeze(root)
        errors = check_or_write(root / FREEZE_PATH, manifest, check=False)
        errors.extend(verify_input_freeze(root, manifest))
    return {
        "status": "PASS" if not errors else "INPUT_FREEZE_BROKEN",
        "errors": errors,
        "freeze_hash": manifest.get("freeze_hash"),
        "subject_commit": manifest.get("subject_commit"),
    }
