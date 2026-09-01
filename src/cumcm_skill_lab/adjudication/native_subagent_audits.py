"""Build and validate read-only native Subagent audit bundles and outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import check_or_write, file_sha256, read_json, sha256_json
from .pre_adjudication import FREEZE_PATH, PRE_RECORD_PATH, SUFFICIENCY_PATH, resolve_policy

RESULT_ROOT = Path("evals/results/phase-002c/subagent_audits")
FIRST_ROUND_ROLES = (
    "evidence_sufficiency_auditor",
    "adjudication_policy_prosecutor",
    "dissent_and_cost_auditor",
    "reproducibility_auditor",
)
POST_DECISION_ROLE = "automated_decision_auditor"

ROLE_TASKS = {
    "evidence_sufficiency_auditor": [
        "independently recompute balanced complete cases and repeat depth",
        "verify recovery failed superseded and NOT_RUN exclusions",
        "verify cross-arm task input hashes and frozen thresholds",
        "do not compare or rank candidates",
    ],
    "adjudication_policy_prosecutor": [
        "attack short-circuit ordering for post-hoc rule changes or hidden evidence",
        "provide counterexamples tests pass conditions and a verdict",
        "verify every inherited hard Gate and threshold remains unchanged",
    ],
    "dissent_and_cost_auditor": [
        "attack the value of further upstream evaluation clean-room work and four mechanisms",
        "state measurable benefit token time and maintenance costs",
        "give stop conditions and the simplest scaffold alternative",
    ],
    "reproducibility_auditor": [
        "audit freeze policy evidence code report and transport hashes",
        "detect hardcoded results self-reference or non-replayable state",
        "verify historical transport evidence is preserved but not ranked",
    ],
    "automated_decision_auditor": [
        "audit decisions against frozen rules tests first-round audits and replay",
        "reject hardcoding threshold mutation recovery ranking votes or invalid routing",
        "return PASS FAIL or RETEST_REQUIRED without modifying files",
    ],
}


def build_first_round_bundles(root: Path) -> dict[str, dict[str, Any]]:
    freeze = read_json(root / FREEZE_PATH)
    sufficiency = read_json(root / SUFFICIENCY_PATH)
    pre_record = read_json(root / PRE_RECORD_PATH)
    policy = resolve_policy(root)
    recovery = read_json(root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json")
    historical_transport = read_json(root / "evals/results/phase-002b/recovery_manifest.json")
    evidence_items = _evidence_items(root)
    allowed_files = [
        FREEZE_PATH.as_posix(),
        SUFFICIENCY_PATH.as_posix(),
        PRE_RECORD_PATH.as_posix(),
        "adjudication/configs/phase-002c.yaml",
        "adjudication/policies/phase-002c.yaml",
        "adjudication/policies/phase-002a.yaml",
        "rules/pre_adjudication_rules.yaml",
        "rules/native_subagent_audit_rules.yaml",
        "contracts/subagent_audit.schema.json",
        "evals/results/phase-002a/eligibility/classification.json",
        "evals/results/phase-002a/recovery_gap_evidence/recovery.json",
        "evals/results/phase-002b/recovery_manifest.json",
        "src/cumcm_skill_lab/adjudication/evidence_sufficiency.py",
        "src/cumcm_skill_lab/adjudication/pre_adjudication.py",
        "src/cumcm_skill_lab/adjudication/short_circuit.py",
        "src/cumcm_skill_lab/adjudication/phase_routing.py",
        "src/cumcm_skill_lab/adjudication/phase002c_records.py",
        "src/cumcm_skill_lab/adjudication/phase002c_reporting.py",
        "src/cumcm_skill_lab/report_generation.py",
        "state/project_state.json",
        "WORKFLOW.md",
        *[item["run_path"] for item in evidence_items],
    ]
    catalog = sorted(
        {
            freeze["freeze_id"],
            sufficiency["sufficiency_id"],
            pre_record["record_id"],
            "ELIGIBILITY-PHASE-002A",
            "RECOVERY-EXCLUSION-PHASE-002A",
            "PHASE-AUTOMATED-ADJUDICATION-RECOVERY-002B",
            *[item["evidence_id"] for item in evidence_items],
        }
    )
    bundles: dict[str, dict[str, Any]] = {}
    for role in FIRST_ROUND_ROLES:
        body = {
            "schema_version": "1.0.0",
            "bundle_id": f"PHASE-002C-NATIVE-{role.upper()}",
            "role": role,
            "round": "FIRST_ROUND",
            "read_only": True,
            "peer_output_access": "NONE",
            "input_freeze_id": freeze["freeze_id"],
            "input_freeze_hash": freeze["freeze_hash"],
            "policy": policy,
            "sufficiency": sufficiency,
            "pre_adjudication": pre_record,
            "evidence_items": evidence_items,
            "recovery_summary": {
                "policy": recovery["policy"],
                "count": recovery["count"],
                "ranking_eligible_count": sum(
                    item["ranking_eligible"] is True for item in recovery["records"]
                ),
            },
            "historical_transport": {
                "status": historical_transport["status"],
                "terminal_failure_class": historical_transport["terminal_failure_class"],
                "phase002b_model_starts": historical_transport["phase002b_model_starts"],
                "completed_roles": historical_transport["completed_roles"],
            },
            "task": ROLE_TASKS[role],
            "evidence_catalog": catalog,
            "allowed_file_references": allowed_files,
            "output_contract": "contracts/subagent_audit.schema.json",
            "prohibitions": [
                "no file writes",
                "no peer outputs",
                "no candidate ranking or majority vote",
                "no nested Codex App Server SDK API or API key",
                "no global configuration changes",
                "no formal state transition",
            ],
        }
        body["bundle_hash"] = sha256_json(body)
        bundles[role] = body
    return bundles


def write_first_round_bundles(root: Path, *, check: bool) -> list[str]:
    errors: list[str] = []
    for role, bundle in build_first_round_bundles(root).items():
        path = root / RESULT_ROOT / "bundles" / f"{role}.json"
        errors.extend(check_or_write(path, bundle, check=check))
    return errors


def build_decision_auditor_bundle(root: Path) -> dict[str, Any]:
    freeze = read_json(root / FREEZE_PATH)
    decisions = [
        read_json(path)
        for path in sorted((root / "evals/results/phase-002c/automated_decisions").glob("*.json"))
    ]
    first_round = [read_json(audit_path(root, role)) for role in FIRST_ROUND_ROLES]
    tests = read_json(root / "evals/results/phase-002c/adversarial_tests/derived_tests.json")
    replay = read_json(root / "evals/results/phase-002c/replay/pre_audit_replay.json")
    allowed_files = [
        FREEZE_PATH.as_posix(),
        SUFFICIENCY_PATH.as_posix(),
        PRE_RECORD_PATH.as_posix(),
        "evals/results/phase-002c/adversarial_tests/derived_tests.json",
        "evals/results/phase-002c/replay/pre_audit_replay.json",
        *[
            path.relative_to(root).as_posix()
            for path in sorted(
                (root / "evals/results/phase-002c/automated_decisions").glob("*.json")
            )
        ],
        *[audit_path(root, role).relative_to(root).as_posix() for role in FIRST_ROUND_ROLES],
        "adjudication/policies/phase-002c.yaml",
        "rules/pre_adjudication_rules.yaml",
        "rules/native_subagent_audit_rules.yaml",
        "src/cumcm_skill_lab/adjudication/phase002c_records.py",
        "src/cumcm_skill_lab/adjudication/phase_routing.py",
    ]
    catalog = sorted(
        {
            freeze["freeze_id"],
            *[item["decision_id"] for item in decisions],
            *[item["audit_id"] for item in first_round],
            *[item["test_id"] for item in tests["tests"]],
            replay["replay_id"],
        }
    )
    body = {
        "schema_version": "1.0.0",
        "bundle_id": "PHASE-002C-NATIVE-AUTOMATED-DECISION-AUDITOR",
        "role": POST_DECISION_ROLE,
        "round": "POST_DECISION",
        "read_only": True,
        "peer_output_access": "FROZEN_PREDECESSORS_ONLY",
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["freeze_hash"],
        "task": ROLE_TASKS[POST_DECISION_ROLE],
        "decisions": decisions,
        "first_round_audits": first_round,
        "adversarial_tests": tests,
        "pre_audit_replay": replay,
        "evidence_catalog": catalog,
        "allowed_file_references": allowed_files,
        "output_contract": "contracts/subagent_audit.schema.json",
        "prohibitions": [
            "no file writes",
            "no majority vote",
            "no threshold mutation",
            "no recovery ranking",
            "no nested Codex App Server SDK API or API key",
            "no formal state transition",
        ],
    }
    body["bundle_hash"] = sha256_json(body)
    return body


def write_decision_auditor_bundle(root: Path, *, check: bool) -> list[str]:
    return check_or_write(
        root / RESULT_ROOT / "bundles/automated_decision_auditor.json",
        build_decision_auditor_bundle(root),
        check=check,
    )


def audit_path(root: Path, role: str) -> Path:
    return root / RESULT_ROOT / f"{role}.json"


def validate_audit(root: Path, audit: dict[str, Any], *, role: str) -> list[str]:
    errors: list[str] = []
    try:
        Draft202012Validator(read_json(root / "contracts/subagent_audit.schema.json")).validate(
            audit
        )
    except Exception as exc:
        return [f"SUBAGENT_SCHEMA_INVALID:{role}:{type(exc).__name__}"]
    if audit.get("role") != role:
        errors.append(f"SUBAGENT_ROLE_MISMATCH:{role}")
    bundle_file = root / RESULT_ROOT / "bundles" / f"{role}.json"
    if not bundle_file.is_file():
        errors.append(f"SUBAGENT_BUNDLE_MISSING:{role}")
        return errors
    bundle = read_json(bundle_file)
    if audit.get("bundle_id") != bundle["bundle_id"]:
        errors.append(f"SUBAGENT_BUNDLE_ID_MISMATCH:{role}")
    if audit.get("bundle_hash") != bundle["bundle_hash"]:
        errors.append(f"SUBAGENT_BUNDLE_HASH_MISMATCH:{role}")
    body = dict(audit)
    recorded_hash = body.pop("output_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append(f"SUBAGENT_OUTPUT_HASH_MISMATCH:{role}")
    allowed_evidence = set(bundle["evidence_catalog"])
    allowed_files = set(bundle["allowed_file_references"])
    for finding in audit.get("findings", []):
        unknown_evidence = sorted(set(finding["evidence_refs"]) - allowed_evidence)
        if unknown_evidence:
            errors.append(f"SUBAGENT_EVIDENCE_REF_INVALID:{role}:{','.join(unknown_evidence)}")
        for reference in finding["file_references"]:
            relative = reference.split(":", 1)[0]
            if relative not in allowed_files or not (root / relative).is_file():
                errors.append(f"SUBAGENT_FILE_REF_INVALID:{role}:{reference}")
            if role in FIRST_ROUND_ROLES and "subagent_audits/" in relative:
                errors.append(f"SUBAGENT_PEER_REFERENCE:{role}:{reference}")
    finding_ids = {item["finding_id"] for item in audit.get("findings", [])}
    if not set(audit.get("blockers", [])).issubset(finding_ids):
        errors.append(f"SUBAGENT_BLOCKER_REF_INVALID:{role}")
    return errors


def validate_first_round(root: Path) -> list[str]:
    errors: list[str] = []
    for role in FIRST_ROUND_ROLES:
        path = audit_path(root, role)
        if not path.is_file():
            errors.append(f"SUBAGENT_OUTPUT_MISSING:{role}")
            continue
        errors.extend(validate_audit(root, read_json(path), role=role))
    return errors


def build_derived_test_ledger(root: Path) -> dict[str, Any]:
    tests: list[dict[str, Any]] = []
    for role in FIRST_ROUND_ROLES:
        audit = read_json(audit_path(root, role))
        for finding in audit["findings"]:
            if finding["severity"] != "BLOCKER":
                continue
            tests.append(blocker_test_record(audit["audit_id"], finding))
    ledger = {
        "schema_version": "1.0.0",
        "ledger_id": "PHASE-002C-SUBAGENT-BLOCKER-TESTS",
        "tests": tests,
        "all_testable_blockers_resolved": not any(item["status"] == "PENDING" for item in tests),
    }
    ledger["content_hash"] = sha256_json(ledger)
    return ledger


def blocker_test_record(audit_id: str, finding: dict[str, Any]) -> dict[str, Any]:
    testable = finding["testability"] == "TESTABLE"
    resolved = finding["status"] == "RESOLVED"
    status = "PASS" if testable and resolved else "PENDING" if testable else "NON_TESTABLE_CLAIM"
    body = {
        "test_id": finding["required_test"] or f"TEST-{finding['finding_id']}",
        "source_audit_id": audit_id,
        "finding_id": finding["finding_id"],
        "testability": finding["testability"],
        "pass_condition": finding["pass_condition"],
        "status": status,
        "evidence_refs": finding["evidence_refs"],
        "result_hash": None,
    }
    if status == "PASS":
        body["result_hash"] = sha256_json(
            {
                "finding_id": finding["finding_id"],
                "required_test": finding["required_test"],
                "pass_condition": finding["pass_condition"],
                "status": status,
            }
        )
    return body


def _evidence_items(root: Path) -> list[dict[str, Any]]:
    from .evidence_sufficiency import collect_evidence_items

    return collect_evidence_items(root)


def audit_file_hash(root: Path, role: str) -> str:
    return file_sha256(audit_path(root, role))
