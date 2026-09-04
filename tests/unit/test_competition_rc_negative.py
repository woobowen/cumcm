from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_all_thirty_negative_scenarios_fail_closed(repo_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "negative-result.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/run_competition_rc_negative_tests.py"),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["scenario_count"] == 30
    assert result["passed"] == 30
    assert result["failed"] == 0
    assert result["unhandled_exceptions"] == 0
    assert result["sensitive_values_reported"] == 0
    assert len({case["scenario_id"] for case in result["cases"]}) == 30
    assert all(case["pass"] for case in result["cases"])
    assert all(case["input_unchanged"] for case in result["cases"])
    assert all(not case["ready_for_paper_handoff"] for case in result["cases"])
