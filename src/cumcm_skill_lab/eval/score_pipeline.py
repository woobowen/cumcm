"""Offline anonymous score freeze and reproducibility checks."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .anonymization import assert_identity_free
from .models import canonical_json, file_sha256, load_json, sha256_text, validate_json, write_json
from .scoring import score_observation


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _current_runs(root: Path) -> dict[tuple[str, str], Path]:
    current: dict[tuple[str, str], Path] = {}
    for path in sorted((root / "evals/results/phase-002/runs").rglob("*.json")):
        run = load_json(path)
        key = (run["anonymous_arm_id"], run["case_id"])
        previous = current.get(key)
        if previous is None or run["run_index"] > load_json(previous)["run_index"]:
            current[key] = path
    return current


def _score_hash(score: dict) -> str:
    content = dict(score)
    content.pop("initial_score_hash", None)
    return sha256_text(canonical_json(content))


def combine_score(
    observation: dict,
    run: dict,
    rubric: dict,
    review: dict,
    *,
    recovered: bool,
    frozen_at: str,
) -> dict:
    maxima = {"A": 10, "B": 8, "C": 6, "D": 6}
    for key, maximum in maxima.items():
        value = float(review["dimensions"][key]["score"])
        if not 0 <= value <= maximum:
            raise RuntimeError(f"REVIEW_DIMENSION_OUT_OF_RANGE:{key}")
    if float(review["score"]) != sum(float(review["dimensions"][key]["score"]) for key in maxima):
        raise RuntimeError("REVIEW_TOTAL_MISMATCH")
    deterministic = score_observation(observation, rubric, run, recovered=recovered)
    if deterministic["status"] != "SCORED":
        raise RuntimeError("CURRENT_CELL_NOT_SCORABLE")
    reviewer_dimensions = {
        f"REVIEWER-{key}": {
            "score": value["score"],
            "evidence": value["evidence"],
            "missing": value["missing"],
            "confidence": value["confidence"],
            "source": "REVIEWER",
            "affected_by_run_failure": recovered,
        }
        for key, value in review["dimensions"].items()
    }
    deterministic_score = deterministic["deterministic_score"]
    reviewer_score = float(review["score"])
    score = {
        "schema_version": "1.0.0",
        "score_id": (
            f"SCORE-{run['anonymous_arm_id']}-{run['case_id']}-RUN-{run['run_index']:03d}"
        ),
        "evaluation_id": run["evaluation_id"],
        "case_id": run["case_id"],
        "anonymous_arm_id": run["anonymous_arm_id"],
        "run_index": run["run_index"],
        "status": "SCORED",
        "deterministic_score": deterministic_score,
        "reviewer_score": reviewer_score,
        "total_score": deterministic_score + reviewer_score,
        "dimensions": {**deterministic["dimensions"], **reviewer_dimensions},
        "hard_failures": deterministic["hard_failures"],
        "evidence": deterministic["evidence"] + review["citations"],
        "missing": deterministic["missing"]
        + [item for value in review["dimensions"].values() for item in value["missing"]],
        "confidence": "LOW" if recovered else review["confidence"],
        "affected_by_run_failure": recovered,
        "identity_revealed": False,
        "initial_score_hash": "",
        "frozen_at": frozen_at,
    }
    score["initial_score_hash"] = _score_hash(score)
    return score


def freeze_scores(root: Path, *, check: bool = False) -> dict:
    current_runs = _current_runs(root)
    candidate_ids = [
        item["candidate_id"]
        for item in load_json(
            root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
        )["arms"]
        if item["candidate_id"]
    ]
    errors: list[str] = []
    score_hashes: dict[str, str] = {}
    review_hashes: dict[str, str] = {}
    run_hashes: dict[str, str] = {}
    recovery_hashes: dict[str, str] = {}
    frozen_at = _now()
    manifest_path = root / "evals/results/phase-002/score_freeze.json"
    if manifest_path.is_file():
        frozen_at = load_json(manifest_path)["frozen_at"]
    for (arm, case_id), run_path in sorted(current_runs.items()):
        run = load_json(run_path)
        observation_path = (
            root
            / "evals/results/phase-002/observations"
            / arm
            / case_id
            / f"run-{run['run_index']:03d}.json"
        )
        review_path = (
            root
            / "evals/results/phase-002/reviews"
            / arm
            / case_id
            / f"run-{run['run_index']:03d}.json"
        )
        score_path = (
            root
            / "evals/results/phase-002/scores"
            / arm
            / case_id
            / f"run-{run['run_index']:03d}.json"
        )
        recovery_path = (
            root
            / "evals/results/phase-002/recoveries"
            / arm
            / case_id
            / f"run-{run['run_index']:03d}.recovery.json"
        )
        if not observation_path.is_file() or not review_path.is_file():
            errors.append(f"SCORE_INPUT_MISSING:{arm}:{case_id}")
            continue
        observation = load_json(observation_path)
        review = load_json(review_path)
        recovered = recovery_path.is_file()
        for schema, data, path in (
            ("eval_observation", observation, observation_path),
            ("eval_review", review, review_path),
        ):
            errors.extend(
                f"SCORE_INPUT_SCHEMA:{path.relative_to(root)}:{item}"
                for item in validate_json(data, root / f"contracts/{schema}.schema.json")
            )
        if any(
            review.get(key) != run[key]
            for key in ("evaluation_id", "case_id", "anonymous_arm_id", "run_index")
        ):
            errors.append(f"REVIEW_RUN_MISMATCH:{arm}:{case_id}")
            continue
        assert_identity_free(review, candidate_ids)
        rubric = load_json(root / "evals/rubrics/phase-002" / f"{case_id}.json")
        score = combine_score(
            observation,
            run,
            rubric,
            review,
            recovered=recovered,
            frozen_at=frozen_at,
        )
        assert_identity_free(score, candidate_ids)
        score_errors = validate_json(score, root / "contracts/eval_score.schema.json")
        if score_errors:
            errors.extend(f"SCORE_SCHEMA:{arm}:{case_id}:{item}" for item in score_errors)
            continue
        if check:
            if not score_path.is_file() or load_json(score_path) != score:
                errors.append(f"SCORE_MISMATCH:{score_path.relative_to(root)}")
                continue
        else:
            if score_path.exists():
                errors.append(f"SCORE_WOULD_OVERWRITE:{score_path.relative_to(root)}")
                continue
            write_json(score_path, score)
        relative = score_path.relative_to(root).as_posix()
        score_hashes[relative] = file_sha256(score_path)
        review_hashes[review_path.relative_to(root).as_posix()] = file_sha256(review_path)
        run_hashes[run_path.relative_to(root).as_posix()] = file_sha256(run_path)
        if recovered:
            recovery_hashes[recovery_path.relative_to(root).as_posix()] = file_sha256(recovery_path)
    manifest = {
        "schema_version": "1.0.0",
        "evaluation_id": "PHASE-002-FIRST-ROUND",
        "status": "ANONYMOUS_SCORES_FROZEN",
        "score_count": len(score_hashes),
        "score_hashes": score_hashes,
        "review_hashes": review_hashes,
        "run_hashes": run_hashes,
        "recovery_hashes": recovery_hashes,
        "rubric_hashes": {
            path.relative_to(root).as_posix(): file_sha256(path)
            for path in sorted((root / "evals/rubrics/phase-002").glob("*.json"))
        },
        "frozen_at": frozen_at,
        "identity_revealed": False,
    }
    if check:
        if not manifest_path.is_file() or load_json(manifest_path) != manifest:
            errors.append("SCORE_FREEZE_MANIFEST_MISMATCH")
    elif not errors:
        if manifest_path.exists():
            errors.append("SCORE_FREEZE_WOULD_OVERWRITE")
        else:
            write_json(manifest_path, manifest)
    return {
        "status": "PASS" if not errors and len(score_hashes) == 18 else "FAIL",
        "score_count": len(score_hashes),
        "errors": errors,
    }
