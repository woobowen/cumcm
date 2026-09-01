"""Promote runtime role JSON into Schema-valid tracked formal records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .bundles.role_views import ROLE_ORDER, ROLE_SLUGS
from .judge_runner import assert_blind
from .models import file_sha256, read_json, sha256_json, write_json

FORMAL_OUTPUT_PATHS = {
    "CORRECTNESS_JUDGE": "evals/results/phase-002b/judge_outputs/correctness.json",
    "SCIENTIFIC_VALIDITY_JUDGE": "evals/results/phase-002b/judge_outputs/scientific_validity.json",
    "ENGINEERING_REPRODUCIBILITY_JUDGE": (
        "evals/results/phase-002b/judge_outputs/engineering_reproducibility.json"
    ),
    "BLIND_DISSENT_JUDGE": "evals/results/phase-002b/dissent_outputs/blind_dissent.json",
    "EVIDENCE_META_ADJUDICATOR": "evals/results/phase-002b/meta_outputs/meta_adjudication.json",
    "DECISION_AUDITOR": "evals/results/phase-002b/audit_outputs/decision_audit.json",
}

CONTRACT_PATHS = {
    "CORRECTNESS_JUDGE": "contracts/judge_decision.schema.json",
    "SCIENTIFIC_VALIDITY_JUDGE": "contracts/judge_decision.schema.json",
    "ENGINEERING_REPRODUCIBILITY_JUDGE": "contracts/judge_decision.schema.json",
    "BLIND_DISSENT_JUDGE": "contracts/dissent_record.schema.json",
    "EVIDENCE_META_ADJUDICATOR": "contracts/meta_adjudication.schema.json",
    "DECISION_AUDITOR": "contracts/decision_audit.schema.json",
}

COMPONENT_IDS = (
    "accepted-versus-done-workflow-state",
    "claim-evidence-support-gate",
    "hash-bound-reproducibility-manifest",
    "leakage-safe-model-comparison-gate",
)

DECISION_FILENAMES = ("architecture.json", "recovery_policy.json", "components.json")


def formal_output_path(root: Path, role: str) -> Path:
    return root / FORMAL_OUTPUT_PATHS[role]


def promote_output(
    root: Path,
    *,
    role: str,
    raw_output: dict[str, Any],
    manifest: dict[str, Any],
    checkpoint_path: Path,
) -> dict[str, Any]:
    assert_blind(raw_output)
    _validate_references(root, role, raw_output)
    common = {
        "role": role,
        "bundle_id": manifest["bundle_id"],
        "bundle_hash": raw_output["bundle_hash"],
        "input_bundle_hash": manifest["bundle_hash"],
        "policy_hash": raw_output["policy_hash"],
        "evidence_hash": raw_output["evidence_hash"],
        "model": manifest["model"],
        "reasoning_setting": manifest["reasoning_setting"],
        "majority_vote_used": raw_output["majority_vote_used"],
        "human_technical_gate_used": raw_output["human_technical_gate_used"],
        "recovery_ranked": raw_output["recovery_ranked"],
        "confidence": raw_output["confidence"],
        "checkpoint_hash": file_sha256(checkpoint_path),
    }
    if role in ROLE_ORDER[:3]:
        evidence_refs = _all_references(
            raw_output["findings"], raw_output["recommendation_evidence_refs"]
        )
        formal = {
            **common,
            "judge_id": f"JUDGE-{ROLE_SLUGS[role].upper()}-002B",
            "identity_blind": True,
            "other_judges_visible": False,
            "findings": raw_output["findings"],
            "recommendation": raw_output["recommendation"],
            "recommendation_evidence_refs": raw_output["recommendation_evidence_refs"],
            "evidence_sufficiency": raw_output["evidence_sufficiency"],
            "unresolved_blockers": raw_output["unresolved_blockers"],
            "evidence_refs": evidence_refs,
            "uncertainties": raw_output["uncertainties"],
        }
    elif role == "BLIND_DISSENT_JUDGE":
        evidence_refs = _all_references(
            raw_output["findings"],
            raw_output["strongest_dissent_evidence_refs"],
            raw_output["test_evidence_refs"],
        )
        formal = {
            **common,
            "dissent_id": "DISSENT-BLIND-002B",
            "independent": True,
            "identity_blind": True,
            "other_judges_visible": False,
            "findings": raw_output["findings"],
            "recommendation": raw_output["recommendation"],
            "evidence_sufficiency": raw_output["evidence_sufficiency"],
            "strongest_dissent": raw_output["strongest_dissent"],
            "strongest_dissent_evidence_refs": raw_output["strongest_dissent_evidence_refs"],
            "test_evidence_refs": raw_output["test_evidence_refs"],
            "unresolved_blockers": raw_output["unresolved_blockers"],
            "evidence_refs": evidence_refs,
            "uncertainties": raw_output["uncertainties"],
        }
    elif role == "EVIDENCE_META_ADJUDICATOR":
        _validate_meta_policy(root, raw_output)
        formal = {
            **common,
            "meta_id": "META-ADJUDICATION-002B",
            "freeze_hash": read_json(root / "evals/results/phase-002b/input_freeze_manifest.json")[
                "freeze_hash"
            ],
            "thresholds_unchanged": raw_output["thresholds_unchanged"],
            "hard_gate_status": raw_output["hard_gate_status"],
            "evidence_sufficiency": raw_output["evidence_sufficiency"],
            "unresolved_blockers": raw_output["unresolved_blockers"],
            "decisions": raw_output["decisions"],
        }
    else:
        decision_ids = [read_json(path)["decision_id"] for path in proposal_decision_paths(root)]
        formal = {
            **common,
            "audit_id": "DECISION-AUDIT-002B",
            "decision_ids": decision_ids,
            "independent": True,
            "checks": raw_output["checks"],
            "result": raw_output["result"],
            "failures": raw_output["failures"],
            "blockers": raw_output["blockers"],
            "replayable": raw_output["replayable"],
            "audit_evidence_refs": raw_output["audit_evidence_refs"],
            "created_at": read_json(checkpoint_path)["last_event_at"],
        }
        if formal["result"] == "PASS" and (
            not all(formal["checks"].values())
            or formal["failures"]
            or formal["blockers"]
            or not formal["replayable"]
        ):
            raise ValueError("AUDIT_POLICY_VIOLATION:PASS_WITH_FAILED_CHECK")
    _validate_contract(root, role, formal)
    assert_blind(formal)
    write_json(formal_output_path(root, role), formal)
    return formal


def create_pre_audit_decisions(root: Path, meta: dict[str, Any]) -> list[dict[str, Any]]:
    judges = [read_json(formal_output_path(root, role))["judge_id"] for role in ROLE_ORDER[:3]]
    dissent = read_json(formal_output_path(root, "BLIND_DISSENT_JUDGE"))
    eligibility = read_json(root / "evals/results/phase-002a/eligibility/classification.json")
    recovery = read_json(root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json")
    tests = read_json(root / "evals/results/phase-002a/adversarial/test_evidence.json")
    automated_schema = read_json(root / "contracts/automated_decision.schema.json")
    created_at = read_json(root / "evals/results/phase-002b/role_checkpoints/meta.json")[
        "last_event_at"
    ]
    if eligibility["summary"]["comparative_sufficiency"] != "INSUFFICIENT":
        raise ValueError("FROZEN_COMPARATIVE_SUFFICIENCY_CHANGED")
    output: list[dict[str, Any]] = []
    decision_dir = root / "evals/results/phase-002b/automated_decisions/proposals"
    for item in meta["decisions"]:
        record = {
            "decision_id": item["decision_id"],
            "decision_type": item["decision_type"],
            "target_ids": item["target_ids"],
            "evidence_freeze_id": "PHASE-002B-ADJUDICATION-INPUT-FREEZE",
            "policy_version": "1.0.0",
            "hard_gate_status": item["hard_gate_status"],
            "evidence_sufficiency": item["evidence_sufficiency"],
            "eligible_evidence": ["eligibility:summary"],
            "excluded_evidence": [
                f"recovery:{value['anonymous_arm_id']}:{value['case_id']}"
                for value in recovery["records"]
            ],
            "judge_decisions": judges,
            "dissent_findings": [finding["finding_id"] for finding in dissent["findings"]],
            "tests": [value["test_id"] for value in tests["evidence"]],
            "meta_adjudication": meta["meta_id"],
            "decision_audit": "AUDIT-PENDING",
            "decision": item["decision"],
            "reason_codes": item["reason_codes"],
            "accepted_scope": item["accepted_scope"],
            "rejected_scope": (
                ["IMPLEMENTATION", "THIRD_PARTY_CODE"]
                if item["accepted_scope"] == "SPECIFICATION_ONLY"
                else item["target_ids"]
            ),
            "retest_requirements": item["retest_requirements"],
            "stale_dependencies": [],
            "confidence": item["confidence"],
            "replay_hash": "0" * 64,
            "next_phase_allowed": None,
            "created_at": created_at,
        }
        if item["decision_type"] == "COMPONENTS":
            record["component_results"] = item["component_results"]
        record["replay_hash"] = sha256_json(
            {key: value for key, value in record.items() if key != "replay_hash"}
        )
        Draft202012Validator(automated_schema).validate(record)
        filename = item["decision_type"].lower() + ".json"
        write_json(decision_dir / filename, record)
        output.append(record)
    return output


def proposal_decision_paths(root: Path) -> list[Path]:
    base = root / "evals/results/phase-002b/automated_decisions/proposals"
    return [base / name for name in DECISION_FILENAMES if (base / name).is_file()]


def final_decision_paths(root: Path) -> list[Path]:
    base = root / "evals/results/phase-002b/automated_decisions"
    return [base / name for name in DECISION_FILENAMES if (base / name).is_file()]


def is_formal_output_valid(root: Path, role: str) -> bool:
    path = formal_output_path(root, role)
    if not path.is_file():
        return False
    try:
        value = read_json(path)
        _validate_contract(root, role, value)
        assert_blind(value)
    except Exception:
        return False
    return True


def _validate_contract(root: Path, role: str, value: dict[str, Any]) -> None:
    Draft202012Validator(read_json(root / CONTRACT_PATHS[role])).validate(value)


def _validate_references(root: Path, role: str, output: dict[str, Any]) -> None:
    catalog_path = root / ".cache/adjudication-002b/bundles" / ROLE_SLUGS[role]
    allowed = set(read_json(catalog_path / "evidence_catalog.json")["identifiers"])
    own_findings = {
        finding["finding_id"] for finding in output.get("findings", []) if "finding_id" in finding
    }
    references: set[str] = set()
    for finding in output.get("findings", []):
        references.update(finding.get("evidence_refs", []))
    for key in (
        "recommendation_evidence_refs",
        "strongest_dissent_evidence_refs",
        "test_evidence_refs",
        "audit_evidence_refs",
    ):
        references.update(output.get(key, []))
    for decision in output.get("decisions", []):
        references.update(decision.get("evidence_refs", []))
        references.update(decision.get("dissent_refs", []))
        for component in decision.get("component_results", []):
            references.update(component.get("evidence_refs", []))
            references.update(component.get("required_tests", []))
    unknown = sorted(references - allowed - own_findings)
    if unknown:
        raise ValueError("UNKNOWN_EVIDENCE_REFERENCE:" + ",".join(unknown))
    finding_ids = [finding["finding_id"] for finding in output.get("findings", [])]
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError("DUPLICATE_FORMAL_FINDING_ID")


def _validate_meta_policy(root: Path, output: dict[str, Any]) -> None:
    decisions = {item["decision_id"]: item for item in output["decisions"]}
    expected = {
        "DECISION-ARCHITECTURE-002A",
        "DECISION-RECOVERY-POLICY-002A",
        "DECISION-COMPONENTS-002A",
    }
    if set(decisions) != expected:
        raise ValueError("META_DECISION_SET_INVALID")
    eligibility = read_json(root / "evals/results/phase-002a/eligibility/classification.json")
    architecture = decisions["DECISION-ARCHITECTURE-002A"]
    if (
        eligibility["summary"]["comparative_sufficiency"] == "INSUFFICIENT"
        and architecture["decision"] != "EVIDENCE_INSUFFICIENT"
    ):
        raise ValueError("META_POLICY_VIOLATION:ARCHITECTURE_MUST_BE_EVIDENCE_INSUFFICIENT")
    for decision in decisions.values():
        if decision["decision"] != "AUTOMATED_ACCEPTED" and decision["accepted_scope"] != "NONE":
            raise ValueError("META_POLICY_VIOLATION:NON_ACCEPTED_SCOPE")
        if decision["next_phase_allowed"] is not None:
            raise ValueError("META_POLICY_VIOLATION:PRE_AUDIT_PHASE003")
    component = decisions["DECISION-COMPONENTS-002A"]
    component_ids = {item["mechanism_id"] for item in component["component_results"]}
    if component_ids != set(COMPONENT_IDS):
        raise ValueError("META_COMPONENT_SET_INVALID")
    if any(
        item["accepted_scope"] not in {"NONE", "SPECIFICATION_ONLY"}
        for item in component["component_results"]
    ):
        raise ValueError("META_COMPONENT_SCOPE_INVALID")
    for item in component["component_results"]:
        if item["decision"] == "AUTOMATED_ACCEPTED":
            if item["accepted_scope"] != "SPECIFICATION_ONLY":
                raise ValueError("META_COMPONENT_ACCEPTED_SCOPE_INVALID")
        elif item["accepted_scope"] != "NONE":
            raise ValueError("META_COMPONENT_NON_ACCEPTED_SCOPE_INVALID")


def _all_references(findings: list[dict], *groups: list[str]) -> list[str]:
    references = {ref for finding in findings for ref in finding["evidence_refs"]}
    for group in groups:
        references.update(group)
    return sorted(references)
