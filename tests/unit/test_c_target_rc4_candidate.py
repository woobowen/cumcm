from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def test_rc4_candidate_freeze_and_neutral_change_set_are_consistent(repo_root: Path) -> None:
    path = repo_root / "scripts/check_c_target_rc4_candidate.py"
    spec = importlib.util.spec_from_file_location("check_c_target_rc4_candidate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    result = module.evaluate()

    assert result["ok"] is True
    assert result["failed_checks"] == []
    assert all(result["checks"].values())
