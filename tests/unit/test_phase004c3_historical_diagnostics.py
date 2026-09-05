from __future__ import annotations

import json
import subprocess
import sys


def test_phase004c3_historical_diagnostics_are_read_only_and_fail_closed(repo_root) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/check_phase004c3_historical_diagnostics.py"),
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
    assert result["historical_verdicts_changed"] is False
    assert result["historical_files_written"] == []
    assert result["new_model_runs"] == 0
    assert result["diagnostics"]["2019_data_sufficiency"] == {
        "status": "UNSATISFIABLE_WITH_CURRENT_INPUTS",
        "reason_codes": ["RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM"],
    }
    assert result["diagnostics"]["2019_policy_claim"] == {
        "status": "BLOCK",
        "reason_codes": ["RC_POLICY_CLAIM_NO_POLICY_EXPOSURE"],
    }
    assert result["diagnostics"]["2024_bounded_claim"] == {
        "status": "PASS",
        "reason_codes": [],
    }
