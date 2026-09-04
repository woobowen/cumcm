from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest


@pytest.mark.parametrize(
    ("kind", "case_id", "expected_model", "run_count"),
    [
        ("prediction", "SYNTH-RC1-PREDICTION-001", "P-LINEAR-TREND", 2),
        ("optimization", "SYNTH-RC1-OPTIMIZATION-002", "O-ENUMERATION", 3),
    ],
)
def test_project_original_case_reaches_ready_through_all_gates(
    repo_root: Path,
    tmp_path: Path,
    kind: str,
    case_id: str,
    expected_model: str,
    run_count: int,
) -> None:
    cli = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    case_root = tmp_path / kind
    result = subprocess.run(
        [
            sys.executable,
            str(cli),
            "smoke",
            "--case-root",
            str(case_root),
            "--case-id",
            case_id,
            "--kind",
            kind,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert payload["result"]["selected_model"] == expected_model
    assert payload["result"]["final_state"] == "READY_FOR_PAPER_HANDOFF"
    assert payload["result"]["transition_count"] == 13

    state = json.loads((case_root / "case_state.json").read_text(encoding="utf-8"))
    assert state["state"] == "READY_FOR_PAPER_HANDOFF"
    assert [item["to"] for item in state["history"]] == [
        "CREATED",
        "INTAKE_COMPLETE",
        "REQUIREMENTS_VALIDATED",
        "SOURCES_PLANNED",
        "DATA_AUDITED",
        "MODELS_PROPOSED",
        "EXPERIMENT_PLAN_VALIDATED",
        "RUNNING",
        "RUN_COMPLETED",
        "RUN_VALIDATED",
        "ROBUSTNESS_VALIDATED",
        "FINAL_CANDIDATE",
        "EVIDENCE_VALIDATED",
        "READY_FOR_PAPER_HANDOFF",
    ]
    assert all(item["status"] == "PASS" for item in state["history"])

    required = [
        "problem/problem_requirements.json",
        "research/research_plan.json",
        "models/assumptions_and_symbols.json",
        "data/data_audit.json",
        "models/model_candidates.json",
        "experiments/experiment_plan.json",
        "results/model_comparison.json",
        "results/robustness.json",
        "evidence/claim_evidence.json",
        "results/final_result.json",
        "handoff/modeling_to_paper.json",
    ]
    assert all((case_root / relative).is_file() for relative in required)
    manifests = sorted(case_root.glob("runs/*/manifest.json"))
    assert len(manifests) == run_count

    handoff = json.loads((case_root / "handoff/modeling_to_paper.json").read_text(encoding="utf-8"))
    schema = json.loads(
        (repo_root / "contracts/modeling_to_paper.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(handoff)
    assert handoff["approved_by"] == ["MACHINE_TECHNICAL_GATES"]
    assert handoff["result_tables"]
    assert handoff["figure_ready_data"]
    assert handoff["limitations"]

    status = subprocess.run(
        [sys.executable, str(cli), "status", "--case-root", str(case_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    stale = subprocess.run(
        [
            sys.executable,
            str(cli),
            "stale-check",
            "--case-root",
            str(case_root),
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert status.returncode == 0
    assert json.loads(status.stdout)["state"]["state"] == "READY_FOR_PAPER_HANDOFF"
    assert stale.returncode == 0
    assert json.loads(stale.stdout)["reason_codes"] == ["RC_DEPENDENCY_HASHES_CURRENT"]

    final = json.loads((case_root / "results/final_result.json").read_text(encoding="utf-8"))[
        "content"
    ]
    checks = [
        [
            "manifest",
            "--case-root",
            str(case_root),
            "--path",
            f"runs/{final['run_id']}/manifest.json",
        ],
        ["compare-check", "--case-root", str(case_root)],
        ["claim-check", "--case-root", str(case_root)],
    ]
    for arguments in checks:
        checked = subprocess.run(
            [sys.executable, str(cli), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        assert checked.returncode == 0, checked.stdout + checked.stderr
        assert json.loads(checked.stdout)["accepted"] is True

    comparison = json.loads(
        (case_root / "results/model_comparison.json").read_text(encoding="utf-8")
    )["content"]
    assert comparison["test_access"] == {
        "authorized": True,
        "count": 1,
        "used_for_selection": False,
    }
    if kind == "prediction":
        audit = json.loads((case_root / "data/data_audit.json").read_text(encoding="utf-8"))[
            "content"
        ]
        assert audit["rejected_leakage_fields"] == ["future_target"]
        assert payload["result"]["final_metric"] == 0.0
    else:
        infeasible = json.loads(
            (case_root / "runs/RUN-O-INFEASIBLE-PROPOSAL/manifest.json").read_text(encoding="utf-8")
        )
        assert infeasible["outcome"] == "INFEASIBLE"
        assert infeasible["failure"]["retained"] is True
        assert payload["result"]["objective"] == 22
