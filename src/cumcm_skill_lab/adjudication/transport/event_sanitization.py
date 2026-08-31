"""Hash raw events and retain only non-content event summaries."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..models import sha256_bytes


def hash_identifier(identifier: str | None) -> str | None:
    return sha256_bytes(identifier.encode()) if identifier else None


def parse_jsonl_bytes(raw: bytes) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            events.append({"type": "MALFORMED_JSON_EVENT"})
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def summarize_event_records(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    session_id: str | None = None
    turn_id: str | None = None
    token_usage: dict[str, int] = {}
    terminal_event: str | None = None
    for event in events:
        event_type = str(event.get("type") or event.get("method") or "UNKNOWN")
        counts[event_type] += 1
        if event_type == "thread.started":
            session_id = _string_or_none(event.get("thread_id"))
        elif event_type == "thread/started":
            session_id = _nested_string(event, "params", "thread", "id") or _nested_string(
                event, "params", "threadId"
            )
        if event_type in {"turn/started", "turn/completed"}:
            turn_id = _nested_string(event, "params", "turn", "id") or _nested_string(
                event, "params", "turnId"
            )
        if event_type == "turn.completed" and isinstance(event.get("usage"), dict):
            token_usage = _integer_mapping(event["usage"])
            terminal_event = event_type
        elif event_type == "thread/tokenUsage/updated":
            usage = event.get("params", {}).get("tokenUsage", {})
            if isinstance(usage, dict):
                total = usage.get("total", usage)
                if isinstance(total, dict):
                    token_usage = _integer_mapping(total)
        if event_type in {"turn.failed", "turn/completed"}:
            terminal_event = event_type
    return {
        "event_counts": dict(sorted(counts.items())),
        "session_id": session_id,
        "turn_id": turn_id,
        "session_id_hash": hash_identifier(session_id),
        "turn_id_hash": hash_identifier(turn_id),
        "token_usage": token_usage,
        "terminal_event": terminal_event,
        "message_content_retained": False,
        "reasoning_content_retained": False,
    }


def summarize_events(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "raw_event_hash": None,
            "event_counts": {},
            "session_id": None,
            "turn_id": None,
            "session_id_hash": None,
            "turn_id_hash": None,
            "token_usage": {},
            "terminal_event": None,
            "message_content_retained": False,
            "reasoning_content_retained": False,
        }
    raw = path.read_bytes()
    summary = summarize_event_records(parse_jsonl_bytes(raw))
    summary["raw_event_hash"] = sha256_bytes(raw)
    return summary


def sanitized_observable(events: Iterable[dict[str, Any]]) -> str:
    """Return only error category text for in-memory classification, never for tracking."""
    fragments: list[str] = []
    for event in events:
        event_type = str(event.get("type") or event.get("method") or "")
        if event_type not in {"error", "turn.failed"}:
            continue
        message = event.get("message")
        if not isinstance(message, str) and isinstance(event.get("error"), dict):
            message = event["error"].get("message")
        if isinstance(message, str):
            fragments.append(message)
    return "\n".join(fragments)


def _nested_string(value: dict[str, Any], *keys: str) -> str | None:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return _string_or_none(current)


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _integer_mapping(value: dict[str, Any]) -> dict[str, int]:
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(item, int) and not isinstance(item, bool)
    }
