"""Canonical, fail-closed file helpers for R3 shadow artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def tree_file_hashes(root: Path, relative: Path) -> dict[str, str]:
    base = root / relative
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(base.rglob("*"))
        if path.is_file() and not path.name.endswith((".pyc", ".pyo"))
    }


def tree_hash(root: Path, relative: Path) -> str:
    return sha256_json(tree_file_hashes(root, relative))


__all__ = [
    "canonical_bytes",
    "file_sha256",
    "read_json",
    "sha256_bytes",
    "sha256_json",
    "tree_file_hashes",
    "tree_hash",
    "write_json_atomic",
]
