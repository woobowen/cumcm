"""Convert R2A authorization attacks into deterministic, fail-closed evidence."""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
)

from .bindings import (
    build_synthetic_replay,
    build_synthetic_seal,
    validate_replay_binding,
    validate_supersession_binding,
)
from .dependency_graph import verify_dependency_graph
from .models import DEPENDENCY_PATH, RESULT_ROOT
from .native_audits import FIRST_ROUND_ROLES, OUTPUT_ROOT
from .scope import SCOPE_PATH, validate_scope_value

FINDINGS_PATH = RESULT_ROOT / "adversarial_findings/findings.json"
CLOSURE_PATH = RESULT_ROOT / "adversarial_findings/closure.json"
REQUESTS_PATH = RESULT_ROOT / "test_requests/requests.json"
EVIDENCE_PATH = RESULT_ROOT / "test_evidence/evidence.json"
CREATED_AT = "2026-09-03T03:30:00+08:00"

TEST_IDS = {
    "R2A-AUTHDEP-001": "R2A-DET-AUTHDEP-M7M8-001",
    "R2A-AUTHDEP-002": "R2A-DET-STATE-GATE-001",
    "R2A-AUTHDEP-003": "R2A-DET-REPLAY-INPUT-BINDING-001",
    "R2A-AUTHDEP-004": "R2A-DET-SUPERSESSION-001",
    "R2A-AUTHDEP-005": "R2A-DET-DAG-SEMANTICS-001",
    "R2A-SEC-001": "R2A-SEC-MANIFEST-BINDING-001",
    "R2A-SEC-002": "R2A-SEC-VAULT-CAPABILITY-001",
    "R2A-SEC-003": "R2A-SEC-PATH-CONFINEMENT-001",
    "R2A-SEC-004": "R2A-SEC-THIRD-PARTY-DENY-001",
    "R2A-SEC-005": "R2A-SEC-CALLER-ISOLATION-001",
    "R2A-SEC-006": "R2A-SEC-RESULT-SCOPE-001",
    "R2A-SEC-007": "R2A-SEC-ROLLBACK-001",
    "R2A-PCD-001": "R2A-DET-PCD-SCHEDULE-001",
    "R2A-PCD-002": "R2A-DET-PCD-COST-001",
    "R2A-PCD-003": "R2A-DET-PCD-DISCRIMINATION-001",
}

FAIL_CLOSED_FINDINGS = {
    "R2A-SEC-002",
    "R2A-SEC-003",
    "R2A-SEC-004",
    "R2A-SEC-005",
    "R2A-SEC-006",
    "R2A-SEC-007",
    "R2A-PCD-001",
    "R2A-PCD-002",
    "R2A-PCD-003",
}


def _rehash(value: dict[str, Any], field: str) -> None:
    body = copy.deepcopy(value)
    body.pop(field, None)
    value[field] = sha256_json(body)


def _dependency_order_is_explicit(root: Path) -> bool:
    graph = read_json(root / DEPENDENCY_PATH)
    audit = read_json(root / "evals/results/phase-002d-r2/decision_audit/audit.json")
    replay_is_evidence = any("replay" in item for item in audit.get("audit_evidence_refs", []))
    return (
        replay_is_evidence
        and graph["graph_purpose"] == "R2A_AUTHORIZATION_EVALUATION_PRECEDENCE"
        and graph["edge_semantics"]
        == "PREREQUISITE_VALIDATION_ORDER_OVER_ALREADY_FROZEN_ATOMIC_ARTIFACTS"
        and graph["historical_evidence_references_create_edges"] is False
        and verify_dependency_graph(root, graph) == []
    )


def _state_bypass_is_rejected(root: Path) -> bool:
    state = read_json(root / "state/project_state.json")
    state["technical_adjudication_status"] = "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE"
    state["next_phase_allowed"] = "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"
    schema = read_json(root / "contracts/project_state.schema.json")
    return bool(list(Draft202012Validator(schema).iter_errors(state)))


def _replay_binding_mutations_are_rejected(root: Path) -> bool:
    seal = build_synthetic_seal(root)
    replay = build_synthetic_replay(root, seal)
    if validate_replay_binding(root, replay, seal):
        return False
    mutations = (
        ("input_freeze_hash", "6" * 64, "R2A_REPLAY_INPUT_FREEZE_HASH_MISMATCH"),
        ("active_decision_hash", "7" * 64, "R2A_REPLAY_ACTIVE_DECISION_HASH_MISMATCH"),
        (
            "final_audit_checkpoint_hash",
            "8" * 64,
            "R2A_REPLAY_FINAL_AUDIT_CHECKPOINT_HASH_MISMATCH",
        ),
    )
    for field, value, expected in mutations:
        candidate = copy.deepcopy(replay)
        candidate[field] = value
        _rehash(candidate, "replay_hash")
        if expected not in validate_replay_binding(root, candidate, seal):
            return False
    return True


def _supersession_mutations_are_rejected(root: Path) -> bool:
    seal = build_synthetic_seal(root)
    if validate_supersession_binding(root, seal):
        return False
    mutations: list[tuple[Callable[[dict[str, Any]], None], str]] = [
        (
            lambda value: value.update(
                {"authorization_id": "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2"}
            ),
            "R2A_SEAL_REUSES_HISTORICAL_DECISION_ID",
        ),
        (
            lambda value: value.update(
                {
                    "artifact_path": (
                        "evals/results/phase-002d-r2/automated_decisions/"
                        "shadow_prototype_authorization.json"
                    )
                }
            ),
            "R2A_SEAL_OVERWRITES_HISTORICAL_ARTIFACT",
        ),
        (
            lambda value: value["supersedes"].update({"decision_hash": "9" * 64}),
            "R2A_SEAL_SUPERSESSION_DECISION_HASH_MISMATCH",
        ),
        (
            lambda value: value["supersedes"].update({"file_sha256": "a" * 64}),
            "R2A_SEAL_SUPERSESSION_FILE_SHA256_MISMATCH",
        ),
    ]
    for mutate, expected in mutations:
        candidate = copy.deepcopy(seal)
        mutate(candidate)
        _rehash(candidate, "authorization_hash")
        if expected not in validate_supersession_binding(root, candidate):
            return False
    return True


def _dag_mutations_are_rejected(root: Path) -> bool:
    graph = read_json(root / DEPENDENCY_PATH)
    mutations: list[tuple[Callable[[dict[str, Any]], None], str, bool]] = [
        (
            lambda value: value["nodes"].append(copy.deepcopy(value["nodes"][0])),
            "PHASE002D_R2A_DEPENDENCY_DUPLICATE_NODE",
            True,
        ),
        (
            lambda value: value["edges"].append(
                {"source": "L0-COMPONENT-SPECS", "target": "L7-MISSING"}
            ),
            "PHASE002D_R2A_DEPENDENCY_DANGLING_ENDPOINT",
            True,
        ),
        (
            lambda value: value["nodes"][0].update({"level": 1}),
            "PHASE002D_R2A_DEPENDENCY_NODE_LEVEL_MISMATCH",
            True,
        ),
        (
            lambda value: value["edges"].append(
                {"source": "L7-FORMAL-STATE-TRANSITION", "target": "L4-R2A-ELIGIBILITY"}
            ),
            "PHASE002D_R2A_DEPENDENCY_CYCLE",
            True,
        ),
        (
            lambda value: value["edges"].__setitem__(
                slice(None),
                [
                    item
                    for item in value["edges"]
                    if not (
                        item["source"] == "L7-R2A-AUTHORIZATION-SEAL"
                        and item["target"] == "L7-R2A-FINAL-REPLAY"
                    )
                ],
            ),
            "PHASE002D_R2A_DEPENDENCY_REQUIRED_EDGE_MISSING",
            True,
        ),
        (
            lambda value: value.update({"graph_purpose": "HISTORICAL_PROVENANCE"}),
            "PHASE002D_R2A_DEPENDENCY_EDGE_SEMANTICS_INVALID",
            True,
        ),
        (
            lambda value: value.update({"input_freeze_hash": "b" * 64}),
            "PHASE002D_R2A_DEPENDENCY_GRAPH_HASH_MISMATCH",
            False,
        ),
    ]
    for mutate, expected, rehash in mutations:
        candidate = copy.deepcopy(graph)
        mutate(candidate)
        if rehash:
            _rehash(candidate, "graph_hash")
        if expected not in verify_dependency_graph(root, candidate):
            return False
    return True


def _public_manifest_uses_canonical_semantic_hashes(root: Path) -> bool:
    benchmark = root / "evals/prospective/phase-002d-r2"
    sealed = read_json(benchmark / "sealed_manifest.json")
    values = {
        "access_policy.yaml": read_yaml(benchmark / "access_policy.yaml"),
        "manifests/candidate_visible_manifest.json": read_json(
            benchmark / "manifests/candidate_visible_manifest.json"
        ),
    }
    return all(
        sealed["public_artifact_hashes"][relative] == sha256_json(value)
        for relative, value in values.items()
    )


def _scope(root: Path) -> dict[str, Any]:
    return read_yaml(root / SCOPE_PATH)


def _scope_is_valid(root: Path) -> bool:
    value = _scope(root)
    return validate_scope_value(root, value) == []


def evaluate_closures(root: Path) -> dict[str, tuple[bool, str]]:
    scope = _scope(root)
    future = scope["future_runtime_gate"]
    stages = scope["execution_stages"]
    path = scope["path_confinement"]
    dependency = scope["dependency_policy"]
    callability = scope["callability_policy"]
    output = scope["output_policy"]
    rollback = scope["rollback"]
    stage2_denied = (
        stages["model_stage2"] == "PROHIBITED_PENDING_NEW_FROZEN_AUTHORIZATION"
        and stages["model_starts_authorized"] == 0
        and set(future["required_before_model_stage2"])
        == {"R2A-PCD-001", "R2A-PCD-002", "R2A-PCD-003"}
    )
    values = {
        "R2A-AUTHDEP-001": _dependency_order_is_explicit(root),
        "R2A-AUTHDEP-002": _state_bypass_is_rejected(root),
        "R2A-AUTHDEP-003": _replay_binding_mutations_are_rejected(root),
        "R2A-AUTHDEP-004": _supersession_mutations_are_rejected(root),
        "R2A-AUTHDEP-005": _dag_mutations_are_rejected(root),
        "R2A-SEC-001": _public_manifest_uses_canonical_semantic_hashes(root),
        "R2A-SEC-002": _scope_is_valid(root)
        and future["current_status"] == "NOT_SATISFIED_EXECUTION_PROHIBITED"
        and future["actual_runtime_evidence_present"] is False
        and stages["hidden_benchmark_use_authorized"] is False,
        "R2A-SEC-003": _scope_is_valid(root)
        and path["status"] == "UNVERIFIED_BLOCKS_FILE_WRITES_AND_EXECUTION"
        and all(
            path[field]
            for field in (
                "canonical_root_required",
                "no_follow_required",
                "shared_inode_forbidden",
                "rename_swap_defense_required",
                "pre_post_protected_hash_required",
            )
        ),
        "R2A-SEC-004": _scope_is_valid(root)
        and dependency["status"] == "UNVERIFIED_BLOCKS_FILE_WRITES_AND_EXECUTION"
        and dependency["project_owned_allowlist_required"]
        and dependency["isolated_interpreter_no_site_packages_required"]
        and not any(
            dependency[field]
            for field in ("dynamic_import_allowed", "subprocess_allowed", "network_allowed")
        ),
        "R2A-SEC-005": _scope_is_valid(root)
        and callability["status"] == "UNVERIFIED_BLOCKS_EXECUTION"
        and callability["shadow_only_runner_capability_required"]
        and not any(
            callability[field]
            for field in (
                "production_registry_entry_allowed",
                "formal_skill_import_allowed",
                "normal_cli_dispatch_allowed",
                "production_subprocess_call_allowed",
            )
        ),
        "R2A-SEC-006": _scope_is_valid(root)
        and output["formal_artifact_kinds_allowed"] == []
        and output["allowed_suffixes"] == [".json"]
        and output["formal_discovery_allowed"] is False
        and output["links_allowed"] is False
        and output["executable_allowed"] is False,
        "R2A-SEC-007": _scope_is_valid(root)
        and rollback["disposable_workspace_required"]
        and rollback["all_refs_absence_verification_required"]
        and not any(
            rollback[field]
            for field in ("git_tracking_allowed", "git_commit_allowed", "git_push_allowed")
        ),
        "R2A-PCD-001": _scope_is_valid(root) and stage2_denied,
        "R2A-PCD-002": _scope_is_valid(root)
        and stage2_denied
        and future["unknown_cost_disposition"] == "EVIDENCE_INSUFFICIENT",
        "R2A-PCD-003": _scope_is_valid(root) and stage2_denied,
    }
    details = {
        "R2A-AUTHDEP-001": (
            "DAG explicitly models R2A evaluation precedence; historical audit evidence "
            "references are content bindings, not inferred graph edges"
        ),
        "R2A-AUTHDEP-002": (
            "complete-state bypass without candidate, active decision, final audit, and replay "
            "bindings is rejected"
        ),
        "R2A-AUTHDEP-003": (
            "replay mutations to input freeze, active decision, or final-audit checkpoint are "
            "rejected"
        ),
        "R2A-AUTHDEP-004": (
            "new ID/path and exact immutable predecessor ID/decision hash/file hash are mandatory"
        ),
        "R2A-AUTHDEP-005": (
            "duplicate nodes, dangling endpoints, level errors, cycles, missing edges, semantic "
            "drift, and stale graph hashes are rejected"
        ),
        "R2A-SEC-001": (
            "sealed public-artifact fields are canonical semantic hashes and both questioned "
            "bindings recompute exactly"
        ),
        "R2A-SEC-002": (
            "OS isolation remains unverified and all prototype execution/hidden-benchmark use is "
            "denied until the future sentinel capability gate passes"
        ),
        "R2A-SEC-003": (
            "file writes and execution remain denied until canonical-root, no-follow, inode, "
            "rename-swap, and protected-hash gates pass"
        ),
        "R2A-SEC-004": (
            "file writes and execution remain denied until project-owned dependency provenance "
            "and isolated-interpreter gates pass"
        ),
        "R2A-SEC-005": (
            "execution remains denied until a non-production shadow-only runner capability is "
            "verified"
        ),
        "R2A-SEC-006": (
            "outputs remain denied until content-addressed JSON-only shadow-origin enforcement "
            "rejects formal artifact kinds"
        ),
        "R2A-SEC-007": (
            "future artifacts must stay disposable, untracked, uncommitted, unpushed, and absent "
            "from every ref after rollback"
        ),
        "R2A-PCD-001": (
            "model Stage 2 has zero authorized starts until an exact frozen schedule proves all "
            "tuples and caps"
        ),
        "R2A-PCD-002": (
            "model Stage 2 is denied and unknown cost deterministically routes to "
            "EVIDENCE_INSUFFICIENT"
        ),
        "R2A-PCD-003": (
            "model Stage 2 is denied until a frozen W1/K1 discriminant-to-case/metric matrix passes"
        ),
    }
    return {key: (value, details[key]) for key, value in values.items()}


def _serious_findings(root: Path) -> list[tuple[str, dict[str, Any]]]:
    values: list[tuple[str, dict[str, Any]]] = []
    for role in FIRST_ROUND_ROLES:
        audit = read_json(root / OUTPUT_ROOT / f"{role}.json")
        values.extend(
            (role, finding)
            for finding in audit["findings"]
            if finding["severity"] in {"BLOCKER", "ERROR"}
        )
    return sorted(values, key=lambda item: item[1]["finding_id"])


def _schema_errors(schema: dict[str, Any], values: list[dict[str, Any]]) -> list[str]:
    return [
        (
            f"{value.get('finding_id', value.get('test_id'))}:"
            f"{'/'.join(map(str, error.absolute_path))}:{error.message}"
        )
        for value in values
        for error in Draft202012Validator(schema).iter_errors(value)
    ]


def synthesize_adversarial_closure(root: Path, *, check: bool) -> dict[str, Any]:
    evaluations = evaluate_closures(root)
    findings: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    closures: list[dict[str, Any]] = []
    for role, item in _serious_findings(root):
        finding_id = item["finding_id"]
        test_id = TEST_IDS[finding_id]
        passed, observed = evaluations[finding_id]
        is_fail_closed = finding_id in FAIL_CLOSED_FINDINGS
        disposition = (
            "CLOSED_BY_FAIL_CLOSED_SCOPE_RESTRICTION"
            if is_fail_closed
            else (
                "CLOSED_AS_CANONICAL_HASH_SEMANTICS_FALSE_POSITIVE"
                if finding_id == "R2A-SEC-001"
                else "CLOSED_BY_DETERMINISTIC_VALIDATOR"
            )
        )
        refs = list(item["file_references"])
        findings.append(
            {
                "finding_id": finding_id,
                "role": role,
                "target": item["target"],
                "severity": item["severity"],
                "claim_attacked": item["statement"],
                "attack": item["statement"],
                "counterexample": item.get("counterexample") or item["required_test"],
                "evidence": refs,
                "required_test": test_id,
                "pass_condition": observed,
                "fail_condition": f"deterministic closure predicate for {finding_id} is false",
                "confidence": 1.0,
                "unresolved": not passed,
                "recommended_action": (
                    "retain the fail-closed gate; do not treat underlying runtime or empirical "
                    "risk as proven"
                    if is_fail_closed
                    else "retain the deterministic regression and re-adjudicate on mutation"
                ),
                "statement": item["statement"],
                "evidence_refs": list(item["evidence_refs"]),
                "testability": "TESTABLE",
                "status": "CLOSED" if passed else "TEST_REQUESTED",
            }
        )
        requests.append(
            {
                "test_id": test_id,
                "finding_id": finding_id,
                "target": item["target"],
                "inputs": refs,
                "oracle": "evaluate_closures deterministic predicate",
                "command_or_procedure": "pytest -q tests/unit/test_phase002d_r2a_adversarial.py",
                "expected_result": observed,
                "pass_condition": observed,
                "fail_condition": f"deterministic closure predicate for {finding_id} is false",
                "artifacts": refs,
                "required_evidence": [
                    "pytest node PASS",
                    "hash-bound R2A closure artifacts",
                    "explicit fail-closed disposition for unverified future evidence",
                ],
                "timeout": 60,
                "reproducibility": "DETERMINISTIC",
                "status": "PASSED" if passed else "PENDING",
            }
        )
        hashes = {
            relative: file_sha256(root / relative)
            for relative in refs
            if "benchmark-vault" not in relative and (root / relative).is_file()
        }
        evidence.append(
            {
                "test_id": test_id,
                "finding_id": finding_id,
                "status": "PASSED" if passed else "FAILED",
                "observed_result": observed,
                "oracle_result": passed,
                "command_or_procedure": "pytest -q tests/unit/test_phase002d_r2a_adversarial.py",
                "artifact_hashes": hashes,
                "started_at": CREATED_AT,
                "completed_at": CREATED_AT,
            }
        )
        closures.append(
            {
                "finding_id": finding_id,
                "test_id": test_id,
                "test_passed": passed,
                "disposition": disposition,
                "underlying_risk_resolved": not is_fail_closed,
                "underlying_risk_status": "UNVERIFIED" if is_fail_closed else "RESOLVED",
                "authorization_effect": (
                    "RISKY_OPERATION_PROHIBITED_UNTIL_FUTURE_TEST_PASSES"
                    if is_fail_closed
                    else "CURRENT_AUTHORIZATION_EVIDENCE_VALIDATED"
                ),
            }
        )
    closure: dict[str, Any] = {
        "schema_version": "1.0.0",
        "created_at": CREATED_AT,
        "serious_finding_count": len(closures),
        "closed_serious_finding_count": sum(item["test_passed"] for item in closures),
        "unresolved_serious_findings": [
            item["finding_id"] for item in closures if not item["test_passed"]
        ],
        "all_serious_findings_closed_for_bounded_authorization": all(
            item["test_passed"] for item in closures
        ),
        "underlying_future_risks_are_not_promoted_to_verified_facts": True,
        "majority_vote_used": False,
        "closures": closures,
    }
    closure["closure_hash"] = sha256_json(closure)
    errors: list[str] = []
    errors.extend(
        _schema_errors(read_json(root / "contracts/adversarial_finding.schema.json"), findings)
    )
    errors.extend(_schema_errors(read_json(root / "contracts/test_request.schema.json"), requests))
    errors.extend(_schema_errors(read_json(root / "contracts/test_evidence.schema.json"), evidence))
    if not closure["all_serious_findings_closed_for_bounded_authorization"]:
        errors.extend(
            f"R2A_UNCLOSED_SERIOUS_FINDING:{item}"
            for item in closure["unresolved_serious_findings"]
        )
    outputs = {
        FINDINGS_PATH: {"schema_version": "1.0.0", "findings": findings},
        CLOSURE_PATH: closure,
        REQUESTS_PATH: {"schema_version": "1.0.0", "test_requests": requests},
        EVIDENCE_PATH: {"schema_version": "1.0.0", "test_evidence": evidence},
    }
    for relative, value in outputs.items():
        errors.extend(check_or_write(root / relative, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "finding_count": len(findings),
        "test_request_count": len(requests),
        "passed_count": sum(item["status"] == "PASSED" for item in evidence),
        "failed_count": sum(item["status"] != "PASSED" for item in evidence),
        "unresolved": closure["unresolved_serious_findings"],
        "closure_hash": closure["closure_hash"],
    }


__all__ = [
    "CLOSURE_PATH",
    "EVIDENCE_PATH",
    "FINDINGS_PATH",
    "REQUESTS_PATH",
    "TEST_IDS",
    "evaluate_closures",
    "synthesize_adversarial_closure",
]
