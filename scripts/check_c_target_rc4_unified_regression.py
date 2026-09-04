#!/usr/bin/env python3
"""Check exact RC4 unified regression evidence and optional ignored workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evals/results/phase-004c-c-batch/rc4/unified_regression_evidence.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(*, verify_workspaces: bool) -> dict[str, Any]:
    errors: list[str] = []
    value = load(EVIDENCE)
    if (
        value.get("schema_version") != "1.0.0"
        or value.get("artifact_type") != "c_target_rc4_unified_regression_evidence"
        or value.get("release_gate") != "PASS_READY_TO_FREEZE_RC4"
    ):
        errors.append("RC4_UNIFIED_IDENTITY_INVALID")
    candidate = value.get("rc4_candidate", {})
    if candidate != {
        "implementation_commit": "297cad0a29c659b18484d4f3b67d69a942ad415c",
        "skill_tree": "d041ca38de030ae04813ef02dbe12f7f2b7a1c22",
        "version": "0.2.0-competition-rc4",
    }:
        errors.append("RC4_UNIFIED_SKILL_BINDING_INVALID")
    batch = value.get("batch_cases")
    if (
        not isinstance(batch, list)
        or len(batch) != 3
        or value.get("batch_regression_status") != "PASS"
        or value.get("universal_hard_failure_count") != 0
    ):
        errors.append("RC4_UNIFIED_BATCH_INVALID")
    for item in batch if isinstance(batch, list) else []:
        path = ROOT / str(item.get("evidence_path", ""))
        record = load(path) if path.is_file() else {}
        if (
            not path.is_file()
            or item.get("evidence_sha256") != digest(path)
            or record.get("case_id") != item.get("case_id")
            or record.get("terminal_state") != "READY_FOR_PAPER_HANDOFF"
            or record.get("universal_hard_failure") is not False
            or record.get("valid_run_count") != 3
            or record.get("failed_run_count") != 0
        ):
            errors.append(f"RC4_UNIFIED_BATCH_CASE_INVALID:{item.get('case_id')}")
    prior = value.get("twenty_twenty_three_c", {})
    prior_path = ROOT / str(prior.get("evidence_path", ""))
    prior_record = load(prior_path) if prior_path.is_file() else {}
    if (
        not prior_path.is_file()
        or prior.get("evidence_sha256") != digest(prior_path)
        or prior_record.get("final_state") != "READY_FOR_PAPER_HANDOFF"
        or len(prior_record.get("runs", [])) != 3
        or prior_record.get("stale_probe", {}).get("case_state") != "STALE"
        or prior_record.get("output_contract_preflight", {}).get("status") != "PASS"
    ):
        errors.append("RC4_UNIFIED_2023C_INVALID")
    auxiliary = value.get("twenty_twenty_a_auxiliary", {})
    auxiliary_path = ROOT / str(auxiliary.get("evidence_path", ""))
    auxiliary_record = load(auxiliary_path) if auxiliary_path.is_file() else {}
    if (
        not auxiliary_path.is_file()
        or auxiliary.get("evidence_sha256") != digest(auxiliary_path)
        or auxiliary_record.get("terminal_state") != "READY_FOR_PAPER_HANDOFF"
        or auxiliary_record.get("nonzero_failure_retained") is not True
        or auxiliary_record.get("failed_run_count") != 1
        or auxiliary_record.get("successful_run_count") != 2
        or auxiliary_record.get("selection_scope") != "SUCCESS_OUTCOMES_ONLY"
        or auxiliary_record.get("claim_gate") != "PASS"
        or auxiliary_record.get("handoff_gate") != "PASS"
        or auxiliary_record.get("c_target_evidence_credit") is not False
    ):
        errors.append("RC4_UNIFIED_2020A_INVALID")
    negative = value.get("negative_scenarios", {})
    negative_path = ROOT / str(negative.get("path", ""))
    negative_record = load(negative_path) if negative_path.is_file() else {}
    if (
        not negative_path.is_file()
        or negative.get("sha256") != digest(negative_path)
        or negative_record.get("scenario_count") != 30
        or negative_record.get("passed") != 30
        or negative_record.get("failed") != 0
        or negative_record.get("unhandled_exceptions") != 0
        or negative_record.get("sensitive_values_reported") != 0
    ):
        errors.append("RC4_UNIFIED_NEGATIVE_INVALID")
    synthetic = value.get("synthetic_e2e")
    if not isinstance(synthetic, list) or len(synthetic) != 2:
        errors.append("RC4_UNIFIED_SYNTHETIC_INVALID")
    elif verify_workspaces:
        for item in synthetic:
            workspace = ROOT / str(item.get("workspace_relative", ""))
            state = workspace / "case_state.json"
            handoff = workspace / "handoff/modeling_to_paper.json"
            if (
                not state.is_file()
                or not handoff.is_file()
                or digest(state) != item.get("case_state_sha256")
                or digest(handoff) != item.get("handoff_sha256")
                or load(state).get("state") != "READY_FOR_PAPER_HANDOFF"
                or len(list((workspace / "runs").glob("*/manifest.json"))) != item.get("run_count")
            ):
                errors.append(f"RC4_UNIFIED_SYNTHETIC_WORKSPACE_INVALID:{item.get('case_id')}")
    if any(
        value.get(name) != expected
        for name, expected in (
            ("formal_skill_count", 1),
            ("third_party_integrated", False),
            ("answer_leakage_count", 0),
            ("secret_count", 0),
            ("api_calls", 0),
            ("model_training", False),
        )
    ):
        errors.append("RC4_UNIFIED_SCOPE_INVALID")
    tracked_cache = subprocess.run(
        ["git", "ls-files", ".cache"], cwd=ROOT, check=False, capture_output=True, text=True
    )
    if tracked_cache.returncode != 0 or tracked_cache.stdout.strip():
        errors.append("RC4_UNIFIED_CACHE_TRACKING_INVALID")
    errors = sorted(set(errors))
    return {
        "ok": not errors,
        "error_count": len(errors),
        "errors": errors,
        "verify_workspaces": verify_workspaces,
        "batch_case_count": len(batch) if isinstance(batch, list) else 0,
        "synthetic_case_count": len(synthetic) if isinstance(synthetic, list) else 0,
        "negative_scenario_count": negative_record.get("scenario_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--verify-workspaces", action="store_true")
    args = parser.parse_args()
    result = evaluate(verify_workspaces=args.verify_workspaces)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
