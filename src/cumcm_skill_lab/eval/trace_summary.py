"""Reduce Codex JSONL to non-sensitive observable counts and command summaries."""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SECRET_ASSIGNMENT = re.compile(r"(?i)(token|password|api[_-]?key|cookie|authorization)=\S+")
SECRET_LITERAL = re.compile(
    r"(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\bsk-[A-Za-z0-9_-]{20,}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|"
    r"(?i:\bBearer\s+[A-Za-z0-9._~-]{16,}))"
)


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def sanitize_error(text: str, root: Path | None = None) -> str:
    cleaned = SECRET_ASSIGNMENT.sub(r"\1=<REDACTED>", text)
    cleaned = SECRET_LITERAL.sub("<REDACTED_SECRET>", cleaned)
    if root is not None:
        cleaned = cleaned.replace(str(root), "<REPO_ROOT>")
    cleaned = re.sub(r"/(?:home|Users)/[^/\s]+/", "/<HOME>/", cleaned)
    return cleaned[:2000]


def _command_summary(command: Any) -> str | None:
    if isinstance(command, list) and command:
        executable = Path(str(command[0])).name
        return f"{executable} argc={len(command)}"
    if isinstance(command, str) and command.strip():
        first = command.strip().split()[0]
        return f"{Path(first).name} shell_text_sha_redacted"
    return None


def summarize_jsonl(text: str) -> dict:
    counts: Counter[str] = Counter()
    commands: set[str] = set()
    usage: Counter[str] = Counter()
    invalid_lines = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            continue
        event_type = str(event.get("type") or event.get("event", {}).get("type") or "unknown")
        counts[event_type] += 1
        for node in _walk(event):
            if "command" in node:
                summary = _command_summary(node["command"])
                if summary:
                    commands.add(summary)
            for key in ("input_tokens", "output_tokens", "reasoning_tokens", "total_tokens"):
                value = node.get(key)
                if isinstance(value, int):
                    usage[key] = max(usage[key], value)
    if invalid_lines:
        counts["invalid_jsonl_line"] = invalid_lines
    return {
        "event_summary": dict(sorted(counts.items())),
        "observable_commands": sorted(commands),
        "token_usage": dict(sorted(usage.items())) or None,
    }
