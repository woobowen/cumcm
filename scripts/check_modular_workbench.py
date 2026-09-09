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
NEGATIVES = {
    "wrong_scenario",
    "input_change",
    "future_information",
    "infeasible_solution",
    "missing_primary_question",
    "scope_conflict",
    "single_module_stop",
    "writer_lock",
    "interrupted_request",
    "one_shot_final",
    "partial_not_whole",
    "local_dependency_stale",
    "idempotent_request_export_feedback",
    "credential_and_injection_rejection",
    "wrong_case_package_hash",
    "malformed_and_archive_feedback_rejection",
}
PREFIXES = [
    ".agents/skills/cumcm-modeling-evidence/",
    "contracts/",
    "rules/",
    "tests/",
    "scripts/",
    "src/",
    "docs/modular_workbench/",
    BASE + "/known_code/",
]
EXACT = {
    "README.md",
    "docs/INDEX.md",
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


def strict_json(data):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("WB_DUPLICATE_JSON_KEY")
            value[key] = item
        return value

    def invalid(value):
        raise ValueError("WB_NONFINITE_JSON_NUMBER:" + value)

    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)


def read(root, relative):
    path = Path(relative)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != relative
        or (root / path).is_symlink()
        or any(p.is_symlink() for p in (root / path).parents if p != root.parent)
    ):
        raise ValueError("WB_ACCEPTANCE_UNSAFE_PATH")
    value = strict_json((root / path).read_text())
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


def mapping(root, subject):
    if subject != "HEAD" and not re.fullmatch(r"[0-9a-f]{40}", subject):
        raise ValueError("WB_SUBJECT_COMMIT_INVALID")
    actual = git(root, "rev-parse", subject).decode().strip()
    return frozen_mapping(root, actual)


@lru_cache(maxsize=32)
def frozen_mapping(root, subject):
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


def exact_records(root, binding):
    packet = strict_json(bound(root, binding))
    if packet.get("derivation") != "EXACT_UTF8_JSON_NO_REDACTION":
        raise ValueError("WB_PUBLIC_PROJECTION_UNDECLARED")
    records = packet["records"]
    if not isinstance(records, dict) or not records:
        raise ValueError("WB_CAPTURED_RECORDS_MISSING")
    for key, record in records.items():
        raw = record["raw_utf8"].encode()
        if not key or digest(raw) != record["raw_sha256"] or strict_json(raw) != record["content"]:
            raise ValueError("WB_RAW_RECORD_IDENTITY_INVALID")
    return records


def actual_command(command):
    if (
        not isinstance(command.get("argv"), list)
        or not command["argv"]
        or not all(isinstance(a, str) and a for a in command["argv"])
        or type(command.get("exit_code")) is not int
    ):
        raise ValueError("WB_COMMAND_RECORD_INVALID")
    start = datetime.fromisoformat(command["started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(command["ended_at"].replace("Z", "+00:00"))
    elapsed = command.get("elapsed_seconds", (end - start).total_seconds())
    if (
        start.tzinfo is None
        or end.tzinfo is None
        or end < start
        or type(elapsed) not in {int, float}
        or elapsed < 0
    ):
        raise ValueError("WB_COMMAND_TIME_INVALID")


def validate_family_evidence(root, family):
    """Cross-bind exact producer, independent checker, Final and handoff records."""
    records = exact_records(root, family["record_packet"])
    values = {k: r["content"] for k, r in records.items()}
    state, ledger, handoff = [values[k] for k in ("case_state", "final_ledger", "handoff")]
    plan = values["experiment_plan"]["content"]
    requirements = values["problem_requirements"]["content"]["requirements"]
    raw = values["input"]
    captures = [r for key, r in values.items() if key.startswith("capture:")]
    errors = []
    if (
        state.get("state") != family["native_state"]
        or state.get("case_id") != family["case_id"]
        or state.get("skill_version") != "0.2.0-competition-rc10"
        or raw.get("kind") != family["kind"]
        or raw.get("provenance") != "PROJECT_ORIGINAL_SYNTHETIC_TRAJECTORY_NOT_EMPIRICAL"
        or len(captures) != family["actual_model_starts"]
    ):
        errors.append("WB_CAPTURED_FAMILY_STATE_MISMATCH")
    ids = [c.get("run_id") for c in captures]
    if any(
        not isinstance(rid, str) or not re.fullmatch(r"RUN-[A-Z0-9-]+", rid) for rid in ids
    ) or len(ids) != len(set(ids)):
        return errors + ["WB_CAPTURED_RUN_IDENTITIES_INVALID"]
    expected = {
        (candidate, seed) for candidate in plan["candidate_ids"] for seed in plan["random_seeds"]
    }
    if {(c.get("candidate_id"), c.get("seed")) for c in captures} != expected:
        errors.append("WB_CAPTURED_CANDIDATE_SEED_INCOMPLETE")
    for capture in captures:
        rid = capture["run_id"]
        actual_command(capture)
        output = records["output:" + rid]
        check = values["check:" + rid]
        check_capture = values["check_capture:" + rid]
        actual_command(check_capture)
        if (
            capture.get("outcome") != "SUCCESS"
            or capture["exit_code"] != 0
            or capture.get("capture_mode") != "CONTROLLED_CASE_SUBPROCESS"
            or capture.get("code_commit") != plan["code_commit"]
            or capture.get("runner_version") != state["skill_version"]
            or capture.get("input_files")
            != [{"path": "data/raw/input.json", "sha256": records["input"]["raw_sha256"]}]
            or capture["output"]["sha256"] != output["raw_sha256"]
            or not re.fullmatch(r"[a-f0-9]{64}", capture.get("scenario_hash", ""))
        ):
            errors.append("WB_CAPTURE_OUTPUT_INPUT_BINDING_INVALID")
        if (
            check.get("run_id") != rid
            or check.get("output_sha256") != output["raw_sha256"]
            or check_capture.get("run_id") != rid
            or check_capture.get("exit_code") != 0
            or check_capture.get("status") != "SUCCESS"
            or check_capture.get("capture_mode") != "CONTROLLED_SCIENTIFIC_CHECK_SUBPROCESS"
            or check_capture["bound_files"].get(f"runs/{rid}/scientific_check.json")
            != records["check:" + rid]["raw_sha256"]
            or check_capture["bound_files"].get(f"runs/{rid}/execution_capture.json")
            != records["capture:" + rid]["raw_sha256"]
        ):
            errors.append("WB_INDEPENDENT_CHECK_BINDING_INVALID")
    selected = ledger.get("selected_run_ids", [])
    if (
        ledger.get("schema_version") != "scientific-final/v1"
        or ledger.get("status") != "SUCCESS"
        or type(ledger.get("count")) is not int
        or ledger["count"] != 1
        or type(ledger.get("test_access_count")) is not int
        or ledger["test_access_count"] != 0
        or not selected
        or len(selected) != len(set(selected))
        or not set(selected) <= set(ids)
        or set(ledger.get("checks", {})) != set(selected)
    ):
        return errors + ["WB_FINAL_LEDGER_NOT_SUCCESS"]
    actual_command({**ledger, "argv": ["SCIENTIFIC_FINAL"], "exit_code": 0})
    for rid in selected:
        final = values["final_check:" + rid]
        command = ledger["checks"][rid]
        actual_command(command)
        if (
            command["exit_code"] != 0
            or command["files"].get(f"runs/{rid}/final_check.json")
            != records["final_check:" + rid]["raw_sha256"]
            or final.get("run_id") != rid
            or final.get("output_sha256") != records["output:" + rid]["raw_sha256"]
            or any(r.get("feasible") is not True for r in final["requirements"].values())
        ):
            errors.append("WB_FINAL_RECALCULATION_BINDING_INVALID")
    final_runs = handoff.get("final_runs", [])
    if (
        handoff.get("approved_by") != ["MACHINE_TECHNICAL_GATES"]
        or {r.get("run_id") for r in final_runs} != set(selected)
        or {r["requirement_id"] for r in requirements}
        != {rid for run in final_runs for rid in run["requirement_ids"]}
        or any(
            run["manifest_hash"] != canonical(values["manifest:" + run["run_id"]])
            for run in final_runs
        )
    ):
        errors.append("WB_HANDOFF_NOT_ACCEPTED")
    if family["kind"] == "mixed" and (
        len(requirements) < 3 or family.get("primary_requirements") != len(requirements)
    ):
        errors.append("WB_MIXED_PRIMARY_COVERAGE_INCOMPLETE")
    for row in family.get("numerical_results", []):
        if row["metrics"] != values["output:" + row["run_id"]]["final_metrics"]:
            errors.append("WB_NUMERICAL_SUMMARY_MISMATCH")
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
        if row.get("kind") == "mixed" and (
            type(row.get("primary_requirements")) is not int or row["primary_requirements"] < 3
        ):
            errors.append("WB_MIXED_PRIMARY_COVERAGE_INCOMPLETE")
    coverage = matrix.get("boundary_coverage", {})
    if set(coverage) != NEGATIVES or any(not v for v in coverage.values()):
        errors.append("WB_BOUNDARY_COVERAGE_INCOMPLETE")
    variants = matrix.get("scenario_equivalence", {})
    if set(variants) != {"prediction", "optimization", "mixed"} or any(
        set(v) != {"default", "equivalent_explicit"} or not all(v.values())
        for v in variants.values()
    ):
        errors.append("WB_DEFAULT_EXPLICIT_EQUIVALENCE_INCOMPLETE")
    if matrix.get("whole_known_problem_completed") is not False:
        errors.append("WB_KNOWN_SCOPE_ESCALATION")
    if matrix.get("new_independent_validation") != 0 or matrix.get("human_review") != "NOT_RUN":
        errors.append("WB_ACCEPTANCE_SCOPE_ESCALATION")
    return errors


def passed_nodes(data):
    return set(re.findall(r"^(tests/[^\r\n]+?) PASSED(?: |$)", data.decode(), re.MULTILINE))


def validate_coverage_logs(root, matrix, snapshot):
    receipt = strict_json(bound(root, snapshot["receipts"]["boundary_tests"]))
    passed = set()
    for command in receipt["commands"]:
        passed.update(passed_nodes(bound(root, command["log"])))
    declared = [node for nodes in matrix["boundary_coverage"].values() for node in nodes]
    declared += [
        node for values in matrix["scenario_equivalence"].values() for node in values.values()
    ]
    if not declared or any(node not in passed for node in declared):
        return ["WB_COVERAGE_NOT_BOUND_TO_ACTUAL_PASSING_TESTS"]
    return []


def validate_detail(root, name, item):
    detail = strict_json(bound(root, item["detail"]))
    if detail.get("schema_version") != "workbench-" + name.replace("_", "-") + "/v1":
        raise ValueError("WB_DETAIL_SCHEMA_INVALID:" + name)
    if detail.get("implementation_hash") != item["implementation_hash"]:
        raise ValueError("WB_DETAIL_IMPLEMENTATION_MISMATCH")
    commands = detail.get("commands", [])
    if not commands:
        raise ValueError("WB_DETAIL_COMMANDS_MISSING:" + name)
    for command in commands:
        actual_command(command)
        if "result" not in command and "log" not in command:
            raise ValueError("WB_DETAIL_COMMAND_RESULT_MISSING")
        if "log" in command:
            bound(root, command["log"])
    if name == "native_review":
        if (
            detail.get("actual_agent_task") != item["actual_agent_task"]
            or len(detail.get("read_files", {})) < 3
            or detail.get("material_open_findings") != []
            or not detail.get("review_report")
            or not detail.get("actual_tool_record")
        ):
            raise ValueError("WB_NATIVE_REVIEW_DETAIL_INCOMPLETE")
        bound(root, detail["review_report"])
        bound(root, detail["actual_tool_record"])
        for path, sha in detail["read_files"].items():
            if digest((root / path).read_bytes()) != sha:
                raise ValueError("WB_NATIVE_REVIEW_SUBJECT_DRIFT")
    elif name == "context_handoff":
        records = exact_records(root, detail["record_packet"])
        request, done, report, context = [
            records[k]["content"] for k in ("request", "completion", "work_report", "context")
        ]
        if (
            detail.get("actual_agent_task") != item["actual_agent_task"]
            or done["request_sha256"] != canonical(request)
            or done["module"] != item["module_executed"]
            or done["module"] != request["module"]
            or report["module"] != done["module"]
            or any(done[k] != request[k] for k in ["case_id", "request_id", "requirement_scope"])
            or done["artifact_hashes"].get(done["report_path"])
            != records["work_report"]["raw_sha256"]
            or done["execution"] != "COMPLETED"
            or done["next_module_started"] is not False
            or context["execution_mode"] != "GUIDED_SINGLE_MODULE"
            or not detail.get("worker_proposal")
            or not detail.get("actual_tool_record")
        ):
            raise ValueError("WB_CONTEXT_HANDOFF_DETAIL_INCOMPLETE")
        bound(root, detail["worker_proposal"])
        bound(root, detail["actual_tool_record"])
    elif name == "review_roundtrip":
        observed = [command.get("result", {}) for command in commands]
        dispositions = {r.get("disposition") for r in observed if isinstance(r, dict)}
        statuses = {r.get("status") for r in observed if isinstance(r, dict)}
        if (
            not {"CONFIRMED", "NEEDS_EVIDENCE", "ALTERNATIVE_DESIGN"} <= dispositions
            or not {"REGISTERED_PENDING", "REGISTERED_STALE", "BLOCK"} <= statuses
            or detail.get("formal_state_before_sha256") != detail.get("formal_state_after_sha256")
            or not re.fullmatch(r"[a-f0-9]{64}", detail.get("formal_state_before_sha256", ""))
        ):
            raise ValueError("WB_FEEDBACK_ACTION_EVIDENCE_INCOMPLETE")
        records = exact_records(root, detail["record_packet"])
        if records["recalculation"]["content"] != {
            "values": [2, 3, 5],
            "sum": 10,
            "draft": 11,
            "residual": 1,
        }:
            raise ValueError("WB_COUNTEREXAMPLE_RECALCULATION_MISSING")
        for disposition in ("COUNTEREXAMPLE", "UNSUPPORTED", "ALTERNATIVE"):
            value = records["disposition:" + disposition]["content"]
            evidence = records["followup:" + disposition]
            if value["evidence_sha256"] != evidence["raw_sha256"]:
                raise ValueError("WB_FEEDBACK_DISPOSITION_BINDING_INVALID")
    elif name == "independent_recalculation":
        if (
            detail.get("producer_imported") is not False
            or not detail.get("independent_code")
            or {r.get("kind") for r in detail.get("results", [])}
            != {"prediction", "optimization", "mixed"}
        ):
            raise ValueError("WB_INDEPENDENT_RECALCULATION_DETAIL_INCOMPLETE")
        bound(root, detail["independent_code"])
        for row in detail["results"]:
            if row.get("max_abs_residual", 1) > 1e-6 or row.get("numeric_values_checked", 0) < 3:
                raise ValueError("WB_INDEPENDENT_RECALCULATION_NOT_PASS")
            bound(root, row["record_packet"])
    elif name == "known_interface":
        records = exact_records(root, detail["record_packet"])
        registration, terminal, budget, ledger = [
            records[k]["content"] for k in ("registration", "terminal", "budget", "final_ledger")
        ]
        used = {
            kind: sum(e.get("kind") == kind for e in budget["events"])
            for kind in ("model_cli_starts", "independent_checker_starts", "final_starts")
        }
        captures = [r["content"] for k, r in records.items() if k.startswith("capture:")]
        if (
            registration["required_question_ids"] != ["REQ-Q3"]
            or registration["evidence_role"] != "MODULE_USABILITY_DEVELOPMENT"
            or terminal["status"] != "SCOPED_DEVELOPMENT_COMPLETE"
            or terminal["case_id"] != registration["case_id"]
            or terminal["subject_commit"] != registration["skill_commit"]
            or terminal["independent_validation"] is not False
            or used != item["actual_starts"]
            or len(captures) != used["model_cli_starts"]
            or ledger["status"] != "SUCCESS"
            or type(ledger["count"]) is not int
            or ledger["count"] != 1
        ):
            raise ValueError("WB_KNOWN_ACTUAL_RECORD_MISMATCH")
        for capture in captures:
            actual_command(capture)
            if (
                capture["outcome"] != "SUCCESS"
                or capture["code_commit"] != registration["skill_commit"]
            ):
                raise ValueError("WB_KNOWN_CAPTURE_NOT_SUCCESS")
    return []


def validate_receipts(root, snapshot):
    errors = []
    receipts = snapshot.get("receipts", {})
    if set(receipts) != RECEIPTS:
        return ["WB_REQUIRED_RECEIPT_SET_INVALID"]
    for name, binding in receipts.items():
        try:
            item = strict_json(bound(root, binding))
            if (
                item.get("kind") != name
                or item.get("status") != "PASS"
                or item.get("implementation_hash") != snapshot["implementation_hash"]
                or not item.get("evidence")
            ):
                errors.append("WB_RECEIPT_IDENTITY_OR_RESULT_INVALID:" + name)
            for evidence in item.get("evidence", []):
                bound(root, evidence)
            if name not in {"full_ci", "strict_checks", "boundary_tests", "public_paths"}:
                errors.extend(validate_detail(root, name, item))
            if name in {"full_ci", "strict_checks", "boundary_tests", "public_paths"}:
                commands = item.get("commands", [])
                if not commands:
                    errors.append("WB_COMMAND_EVIDENCE_MISSING:" + name)
                for command in commands:
                    actual_command(command)
                    if command.get("exit_code") != 0:
                        errors.append("WB_COMMAND_FAILED:" + name)
                    start = datetime.fromisoformat(command["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(command["ended_at"].replace("Z", "+00:00"))
                    if start.tzinfo is None or end < start or command["elapsed_seconds"] < 0:
                        errors.append("WB_COMMAND_TIME_INVALID")
                    if mapping(root, command["executed_head"]) != snapshot["implementation_sha256"]:
                        errors.append("WB_TESTED_SUBJECT_MISMATCH")
                    log = bound(root, command["log"])
                    if name == "full_ci":
                        counts = re.findall(rb"(?:^|\n)(\d+) passed(?:, (\d+) skipped)? in ", log)
                        if not counts or int(counts[-1][0]) != item.get("pytest_passed"):
                            errors.append("WB_FULL_CI_LOG_COUNT_MISMATCH")
                if name == "strict_checks":
                    required = {
                        (".venv/bin/python", "scripts/validate_repo.py", "--strict"),
                        (".venv/bin/python", "scripts/render_status.py", "--check"),
                        ("git", "diff", "--check"),
                    }
                    if not required <= {tuple(c["argv"]) for c in commands}:
                        errors.append("WB_STRICT_CHECK_COMMANDS_INCOMPLETE")
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
            or protocol.get("target_repository_version") != "0.3.0-competition-rc10"
            or (root / "VERSION").read_text().strip() != "0.3.0-competition-rc10"
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
        untracked = git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()
        if any(p in EXACT or any(p.startswith(prefix) for prefix in PREFIXES) for p in untracked):
            errors.append("WB_UNTRACKED_IMPLEMENTATION_PATH")
        if (
            stage == "workspace"
            and state.get("technical_adjudication_status") == "MODULAR_WORKBENCH_BUILD_IN_PROGRESS"
        ):
            return {
                "status": "BLOCK" if errors else "PASS_BUILD_NOT_QUALIFIED",
                "qualified": False,
                "reason_codes": sorted(set(errors)),
            }
        matrix = strict_json(bound(root, snapshot["acceptance_matrix"]))
        errors.extend(validate_matrix(matrix))
        errors.extend(validate_coverage_logs(root, matrix, snapshot))
        for row in matrix.get("modules", []):
            actual = strict_json(bound(root, row["receipt"]))
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
