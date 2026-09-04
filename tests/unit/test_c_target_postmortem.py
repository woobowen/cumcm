from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.check_c_target_postmortem import (
    MATRIX_PATH,
    REVIEWS_PATH,
    ROOT,
    UNLOCK_PATH,
    validate_matrix,
    validate_reviews,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_postmortem_documents_are_valid() -> None:
    reviews = load(REVIEWS_PATH)
    matrix = load(MATRIX_PATH)
    unlock = load(UNLOCK_PATH)
    assert validate_reviews(reviews, unlock) == []
    assert validate_matrix(matrix, reviews) == []


def test_rc4_admission_rejects_case_specific_change() -> None:
    reviews = load(REVIEWS_PATH)
    matrix = copy.deepcopy(load(MATRIX_PATH))
    authorized = next(
        item for item in matrix["findings"] if item["decision"] == "AUTHORIZE_SINGLE_RC4_CHANGE_SET"
    )
    authorized["proposed_skill_change"] += " for 2022"
    assert any(
        error.startswith("POSTMORTEM_RC4_ADMISSION_INVALID")
        for error in validate_matrix(matrix, reviews)
    )


def test_reference_review_rejects_premature_access() -> None:
    reviews = copy.deepcopy(load(REVIEWS_PATH))
    unlock = load(UNLOCK_PATH)
    reviews["cases"][0]["references"][0]["accessed_at"] = unlock["unlock_time"]
    assert any(
        error.startswith("POSTMORTEM_REFERENCE_RECORD_INVALID")
        for error in validate_reviews(reviews, unlock, root=ROOT)
    )
