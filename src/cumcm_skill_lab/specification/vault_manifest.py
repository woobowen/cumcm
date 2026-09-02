"""Check vault isolation and presence without opening or parsing private vault files."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import sha256_json

from .benchmark_generator import (
    BENCHMARK_ROOT,
    COHORT_ID,
    ISOLATION_LEVEL,
    SEALED_CASE_COUNT,
    VAULT_ROOT,
)

VAULT_FILES = (
    "hidden_seeds.json",
    "hidden_oracle_parameters.json",
    "vault_manifest.json",
    "generated_case_hashes.json",
    "hidden_seeds_v2.json",
    "hidden_oracle_parameters_v2.json",
    "oracle_class_map_v2.json",
    "generated_case_hashes_v2.json",
    "vault_manifest_v2.json",
)


def _public_commitment_errors(root: Path) -> list[str]:
    errors: list[str] = []
    sealed_path = root / BENCHMARK_ROOT / "sealed_manifest.json"
    commitment_path = root / BENCHMARK_ROOT / "manifests/oracle_commitments.json"
    try:
        sealed = json.loads(sealed_path.read_text(encoding="utf-8"))
        commitment = json.loads(commitment_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["VAULT_PUBLIC_COMMITMENT_UNREADABLE"]
    body = dict(sealed)
    recorded_hash = body.pop("manifest_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("VAULT_PUBLIC_SEALED_MANIFEST_HASH_MISMATCH")
    if sealed.get("cohort_id") != COHORT_ID or commitment.get("cohort_id") != COHORT_ID:
        errors.append("VAULT_PUBLIC_COHORT_MISMATCH")
    if len(sealed.get("hidden_seed_hashes", {})) != SEALED_CASE_COUNT:
        errors.append("VAULT_PUBLIC_SEED_COMMITMENT_COUNT_MISMATCH")
    if sealed.get("private_oracle_commitment") != commitment.get("private_mapping_commitment"):
        errors.append("VAULT_PUBLIC_ORACLE_COMMITMENT_MISMATCH")
    if sealed.get("contains_hidden_seed") is not False:
        errors.append("VAULT_PUBLIC_MANIFEST_CONTAINS_HIDDEN_SEED")
    if sealed.get("contains_hidden_oracle") is not False:
        errors.append("VAULT_PUBLIC_MANIFEST_CONTAINS_HIDDEN_ORACLE")
    return errors


def check_benchmark_vault(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    ignored: dict[str, bool] = {}
    present: dict[str, bool] = {}
    for name in VAULT_FILES:
        relative = VAULT_ROOT / name
        path = root / relative
        present[name] = path.is_file() and path.stat().st_size > 0 if path.exists() else False
        check = subprocess.run(
            ["git", "check-ignore", relative.as_posix()],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        ignored[name] = check.returncode == 0
        if not ignored[name]:
            errors.append(f"VAULT_NOT_IGNORED:{name}")
    present_count = sum(present.values())
    if present_count not in {0, len(VAULT_FILES)}:
        errors.extend(
            f"VAULT_PARTIAL_MOUNT_MISSING_OR_EMPTY:{name}"
            for name, is_present in present.items()
            if not is_present
        )
    mount_status = "MOUNTED" if present_count == len(VAULT_FILES) else "NOT_MOUNTED"
    commitment_errors = _public_commitment_errors(root)
    errors.extend(commitment_errors)
    tracked = subprocess.run(
        ["git", "ls-files", VAULT_ROOT.as_posix()],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked.stdout.strip():
        errors.append("VAULT_FILE_TRACKED")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "isolation_level": ISOLATION_LEVEL,
        "ignored": ignored,
        "mount_status": mount_status,
        "public_commitment_verified": not commitment_errors,
        "private_values_read": False,
    }


__all__ = ["VAULT_FILES", "check_benchmark_vault"]
