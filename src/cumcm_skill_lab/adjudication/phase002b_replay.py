"""Deterministically finalize and replay Phase 002B automated decisions offline."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .bundles.role_views import ROLE_ORDER
from .formal_outputs import (
    final_decision_paths,
    formal_output_path,
    proposal_decision_paths,
)
from .models import file_sha256, read_json, read_yaml, sha256_json
from .recovery_freeze import verify_manifest as verify_input_freeze

NEXT_PHASE = "PHASE-SKILL-INTEGRATION-003"


def build_replay(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors = verify_input_freeze(root)
    if errors:
        raise ValueError("INPUT_FREEZE_BROKEN:" + ",".join(errors))
    proposals = [read_json(path) for path in proposal_decision_paths(root)]
    if len(proposals) != 3:
        raise ValueError("PRE_AUDIT_DECISIONS_INCOMPLETE")
    meta = read_json(formal_output_path(root, "EVIDENCE_META_ADJUDICATOR"))
    audit = read_json(formal_output_path(root, "DECISION_AUDITOR"))
    _validate_proposals(meta, audit, proposals)
    phase_allowed = _phase_transition_allowed(proposals, audit)
    decisions = [_finalize(proposal, audit, phase_allowed=phase_allowed) for proposal in proposals]
    validator = Draft202012Validator(read_json(root / "contracts/automated_decision.schema.json"))
    for decision in decisions:
        validator.validate(decision)
    base = _replay_projection(root, decisions, meta, audit)
    evidence_order = _permute_sequences(base)
    judge_order = deepcopy(base)
    judge_order["judges"] = list(reversed(judge_order["judges"]))
    label_swap = _round_trip_anonymous_labels(base)
    recovery_only = deepcopy(base)
    recovery_only["recovery_exclusion"] = {
        **recovery_only["recovery_exclusion"],
        "records": list(reversed(recovery_only["recovery_exclusion"]["records"])),
    }
    variants = {
        "original": _normalized_hash(base),
        "evidence_item_order_permuted": _normalized_hash(evidence_order),
        "judge_file_order_permuted": _normalized_hash(judge_order),
        "anonymous_label_swapped_then_mapped_back": _normalized_hash(label_swap),
        "recovery_present_but_excluded": _normalized_hash(recovery_only),
    }
    stable = len(set(variants.values())) == 1
    replay = {
        "schema_version": "1.0.0",
        "mode": "OFFLINE_NO_MODEL",
        "input_freeze_hash": read_json(
            root / "evals/results/phase-002b/input_freeze_manifest.json"
        )["freeze_hash"],
        "policy_hash": meta["policy_hash"],
        "audit_id": audit["audit_id"],
        "audit_result": audit["result"],
        "decision_ids": [item["decision_id"] for item in decisions],
        "decision_values": {item["decision_id"]: item["decision"] for item in decisions},
        "accepted_scopes": {item["decision_id"]: item["accepted_scope"] for item in decisions},
        "next_phase_allowed": NEXT_PHASE if phase_allowed else None,
        "variants": variants,
        "stable": stable,
        "resulting_action": "RETAIN_DECISIONS" if stable else "RETEST_REQUIRED",
        "final_decision_hashes": {item["decision_id"]: sha256_json(item) for item in decisions},
    }
    replay["content_hash"] = sha256_json(replay)
    if not stable:
        raise ValueError("DETERMINISTIC_REPLAY_UNSTABLE")
    return decisions, replay


def existing_replay_errors(root: Path) -> list[str]:
    expected_decisions, expected_replay = build_replay(root)
    errors: list[str] = []
    actual_paths = final_decision_paths(root)
    if len(actual_paths) != 3:
        errors.append("FINAL_DECISIONS_INCOMPLETE")
    actual = {read_json(path)["decision_id"]: read_json(path) for path in actual_paths}
    for expected in expected_decisions:
        if actual.get(expected["decision_id"]) != expected:
            errors.append(f"FINAL_DECISION_MISMATCH:{expected['decision_id']}")
    replay_path = root / "evals/results/phase-002b/replay/replay.json"
    if not replay_path.is_file():
        errors.append("REPLAY_RECORD_MISSING")
    elif read_json(replay_path) != expected_replay:
        errors.append("REPLAY_RECORD_MISMATCH")
    return errors


def _validate_proposals(
    meta: dict[str, Any], audit: dict[str, Any], proposals: list[dict[str, Any]]
) -> None:
    meta_by_id = {item["decision_id"]: item for item in meta["decisions"]}
    proposal_ids = {item["decision_id"] for item in proposals}
    if proposal_ids != set(meta_by_id):
        raise ValueError("PRE_AUDIT_DECISION_SET_MISMATCH")
    if set(audit["decision_ids"]) != proposal_ids:
        raise ValueError("AUDIT_DECISION_SET_MISMATCH")
    comparable = (
        "decision_type",
        "target_ids",
        "hard_gate_status",
        "evidence_sufficiency",
        "decision",
        "reason_codes",
        "accepted_scope",
        "retest_requirements",
        "confidence",
        "component_results",
    )
    for proposal in proposals:
        meta_item = meta_by_id[proposal["decision_id"]]
        for key in comparable:
            if proposal.get(key) != meta_item.get(key):
                raise ValueError(
                    f"PRE_AUDIT_DECISION_META_MISMATCH:{proposal['decision_id']}:{key}"
                )
        if proposal["meta_adjudication"] != meta["meta_id"]:
            raise ValueError("PRE_AUDIT_META_ID_MISMATCH")


def _phase_transition_allowed(proposals: list[dict[str, Any]], audit: dict[str, Any]) -> bool:
    if audit["result"] != "PASS" or not audit["replayable"]:
        return False
    by_type = {item["decision_type"]: item for item in proposals}
    architecture = by_type["ARCHITECTURE"]
    components = by_type["COMPONENTS"]
    return bool(
        architecture["decision"] == "AUTOMATED_ACCEPTED"
        and components["decision"] == "AUTOMATED_ACCEPTED"
        and components["accepted_scope"] == "SPECIFICATION_ONLY"
    )


def _finalize(
    proposal: dict[str, Any], audit: dict[str, Any], *, phase_allowed: bool
) -> dict[str, Any]:
    decision = deepcopy(proposal)
    decision["decision_audit"] = audit["audit_id"]
    if audit["result"] != "PASS":
        decision["decision"] = "RETEST_REQUIRED"
        decision["accepted_scope"] = "NONE"
        decision["rejected_scope"] = decision["target_ids"]
        decision["reason_codes"] = sorted(
            {*decision["reason_codes"], f"DECISION_AUDIT_{audit['result']}"}
        )
        decision["retest_requirements"] = sorted(
            {*decision["retest_requirements"], *audit["failures"], *audit["blockers"]}
        )
        if "component_results" in decision:
            decision["component_results"] = [
                {
                    **component,
                    "decision": "RETEST_REQUIRED",
                    "accepted_scope": "NONE",
                    "reason_codes": sorted(
                        {*component["reason_codes"], f"DECISION_AUDIT_{audit['result']}"}
                    ),
                }
                for component in decision["component_results"]
            ]
    decision["next_phase_allowed"] = (
        NEXT_PHASE if phase_allowed and decision["decision_type"] == "ARCHITECTURE" else None
    )
    decision["replay_hash"] = "0" * 64
    decision["replay_hash"] = sha256_json(
        {key: value for key, value in decision.items() if key != "replay_hash"}
    )
    return decision


def _replay_projection(
    root: Path,
    decisions: list[dict[str, Any]],
    meta: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    judges = [read_json(formal_output_path(root, role)) for role in ROLE_ORDER[:3]]
    dissent = read_json(formal_output_path(root, "BLIND_DISSENT_JUDGE"))
    recovery = read_json(root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json")
    policy = read_yaml(root / "adjudication/policies/phase-002a.yaml")
    labels = sorted(
        {
            record["anonymous_arm_id"]
            for record in recovery["records"]
            if isinstance(record.get("anonymous_arm_id"), str)
        }
    )
    return {
        "freeze_hash": read_json(root / "evals/results/phase-002b/input_freeze_manifest.json")[
            "freeze_hash"
        ],
        "policy_hash": policy["policy_hash"],
        "judges": [
            {
                "judge_id": item["judge_id"],
                "role": item["role"],
                "recommendation": item["recommendation"],
                "evidence_refs": item["evidence_refs"],
            }
            for item in judges
        ],
        "dissent": {
            "dissent_id": dissent["dissent_id"],
            "recommendation": dissent["recommendation"],
            "evidence_refs": dissent["evidence_refs"],
        },
        "meta": {
            "meta_id": meta["meta_id"],
            "decisions": meta["decisions"],
        },
        "audit": {
            "audit_id": audit["audit_id"],
            "result": audit["result"],
            "checks": audit["checks"],
            "replayable": audit["replayable"],
        },
        "decisions": [
            {
                "decision_id": item["decision_id"],
                "decision": item["decision"],
                "accepted_scope": item["accepted_scope"],
                "next_phase_allowed": item["next_phase_allowed"],
            }
            for item in decisions
        ],
        "anonymous_labels": labels,
        "recovery_exclusion": {
            "policy": recovery["policy"],
            "ranking_eligible": False,
            "records": [
                f"{item['anonymous_arm_id']}:{item['case_id']}" for item in recovery["records"]
            ],
        },
        "source_hashes": {
            str(formal_output_path(root, role).relative_to(root)): file_sha256(
                formal_output_path(root, role)
            )
            for role in ROLE_ORDER
        },
    }


def _normalized(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalized(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        normalized = [_normalized(item) for item in value]
        return sorted(normalized, key=sha256_json)
    return value


def _normalized_hash(value: Any) -> str:
    return sha256_json(_normalized(value))


def _permute_sequences(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _permute_sequences(item) for key, item in reversed(list(value.items()))}
    if isinstance(value, list):
        return [_permute_sequences(item) for item in reversed(value)]
    return value


def _round_trip_anonymous_labels(value: dict[str, Any]) -> dict[str, Any]:
    transformed = deepcopy(value)
    labels = transformed["anonymous_labels"]
    if len(labels) < 2:
        return transformed
    first, second = labels[:2]
    mapping = {first: second, second: first}
    inverse = {new: old for old, new in mapping.items()}
    transformed = _replace_labels(transformed, mapping)
    return _replace_labels(transformed, inverse)


def _replace_labels(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_labels(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_labels(item, mapping) for item in value]
    if isinstance(value, str):
        placeholders = {key: f"__LABEL_{index}__" for index, key in enumerate(mapping)}
        for old, placeholder in placeholders.items():
            value = value.replace(old, placeholder)
        for old, placeholder in placeholders.items():
            value = value.replace(placeholder, mapping[old])
    return value
