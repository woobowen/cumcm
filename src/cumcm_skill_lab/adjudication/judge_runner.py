"""Run a blind adjudication role in a disposable, no-remote Git workspace."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .models import canonical_json, read_json, sha256_bytes, sha256_json, write_json

ROLES = (
    "CORRECTNESS_JUDGE",
    "SCIENTIFIC_VALIDITY_JUDGE",
    "ENGINEERING_REPRODUCIBILITY_JUDGE",
)
REAL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string"},
        "recommendation": {
            "type": "string",
            "enum": ["ACCEPT", "REJECT", "RETEST", "INSUFFICIENT", "ABSTAIN"],
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["BLOCKER", "ERROR", "WARNING", "INFO"]},
                    "target": {"type": "string"},
                    "statement": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                    "testability": {"type": "string", "enum": ["TESTABLE", "NON_TESTABLE_CLAIM"]},
                },
                "required": ["severity", "target", "statement", "evidence_refs", "testability"],
                "additionalProperties": False,
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["role", "recommendation", "findings", "confidence", "uncertainties"],
    "additionalProperties": False,
}
IDENTITY_MARKERS = ("YUSHUI", "HANDSOMEZR", "NO_PROJECT_MODELING_SKILL", "woobowen")


def assert_blind(bundle: dict) -> None:
    text = canonical_json(bundle).lower()
    leaked = [marker for marker in IDENTITY_MARKERS if marker.lower() in text]
    if leaked:
        raise ValueError(f"IDENTITY_LEAKED:{','.join(leaked)}")


def build_anonymous_bundle(root: Path) -> dict:
    paths = {
        "freeze": "evals/results/phase-002a/evidence_freeze_manifest.json",
        "eligibility": "evals/results/phase-002a/eligibility/classification.json",
        "coverage": "evals/results/phase-002a/structured_coverage/coverage.json",
        "oracles": "evals/results/phase-002a/oracle_correctness/oracles.json",
        "process": "evals/results/phase-002a/process_evidence/process.json",
        "recovery": "evals/results/phase-002a/recovery_gap_evidence/recovery.json",
    }
    bundle = {
        "schema_version": "1.0.0",
        "bundle_id": "ANON-EVIDENCE-PHASE-002A",
        "candidate_labels": ["ARM-A", "ARM-B", "ARM-C"],
        "identity_revealed": False,
        "evidence": {key: read_json(root / value) for key, value in paths.items()},
    }
    bundle["bundle_hash"] = sha256_json(bundle)
    assert_blind(bundle)
    return bundle


def role_prompt(role: str, *, transformed: bool = False) -> str:
    scopes = {
        "CORRECTNESS_JUDGE": "题意、数学、数据泄漏、deterministic oracle、baseline 与 E1/E2 证据",
        "SCIENTIFIC_VALIDITY_JUDGE": "假设、现实约束、实验设计、稳健性、负对照、不确定性和过度结论",
        "ENGINEERING_REPRODUCIBILITY_JUDGE": "Run、哈希、命令、环境、seed、输出、STALE、失败和重放",
    }
    transform_note = "证据项顺序已变换；不得依赖顺序。" if transformed else "这是首轮独立审查。"
    return (
        f"你是 {role}。只审查：{scopes[role]}。{transform_note}"
        "读取当前临时仓库的 evidence_bundle.json 与 policy.json。候选身份已隐藏；不得猜测身份。"
        "你看不到其他 Judge 输出，不得投票或服从社会证明。"
        "每个结论必须引用 bundle 内 evidence_refs。"
        "只输出符合 output.schema.json 的 JSON。"
    )


def _safe_env() -> dict[str, str]:
    allowed = {"PATH", "LANG", "LC_ALL", "TERM", "HOME", "CODEX_HOME"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    for key in list(env):
        upper = key.upper()
        if "TOKEN" in upper or "KEY" in upper or upper.startswith("GITHUB") or upper == "GH_TOKEN":
            env.pop(key, None)
    return env


def run_role(
    root: Path,
    *,
    role: str,
    bundle: dict,
    policy: dict,
    transformed: bool = False,
    timeout: int = 1200,
) -> tuple[dict, dict]:
    if role not in ROLES:
        raise ValueError(f"UNSUPPORTED_ROLE:{role}")
    assert_blind(bundle)
    workspace = Path(tempfile.mkdtemp(prefix="cumcm-adjudication-", dir="/tmp"))
    raw_dir = root / ".cache/upstream-eval/phase-002a/raw-agent-events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    attempt_id = f"{role.lower()}-{'swap' if transformed else 'first'}"
    raw_trace = raw_dir / f"{attempt_id}.jsonl"
    try:
        write_json(workspace / "evidence_bundle.json", bundle)
        write_json(workspace / "policy.json", policy)
        write_json(workspace / "output.schema.json", REAL_OUTPUT_SCHEMA)
        (workspace / ".harness").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True, env=_safe_env())
        subprocess.run(
            ["git", "add", "evidence_bundle.json", "policy.json", "output.schema.json"],
            cwd=workspace,
            check=True,
            env=_safe_env(),
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=adjudication-harness",
                "-c",
                "user.email=none@invalid",
                "commit",
                "-qm",
                "frozen anonymous evidence",
            ],
            cwd=workspace,
            check=True,
            env=_safe_env(),
        )
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--strict-config",
            "--model",
            "gpt-5.4",
            "--sandbox",
            "workspace-write",
            "--config",
            'model_reasoning_effort="medium"',
            "--json",
            "--output-schema",
            str(workspace / "output.schema.json"),
            "--output-last-message",
            str(workspace / ".harness/last-message.json"),
            "--cd",
            str(workspace),
            role_prompt(role, transformed=transformed),
        ]
        started = time.monotonic()
        with raw_trace.open("wb") as stdout:
            result = subprocess.run(
                command,
                cwd=workspace,
                env=_safe_env(),
                stdout=stdout,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        duration = round(time.monotonic() - started, 6)
        last_message = workspace / ".harness/last-message.json"
        if result.returncode != 0 or not last_message.is_file():
            raise RuntimeError(
                f"AGENT_RUN_FAILED:{role}:exit={result.returncode}:"
                f"{result.stderr.decode(errors='replace')[-500:]}"
            )
        output = read_json(last_message)
        if output.get("role") != role:
            raise RuntimeError(f"ROLE_OUTPUT_MISMATCH:{role}")
        assert_blind(output)
        tracked = {
            "judge_id": f"JUDGE-{attempt_id.upper()}",
            "role": role,
            "bundle_id": bundle["bundle_id"],
            "policy_hash": policy["policy_hash"],
            "identity_blind": True,
            "other_judges_visible": False,
            "findings": [],
            "recommendation": output["recommendation"],
            "evidence_refs": sorted(
                {ref for finding in output["findings"] for ref in finding["evidence_refs"]}
            )
            or ["bundle:" + bundle["bundle_hash"]],
            "finding_details": output["findings"],
            "confidence": output["confidence"],
            "uncertainties": output["uncertainties"],
        }
        for index, finding in enumerate(tracked["finding_details"], start=1):
            finding["finding_id"] = f"FINDING-{attempt_id.upper()}-{index:02d}"
            finding["role"] = role
            finding["status"] = "OPEN"
            tracked["findings"].append(finding["finding_id"])
        ledger = {
            "attempt_id": attempt_id,
            "execution_kind": "REAL",
            "role": role,
            "model": "gpt-5.4",
            "reasoning_setting": "medium",
            "sandbox": "workspace-write",
            "network_isolation_level": "NETWORK_POLICY_PROHIBITED_TRACE_AUDITED",
            "workspace_remote_count": 0,
            "identity_blind": True,
            "other_judges_visible": False,
            "exit_code": result.returncode,
            "duration_seconds": duration,
            "prompt_hash": sha256_bytes(role_prompt(role, transformed=transformed).encode()),
            "schema_hash": sha256_json(REAL_OUTPUT_SCHEMA),
            "bundle_hash": bundle["bundle_hash"],
            "output_hash": sha256_json(tracked),
            "raw_trace_tracked": False,
            "stderr_risk_summary_hash": sha256_bytes(result.stderr),
            "token_usage": "RECORDED_IN_IGNORED_RAW_TRACE",
            "result": "COMPLETED",
            "failure": None,
            "blocker": None,
        }
        return tracked, ledger
    finally:
        shutil.rmtree(workspace)


def run_structured_role(
    root: Path,
    *,
    role: str,
    prompt: str,
    inputs: dict,
    output_schema: dict,
    attempt_id: str,
    timeout: int = 1200,
) -> tuple[dict, dict]:
    """Run non-blind-stage roles with the same disposable-workspace controls."""
    workspace = Path(tempfile.mkdtemp(prefix="cumcm-adjudication-", dir="/tmp"))
    raw_dir = root / ".cache/upstream-eval/phase-002a/raw-agent-events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_trace = raw_dir / f"{attempt_id}.jsonl"
    try:
        write_json(workspace / "inputs.json", inputs)
        write_json(workspace / "output.schema.json", output_schema)
        (workspace / ".harness").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True, env=_safe_env())
        subprocess.run(
            ["git", "add", "inputs.json", "output.schema.json"],
            cwd=workspace,
            check=True,
            env=_safe_env(),
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=adjudication-harness",
                "-c",
                "user.email=none@invalid",
                "commit",
                "-qm",
                "frozen adjudication inputs",
            ],
            cwd=workspace,
            check=True,
            env=_safe_env(),
        )
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--strict-config",
            "--model",
            "gpt-5.4",
            "--sandbox",
            "workspace-write",
            "--config",
            'model_reasoning_effort="medium"',
            "--json",
            "--output-schema",
            str(workspace / "output.schema.json"),
            "--output-last-message",
            str(workspace / ".harness/last-message.json"),
            "--cd",
            str(workspace),
            prompt,
        ]
        started = time.monotonic()
        with raw_trace.open("wb") as stdout:
            result = subprocess.run(
                command,
                cwd=workspace,
                env=_safe_env(),
                stdout=stdout,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        duration = round(time.monotonic() - started, 6)
        last_message = workspace / ".harness/last-message.json"
        if result.returncode != 0 or not last_message.is_file():
            raise RuntimeError(
                f"AGENT_RUN_FAILED:{role}:exit={result.returncode}:"
                f"{result.stderr.decode(errors='replace')[-500:]}"
            )
        output = read_json(last_message)
        ledger = {
            "attempt_id": attempt_id,
            "execution_kind": "REAL",
            "role": role,
            "model": "gpt-5.4",
            "reasoning_setting": "medium",
            "sandbox": "workspace-write",
            "network_isolation_level": "NETWORK_POLICY_PROHIBITED_TRACE_AUDITED",
            "workspace_remote_count": 0,
            "exit_code": result.returncode,
            "duration_seconds": duration,
            "prompt_hash": sha256_bytes(prompt.encode()),
            "schema_hash": sha256_json(output_schema),
            "input_hash": sha256_json(inputs),
            "output_hash": sha256_json(output),
            "raw_trace_tracked": False,
            "stderr_risk_summary_hash": sha256_bytes(result.stderr),
            "token_usage": "RECORDED_IN_IGNORED_RAW_TRACE",
            "result": "COMPLETED",
            "failure": None,
            "blocker": None,
        }
        return output, ledger
    finally:
        shutil.rmtree(workspace)
