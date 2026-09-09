"""One bounded engineering adjudication, separate from historical research qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "evals/results/modular-workbench-001"
QUAL = BASE + "/qualification"
SNAPSHOT = QUAL + "/candidate_snapshot.json"
DECISION = QUAL + "/decision.json"
AUDIT = QUAL + "/decision_audit.json"
PHASE = "PHASE-SKILL-MODULAR-WORKBENCH-004C7"
HISTORY = "604c7facda586cecb6785c44949f0cd1217cd297"
RECEIPTS = {
    "public_paths",
    "boundary_tests",
    "review_roundtrip",
    "context_handoff",
    "native_review",
    "independent_recalculation",
    "known_interface",
    "full_ci",
    "strict_checks",
}
PREFIXES = [
    ".agents/skills/cumcm-modeling-evidence/",
    "contracts/",
    "rules/",
    "tests/",
    "docs/modular_workbench/",
    BASE + "/known_code/",
]
EXACT = {
    "VERSION",
    "pyproject.toml",
    "scripts/ci.sh",
    "scripts/finalize_fresh_c_validation.py",
    "scripts/check_modular_workbench.py",
    "scripts/exercise_modular_workbench.py",
    "scripts/prepare_workbench_known.py",
    "scripts/render_workbench_docs.py",
    "src/cumcm_skill_lab/training_registry.py",
    "src/cumcm_skill_lab/historical_compat.py",
    "src/cumcm_skill_lab/authorization_c1/schema_resolution.py",
    BASE + "/original_analysis.md",
    QUAL + "/protocol.json",
}


def read(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("WB_ACCEPTANCE_UNSAFE_PATH")
    value = json.loads((root / path).read_text())
    if not isinstance(value, dict):
        raise ValueError("WB_ACCEPTANCE_OBJECT_REQUIRED")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return digest(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


@lru_cache(maxsize=32)
def mapping(root, subject):
    if subject != "HEAD" and not re.fullmatch(r"[0-9a-f]{40}", subject):
        raise ValueError("WB_SUBJECT_COMMIT_INVALID")
    paths = git(root, "ls-tree", "-r", "--name-only", subject).decode().splitlines()
    return {
        p: digest(git(root, "show", subject + ":" + p))
        for p in paths
        if p in EXACT or any(p.startswith(prefix) for prefix in PREFIXES)
    }


def bound(root, binding):
    relative = binding["path"]
    path = Path(relative)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not relative.startswith(BASE + "/")
        or relative != path.as_posix()
        or any((root / path).parents[i].is_symlink() for i in range(len(path.parts) - 1))
        or (root / path).is_symlink()
    ):
        raise ValueError("WB_ACCEPTANCE_EVIDENCE_PATH_INVALID")
    data = (root / path).read_bytes()
    if digest(data) != binding["sha256"]:
        raise ValueError("WB_ACCEPTANCE_EVIDENCE_HASH_MISMATCH:" + relative)
    return data


def validate_family_evidence(root, family):
    """Read the actual captured-record projection, not just summary labels."""
    packet = json.loads(bound(root, family["record_packet"]))
    if packet.get("derivation") != "EXACT_JSON_WITH_PRIVATE_ARGV_PATH_REDACTION":
        return ["WB_PUBLIC_PROJECTION_UNDECLARED"]
    records = packet["records"]
    if any(not re.fullmatch(r"[a-f0-9]{64}", r.get("raw_sha256", "")) for r in records.values()):
        return ["WB_RAW_RECORD_IDENTITY_MISSING"]
    state = records["case_state"]["content"]
    ledger = records["final_ledger"]["content"]
    handoff = records["handoff"]["content"]
    captures = [r["content"] for key, r in records.items() if key.startswith("capture:")]
    errors = []
    if (
        state.get("state") != family["native_state"]
        or state.get("skill_version") != "0.2.0-competition-rc10"
        or len(captures) != family["actual_model_starts"]
        or any(c.get("outcome") != "SUCCESS" for c in captures)
        or len({c.get("run_id") for c in captures}) != len(captures)
    ):
        errors.append("WB_CAPTURED_FAMILY_STATE_MISMATCH")
    if (
        ledger.get("status") != "SUCCESS"
        or ledger.get("count") != 1
        or ledger.get("max_count") != 1
    ):
        errors.append("WB_FINAL_LEDGER_NOT_SUCCESS")
    if handoff.get("approved_by") != ["MACHINE_TECHNICAL_GATES"] or not handoff.get("final_runs"):
        errors.append("WB_HANDOFF_NOT_ACCEPTED")
    return errors


def history_errors(root):
    errors = []
    for relative in ["evals/results/phase-004c5", "evals/results/phase-004c6"]:
        if (
            git(root, "ls-tree", "-r", HISTORY, "--", relative)
            != git(root, "ls-tree", "-r", "HEAD", "--", relative)
            or git(root, "diff", "HEAD", "--", relative).strip()
        ):
            errors.append("WB_FROZEN_HISTORY_CHANGED:" + relative)
    old = read(
        root, "evals/results/phase-004c6/qualification/rejected_r2/rc9_candidate_decision.json"
    )
    if (
        old.get("status") != "BLOCK"
        or old.get("subject_commit") != ("10e8b038d571b88ce2b7f2388da00a618c774f69")
        or old.get("old_validation") != {"passed": 0, "total": 2}
    ):
        errors.append("WB_HISTORICAL_REJECTION_IDENTITY_CHANGED")
    return errors


def validate_matrix(matrix):
    errors = []
    modules = matrix.get("modules", [])
    if len(modules) != 14 or {m.get("module") for m in modules} != {
        f"M{i:02}" for i in range(1, 15)
    }:
        errors.append("WB_MODULE_COVERAGE_INVALID")
    for row in modules:
        if (
            row.get("execution") != "COMPLETED"
            or row.get("engineering") != "CONTRACTS_CHECKED"
            or row.get("next_module_started") is not False
            or not row.get("receipt")
            or row.get("human_review") != "NOT_RUN"
            or not row.get("scientific")
        ):
            errors.append("WB_MODULE_NOT_ACTUALLY_ACCEPTED")
    families = matrix.get("families", [])
    if len(families) != 3 or {f.get("kind") for f in families} != {
        "prediction",
        "optimization",
        "mixed",
    }:
        errors.append("WB_FAMILY_COVERAGE_INVALID")
    for row in families:
        if (
            row.get("native_state") != "READY_FOR_PAPER_HANDOFF"
            or row.get("actual_model_starts", 0) < 2
            or row.get("independent_final_starts") != 1
            or row.get("negative_cases_passed", 0) < 1
            or not row.get("numerical_results")
            or not row.get("evidence")
        ):
            errors.append("WB_FAMILY_EXECUTION_INCOMPLETE")
    if matrix.get("whole_known_problem_completed") is not False:
        errors.append("WB_KNOWN_SCOPE_ESCALATION")
    if matrix.get("new_independent_validation") != 0 or matrix.get("human_review") != "NOT_RUN":
        errors.append("WB_ACCEPTANCE_SCOPE_ESCALATION")
    return errors


def validate_receipts(root, snapshot):
    errors = []
    receipts = snapshot.get("receipts", {})
    if set(receipts) != RECEIPTS:
        return ["WB_REQUIRED_RECEIPT_SET_INVALID"]
    for name, binding in receipts.items():
        try:
            item = json.loads(bound(root, binding))
            if (
                item.get("kind") != name
                or item.get("status") != "PASS"
                or item.get("implementation_hash") != snapshot["implementation_hash"]
                or not item.get("evidence")
            ):
                errors.append("WB_RECEIPT_IDENTITY_OR_RESULT_INVALID:" + name)
            for evidence in item.get("evidence", []):
                bound(root, evidence)
            if name in {"full_ci", "strict_checks", "boundary_tests", "public_paths"}:
                commands = item.get("commands", [])
                if not commands:
                    errors.append("WB_COMMAND_EVIDENCE_MISSING:" + name)
                for command in commands:
                    if command.get("exit_code") != 0:
                        errors.append("WB_COMMAND_FAILED:" + name)
                    start = datetime.fromisoformat(command["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(command["ended_at"].replace("Z", "+00:00"))
                    if start.tzinfo is None or end < start or command["elapsed_seconds"] < 0:
                        errors.append("WB_COMMAND_TIME_INVALID")
                    if mapping(root, command["executed_head"]) != snapshot["implementation_sha256"]:
                        errors.append("WB_TESTED_SUBJECT_MISMATCH")
                    bound(root, command["log"])
                if name == "full_ci" and not any(
                    c.get("argv") == ["bash", "scripts/ci.sh"] for c in commands
                ):
                    errors.append("WB_FULL_CI_REQUIRED")
                if name == "full_ci" and (
                    item.get("pytest_failed") != 0 or item.get("pytest_passed", 0) < 2240
                ):
                    errors.append("WB_FULL_CI_NOT_PASS")
            if name == "native_review" and (
                item.get("mechanism") != "NATIVE_READ_ONLY_AGENT"
                or not item.get("actual_agent_task")
                or item.get("material_open_findings") != []
                or item.get("actual_command_count", 0) < 1
            ):
                errors.append("WB_NATIVE_REVIEW_INSUFFICIENT")
            if name == "context_handoff" and (
                item.get("mechanism") != "NATIVE_RESTRICTED_CONTEXT_WORKER"
                or not item.get("actual_agent_task")
                or item.get("module_executed") not in {f"M{i:02}" for i in range(1, 15)}
                or item.get("web_review") != "NOT_RUN"
                or item.get("next_module_started") is not False
            ):
                errors.append("WB_CONTEXT_HANDOFF_INSUFFICIENT")
            if name == "known_interface":
                counts = item.get("actual_starts", {})
                if (
                    item.get("scope") != ["REQ-Q3"]
                    or item.get("default_scenario") is not True
                    or item.get("native_state") != "READY_FOR_PAPER_HANDOFF"
                    or item.get("whole_problem_completed") is not False
                    or not 1 <= counts.get("model_cli_starts", 0) <= 4
                    or not 1 <= counts.get("independent_checker_starts", 0) <= 6
                    or counts.get("final_starts") != 1
                ):
                    errors.append("WB_KNOWN_INTERFACE_INCOMPLETE")
            if name == "review_roundtrip" and item.get("observed_dispositions") != {
                "counterexample": "CONFIRMED",
                "unsupported": "NEEDS_EVIDENCE",
                "old_package": "REGISTERED_STALE",
                "malicious": "BLOCK",
            }:
                errors.append("WB_REVIEW_ROUNDTRIP_INCOMPLETE")
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            errors.append("WB_RECEIPT_INVALID:" + name + ":" + str(exc))
    return sorted(set(errors))


def evaluate(stage="workspace", root=ROOT):
    errors = history_errors(root)
    state = read(root, "state/project_state.json")
    if state.get("phase") != PHASE:
        return {"status": "BLOCK", "reason_codes": ["WB_PHASE_IDENTITY_INVALID"]}
    if not (root / SNAPSHOT).exists():
        if stage != "workspace" or state.get("active_skill_version") != "0.2.0-competition-rc8":
            errors.append("WB_CANDIDATE_EVIDENCE_REQUIRED")
        return {
            "status": "BLOCK" if errors else "PASS_BUILD_NOT_QUALIFIED",
            "qualified": False,
            "reason_codes": errors,
        }
    snapshot = read(root, SNAPSHOT)
    try:
        protocol = read(root, QUAL + "/protocol.json")
        if (
            snapshot.get("protocol_sha256") != digest((root / QUAL / "protocol.json").read_bytes())
            or protocol.get("target_skill_version") != "0.2.0-competition-rc10"
            or (root / ".agents/skills/cumcm-modeling-evidence/VERSION").read_text().strip()
            != "0.2.0-competition-rc10"
        ):
            errors.append("WB_PROTOCOL_OR_VERSION_IDENTITY_INVALID")
        expected = mapping(root, snapshot["subject_commit"])
        if (
            snapshot.get("implementation_sha256") != expected
            or not expected
            or snapshot.get("implementation_hash") != canonical(expected)
        ):
            errors.append("WB_CANDIDATE_MAPPING_INVALID")
        for path, expected_hash in expected.items():
            if not (root / path).is_file() or digest((root / path).read_bytes()) != expected_hash:
                errors.append("WB_CURRENT_IMPLEMENTATION_DRIFT:" + path)
        if set(mapping(root, "HEAD")) != set(expected):
            errors.append("WB_CURRENT_PATH_SET_DRIFT")
        if (
            stage == "workspace"
            and state.get("technical_adjudication_status") == "MODULAR_WORKBENCH_BUILD_IN_PROGRESS"
        ):
            return {
                "status": "BLOCK" if errors else "PASS_BUILD_NOT_QUALIFIED",
                "qualified": False,
                "reason_codes": sorted(set(errors)),
            }
        matrix = json.loads(bound(root, snapshot["acceptance_matrix"]))
        errors.extend(validate_matrix(matrix))
        for row in matrix.get("modules", []):
            actual = json.loads(bound(root, row["receipt"]))
            if any(
                actual.get(k) != row.get(k)
                for k in [
                    "module",
                    "execution",
                    "engineering",
                    "scientific",
                    "human_review",
                    "next_module_started",
                ]
            ):
                errors.append("WB_MODULE_RECEIPT_MISMATCH")
        for family in matrix.get("families", []):
            errors.extend(validate_family_evidence(root, family))
            for evidence in family.get("evidence", []):
                bound(root, evidence)
        errors.extend(validate_receipts(root, snapshot))
        decision = {
            "schema_version": "modular-workbench-adjudication/v1",
            "decision_id": "DECISION-MODULAR-WORKBENCH-004C7",
            "subject_commit": snapshot["subject_commit"],
            "candidate_sha256": digest((root / SNAPSHOT).read_bytes()),
            "status": "BLOCK" if errors else "PASS",
            "reason_codes": sorted(set(errors)),
            "scope": "MODULAR_WORKBENCH_ENGINEERING_ONLY",
            "new_independent_validation": 0,
            "old_validation": {"passed": 0, "total": 2},
            "team_compliance_review": "NOT_RUN",
        }
        if stage == "active" or (
            stage == "workspace" and state.get("active_skill_version") == "0.2.0-competition-rc10"
        ):
            if read(root, DECISION) != decision:
                errors.append("WB_DECISION_REPLAY_MISMATCH")
            audit = read(root, AUDIT)
            if (
                audit.get("status") != "PASS"
                or audit.get("mechanism") != "NATIVE_READ_ONLY_DECISION_AUDITOR"
                or audit.get("decision_sha256") != digest((root / DECISION).read_bytes())
                or audit.get("subject_commit") != snapshot["subject_commit"]
                or not audit.get("actual_agent_task")
                or not audit.get("evidence")
            ):
                errors.append("WB_DECISION_AUDITOR_REQUIRED")
            for evidence in audit.get("evidence", []):
                bound(root, evidence)
            if (
                state.get("technical_adjudication_status")
                != "MODULAR_WORKBENCH_ENGINEERING_ACCEPTED"
            ):
                errors.append("WB_ACTIVE_STATE_MISMATCH")
        return {
            **decision,
            "status": "BLOCK" if errors else "PASS",
            "reason_codes": sorted(set(errors)),
        }
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        subprocess.CalledProcessError,
    ) as exc:
        return {"status": "BLOCK", "reason_codes": ["WB_QUALIFICATION_INVALID:" + str(exc)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=["workspace", "candidate", "active"], default="workspace"
    )
    args = parser.parse_args()
    result = evaluate(args.stage)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
