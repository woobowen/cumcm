"""Append-only case history and explicit terminal identities for current maintenance."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

HISTORY_SUBJECT = "bcf498907cbf282e2c79580ea56b043fc1a7b52b"
PHASE = "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C6"
REQUIRED_FIELDS = {
    "case_id",
    "set_type",
    "problem_source",
    "problem_hash",
    "data_hashes",
    "answer_access_status",
    "first_run_status",
    "skill_version",
    "skill_commit",
    "model",
    "reasoning",
    "start_time",
    "freeze_time",
    "unlock_time",
    "generalizable_failures",
    "problem_specific_findings",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def historical_registry(root: Path) -> dict[str, Any]:
    data = subprocess.check_output(
        ["git", "show", f"{HISTORY_SUBJECT}:benchmarks/case_registry.yaml"], cwd=root
    )
    return yaml.safe_load(data)


def validate_registry(
    registry: Any,
    history: dict[str, Any],
    registrations: dict[str, Any],
    terminals: dict[str, Any] | None = None,
) -> list[str]:
    """Validate records and immutable historical projections, independent of list order."""
    errors: list[str] = []
    if not isinstance(registry, dict) or not isinstance(registry.get("cases"), list):
        return ["REGISTRY_CASES_INVALID"]
    if set(registry.get("required_case_fields", [])) != REQUIRED_FIELDS:
        errors.append("REGISTRY_FIELD_CONTRACT_INVALID")
    old = {case["case_id"]: case for case in history["cases"]}
    seen: set[str] = set()
    roots: set[str] = set()
    for case in registry["cases"]:
        if not isinstance(case, dict) or not case.keys() >= REQUIRED_FIELDS:
            errors.append("CASE_REQUIRED_FIELDS_MISSING")
            continue
        cid = case["case_id"]
        if not isinstance(cid, str) or not cid:
            errors.append("CASE_ID_INVALID")
            continue
        if cid in seen:
            errors.append("CASE_ID_DUPLICATE")
        seen.add(cid)
        if case["set_type"] not in {"DEVELOPMENT", "VALIDATION", "HELD_OUT", "STRESS"}:
            errors.append(f"CASE_SET_TYPE_INVALID:{cid}")
        if case["first_run_status"] not in {"NOT_STARTED", "IN_PROGRESS", "FROZEN"}:
            errors.append(f"CASE_FIRST_RUN_STATUS_INVALID:{cid}")
        if case["answer_access_status"] not in {
            "SEALED",
            "UNLOCKED_AFTER_FIRST_RUN",
            "PERMANENTLY_DEVELOPMENT",
        }:
            errors.append(f"CASE_ANSWER_STATUS_INVALID:{cid}")
        for field in ("problem_source", "skill_version", "model", "reasoning"):
            if not isinstance(case[field], str) or not case[field]:
                errors.append(f"CASE_FIELD_TYPE_INVALID:{cid}:{field}")
        if not SHA.fullmatch(str(case["skill_commit"])):
            errors.append(f"CASE_SKILL_COMMIT_INVALID:{cid}")
        if not HEX64.fullmatch(str(case["problem_hash"])):
            errors.append(f"CASE_PROBLEM_HASH_INVALID:{cid}")
        if not isinstance(case["data_hashes"], dict) or any(
            not isinstance(k, str) or not HEX64.fullmatch(str(v))
            for k, v in case["data_hashes"].items()
        ):
            errors.append(f"CASE_DATA_HASH_INVALID:{cid}")
        if any(
            not isinstance(case[k], list)
            for k in ("generalizable_failures", "problem_specific_findings")
        ):
            errors.append(f"CASE_FINDINGS_INVALID:{cid}")
        if cid in old:
            # New annotations may be appended. Every original key/value is immutable,
            # including raw/freeze/terminal/answer evidence, not just a count or ID.
            if any(case.get(k) != v or k not in case for k, v in old[cid].items()):
                errors.append(f"REGISTRY_HISTORY_DRIFT:{cid}")
            continue
        reg = registrations.get(cid)
        if (
            not isinstance(reg, dict)
            or reg.get("schema_version") != "postvalidation-development-registration/v1"
        ):
            errors.append(f"CASE_REGISTRATION_MISSING:{cid}")
            continue
        parent = old.get(reg.get("parent_case_id"), {})
        identity = {
            "case_id": cid,
            "set_type": "DEVELOPMENT",
            "evidence_role": "DEVELOPMENT_AFTER_VALIDATION",
            "independent_problem": False,
            "contamination_status": "KNOWN_PROBLEM_AND_PRIOR_RESULTS",
            "answer_access_status": "SEALED",
            "unlock_time": None,
            "skill_version": "0.2.0-competition-rc9",
        }
        if any(case.get(k) != v or reg.get(k) != v for k, v in identity.items()):
            errors.append(f"CASE_DEVELOPMENT_IDENTITY_INVALID:{cid}")
        if (
            reg.get("phase") != PHASE
            or reg.get("authorization_path")
            != "evals/results/phase-004c6/qualification/proposal.json"
            or parent.get("set_type") != "VALIDATION"
            or parent.get("first_run_status") != "FROZEN"
            or reg.get("parent_terminal_path") != parent.get("terminal_decision")
            or not HEX64.fullmatch(str(reg.get("parent_terminal_sha256", "")))
            or reg.get("parent_case_id") != case.get("parent_case_id")
            or reg.get("parent_terminal_sha256") != case.get("parent_terminal_sha256")
        ):
            errors.append(f"CASE_PARENT_TERMINAL_INVALID:{cid}")
        for field in ("problem_hash", "data_hashes", "skill_commit", "case_root"):
            if reg.get(field) != case.get(field):
                errors.append(f"CASE_REGISTRATION_BINDING_INVALID:{cid}:{field}")
        case_root = reg.get("case_root", "")
        if (
            not isinstance(case_root, str)
            or not case_root.startswith(".cache/pr12-rc9/development/")
            or ".." in Path(case_root).parts
            or case_root in roots
        ):
            errors.append(f"CASE_DEVELOPMENT_ROOT_INVALID:{cid}")
        roots.add(str(case_root))
        budget = reg.get("budget", {})
        if any(
            type(budget.get(k)) is not int or not 1 <= budget[k] <= limit
            for k, limit in (
                ("model_cli_starts", 4),
                ("independent_checker_starts", 4),
                ("final_starts", 1),
            )
        ):
            errors.append(f"CASE_DEVELOPMENT_BUDGET_INVALID:{cid}")
        try:
            status = case["first_run_status"]
            if status == "NOT_STARTED":
                if case["start_time"] is not None or case["freeze_time"] is not None:
                    raise ValueError("unstarted time")
            else:
                start = datetime.fromisoformat(case["start_time"].replace("Z", "+00:00"))
                if start.tzinfo is None:
                    raise ValueError("timezone")
                if status == "IN_PROGRESS" and case["freeze_time"] is not None:
                    raise ValueError("in-progress freeze")
                if status == "FROZEN":
                    freeze = datetime.fromisoformat(case["freeze_time"].replace("Z", "+00:00"))
                    if freeze < start:
                        raise ValueError("reversed time")
                    errors.extend(validate_development_terminal(case, (terminals or {}).get(cid)))
        except (ValueError, TypeError, AttributeError, KeyError):
            errors.append(f"CASE_DEVELOPMENT_LIFECYCLE_INVALID:{cid}")
    for cid in old.keys() - seen:
        errors.append(f"REGISTRY_HISTORY_MISSING:{cid}")
    if registry.get("held_out_reservations") != history.get("held_out_reservations"):
        errors.append("REGISTRY_RESERVATION_DRIFT")
    return sorted(set(errors))


def validate_development_terminal(case: dict[str, Any], terminal: Any) -> list[str]:
    cid = case["case_id"]
    expected = {
        "schema_version": "postvalidation-development-terminal/v1",
        "phase": PHASE,
        "case_id": cid,
        "subject_commit": case["skill_commit"],
        "skill_version": "0.2.0-competition-rc9",
        "independent_validation": False,
        "parent_terminal_sha256": case["parent_terminal_sha256"],
        "decision_id": "DECISION-" + cid,
    }
    if (
        not isinstance(terminal, dict)
        or any(terminal.get(k) != v for k, v in expected.items())
        or terminal.get("independent_validation") is not False
        or terminal.get("status") not in {"SCOPED_DEVELOPMENT_COMPLETE", "FAILED", "INSUFFICIENT"}
        or not terminal.get("question_results")
        or not terminal.get("limitations")
        or case.get("terminal_decision_id") != expected["decision_id"]
    ):
        return [f"CASE_DEVELOPMENT_TERMINAL_TUPLE_INVALID:{cid}"]
    return []


def repository_registry_errors(root: Path, registry: dict[str, Any]) -> list[str]:
    registrations: dict[str, Any] = {}
    terminals: dict[str, Any] = {}
    errors: list[str] = []
    history = historical_registry(root)
    historical_ids = {case["case_id"] for case in history["cases"]}
    for case in registry.get("cases", []):
        if isinstance(case, dict) and case.get("case_id") in historical_ids:
            continue  # Original records are compared in full below.
        binding = case.get("registration") if isinstance(case, dict) else None
        if not binding:
            continue
        try:
            relative = binding["path"]
            path = (root / relative).resolve()
            if not path.is_relative_to(root / "evals/results/phase-004c6"):
                raise ValueError("registration outside authorized evidence root")
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != binding["sha256"]:
                raise ValueError("registration hash")
            reg = json.loads(data)
            parent_path = root / reg["parent_terminal_path"]
            if not parent_path.resolve().is_relative_to(root / "evals/results/phase-004c5"):
                raise ValueError("parent outside historical evidence root")
            old_blob = subprocess.check_output(
                ["git", "show", f"{HISTORY_SUBJECT}:{reg['parent_terminal_path']}"], cwd=root
            )
            if (
                parent_path.read_bytes() != old_blob
                or hashlib.sha256(old_blob).hexdigest() != reg["parent_terminal_sha256"]
            ):
                raise ValueError("parent terminal drift")
            registrations[case["case_id"]] = reg
            if case.get("first_run_status") == "FROZEN":
                binding = case["terminal_decision"]
                expected_path = (
                    f"evals/results/phase-004c6/{case['case_id']}/terminal/decision.json"
                )
                if binding["path"] != expected_path:
                    raise ValueError("child terminal path")
                data = (root / expected_path).read_bytes()
                if hashlib.sha256(data).hexdigest() != binding["sha256"]:
                    raise ValueError("child terminal hash")
                terminals[case["case_id"]] = json.loads(data)
        except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError):
            errors.append(f"CASE_REGISTRATION_HASH_INVALID:{case.get('case_id')}")
    return sorted(set(errors + validate_registry(registry, history, registrations, terminals)))


TERMINALS = {
    "CUMCM-2024-C-VALIDATION-001": (
        "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C",
        "0.2.0-competition-rc4",
        "DECISION-C-TARGET-VALIDATION-004C",
        "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2",
    ),
    "CUMCM-2019-C-VALIDATION-002": (
        "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2",
        "0.2.0-competition-rc5",
        "DECISION-C-TARGET-VALIDATION-004C2",
        None,
    ),
    "CUMCM-2017-C-VALIDATION-003F": (
        "PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4",
        "0.2.0-competition-rc7",
        "DECISION-C-TARGET-VALIDATION-004C4",
        "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5",
    ),
    "CUMCM-2016-C-VALIDATION-004": (
        "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5",
        "0.2.0-competition-rc8",
        "DECISION-C-TARGET-VALIDATION-004C5-2016",
        None,
    ),
    "CUMCM-2015-C-VALIDATION-005": (
        "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5",
        "0.2.0-competition-rc8",
        "DECISION-C-TARGET-VALIDATION-004C5-2015",
        None,
    ),
}


def state_identity_errors(
    state: dict[str, Any], schema: dict[str, Any], history: dict[str, Any]
) -> list[str]:
    errors = (
        ["PROJECT_STATE_SCHEMA_INVALID"]
        if list(Draft202012Validator(schema).iter_errors(state))
        else []
    )
    status = state.get("technical_adjudication_status")
    if status not in {"C_TARGET_VALIDATION_FAILED", "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT"}:
        return errors
    cid = state.get("current_validation_case")
    expected = TERMINALS.get(cid)
    case = next((c for c in history["cases"] if c["case_id"] == cid), {})
    if expected is None or (
        state.get("phase"),
        state.get("active_skill_version"),
        state.get("next_phase_allowed"),
    ) != (expected[0], expected[1], expected[3]):
        errors.append("TERMINAL_PHASE_VERSION_CASE_TUPLE_INVALID")
    if expected is None or expected[2] not in state.get("automated_decision_ids", []):
        errors.append("TERMINAL_DECISION_BINDING_INVALID")
    if status != case.get("validation_decision") or case.get("set_type") != "VALIDATION":
        errors.append("TERMINAL_CASE_OUTCOME_MISMATCH")
    return sorted(set(errors))
