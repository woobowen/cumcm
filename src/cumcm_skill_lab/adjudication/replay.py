"""Offline decision replay and identity/order stability transformations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .decision_engine import decide
from .models import sha256_json


def replay_hash(frozen_inputs: dict[str, Any]) -> str:
    return sha256_json(frozen_inputs)


def replay(frozen_inputs: dict[str, Any]) -> dict:
    outcome = decide(frozen_inputs["facts"])
    return {**outcome, "replay_hash": replay_hash(frozen_inputs)}


def permute_evidence(value: Any) -> Any:
    transformed = deepcopy(value)
    if isinstance(transformed, dict):
        return {
            key: permute_evidence(transformed[key]) for key in sorted(transformed, reverse=True)
        }
    if isinstance(transformed, list):
        return [permute_evidence(item) for item in reversed(transformed)]
    return transformed


def order_stable(frozen_inputs: dict[str, Any]) -> bool:
    return replay(frozen_inputs)["decision"] == replay(permute_evidence(frozen_inputs))["decision"]


def identity_swap(frozen_inputs: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    text = __import__("json").dumps(frozen_inputs, ensure_ascii=False)
    placeholders = {key: f"__IDENTITY_{index}__" for index, key in enumerate(mapping)}
    for key, placeholder in placeholders.items():
        text = text.replace(key, placeholder)
    for key, placeholder in placeholders.items():
        text = text.replace(placeholder, mapping[key])
    return __import__("json").loads(text)


def identity_stable(frozen_inputs: dict[str, Any], mapping: dict[str, str]) -> bool:
    return (
        replay(frozen_inputs)["decision"]
        == replay(identity_swap(frozen_inputs, mapping))["decision"]
    )
