"""Evidence adjudication for a new RC9 subject; never reuse RC8 current-tree eligibility.

Subject -> command/review receipts -> candidate -> decision -> independent Auditor
-> activation are separate objects. No object contains its own future Git commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("evals/results/phase-004c6/qualification")
PROTOCOL = BASE / "rc9_candidate_protocol.json"
SNAPSHOT = BASE / "rc9_candidate_snapshot.json"
DECISION = BASE / "rc9_candidate_decision.json"
AUDITOR = BASE / "rc9_decision_audit.json"
ACTIVATION = BASE / "rc9_activation.json"
HEX40 = re.compile(r"[a-f0-9]{40}\Z")


def read(path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("OBJECT_REQUIRED")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return digest(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    )


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def selected_paths(root, subject, protocol):
    paths = git(root, "ls-tree", "-r", "--name-only", subject).decode().splitlines()
    prefixes = protocol["implementation_prefixes"] + protocol["case_code_prefixes"]
    exact = set(protocol["implementation_files"]) | {
        PROTOCOL.as_posix(),
        (BASE / "neutral_design.json").as_posix(),
        *[
            f"evals/results/phase-004c6/{c}/development_design.json"
            for c in protocol["required_development_cases"]
        ],
    }
    return sorted(p for p in paths if p in exact or any(p.startswith(x + "/") for x in prefixes))


def subject_mapping(root, subject, protocol):
    return {
        p: digest(git(root, "show", subject + ":" + p))
        for p in selected_paths(root, subject, protocol)
    }


def validate_subject(snapshot, protocol, root=ROOT):
    errors = []
    if (
        snapshot.get("schema_version") != "phase-004c6-rc9-candidate/v1"
        or snapshot.get("candidate_id") != protocol["candidate_id"]
        or snapshot.get("accepted_scope") != protocol["accepted_scope"]
        or type(snapshot.get("functional_revision")) is not int
        or not 1 <= snapshot["functional_revision"] <= protocol["functional_candidate_limit"]
    ):
        errors.append("RC9_CANDIDATE_IDENTITY_INVALID")
    subject = snapshot.get("subject_commit", "")
    if not HEX40.fullmatch(subject):
        return ["RC9_SUBJECT_INVALID"]
    mapping = subject_mapping(root, subject, protocol)
    if snapshot.get("implementation_sha256") != mapping or not mapping:
        errors.append("RC9_SUBJECT_MAPPING_INVALID")
    if snapshot.get("protocol_sha256") != digest((root / PROTOCOL).read_bytes()):
        errors.append("RC9_PROTOCOL_DRIFT")
    for path, expected in mapping.items():
        current = root / path
        if not current.is_file() or digest(current.read_bytes()) != expected:
            errors.append("RC9_CURRENT_IMPLEMENTATION_DRIFT:" + path)
    head_paths = selected_paths(root, "HEAD", protocol)
    if set(head_paths) != set(mapping):
        errors.append("RC9_CURRENT_IMPLEMENTATION_PATH_DRIFT")
    if (
        git(root, "show", subject + ":VERSION").decode().strip()
        != protocol["target_versions"]["project"]
    ):
        errors.append("RC9_PROJECT_VERSION_MISMATCH")
    if (
        git(root, "show", subject + ":.agents/skills/cumcm-modeling-evidence/VERSION")
        .decode()
        .strip()
        != protocol["target_versions"]["skill"]
    ):
        errors.append("RC9_SKILL_VERSION_MISMATCH")
    historical = "evals/results/phase-004c5"
    old = git(root, "ls-tree", "-r", protocol["history_subject"], "--", historical)
    current = git(root, "ls-tree", "-r", "HEAD", "--", historical)
    if old != current or git(root, "diff", "HEAD", "--", historical).strip():
        errors.append("RC9_PREDECESSOR_HISTORY_DRIFT")
    if (
        snapshot.get("old_validation") != {"passed": 0, "total": 2}
        or snapshot.get("new_independent_validation") != 0
    ):
        errors.append("RC9_VALIDATION_SCOPE_ESCALATION")
    return errors


def binding_file(root, binding):
    path = Path(binding["path"])
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.as_posix().startswith("evals/results/phase-004c6/")
    ):
        raise ValueError("RC9_EVIDENCE_PATH_INVALID")
    data = (root / path).read_bytes()
    if digest(data) != binding["sha256"]:
        raise ValueError("RC9_EVIDENCE_HASH_MISMATCH:" + path.as_posix())
    return data


def validate_receipts(snapshot, protocol, root=ROOT):
    errors = []
    records = snapshot.get("receipts", {})
    if set(records) != set(protocol["required_receipts"]):
        return ["RC9_RECEIPT_SET_INVALID"]
    subject = snapshot["subject_commit"]
    for key, binding in records.items():
        try:
            receipt = json.loads(binding_file(root, binding))
            if receipt.get("subject_commit") != subject or receipt.get("status") != "PASS":
                errors.append("RC9_RECEIPT_NOT_PASS:" + key)
            if receipt.get("kind") != key:
                errors.append("RC9_RECEIPT_KIND_INVALID:" + key)
            if not receipt.get("evidence"):
                errors.append("RC9_RECEIPT_EVIDENCE_MISSING:" + key)
            for evidence in receipt.get("evidence", []):
                binding_file(root, evidence)
            if key in {"focused_tests", "full_ci", "strict", "historical_subjects"}:
                commands = receipt.get("commands", [])
                if not commands or any(c.get("exit_code") != 0 for c in commands):
                    errors.append("RC9_COMMAND_FAILURE:" + key)
                for command in commands:
                    started = datetime.fromisoformat(command["started_at"].replace("Z", "+00:00"))
                    ended = datetime.fromisoformat(command["ended_at"].replace("Z", "+00:00"))
                    if ended < started or command.get("elapsed_seconds", -1) < 0:
                        errors.append("RC9_COMMAND_TIME_INVALID:" + key)
                    if (
                        subject_mapping(root, command["executed_head"], protocol)
                        != snapshot["implementation_sha256"]
                    ):
                        errors.append("RC9_TESTED_IMPLEMENTATION_MISMATCH:" + key)
                    binding_file(root, command["log"])
                if key == "full_ci":
                    if not any(c["argv"] == ["bash", "scripts/ci.sh"] for c in commands):
                        errors.append("RC9_FULL_CI_COMMAND_MISSING")
                    if (
                        receipt.get("pytest_passed", 0) < protocol["minimum_full_pytest_passed"]
                        or receipt.get("pytest_failed") != 0
                    ):
                        errors.append("RC9_FULL_PYTEST_NOT_PASS")
                if (
                    key == "focused_tests"
                    and receipt.get("pytest_passed", 0) < protocol["minimum_focused_passed"]
                ):
                    errors.append("RC9_FOCUSED_TEST_COVERAGE_INSUFFICIENT")
            elif key == "neutral_spec_results":
                design = read(root / BASE / "neutral_design.json")
                cases = receipt.get("cases", [])
                if {c.get("id") for c in cases} != {c["id"] for c in design["cases"]} or len(
                    cases
                ) != 10:
                    errors.append("RC9_NEUTRAL_SPEC_COVERAGE_INVALID")
                if any(c.get("status") != "PASS" or not c.get("pytest_nodeids") for c in cases):
                    errors.append("RC9_NEUTRAL_SPEC_NOT_PASS")
                if receipt.get("actual_cli_e2e") != {
                    "optimization": "PASS",
                    "same_entity_prediction": "PASS",
                    "mixed_requirements": "PASS",
                }:
                    errors.append("RC9_THREE_CLI_E2E_NOT_PASS")
            elif key.startswith("native_"):
                if (
                    receipt.get("mechanism") != "NATIVE_READ_ONLY_AGENT"
                    or not receipt.get("actual_agent_task")
                    or receipt.get("material_open_findings") != []
                ):
                    errors.append("RC9_NATIVE_REVIEW_INSUFFICIENT:" + key)
                if (
                    receipt.get("reviewed_subject") != subject
                    or type(receipt.get("actual_command_count")) is not int
                    or receipt["actual_command_count"] < 1
                ):
                    errors.append("RC9_NATIVE_REVIEW_SUBJECT_OR_CALLS_INVALID:" + key)
                if key == "native_result_review":
                    development = json.loads(binding_file(root, records["development_results"]))
                    expected = {
                        c["case_id"]: {
                            "terminal": c["terminal"],
                            "execution_evidence": c["execution_evidence"],
                        }
                        for c in development["cases"]
                    }
                    if (
                        receipt.get("review_scope") != "ACTUAL_POSTVALIDATION_DEVELOPMENT_RESULTS"
                        or receipt.get("reviewed_development_artifacts") != expected
                    ):
                        errors.append("RC9_NATIVE_RESULT_ARTIFACT_BINDING_INVALID")
            elif key == "development_results":
                cases = receipt.get("cases", [])
                if {c.get("case_id") for c in cases} != set(
                    protocol["required_development_cases"]
                ) or len(cases) != 2:
                    errors.append("RC9_DEVELOPMENT_COVERAGE_INVALID")
                for case in cases:
                    design = read(
                        root
                        / "evals/results/phase-004c6"
                        / case["case_id"]
                        / "development_design.json"
                    )
                    terminal = json.loads(binding_file(root, case["terminal"]))
                    execution = json.loads(binding_file(root, case["execution_evidence"]))
                    expected_questions = set(design["required_question_ids"])
                    questions = case.get("question_results", [])
                    if (
                        {r.get("requirement_id") for r in questions} != expected_questions
                        or len(questions) != len(expected_questions)
                        or terminal.get("question_results") != questions
                        or terminal.get("case_id") != case["case_id"]
                        or terminal.get("subject_commit") != subject
                        or terminal.get("status") != case.get("terminal_status")
                        or execution.get("case_id") != case["case_id"]
                        or execution.get("subject_commit") != subject
                        or case["terminal"]["path"]
                        != f"evals/results/phase-004c6/{case['case_id']}/terminal/decision.json"
                    ):
                        errors.append("RC9_DEVELOPMENT_RESULT_BINDING_INVALID")
                    if (
                        case.get("subject_commit") != subject
                        or case.get("independent_validation") is not False
                        or not case.get("question_results")
                        or not case.get("limitations")
                    ):
                        errors.append("RC9_DEVELOPMENT_SCOPE_INVALID")
                    starts = case.get("actual_starts", {})
                    ledger = json.loads(binding_file(root, execution["budget_ledger"]))
                    actual_counts = {
                        k: sum(e["kind"] == k for e in ledger["events"]) for k in design["budget"]
                    }
                    if (
                        starts != actual_counts
                        or terminal.get("actual_starts") != starts
                        or ledger.get("limits") != design["budget"]
                    ):
                        errors.append("RC9_DEVELOPMENT_BUDGET_RECEIPT_MISMATCH")
                    for artifact in execution.get("artifacts", []):
                        binding_file(root, artifact)
                    if not execution.get("artifacts") or not execution.get("model_run_ids"):
                        errors.append("RC9_DEVELOPMENT_EXECUTION_EVIDENCE_MISSING")
                    for k, maximum in {
                        "model_cli_starts": 4,
                        "independent_checker_starts": 4,
                        "final_starts": 1,
                    }.items():
                        if type(starts.get(k)) is not int or not 0 <= starts[k] <= maximum:
                            errors.append("RC9_DEVELOPMENT_START_BUDGET_INVALID")
                    if starts.get("model_cli_starts", 0) < protocol.get(
                        "development_minimum_model_cli_starts", 1
                    ) or starts.get("independent_checker_starts", 0) < protocol.get(
                        "development_minimum_independent_checker_starts", 1
                    ):
                        errors.append("RC9_DEVELOPMENT_MINIMUM_EXECUTION_EVIDENCE_NOT_MET")
                    if (
                        case.get("terminal_status") == "SCOPED_DEVELOPMENT_COMPLETE"
                        and starts.get("final_starts") != 1
                    ):
                        errors.append("RC9_DEVELOPMENT_COMPLETE_WITHOUT_FINAL")
                    if case.get("terminal_status") not in {
                        "SCOPED_DEVELOPMENT_COMPLETE",
                        "FAILED",
                        "INSUFFICIENT",
                    }:
                        errors.append("RC9_DEVELOPMENT_TERMINAL_INVALID")
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            errors.append("RC9_RECEIPT_INVALID:" + key + ":" + str(exc))
    return errors


def evaluate(stage="candidate", root=ROOT):
    errors = []
    try:
        protocol = read(root / PROTOCOL)
        if stage == "workspace" and not (root / SNAPSHOT).exists():
            state = read(root / "state/project_state.json")
            if state.get("active_skill_version") == protocol["target_versions"]["skill"]:
                return {"status": "BLOCK", "reason_codes": ["RC9_ACTIVE_WITHOUT_CANDIDATE"]}
            return {"status": "PASS_PENDING_CANDIDATE", "qualified": False, "reason_codes": []}
        snapshot = read(root / SNAPSHOT)
        if (
            stage == "workspace"
            and read(root / "state/project_state.json").get("active_skill_version")
            == protocol["target_versions"]["skill"]
        ):
            stage = "active"
        errors.extend(validate_subject(snapshot, protocol, root))
        errors.extend(validate_receipts(snapshot, protocol, root))
        result = {
            "schema_version": "rc9-adjudication/v1",
            "subject_commit": snapshot["subject_commit"],
            "candidate_sha256": digest((root / SNAPSHOT).read_bytes()),
            "status": "BLOCK" if errors else "PASS",
            "reason_codes": sorted(set(errors)),
            "scope": protocol["accepted_scope"],
            "old_validation": {"passed": 0, "total": 2},
            "new_independent_validation": 0,
        }
        if stage == "active":
            decision = read(root / DECISION)
            if decision != result:
                errors.append("RC9_DECISION_REPLAY_MISMATCH")
            audit = read(root / AUDITOR)
            if (
                audit.get("status") != "PASS"
                or audit.get("decision_sha256") != digest((root / DECISION).read_bytes())
                or audit.get("subject_commit") != snapshot["subject_commit"]
                or audit.get("mechanism") != "NATIVE_READ_ONLY_DECISION_AUDITOR"
                or not audit.get("actual_agent_task")
            ):
                errors.append("RC9_DECISION_AUDITOR_NOT_PASS")
            for evidence in audit.get("evidence", []):
                binding_file(root, evidence)
            if not audit.get("evidence"):
                errors.append("RC9_DECISION_AUDITOR_EVIDENCE_MISSING")
            activation = read(root / ACTIVATION)
            for key, path in (
                ("candidate_sha256", SNAPSHOT),
                ("decision_sha256", DECISION),
                ("auditor_sha256", AUDITOR),
            ):
                if activation.get(key) != digest((root / path).read_bytes()):
                    errors.append("RC9_ACTIVATION_BINDING_INVALID:" + key)
            if (
                activation.get("subject_commit") != snapshot["subject_commit"]
                or activation.get("scope") != protocol["accepted_scope"]
            ):
                errors.append("RC9_ACTIVATION_SCOPE_INVALID")
            state = read(root / "state/project_state.json")
            if (
                state.get("active_skill_version") != protocol["target_versions"]["skill"]
                or state.get("technical_adjudication_status") != "C_TARGET_RC9_RESEARCH_READY"
            ):
                errors.append("RC9_ACTIVE_STATE_MISMATCH")
        result.update(status="BLOCK" if errors else "PASS", reason_codes=sorted(set(errors)))
        return result
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        return {"status": "BLOCK", "reason_codes": ["RC9_QUALIFICATION_INVALID:" + str(exc)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=["candidate", "active", "workspace"], default="candidate"
    )
    parser.add_argument("--write-decision", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.stage)
    if args.write_decision:
        if args.stage != "candidate":
            raise SystemExit("Decision creation only in candidate stage")
        with (ROOT / DECISION).open("x") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
