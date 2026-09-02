"""Phase 002D compatibility replay for the strict direct-adoption risk enum."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .models import check_or_write, file_sha256, read_json, read_yaml, sha256_json
from .phase002c_records import evaluate_direct_adoption_gates

BASE_COMMIT = "8dd43cad3bac58ac25fdbb0d412d894d428472ae"
HISTORICAL_DECISION = Path(
    "evals/results/phase-002c/automated_decisions/direct_upstream_adoption.json"
)
OUTPUT_PATH = Path("evals/results/phase-002d/replay/phase002c_risk_enum_compatibility.json")
CREATED_AT = "2026-09-01T17:58:44+08:00"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"GIT_COMMAND_FAILED:{' '.join(args)}:{result.stderr.strip()}")
    return result.stdout


def historical_phase002c_integrity(root: Path) -> dict[str, Any]:
    """Compare every current Phase 002C result with the merge-base snapshot."""
    prefix = "evals/results/phase-002c/"
    expected = sorted(
        line.split("\t", 1)[1]
        for line in _git(root, "ls-tree", "-r", BASE_COMMIT, prefix).splitlines()
    )
    current = sorted(
        path.relative_to(root).as_posix() for path in (root / prefix).rglob("*") if path.is_file()
    )
    missing = sorted(set(expected) - set(current))
    added = sorted(set(current) - set(expected))
    mutated: list[str] = []
    for relative in sorted(set(expected) & set(current)):
        historical = _git(root, "show", f"{BASE_COMMIT}:{relative}").encode()
        current_bytes = (root / relative).read_bytes()
        if historical != current_bytes:
            mutated.append(relative)
    return {
        "base_commit": BASE_COMMIT,
        "expected_file_count": len(expected),
        "current_file_count": len(current),
        "missing": missing,
        "added": added,
        "mutated": mutated,
        "passed": not (missing or added or mutated),
    }


def build_risk_compatibility_replay(root: Path) -> dict[str, Any]:
    manifest = read_yaml(root / "research/upstream_candidates/manifest.yaml")
    review = read_json(
        root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
    )
    historical = read_json(root / HISTORICAL_DECISION)
    candidates = {item["id"]: item for item in manifest["candidates"]}
    arms = {item["candidate_id"]: item for item in review["arms"] if item["candidate_id"]}
    historical_by_candidate = {
        item["candidate_id"]: item for item in historical["adoption_results"]
    }
    candidate_results: list[dict[str, Any]] = []
    for candidate_id in sorted(historical_by_candidate):
        gates = evaluate_direct_adoption_gates(
            candidates[candidate_id],
            arms[candidate_id],
            review_status=review["review_status"],
            third_party_code_executed=review.get("third_party_code_executed", False),
            candidate_dependencies_installed=review.get("candidate_dependencies_installed", False),
        )
        failed = sorted(name for name, passed in gates.items() if not passed)
        current_decision = "AUTOMATED_REJECTED" if failed else "RETEST_REQUIRED"
        candidate_results.append(
            {
                "candidate_id": candidate_id,
                "historical_decision": historical_by_candidate[candidate_id]["decision"],
                "current_strict_decision": current_decision,
                "strict_hard_gates": gates,
                "failed_gates": failed,
                "decision_unchanged": (
                    historical_by_candidate[candidate_id]["decision"] == current_decision
                ),
            }
        )
    integrity = historical_phase002c_integrity(root)
    replay = {
        "schema_version": "1.0.0",
        "replay_id": "PHASE-002D-PHASE002C-RISK-ENUM-COMPATIBILITY",
        "mode": "OFFLINE_NO_MODEL_NO_NETWORK",
        "created_at": CREATED_AT,
        "historical_decision_path": HISTORICAL_DECISION.as_posix(),
        "historical_decision_sha256": file_sha256(root / HISTORICAL_DECISION),
        "strict_risk_schema_sha256": file_sha256(
            root / "contracts/direct_adoption_risk.schema.json"
        ),
        "historical_phase002c_integrity": integrity,
        "candidate_results": candidate_results,
        "historical_rejection_invariant": integrity["passed"]
        and all(item["decision_unchanged"] for item in candidate_results),
    }
    replay["result_hash"] = sha256_json(replay)
    return replay


def write_risk_compatibility_replay(root: Path, *, check: bool) -> dict[str, Any]:
    replay = build_risk_compatibility_replay(root)
    errors = check_or_write(root / OUTPUT_PATH, replay, check=check)
    if not replay["historical_rejection_invariant"]:
        errors.append("PHASE002C_REJECTION_CHANGED")
    return {
        "status": "PASS" if not errors else "FAIL",
        "historical_rejection_invariant": replay["historical_rejection_invariant"],
        "result_hash": replay["result_hash"],
        "errors": errors,
    }
