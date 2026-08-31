"""Validate and materialize read-only anonymous reviewer output."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .anonymization import assert_identity_free
from .models import load_json, validate_json, write_json

MAXIMA = {"A": 10, "B": 8, "C": 6, "D": 6}
CONFIDENCE_MAP = {
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "UNKNOWN": "UNKNOWN",
    "高": "HIGH",
    "中": "MEDIUM",
    "低": "LOW",
    "未知": "UNKNOWN",
}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_review(
    item: dict,
    *,
    reviewer_id: str,
    affected_by_run_failure: bool,
    reviewed_at: str,
) -> dict:
    if set(item.get("dimensions", {})) != set(MAXIMA):
        raise ValueError("REVIEW_DIMENSIONS_INVALID")
    total = 0.0
    citations: list[str] = []
    confidences: list[str] = []
    for key, maximum in MAXIMA.items():
        dimension = dict(item["dimensions"][key])
        value = float(dimension["score"])
        if not 0 <= value <= maximum:
            raise ValueError(f"REVIEW_DIMENSION_OUT_OF_RANGE:{key}")
        total += value
        try:
            dimension["confidence"] = CONFIDENCE_MAP[dimension["confidence"]]
        except KeyError as exc:
            raise ValueError(f"REVIEW_CONFIDENCE_INVALID:{key}") from exc
        item["dimensions"][key] = dimension
        confidences.append(dimension["confidence"])
        citations.extend(f"reviewer:{key}:{evidence}" for evidence in dimension["evidence"])
    if total != float(item["score"]):
        raise ValueError("REVIEW_TOTAL_MISMATCH")
    confidence = "LOW" if affected_by_run_failure or "LOW" in confidences else "MEDIUM"
    if not affected_by_run_failure and confidences and set(confidences) == {"HIGH"}:
        confidence = "HIGH"
    arm = item["anonymous_arm_id"]
    case_id = item["case_id"]
    run_index = int(item["run_index"])
    return {
        "schema_version": "1.0.0",
        "review_id": f"REVIEW-{arm}-{case_id}-RUN-{run_index:03d}",
        "evaluation_id": "PHASE-002-FIRST-ROUND",
        "case_id": case_id,
        "anonymous_arm_id": arm,
        "run_index": run_index,
        "reviewer_id": reviewer_id,
        "reviewer_source": "READ_ONLY_SUBAGENT",
        "status": "REVIEWED",
        "score": total,
        "dimensions": item["dimensions"],
        "overall_assessment": item["overall_assessment"],
        "citations": citations or ["reviewer:no-positive-evidence"],
        "confidence": confidence,
        "affected_by_run_failure": affected_by_run_failure,
        "identity_visible": False,
        "deterministic_score_visible": False,
        "candidate_metadata_visible": False,
        "reviewed_at": reviewed_at,
    }


def import_reviews(root: Path, source_path: Path | None = None, *, check: bool = False) -> dict:
    candidate_ids = [
        item["candidate_id"]
        for item in load_json(
            root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
        )["arms"]
        if item["candidate_id"]
    ]
    review_root = root / "evals/results/phase-002/reviews"
    errors: list[str] = []
    if check:
        paths = sorted(review_root.rglob("*.json")) if review_root.exists() else []
        for path in paths:
            review = load_json(path)
            assert_identity_free(review, candidate_ids)
            errors.extend(
                f"REVIEW_SCHEMA:{path.relative_to(root)}:{item}"
                for item in validate_json(review, root / "contracts/eval_review.schema.json")
            )
            run_path = (
                root
                / "evals/results/phase-002/runs"
                / review["anonymous_arm_id"]
                / review["case_id"]
                / f"run-{review['run_index']:03d}.json"
            )
            if not run_path.is_file():
                errors.append(f"REVIEW_RUN_MISSING:{path.relative_to(root)}")
        return {
            "status": "PASS" if len(paths) == 18 and not errors else "FAIL",
            "review_count": len(paths),
            "errors": errors,
        }
    if source_path is None or not source_path.is_file():
        return {"status": "FAIL", "review_count": 0, "errors": ["REVIEW_SOURCE_MISSING"]}
    source = load_json(source_path)
    if source.get("identity_visible") is not False:
        errors.append("REVIEW_SOURCE_IDENTITY_VISIBLE")
    if source.get("deterministic_score_visible") is not False:
        errors.append("REVIEW_SOURCE_DETERMINISTIC_SCORE_VISIBLE")
    reviewer_id = source.get("reviewer_id", "")
    items = source.get("reviews", [])
    keys = {
        (item.get("anonymous_arm_id"), item.get("case_id"), item.get("run_index")) for item in items
    }
    if len(items) != 18 or len(keys) != 18:
        errors.append("REVIEW_SOURCE_CARDINALITY_INVALID")
    reviewed_at = _now()
    records: list[tuple[Path, dict]] = []
    for item in items:
        arm = item.get("anonymous_arm_id")
        case_id = item.get("case_id")
        run_index = item.get("run_index")
        recovery_path = (
            root
            / "evals/results/phase-002/recoveries"
            / str(arm)
            / str(case_id)
            / f"run-{int(run_index):03d}.recovery.json"
        )
        try:
            record = normalize_review(
                item,
                reviewer_id=reviewer_id,
                affected_by_run_failure=recovery_path.is_file(),
                reviewed_at=reviewed_at,
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"REVIEW_SOURCE_INVALID:{arm}:{case_id}:{exc}")
            continue
        assert_identity_free(record, candidate_ids)
        errors.extend(
            f"REVIEW_SCHEMA:{arm}:{case_id}:{schema_error}"
            for schema_error in validate_json(record, root / "contracts/eval_review.schema.json")
        )
        target = review_root / str(arm) / str(case_id) / f"run-{int(run_index):03d}.json"
        if target.exists():
            errors.append(f"REVIEW_WOULD_OVERWRITE:{target.relative_to(root)}")
        records.append((target, record))
    if errors:
        return {"status": "FAIL", "review_count": 0, "errors": errors}
    for path, record in records:
        write_json(path, record)
    return {"status": "PASS", "review_count": len(records), "errors": []}
