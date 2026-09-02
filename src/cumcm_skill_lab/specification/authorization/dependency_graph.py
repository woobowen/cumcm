"""Construct and validate the acyclic R2A authorization dependency graph."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import check_or_write, read_json, sha256_json

from .evidence_freeze import verify_input_freeze
from .models import CREATED_AT, DAG_ID, DEPENDENCY_PATH, FREEZE_PATH


def build_dependency_graph(root: Path) -> dict[str, Any]:
    freeze = read_json(root / FREEZE_PATH)
    nodes = [
        {"id": "L0-COMPONENT-SPECS", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L0-INTERACTION", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L0-CANDIDATE-SET", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L0-BENCHMARK", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L0-THRESHOLD-PROTOCOL", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L0-IMPLEMENTATION-EMBARGO", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L0-CLEAN-ROOM-PROVENANCE", "level": 0, "kind": "FROZEN_INPUT"},
        {"id": "L1-COMPONENT-DECISION", "level": 1, "kind": "PREREQUISITE_DECISION"},
        {"id": "L1-INTERACTION-DECISION", "level": 1, "kind": "PREREQUISITE_DECISION"},
        {"id": "L1-CANDIDATE-SET-DECISION", "level": 1, "kind": "PREREQUISITE_DECISION"},
        {"id": "L1-BENCHMARK-DECISION", "level": 1, "kind": "PREREQUISITE_DECISION"},
        {"id": "L1-THRESHOLD-DECISION", "level": 1, "kind": "PREREQUISITE_DECISION"},
        {"id": "L2-R2-DECISION-AUDIT", "level": 2, "kind": "PREREQUISITE_AUDIT"},
        {"id": "L3-R2-REPLAY", "level": 3, "kind": "PREREQUISITE_REPLAY"},
        {"id": "L4-R2A-ELIGIBILITY", "level": 4, "kind": "ELIGIBILITY"},
        {"id": "L5-R2A-AUTHORIZATION-CANDIDATE", "level": 5, "kind": "DECISION_CANDIDATE"},
        {"id": "L6-R2A-FINAL-AUDITOR", "level": 6, "kind": "FINAL_AUDIT"},
        {"id": "L7-R2A-AUTHORIZATION-SEAL", "level": 7, "kind": "ACTIVE_DECISION"},
        {"id": "L7-R2A-FINAL-REPLAY", "level": 7, "kind": "FINAL_REPLAY"},
        {"id": "L7-FORMAL-STATE-TRANSITION", "level": 7, "kind": "STATE_TRANSITION"},
    ]
    edges = [
        ["L0-COMPONENT-SPECS", "L1-COMPONENT-DECISION"],
        ["L0-INTERACTION", "L1-INTERACTION-DECISION"],
        ["L0-CANDIDATE-SET", "L1-CANDIDATE-SET-DECISION"],
        ["L0-BENCHMARK", "L1-BENCHMARK-DECISION"],
        ["L0-THRESHOLD-PROTOCOL", "L1-THRESHOLD-DECISION"],
        ["L0-IMPLEMENTATION-EMBARGO", "L4-R2A-ELIGIBILITY"],
        ["L0-CLEAN-ROOM-PROVENANCE", "L4-R2A-ELIGIBILITY"],
    ]
    decision_nodes = [item["id"] for item in nodes if item["level"] == 1]
    edges.extend([node, "L2-R2-DECISION-AUDIT"] for node in decision_nodes)
    edges.extend(
        [
            ["L2-R2-DECISION-AUDIT", "L3-R2-REPLAY"],
            ["L3-R2-REPLAY", "L4-R2A-ELIGIBILITY"],
            *[[node, "L4-R2A-ELIGIBILITY"] for node in decision_nodes],
            ["L4-R2A-ELIGIBILITY", "L5-R2A-AUTHORIZATION-CANDIDATE"],
            ["L5-R2A-AUTHORIZATION-CANDIDATE", "L6-R2A-FINAL-AUDITOR"],
            ["L6-R2A-FINAL-AUDITOR", "L7-R2A-AUTHORIZATION-SEAL"],
            ["L7-R2A-AUTHORIZATION-SEAL", "L7-R2A-FINAL-REPLAY"],
            ["L6-R2A-FINAL-AUDITOR", "L7-FORMAL-STATE-TRANSITION"],
            ["L7-R2A-FINAL-REPLAY", "L7-FORMAL-STATE-TRANSITION"],
        ]
    )
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "graph_id": DAG_ID,
        "created_at": CREATED_AT,
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "nodes": nodes,
        "edges": [{"source": source, "target": target} for source, target in edges],
        "prerequisite_audit_node": "L2-R2-DECISION-AUDIT",
        "final_authorization_audit_node": "L6-R2A-FINAL-AUDITOR",
        "candidate_node": "L5-R2A-AUTHORIZATION-CANDIDATE",
        "active_decision_node": "L7-R2A-AUTHORIZATION-SEAL",
        "final_replay_node": "L7-R2A-FINAL-REPLAY",
        "state_transition_node": "L7-FORMAL-STATE-TRANSITION",
        "cycle_detected": False,
    }
    body["graph_hash"] = sha256_json(body)
    return body


def cycle_nodes(graph: dict[str, Any]) -> list[str]:
    ids = {item["id"] for item in graph.get("nodes", [])}
    indegree = {node: 0 for node in ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in graph.get("edges", []):
        source, target = edge.get("source"), edge.get("target")
        if source in ids and target in ids:
            outgoing[source].append(target)
            indegree[target] += 1
    queue = deque(sorted(node for node, count in indegree.items() if count == 0))
    visited: list[str] = []
    while queue:
        node = queue.popleft()
        visited.append(node)
        for target in sorted(outgoing[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return sorted(ids - set(visited))


def verify_dependency_graph(root: Path, graph: dict[str, Any] | None = None) -> list[str]:
    if graph is None:
        if not (root / DEPENDENCY_PATH).is_file():
            return ["PHASE002D_R2A_DEPENDENCY_GRAPH_MISSING"]
        graph = read_json(root / DEPENDENCY_PATH)
    errors: list[str] = []
    body = dict(graph)
    recorded_hash = body.pop("graph_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("PHASE002D_R2A_DEPENDENCY_GRAPH_HASH_MISMATCH")
    schema = read_json(root / "contracts/authorization_dependency_graph.schema.json")
    schema_errors = sorted(Draft202012Validator(schema).iter_errors(graph), key=str)
    if schema_errors:
        errors.append(f"PHASE002D_R2A_DEPENDENCY_SCHEMA_INVALID:{schema_errors[0].message}")
    cycles = cycle_nodes(graph)
    if cycles or graph.get("cycle_detected") is not False:
        errors.append("PHASE002D_R2A_DEPENDENCY_CYCLE")
    ids = {item["id"] for item in graph.get("nodes", [])}
    required = {
        "L2-R2-DECISION-AUDIT",
        "L3-R2-REPLAY",
        "L4-R2A-ELIGIBILITY",
        "L5-R2A-AUTHORIZATION-CANDIDATE",
        "L6-R2A-FINAL-AUDITOR",
        "L7-R2A-AUTHORIZATION-SEAL",
        "L7-R2A-FINAL-REPLAY",
        "L7-FORMAL-STATE-TRANSITION",
    }
    if not required <= ids:
        errors.append("PHASE002D_R2A_DEPENDENCY_REQUIRED_NODE_MISSING")
    edges = {(item["source"], item["target"]) for item in graph.get("edges", [])}
    required_edges = {
        ("L2-R2-DECISION-AUDIT", "L3-R2-REPLAY"),
        ("L3-R2-REPLAY", "L4-R2A-ELIGIBILITY"),
        ("L4-R2A-ELIGIBILITY", "L5-R2A-AUTHORIZATION-CANDIDATE"),
        ("L5-R2A-AUTHORIZATION-CANDIDATE", "L6-R2A-FINAL-AUDITOR"),
        ("L6-R2A-FINAL-AUDITOR", "L7-R2A-AUTHORIZATION-SEAL"),
        ("L7-R2A-AUTHORIZATION-SEAL", "L7-R2A-FINAL-REPLAY"),
        ("L6-R2A-FINAL-AUDITOR", "L7-FORMAL-STATE-TRANSITION"),
        ("L7-R2A-FINAL-REPLAY", "L7-FORMAL-STATE-TRANSITION"),
    }
    if not required_edges <= edges:
        errors.append("PHASE002D_R2A_DEPENDENCY_REQUIRED_EDGE_MISSING")
    forbidden = {
        ("L6-R2A-FINAL-AUDITOR", "L5-R2A-AUTHORIZATION-CANDIDATE"),
        ("L5-R2A-AUTHORIZATION-CANDIDATE", "L2-R2-DECISION-AUDIT"),
        ("L7-FORMAL-STATE-TRANSITION", "L6-R2A-FINAL-AUDITOR"),
    }
    if forbidden & edges:
        errors.append("PHASE002D_R2A_DEPENDENCY_FORBIDDEN_BACK_EDGE")
    errors.extend(verify_input_freeze(root))
    return sorted(set(errors))


def check_or_write_dependency_graph(root: Path, *, check: bool) -> dict[str, Any]:
    graph = (
        read_json(root / DEPENDENCY_PATH) if check and (root / DEPENDENCY_PATH).is_file() else None
    )
    if check:
        errors = verify_dependency_graph(root, graph)
    else:
        graph = build_dependency_graph(root)
        errors = check_or_write(root / DEPENDENCY_PATH, graph, check=False)
        errors.extend(verify_dependency_graph(root, graph))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "graph_id": graph.get("graph_id") if graph else None,
        "graph_hash": graph.get("graph_hash") if graph else None,
        "node_count": len(graph.get("nodes", [])) if graph else 0,
        "edge_count": len(graph.get("edges", [])) if graph else 0,
        "cycle_detected": bool(cycle_nodes(graph)) if graph else None,
    }
