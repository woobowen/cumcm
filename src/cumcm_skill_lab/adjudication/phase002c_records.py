"""Generate Phase 002C automated decisions and pre-audit replay from frozen inputs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .evidence_sufficiency import collect_evidence_items, compute_evidence_sufficiency
from .models import check_or_write, read_json, read_yaml, sha256_json
from .native_subagent_audits import (
    FIRST_ROUND_ROLES,
    audit_path,
    build_derived_test_ledger,
    validate_first_round,
    write_decision_auditor_bundle,
)
from .pre_adjudication import (
    FREEZE_PATH,
    PRE_RECORD_PATH,
    SUFFICIENCY_PATH,
    build_input_freeze,
    build_pre_adjudication,
    recovery_exclusion_passed,
    resolve_config,
    resolve_policy,
)
from .short_circuit import evaluate_short_circuit

DECISION_ROOT = Path("evals/results/phase-002c/automated_decisions")
TEST_LEDGER_PATH = Path("evals/results/phase-002c/adversarial_tests/derived_tests.json")
PRE_AUDIT_REPLAY_PATH = Path("evals/results/phase-002c/replay/pre_audit_replay.json")
DECISION_FILES = {
    "EVIDENCE_SUFFICIENCY": "evidence_sufficiency.json",
    "DIRECT_UPSTREAM_ADOPTION": "direct_upstream_adoption.json",
    "RECOVERY_POLICY": "recovery_policy.json",
    "COMPONENT_READINESS": "component_readiness.json",
}

DIRECT_ADOPTION_RISK_LEVELS = frozenset(
    {
        "LOW_CONFIRMED",
        "LOW_REVIEWED",
        "MEDIUM",
        "HIGH",
        "BLOCKER",
        "UNKNOWN",
        "UNVERIFIED",
    }
)
SAFE_DIRECT_ADOPTION_RISK_LEVELS = frozenset({"LOW_CONFIRMED", "LOW_REVIEWED"})


def is_registered_safe_risk(value: Any) -> bool:
    """Accept only an exact registered safe value; unknown/mixed-case/prefix values fail closed."""
    return (
        isinstance(value, str)
        and value in DIRECT_ADOPTION_RISK_LEVELS
        and value in SAFE_DIRECT_ADOPTION_RISK_LEVELS
    )


def decision_created_at(root: Path) -> str:
    """Use the governing policy freeze timestamp for every derived decision."""
    return str(resolve_policy(root)["frozen_at"])


def _common(root: Path, *, decision_id: str, decision_type: str, targets: list[str]) -> dict:
    freeze = read_json(root / FREEZE_PATH)
    sufficiency = read_json(root / SUFFICIENCY_PATH)
    audits = [read_json(audit_path(root, role)) for role in FIRST_ROUND_ROLES]
    tests = read_json(root / TEST_LEDGER_PATH)
    recovery = read_json(root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json")
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "target_ids": targets,
        "evidence_freeze_id": freeze["freeze_id"],
        "policy_version": "1.1.0",
        "hard_gate_status": "PASS",
        "evidence_sufficiency": sufficiency["result"],
        "eligible_evidence": [
            sufficiency["sufficiency_id"],
            "ELIGIBILITY-PHASE-002A",
        ],
        "excluded_evidence": [
            f"recovery:{item['anonymous_arm_id']}:{item['case_id']}" for item in recovery["records"]
        ],
        "judge_decisions": [],
        "dissent_findings": sorted(
            finding["finding_id"] for audit in audits for finding in audit["findings"]
        ),
        "tests": sorted(item["test_id"] for item in tests["tests"]),
        "meta_adjudication": "PRE-ADJUDICATION-PHASE-002C",
        "decision_audit": "DECISION-AUDIT-002C",
        "rejected_scope": [],
        "retest_requirements": [],
        "stale_dependencies": [],
        "confidence": 1.0,
        "next_phase_allowed": None,
        "created_at": decision_created_at(root),
    }


def build_decisions(root: Path) -> list[dict[str, Any]]:
    from .pre_adjudication import verify_input_freeze

    freeze_errors = verify_input_freeze(root)
    if freeze_errors:
        raise ValueError("INPUT_FREEZE_BROKEN:" + ",".join(freeze_errors))
    audit_errors = validate_first_round(root)
    if audit_errors:
        raise ValueError("SUBAGENT_AUDITS_INVALID:" + ",".join(audit_errors))
    tests = read_json(root / TEST_LEDGER_PATH)
    if not tests["all_testable_blockers_resolved"]:
        raise ValueError("SUBAGENT_BLOCKER_TESTS_PENDING")
    sufficiency = read_json(root / SUFFICIENCY_PATH)
    pre_record = read_json(root / PRE_RECORD_PATH)
    decisions = [
        _evidence_decision(root, sufficiency, pre_record),
        _direct_adoption_decision(root),
        _recovery_policy_decision(root),
        _component_readiness_decision(root, sufficiency),
    ]
    validator = Draft202012Validator(read_json(root / "contracts/automated_decision.schema.json"))
    for decision in decisions:
        decision["replay_hash"] = "0" * 64
        decision["replay_hash"] = sha256_json(
            {key: value for key, value in decision.items() if key != "replay_hash"}
        )
        validator.validate(decision)
    return decisions


def _evidence_decision(root: Path, sufficiency: dict, pre_record: dict) -> dict:
    common = _common(
        root,
        decision_id="DECISION-EVIDENCE-SUFFICIENCY-002C",
        decision_type="EVIDENCE_SUFFICIENCY",
        targets=["ARCHITECTURE_SELECTION", "COMPONENT_COMBINATION_SELECTION"],
    )
    decision = pre_record["decision"]
    if decision == "CONTINUE_SEMANTIC_ADJUDICATION":
        decision = "RETEST_REQUIRED"
        reasons = ["CONDITIONAL_SEMANTIC_ADJUDICATION_REQUIRED"]
        retests = ["Run frozen candidate-quality semantic adjudication in an authorized phase."]
    else:
        reasons = sufficiency["reason_codes"]
        retests = [
            "Reach the frozen balanced-case minimum with primary non-recovery evidence.",
            "Reach the frozen independent-repeat minimum for every balanced arm/case cell.",
        ]
    common.update(
        {
            "hard_gate_status": (
                "PASS" if all(item["passed"] for item in pre_record["hard_gates"]) else "FAIL"
            ),
            "decision": decision,
            "reason_codes": reasons,
            "accepted_scope": "NONE",
            "rejected_scope": ["BASE_SELECTION", "ARCHITECTURE_SELECTION", "PHASE_003"],
            "retest_requirements": retests,
            "next_phase_allowed": (
                "PHASE-EVIDENCE-EXPANSION-002D"
                if decision in {"EVIDENCE_INSUFFICIENT", "AUTOMATED_REJECTED"}
                else None
            ),
        }
    )
    return common


def _direct_adoption_decision(root: Path) -> dict:
    common = _common(
        root,
        decision_id="DECISION-DIRECT-UPSTREAM-ADOPTION-002C",
        decision_type="DIRECT_UPSTREAM_ADOPTION",
        targets=["HANDSOMEZR_WHOLE_PACKAGE", "YUSHUI_WHOLE_PACKAGE"],
    )
    config = resolve_config(root)
    manifest = read_yaml(root / "research/upstream_candidates/manifest.yaml")
    package_review = read_json(
        root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
    )
    candidates = {item["id"]: item for item in manifest["candidates"]}
    arms = {item["candidate_id"]: item for item in package_review["arms"] if item["candidate_id"]}
    results = []
    for target_id, candidate_id in config["direct_adoption_targets"].items():
        candidate = candidates[candidate_id]
        arm = arms[candidate_id]
        gates = evaluate_direct_adoption_gates(
            candidate,
            arm,
            review_status=package_review["review_status"],
            third_party_code_executed=package_review.get("third_party_code_executed", False),
            candidate_dependencies_installed=package_review.get(
                "candidate_dependencies_installed", False
            ),
        )
        failed = sorted(name for name, passed in gates.items() if not passed)
        results.append(
            {
                "target_id": f"{target_id}_WHOLE_PACKAGE",
                "candidate_id": candidate_id,
                "decision": "AUTOMATED_REJECTED" if failed else "RETEST_REQUIRED",
                "accepted_scope": "NONE",
                "hard_gates": gates,
                "reason_codes": (
                    [f"HARD_GATE_FAILED:{name}" for name in failed]
                    if failed
                    else ["FULL_PACKAGE_ACCEPTANCE_NOT_ESTABLISHED"]
                ),
                "evidence_refs": [
                    "research/upstream_candidates/manifest.yaml",
                    "research/upstream_candidates/dynamic_reviews/package_safety_review.json",
                ],
            }
        )
    values = {item["decision"] for item in results}
    overall = "AUTOMATED_REJECTED" if values == {"AUTOMATED_REJECTED"} else "RETEST_REQUIRED"
    common.update(
        {
            "hard_gate_status": "FAIL" if overall == "AUTOMATED_REJECTED" else "UNKNOWN",
            "evidence_sufficiency": read_json(root / SUFFICIENCY_PATH)["result"],
            "decision": overall,
            "reason_codes": sorted({reason for item in results for reason in item["reason_codes"]}),
            "accepted_scope": "NONE",
            "adoption_results": results,
            "rejected_scope": [item["target_id"] for item in results],
            "retest_requirements": [
                "Whole-package adoption requires every target-specific hard Gate to pass."
            ],
        }
    )
    return common


def evaluate_direct_adoption_gates(
    candidate: dict[str, Any],
    arm: dict[str, Any],
    *,
    review_status: str,
    third_party_code_executed: bool,
    candidate_dependencies_installed: bool,
) -> dict[str, bool]:
    """Apply whole-package hard gates without considering component value or scores."""
    license_status = str(arm.get("license_status", "UNKNOWN")).upper()
    leakage = candidate.get("answer_leakage_risk", "UNKNOWN")
    integration = candidate.get("integration_conflict_risk", "UNKNOWN")
    state = str(candidate.get("state_management", "UNKNOWN")).upper()
    skills = candidate.get("skill_names")
    dangerous = candidate.get("dangerous_or_privileged_instructions")
    network = candidate.get("network_dependencies")
    recognized_permissive_licenses = {
        "APACHE-2.0",
        "BSD-2-CLAUSE",
        "BSD-3-CLAUSE",
        "ISC",
        "MIT",
    }
    return {
        "license": license_status in recognized_permissive_licenses,
        "answer_contamination": is_registered_safe_risk(leakage),
        "scope_conflict": review_status == "FULL_RUNTIME_VERIFIED",
        "second_state_source": state == "NONE",
        "second_orchestrator": is_registered_safe_risk(integration)
        and isinstance(skills, list)
        and len(skills) == 1
        and isinstance(skills[0], str)
        and bool(skills[0]),
        "security": isinstance(dangerous, list)
        and not dangerous
        and isinstance(network, list)
        and not network,
        "full_runtime_verification": third_party_code_executed is True
        and candidate_dependencies_installed is True,
    }


def _recovery_policy_decision(root: Path) -> dict:
    common = _common(
        root,
        decision_id="DECISION-RECOVERY-POLICY-002C",
        decision_type="RECOVERY_POLICY",
        targets=["RECOVERY_AFFECTED_EVIDENCE_USAGE"],
    )
    recovery = read_json(root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json")
    accepted = bool(recovery["records"]) and all(
        item["allowed_use"] == "GAP_EVIDENCE_ONLY" and item["ranking_eligible"] is False
        for item in recovery["records"]
    )
    common.update(
        {
            "evidence_sufficiency": "SUFFICIENT" if accepted else "INSUFFICIENT",
            "decision": "AUTOMATED_ACCEPTED" if accepted else "RETEST_REQUIRED",
            "reason_codes": (
                [
                    "RECOVERY_ALLOWED_FOR_DIAGNOSIS_GAP_DISCOVERY_TEST_DESIGN_AND_ENGINEERING",
                    "RECOVERY_PROHIBITED_FROM_RANKING_SELECTION_AND_SUPERIORITY_CLAIMS",
                ]
                if accepted
                else ["RECOVERY_EXCLUSION_NOT_PROVEN"]
            ),
            "accepted_scope": "POLICY_ONLY" if accepted else "NONE",
            "rejected_scope": [
                "RANKING",
                "MEDIAN",
                "EFFECT_COMPARISON",
                "SUPERIORITY_CLAIM",
                "BASE_SELECTION",
                "PHASE_INTEGRATION_GATE",
            ],
            "retest_requirements": [] if accepted else ["Repair recovery exclusion evidence."],
        }
    )
    return common


def _component_readiness_decision(root: Path, sufficiency: dict) -> dict:
    config = resolve_config(root)
    common = _common(
        root,
        decision_id="DECISION-COMPONENT-READINESS-002C",
        decision_type="COMPONENT_READINESS",
        targets=list(config["component_targets"]),
    )
    sufficient = sufficiency["result"] == "SUFFICIENT"
    component_decision = "RETEST_REQUIRED" if sufficient else "EVIDENCE_INSUFFICIENT"
    components = [
        {
            "mechanism_id": mechanism,
            "decision": component_decision,
            "accepted_scope": "NONE",
            "reason_codes": [
                (
                    "SEMANTIC_AND_IMPLEMENTATION_TESTS_REQUIRED"
                    if sufficient
                    else "COMPARATIVE_EVIDENCE_INSUFFICIENT_FOR_SPECIFICATION_READINESS"
                )
            ],
            "evidence_refs": [sufficiency["sufficiency_id"]],
            "required_tests": [f"PHASE-002D-RETEST:{mechanism}"],
            "maintenance_cost": "MEDIUM",
        }
        for mechanism in config["component_targets"]
    ]
    common.update(
        {
            "decision": component_decision,
            "reason_codes": [
                (
                    "COMPONENT_SEMANTIC_TESTS_REQUIRED"
                    if sufficient
                    else "FROZEN_COMPARATIVE_EVIDENCE_INSUFFICIENT"
                )
            ],
            "accepted_scope": "NONE",
            "component_results": components,
            "rejected_scope": ["DIRECT_REUSE", "IMPLEMENTATION_READY", "PRODUCTION_READY"],
            "retest_requirements": [
                "Re-evaluate each mechanism after the frozen Phase 002D evidence minima pass."
            ],
        }
    )
    return common


def build_pre_audit_replay(root: Path, decisions: list[dict[str, Any]]) -> dict[str, Any]:
    recorded_freeze = read_json(root / FREEZE_PATH)
    recorded_sufficiency = read_json(root / SUFFICIENCY_PATH)
    recorded_pre = read_json(root / PRE_RECORD_PATH)
    rebuilt_freeze = build_input_freeze(root)
    rebuilt_sufficiency, rebuilt_pre = build_pre_adjudication(root, rebuilt_freeze)
    rebuilt_decisions = build_decisions(root)
    items = collect_evidence_items(root)
    policy = resolve_policy(root)
    hard_gates_passed = all(item["passed"] for item in rebuilt_pre["hard_gates"])

    def recompute(variant_items: list[dict[str, Any]]) -> dict[str, Any]:
        result = compute_evidence_sufficiency(
            variant_items,
            balanced_case_minimum=policy["balanced_case_minimum"],
            minimum_repeats=policy["minimum_repeats"],
            required_arms=rebuilt_sufficiency["required_arms"],
            mandatory_hard_gates_passed=hard_gates_passed,
            input_freeze_id=rebuilt_freeze["freeze_id"],
            input_freeze_hash=rebuilt_freeze["freeze_hash"],
            policy_id=policy["policy_id"],
            policy_hash=policy["policy_hash"],
        )
        return _outcome_projection(result)

    label_swapped = deepcopy(items)
    for item in label_swapped:
        item["anonymous_arm_id"] = {"ARM-A": "ARM-B", "ARM-B": "ARM-A"}.get(
            item["anonymous_arm_id"], item["anonymous_arm_id"]
        )
    recovery_extra = [
        *items,
        {
            "evidence_id": "REPLAY:RECOVERY:EXCLUDED",
            "anonymous_arm_id": rebuilt_sufficiency["required_arms"][0],
            "case_id": "CASE-REPLAY-RECOVERY",
            "run_index": 999,
            "completion_status": "COMPLETED",
            "schema_valid": True,
            "task_input_hash": "replay-only-hash",
            "classification": "RECOVERY_AFFECTED",
            "ranking_eligible": False,
            "exclusion_reasons": ["RECOVERY_AFFECTED"],
            "run_path": "REPLAY_SYNTHETIC_NOT_WRITTEN",
        },
    ]
    base_projection = recompute(items)
    variants = {
        "original_recomputed": _normalized_hash(base_projection),
        "evidence_item_order_permuted": _normalized_hash(recompute(list(reversed(items)))),
        "anonymous_arm_label_swapped": _normalized_hash(recompute(label_swapped)),
        "recovery_present_but_excluded": _normalized_hash(recompute(recovery_extra)),
    }
    rebuild_checks = {
        "input_freeze": rebuilt_freeze == recorded_freeze,
        "evidence_sufficiency": rebuilt_sufficiency == recorded_sufficiency,
        "pre_adjudication": rebuilt_pre == recorded_pre,
        "automated_decisions": rebuilt_decisions == decisions,
        "recovery_contamination_rejected": not recovery_exclusion_passed(
            [{"ranking_eligible": True}]
        ),
    }
    replay = {
        "schema_version": "1.0.0",
        "replay_id": "PHASE-002C-PRE-AUDIT-REPLAY",
        "mode": "OFFLINE_NO_MODEL",
        "decision_ids": [item["decision_id"] for item in decisions],
        "rebuild_checks": rebuild_checks,
        "rebuilt_record_hashes": {
            "freeze": rebuilt_freeze["freeze_hash"],
            "sufficiency": rebuilt_sufficiency["record_hash"],
            "pre_adjudication": rebuilt_pre["record_hash"],
            **{item["decision_id"]: item["replay_hash"] for item in rebuilt_decisions},
        },
        "variants": variants,
        "stable": len(set(variants.values())) == 1 and all(rebuild_checks.values()),
        "audit_result": "PENDING",
    }
    replay["content_hash"] = sha256_json(replay)
    return replay


def write_decisions(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    expected_tests = build_derived_test_ledger(root)
    errors.extend(check_or_write(root / TEST_LEDGER_PATH, expected_tests, check=check))
    if errors:
        return {"status": "FAIL", "errors": errors}
    decisions = build_decisions(root)
    by_type = {item["decision_type"]: item for item in decisions}
    for decision_type, filename in DECISION_FILES.items():
        errors.extend(
            check_or_write(root / DECISION_ROOT / filename, by_type[decision_type], check=check)
        )
    replay = build_pre_audit_replay(root, decisions)
    errors.extend(check_or_write(root / PRE_AUDIT_REPLAY_PATH, replay, check=check))
    errors.extend(write_decision_auditor_bundle(root, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "decision_ids": [item["decision_id"] for item in decisions],
        "decision_values": {item["decision_id"]: item["decision"] for item in decisions},
        "pre_audit_replay_stable": replay["stable"],
    }


def _normalized(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalized(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        normalized = [_normalized(item) for item in value]
        return sorted(normalized, key=sha256_json)
    return value


def _normalized_hash(value: Any) -> str:
    return sha256_json(_normalized(value))


def _outcome_projection(sufficiency: dict[str, Any]) -> dict[str, Any]:
    action = evaluate_short_circuit(sufficiency)
    return {
        "thresholds": sufficiency["thresholds"],
        "balanced_cases": sufficiency["actual"]["balanced_cases"],
        "balanced_case_count": sufficiency["actual"]["balanced_case_count"],
        "independent_repeats": sufficiency["actual"]["independent_repeats"],
        "conditions": sufficiency["conditions"],
        "result": sufficiency["result"],
        "action": action,
    }


def _reverse_sequences(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _reverse_sequences(item) for key, item in reversed(list(value.items()))}
    if isinstance(value, list):
        return [_reverse_sequences(item) for item in reversed(value)]
    return value


def _label_round_trip(value: dict[str, Any]) -> dict[str, Any]:
    text = __import__("json").dumps(value, ensure_ascii=False)
    mapping = {"HANDSOMEZR": "__LABEL_A__", "YUSHUI": "__LABEL_B__"}
    for old, placeholder in mapping.items():
        text = text.replace(old, placeholder)
    text = text.replace("__LABEL_A__", "YUSHUI").replace("__LABEL_B__", "HANDSOMEZR")
    text = text.replace("YUSHUI", "__BACK_A__").replace("HANDSOMEZR", "__BACK_B__")
    text = text.replace("__BACK_A__", "HANDSOMEZR").replace("__BACK_B__", "YUSHUI")
    return __import__("json").loads(text)
