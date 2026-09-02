"""Check vault isolation and presence without opening or parsing private vault files."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .benchmark_generator import ISOLATION_LEVEL, VAULT_ROOT

VAULT_FILES = (
    "hidden_seeds.json",
    "hidden_oracle_parameters.json",
    "vault_manifest.json",
    "generated_case_hashes.json",
)


def check_benchmark_vault(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    ignored: dict[str, bool] = {}
    for name in VAULT_FILES:
        relative = VAULT_ROOT / name
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"VAULT_FILE_MISSING_OR_EMPTY:{name}")
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
        "private_values_read": False,
    }


__all__ = ["VAULT_FILES", "check_benchmark_vault"]
