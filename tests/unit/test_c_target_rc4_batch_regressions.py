from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def test_three_rc4_batch_regressions_are_complete(repo_root: Path) -> None:
    path = repo_root / "scripts/check_c_target_rc4_batch_regressions.py"
    spec = importlib.util.spec_from_file_location("check_c_target_rc4_batch_regressions", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    result = module.evaluate(verify_workspaces=False)

    assert result["ok"] is True
    assert result["case_count"] == 3
    assert result["errors"] == []
