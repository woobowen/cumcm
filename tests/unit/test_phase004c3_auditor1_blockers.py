from __future__ import annotations

import json
import subprocess
import sys


def test_auditor1_rc6_release_blockers_reproduce_without_skill_mutation(repo_root) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/check_phase004c3_auditor1_blockers.py"),
            "--check",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS"
    assert result["release_verdict"] == "BLOCK"
    assert result["probe_count"] == 13
    assert result["reproduced_probe_count"] == 13
    assert len(result["reason_codes"]) == 5
    assert all(result["controller_checks"].values())
    assert result["formal_revision_cycles_remaining"] == 0
    assert result["third_cycle_permitted"] is False
    assert result["fresh_validation_input_accessed"] is False
    assert result["held_out_2025_accessed"] is False
