from __future__ import annotations

import json
import subprocess
import sys


def test_phase004c4_regression_evidence_is_hash_bound_and_replayable(repo_root) -> None:
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts/check_phase004c4_regressions.py"), "--check"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result == {"error_count": 0, "errors": [], "status": "PASS"}
