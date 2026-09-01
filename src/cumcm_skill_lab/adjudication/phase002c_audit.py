"""Mechanically audit Phase 002C decisions after the native Decision Auditor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import check_or_write, read_json, sha256_json
from .native_subagent_audits import POST_DECISION_ROLE, audit_path, validate_audit
from .phase002c_records import DECISION_ROOT, PRE_AUDIT_REPLAY_PATH
from .phase_routing import build_phase_route
from .pre_adjudication import FREEZE_PATH, SUFFICIENCY_PATH, resolve_policy, verify_input_freeze

AUDIT_PATH = Path("evals/results/phase-002c/decision_audit/audit.json")
ROUTE_PATH = Path("evals/results/phase-002c/replay/phase_route.json")


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_walk_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_walk_keys(item) for item in value), set())
    return set()


def build_decision_audit(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    native_path = audit_path(root, POST_DECISION_ROLE)
    if not native_path.is_file():
        raise ValueError("DECISION_AUDITOR_OUTPUT_MISSING")
    native = read_json(native_path)
    native_errors = validate_audit(root, native, role=POST_DECISION_ROLE)
    decisions = [read_json(path) for path in sorted((root / DECISION_ROOT).glob("*.json"))]
    if len(decisions) != 4:
        raise ValueError("PHASE002C_DECISION_SET_INCOMPLETE")
    policy = resolve_policy(root)
    freeze = read_json(root / FREEZE_PATH)
    sufficiency = read_json(root / SUFFICIENCY_PATH)
    replay = read_json(root / PRE_AUDIT_REPLAY_PATH)
    forbidden = {"human_gate", "human_approved", "human_selected", "majority_vote_result"}
    by_type = {item["decision_type"]: item for item in decisions}
    evidence = by_type["EVIDENCE_SUFFICIENCY"]
    recovery = by_type["RECOVERY_POLICY"]
    components = by_type["COMPONENT_READINESS"]
    direct = by_type["DIRECT_UPSTREAM_ADOPTION"]
    checks = {
        "native_auditor_schema_valid": not native_errors,
        "native_auditor_pass": native["verdict"] == "PASS",
        "native_auditor_read_only": native["read_only"] and not native["writes_observed"],
        "native_auditor_no_nested_codex": not native["nested_codex_used"],
        "native_auditor_no_api_key": not native["api_key_used"],
        "input_freeze_valid": not verify_input_freeze(root),
        "policy_hash_frozen": all(
            item["policy_version"] == policy["version"] for item in decisions
        ),
        "thresholds_unchanged": policy["thresholds_unchanged"] is True,
        "decision_set_complete": set(by_type)
        == {
            "EVIDENCE_SUFFICIENCY",
            "DIRECT_UPSTREAM_ADOPTION",
            "RECOVERY_POLICY",
            "COMPONENT_READINESS",
        },
        "sufficiency_matches_pre_gate": evidence["decision"]
        == (
            "EVIDENCE_INSUFFICIENT"
            if sufficiency["result"] == "INSUFFICIENT"
            else evidence["decision"]
        ),
        "semantic_judges_conditionally_skipped": not sufficiency["semantic_judges_required"]
        and not any(item["judge_decisions"] for item in decisions),
        "recovery_not_ranked": recovery["accepted_scope"] in {"POLICY_ONLY", "NONE"}
        and "RANKING" in recovery["rejected_scope"],
        "whole_packages_not_accepted_by_component_value": all(
            item["decision"] != "AUTOMATED_ACCEPTED" for item in direct["adoption_results"]
        ),
        "component_scope_bounded": all(
            item["accepted_scope"] in {"NONE", "SPECIFICATION_ONLY"}
            for item in components["component_results"]
        ),
        "no_majority_vote": not any("majority_vote" in _walk_keys(item) for item in decisions),
        "no_human_technical_gate": not any(_walk_keys(item) & forbidden for item in decisions),
        "pre_audit_replay_stable": replay["stable"] is True,
        "insufficient_blocks_phase003": evidence["decision"] != "EVIDENCE_INSUFFICIENT"
        or evidence["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D",
        "decision_hashes_valid": all(
            item["replay_hash"]
            == sha256_json({key: value for key, value in item.items() if key != "replay_hash"})
            for item in decisions
        ),
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    blockers = sorted(set(native["blockers"]) | set(native_errors))
    result = (
        "PASS"
        if not failures and not blockers
        else ("RETEST_REQUIRED" if native["verdict"] == "RETEST_REQUIRED" else "FAIL")
    )
    bundle = read_json(
        root / "evals/results/phase-002c/subagent_audits/bundles/automated_decision_auditor.json"
    )
    audit = {
        "audit_id": "DECISION-AUDIT-002C",
        "role": "DECISION_AUDITOR",
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "input_bundle_hash": native["bundle_hash"],
        "policy_hash": policy["policy_hash"],
        "evidence_hash": freeze["evidence_hash"],
        "model": native["model"],
        "reasoning_setting": native["reasoning_setting"],
        "decision_ids": [item["decision_id"] for item in decisions],
        "independent": True,
        "majority_vote_used": False,
        "human_technical_gate_used": False,
        "recovery_ranked": False,
        "checks": checks,
        "result": result,
        "failures": failures,
        "blockers": blockers,
        "replayable": not failures and not blockers,
        "audit_evidence_refs": [native["audit_id"], replay["replay_id"], freeze["freeze_id"]],
        "confidence": 1.0 if result == "PASS" else 0.0,
        "checkpoint_hash": "0" * 64,
        "created_at": policy["frozen_at"],
    }
    audit["checkpoint_hash"] = sha256_json(
        {key: value for key, value in audit.items() if key != "checkpoint_hash"}
    )
    Draft202012Validator(read_json(root / "contracts/decision_audit.schema.json")).validate(audit)
    route = build_phase_route(evidence, audit_result=result)
    Draft202012Validator(read_json(root / "contracts/phase_route.schema.json")).validate(route)
    return audit, route


def write_decision_audit(root: Path, *, check: bool) -> dict[str, Any]:
    audit, route = build_decision_audit(root)
    errors = check_or_write(root / AUDIT_PATH, audit, check=check)
    errors.extend(check_or_write(root / ROUTE_PATH, route, check=check))
    return {
        "status": "PASS" if not errors and audit["result"] == "PASS" else "FAIL",
        "audit_result": audit["result"],
        "route": route["next_phase_allowed"],
        "errors": errors,
    }
