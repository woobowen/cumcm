"""Ignored arm mapping and public identity-free helpers."""

import json
import random
from pathlib import Path

from .models import canonical_json, sha256_text


def expected_mapping(arm_ids: list[str], labels: list[str], seed: int) -> dict:
    if len(arm_ids) != len(labels) or len(set(arm_ids)) != len(arm_ids):
        raise ValueError("ANONYMIZATION_CARDINALITY_INVALID")
    shuffled = list(labels)
    random.Random(seed).shuffle(shuffled)
    return {
        "schema_version": "1.0.0",
        "seed": seed,
        "actual_to_anonymous": dict(zip(arm_ids, shuffled, strict=True)),
    }


def load_or_create_mapping(path: Path, arm_ids: list[str], labels: list[str], seed: int) -> dict:
    expected = expected_mapping(arm_ids, labels, seed)
    if path.is_file():
        current = json.loads(path.read_text(encoding="utf-8"))
        if current != expected:
            raise RuntimeError("ANONYMIZATION_MAP_MISMATCH")
        return current
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(expected, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return expected


def public_mapping_hash(mapping: dict) -> str:
    return sha256_text(canonical_json(mapping))


def assert_identity_free(data: object, candidate_ids: list[str]) -> None:
    text = canonical_json(data).lower()
    leaked = [candidate for candidate in candidate_ids if candidate.lower() in text]
    if leaked:
        raise RuntimeError(f"ANONYMIZATION_IDENTITY_LEAK: {leaked}")
