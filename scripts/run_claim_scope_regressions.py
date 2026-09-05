#!/usr/bin/env python3
"""Replay frozen machine artifacts through the current Claim and handoff contract only."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_core():
    path = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("claim_regression_core", path)
    core = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = core
    spec.loader.exec_module(core)
    return core


def replay(core, source, destination, *, diagnostic=False):
    started = time.monotonic()
    state = core.load_json(source / "case_state.json")
    before = {
        str(p.relative_to(source)): core.file_hash(p)
        for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    claim = core.read_artifact(source, "claim_evidence")["content"]
    final = core.read_artifact(source, "final_result")["content"]
    requirements = core.read_artifact(source, "problem_requirements")["content"]["requirements"]
    manifest = core.load_json(source / "runs" / claim["run_id"] / "manifest.json")
    derived = core.derive_claim_contract(claim, requirements)
    claim_result = core.validate_claim(derived, manifest, final, case_root=source, state=state)
    destination.mkdir(parents=True, exist_ok=False)
    core.write_json(destination / "derived_claim.json", core.artifact("claim_evidence", derived))
    # The builder consumes the unchanged legacy artifact via its pure migration path.
    handoff = core.build_expected_handoff(source, state)
    handoff_result = core.validate_handoff(handoff, case_root=source, state=state)
    core.write_json(destination / "derived_handoff.json", handoff)
    manifests = [core.load_json(p) for p in sorted((source / "runs").glob("*/manifest.json"))]
    active_core = core
    plan = core.read_artifact(source, "experiment_plan")["content"]
    historical_skill = destination / "frozen_skill"
    for code in plan["required_code_files"]:
        if code["scope"] != "SKILL_ROOT":
            continue
        content = subprocess.check_output(
            ["git", "show", f"{plan['code_commit']}:{code['repository_path']}"], cwd=ROOT
        )
        path = historical_skill / code["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if core.file_hash(path) != code["sha256"]:
            raise ValueError("HISTORICAL_CODE_BLOB_MISMATCH")
    spec = importlib.util.spec_from_file_location(
        "frozen_run_kernel", historical_skill / "scripts/cumcm_case.py"
    )
    core = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = core
    spec.loader.exec_module(core)
    core.REPO_ROOT = ROOT
    freezes = core.trusted_freezes(source)
    run_results = [
        core.validate_manifest(item, case_root=source, trusted_freezes=freezes)
        for item in manifests
    ]
    comparison = core.read_artifact(source, "model_comparison")["content"]
    comparison_result = core.validate_comparison(comparison, freezes, case_root=source)
    robustness = core.read_artifact(source, "robustness_analysis")["content"]
    robustness_result = core.validate_robustness(robustness, comparison, case_root=source)
    final_result = core.validate_final_result(final, comparison, case_root=source)
    core = active_core
    after = {
        str(p.relative_to(source)): core.file_hash(p)
        for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    reasons = sorted(
        {
            reason
            for result in [
                claim_result,
                handoff_result,
                comparison_result,
                robustness_result,
                final_result,
            ]
            if not result.accepted
            for reason in result.reason_codes
        }
    )
    for item, result in zip(manifests, run_results, strict=True):
        if not result.accepted and not (
            item["outcome"] != "SUCCESS"
            and set(result.reason_codes) == {f"RC_MANIFEST_NOT_SUCCESS:{item['outcome']}"}
        ):
            reasons += list(result.reason_codes)
    if before != after:
        reasons.append("HISTORICAL_EVIDENCE_DRIFT")
    record = {
        "case_id": state["case_id"],
        "classification": "POST_VALIDATION_DIAGNOSTIC_REPLAY"
        if diagnostic
        else "DEVELOPMENT_ARTIFACT_REGRESSION",
        "diagnostic_id": "CUMCM-2024-C-POST-VALIDATION-DEVELOPMENT-DIAGNOSTIC"
        if diagnostic
        else None,
        "skill_version": core.VERSION,
        "claim_contract_version": core.CLAIM_CONTRACT_VERSION,
        "source_state": state["state"],
        "run_validation_code_context": "HASH_VERIFIED_ORIGINAL_GIT_BLOBS_NO_EXECUTION",
        "source_state_sha256": core.file_hash(source / "case_state.json"),
        "source_manifest_hashes": {item["run_id"]: core.canonical_hash(item) for item in manifests},
        "primary_requirement_count": len(core.required_requirement_ids(source)),
        "aggregate_primary_ids": handoff["validation_results"]["aggregate_claim"][
            "covered_primary_requirement_ids"
        ],
        "claim_gate": claim_result.as_dict(),
        "handoff_gate": handoff_result.as_dict(),
        "comparison_gate": comparison_result.as_dict(),
        "robustness_gate": robustness_result.as_dict(),
        "final_gate": final_result.as_dict(),
        "run_gates": [item.as_dict() for item in run_results],
        "run_count": len(manifests),
        "failed_runs_retained": sum(item["outcome"] != "SUCCESS" for item in manifests),
        "new_model_runs": 0,
        "old_files_unchanged": before == after,
        "source_tree_sha256": core.canonical_hash(before),
        "derived_claim_sha256": core.file_hash(destination / "derived_claim.json"),
        "derived_handoff_sha256": core.file_hash(destination / "derived_handoff.json"),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "status": "PASS" if not reasons else "BLOCK",
        "reason_codes": sorted(set(reasons)),
        "stage_history": [item["to"] for item in state["history"]],
        "no_validation_credit": True,
    }
    if diagnostic:
        record["old_verdict"] = "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT"
        record["old_case_state"] = "REJECTED"
        record["answer_state"] = "SEALED"
    return record


def main():
    core = load_core()
    checkpoint = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    rows = []
    for year in (2020, 2021, 2022):
        matches = list(
            (ROOT / "evals/results/phase-004c-c-batch").glob(
                f"CUMCM-{year}-C-*/rc4/development_regression_evidence.json"
            )
        )
        record = core.load_json(matches[0])
        rows.append((f"{year}c", ROOT / record["workspace_relative"], False))
    rows += [
        ("2023c", ROOT / ".cache/official_inputs/CUMCM-2023-C/rc4_main_chain_attempt_001", False),
        ("2020a", ROOT / ".cache/official_inputs/CUMCM-2020-A/rc4_auxiliary_attempt_003", False),
        ("2024c", ROOT / ".cache/official_inputs/CUMCM-2024-C/validation_001", True),
    ]
    results = []
    for key, source, diagnostic in rows:
        result = replay(
            core,
            source,
            ROOT / ".cache/phase004c2/derived" / (checkpoint + "-attempt-003") / key,
            diagnostic=diagnostic,
        )
        results.append(result)
        print(
            json.dumps(
                {"case": key, "status": result["status"], "reasons": result["reason_codes"]}
            ),
            flush=True,
        )
        if result["status"] != "PASS":
            break
    result = {
        "schema_version": "1.0.0",
        "implementation_commit": checkpoint,
        "cases": results,
        "status": "PASS"
        if len(results) == 6 and all(item["status"] == "PASS" for item in results)
        else "BLOCK",
    }
    result["payload_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    core.write_json(
        ROOT / "evals/results/phase-004c2/historical_regressions.json", result, overwrite=False
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
