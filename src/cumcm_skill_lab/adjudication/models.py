"""Small deterministic serialization helpers used by adjudication modules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode())


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def check_or_write(path: Path, value: Any, *, check: bool) -> list[str]:
    if check:
        if not path.is_file():
            return [f"MISSING:{path}"]
        if read_json(path) != value:
            return [f"MISMATCH:{path}"]
        return []
    write_json(path, value)
    return []


def without_keys(value: dict, *keys: str) -> dict:
    return {key: item for key, item in value.items() if key not in keys}
