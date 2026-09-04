#!/usr/bin/env python3
"""Promote one pre-acquisition C batch record after verifying ignored official inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "benchmarks/case_registry.yaml"
DEFAULT_PROJECT_STATE = REPO_ROOT / "state/project_state.json"
DEFAULT_INPUT_REGISTRATION = REPO_ROOT / "evals/results/phase-004c-c-batch/input_registration.json"
CASE_CLI = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
PHASE = "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C"
BATCH_ID = "C-TARGET-BATCH-001"
SKILL_VERSION = "0.2.0-competition-rc3"
SKILL_COMMIT = "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_file(case_root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if not relative or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("OFFICIAL_INPUT_PATH_INVALID")
    resolved = (case_root / candidate).resolve()
    try:
        resolved.relative_to(case_root.resolve())
    except ValueError as exc:
        raise ValueError("OFFICIAL_INPUT_PATH_INVALID") from exc
    if not resolved.is_file():
        raise ValueError("OFFICIAL_INPUT_MISSING")
    return resolved


def load_object(path: Path, *, json_file: bool = False) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    value = json.loads(raw) if json_file else yaml.safe_load(raw)
    if not isinstance(value, dict):
        raise ValueError("REGISTRATION_DOCUMENT_INVALID")
    return value


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    os.replace(temporary, path)


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def iso_time(value: str | None) -> str:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("START_TIME_INVALID") from exc
    if parsed.utcoffset() is None:
        raise ValueError("START_TIME_TIMEZONE_REQUIRED")
    return value


def require_live_batch_state(path: Path) -> None:
    state = load_object(path, json_file=True)
    if (
        state.get("phase") != PHASE
        or state.get("technical_adjudication_status") != "C_TARGET_BATCH_IN_PROGRESS"
        or state.get("current_batch_id") != BATCH_ID
        or state.get("active_skill_version") != SKILL_VERSION
        or state.get("batch_skill_frozen") is not True
        or state.get("batch_reference_unlocked") is not False
    ):
        raise ValueError("C_TARGET_BATCH_STATE_NOT_READY")


def verify_skill() -> None:
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{SKILL_COMMIT}^{{commit}}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", SKILL_COMMIT, "--", ".agents/skills/cumcm-modeling-evidence"],
        cwd=REPO_ROOT,
        check=False,
    )
    if exists.returncode != 0 or unchanged.returncode != 0:
        raise ValueError("FROZEN_RC3_SKILL_DRIFT")


def input_case(metadata: dict[str, Any], case_id: str) -> dict[str, Any]:
    values = [
        item
        for item in metadata.get("cases", [])
        if isinstance(item, dict) and item.get("case_id") == case_id
    ]
    if len(values) != 1:
        raise ValueError("INPUT_REGISTRATION_CASE_NOT_UNIQUE")
    return values[0]


def verify_inputs(
    case_root: Path, metadata: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    archive = metadata.get("archive")
    extracted = metadata.get("extracted_c_files")
    if not isinstance(archive, dict) or not isinstance(extracted, list) or not extracted:
        raise ValueError("INPUT_REGISTRATION_FIELDS_MISSING")
    archive_path = safe_file(case_root, str(archive.get("local_path", "")))
    if (
        file_hash(archive_path) != archive.get("sha256")
        or archive_path.stat().st_size != archive.get("size_bytes")
        or not HEX64.fullmatch(str(archive.get("sha256", "")))
    ):
        raise ValueError("OFFICIAL_ARCHIVE_EVIDENCE_MISMATCH")
    checked: list[dict[str, Any]] = []
    for item in extracted:
        if not isinstance(item, dict) or item.get("role") not in {"PROBLEM", "DATA"}:
            raise ValueError("EXTRACTED_C_FILE_RECORD_INVALID")
        path = safe_file(case_root, str(item.get("path", "")))
        if (
            file_hash(path) != item.get("sha256")
            or path.stat().st_size != item.get("size_bytes")
            or not HEX64.fullmatch(str(item.get("sha256", "")))
        ):
            raise ValueError("EXTRACTED_C_FILE_EVIDENCE_MISMATCH")
        checked.append(item)
    problems = [item for item in checked if item["role"] == "PROBLEM"]
    if len(problems) != 1 or not any(item["role"] == "DATA" for item in checked):
        raise ValueError("PROBLEM_DATA_ROLE_SET_INVALID")
    return archive, checked


def promote(args: argparse.Namespace) -> dict[str, Any]:
    require_live_batch_state(args.project_state)
    verify_skill()
    registry = load_object(args.registry)
    metadata_document = load_object(args.input_registration, json_file=True)
    metadata = input_case(metadata_document, args.case_id)
    archive, files = verify_inputs(args.case_root, metadata)
    planned = [item for item in registry.get("planned_cases", []) if isinstance(item, dict)]
    matches = [item for item in planned if item.get("case_id") == args.case_id]
    if len(matches) != 1:
        if any(
            isinstance(item, dict) and item.get("case_id") == args.case_id
            for item in registry.get("cases", [])
        ):
            raise ValueError("CASE_ID_ALREADY_REGISTERED")
        raise ValueError("PLANNED_CASE_NOT_UNIQUE")
    planned_record = matches[0]
    if (
        planned_record.get("registration_status") != "PRE_ACQUISITION_REGISTERED"
        or planned_record.get("batch_id") != BATCH_ID
        or planned_record.get("formal_skill_version") != SKILL_VERSION
        or planned_record.get("formal_skill_commit") != SKILL_COMMIT
        or planned_record.get("official_page_url_sha256")
        != metadata.get("official_page_url_sha256")
        or planned_record.get("official_archive_url_sha256")
        != metadata.get("official_archive_url_sha256")
        or planned_record.get("answer_access_status") != "SEALED"
        or metadata.get("answer_access_status") != "SEALED"
    ):
        raise ValueError("PLANNED_INPUT_BINDING_MISMATCH")
    problem = next(item for item in files if item["role"] == "PROBLEM")
    data_hashes = {
        str(item["path"]): str(item["sha256"]) for item in files if item["role"] == "DATA"
    }
    start_time = iso_time(args.start_time)
    if args.dry_run:
        return {
            "answer_access_status": "SEALED",
            "case_id": args.case_id,
            "dry_run": True,
            "first_run_status": "IN_PROGRESS",
            "official_package_sha256": archive["sha256"],
            "status": "PASS",
            "strict_first_run_eligibility": metadata["strict_first_run_eligibility"],
        }
    state_path = args.case_root / "case_state.json"
    if not state_path.exists():
        completed = subprocess.run(
            [
                sys.executable,
                str(CASE_CLI),
                "init",
                "--case-root",
                str(args.case_root),
                "--case-id",
                args.case_id,
                "--kind",
                args.case_kind,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise ValueError("CASE_WORKSPACE_INITIALIZATION_FAILED")
    state = load_object(state_path, json_file=True)
    if (
        state.get("case_id") != args.case_id
        or state.get("skill_version") != SKILL_VERSION
        or state.get("state") != "CREATED"
    ):
        raise ValueError("CASE_WORKSPACE_BINDING_MISMATCH")
    binding_relative = "state/development_eval_binding.json"
    binding_path = args.case_root / binding_relative
    if binding_path.exists():
        raise ValueError("CASE_WORKSPACE_BINDING_ALREADY_EXISTS")
    binding = {
        "answer_access_status": "SEALED",
        "case_id": args.case_id,
        "data_hashes": data_hashes,
        "problem_hash": problem["sha256"],
        "problem_source": problem["path"],
        "skill_commit": SKILL_COMMIT,
        "skill_version": SKILL_VERSION,
    }
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(binding_path, binding)
    bound = {
        str(problem["path"]): str(problem["sha256"]),
        **data_hashes,
        binding_relative: file_hash(binding_path),
    }
    state["evidence_bindings"].update(bound)
    state["history"][0]["evidence"] = sorted(bound)
    write_json(state_path, state)
    record = {
        **planned_record,
        "registration_status": "INPUT_REGISTERED",
        "official_title": metadata["official_title"],
        "official_package_sha256": archive["sha256"],
        "official_archive_mime_type": archive["mime_type"],
        "official_archive_size_bytes": archive["size_bytes"],
        "official_archive_retrieved_at": archive["retrieved_at"],
        "extracted_c_files": files,
        "input_registration": {
            "path": str(args.input_registration.resolve().relative_to(REPO_ROOT)),
            "sha256": file_hash(args.input_registration),
        },
        "problem_source": problem["path"],
        "problem_hash": problem["sha256"],
        "data_hashes": data_hashes,
        "first_run_status": "IN_PROGRESS",
        "skill_version": SKILL_VERSION,
        "skill_commit": SKILL_COMMIT,
        "model": args.model,
        "reasoning": args.reasoning,
        "start_time": start_time,
        "freeze_time": None,
        "unlock_time": None,
        "generalizable_failures": [],
        "problem_specific_findings": [],
        "contamination_status": metadata["contamination_status"],
        "strict_first_run_eligibility": metadata["strict_first_run_eligibility"],
        "no_solution_exposure_result": metadata["no_solution_exposure_result"],
    }
    registry["planned_cases"] = [item for item in planned if item is not planned_record]
    registry["cases"].append(record)
    write_yaml(args.registry, registry)
    return {
        "answer_access_status": "SEALED",
        "case_id": args.case_id,
        "dry_run": args.dry_run,
        "first_run_status": "IN_PROGRESS",
        "official_package_sha256": archive["sha256"],
        "status": "PASS",
        "strict_first_run_eligibility": metadata["strict_first_run_eligibility"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument(
        "--case-kind", choices=("general", "optimization", "prediction"), default="general"
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--project-state", type=Path, default=DEFAULT_PROJECT_STATE)
    parser.add_argument("--input-registration", type=Path, default=DEFAULT_INPUT_REGISTRATION)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", required=True)
    parser.add_argument("--start-time")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = promote(args)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(
            json.dumps(
                {"reason_codes": [str(exc) or type(exc).__name__], "status": "BLOCK"},
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
