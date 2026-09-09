"""Run a validation command and retain its actual subject, times, output and exit code."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--junit", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv or not re.fullmatch(r"[a-z0-9_-]+", args.name):
        raise SystemExit("A command and safe unique receipt name are required")
    spec = importlib.util.spec_from_file_location(
        "rc9_receipt_subject", ROOT / "scripts/check_phase004c6_rc9_release.py"
    )
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    protocol = q.read(ROOT / q.PROTOCOL)
    mapping = q.subject_mapping(ROOT, args.subject, protocol)
    changed = [
        p
        for p, digest in mapping.items()
        if not (ROOT / p).is_file() or q.digest((ROOT / p).read_bytes()) != digest
    ]
    if changed:
        raise SystemExit("Subject has current implementation drift: " + ",".join(changed))
    dest = ROOT / q.BASE / "receipts"
    dest.mkdir(parents=True, exist_ok=True)
    receipt_path = dest / (args.name + ".json")
    log_path = dest / (args.name + ".log")
    if receipt_path.exists() or log_path.exists():
        raise SystemExit("Receipt already exists; use a new name and preserve the failed attempt")
    head = q.git(ROOT, "rev-parse", "HEAD").decode().strip()
    before = datetime.now(UTC).isoformat()
    clock = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    elapsed = time.monotonic() - clock
    after = datetime.now(UTC).isoformat()
    raw = ROOT / ".cache/pr12-rc9/command-logs" / args.name
    raw.mkdir(parents=True, exist_ok=False)
    (raw / "stdout").write_bytes(result.stdout)
    (raw / "stderr").write_bytes(result.stderr)
    stdout, stderr = result.stdout.decode(errors="replace"), result.stderr.decode(errors="replace")
    text = (
        ("STDOUT\n" + stdout + "\nSTDERR\n" + stderr)
        .replace(str(ROOT), "<REPO_ROOT>")
        .replace(str(Path.home()), "<USER_HOME>")
    )
    log_path.write_text(text)

    def binding(path):
        return {"path": path.relative_to(ROOT).as_posix(), "sha256": q.digest(path.read_bytes())}

    command = {
        "argv": argv,
        "executed_head": head,
        "started_at": before,
        "ended_at": after,
        "elapsed_seconds": elapsed,
        "exit_code": result.returncode,
        "log": binding(log_path),
        "raw_stdout_sha256": q.digest(result.stdout),
        "raw_stderr_sha256": q.digest(result.stderr),
        "implementation_mapping_sha256": q.canonical(mapping),
    }
    receipt = {
        "schema_version": "phase-004c6-command-receipt/v1",
        "kind": args.kind,
        "subject_commit": args.subject,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "commands": [command],
        "evidence": [binding(log_path)],
        "publication": "Private root normalization only; original streams retained ignored.",
    }
    summary = re.findall(
        r"(?:\d+ (?:passed|failed|skipped|xfailed|xpassed|deselected)(?:, )?)+ in [0-9.]+s", stdout
    )
    if summary:
        counts = {
            key: int(value)
            for value, key in re.findall(
                r"(\d+) (passed|failed|skipped|xfailed|xpassed|deselected)", summary[-1]
            )
        }
        for key in ("passed", "failed", "skipped"):
            receipt["pytest_" + key] = counts.get(key, 0)
        receipt["pytest_summary"] = summary[-1]
    if args.junit and args.junit.is_file():
        target = dest / (args.name + ".xml")
        target.write_text(
            args.junit.read_text()
            .replace(str(ROOT), "<REPO_ROOT>")
            .replace(str(Path.home()), "<USER_HOME>")
        )
        receipt["junit"] = binding(target)
        receipt["evidence"].append(binding(target))
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "receipt": receipt_path.relative_to(ROOT).as_posix(),
                "status": receipt["status"],
                "elapsed_seconds": elapsed,
                "executed_head": head,
                "pytest_summary": receipt.get("pytest_summary"),
            },
            sort_keys=True,
        )
    )
    if result.returncode:
        print(text[-12000:])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
