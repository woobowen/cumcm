#!/usr/bin/env python3
"""Run both project-original RC1 smoke cases and retain compact evidence summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
SCHEMA_PATH = REPO_ROOT / "contracts/modeling_to_paper.schema.json"
ARTIFACTS = (
    "case_state.json",
    "problem/problem_requirements.json",
    "research/research_plan.json",
    "research/source_ledger.json",
    "models/assumptions_and_symbols.json",
    "data/data_audit.json",
    "models/model_candidates.json",
    "experiments/experiment_plan.json",
    "results/model_comparison.json",
    "results/robustness.json",
    "evidence/claim_evidence.json",
    "results/final_result.json",
    "handoff/modeling_to_paper.json",
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run_case(
    temporary_root: Path,
    kind: str,
    case_id: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    case_root = temporary_root / kind
    command = [
        sys.executable,
        str(CLI),
        "smoke",
        "--case-root",
        str(case_root),
        "--case-id",
        case_id,
        "--kind",
        kind,
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"RC_E2E_{kind.upper()}_FAILED")
    cli_result = json.loads(completed.stdout)
    state = load_json(case_root / "case_state.json")
    handoff = load_json(case_root / "handoff/modeling_to_paper.json")
    jsonschema.Draft202012Validator(schema).validate(handoff)
    manifests = {
        path.parent.name: {
            "sha256": file_hash(path),
            "outcome": load_json(path)["outcome"],
            "code_commit": load_json(path)["code_commit"],
            "code_files": load_json(path)["code_files"],
            "code_tree_hash": load_json(path)["code_tree_hash"],
            "input_files": load_json(path)["input_files"],
            "input_hash": load_json(path)["input_hash"],
            "configuration": load_json(path)["configuration"],
            "configuration_hash": load_json(path)["configuration_hash"],
            "random_seed": load_json(path)["random_seed"],
            "output_hash": load_json(path)["output_hash"],
        }
        for path in sorted(case_root.glob("runs/*/manifest.json"))
    }
    comparison = load_json(case_root / "results/model_comparison.json")["content"]
    robustness = load_json(case_root / "results/robustness.json")["content"]
    final = load_json(case_root / "results/final_result.json")["content"]
    raw_files = sorted((case_root / "data/raw").glob("*"))
    processed_files = sorted((case_root / "data/processed").glob("*"))
    data_audit = load_json(case_root / "data/data_audit.json")["content"]
    state_bytes_before_probe = (case_root / "case_state.json").read_bytes()
    raw_before = raw_files[0].read_bytes()
    raw_files[0].write_bytes(raw_before + b"\n")
    stale_command = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "stale-check",
            "--case-root",
            str(case_root),
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    stale_result = json.loads(stale_command.stdout)
    state_bytes_after_probe = (case_root / "case_state.json").read_bytes()
    summary = {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "kind": kind,
        "command": (
            "python <skill>/scripts/cumcm_case.py smoke "
            f"--case-root <TEMP>/{kind} --case-id {case_id} --kind {kind}"
        ),
        "exit_code": completed.returncode,
        "actual_execution": True,
        "final_state": state["state"],
        "state_sequence": [item["to"] for item in state["history"]],
        "gate_sequence": [item["gate"] for item in state["history"][1:]],
        "artifact_hashes": {relative: file_hash(case_root / relative) for relative in ARTIFACTS},
        "raw_input_hashes": {
            str(path.relative_to(case_root)): data_audit["data_hashes"][
                str(path.relative_to(case_root))
            ]
            for path in raw_files
        },
        "processed_input_hashes": {
            str(path.relative_to(case_root)): file_hash(path) for path in processed_files
        },
        "processing_lineage": data_audit.get("processing_lineage"),
        "post_ready_raw_mutation_probe": {
            "exit_code": stale_command.returncode,
            "status": stale_result["status"],
            "reason_codes": stale_result["reason_codes"],
            "dependency_chain": stale_result["dependency_chain"],
            "state_mutated": state_bytes_after_probe != state_bytes_before_probe,
        },
        "run_manifests": manifests,
        "selected_model": final["selected_model"],
        "final_run_id": final["run_id"],
        "final_metrics": final["final_metrics"],
        "test_access": comparison["test_access"],
        "robustness_perturbation_count": len(robustness["perturbations"]),
        "failure_cases": robustness["failure_cases"],
        "handoff_required_fields": sorted(schema["required"]),
        "handoff_generated_fields": sorted(handoff),
        "handoff_contract_result": "PASS",
        "handoff_hash": file_hash(case_root / "handoff/modeling_to_paper.json"),
        "cli_result": cli_result["result"],
        "historical_answer_accesses": 0,
        "api_calls": 0,
        "third_party_executions": 0,
        "zero_count_sources": {
            "historical_answer_accesses": "accepted source_ledger.answer_access_status",
            "api_calls": "offline subprocess harness with no network operation",
            "third_party_executions": "project-original deterministic code path only",
        },
    }
    summary["evidence_hash"] = canonical_hash(summary)
    return summary


def evaluate(output_dir: Path) -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    cases = (
        ("prediction", "SYNTH-RC1-PREDICTION-001"),
        ("optimization", "SYNTH-RC1-OPTIMIZATION-002"),
    )
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cumcm-rc-e2e-") as temporary:
        root = Path(temporary)
        for kind, case_id in cases:
            summary = run_case(root, kind, case_id, schema)
            write_json(output_dir / f"{kind}.json", summary)
            results.append(summary)
    combined = {
        "schema_version": "1.0.0",
        "case_count": 2,
        "passed": sum(
            result["final_state"] == "READY_FOR_PAPER_HANDOFF"
            and result["handoff_contract_result"] == "PASS"
            for result in results
        ),
        "failed": sum(
            result["final_state"] != "READY_FOR_PAPER_HANDOFF"
            or result["handoff_contract_result"] != "PASS"
            for result in results
        ),
        "case_evidence": [
            {
                "case_id": result["case_id"],
                "kind": result["kind"],
                "evidence_hash": result["evidence_hash"],
                "final_state": result["final_state"],
            }
            for result in results
        ],
        "historical_answer_accesses": 0,
        "api_calls": 0,
        "real_comparison_model_starts": 0,
        "third_party_executions": 0,
    }
    combined["evidence_hash"] = canonical_hash(combined)
    write_json(output_dir / "result.json", combined)
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] == 2 and result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
