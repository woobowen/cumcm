"""Resolve the C1 final-audit/replay semantic cycle for the one allowed C2 revision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .final_audit import FINAL_AUDIT_PATH
from .models import RESULT_ROOT, check_or_write_json, file_sha256, sha256_json

SOURCE_GRAPH_PATH = Path("evals/results/phase-002d-r2a/authorization_dependency_graph.json")
R2_AUDIT_PATH = Path("evals/results/phase-002d-r2/decision_audit/audit.json")
R2_REPLAY_PATH = Path("evals/results/phase-002d-r2/replay/replay.json")
RESOLUTION_PATH = RESULT_ROOT / "dependency_resolution/dependency-graph-c2.json"
AUDIT_NODE = "L3-R2-DECISION-AUDIT"
REPLAY_NODE = "L2-R2-REPLAY"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cycle_detected(nodes: list[dict[str, Any]], edges: list[dict[str, str]]) -> bool:
    node_ids = {item["id"] for item in nodes}
    incoming = {node: 0 for node in node_ids}
    outgoing = {node: [] for node in node_ids}
    for edge in edges:
        source, target = edge["source"], edge["target"]
        if source not in node_ids or target not in node_ids:
            return True
        outgoing[source].append(target)
        incoming[target] += 1
    ready = [node for node, count in incoming.items() if count == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for target in outgoing[node]:
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    return visited != len(node_ids)


def validate_audit_replay_order(
    graph: dict[str, Any], audit: dict[str, Any], replay_path: str
) -> list[str]:
    errors: list[str] = []
    edges = {(item["source"], item["target"]) for item in graph.get("edges", [])}
    audit_node = graph.get("prerequisite_audit_node")
    replay_node = graph.get("prerequisite_replay_node", "L3-R2-REPLAY")
    consumes_replay = replay_path in audit.get("audit_evidence_refs", [])
    if consumes_replay and (audit_node, replay_node) in edges:
        errors.append("C1_R2_AUDIT_REPLAY_SEMANTIC_CYCLE")
    if consumes_replay and (replay_node, audit_node) not in edges:
        errors.append("C1_R2_REPLAY_TO_AUDIT_PREREQUISITE_EDGE_MISSING")
    if _cycle_detected(graph.get("nodes", []), graph.get("edges", [])):
        errors.append("C1_DEPENDENCY_GRAPH_STRUCTURAL_CYCLE")
    return sorted(set(errors))


def build_corrected_graph(root: Path) -> dict[str, Any]:
    source = _read_json(root / SOURCE_GRAPH_PATH)
    rename = {
        "L2-R2-DECISION-AUDIT": AUDIT_NODE,
        "L3-R2-REPLAY": REPLAY_NODE,
    }
    nodes = []
    for item in source["nodes"]:
        node = dict(item)
        node["id"] = rename.get(node["id"], node["id"])
        if node["id"] == AUDIT_NODE:
            node["level"] = 3
        elif node["id"] == REPLAY_NODE:
            node["level"] = 2
        nodes.append(node)
    edges = [
        {
            "source": rename.get(item["source"], item["source"]),
            "target": rename.get(item["target"], item["target"]),
        }
        for item in source["edges"]
        if not (item["source"] == "L2-R2-DECISION-AUDIT" and item["target"] == "L3-R2-REPLAY")
    ]
    decision_nodes = sorted(
        item["id"] for item in nodes if item.get("kind") == "PREREQUISITE_DECISION"
    )
    edges.extend({"source": node, "target": REPLAY_NODE} for node in decision_nodes)
    edges.append({"source": REPLAY_NODE, "target": AUDIT_NODE})
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "graph_id": "PHASE-002D-R2A-C2-AUTHORIZATION-DAG-001",
        "graph_purpose": "C2_AUTHORIZATION_EVALUATION_PRECEDENCE",
        "edge_semantics": "ACTUAL_CONSUMER_PREREQUISITE_ORDER",
        "source_graph_path": SOURCE_GRAPH_PATH.as_posix(),
        "source_graph_file_sha256": file_sha256(root / SOURCE_GRAPH_PATH),
        "source_graph_hash": source["graph_hash"],
        "nodes": nodes,
        "edges": edges,
        "prerequisite_replay_node": REPLAY_NODE,
        "prerequisite_audit_node": AUDIT_NODE,
        "candidate_node": rename.get(source["candidate_node"], source["candidate_node"]),
        "final_authorization_audit_node": rename.get(
            source["final_authorization_audit_node"], source["final_authorization_audit_node"]
        ),
        "active_decision_node": source["active_decision_node"],
        "final_replay_node": source["final_replay_node"],
        "state_transition_node": source["state_transition_node"],
        "cycle_detected": _cycle_detected(nodes, edges),
        "historical_source_modified": False,
    }
    body["graph_hash"] = sha256_json(body)
    return body


def build_dependency_resolution(root: Path) -> dict[str, Any]:
    source = _read_json(root / SOURCE_GRAPH_PATH)
    audit = _read_json(root / R2_AUDIT_PATH)
    final_audit = _read_json(root / FINAL_AUDIT_PATH)
    corrected = build_corrected_graph(root)
    original_errors = validate_audit_replay_order(
        {
            **source,
            "prerequisite_replay_node": "L3-R2-REPLAY",
        },
        audit,
        R2_REPLAY_PATH.as_posix(),
    )
    corrected_errors = validate_audit_replay_order(corrected, audit, R2_REPLAY_PATH.as_posix())
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "resolution_id": "PHASE-002D-R2A-C1-FINAL-001-C2-DEPENDENCY-RESOLUTION-001",
        "finding_id": "R2A-C1-FINAL-001",
        "parent_artifact_hash": final_audit["output_hash"],
        "artifact_sequence_index": 11,
        "source_graph_hash": source["graph_hash"],
        "source_graph_file_sha256": file_sha256(root / SOURCE_GRAPH_PATH),
        "source_graph_unchanged": True,
        "original_semantic_errors": original_errors,
        "corrected_graph": corrected,
        "corrected_graph_errors": corrected_errors,
        "required_test": "C1-DET-R2-AUDIT-REPLAY-ACYCLIC-PREREQUISITE-001",
        "status": (
            "PASS"
            if "C1_R2_AUDIT_REPLAY_SEMANTIC_CYCLE" in original_errors
            and "C1_R2_REPLAY_TO_AUDIT_PREREQUISITE_EDGE_MISSING" in original_errors
            and not corrected_errors
            else "FAIL"
        ),
    }
    body["resolution_hash"] = sha256_json(body)
    return body


def validate_dependency_resolution(root: Path, value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    body = dict(value)
    recorded = body.pop("resolution_hash", None)
    if recorded != sha256_json(body):
        errors.append("C1_C2_DEPENDENCY_RESOLUTION_HASH_MISMATCH")
    if value != build_dependency_resolution(root):
        errors.append("C1_C2_DEPENDENCY_RESOLUTION_NOT_REPRODUCIBLE")
    if value.get("status") != "PASS":
        errors.append("C1_C2_DEPENDENCY_RESOLUTION_NOT_PASS")
    return sorted(set(errors))


def check_or_write_dependency_resolution(root: Path, *, check: bool) -> dict[str, Any]:
    value = build_dependency_resolution(root)
    errors = validate_dependency_resolution(root, value)
    errors.extend(check_or_write_json(root / RESOLUTION_PATH, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "resolution_hash": value["resolution_hash"],
        "corrected_graph_hash": value["corrected_graph"]["graph_hash"],
        "finding_id": value["finding_id"],
    }


__all__ = [
    "RESOLUTION_PATH",
    "build_dependency_resolution",
    "check_or_write_dependency_resolution",
    "validate_audit_replay_order",
    "validate_dependency_resolution",
]
