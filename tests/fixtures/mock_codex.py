#!/usr/bin/env python3
"""Offline test double for the small `codex exec` surface used by the harness."""

import json
import os
import sys
import time
from pathlib import Path


def _value(flag: str) -> str:
    return sys.argv[sys.argv.index(flag) + 1]


def main() -> int:
    workspace = Path(_value("--cd"))
    output = Path(_value("--output-last-message"))
    mode = os.environ.get("MOCK_CODEX_MODE", "normal")
    if mode == "timeout":
        time.sleep(2)
    if mode == "auth":
        print("Authentication failed", file=sys.stderr)
        return 1
    if mode == "quota":
        print("quota exceeded", file=sys.stderr)
        return 1
    if mode == "nonzero":
        print("synthetic nonzero exit", file=sys.stderr)
        return 7
    metadata = json.loads((workspace / "runtime_metadata.json").read_text(encoding="utf-8"))
    observation = {
        **metadata,
        "completion_status": "COMPLETED",
        "requirements": ["trace all required outputs and dependencies"],
        "assumptions": ["synthetic local inputs only"],
        "reality_constraints": ["preserve raw input"],
        "data_findings": [],
        "baseline": {
            "description": "simple feasible baseline",
            "result": None,
            "evidence": ["local case"],
        },
        "candidate_models": ["candidate A"],
        "selected_model": "candidate A",
        "formalization": {
            "variables": [],
            "parameters": [],
            "objective": "case-specific objective",
            "constraints": [],
            "units": [],
            "notes": [],
        },
        "code_artifacts": [],
        "commands_executed": [],
        "tests_claimed": [],
        "tests_verified": [],
        "experiment_design": ["fixed synthetic evaluation"],
        "validation": ["schema validation"],
        "falsification_tests": ["counterexample check"],
        "robustness_tests": ["boundary check"],
        "sources_used": [],
        "claims": [
            "correlation is not causation",
            f"env-secret-visible={bool(os.environ.get('EVAL_FAKE_TOKEN'))}",
        ],
        "uncertainties": ["mock output has no scientific authority"],
        "human_gates": ["base selection remains pending"],
        "files_created": [],
        "prohibited_actions_attempted": [],
        "self_reported_limitations": ["MOCK execution"],
    }
    if mode == "invalid_schema":
        observation["unexpected"] = True
    if mode == "missing_file":
        observation["code_artifacts"] = ["does-not-exist.py"]
    if mode == "secret_output":
        observation["claims"] = ["s" + "k-" + "abcdefghijklmnopqrstuvwxyz123456"]
    if mode == "private_path":
        observation["files_created"] = ["/" + "home/private/result.txt"]
    if mode == "write_input":
        input_path = next(path for path in (workspace / "case").rglob("*") if path.is_file())
        input_path.write_text("mutated\n", encoding="utf-8")
    if mode == "network_trace":
        print(json.dumps({"type": "item.completed", "command": ["curl", "https://invalid"]}))
    if mode == "mcp_trace":
        print(json.dumps({"type": "mcp_tool_call"}))
    if mode == "reported_prohibition":
        observation["prohibited_actions_attempted"] = ["network"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(observation), encoding="utf-8")
    print(json.dumps({"type": "thread.started", "thread_id": "mock"}))
    print(
        json.dumps(
            {
                "type": "item.completed",
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
