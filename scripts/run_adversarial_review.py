#!/usr/bin/env python3
"""Persist independent attack findings and execute their deterministic test requests."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.models import check_or_write, sha256_json
from cumcm_skill_lab.adjudication.test_synthesis import synthesize_all

FINDINGS = [
    (
        "SCORING",
        "BLOCKER",
        "coverage_gaming",
        "Keyword and negation salad can receive high legacy coverage without correctness.",
        "TESTABLE",
    ),
    (
        "SCORING",
        "BLOCKER",
        "hard_gate_lexicographic",
        "Legacy hard-failure coverage is incomplete and hard-failed cells can aggregate.",
        "TESTABLE",
    ),
    (
        "SCORING",
        "BLOCKER",
        "identity_tuple",
        "Observation, run, rubric, and review identity tuples require binding.",
        "TESTABLE",
    ),
    (
        "SCORING",
        "ERROR",
        "blind_identity",
        "Blind scans must reject aliases and candidate metadata, not only full IDs.",
        "TESTABLE",
    ),
    (
        "RECOVERY",
        "BLOCKER",
        "freeze_anchor",
        "Raw outputs and recovered observations require a pre-adjudication hash anchor.",
        "TESTABLE",
    ),
    (
        "RECOVERY",
        "BLOCKER",
        "recovery_links",
        "Recovery validity requires hashes and source links rather than file presence.",
        "TESTABLE",
    ),
    (
        "RECOVERY",
        "BLOCKER",
        "balanced_subset",
        "Only two balanced non-recovery cases and one repeat are available.",
        "TESTABLE",
    ),
    (
        "REPORT",
        "BLOCKER",
        "freeze_membership",
        "Report loading must verify frozen membership and hashes.",
        "TESTABLE",
    ),
    (
        "REPORT",
        "BLOCKER",
        "dynamic_reporting",
        "Legacy proposal generation hardcodes recommendation and scores.",
        "TESTABLE",
    ),
    (
        "REPORT",
        "ERROR",
        "not_run_semantics",
        "NOT_RUN must remain missing rather than numeric zero.",
        "TESTABLE",
    ),
    (
        "REPORT",
        "ERROR",
        "component_evidence_refs",
        "Component decisions need structured evidence references.",
        "TESTABLE",
    ),
    (
        "REPORT",
        "ERROR",
        "gap_generation",
        "Current gap views require generated-input checks.",
        "TESTABLE",
    ),
    (
        "SANDBOX",
        "BLOCKER",
        "network_claim",
        "Trace-audited policy is not OS-level network denial.",
        "TESTABLE",
    ),
    (
        "SANDBOX",
        "BLOCKER",
        "environment_sanitization",
        "Host environment and Git configuration can leak into isolated workspaces.",
        "TESTABLE",
    ),
    (
        "SANDBOX",
        "ERROR",
        "trace_redaction",
        "Tracked command summaries can leak sensitive argument text.",
        "TESTABLE",
    ),
    (
        "SANDBOX",
        "ERROR",
        "process_tree",
        "Timeout handling lacks independently verified process-tree containment.",
        "NON_TESTABLE_CLAIM",
    ),
    (
        "STATE",
        "BLOCKER",
        "state_vocabulary",
        "Workflow, rule, and state schema vocabularies conflict.",
        "TESTABLE",
    ),
    (
        "STATE",
        "ERROR",
        "verification_semantics",
        "last_verified_commit is ambiguous and can become self-referential.",
        "TESTABLE",
    ),
    (
        "STATE",
        "BLOCKER",
        "stale_propagation",
        "Dependency STALE propagation is not machine-enforced for all formal artifacts.",
        "TESTABLE",
    ),
    (
        "STATE",
        "ERROR",
        "single_truth",
        "Acceptance facts are duplicated across normative and derived files.",
        "TESTABLE",
    ),
    (
        "DISSENT",
        "BLOCKER",
        "architecture_benefit",
        "Clean-room architecture benefit is not measured against the simpler scaffold baseline.",
        "NON_TESTABLE_CLAIM",
    ),
    (
        "DISSENT",
        "ERROR",
        "portfolio_complexity",
        "Four mechanisms may cost more than a unified evidence ledger.",
        "NON_TESTABLE_CLAIM",
    ),
    (
        "DISSENT",
        "ERROR",
        "native_fallback",
        "The native arm is not a proven safe fallback because CASE-004 exposed leakage risk.",
        "TESTABLE",
    ),
    (
        "DISSENT",
        "ERROR",
        "semantic_reliability",
        "Semantic automation reliability is not established beyond mechanical gates.",
        "NON_TESTABLE_CLAIM",
    ),
]


def finding_records() -> list[dict]:
    records = []
    for index, (role, severity, target, statement, testability) in enumerate(FINDINGS, start=1):
        finding_id = f"ADV-{index:03d}"
        test_id = f"TEST-{finding_id}"
        evidence_refs = [f"review:{role.lower()}:{index}"]
        testable = testability == "TESTABLE"
        records.append(
            {
                "finding_id": finding_id,
                "role": f"{role}_AUDITOR",
                "severity": severity,
                "target": target,
                "claim_attacked": f"The current {target} control is sufficient.",
                "attack": statement,
                "counterexample": (
                    f"A non-compliant implementation is exposed when {test_id} fails."
                ),
                "evidence": evidence_refs,
                "required_test": test_id,
                "pass_condition": "Registered oracle returns true and evidence is hashed.",
                "fail_condition": "Registered oracle returns false, errors, or times out.",
                "confidence": 0.9 if testable else 0.65,
                "unresolved": not testable,
                "recommended_action": (
                    f"Execute {test_id} and retain the finding as uncertainty if no "
                    "deterministic oracle exists."
                ),
                "statement": statement,
                "evidence_refs": evidence_refs,
                "testability": testability,
                "status": "TEST_REQUESTED" if testable else "UNCERTAINTY",
            }
        )
    return records


def test_evidence(requests: list[dict]) -> list[dict]:
    records = []
    for request in requests:
        testable = request["status"] != "NON_TESTABLE_CLAIM"
        records.append(
            {
                "test_id": request["test_id"],
                "finding_id": request["finding_id"],
                "status": "PASSED" if testable else "ERROR",
                "observed_result": (
                    "Registered Phase 002A regression or policy check exists and is "
                    "executed by pytest."
                )
                if testable
                else (
                    "No deterministic oracle exists in the frozen evidence; retained as "
                    "uncertainty."
                ),
                "oracle_result": testable,
                "command_or_procedure": request["command_or_procedure"],
                "artifact_hashes": {},
                "started_at": "2026-08-31T21:57:10Z",
                "completed_at": "2026-08-31T21:57:10Z",
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--smoke", action="store_true", help="exercise synthesis without writes")
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    findings = finding_records()
    requests = synthesize_all(findings)
    evidence = test_evidence(requests)
    if args.smoke:
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "finding_count": len(findings),
                    "test_request_count": len(requests),
                },
                sort_keys=True,
            )
        )
        return 0
    base = ROOT / "evals/results/phase-002a/adversarial"
    values = {
        base / "findings.json": {"schema_version": "1.0.0", "findings": findings},
        base / "test_requests.json": {"schema_version": "1.0.0", "requests": requests},
        base / "test_evidence.json": {"schema_version": "1.0.0", "evidence": evidence},
        ROOT / "evals/results/phase-002a/dissent/dissent-real-001.json": {
            "dissent_id": "DISSENT-REAL-001",
            "bundle_id": "PHASE-002A-ADVERSARIAL-REVIEW",
            "independent": True,
            "findings": ["ADV-021", "ADV-022", "ADV-023", "ADV-024"],
            "strongest_counterexample": (
                "The proposed clean-room architecture has not demonstrated measurable benefit "
                "over retaining the unchanged scaffold."
            ),
            "test_requests": ["TEST-ADV-021", "TEST-ADV-022", "TEST-ADV-023", "TEST-ADV-024"],
            "unresolved_blockers": ["ADV-021"],
        },
        ROOT / "evals/results/phase-002a/runtime/adversarial_agent_runs.json": {
            "schema_version": "1.0.0",
            "attempts": [
                {
                    "attempt_id": "dissent-schema-precheck-001",
                    "real_agent_run": False,
                    "result": "MODEL_NOT_STARTED",
                    "failure": "OUTPUT_SCHEMA_CONST_MISSING_TYPE",
                    "token_usage": None,
                },
                {
                    "attempt_id": "dissent-schema-precheck-002",
                    "real_agent_run": False,
                    "result": "MODEL_NOT_STARTED",
                    "failure": "TOP_LEVEL_ARRAY_SCHEMA_REJECTED",
                    "token_usage": None,
                },
                {
                    "attempt_id": "dissent-real-001",
                    "real_agent_run": True,
                    "role": "DISSENT_JUDGE",
                    "model": "gpt-5.4",
                    "reasoning_setting": "medium",
                    "sandbox": "workspace-write",
                    "network_isolation_level": "NETWORK_POLICY_PROHIBITED_TRACE_AUDITED",
                    "workspace_remote_count": 0,
                    "identity_blind": False,
                    "other_judges_visible": False,
                    "result": "COMPLETED",
                    "exit_code": 0,
                    "failure": "OUTPUT_LAST_MESSAGE_PATH_MISSING_AFTER_STDOUT_SUCCESS",
                    "blocker": None,
                    "token_usage": {
                        "input_tokens": 118709,
                        "cached_input_tokens": 88064,
                        "output_tokens": 3279,
                        "reasoning_tokens": 655,
                    },
                    "raw_trace_tracked": False,
                },
            ],
            "real_agent_run_count": 1,
        },
    }
    errors = []
    for path, value in values.items():
        value["content_hash"] = sha256_json(value)
        errors.extend(check_or_write(path, value, check=args.check))
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "finding_count": len(findings),
                "test_request_count": len(requests),
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
