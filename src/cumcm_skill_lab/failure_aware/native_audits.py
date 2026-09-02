"""Build isolated Phase 002D-R1 native Subagent bundles and validate outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, file_sha256, read_json, sha256_json

AUDIT_ROOT = RESULT_ROOT / "subagent_audits"
BUNDLE_ROOT = AUDIT_ROOT / "bundles"
AUDIT_CONTRACT = "contracts/failure_aware_subagent_audit.schema.json"
FIRST_ROUND_ROLES = (
    "failure_attribution_auditor",
    "retry_bias_prosecutor",
    "evidence_scope_statistician",
    "experiment_protocol_auditor",
    "cost_and_stop_auditor",
)
POST_DECISION_ROLE = "failure_aware_decision_auditor"
POST_AUDIT_REMEDIATION_PATHS = frozenset(
    {
        "src/cumcm_skill_lab/failure_aware/retry_bias.py",
        "src/cumcm_skill_lab/failure_aware/slot_matrix.py",
        "evals/results/phase-002d-r1/retry_bias/retry_bias_audit.json",
        "evals/results/phase-002d-r1/slot_outcomes/slot_outcome_matrix.json",
        "evals/results/phase-002d-r1/slot_outcomes/slot_outcome_matrix.csv",
        "evals/results/phase-002d-r1/slot_outcomes/records/CASE-004-ARM-A-R2.json",
        "plans/active/PLAN-0002D-R1-failure-aware-outcomes.md",
    }
)
LEGACY_COMPLETED_PATHS = {
    "plans/active/PLAN-0002D-R1-failure-aware-outcomes.md": (
        "plans/completed/PLAN-0002D-R1-failure-aware-outcomes.md"
    )
}

ROLE_TASKS = {
    "failure_attribution_auditor": [
        "attack each primary classification using only frozen observable evidence",
        (
            "verify the seven policy violations, six HARD-FAIL-003 flags, mixed transport "
            "attempt, two completed exclusions, and every retry"
        ),
        (
            "distinguish model, policy, infrastructure, harness, and unknown outcomes "
            "without identity inference"
        ),
    ],
    "retry_bias_prosecutor": [
        "attack earliest-success selection and search for best-of-N or later-success erasure",
        "verify every retry remains in reliability and cost and the original budget is unchanged",
        "test per-cell caps, post-hoc expansion, and failure-to-zero imputation",
    ],
    "evidence_scope_statistician": [
        (
            "independently recompute quality, reliability, outcome-completeness, and "
            "component-gap scopes"
        ),
        (
            "verify terminal negatives do not fill the quality Gate and infrastructure does "
            "not prove a component gap"
        ),
        "audit all six explicit repeat semantics and the deprecated unscoped repeat_depth",
    ],
    "experiment_protocol_auditor": [
        (
            "audit the frozen cohort, schedule, source evidence, protocol invariants, and "
            "historical immutability"
        ),
        (
            "attack supplemental eligibility and require a new cohort for any prompt, "
            "schema, fixture, scorer, oracle, model, reasoning, or transport change"
        ),
        "verify real starts remain locked before authorization and pre-audit",
    ],
    "cost_and_stop_auditor": [
        "audit attempt, token, elapsed, retry, and unknown-cost accounting",
        "test original elapsed-budget termination and every supplemental stop condition",
        (
            "state measurable value, costs, simplest alternative, and whether more runs are "
            "justified without voting"
        ),
    ],
    "failure_aware_decision_auditor": [
        "audit failure-aware decisions, accepted scopes, route, replay, and post-hoc claim limits",
        (
            "reject identity bias, majority vote, recovery contamination, budget mutation, "
            "or quality/reliability confusion"
        ),
        "return PASS, FAIL, RETEST_REQUIRED, or ABSTAIN without modifying files",
    ],
}


def _resolved_source_path(root: Path, relative: str) -> Path:
    """Resolve the one lifecycle move without changing frozen R1 bundle keys."""
    path = root / relative
    if path.is_file():
        return path
    replacement = LEGACY_COMPLETED_PATHS.get(relative)
    return root / replacement if replacement else path


def _source_evidence_paths(root: Path) -> list[str]:
    classifications = [
        read_json(path)
        for path in sorted((root / RESULT_ROOT / "attempt_classification").glob("*.json"))
    ]
    paths = {
        reference
        for item in classifications
        for reference in item["evidence_refs"]
        if "#" not in reference
    }
    return sorted(paths)


def _common_allowed_paths(root: Path) -> list[str]:
    generated = [
        path.relative_to(root).as_posix()
        for relative in (
            RESULT_ROOT / "attempt_classification",
            RESULT_ROOT / "slot_outcomes/records",
        )
        for path in sorted((root / relative).glob("*.json"))
    ]
    return sorted(
        {
            (RESULT_ROOT / "input_freeze_manifest.json").as_posix(),
            (RESULT_ROOT / "failure_attribution_summary.json").as_posix(),
            (RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.json").as_posix(),
            (RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.csv").as_posix(),
            (RESULT_ROOT / "evidence_scopes/evidence_scope_summary.json").as_posix(),
            (RESULT_ROOT / "retry_bias/retry_bias_audit.json").as_posix(),
            (SOURCE_ROOT / "attempt_ledger.json").as_posix(),
            (SOURCE_ROOT / "budget/frozen_budget.json").as_posix(),
            (SOURCE_ROOT / "cost/cost.json").as_posix(),
            (SOURCE_ROOT / "schedule/schedule.json").as_posix(),
            "rules/dynamic_eval_rules.yaml",
            "rules/evidence_hierarchy.yaml",
            "rules/native_subagent_audit_rules.yaml",
            "rules/pre_adjudication_rules.yaml",
            "rules/phase002d_r1_workflow_rules.yaml",
            AUDIT_CONTRACT,
            "src/cumcm_skill_lab/failure_aware/classification.py",
            "src/cumcm_skill_lab/failure_aware/slot_matrix.py",
            "src/cumcm_skill_lab/failure_aware/evidence_scopes.py",
            "src/cumcm_skill_lab/failure_aware/retry_bias.py",
            "plans/active/PLAN-0002D-R1-failure-aware-outcomes.md",
            *generated,
            *_source_evidence_paths(root),
        }
    )


def _evidence_catalog(root: Path) -> list[str]:
    classifications = [
        read_json(path)
        for path in sorted((root / RESULT_ROOT / "attempt_classification").glob("*.json"))
    ]
    slots = [
        read_json(path)
        for path in sorted((root / RESULT_ROOT / "slot_outcomes/records").glob("*.json"))
    ]
    scope = read_json(root / RESULT_ROOT / "evidence_scopes/evidence_scope_summary.json")
    retry = read_json(root / RESULT_ROOT / "retry_bias/retry_bias_audit.json")
    return sorted(
        {
            "PHASE-002D-R1-INPUT-FREEZE-001",
            "PHASE-002D-R1-FAILURE-ATTRIBUTION-001",
            "PHASE-002D-R1-SLOT-OUTCOME-MATRIX-001",
            scope["scope_summary_id"],
            retry["audit_id"],
            *[item["classification_id"] for item in classifications],
            *[item["slot_id"] for item in slots],
            *[item["attempt_id"] for item in classifications],
        }
    )


def build_first_round_bundles(root: Path) -> dict[str, dict[str, Any]]:
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    allowed_paths = _common_allowed_paths(root)
    source_hashes = {path: file_sha256(_resolved_source_path(root, path)) for path in allowed_paths}
    evidence_catalog = _evidence_catalog(root)
    bundles: dict[str, dict[str, Any]] = {}
    for role in FIRST_ROUND_ROLES:
        body = {
            "schema_version": "1.0.0",
            "bundle_id": f"PHASE-002D-R1-NATIVE-{role.upper()}",
            "role": role,
            "round": "FIRST_ROUND",
            "independent": True,
            "read_only": True,
            "identity_blind": True,
            "peer_output_access": "NONE",
            "peer_outputs_visible": False,
            "expected_conclusion_visible": False,
            "input_freeze_id": freeze["freeze_id"],
            "input_freeze_hash": freeze["manifest_hash"],
            "task": ROLE_TASKS[role],
            "evidence_catalog": evidence_catalog,
            "allowed_file_references": allowed_paths,
            "source_hashes": source_hashes,
            "output_contract": AUDIT_CONTRACT,
            "prohibitions": [
                "no file writes, commits, pushes, or formal-state changes",
                "no peer outputs or expected main-agent conclusion",
                "no web, MCP, nested Codex, API key, or global configuration",
                "no arm-identity lookup, candidate ranking, majority vote, or human technical Gate",
                "no fabricated evidence and no inference beyond cited observable records",
            ],
        }
        bundles[role] = {**body, "bundle_hash": sha256_json(body)}
    return bundles


def check_or_write_first_round_bundles(root: Path, *, check: bool) -> dict[str, Any]:
    if check and all((root / BUNDLE_ROOT / f"{role}.json").is_file() for role in FIRST_ROUND_ROLES):
        return validate_frozen_first_round_bundles(root)
    bundles = build_first_round_bundles(root)
    errors: list[str] = []
    for role, bundle in bundles.items():
        errors.extend(check_or_write(root / BUNDLE_ROOT / f"{role}.json", bundle, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "roles": list(FIRST_ROUND_ROLES),
        "bundle_hashes": {role: bundle["bundle_hash"] for role, bundle in bundles.items()},
    }


def validate_frozen_first_round_bundles(root: Path) -> dict[str, Any]:
    """Validate immutable pre-remediation bundles without regenerating their inputs."""
    errors: list[str] = []
    bundle_hashes: dict[str, str] = {}
    remediation_drift: set[str] = set()
    closure_path = root / RESULT_ROOT / "adversarial_tests/finding_closure.json"
    closure_pass = (
        closure_path.is_file()
        and read_json(closure_path).get("all_serious_findings_closed") is True
    )
    for role in FIRST_ROUND_ROLES:
        path = root / BUNDLE_ROOT / f"{role}.json"
        if not path.is_file():
            errors.append(f"SUBAGENT_BUNDLE_MISSING:{role}")
            continue
        bundle = read_json(path)
        body = dict(bundle)
        recorded_hash = body.pop("bundle_hash", None)
        bundle_hashes[role] = recorded_hash
        if sha256_json(body) != recorded_hash:
            errors.append(f"SUBAGENT_BUNDLE_HASH_MISMATCH:{role}")
        for relative, expected in bundle["source_hashes"].items():
            target = _resolved_source_path(root, relative)
            if not target.is_file():
                errors.append(f"SUBAGENT_BUNDLE_SOURCE_MISSING:{role}:{relative}")
            elif file_sha256(target) != expected:
                remediation_drift.add(relative)
    unapproved = remediation_drift - POST_AUDIT_REMEDIATION_PATHS
    if unapproved:
        errors.extend(f"SUBAGENT_BUNDLE_UNAPPROVED_DRIFT:{path}" for path in sorted(unapproved))
    if remediation_drift and not closure_pass:
        errors.append("SUBAGENT_BUNDLE_REMEDIATION_WITHOUT_TEST_CLOSURE")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "roles": list(FIRST_ROUND_ROLES),
        "bundle_hashes": bundle_hashes,
        "post_audit_remediation_drift": sorted(remediation_drift),
        "all_serious_findings_closed": closure_pass,
    }


def build_decision_auditor_bundle(root: Path) -> dict[str, Any]:
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    generated_paths = [
        path.relative_to(root).as_posix()
        for relative in (
            RESULT_ROOT / "attempt_classification",
            RESULT_ROOT / "slot_outcomes/records",
            RESULT_ROOT / "automated_decisions",
        )
        for path in sorted((root / relative).glob("*.json"))
    ]
    allowed_paths = sorted(
        {
            (RESULT_ROOT / "input_freeze_manifest.json").as_posix(),
            (RESULT_ROOT / "failure_attribution_summary.json").as_posix(),
            (RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.json").as_posix(),
            (RESULT_ROOT / "evidence_scopes/evidence_scope_summary.json").as_posix(),
            (RESULT_ROOT / "evidence_scopes/quality_sufficiency.json").as_posix(),
            (RESULT_ROOT / "evidence_scopes/reliability_sufficiency.json").as_posix(),
            (RESULT_ROOT / "retry_bias/retry_bias_audit.json").as_posix(),
            (RESULT_ROOT / "adversarial_tests/test_evidence.json").as_posix(),
            (RESULT_ROOT / "adversarial_tests/finding_closure.json").as_posix(),
            (RESULT_ROOT / "supplemental/authorization.json").as_posix(),
            (RESULT_ROOT / "supplemental/authorization_pre_audit.json").as_posix(),
            (RESULT_ROOT / "supplemental/budget.json").as_posix(),
            (RESULT_ROOT / "supplemental/status.json").as_posix(),
            (RESULT_ROOT / "replay/replay.json").as_posix(),
            (
                RESULT_ROOT / "subagent_audits/decision_repair_rounds/finding_closure.json"
            ).as_posix(),
            (RESULT_ROOT / "subagent_audits/decision_repair_rounds/test_evidence.json").as_posix(),
            AUDIT_CONTRACT,
            "src/cumcm_skill_lab/failure_aware/replay.py",
            "tests/unit/test_phase002d_r1_replay.py",
            *generated_paths,
            *[
                (RESULT_ROOT / f"subagent_audits/{role}.json").as_posix()
                for role in FIRST_ROUND_ROLES
            ],
        }
    )
    decisions = [
        read_json(path)
        for path in sorted((root / RESULT_ROOT / "automated_decisions").glob("*.json"))
    ]
    audits = [
        read_json(root / RESULT_ROOT / f"subagent_audits/{role}.json") for role in FIRST_ROUND_ROLES
    ]
    evidence = read_json(root / RESULT_ROOT / "adversarial_tests/test_evidence.json")
    quality = read_json(root / RESULT_ROOT / "evidence_scopes/quality_sufficiency.json")
    reliability = read_json(root / RESULT_ROOT / "evidence_scopes/reliability_sufficiency.json")
    replay = read_json(root / RESULT_ROOT / "replay/replay.json")
    repair_evidence = read_json(
        root / RESULT_ROOT / "subagent_audits/decision_repair_rounds/test_evidence.json"
    )
    repair_closure = read_json(
        root / RESULT_ROOT / "subagent_audits/decision_repair_rounds/finding_closure.json"
    )
    catalog = sorted(
        {
            freeze["freeze_id"],
            "PHASE-002D-R1-FAILURE-ATTRIBUTION-001",
            "PHASE-002D-R1-SLOT-OUTCOME-MATRIX-001",
            "PHASE-002D-R1-EVIDENCE-SCOPES-001",
            "PHASE-002D-R1-RETRY-BIAS-AUDIT-001",
            "DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1",
            quality["record_id"],
            reliability["record_id"],
            replay["replay_id"],
            repair_closure["closure_id"],
            *[item["audit_id"] for item in audits],
            *[item["test_id"] for item in evidence["evidence"]],
            *[item["test_id"] for item in repair_evidence["evidence"]],
            *[item["automated_decision"]["decision_id"] for item in decisions],
        }
    )
    body = {
        "schema_version": "1.0.0",
        "bundle_id": "PHASE-002D-R1-NATIVE-FAILURE_AWARE_DECISION_AUDITOR",
        "role": POST_DECISION_ROLE,
        "round": "POST_DECISION",
        "independent": True,
        "read_only": True,
        "identity_blind": True,
        "peer_output_access": "FROZEN_PREDECESSORS_ONLY",
        "peer_outputs_visible": True,
        "expected_conclusion_visible": False,
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "task": ROLE_TASKS[POST_DECISION_ROLE],
        "required_checks": [
            "failure misattribution",
            "retry bias",
            "recovery contamination",
            "budget mutation",
            "identity bias",
            "majority vote",
            "hardcoding",
            "quality/reliability scope confusion",
            "post-hoc positive claim",
            "supplemental overreach",
            "next-phase route",
            "accepted scope",
            "replay readiness",
        ],
        "evidence_catalog": catalog,
        "allowed_file_references": allowed_paths,
        "source_hashes": {path: file_sha256(root / path) for path in allowed_paths},
        "output_contract": AUDIT_CONTRACT,
        "prohibitions": [
            "no file writes, commits, pushes, or formal-state changes",
            "no expected main-agent conclusion",
            "no web, MCP, nested Codex, API key, or global configuration",
            "no arm-identity lookup, candidate ranking, majority vote, or human technical Gate",
            "no fabricated evidence and no inference beyond cited observable records",
        ],
    }
    return {**body, "bundle_hash": sha256_json(body)}


def check_or_write_decision_auditor_bundle(root: Path, *, check: bool) -> dict[str, Any]:
    bundle = build_decision_auditor_bundle(root)
    errors = check_or_write(root / BUNDLE_ROOT / f"{POST_DECISION_ROLE}.json", bundle, check=check)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "role": POST_DECISION_ROLE,
        "bundle_hash": bundle["bundle_hash"],
    }


def audit_path(root: Path, role: str) -> Path:
    return root / AUDIT_ROOT / f"{role}.json"


def validate_audit(root: Path, audit: dict[str, Any], *, role: str) -> list[str]:
    errors: list[str] = []
    validator = Draft202012Validator(read_json(root / AUDIT_CONTRACT))
    errors.extend(f"SUBAGENT_SCHEMA:{role}:{item.message}" for item in validator.iter_errors(audit))
    bundle_path = root / BUNDLE_ROOT / f"{role}.json"
    if not bundle_path.is_file():
        return [*errors, f"SUBAGENT_BUNDLE_MISSING:{role}"]
    bundle = read_json(bundle_path)
    for field in ("role", "bundle_id", "bundle_hash"):
        expected = role if field == "role" else bundle[field]
        if audit.get(field) != expected:
            errors.append(f"SUBAGENT_{field.upper()}_MISMATCH:{role}")
    body = dict(audit)
    recorded_hash = body.pop("output_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append(f"SUBAGENT_OUTPUT_HASH_MISMATCH:{role}")
    if audit.get("peer_output_access") != (
        "FROZEN_PREDECESSORS_ONLY" if role == POST_DECISION_ROLE else "NONE"
    ):
        errors.append(f"SUBAGENT_PEER_ACCESS_INVALID:{role}")
    allowed_evidence = set(bundle["evidence_catalog"])
    allowed_files = set(bundle["allowed_file_references"])
    finding_ids = {item.get("finding_id") for item in audit.get("findings", [])}
    for finding in audit.get("findings", []):
        unknown_evidence = sorted(set(finding.get("evidence_refs", [])) - allowed_evidence)
        if unknown_evidence:
            errors.append(f"SUBAGENT_EVIDENCE_REF_INVALID:{role}:{','.join(unknown_evidence)}")
        for reference in finding.get("file_references", []):
            path = reference.split(":", 1)[0]
            if path not in allowed_files or not _resolved_source_path(root, path).is_file():
                errors.append(f"SUBAGENT_FILE_REF_INVALID:{role}:{reference}")
            if role in FIRST_ROUND_ROLES and "subagent_audits/" in path:
                errors.append(f"SUBAGENT_PEER_REFERENCE:{role}:{reference}")
    blockers = set(audit.get("blockers", []))
    if not blockers.issubset(finding_ids):
        errors.append(f"SUBAGENT_BLOCKER_REF_INVALID:{role}")
    if audit.get("verdict") == "PASS" and blockers:
        errors.append(f"SUBAGENT_PASS_WITH_BLOCKER:{role}")
    return sorted(set(errors))


def validate_first_round(root: Path) -> list[str]:
    errors: list[str] = []
    for role in FIRST_ROUND_ROLES:
        path = audit_path(root, role)
        if not path.is_file():
            errors.append(f"SUBAGENT_OUTPUT_MISSING:{role}")
            continue
        errors.extend(validate_audit(root, read_json(path), role=role))
    return sorted(set(errors))


def check_or_seal_first_round_audits(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    audit_hashes: dict[str, str] = {}
    for role in FIRST_ROUND_ROLES:
        path = audit_path(root, role)
        if not path.is_file():
            errors.append(f"SUBAGENT_OUTPUT_MISSING:{role}")
            continue
        audit = read_json(path)
        body = dict(audit)
        body.pop("output_hash", None)
        sealed = {**body, "output_hash": sha256_json(body)}
        audit_hashes[role] = sealed["output_hash"]
        errors.extend(check_or_write(path, sealed, check=check))
        errors.extend(validate_audit(root, sealed, role=role))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "audit_count": len(audit_hashes),
        "audit_hashes": audit_hashes,
    }


def check_or_seal_decision_auditor(root: Path, *, check: bool) -> dict[str, Any]:
    """Seal and validate the single post-decision native audit output."""
    role = POST_DECISION_ROLE
    path = audit_path(root, role)
    if not path.is_file():
        return {
            "status": "FAIL",
            "errors": [f"SUBAGENT_OUTPUT_MISSING:{role}"],
            "role": role,
            "audit_hash": None,
        }
    audit = read_json(path)
    body = dict(audit)
    body.pop("output_hash", None)
    sealed = {**body, "output_hash": sha256_json(body)}
    errors = check_or_write(path, sealed, check=check)
    errors.extend(validate_audit(root, sealed, role=role))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "role": role,
        "verdict": sealed.get("verdict"),
        "audit_hash": sealed["output_hash"],
    }
