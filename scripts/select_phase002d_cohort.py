#!/usr/bin/env python3
"""Probe the local Codex model catalog or verify the frozen Phase 002D cohort."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from cumcm_skill_lab.adjudication.models import file_sha256, write_json
from cumcm_skill_lab.adjudication.transport.app_server_client import AppServerClient
from cumcm_skill_lab.expansion.cohort import (
    MODEL_AVAILABILITY_PATH,
    check_or_write_cohort,
    record_availability,
)


def _normalize_models(result: object) -> list[dict]:
    if not isinstance(result, dict):
        raise RuntimeError("MODEL_LIST_NOT_OBJECT")
    values = result.get("data", result.get("models", []))
    if not isinstance(values, list):
        raise RuntimeError("MODEL_LIST_DATA_NOT_ARRAY")
    models = []
    for item in values:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id", item.get("model"))
        efforts = item.get(
            "supportedReasoningEfforts",
            item.get("supported_reasoning_efforts", item.get("reasoningEfforts", [])),
        )
        if isinstance(model_id, str) and model_id:
            models.append(
                {
                    "id": model_id,
                    "default": bool(item.get("isDefault", item.get("is_default", False))),
                    "reasoning": efforts if isinstance(efforts, list) else [],
                }
            )
    return sorted(models, key=lambda item: item["id"])


def _probe(root: Path) -> None:
    cache = root / ".cache/phase002d"
    raw_path = cache / "model-catalog-m2.raw.jsonl"
    stderr_path = cache / "model-catalog-m2.stderr"
    client = AppServerClient(
        raw_event_path=raw_path,
        stderr_path=stderr_path,
        timeout_seconds=30,
    )
    try:
        client.start()
        result = client.request("model/list", {"limit": 100})
    finally:
        client.close()
    version = subprocess.run(
        ["codex", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    availability = record_availability(
        checked_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        codex_cli_version=version.removeprefix("codex-cli "),
        models=_normalize_models(result),
        raw_catalog_hash=file_sha256(raw_path),
    )
    write_json(root / MODEL_AVAILABILITY_PATH, availability)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.check and args.probe:
        parser.error("--check and --probe are mutually exclusive")
    root = Path.cwd()
    if not args.check:
        _probe(root)
    result = check_or_write_cohort(root, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
