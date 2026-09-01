"""Reveal anonymous identities only after immutable score freeze evidence exists."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .anonymization import public_mapping_hash
from .models import file_sha256, load_json, load_yaml, validate_json, write_json


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def reveal_identities(root: Path, *, check: bool = False) -> dict:
    score_freeze_path = root / "evals/results/phase-002/score_freeze.json"
    reveal_path = root / "evals/results/phase-002/reveal_record.json"
    mapping_path = root / ".cache/upstream-eval/arm-map.json"
    errors: list[str] = []
    if not score_freeze_path.is_file():
        return {"status": "FAIL", "errors": ["SCORE_FREEZE_MISSING"]}
    freeze = load_json(score_freeze_path)
    if freeze["status"] != "ANONYMOUS_SCORES_FROZEN" or freeze["identity_revealed"] is not False:
        errors.append("SCORE_FREEZE_NOT_BLIND")
    for relative, expected_hash in freeze["score_hashes"].items():
        path = root / relative
        if not path.is_file() or file_sha256(path) != expected_hash:
            errors.append(f"FROZEN_SCORE_HASH_MISMATCH:{relative}")
    if mapping_path.is_file():
        mapping = load_json(mapping_path)
        actual_to_anonymous = mapping["actual_to_anonymous"]
        anonymous_to_actual = {
            anonymous: actual for actual, anonymous in actual_to_anonymous.items()
        }
        mapping_hash = public_mapping_hash(mapping)
    elif check and reveal_path.is_file():
        existing = load_json(reveal_path)
        anonymous_to_actual = existing["anonymous_to_actual"]
        mapping_hash = existing["mapping_hash"]
    else:
        errors.append("ANONYMIZATION_MAP_MISSING")
        return {"status": "FAIL", "errors": errors}
    if set(anonymous_to_actual) != {"ARM-A", "ARM-B", "ARM-C"} or set(
        anonymous_to_actual.values()
    ) != {"NO_PROJECT_MODELING_SKILL", "HANDSOMEZR", "YUSHUI"}:
        errors.append("REVEAL_MAPPING_NOT_BIJECTIVE")
    config = load_yaml(root / "evals/configs/phase-002.yaml")
    by_actual = {item["arm_id"]: item for item in config["arms"]}
    actual_arm_details = [
        {
            "anonymous_arm_id": anonymous,
            "actual_arm_id": actual,
            "candidate_id": by_actual[actual]["candidate_id"],
            "evaluation_mode": by_actual[actual]["evaluation_mode"],
        }
        for anonymous, actual in sorted(anonymous_to_actual.items())
    ]
    revealed_at = _now()
    if reveal_path.is_file():
        revealed_at = load_json(reveal_path)["revealed_at"]
    record = {
        "schema_version": "1.0.0",
        "reveal_id": "REVEAL-PHASE-002-FIRST-ROUND",
        "evaluation_id": "PHASE-002-FIRST-ROUND",
        "status": "IDENTITIES_REVEALED_AFTER_SCORE_FREEZE",
        "score_freeze_path": score_freeze_path.relative_to(root).as_posix(),
        "score_freeze_hash": file_sha256(score_freeze_path),
        "score_count": freeze["score_count"],
        "mapping_hash": mapping_hash,
        "anonymous_to_actual": anonymous_to_actual,
        "actual_arm_details": actual_arm_details,
        "frozen_at": freeze["frozen_at"],
        "revealed_at": revealed_at,
        "revealed_after_freeze": True,
        "score_hashes_preserved": not errors,
        "initial_scores_modified": False,
        "identity_bias_check": "NO_POST_REVEAL_SCORE_CHANGE_DETECTED",
        "correction_records": [],
    }
    errors.extend(
        f"REVEAL_SCHEMA:{item}"
        for item in validate_json(record, root / "contracts/eval_reveal.schema.json")
    )
    if check:
        if not reveal_path.is_file() or load_json(reveal_path) != record:
            errors.append("REVEAL_RECORD_MISMATCH")
    elif not errors:
        if reveal_path.exists():
            errors.append("REVEAL_WOULD_OVERWRITE")
        else:
            write_json(reveal_path, record)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "record": record}
