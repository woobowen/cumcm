import pytest

from cumcm_skill_lab.eval.review_import import normalize_review


def _item():
    return {
        "anonymous_arm_id": "ARM-A",
        "case_id": "CASE-001",
        "run_index": 1,
        "score": 20,
        "dimensions": {
            "A": {"score": 7, "evidence": ["requirements"], "missing": [], "confidence": "HIGH"},
            "B": {"score": 5, "evidence": ["baseline"], "missing": [], "confidence": "MEDIUM"},
            "C": {"score": 4, "evidence": ["validation"], "missing": [], "confidence": "MEDIUM"},
            "D": {"score": 4, "evidence": ["trace"], "missing": [], "confidence": "MEDIUM"},
        },
        "overall_assessment": "Evidence is useful but incomplete.",
    }


def test_review_normalization_keeps_identity_hidden():
    review = normalize_review(
        _item(),
        reviewer_id="READONLY-ANON-MODELING-001",
        affected_by_run_failure=False,
        reviewed_at="2026-08-31T00:00:00Z",
    )
    assert review["score"] == 20
    assert review["identity_visible"] is False
    assert review["deterministic_score_visible"] is False


def test_recovery_forces_low_confidence():
    review = normalize_review(
        _item(),
        reviewer_id="READONLY-ANON-MODELING-001",
        affected_by_run_failure=True,
        reviewed_at="2026-08-31T00:00:00Z",
    )
    assert review["confidence"] == "LOW"
    assert review["affected_by_run_failure"] is True


def test_review_total_must_equal_dimensions():
    item = _item()
    item["score"] = 30
    with pytest.raises(ValueError, match="REVIEW_TOTAL_MISMATCH"):
        normalize_review(
            item,
            reviewer_id="READONLY-ANON-MODELING-001",
            affected_by_run_failure=False,
            reviewed_at="2026-08-31T00:00:00Z",
        )
