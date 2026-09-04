"""Deterministic lifecycle transition and STALE-closure kernel."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from experiments.shadow_prototypes.common.interface import sha256_json


class LifecycleState(StrEnum):
    TASK_CREATED = "TASK_CREATED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    COMMAND_COMPLETED = "COMMAND_COMPLETED"
    ARTIFACT_PRODUCED = "ARTIFACT_PRODUCED"
    AUTOMATIC_VALIDATION_PASSED = "AUTOMATIC_VALIDATION_PASSED"
    AUTOMATIC_ADJUDICATION_ACCEPTED = "AUTOMATIC_ADJUDICATION_ACCEPTED"
    FINAL_EVIDENCE_FROZEN = "FINAL_EVIDENCE_FROZEN"
    FORMALLY_INTEGRATED = "FORMALLY_INTEGRATED"
    STALE = "STALE"
    AUTOMATED_REJECTED = "AUTOMATED_REJECTED"


ORDERED_STATES = tuple(LifecycleState)[:8]
REQUIRED_GATES = (
    "claim-evidence-support-gate",
    "leakage-safe-model-comparison-gate",
)


def _stale_closure(graph: Any, changed: set[str]) -> tuple[set[str], bool]:
    if not isinstance(graph, Mapping):
        return set(changed), False
    if any(
        not isinstance(node, str)
        or not isinstance(children, (list, tuple))
        or any(not isinstance(child, str) for child in children)
        for node, children in graph.items()
    ):
        return set(changed), False
    visiting: set[str] = set()
    visited: set[str] = set()

    def cyclic(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(cyclic(child) for child in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(cyclic(str(node)) for node in graph):
        return set(changed), False
    stale = set(changed)
    frontier = list(changed)
    while frontier:
        node = frontier.pop()
        for child in graph.get(node, ()):
            if child not in stale:
                stale.add(child)
                frontier.append(child)
    return stale, True


def _trusted_stage(stage: LifecycleState, record: Any, isolated_state: Mapping[str, Any]) -> bool:
    if not isinstance(record, Mapping):
        return False
    body = record.get("artifact_body")
    trusted_hashes = isolated_state.get("trusted_stage_hashes", {})
    trusted_runs = set(isolated_state.get("trusted_run_ids", ()))
    return bool(
        isinstance(body, Mapping)
        and isinstance(trusted_hashes, Mapping)
        and record.get("registered") is True
        and record.get("current") is True
        and record.get("authority") == "existing-state-transition-ledger"
        and body.get("stage") == stage.value
        and body.get("run_id") in trusted_runs
        and record.get("artifact_hash") == sha256_json(body)
        and record.get("artifact_hash") == trusted_hashes.get(stage.value)
        and (
            stage is not LifecycleState.AUTOMATIC_ADJUDICATION_ACCEPTED
            or record.get("audited") is True
        )
    )


def _trusted_gate(component_id: str, record: Any, isolated_state: Mapping[str, Any]) -> bool:
    if not isinstance(record, Mapping):
        return False
    body = {
        key: record.get(key)
        for key in (
            "component_id",
            "decision_id",
            "run_id",
            "authority",
            "outcome",
            "current",
            "audited",
        )
    }
    hashes = isolated_state.get("trusted_gate_hashes", {})
    return bool(
        isinstance(hashes, Mapping)
        and record.get("component_id") == component_id
        and record.get("decision_id")
        and record.get("run_id") in set(isolated_state.get("trusted_run_ids", ()))
        and record.get("authority") == "existing-native-component-ledger"
        and record.get("outcome") == "PASS"
        and record.get("current") is True
        and record.get("audited") is True
        and record.get("artifact_hash") == sha256_json(body)
        and record.get("artifact_hash") == hashes.get(component_id)
    )


def evaluate_lifecycle(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    """Return the greatest evidenced stage and exact proposed STALE closure."""
    reasons: list[str] = []
    requested_raw = payload.get("requested_state")
    try:
        requested = LifecycleState(str(requested_raw))
    except ValueError:
        requested = None
        reasons.append("K1_LIFECYCLE_UNKNOWN_STATE")

    evidenced_raw = payload.get("evidenced_stages", ())
    if not isinstance(evidenced_raw, (list, tuple)):
        evidenced: tuple[str, ...] = ()
        reasons.append("K1_LIFECYCLE_STAGE_SEQUENCE_INVALID")
    else:
        evidenced = tuple(str(item) for item in evidenced_raw)
    expected = (
        ORDERED_STATES[: ORDERED_STATES.index(requested) + 1] if requested in ORDERED_STATES else ()
    )
    if evidenced != tuple(stage.value for stage in expected):
        reasons.append("K1_LIFECYCLE_SKIPPED_OR_UNEVIDENCED_STAGE")

    records = payload.get("evidence_records")
    greatest: str | None = None
    if not isinstance(records, Mapping):
        reasons.append("K1_LIFECYCLE_EVIDENCE_REGISTRY_INVALID")
    else:
        for stage in expected:
            if not _trusted_stage(stage, records.get(stage.value), isolated_state):
                reasons.append(f"K1_LIFECYCLE_STAGE_EVIDENCE_INVALID:{stage.value}")
                break
            greatest = stage.value

    if payload.get("state_truth_path") != "state/project_state.json":
        reasons.append("K1_LIFECYCLE_SECOND_STATE_TRUTH_REJECTED")
    if payload.get("actor") != "MAIN_AGENT_FORMAL_STATE_WRITER":
        reasons.append("K1_LIFECYCLE_UNAUTHORIZED_WRITER")
    if payload.get("narrative_override"):
        reasons.append("K1_LIFECYCLE_NARRATIVE_BYPASS_REJECTED")

    graph = payload.get("dependency_graph")
    trusted_graph = isolated_state.get("trusted_dependency_graph")
    if (
        not isinstance(trusted_graph, Mapping)
        or graph != trusted_graph
        or payload.get("dependency_graph_hash") != sha256_json(graph)
        or payload.get("dependency_graph_hash")
        != isolated_state.get("trusted_dependency_graph_hash")
    ):
        reasons.append("K1_LIFECYCLE_UNTRUSTED_DEPENDENCY_GRAPH")
    changed_raw = payload.get("changed_nodes", ())
    if not isinstance(changed_raw, (list, tuple)):
        changed: set[str] = set()
        reasons.append("K1_LIFECYCLE_CHANGED_NODE_SET_INVALID")
    else:
        changed = {str(item) for item in changed_raw}
    challenge = payload.get("team_challenge", {})
    if not isinstance(challenge, Mapping):
        reasons.append("K1_LIFECYCLE_CHALLENGE_INVALID")
    elif challenge.get("supported") is True:
        target = challenge.get("target")
        if not isinstance(target, str) or not target:
            reasons.append("K1_LIFECYCLE_CHALLENGE_TARGET_MISSING")
        else:
            changed.add(target)
            if requested is not LifecycleState.STALE:
                reasons.append("K1_LIFECYCLE_SUPPORTED_CHALLENGE_STALE")
            challenge_body = {
                key: challenge.get(key)
                for key in ("target", "finding_hash", "test_hash", "readjudication_id")
            }
            trusted_challenges = isolated_state.get("trusted_challenge_hashes", {})
            challenge_hash = sha256_json(challenge_body)
            if (
                not isinstance(trusted_challenges, Mapping)
                or not challenge.get("finding_hash")
                or not challenge.get("test_hash")
                or not challenge.get("readjudication_id")
                or challenge_hash != trusted_challenges.get(target)
            ):
                reasons.append("K1_LIFECYCLE_CHALLENGE_EVIDENCE_INVALID")
    stale, graph_valid = _stale_closure(graph, changed)
    if not graph_valid:
        reasons.append("K1_LIFECYCLE_DEPENDENCY_GRAPH_INVALID")
    if stale and requested is not LifecycleState.STALE:
        reasons.append("K1_LIFECYCLE_STALE_DEPENDENCY")

    if requested in {LifecycleState.STALE, LifecycleState.AUTOMATED_REJECTED}:
        disposition = payload.get("disposition_record")
        trusted_dispositions = isolated_state.get("trusted_disposition_hashes", {})
        if (
            not isinstance(disposition, Mapping)
            or not isinstance(trusted_dispositions, Mapping)
            or disposition.get("state") != requested.value
            or disposition.get("authority") != "existing-state-transition-ledger"
            or disposition.get("audited") is not True
            or (
                requested is LifecycleState.AUTOMATED_REJECTED
                and disposition.get("hard_gate_failure") is not True
            )
            or disposition.get("artifact_hash") != trusted_dispositions.get(requested.value)
        ):
            reasons.append("K1_LIFECYCLE_DISPOSITION_EVIDENCE_INVALID")
        if requested is LifecycleState.STALE and not stale:
            reasons.append("K1_LIFECYCLE_STALE_CAUSE_REQUIRED")

    if requested in ORDERED_STATES:
        gates = payload.get("upstream_gates")
        if not isinstance(gates, Mapping) or any(
            not _trusted_gate(component, gates.get(component), isolated_state)
            for component in REQUIRED_GATES
        ):
            reasons.append("K1_LIFECYCLE_REQUIRED_GATE_NOT_PASS")
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {
            "greatest_evidenced_stage": greatest,
            "stale_nodes": sorted(stale),
        },
    )


__all__ = ["LifecycleState", "evaluate_lifecycle"]
