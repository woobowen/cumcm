"""Build and validate the sole formal Phase 002D-R2 state transition."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import check_or_write, read_json

from .adjudication import DECISION_FILES, DECISION_ROOT, SHADOW_DECISION_ID
from .architecture_validator import validate_architecture_candidates
from .decision_audit import AUDIT_PATH, validate_audit
from .models import COMPONENT_IDS, RESULT_ROOT, verify_input_freeze
from .replay import REPLAY_PATH, validate_replay

STATE_PATH = Path("state/project_state.json")
CONTENT_VERIFIED_COMMIT = "4434e0c5df9621c7b17731a3854a80442401da2b"
UPDATED_AT = "2026-09-02T22:00:00+08:00"
R2_ROUTE = "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL"
LEDGER_ENTRIES = {
    Path("state/decision_log.jsonl"): [
        {
            "decision_id": "DEC-0040",
            "timestamp": UPDATED_AT,
            "context": "Phase 002D-R2 specification, protocol and shadow-scope adjudication",
            "options": [
                "freeze validated specifications and protocol while retaining scaffold only",
                "select an architecture without prospective results",
                "authorize a shadow prototype before Decision Audit and replay",
                "enter Phase 003",
            ],
            "evidence": [
                "evals/results/phase-002d-r2/automated_decisions",
                "evals/results/phase-002d-r2/adversarial_findings/findings.json",
                "evals/results/phase-002d-r2/test_evidence/evidence.json",
                "evals/results/phase-002d-r2/decision_audit/audit.json",
                "evals/results/phase-002d-r2/replay/replay.json",
            ],
            "decision": (
                "Accept the four component specifications, interaction contract, candidate set, "
                "prospective Benchmark and threshold policy only at their frozen scopes; keep "
                "shadow authorization RETEST_REQUIRED because its M7 snapshot precedes the "
                "mandatory Auditor and replay."
            ),
            "rejected_options": [
                "architecture or base selection",
                "formal Skill implementation",
                "prototype execution in R2",
                "third-party integration",
                "Phase 003 entry",
            ],
            "consequences": [
                "Architecture remains null and all three candidates remain comparison arms only.",
                "The formal Skill remains 0.1.0-foundation and SCAFFOLD_ONLY.",
                "The next route remains Phase 002D-R2; no prototype is authorized.",
            ],
            "revisit_conditions": [
                "a newly frozen shadow-authorization decision after independent audit and replay",
                "decision or replay hash drift",
                "implementation embargo violation",
            ],
            "approved_by": ["main-agent"],
        },
        {
            "decision_id": "DEC-0041",
            "timestamp": UPDATED_AT,
            "context": "Phase 002D-R2 formal technical-state transition",
            "options": [
                "mark the specification/protocol phase complete with shadow authorization pending",
                "misreport RETEST_REQUIRED shadow scope as phase incompleteness",
                "route to R3 or Phase 003",
            ],
            "evidence": [
                "evals/results/phase-002d-r2/decision_audit/audit.json",
                "evals/results/phase-002d-r2/replay/replay.json",
                "contracts/project_state.schema.json",
                "rules/phase002d_r2_workflow_rules.yaml",
            ],
            "decision": (
                "Set technical_adjudication_status to SPECIFICATION_PROTOCOL_COMPLETE because all "
                "phase artifacts, adversarial tests, Decision Audit and replay pass, while routing "
                "back to R2 because shadow authorization is RETEST_REQUIRED."
            ),
            "rejected_options": [
                "treating shadow authorization as a completion prerequisite",
                "architecture selection",
                "component integration",
                "Phase 003 entry",
            ],
            "consequences": [
                "The phase is complete as a specification/protocol deliverable.",
                "No implementation, model-in-loop experiment, API call or prototype run occurred.",
            ],
            "revisit_conditions": [
                "validation failure",
                "remote SHA mismatch",
                "Decision Audit or replay becomes stale",
            ],
            "approved_by": ["main-agent"],
        },
    ],
    Path("state/task_ledger.jsonl"): [
        {
            "task_id": "PHASE-002D-R2-M9",
            "status": "REMOTE_DELIVERED_CONTENT_BASE_READY_FOR_CLOSURE",
            "plan": "plans/active/PLAN-0002D-R2-specification-and-protocol.md",
            "updated_at": UPDATED_AT,
            "owner": "main-agent",
            "technical_adjudication_status": "SPECIFICATION_PROTOCOL_COMPLETE",
            "automated_decision_count": 6,
            "decision_auditor": "PASS",
            "replay_stable": True,
            "replay_variants": 5,
            "serious_findings": 29,
            "serious_findings_closed_by_tests": 29,
            "native_subagent_runs": 17,
            "selected_architecture": None,
            "base_selected": False,
            "third_party_integrated": False,
            "shadow_authorization": "RETEST_REQUIRED",
            "next_phase_allowed": R2_ROUTE,
            "content_verified_commit": CONTENT_VERIFIED_COMMIT,
            "remote": "origin",
            "remote_sha": CONTENT_VERIFIED_COMMIT,
            "real_batch_codex_runs": 0,
            "api_calls": 0,
            "prototype_executions": 0,
            "third_party_executions": 0,
            "phase_003_started": False,
        },
        {
            "task_id": "PHASE-002D-R2-M9-CONTENT-RECEIPT",
            "status": "REMOTE_DELIVERED",
            "plan": "plans/active/PLAN-0002D-R2-specification-and-protocol.md",
            "updated_at": UPDATED_AT,
            "owner": "main-agent",
            "technical_adjudication_status": "SPECIFICATION_PROTOCOL_COMPLETE",
            "content_verified_commit": CONTENT_VERIFIED_COMMIT,
            "remote": "origin",
            "remote_sha": CONTENT_VERIFIED_COMMIT,
            "selected_architecture": None,
            "base_selected": False,
            "third_party_integrated": False,
            "shadow_authorization": "RETEST_REQUIRED",
            "next_phase_allowed": R2_ROUTE,
            "phase_003_started": False,
        },
    ],
    Path("state/risk_register.jsonl"): [
        {
            "risk_id": "RISK-0025",
            "severity": "HIGH",
            "status": "MITIGATED_FOR_FREEZE_REQUIRES_FUTURE_OS_ENFORCEMENT",
            "summary": (
                "The prospective hidden Benchmark is policy/workspace isolated but not OS-level "
                "isolated."
            ),
            "mitigation": (
                "Keep private seeds and oracles ignored and unread in R2; require OS-level denial, "
                "a fresh access ledger and one-time sealed evaluation before any future execution."
            ),
            "resolution_evidence": (
                "evals/prospective/phase-002d-r2/access_policy.yaml; "
                "evals/results/phase-002d-r2/replay/replay.json"
            ),
        },
        {
            "risk_id": "RISK-0026",
            "severity": "MEDIUM",
            "status": "OPEN_RETEST_REQUIRED",
            "summary": (
                "The frozen M7 shadow authorization cannot incorporate the later M8 Auditor and "
                "replay without invalidating its own decision snapshot."
            ),
            "mitigation": (
                "Keep authorization RETEST_REQUIRED and route to R2. A future phase may create a "
                "new versioned authorization that binds the completed audit and replay."
            ),
            "resolution_evidence": (
                "evals/results/phase-002d-r2/automated_decisions/"
                "shadow_prototype_authorization.json"
            ),
        },
    ],
    Path("state/review_ledger.jsonl"): [
        {
            "review_id": "REVIEW-0016",
            "reviewer": "independent-phase-002d-r2-decision-auditor",
            "scope": (
                "six frozen automated decisions, clean-room provenance, implementation embargo, "
                "prospective policy, shadow boundary and five-variant offline replay"
            ),
            "status": "SPECIFICATION_PROTOCOL_COMPLETE",
            "evidence": (
                "evals/results/phase-002d-r2/subagent_outputs/decision_auditor.json; "
                "evals/results/phase-002d-r2/decision_audit/audit.json; "
                "evals/results/phase-002d-r2/replay/replay.json"
            ),
            "unknowns": [
                "Hidden Benchmark isolation is not OS-enforced in R2.",
                (
                    "Shadow prototype effectiveness and cost are unmeasured because no prototype "
                    "exists."
                ),
                (
                    "Source license/legal sufficiency remains unproven beyond metadata-only "
                    "clean-room controls."
                ),
            ],
            "finding": (
                "All 29 audit checks pass without vote or human technical override; shadow scope "
                "remains RETEST_REQUIRED and Phase 003 remains prohibited."
            ),
        }
    ],
}


def _append_entries(original: str, entries: list[dict[str, Any]], id_key: str) -> str:
    lines = [line for line in original.splitlines() if line.strip()]
    existing = {json.loads(line)[id_key] for line in lines}
    for entry in entries:
        if entry[id_key] not in existing:
            lines.append(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def build_final_state(root: Path) -> dict[str, Any]:
    state = deepcopy(read_json(root / STATE_PATH))
    audit = read_json(root / AUDIT_PATH)
    replay = read_json(root / REPLAY_PATH)
    decisions = [
        read_json(root / DECISION_ROOT / DECISION_FILES[decision_id])
        for decision_id in sorted(DECISION_FILES)
    ]
    by_id = {item["automated_decision"]["decision_id"]: item for item in decisions}
    shadow = by_id[SHADOW_DECISION_ID]["authorization"]
    architecture = validate_architecture_candidates(root)
    if (
        verify_input_freeze(root)
        or validate_audit(root, audit)
        or audit["result"] != "PASS"
        or validate_replay(replay)
        or not replay["stable"]
        or architecture["status"] != "PASS"
    ):
        raise ValueError("PHASE002D_R2_FORMAL_STATE_PRECONDITION_FAILED")
    next_route = (
        "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"
        if shadow["decision"] == "AUTOMATED_ACCEPTED"
        else R2_ROUTE
    )
    state.update(
        {
            "schema_version": "2.3.0",
            "subphase": "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL",
            "current_plan": "plans/completed/PLAN-0002D-R2-specification-and-protocol.md",
            "current_branch": "feat/phase002d-r2-spec-protocol",
            "technical_adjudication_status": "SPECIFICATION_PROTOCOL_COMPLETE",
            "automated_decision_ids": sorted(
                set(state["automated_decision_ids"]) | set(DECISION_FILES)
            ),
            "selected_architecture": None,
            "accepted_component_specifications": list(COMPONENT_IDS),
            "architecture_candidate_set": architecture["candidate_ids"],
            "next_phase_allowed": next_route,
            "content_verified_commit": CONTENT_VERIFIED_COMMIT,
            "delivery_receipt_for_commit": {
                "commit": CONTENT_VERIFIED_COMMIT,
                "remote": "origin",
                "remote_sha": CONTENT_VERIFIED_COMMIT,
                "verified_at": UPDATED_AT,
            },
            "base_selected": False,
            "third_party_integrated": False,
            "skill_capability_status": "SCAFFOLD_ONLY",
            "updated_at": UPDATED_AT,
            "updated_by": "main-agent",
            "blockers": [],
        }
    )
    state["specification_protocol"] = {
        "input_freeze_id": "PHASE-002D-R2-INPUT-FREEZE-001",
        "input_freeze_hash": read_json(root / RESULT_ROOT / "input_freeze_manifest.json")[
            "manifest_hash"
        ],
        "implementation_embargo_status": "PASS",
        "benchmark_freeze_status": "BENCHMARK_FROZEN",
        "threshold_policy_status": "POLICY_FROZEN",
        "decision_audit_status": "PASS",
        "replay_stable": True,
        "real_model_starts": 0,
        "native_subagent_runs": 17,
        "prototype_executions": 0,
        "third_party_executions": 0,
    }
    risks = list(state["risks"])
    for risk in (
        "Shadow prototype authorization is RETEST_REQUIRED; no R3 prototype work is authorized.",
        "Clean-room provenance is evidence of process controls, not proof of legal compliance.",
    ):
        if risk not in risks:
            risks.append(risk)
    state["risks"] = risks
    return state


def validate_final_state(root: Path, state: dict[str, Any]) -> list[str]:
    errors = [
        f"PHASE002D_R2_STATE_SCHEMA:{item.message}"
        for item in Draft202012Validator(
            read_json(root / "contracts/project_state.schema.json")
        ).iter_errors(state)
    ]
    if state.get("selected_architecture") is not None or state.get("base_selected") is not False:
        errors.append("PHASE002D_R2_STATE_ARCHITECTURE_SELECTION_PROHIBITED")
    if state.get("third_party_integrated") is not False:
        errors.append("PHASE002D_R2_STATE_THIRD_PARTY_INTEGRATION_PROHIBITED")
    if state.get("skill_capability_status") != "SCAFFOLD_ONLY":
        errors.append("PHASE002D_R2_STATE_SKILL_SCOPE_ESCALATION")
    return sorted(set(errors))


def check_or_write_state(root: Path, *, check: bool) -> dict[str, Any]:
    state = build_final_state(root)
    errors = validate_final_state(root, state)
    errors.extend(check_or_write(root / STATE_PATH, state, check=check))
    id_keys = {
        Path("state/decision_log.jsonl"): "decision_id",
        Path("state/task_ledger.jsonl"): "task_id",
        Path("state/risk_register.jsonl"): "risk_id",
        Path("state/review_ledger.jsonl"): "review_id",
    }
    for path, entries in LEDGER_ENTRIES.items():
        current = (root / path).read_text(encoding="utf-8")
        expected = _append_entries(current, entries, id_keys[path])
        if check:
            if current != expected:
                errors.append(f"PHASE002D_R2_LEDGER_ENTRY_MISSING:{path}")
        else:
            (root / path).write_text(expected, encoding="utf-8")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "technical_adjudication_status": state["technical_adjudication_status"],
        "selected_architecture": state["selected_architecture"],
        "next_phase_allowed": state["next_phase_allowed"],
        "content_verified_commit": state["content_verified_commit"],
    }


__all__ = [
    "CONTENT_VERIFIED_COMMIT",
    "LEDGER_ENTRIES",
    "STATE_PATH",
    "build_final_state",
    "check_or_write_state",
    "validate_final_state",
]
