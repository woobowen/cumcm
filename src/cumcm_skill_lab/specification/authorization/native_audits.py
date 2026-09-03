"""Build identity-blind read-only bundles and validate native authorization audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    sha256_json,
)

from .models import CREATED_AT, RESULT_ROOT

INPUT_ROOT = RESULT_ROOT / "subagent_inputs"
OUTPUT_ROOT = RESULT_ROOT / "subagent_outputs"
RAW_OUTPUT_ROOT = OUTPUT_ROOT / "raw"
FINAL_AUDIT_PATH = RESULT_ROOT / "authorization_audit/audit.json"
FIRST_ROUND_ROLES = (
    "authorization_dependency_prosecutor",
    "shadow_scope_security_auditor",
    "protocol_cost_dissent_auditor",
)
FINAL_ROLE = "final_shadow_authorization_auditor"
COMMON_PATHS = (
    "evals/results/phase-002d-r2a/input_freeze_manifest.json",
    "evals/results/phase-002d-r2a/authorization_dependency_graph.json",
    "specifications/shadow_prototype_scope.yaml",
    "evals/results/phase-002d-r2/automated_decisions/shadow_prototype_authorization.json",
    "evals/results/phase-002d-r2/decision_audit/audit.json",
    "evals/results/phase-002d-r2/replay/replay.json",
    "rules/phase002d_r2a_workflow_rules.yaml",
    "contracts/subagent_audit.schema.json",
)
ROLE_PATHS = {
    "authorization_dependency_prosecutor": COMMON_PATHS
    + (
        "contracts/authorization_dependency_graph.schema.json",
        "contracts/project_state.schema.json",
        "state/project_state.json",
        "evals/results/phase-002d-r2/automated_decisions/component_specification_freeze.json",
        "evals/results/phase-002d-r2/automated_decisions/interaction_contract.json",
        "evals/results/phase-002d-r2/automated_decisions/architecture_candidate_set.json",
        "evals/results/phase-002d-r2/automated_decisions/prospective_benchmark_freeze.json",
        "evals/results/phase-002d-r2/automated_decisions/threshold_policy_freeze.json",
    ),
    "shadow_scope_security_auditor": COMMON_PATHS
    + (
        "contracts/shadow_prototype_scope.schema.json",
        "evals/prospective/phase-002d-r2/access_policy.yaml",
        "evals/prospective/phase-002d-r2/sealed_manifest.json",
        "evals/prospective/phase-002d-r2/manifests/candidate_visible_manifest.json",
        "evals/results/phase-002d-r2/implementation_embargo.json",
        "specifications/architectures/architecture_candidate_set.yaml",
        ".gitignore",
        "state/project_state.json",
    ),
    "protocol_cost_dissent_auditor": COMMON_PATHS
    + (
        "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml",
        "evals/prospective/phase-002d-r2/budget_policy.yaml",
        "evals/prospective/phase-002d-r2/threshold_policy.yaml",
        "evals/prospective/phase-002d-r2/metric_registry.yaml",
        "evals/prospective/phase-002d-r2/ablation_policy.yaml",
        "evals/prospective/phase-002d-r2/case_catalog.yaml",
        "specifications/architectures/architecture_candidate_set.yaml",
    ),
}


def build_audit_bundle(root: Path, role: str) -> dict[str, Any]:
    if role not in ROLE_PATHS:
        raise ValueError(f"UNKNOWN_FIRST_ROUND_AUTHORIZATION_ROLE:{role}")
    paths = ROLE_PATHS[role]
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "bundle_id": f"PHASE-002D-R2A-{role.upper().replace('_', '-')}-001",
        "role": role,
        "round": "FIRST_ROUND",
        "created_at": CREATED_AT,
        "allowed_paths": list(paths),
        "path_hashes": {path: file_sha256(root / path) for path in paths},
        "constraints": {
            "read_only": True,
            "peer_output_access": "NONE",
            "writes_allowed": False,
            "nested_codex_allowed": False,
            "web_allowed": False,
            "mcp_allowed": False,
            "api_allowed": False,
            "majority_vote_allowed": False,
            "expected_conclusion_visible": False,
            "abstention_allowed": True,
            "fabricated_evidence_allowed": False,
        },
    }
    body["bundle_hash"] = sha256_json(body)
    return body


def check_or_write_first_round_bundles(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    hashes: dict[str, str] = {}
    for role in FIRST_ROUND_ROLES:
        bundle = build_audit_bundle(root, role)
        errors.extend(check_or_write(root / INPUT_ROOT / f"{role}.json", bundle, check=check))
        hashes[role] = bundle["bundle_hash"]
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "hashes": hashes}


def recorded_audit_bundle(root: Path, role: str) -> dict[str, Any]:
    """Load a historical first-round bundle without re-reading remediated live inputs."""
    if role not in FIRST_ROUND_ROLES:
        raise ValueError(f"UNKNOWN_FIRST_ROUND_AUTHORIZATION_ROLE:{role}")
    bundle = read_json(root / INPUT_ROOT / f"{role}.json")
    body = dict(bundle)
    recorded_hash = body.pop("bundle_hash", None)
    if sha256_json(body) != recorded_hash:
        raise ValueError(f"R2A_RECORDED_AUDIT_BUNDLE_HASH_MISMATCH:{role}")
    return bundle


def validate_subagent_output(
    root: Path,
    value: dict[str, Any],
    role: str,
    *,
    final_bundle_path: Path | None = None,
) -> list[str]:
    errors = [
        f"R2A_SUBAGENT_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(
            read_json(root / "contracts/subagent_audit.schema.json")
        ).iter_errors(value)
    ]
    if value.get("role") != role:
        errors.append("R2A_SUBAGENT_ROLE_MISMATCH")
    if role in ROLE_PATHS:
        bundle = recorded_audit_bundle(root, role)
        if (
            value.get("bundle_id") != bundle["bundle_id"]
            or value.get("bundle_hash") != bundle["bundle_hash"]
        ):
            errors.append("R2A_SUBAGENT_BUNDLE_MISMATCH")
    elif role == FINAL_ROLE:
        bundle_path = final_bundle_path or INPUT_ROOT / f"{FINAL_ROLE}.json"
        bundle = read_json(root / bundle_path)
        bundle_body = dict(bundle)
        recorded_bundle_hash = bundle_body.pop("bundle_hash", None)
        if sha256_json(bundle_body) != recorded_bundle_hash:
            errors.append("R2A_FINAL_AUDIT_BUNDLE_HASH_MISMATCH")
        if value.get("bundle_id") != bundle.get("bundle_id") or value.get(
            "bundle_hash"
        ) != bundle.get("bundle_hash"):
            errors.append("R2A_SUBAGENT_BUNDLE_MISMATCH")
        if value.get("round") != "POST_DECISION":
            errors.append("R2A_FINAL_AUDIT_ROUND_MISMATCH")
        if value.get("peer_output_access") != "FROZEN_PREDECESSORS_ONLY":
            errors.append("R2A_FINAL_AUDIT_PEER_VISIBILITY_MISMATCH")
    body = dict(value)
    recorded = body.pop("output_hash", None)
    if sha256_json(body) != recorded:
        errors.append("R2A_SUBAGENT_OUTPUT_HASH_MISMATCH")
    finding_ids = [item.get("finding_id") for item in value.get("findings", [])]
    if len(finding_ids) != len(set(finding_ids)):
        errors.append("R2A_SUBAGENT_FINDING_ID_DUPLICATE")
    if any(
        item.get("severity") in {"BLOCKER", "ERROR"} and not item.get("required_test")
        for item in value.get("findings", [])
    ):
        errors.append("R2A_SUBAGENT_SERIOUS_FINDING_WITHOUT_TEST")
    return sorted(set(errors))


def normalize_subagent_output(value: dict[str, Any]) -> dict[str, Any]:
    """Replace the transport placeholder with a canonical semantic output hash."""
    normalized = dict(value)
    normalized.pop("output_hash", None)
    normalized["output_hash"] = sha256_json(normalized)
    return normalized


def check_or_write_normalized_first_round_outputs(root: Path, *, check: bool) -> dict[str, Any]:
    """Preserve raw transports and derive schema-valid, hash-bound audit records."""
    errors: list[str] = []
    hashes: dict[str, str] = {}
    for role in FIRST_ROUND_ROLES:
        raw_path = root / RAW_OUTPUT_ROOT / f"{role}.json"
        if not raw_path.exists():
            errors.append(f"R2A_SUBAGENT_RAW_OUTPUT_MISSING:{role}")
            continue
        normalized = normalize_subagent_output(read_json(raw_path))
        validation_errors = validate_subagent_output(root, normalized, role)
        errors.extend(f"{role}:{item}" for item in validation_errors)
        errors.extend(check_or_write(root / OUTPUT_ROOT / f"{role}.json", normalized, check=check))
        hashes[role] = normalized["output_hash"]
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "hashes": hashes}


def check_or_write_normalized_final_output(root: Path, *, check: bool) -> dict[str, Any]:
    """Preserve final-auditor transport and publish its canonical audit record."""
    errors: list[str] = []
    historical_hashes: dict[str, str] = {}
    for attempt in ("001", "002"):
        raw_attempt_path = root / RAW_OUTPUT_ROOT / f"{FINAL_ROLE}-attempt-{attempt}.json"
        bundle_attempt_path = INPUT_ROOT / f"{FINAL_ROLE}-attempt-{attempt}.json"
        if not raw_attempt_path.exists():
            continue
        normalized_attempt = normalize_subagent_output(read_json(raw_attempt_path))
        errors.extend(
            f"attempt-{attempt}:{item}"
            for item in validate_subagent_output(
                root,
                normalized_attempt,
                FINAL_ROLE,
                final_bundle_path=bundle_attempt_path,
            )
        )
        errors.extend(
            check_or_write(
                root / OUTPUT_ROOT / f"{FINAL_ROLE}-attempt-{attempt}.json",
                normalized_attempt,
                check=check,
            )
        )
        historical_hashes[attempt] = normalized_attempt["output_hash"]
    raw_path = root / RAW_OUTPUT_ROOT / f"{FINAL_ROLE}.json"
    if not raw_path.exists():
        return {
            "status": "FAIL",
            "errors": errors + ["R2A_FINAL_AUDIT_RAW_OUTPUT_MISSING"],
            "audit_id": None,
            "result": "NOT_RUN",
            "checkpoint_hash": None,
            "historical_attempt_hashes": historical_hashes,
        }
    normalized = normalize_subagent_output(read_json(raw_path))
    errors.extend(validate_subagent_output(root, normalized, FINAL_ROLE))
    errors.extend(
        check_or_write(root / OUTPUT_ROOT / f"{FINAL_ROLE}.json", normalized, check=check)
    )
    errors.extend(check_or_write(root / FINAL_AUDIT_PATH, normalized, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "audit_id": normalized.get("audit_id"),
        "result": normalized.get("verdict"),
        "checkpoint_hash": normalized.get("output_hash"),
        "finding_count": len(normalized.get("findings", [])),
        "blocker_count": len(normalized.get("blockers", [])),
        "historical_attempt_hashes": historical_hashes,
    }
