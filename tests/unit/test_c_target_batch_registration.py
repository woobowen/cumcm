from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import register_c_target_batch_case as registration


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_verify_inputs_binds_archive_problem_and_data(tmp_path: Path) -> None:
    archive = tmp_path / "raw/archive/problems.rar"
    problem = tmp_path / "raw/case_files/problem.pdf"
    data = tmp_path / "raw/case_files/data.xlsx"
    for path, value in ((archive, b"rar"), (problem, b"pdf"), (data, b"xlsx")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    metadata = {
        "archive": {
            "local_path": "raw/archive/problems.rar",
            "sha256": _hash(archive),
            "size_bytes": archive.stat().st_size,
        },
        "extracted_c_files": [
            {
                "path": "raw/case_files/problem.pdf",
                "role": "PROBLEM",
                "sha256": _hash(problem),
                "size_bytes": problem.stat().st_size,
            },
            {
                "path": "raw/case_files/data.xlsx",
                "role": "DATA",
                "sha256": _hash(data),
                "size_bytes": data.stat().st_size,
            },
        ],
    }

    checked_archive, checked_files = registration.verify_inputs(tmp_path, metadata)

    assert checked_archive["sha256"] == _hash(archive)
    assert [item["role"] for item in checked_files] == ["PROBLEM", "DATA"]


def test_verify_inputs_rejects_path_escape_and_hash_drift(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.rar"
    outside.write_bytes(b"outside")
    metadata = {
        "archive": {
            "local_path": "../outside.rar",
            "sha256": _hash(outside),
            "size_bytes": outside.stat().st_size,
        },
        "extracted_c_files": [
            {
                "path": "raw/case_files/problem.pdf",
                "role": "PROBLEM",
                "sha256": "0" * 64,
                "size_bytes": 1,
            }
        ],
    }
    with pytest.raises(ValueError, match="OFFICIAL_INPUT_PATH_INVALID"):
        registration.verify_inputs(tmp_path, metadata)


def test_live_batch_state_gate_is_fail_closed(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    valid = {
        "active_skill_version": registration.SKILL_VERSION,
        "batch_reference_unlocked": False,
        "batch_skill_frozen": True,
        "current_batch_id": registration.BATCH_ID,
        "phase": registration.PHASE,
        "technical_adjudication_status": "C_TARGET_BATCH_IN_PROGRESS",
    }
    state.write_text(json.dumps(valid), encoding="utf-8")
    registration.require_live_batch_state(state)
    valid["batch_reference_unlocked"] = True
    state.write_text(json.dumps(valid), encoding="utf-8")
    with pytest.raises(ValueError, match="C_TARGET_BATCH_STATE_NOT_READY"):
        registration.require_live_batch_state(state)
