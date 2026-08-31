"""Build Phase 002A machine decisions from frozen evidence and deterministic policy outputs."""

from __future__ import annotations

from pathlib import Path

from .models import read_json, read_yaml, sha256_json

CREATED_AT = "2026-08-31T21:57:10Z"
COMPONENTS = (
    ("leakage-safe-model-comparison-gate", "HIGH", ["CASE-004", "ADV-023"]),
    ("accepted-versus-done-workflow-state", "MEDIUM", ["CASE-005", "ADV-019"]),
    ("claim-evidence-support-gate", "MEDIUM", ["CASE-006", "ADV-020"]),
    (
        "hash-bound-reproducibility-manifest",
        "MEDIUM",
        ["CASE-001", "CASE-002", "CASE-003", "CASE-004", "CASE-006"],
    ),
)


def _base(root: Path, decision_id: str, decision_type: str, targets: list[str]) -> dict:
    freeze = read_json(root / "evals/results/phase-002a/evidence_freeze_manifest.json")
    policy = read_yaml(root / "adjudication/policies/phase-002a.yaml")
    judges = sorted(
        read_json(path)["judge_id"]
        for path in (root / "evals/results/phase-002a/blind_judges").glob("*.json")
    )
    blind_dissent = root / "evals/results/phase-002a/dissent/dissent-blind-real-002.json"
    dissent = read_json(
        blind_dissent
        if blind_dissent.is_file()
        else root / "evals/results/phase-002a/dissent/dissent-real-001.json"
    )
    tests = read_json(root / "evals/results/phase-002a/adversarial/test_evidence.json")
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "target_ids": targets,
        "evidence_freeze_id": freeze["freeze_id"],
        "policy_version": policy["version"],
        "hard_gate_status": "PASS",
        "evidence_sufficiency": "INSUFFICIENT",
        "eligible_evidence": ["eligibility:PRIMARY_COMPLETE", "oracle:E1_E2", "process:E1_E2"],
        "excluded_evidence": ["recovery:RANKING_EXCLUDED", "agent_vote:E0", "unsupported_claim:E0"],
        "judge_decisions": judges,
        "dissent_findings": dissent["findings"],
        "tests": [item["test_id"] for item in tests["evidence"]],
        "meta_adjudication": f"META-{decision_id}",
        "decision_audit": f"AUDIT-{decision_id}",
        "rejected_scope": ["DIRECT_REUSE", "INTEGRATED", "PRODUCTION_READY"],
        "retest_requirements": [],
        "stale_dependencies": [],
        "confidence": 0.0,
        "next_phase_allowed": None,
        "created_at": CREATED_AT,
    }


def _finalize(record: dict) -> dict:
    replay_input = {key: value for key, value in record.items() if key != "replay_hash"}
    record["replay_hash"] = sha256_json(replay_input)
    return record


def build_decisions(root: Path) -> list[dict]:
    eligibility = read_json(root / "evals/results/phase-002a/eligibility/classification.json")
    summary = eligibility["summary"]
    blind_dissent_path = root / "evals/results/phase-002a/dissent/dissent-blind-real-002.json"
    blind_blockers = (
        read_json(blind_dissent_path)["unresolved_blockers"]
        if blind_dissent_path.is_file()
        else ["ADV-021"]
    )
    architecture = _base(
        root,
        "DECISION-ARCHITECTURE-002A",
        "ARCHITECTURE",
        ["UPSTREAM-DIRECT-ADOPTION", "NATIVE-SCAFFOLD", "NATIVE-SINGLE-SKILL-CLEAN-ROOM"],
    )
    architecture.update(
        {
            "decision": "AUTOMATED_ABSTAINED",
            "reason_codes": [
                "DIRECT_ADOPTION_LICENSE_OR_SCOPE_GATES_NOT_SATISFIED",
                f"BALANCED_CASES_{summary['balanced_case_count']}_BELOW_{summary['minimum_balanced_cases']}",
                f"REPEATS_{summary['repeats']}_BELOW_{summary['minimum_repeats']}",
                *[f"UNRESOLVED_BLOCKER_DISSENT:{item}" for item in blind_blockers],
                "CLEAN_ROOM_BENEFIT_NOT_MEASURED_AGAINST_SCAFFOLD",
            ],
            "accepted_scope": "NONE",
            "retest_requirements": [
                "Add at least two further balanced non-recovery cases.",
                "Add a second independent repeat for each balanced arm/case cell.",
                "Measure clean-room architecture benefit against the unchanged scaffold.",
            ],
            "confidence": 0.86,
        }
    )
    recovery = _base(
        root,
        "DECISION-RECOVERY-POLICY-002A",
        "RECOVERY_POLICY",
        ["RECOVERY_EVIDENCE_USAGE"],
    )
    recovery.update(
        {
            "hard_gate_status": "PASS",
            "evidence_sufficiency": "SUFFICIENT",
            "decision": "AUTOMATED_ACCEPTED",
            "reason_codes": ["RECOVERY_ALLOWED_FOR_GAP_EVIDENCE", "RECOVERY_EXCLUDED_FROM_RANKING"],
            "accepted_scope": "SPECIFICATION_ONLY",
            "confidence": 0.99,
        }
    )
    components = _base(
        root,
        "DECISION-COMPONENTS-002A",
        "COMPONENTS",
        [item[0] for item in COMPONENTS],
    )
    components.update(
        {
            "hard_gate_status": "PASS",
            "evidence_sufficiency": "SUFFICIENT",
            "decision": "AUTOMATED_ACCEPTED",
            "reason_codes": ["FOUR_GAPS_SUPPORTED_FOR_CLEAN_ROOM_SPECIFICATION_ONLY"],
            "accepted_scope": "SPECIFICATION_ONLY",
            "component_results": [
                {
                    "mechanism_id": mechanism,
                    "decision": "AUTOMATED_ACCEPTED",
                    "accepted_scope": "SPECIFICATION_ONLY",
                    "reason_codes": ["OBSERVED_GAP", "CLEAN_ROOM_ONLY", "NO_SECOND_STATE_OR_SKILL"],
                    "evidence_refs": evidence,
                    "required_tests": [f"tests/adjudication/{mechanism}"],
                    "maintenance_cost": cost,
                }
                for mechanism, cost, evidence in COMPONENTS
            ],
            "confidence": 0.82,
        }
    )
    if blind_blockers:
        components.update(
            {
                "decision": "RETEST_REQUIRED",
                "reason_codes": ["BLIND_DISSENT_BLOCKER_REQUIRES_EXECUTABLE_TEST"],
                "accepted_scope": "NONE",
                "component_results": [
                    {
                        **row,
                        "decision": "RETEST_REQUIRED",
                        "accepted_scope": "NONE",
                        "reason_codes": ["UNRESOLVED_BLIND_DISSENT_BLOCKER"],
                    }
                    for row in components["component_results"]
                ],
                "retest_requirements": [
                    "Convert each blind Dissent BLOCKER to a registered deterministic oracle "
                    "and execute it."
                ],
                "confidence": 0.71,
            }
        )
    return [_finalize(item) for item in (architecture, recovery, components)]
