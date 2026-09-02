"""Validate the frozen single-truth interaction specification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import read_json, read_yaml, sha256_json

from .models import COMPONENT_IDS

CONTRACT = Path("contracts/component_interaction.schema.json")
SPECIFICATION = Path("specifications/interactions/component_interaction_contract.yaml")


def _has_cycle(edges: list[dict[str, Any]]) -> bool:
    graph: dict[str, set[str]] = {}
    for edge in edges:
        graph.setdefault(edge["from"], set()).add(edge["to"])
        graph.setdefault(edge["to"], set())
    active: set[str] = set()
    complete: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in complete:
            return False
        active.add(node)
        if any(visit(next_node) for next_node in graph[node]):
            return True
        active.remove(node)
        complete.add(node)
        return False

    return any(visit(node) for node in graph)


def validate_interaction_value(schema: dict[str, Any], value: dict[str, Any]) -> list[str]:
    errors = [
        f"INTERACTION_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(schema).iter_errors(value)
    ]
    interfaces = value.get("component_interfaces", [])
    component_ids = [item.get("component_id") for item in interfaces]
    if set(component_ids) != set(COMPONENT_IDS) or len(component_ids) != len(set(component_ids)):
        errors.append("INTERACTION_COMPONENT_SET_INVALID")
    if any(item.get("direct_state_advance") is not False for item in interfaces):
        errors.append("INTERACTION_DIRECT_STATE_ADVANCE")
    if value.get("state_truth") != "state/project_state.json":
        errors.append("INTERACTION_SECOND_STATE_TRUTH")
    if value.get("formal_skill_count") != 1:
        errors.append("INTERACTION_FORMAL_SKILL_COUNT")
    if _has_cycle(value.get("data_dependencies", [])):
        errors.append("INTERACTION_DEPENDENCY_CYCLE")
    body = dict(value)
    recorded = body.pop("contract_hash", None)
    if sha256_json(body) != recorded:
        errors.append("INTERACTION_HASH_MISMATCH")
    return sorted(set(errors))


def validate_component_interactions(root: Path) -> dict[str, Any]:
    schema = read_json(root / CONTRACT)
    value = read_yaml(root / SPECIFICATION)
    errors = validate_interaction_value(schema, value)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "contract_id": value.get("contract_id"),
        "component_count": len(value.get("component_interfaces", [])),
        "state_truth": value.get("state_truth"),
        "decision": value.get("decision"),
    }


__all__ = [
    "CONTRACT",
    "SPECIFICATION",
    "validate_component_interactions",
    "validate_interaction_value",
]
