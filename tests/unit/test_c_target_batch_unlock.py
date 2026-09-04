from __future__ import annotations

import json

import pytest

from scripts.unlock_c_target_batch import parse_commit_bindings, validate_search_log


def test_unlock_commit_bindings_require_exact_case_set() -> None:
    values = [
        f"CUMCM-2022-C-DEVELOPMENT-BATCH-001={'a' * 40}",
        f"CUMCM-2021-C-DEVELOPMENT-BATCH-002={'b' * 40}",
        f"CUMCM-2020-C-DEVELOPMENT-BATCH-003={'c' * 40}",
    ]
    assert parse_commit_bindings(values)["CUMCM-2020-C-DEVELOPMENT-BATCH-003"] == "c" * 40
    with pytest.raises(ValueError, match="FREEZE_COMMIT_BINDING_SET_INVALID"):
        parse_commit_bindings(values[:2])


def test_unlock_search_log_rejects_solution_exposure(tmp_path) -> None:
    path = tmp_path / "search.jsonl"
    safe = {
        "answer_state": "SEALED",
        "access_class": "OFFICIAL_INPUT_PAGE",
        "no_solution_exposure": True,
    }
    path.write_text(json.dumps(safe) + "\n", encoding="utf-8")
    assert validate_search_log(path) == 1
    unsafe = {**safe, "access_class": "SOLUTION_SEARCH"}
    path.write_text(json.dumps(unsafe) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="EXPOSURE_UNRESOLVED"):
        validate_search_log(path)
