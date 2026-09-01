"""Recompute and verify the final Phase 002C outcome without a model or network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import check_or_write, read_json, sha256_json
from .phase002c_audit import AUDIT_PATH, ROUTE_PATH, build_decision_audit
from .phase002c_records import (
    DECISION_ROOT,
    PRE_AUDIT_REPLAY_PATH,
    build_decisions,
    build_pre_audit_replay,
)
from .pre_adjudication import FREEZE_PATH, SUFFICIENCY_PATH, verify_input_freeze

REPLAY_PATH = Path("evals/results/phase-002c/replay/replay.json")


def decision_sets_equal(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> bool:
    """Compare complete decision sets by stable identity, independent of file ordering."""

    def by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]] | None:
        result: dict[str, dict[str, Any]] = {}
        for item in items:
            decision_id = item.get("decision_id")
            if not isinstance(decision_id, str) or not decision_id or decision_id in result:
                return None
            result[decision_id] = item
        return result

    left_by_id = by_id(left)
    right_by_id = by_id(right)
    return bool(left_by_id) and bool(right_by_id) and left_by_id == right_by_id


def build_replay(root: Path) -> dict[str, Any]:
    freeze_errors = verify_input_freeze(root)
    if freeze_errors:
        raise ValueError("INPUT_FREEZE_BROKEN:" + ",".join(freeze_errors))
    expected_audit, expected_route = build_decision_audit(root)
    if expected_audit["result"] != "PASS":
        raise ValueError("DECISION_AUDIT_NOT_PASS")
    decisions = [read_json(path) for path in sorted((root / DECISION_ROOT).glob("*.json"))]
    rebuilt_decisions = build_decisions(root)
    rebuilt_pre_replay = build_pre_audit_replay(root, rebuilt_decisions)
    recorded_pre_replay = read_json(root / PRE_AUDIT_REPLAY_PATH)
    variants = {
        name: sha256_json(
            {
                "pre_adjudication_variant": variant_hash,
                "decision_audit": expected_audit["checkpoint_hash"],
                "phase_route": expected_route["route_hash"],
            }
        )
        for name, variant_hash in rebuilt_pre_replay["variants"].items()
    }
    rebuild_checks = {
        "automated_decisions": decision_sets_equal(rebuilt_decisions, decisions),
        "pre_audit_replay": rebuilt_pre_replay == recorded_pre_replay,
        "decision_audit": expected_audit == read_json(root / AUDIT_PATH),
        "phase_route": expected_route == read_json(root / ROUTE_PATH),
    }
    stable = len(set(variants.values())) == 1 and all(rebuild_checks.values())
    freeze = read_json(root / FREEZE_PATH)
    sufficiency = read_json(root / SUFFICIENCY_PATH)
    replay = {
        "schema_version": "1.0.0",
        "replay_id": "PHASE-002C-FINAL-REPLAY",
        "mode": "OFFLINE_NO_MODEL_NO_NETWORK",
        "input_freeze_hash": freeze["freeze_hash"],
        "policy_hash": sufficiency["policy_hash"],
        "audit_id": expected_audit["audit_id"],
        "audit_result": expected_audit["result"],
        "decision_values": {item["decision_id"]: item["decision"] for item in decisions},
        "next_phase_allowed": expected_route["next_phase_allowed"],
        "phase003_allowed": expected_route["phase003_allowed"],
        "phase002d_started": False,
        "rebuild_checks": rebuild_checks,
        "variants": variants,
        "stable": stable,
        "resulting_action": "RETAIN_DECISIONS" if stable else "RETEST_REQUIRED",
    }
    replay["content_hash"] = sha256_json(replay)
    if not stable:
        raise ValueError("DETERMINISTIC_REPLAY_UNSTABLE")
    return replay


def write_replay(root: Path, *, check: bool) -> dict[str, Any]:
    expected_audit, expected_route = build_decision_audit(root)
    errors = check_or_write(root / AUDIT_PATH, expected_audit, check=check)
    errors.extend(check_or_write(root / ROUTE_PATH, expected_route, check=check))
    replay = build_replay(root)
    errors.extend(check_or_write(root / REPLAY_PATH, replay, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "stable": replay["stable"],
        "next_phase_allowed": replay["next_phase_allowed"],
        "errors": errors,
    }
