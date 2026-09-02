"""Offline, identity-blind replay for Phase 002D-R1 decisions."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from .decisions import DECISION_FILES, validate_decisions
from .models import RESULT_ROOT, check_or_write, read_json, sha256_json

REPLAY_PATH = RESULT_ROOT / "replay/replay.json"
CREATED_AT = "2026-09-01T23:12:32+08:00"


def _read_inputs(root: Path) -> dict[str, Any]:
    classifications = [
        read_json(path)
        for path in sorted((root / RESULT_ROOT / "attempt_classification").glob("*.json"))
    ]
    matrix = read_json(root / RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.json")
    scopes = read_json(root / RESULT_ROOT / "evidence_scopes/evidence_scope_summary.json")
    retry = read_json(root / RESULT_ROOT / "retry_bias/retry_bias_audit.json")
    supplemental = read_json(root / RESULT_ROOT / "supplemental/authorization.json")
    evidence_items = [
        {"kind": "quality", "value": scopes["quality_evidence"]},
        {"kind": "reliability", "value": scopes["reliability_evidence"]},
        {"kind": "outcome", "value": scopes["outcome_completeness"]},
        {"kind": "component_gap", "value": scopes["component_gap_evidence"]},
        {"kind": "retry", "value": retry},
        {"kind": "supplemental", "value": supplemental},
    ]
    return {
        "classifications": classifications,
        "slots": matrix["slots"],
        "matrix_controls": {
            "all_attempts_accounted": matrix["all_attempts_accounted"],
            "best_of_n_prohibited": matrix["best_of_n_prohibited"],
            "earliest_eligible_selection": matrix["earliest_eligible_selection"],
        },
        "evidence_items": evidence_items,
    }


def _item(inputs: dict[str, Any], kind: str) -> dict[str, Any]:
    matches = [item["value"] for item in inputs["evidence_items"] if item["kind"] == kind]
    if len(matches) != 1:
        raise ValueError(f"REPLAY_EVIDENCE_ITEM_SET_INVALID:{kind}")
    return matches[0]


def project_from_evidence(inputs: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Resolve only the bounded decision projection from observable evidence."""
    classifications = inputs["classifications"]
    slots = inputs["slots"]
    if len({item["attempt_id"] for item in classifications}) != len(classifications):
        raise ValueError("REPLAY_DUPLICATE_ATTEMPT_ID")
    if len({item["slot_id"] for item in slots}) != len(slots):
        raise ValueError("REPLAY_DUPLICATE_SLOT_ID")

    counts = Counter(item["primary_classification"] for item in classifications)
    failure_semantics_pass = (
        len(classifications) == 28
        and counts
        == {
            "ELIGIBLE_SUCCESS": 9,
            "VALID_OUTPUT_ORACLE_FAIL": 9,
            "TERMINAL_POLICY_FAILURE": 7,
            "INFRASTRUCTURE_CENSORED": 1,
            "HARNESS_CENSORED": 2,
        }
        and all(not item["identity_used"] and not item["recovery_used"] for item in classifications)
    )
    controls = inputs["matrix_controls"]
    resolutions = Counter(item["outcome_resolution"] for item in slots)
    slot_pass = (
        len(slots) == 24
        and resolutions
        == {
            "RESOLVED_ELIGIBLE_SUCCESS": 9,
            "RESOLVED_TERMINAL_NEGATIVE": 14,
            "CENSORED_HARNESS": 1,
        }
        and all(controls.values())
    )

    quality_slots = [item for item in slots if item["quality_eligible"]]
    by_case: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    for slot in quality_slots:
        by_case[slot["case_id"]][slot["repeat_id"]].add(slot["anonymous_arm_id"])
    balanced = {
        case_id
        for case_id, repeats in by_case.items()
        if any(len(arms) == 3 for arms in repeats.values())
    }
    depths = [sum(len(arms) == 3 for arms in repeats.values()) for repeats in by_case.values()]
    minimum_depth = min(depths, default=0)
    quality_sufficient = len(balanced) >= 4 and minimum_depth >= 2

    retry = _item(inputs, "retry")
    outcome = _item(inputs, "outcome")
    reliability_sufficient = (
        len(classifications) == 28
        and retry["attempt_count"] == 28
        and retry["all_attempts_in_cost"]
        and retry["cost_reconciliation"]["exact_match"]
        and retry["retry_burden"] == 4
        and not retry["failure_zero_imputation"]
        and outcome["resolved_slot_count"] / 24 >= 0.9
    )
    supplemental = _item(inputs, "supplemental")
    supplemental_rejected = (
        supplemental["authorized_slot_ids"] == []
        and supplemental["maximum_real_starts"] == 0
        and supplemental["decision"] == "AUTOMATED_REJECTED"
        and not supplemental["original_budget_mutated"]
    )
    gap = _item(inputs, "component_gap")
    gap_groups = gap["eligible_gap_groups"]
    component_specifiable = (
        len(gap_groups) >= 2
        and all(len(set(group["case_ids"])) >= 2 for group in gap_groups)
        and gap["infrastructure_excluded"]
        and gap["recovery_excluded"]
        and gap["agent_votes_excluded"]
    )

    next_phase = "PHASE-EVIDENCE-EXPANSION-002D"
    excluded = sorted(
        ["RECOVERY_AFFECTED_EVIDENCE", "AGENT_VOTES", "HUMAN_TECHNICAL_GATE", "ARM_IDENTITY"]
    )

    def projection(decision: str, accepted_scope: str, route: str | None) -> dict[str, Any]:
        return {
            "decision": decision,
            "accepted_scope": accepted_scope,
            "next_phase_allowed": route,
            "excluded_evidence": excluded,
            "posthoc_observation_policy": True,
            "positive_performance_superiority_claim_allowed": False,
            "quality_reliability_conflated": False,
            "terminal_negative_zero_imputed": False,
            "majority_vote_used": False,
            "human_technical_gate_used": False,
            "recovery_ranked": False,
            "identity_used": False,
        }

    return {
        "DECISION-FAILURE-SEMANTICS-002D-R1": projection(
            "AUTOMATED_ACCEPTED" if failure_semantics_pass else "AUTOMATED_REJECTED",
            "POLICY_ONLY" if failure_semantics_pass else "NONE",
            next_phase,
        ),
        "DECISION-SLOT-RESOLUTION-002D-R1": projection(
            "AUTOMATED_ACCEPTED" if slot_pass else "RETEST_REQUIRED",
            "POLICY_ONLY" if slot_pass else "NONE",
            next_phase if slot_pass else None,
        ),
        "DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1": projection(
            "AUTOMATED_REJECTED" if supplemental_rejected else "RETEST_REQUIRED",
            "NONE",
            next_phase if supplemental_rejected else None,
        ),
        "DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1": projection(
            "AUTOMATED_ACCEPTED" if quality_sufficient else "EVIDENCE_INSUFFICIENT",
            "QUALITY_ONLY" if quality_sufficient else "NONE",
            "PHASE-SKILL-INTEGRATION-003" if quality_sufficient else next_phase,
        ),
        "DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1": projection(
            "AUTOMATED_ACCEPTED" if reliability_sufficient else "EVIDENCE_INSUFFICIENT",
            "RELIABILITY_ONLY" if reliability_sufficient else "NONE",
            next_phase,
        ),
        "DECISION-ARCHITECTURE-002D-R1": projection(
            "AUTOMATED_ABSTAINED" if quality_sufficient else "EVIDENCE_INSUFFICIENT",
            "NONE",
            None if quality_sufficient else next_phase,
        ),
        "DECISION-COMPONENT-READINESS-002D-R1": projection(
            "AUTOMATED_ACCEPTED" if component_specifiable else "EVIDENCE_INSUFFICIENT",
            "SPECIFICATION_ONLY" if component_specifiable else "NONE",
            next_phase,
        ),
    }


def recorded_projection(root: Path) -> dict[str, dict[str, str]]:
    decisions = [
        read_json(root / RESULT_ROOT / "automated_decisions" / filename)
        for filename in DECISION_FILES.values()
    ]
    errors = validate_decisions(root, decisions)
    if errors:
        raise ValueError("REPLAY_DECISION_SET_INVALID:" + ",".join(errors))
    result = {}
    for envelope in decisions:
        core = envelope["automated_decision"]
        if core["accepted_scope"] != envelope["accepted_scope"]:
            raise ValueError(f"REPLAY_ACCEPTED_SCOPE_MISMATCH:{core['decision_id']}")
        result[core["decision_id"]] = {
            "decision": core["decision"],
            "accepted_scope": envelope["accepted_scope"],
            "next_phase_allowed": core["next_phase_allowed"],
            "excluded_evidence": sorted(core["excluded_evidence"]),
            "posthoc_observation_policy": envelope["posthoc_observation_policy"],
            "positive_performance_superiority_claim_allowed": envelope[
                "positive_performance_superiority_claim_allowed"
            ],
            "quality_reliability_conflated": envelope["quality_reliability_conflated"],
            "terminal_negative_zero_imputed": envelope["terminal_negative_zero_imputed"],
            "majority_vote_used": envelope["majority_vote_used"],
            "human_technical_gate_used": envelope["human_technical_gate_used"],
            "recovery_ranked": envelope["recovery_ranked"],
            "identity_used": envelope["identity_used"],
        }
    return result


def replay_variants(inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    variants: dict[str, dict[str, Any]] = {"ORIGINAL": deepcopy(inputs)}
    attempt_order = deepcopy(inputs)
    attempt_order["classifications"].reverse()
    variants["ATTEMPT_ORDER_PERMUTATION"] = attempt_order
    evidence_order = deepcopy(inputs)
    evidence_order["evidence_items"].reverse()
    variants["EVIDENCE_ITEM_ORDER_PERMUTATION"] = evidence_order
    arm_labels = deepcopy(inputs)
    arm_map = {"ARM-A": "ARM-C", "ARM-B": "ARM-A", "ARM-C": "ARM-B"}
    for collection in (arm_labels["classifications"], arm_labels["slots"]):
        for item in collection:
            item["anonymous_arm_id"] = arm_map[item["anonymous_arm_id"]]
    variants["ANONYMOUS_ARM_LABEL_PERMUTATION"] = arm_labels
    flag_order = deepcopy(inputs)
    for item in flag_order["classifications"]:
        item["secondary_flags"].reverse()
    variants["FAILURE_FLAG_ORDER_PERMUTATION"] = flag_order
    return {name: {"projection": project_from_evidence(value)} for name, value in variants.items()}


def build_replay(root: Path) -> dict[str, Any]:
    variants = replay_variants(_read_inputs(root))
    expected = recorded_projection(root)
    for variant in variants.values():
        variant["projection_hash"] = sha256_json(variant["projection"])
        variant["matches_recorded_decisions"] = variant["projection"] == expected
    hashes = {variant["projection_hash"] for variant in variants.values()}
    stable = len(hashes) == 1 and all(
        variant["matches_recorded_decisions"] for variant in variants.values()
    )
    decision_replay_hashes = {
        decision_id: read_json(root / RESULT_ROOT / "automated_decisions" / filename)[
            "automated_decision"
        ]["replay_hash"]
        for decision_id, filename in DECISION_FILES.items()
    }
    for variant in variants.values():
        variant["decision_replay_hashes"] = decision_replay_hashes
    replay = {
        "schema_version": "1.0.0",
        "replay_id": "PHASE-002D-R1-FAILURE-AWARE-REPLAY-001",
        "mode": "OFFLINE_NO_MODEL_NO_NETWORK",
        "variant_count": len(variants),
        "variants": variants,
        "stable": stable,
        "decision_ids": sorted(expected),
        "canonical_scope_projection": "WRAPPER_EQUALS_AUTOMATED_DECISION",
        "next_phase_allowed": "PHASE-EVIDENCE-EXPANSION-002D" if stable else None,
        "model_starts": 0,
        "api_key_used": False,
        "api_billing_used": False,
        "network_used": False,
        "created_at": CREATED_AT,
    }
    replay["replay_hash"] = sha256_json(replay)
    if not stable:
        raise ValueError("PHASE002D_R1_REPLAY_UNSTABLE")
    return replay


def check_or_write_replay(root: Path, *, check: bool) -> dict[str, Any]:
    replay = build_replay(root)
    errors = check_or_write(root / REPLAY_PATH, replay, check=check)
    return {
        "status": "PASS" if not errors else "FAIL",
        "stable": replay["stable"],
        "variant_count": replay["variant_count"],
        "next_phase_allowed": replay["next_phase_allowed"],
        "replay_hash": replay["replay_hash"],
        "errors": errors,
    }
