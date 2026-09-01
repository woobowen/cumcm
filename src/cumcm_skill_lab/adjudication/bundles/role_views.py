"""Role definitions and deterministic evidence projections."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

ROLE_ORDER = (
    "CORRECTNESS_JUDGE",
    "SCIENTIFIC_VALIDITY_JUDGE",
    "ENGINEERING_REPRODUCIBILITY_JUDGE",
    "BLIND_DISSENT_JUDGE",
    "EVIDENCE_META_ADJUDICATOR",
    "DECISION_AUDITOR",
)

ROLE_SLUGS = {
    "CORRECTNESS_JUDGE": "correctness",
    "SCIENTIFIC_VALIDITY_JUDGE": "scientific_validity",
    "ENGINEERING_REPRODUCIBILITY_JUDGE": "engineering_reproducibility",
    "BLIND_DISSENT_JUDGE": "blind_dissent",
    "EVIDENCE_META_ADJUDICATOR": "meta",
    "DECISION_AUDITOR": "decision_audit",
}

ROLE_SCOPES = {
    "CORRECTNESS_JUDGE": [
        "balanced complete-case evidence",
        "deterministic oracle correctness",
        "actual calculation and mathematical validity",
        "data leakage and evidence insufficiency",
    ],
    "SCIENTIFIC_VALIDITY_JUDGE": [
        "assumptions and real constraints",
        "experimental design and robustness",
        "external validity and overclaiming",
        "uncertainty and evidence insufficiency",
    ],
    "ENGINEERING_REPRODUCIBILITY_JUDGE": [
        "run and input/output hashes",
        "recovery and failure records",
        "replay, state and staleness",
        "maintenance and operational cost",
    ],
    "BLIND_DISSENT_JUDGE": [
        "clean-room architecture benefit",
        "native fallback",
        "four proposed mechanisms",
        "automated adjudication reliability",
        "input sufficiency and cost-benefit",
    ],
    "EVIDENCE_META_ADJUDICATOR": [
        "apply the frozen lexicographic policy",
        "resolve evidence-backed dissent without voting",
        "emit exactly three automated technical decisions",
    ],
    "DECISION_AUDITOR": [
        "audit independence, freeze and identity boundaries",
        "audit thresholds, recovery exclusion and accepted scope",
        "audit decision derivation and replayability",
    ],
}

ROLE_FINDING_ROLES = {
    "CORRECTNESS_JUDGE": {"SCORING_AUDITOR", "DISSENT_AUDITOR"},
    "SCIENTIFIC_VALIDITY_JUDGE": {"SCORING_AUDITOR", "DISSENT_AUDITOR"},
    "ENGINEERING_REPRODUCIBILITY_JUDGE": {
        "RECOVERY_AUDITOR",
        "REPORT_AUDITOR",
        "SANDBOX_AUDITOR",
        "STATE_AUDITOR",
        "DISSENT_AUDITOR",
    },
    "BLIND_DISSENT_JUDGE": {
        "SCORING_AUDITOR",
        "RECOVERY_AUDITOR",
        "REPORT_AUDITOR",
        "SANDBOX_AUDITOR",
        "STATE_AUDITOR",
        "DISSENT_AUDITOR",
    },
    "EVIDENCE_META_ADJUDICATOR": {
        "SCORING_AUDITOR",
        "RECOVERY_AUDITOR",
        "REPORT_AUDITOR",
        "SANDBOX_AUDITOR",
        "STATE_AUDITOR",
        "DISSENT_AUDITOR",
    },
    "DECISION_AUDITOR": {
        "SCORING_AUDITOR",
        "RECOVERY_AUDITOR",
        "REPORT_AUDITOR",
        "SANDBOX_AUDITOR",
        "STATE_AUDITOR",
        "DISSENT_AUDITOR",
    },
}

ROLE_EVIDENCE_SECTIONS = {
    "CORRECTNESS_JUDGE": ("eligibility", "coverage", "oracles"),
    "SCIENTIFIC_VALIDITY_JUDGE": ("eligibility", "oracles", "process"),
    "ENGINEERING_REPRODUCIBILITY_JUDGE": ("eligibility", "process"),
    "BLIND_DISSENT_JUDGE": ("eligibility", "coverage", "oracles", "process"),
    "EVIDENCE_META_ADJUDICATOR": ("eligibility", "coverage", "oracles", "process"),
    "DECISION_AUDITOR": ("eligibility", "coverage", "oracles", "process"),
}


def select_findings(role: str, findings: list[dict]) -> list[dict]:
    """Retain every BLOCKER plus role-relevant lower-severity findings."""
    relevant = ROLE_FINDING_ROLES[role]
    return [
        deepcopy(item)
        for item in findings
        if item["severity"] == "BLOCKER" or item["role"] in relevant
    ]


def select_test_evidence(selected_findings: list[dict], evidence: list[dict]) -> list[dict]:
    finding_ids = {item["finding_id"] for item in selected_findings}
    return [deepcopy(item) for item in evidence if item["finding_id"] in finding_ids]


def runtime_output_schema(
    role: str,
    *,
    bundle_hash: str,
    policy_hash: str,
    evidence_hash: str,
) -> dict[str, Any]:
    common = {
        "role": {"const": role},
        "bundle_hash": {"const": bundle_hash},
        "policy_hash": {"const": policy_hash},
        "evidence_hash": {"const": evidence_hash},
        "majority_vote_used": {"const": False},
        "human_technical_gate_used": {"const": False},
        "recovery_ranked": {"const": False},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    }
    if role in ROLE_ORDER[:3]:
        properties = {
            **common,
            "recommendation": {"enum": ["ACCEPT", "REJECT", "RETEST", "INSUFFICIENT", "ABSTAIN"]},
            "recommendation_evidence_refs": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "evidence_sufficiency": {"enum": ["SUFFICIENT", "INSUFFICIENT"]},
            "findings": {"type": "array", "items": _finding_schema()},
            "unresolved_blockers": {"type": "array", "items": {"type": "string"}},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
        }
        required = list(properties)
    elif role == "BLIND_DISSENT_JUDGE":
        properties = {
            **common,
            "recommendation": {
                "enum": ["REJECT", "RETEST", "INSUFFICIENT", "ABSTAIN", "NO_DISSENT"]
            },
            "evidence_sufficiency": {"enum": ["SUFFICIENT", "INSUFFICIENT"]},
            "findings": {"type": "array", "items": _finding_schema()},
            "unresolved_blockers": {"type": "array", "items": {"type": "string"}},
            "strongest_dissent": {"type": "string", "minLength": 1},
            "strongest_dissent_evidence_refs": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "test_evidence_refs": {"type": "array", "items": {"type": "string"}},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
        }
        required = list(properties)
    elif role == "EVIDENCE_META_ADJUDICATOR":
        properties = {
            **common,
            "thresholds_unchanged": {"const": True},
            "hard_gate_status": {"enum": ["PASS", "FAIL", "UNKNOWN"]},
            "evidence_sufficiency": {"enum": ["SUFFICIENT", "INSUFFICIENT"]},
            "unresolved_blockers": {"type": "array", "items": {"type": "string"}},
            "decisions": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": _meta_decision_schema(),
            },
        }
        required = list(properties)
    else:
        checks = {
            name: {"type": "boolean"}
            for name in (
                "identity_blind",
                "role_independence",
                "no_majority_vote",
                "recovery_excluded_from_ranking",
                "coverage_not_correctness",
                "recommendation_not_hardcoded",
                "thresholds_unchanged",
                "evidence_freeze_intact",
                "all_judges_present",
                "dissent_handled",
                "sources_supported",
                "no_human_technical_gate",
                "phase003_not_started",
                "model_consistent",
                "bundles_complete",
                "resume_context_unchanged",
                "decisions_replayable",
                "accepted_scope_bounded",
            )
        }
        properties = {
            **common,
            "result": {"enum": ["PASS", "FAIL", "RETEST_REQUIRED"]},
            "checks": {
                "type": "object",
                "properties": checks,
                "required": list(checks),
                "additionalProperties": False,
            },
            "failures": {"type": "array", "items": {"type": "string"}},
            "blockers": {"type": "array", "items": {"type": "string"}},
            "replayable": {"type": "boolean"},
            "audit_evidence_refs": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
        }
        required = list(properties)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _finding_schema() -> dict[str, Any]:
    properties = {
        "finding_id": {"type": "string", "minLength": 1},
        "severity": {"enum": ["BLOCKER", "ERROR", "WARNING", "INFO"]},
        "target": {"type": "string", "minLength": 1},
        "statement": {"type": "string", "minLength": 1},
        "evidence_refs": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "testability": {"enum": ["TESTABLE", "NON_TESTABLE_CLAIM"]},
        "status": {"enum": ["OPEN", "RESOLVED", "UNRESOLVED"]},
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _meta_decision_schema() -> dict[str, Any]:
    properties = {
        "decision_id": {
            "enum": [
                "DECISION-ARCHITECTURE-002A",
                "DECISION-RECOVERY-POLICY-002A",
                "DECISION-COMPONENTS-002A",
            ]
        },
        "decision_type": {"enum": ["ARCHITECTURE", "RECOVERY_POLICY", "COMPONENTS"]},
        "target_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "decision": {
            "enum": [
                "AUTOMATED_ACCEPTED",
                "AUTOMATED_REJECTED",
                "RETEST_REQUIRED",
                "EVIDENCE_INSUFFICIENT",
                "AUTOMATED_ABSTAINED",
                "STALE",
            ]
        },
        "accepted_scope": {"enum": ["NONE", "SPECIFICATION_ONLY"]},
        "hard_gate_status": {"enum": ["PASS", "FAIL", "UNKNOWN"]},
        "evidence_sufficiency": {"enum": ["SUFFICIENT", "INSUFFICIENT"]},
        "reason_codes": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "evidence_refs": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "dissent_refs": {"type": "array", "items": {"type": "string"}},
        "retest_requirements": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "next_phase_allowed": {"type": ["string", "null"]},
        "component_results": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "mechanism_id": {"type": "string", "minLength": 1},
                    "decision": {
                        "enum": [
                            "AUTOMATED_ACCEPTED",
                            "AUTOMATED_REJECTED",
                            "RETEST_REQUIRED",
                            "EVIDENCE_INSUFFICIENT",
                            "AUTOMATED_ABSTAINED",
                        ]
                    },
                    "accepted_scope": {"enum": ["NONE", "SPECIFICATION_ONLY"]},
                    "reason_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "evidence_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "required_tests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "maintenance_cost": {"enum": ["LOW", "MEDIUM", "HIGH"]},
                },
                "required": [
                    "mechanism_id",
                    "decision",
                    "accepted_scope",
                    "reason_codes",
                    "evidence_refs",
                    "required_tests",
                    "maintenance_cost",
                ],
                "additionalProperties": False,
            },
        },
    }
    return {
        "type": "object",
        "properties": properties,
        "required": [key for key in properties if key != "component_results"],
        "allOf": [
            {
                "if": {"properties": {"decision_type": {"const": "COMPONENTS"}}},
                "then": {"required": ["component_results"]},
            }
        ],
        "additionalProperties": False,
    }
