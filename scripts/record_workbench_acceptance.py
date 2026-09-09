"""Main-writer tools for observed construction commands and original-case evidence export."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals/results/modular-workbench-001"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def binding(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path.read_bytes())}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def record(path):
    data = path.read_bytes()
    text = data.decode()
    if re.search(r"/(?:home|Users)/[^/\s]+/|(?i:password|api_key|authorization)\s*[:=]", text):
        raise ValueError("RECORD_REQUIRES_SEPARATE_REDACTION_VIEW")
    return {"raw_sha256": sha(data), "raw_utf8": text, "content": json.loads(text)}


def run(name, argv):
    if not argv or not re.fullmatch(r"[a-z0-9_-]+", name):
        raise ValueError("EXPLICIT_COMMAND_AND_UNIQUE_NAME_REQUIRED")
    if any((BASE / "commands" / (name + suffix)).exists() for suffix in (".log", ".json")):
        raise ValueError("RECORDED_COMMAND_NAME_ALREADY_USED_NO_EXECUTION")
    start = datetime.now(UTC).isoformat()
    tick = time.monotonic()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    process = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    elapsed = time.monotonic() - tick
    end = datetime.now(UTC).isoformat()
    raw = process.stdout + process.stderr
    scratch = ROOT / ".cache/modular-workbench-001/acceptance-commands" / name
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "raw.log").write_bytes(raw)
    public = re.sub(rb"/(?:home|Users)/[^/\s]+", b"<PRIVATE_USER_ROOT>", raw)
    # Temporary test paths are useful only as local recovery references.
    public = re.sub(rb"/tmp/pytest-of-[^/\s]+/[^\s'\"]+", b"<PYTEST_TEMP_PATH>", public)
    public = re.sub(rb"[ \t]+(?=\r?$)", b"", public, flags=re.MULTILINE)
    log = BASE / "commands" / (name + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("xb") as handle:
        handle.write(public)
    public_args = [re.sub(r"/(?:home|Users)/[^/\s]+", "<PRIVATE_USER_ROOT>", a) for a in argv]
    value = {
        "argv": public_args,
        "started_at": start,
        "ended_at": end,
        "elapsed_seconds": elapsed,
        "exit_code": process.returncode,
        "executed_head": head,
        "log": binding(log),
        "raw_log_sha256": sha(raw),
        "log_derivation": "PRIVATE_USER_AND_PYTEST_PATH_REDACTION_AND_TRAILING_WHITESPACE_REMOVAL",
    }
    write(BASE / "commands" / (name + ".json"), value)
    print(json.dumps(value, ensure_ascii=False))
    return process.returncode


def original(root, name):
    state = json.loads((root / "case_state.json").read_text())
    if not state["case_id"].startswith("ORIGINAL-WATER-"):
        raise ValueError("ONLY_PROJECT_ORIGINAL_WATER_EXPORT_AUTHORIZED")
    paths = {
        "case_state": "case_state.json",
        "final_ledger": "evidence/scientific_final_ledger.json",
        "handoff": "handoff/modeling_to_paper.json",
        "input": "data/raw/input.json",
        "experiment_plan": "experiments/experiment_plan.json",
        "problem_requirements": "problem/problem_requirements.json",
    }
    kinds = {
        "capture": "execution_capture.json",
        "output": "output.json",
        "manifest": "manifest.json",
        "check": "scientific_check.json",
        "check_capture": "scientific_check_capture.json",
        "final_check": "final_check.json",
    }
    for run_dir in sorted((root / "runs").iterdir()):
        for key, filename in kinds.items():
            if (run_dir / filename).is_file():
                paths[key + ":" + run_dir.name] = (run_dir / filename).relative_to(root).as_posix()
    packet = {
        "derivation": "EXACT_UTF8_JSON_NO_REDACTION",
        "source_case_id": state["case_id"],
        "records": {key: record(root / path) for key, path in paths.items()},
    }
    destination = BASE / "original" / name
    write(destination / "records.json", packet)
    for request in sorted((root / "evidence/module_requests").iterdir()):
        if not (request / "completion.json").exists():
            continue
        done = json.loads((request / "completion.json").read_text())
        write(destination / "modules" / (done["module"] + ".json"), done)
        write(
            destination / "modules" / (done["module"] + "-records.json"),
            {
                "derivation": "EXACT_UTF8_JSON_NO_REDACTION",
                "records": {
                    "request": record(request / "request.json"),
                    "completion": record(request / "completion.json"),
                    "work_report": record(root / done["report_path"]),
                    "recovery_proof": record(
                        root / "evidence/module_resume" / (done["module"] + ".json")
                    ),
                },
            },
        )
    print(json.dumps(binding(destination / "records.json")))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build-evidence", action="store_true", required=True)
    subs = p.add_subparsers(dest="command", required=True)
    cmd = subs.add_parser("run")
    cmd.add_argument("--name", required=True)
    cmd.add_argument("argv", nargs=argparse.REMAINDER)
    cmd = subs.add_parser("original")
    cmd.add_argument("--case-root", type=Path, required=True)
    cmd.add_argument("--name", choices=["prediction", "optimization", "mixed"], required=True)
    args = p.parse_args()
    if args.command == "run":
        return run(args.name, args.argv[1:] if args.argv[:1] == ["--"] else args.argv)
    original(args.case_root.resolve(), args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
