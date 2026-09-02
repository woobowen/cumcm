"""Deterministic Phase 002D-R2 specification and protocol decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    read_json,
    sha256_json,
)

from .adversarial_closure import synthesize
from .architecture_validator import SPECIFICATION as ARCHITECTURE_PATH
from .architecture_validator import validate_architecture_candidates
from .benchmark_integrity import validate_prospective_benchmark
from .component_validator import SPEC_ROOT, validate_component_specifications
from .implementation_embargo import verify_embargo
from .interaction_validator import SPECIFICATION as INTERACTION_PATH
from .interaction_validator import validate_component_interactions
from .models import COMPONENT_IDS, CREATED_AT, FREEZE_ID, RESULT_ROOT, verify_input_freeze
from .protocol_validator import PROTOCOL_PATH, validate_protocol
from .provenance_validator import validate_clean_room_provenance
from .threshold_validator import THRESHOLD_PATH, validate_thresholds
from .vault_manifest import check_benchmark_vault

DECISION_ROOT = RESULT_ROOT / "automated_decisions"
DECISION_FILES = {
    "DECISION-COMPONENT-SPECIFICATION-FREEZE-002D-R2": ("component_specification_freeze.json"),
    "DECISION-INTERACTION-CONTRACT-002D-R2": "interaction_contract.json",
    "DECISION-ARCHITECTURE-CANDIDATE-SET-002D-R2": "architecture_candidate_set.json",
    "DECISION-PROSPECTIVE-BENCHMARK-FREEZE-002D-R2": "prospective_benchmark_freeze.json",
    "DECISION-THRESHOLD-POLICY-FREEZE-002D-R2": "threshold_policy_freeze.json",
    "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2": ("shadow_prototype_authorization.json"),
}
SHADOW_DECISION_ID = "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2"
R2_ROUTE = "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL"


def _audit_context(root: Path) -> tuple[list[str], list[str]]:
    findings = read_json(root / RESULT_ROOT / "adversarial_findings/findings.json")["findings"]
    evidence = read_json(root / RESULT_ROOT / "test_evidence/evidence.json")["test_evidence"]
    return (
        sorted(item["finding_id"] for item in findings),
        sorted(item["test_id"] for item in evidence if item["status"] == "PASSED"),
    )


def _common(
    root: Path,
    *,
    decision_id: str,
    decision_type: str,
    target_ids: list[str],
    sufficient: bool,
) -> dict[str, Any]:
    findings, tests = _audit_context(root)
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "target_ids": target_ids,
        "evidence_freeze_id": FREEZE_ID,
        "policy_version": "phase002d-r2/1.0.0",
        "hard_gate_status": "PASS" if sufficient else "FAIL",
        "evidence_sufficiency": "SUFFICIENT" if sufficient else "INSUFFICIENT",
        "eligible_evidence": [],
        "excluded_evidence": [
            "AGENT_VOTES",
            "HUMAN_TECHNICAL_GATE",
            "HISTORICAL_BENCHMARK_ANSWERS",
            "HIDDEN_VAULT_VALUES",
            "UPSTREAM_EXECUTABLE_CONTENT",
            "PROTOTYPE_OR_MODEL_RESULTS",
        ],
        "judge_decisions": [],
        "dissent_findings": findings,
        "tests": tests,
        "meta_adjudication": "DETERMINISTIC_SPECIFICATION_POLICY_ENGINE_NO_VOTE",
        "decision_audit": "PENDING:PHASE002D_R2_DECISION_AUDITOR",
        "rejected_scope": [],
        "retest_requirements": [],
        "stale_dependencies": [],
        "confidence": 1.0,
        "next_phase_allowed": None,
        "created_at": CREATED_AT,
    }


def _finalize_core(core: dict[str, Any]) -> dict[str, Any]:
    value = dict(core)
    value["replay_hash"] = "0" * 64
    value["replay_hash"] = sha256_json(
        {key: item for key, item in value.items() if key != "replay_hash"}
    )
    return value


def _wrap(
    core: dict[str, Any],
    *,
    phase_scope: str | None,
    phase_scope_source: str,
    authorization: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "automated_decision_contract": "contracts/automated_decision.schema.json",
        "automated_decision": _finalize_core(core),
        "phase_scope": phase_scope,
        "phase_scope_source": phase_scope_source,
        "majority_vote_used": False,
        "human_technical_gate_used": False,
        "architecture_selected": False,
        "formal_skill_modified": False,
        "prototype_executed": False,
        "model_or_api_evidence_used": False,
    }
    if authorization is not None:
        body["authorization"] = authorization
    return {**body, "decision_hash": sha256_json(body)}


def _shadow_authorization(
    architecture_ids: list[str], prerequisites: dict[str, bool]
) -> dict[str, Any]:
    accepted = all(prerequisites.values())
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "authorization_id": SHADOW_DECISION_ID,
        "decision": "AUTOMATED_ACCEPTED" if accepted else "RETEST_REQUIRED",
        "accepted_scope": "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY" if accepted else None,
        "architecture_ids": architecture_ids,
        "prerequisites": prerequisites,
        "next_phase_allowed": (
            "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION" if accepted else R2_ROUTE
        ),
        "phase003_prohibited": True,
        "formal_skill_modification_allowed": False,
        "prototype_execution_in_r2": False,
    }
    return {**body, "authorization_hash": sha256_json(body)}


def build_decisions(root: Path) -> list[dict[str, Any]]:
    historical_ok = not verify_input_freeze(root)
    component = validate_component_specifications(root)
    interaction = validate_component_interactions(root)
    architecture = validate_architecture_candidates(root)
    benchmark = validate_prospective_benchmark(root)
    vault = check_benchmark_vault(root)
    threshold = validate_thresholds(root)
    protocol = validate_protocol(root)
    provenance = validate_clean_room_provenance(root, check=True)
    embargo_ok = not verify_embargo(root)
    closure = synthesize(root, check=True)

    component_ok = historical_ok and component["status"] == "PASS"
    core = _common(
        root,
        decision_id="DECISION-COMPONENT-SPECIFICATION-FREEZE-002D-R2",
        decision_type="COMPONENTS",
        target_ids=list(COMPONENT_IDS),
        sufficient=component_ok,
    )
    core.update(
        {
            "eligible_evidence": [
                f"{SPEC_ROOT.as_posix()}/{component_id}.yaml" for component_id in COMPONENT_IDS
            ],
            "decision": "AUTOMATED_ACCEPTED" if component_ok else "AUTOMATED_REJECTED",
            "reason_codes": [
                "FOUR_COMPONENT_SPECIFICATIONS_SCHEMA_VALID",
                "SPECIFICATION_SCOPE_ONLY_NO_IMPLEMENTATION",
            ]
            if component_ok
            else ["COMPONENT_SPECIFICATION_GATE_FAILED"],
            "accepted_scope": "SPECIFICATION_ONLY" if component_ok else "NONE",
            "component_results": [
                {
                    "mechanism_id": component_id,
                    "decision": "AUTOMATED_ACCEPTED" if component_ok else "AUTOMATED_REJECTED",
                    "accepted_scope": "SPECIFICATION_ONLY" if component_ok else "NONE",
                    "reason_codes": [
                        "SPECIFICATION_FROZEN",
                        "IMPLEMENTATION_NOT_AUTHORIZED",
                    ],
                    "evidence_refs": [
                        f"{SPEC_ROOT.as_posix()}/{component_id}.yaml",
                        "evals/results/phase-002d-r2/provenance/role_chain.json",
                    ],
                    "required_tests": [f"R2-DET-COMPONENT:{component_id}"],
                    "maintenance_cost": "MEDIUM",
                }
                for component_id in COMPONENT_IDS
            ],
            "rejected_scope": ["IMPLEMENTATION_READY", "INTEGRATED", "PRODUCTION_READY"],
        }
    )
    decisions = [
        _wrap(
            core,
            phase_scope="SPECIFICATION_FROZEN" if component_ok else None,
            phase_scope_source="contracts/component_specification.schema.json",
        )
    ]

    interaction_ok = historical_ok and interaction["status"] == "PASS"
    core = _common(
        root,
        decision_id="DECISION-INTERACTION-CONTRACT-002D-R2",
        decision_type="RECOVERY_POLICY",
        target_ids=["PHASE-002D-R2-COMPONENT-INTERACTION-001"],
        sufficient=interaction_ok,
    )
    core.update(
        {
            "eligible_evidence": [INTERACTION_PATH.as_posix()],
            "decision": "AUTOMATED_ACCEPTED" if interaction_ok else "AUTOMATED_REJECTED",
            "reason_codes": ["SINGLE_TRUTH_INTERACTION_CONTRACT_VALID"]
            if interaction_ok
            else ["INTERACTION_CONTRACT_GATE_FAILED"],
            "accepted_scope": "SPECIFICATION_ONLY" if interaction_ok else "NONE",
            "rejected_scope": ["DIRECT_STATE_ADVANCE", "SECOND_STATE_TRUTH", "SECOND_SKILL"],
        }
    )
    decisions.append(
        _wrap(
            core,
            phase_scope="SPECIFICATION_FROZEN" if interaction_ok else None,
            phase_scope_source="contracts/component_interaction.schema.json",
        )
    )

    architecture_ok = historical_ok and architecture["status"] == "PASS"
    core = _common(
        root,
        decision_id="DECISION-ARCHITECTURE-CANDIDATE-SET-002D-R2",
        decision_type="ARCHITECTURE",
        target_ids=architecture["candidate_ids"],
        sufficient=architecture_ok,
    )
    core.update(
        {
            "eligible_evidence": [ARCHITECTURE_PATH.as_posix()],
            "decision": "AUTOMATED_ACCEPTED" if architecture_ok else "AUTOMATED_REJECTED",
            "reason_codes": ["CANDIDATE_SET_FROZEN_WITH_BASELINE_NO_SELECTION"]
            if architecture_ok
            else ["ARCHITECTURE_CANDIDATE_SET_GATE_FAILED"],
            "accepted_scope": "POLICY_ONLY" if architecture_ok else "NONE",
            "rejected_scope": ["ARCHITECTURE_SELECTION", "BASE_SELECTION", "PHASE_003"],
        }
    )
    decisions.append(
        _wrap(
            core,
            phase_scope="CANDIDATE_SET_FROZEN" if architecture_ok else None,
            phase_scope_source="contracts/architecture_candidate_set.schema.json",
        )
    )

    benchmark_ok = historical_ok and benchmark["status"] == "PASS" and vault["status"] == "PASS"
    core = _common(
        root,
        decision_id="DECISION-PROSPECTIVE-BENCHMARK-FREEZE-002D-R2",
        decision_type="EVIDENCE_SUFFICIENCY",
        target_ids=["PHASE-002D-R2-PROSPECTIVE-BENCHMARK-001"],
        sufficient=benchmark_ok,
    )
    core.update(
        {
            "eligible_evidence": [
                "evals/prospective/phase-002d-r2/sealed_manifest.json",
                "evals/prospective/phase-002d-r2/manifests/separation_report.json",
            ],
            "decision": "AUTOMATED_ACCEPTED" if benchmark_ok else "AUTOMATED_REJECTED",
            "reason_codes": ["PROSPECTIVE_SEALED_BENCHMARK_VALID_AND_VAULT_IGNORED"]
            if benchmark_ok
            else ["PROSPECTIVE_BENCHMARK_GATE_FAILED"],
            "accepted_scope": "POLICY_ONLY" if benchmark_ok else "NONE",
            "rejected_scope": ["HISTORICAL_ANSWER_USE", "CANDIDATE_VISIBLE_ORACLE"],
        }
    )
    decisions.append(
        _wrap(
            core,
            phase_scope="BENCHMARK_FROZEN" if benchmark_ok else None,
            phase_scope_source="contracts/sealed_benchmark_manifest.schema.json",
        )
    )

    threshold_ok = historical_ok and threshold["status"] == "PASS" and protocol["status"] == "PASS"
    core = _common(
        root,
        decision_id="DECISION-THRESHOLD-POLICY-FREEZE-002D-R2",
        decision_type="RECOVERY_POLICY",
        target_ids=["PHASE-002D-R2-THRESHOLDS-001"],
        sufficient=threshold_ok,
    )
    core.update(
        {
            "eligible_evidence": [THRESHOLD_PATH.as_posix(), PROTOCOL_PATH.as_posix()],
            "decision": "AUTOMATED_ACCEPTED" if threshold_ok else "AUTOMATED_REJECTED",
            "reason_codes": ["PROSPECTIVE_NONCOMPENSATORY_POLICY_FROZEN_BEFORE_RESULTS"]
            if threshold_ok
            else ["THRESHOLD_OR_PROTOCOL_GATE_FAILED"],
            "accepted_scope": "POLICY_ONLY" if threshold_ok else "NONE",
            "rejected_scope": ["CANDIDATE_INFORMED_THRESHOLD", "POST_HOC_ABLATION"],
        }
    )
    decisions.append(
        _wrap(
            core,
            phase_scope="POLICY_FROZEN" if threshold_ok else None,
            phase_scope_source="contracts/threshold_policy.schema.json",
        )
    )

    prerequisites = {
        "component_specs": component_ok,
        "interaction": interaction_ok,
        "candidate_set": architecture_ok,
        "benchmark": benchmark_ok,
        "thresholds": threshold_ok,
        "embargo": historical_ok and embargo_ok,
        "provenance": historical_ok and provenance["status"] == "PASS",
        "blocker_tests": historical_ok and closure["status"] == "PASS",
        # These are deliberately false in the M7 decision snapshot. The decision must be frozen
        # before the independent M8 audit and replay that evaluate it.
        "decision_auditor": False,
        "replay": False,
    }
    authorization = _shadow_authorization(architecture["candidate_ids"], prerequisites)
    shadow_ok = authorization["decision"] == "AUTOMATED_ACCEPTED"
    core = _common(
        root,
        decision_id=SHADOW_DECISION_ID,
        decision_type="RECOVERY_POLICY",
        target_ids=architecture["candidate_ids"],
        sufficient=shadow_ok,
    )
    core.update(
        {
            "eligible_evidence": [item for item, passed in prerequisites.items() if passed],
            "decision": authorization["decision"],
            "reason_codes": [
                f"PREREQUISITE_PENDING:{item}"
                for item, passed in prerequisites.items()
                if not passed
            ]
            or ["ALL_SHADOW_AUTHORIZATION_PREREQUISITES_PASS"],
            "accepted_scope": "POLICY_ONLY" if shadow_ok else "NONE",
            "rejected_scope": [
                "FORMAL_SKILL_IMPLEMENTATION",
                "INTEGRATION",
                "PRODUCTION",
                "DIRECT_REUSE",
                "PHASE_003",
            ],
            "retest_requirements": [item for item, passed in prerequisites.items() if not passed],
            "next_phase_allowed": authorization["next_phase_allowed"],
        }
    )
    decisions.append(
        _wrap(
            core,
            phase_scope=authorization["accepted_scope"],
            phase_scope_source="contracts/shadow_prototype_authorization.schema.json",
            authorization=authorization,
        )
    )
    return decisions


def validate_decisions(root: Path, decisions: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    decision_schema = read_json(root / "contracts/automated_decision.schema.json")
    shadow_schema = read_json(root / "contracts/shadow_prototype_authorization.schema.json")
    ids: list[str] = []
    for envelope in decisions:
        core = envelope["automated_decision"]
        decision_id = core["decision_id"]
        ids.append(decision_id)
        errors.extend(
            f"AUTOMATED_DECISION_SCHEMA:{decision_id}:{item.message}"
            for item in Draft202012Validator(decision_schema).iter_errors(core)
        )
        body = dict(envelope)
        recorded = body.pop("decision_hash", None)
        if sha256_json(body) != recorded:
            errors.append(f"AUTOMATED_DECISION_HASH_MISMATCH:{decision_id}")
        replay_body = dict(core)
        replay_hash = replay_body.pop("replay_hash", None)
        if sha256_json(replay_body) != replay_hash:
            errors.append(f"AUTOMATED_DECISION_REPLAY_HASH_MISMATCH:{decision_id}")
        if envelope.get("architecture_selected") is not False:
            errors.append(f"ARCHITECTURE_SELECTION_PROHIBITED:{decision_id}")
        if envelope.get("prototype_executed") is not False:
            errors.append(f"PROTOTYPE_EXECUTION_PROHIBITED:{decision_id}")
        if decision_id == SHADOW_DECISION_ID:
            authorization = envelope["authorization"]
            errors.extend(
                f"SHADOW_AUTHORIZATION_SCHEMA:{item.message}"
                for item in Draft202012Validator(shadow_schema).iter_errors(authorization)
            )
            auth_body = dict(authorization)
            auth_hash = auth_body.pop("authorization_hash", None)
            if sha256_json(auth_body) != auth_hash:
                errors.append("SHADOW_AUTHORIZATION_HASH_MISMATCH")
    if set(ids) != set(DECISION_FILES) or len(ids) != len(set(ids)):
        errors.append("PHASE002D_R2_DECISION_SET_MISMATCH")
    return sorted(set(errors))


def check_or_write_decisions(root: Path, *, check: bool) -> dict[str, Any]:
    decisions = build_decisions(root)
    errors = validate_decisions(root, decisions)
    for envelope in decisions:
        decision_id = envelope["automated_decision"]["decision_id"]
        errors.extend(
            check_or_write(
                root / DECISION_ROOT / DECISION_FILES[decision_id], envelope, check=check
            )
        )
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "decision_count": len(decisions),
        "decisions": {
            item["automated_decision"]["decision_id"]: {
                "decision": item["automated_decision"]["decision"],
                "phase_scope": item["phase_scope"],
                "decision_hash": item["decision_hash"],
            }
            for item in decisions
        },
    }


__all__ = [
    "DECISION_FILES",
    "DECISION_ROOT",
    "SHADOW_DECISION_ID",
    "build_decisions",
    "check_or_write_decisions",
    "validate_decisions",
]
