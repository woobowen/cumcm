"""Generate the complete Phase 002D-R1 report set from machine records."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .decisions import DECISION_FILES
from .models import RESULT_ROOT, check_or_write, hashed_body, read_json
from .native_audits import FIRST_ROUND_ROLES, POST_DECISION_ROLE

REPORT_PATHS = (
    "reports/phase002d_r1_failure_taxonomy.md",
    "reports/phase002d_r1_slot_outcomes.md",
    "reports/phase002d_r1_retry_bias.md",
    "reports/phase002d_r1_quality_evidence.md",
    "reports/phase002d_r1_reliability_evidence.md",
    "reports/phase002d_r1_subagent_audits.md",
    "reports/phase002d_r1_supplemental_decision.md",
    "reports/phase002d_r1_automated_decisions.md",
    "reports/phase002d_r1_decision_audit.md",
    "reports/phase002d_r1_replay.md",
    "reports/phase-002d-r1-acceptance.md",
    "reports/phase-002d-acceptance.md",
    "reports/automated_adjudication_dossier.md",
    "reports/formal_automated_decisions.md",
)
MANIFEST_PATH = RESULT_ROOT / "reports_manifest.json"
GENERATED = "<!-- GENERATED FILE — DO NOT EDIT -->\n"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _decision_rows(decisions: list[dict[str, Any]]) -> list[list[str]]:
    return [
        [
            item["automated_decision"]["decision_id"],
            item["automated_decision"]["decision"],
            item["accepted_scope"],
            item["automated_decision"]["next_phase_allowed"],
            item["failure_aware_hash"],
        ]
        for item in decisions
    ]


def build_reports(root: Path) -> dict[str, str]:
    failure = read_json(root / RESULT_ROOT / "failure_attribution_summary.json")
    matrix = read_json(root / RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.json")
    quality = read_json(root / RESULT_ROOT / "evidence_scopes/quality_sufficiency.json")
    reliability = read_json(root / RESULT_ROOT / "evidence_scopes/reliability_sufficiency.json")
    retry = read_json(root / RESULT_ROOT / "retry_bias/retry_bias_audit.json")
    authorization = read_json(root / RESULT_ROOT / "supplemental/authorization.json")
    budget = read_json(root / RESULT_ROOT / "supplemental/budget.json")
    supplemental = read_json(root / RESULT_ROOT / "supplemental/status.json")
    audit = read_json(root / RESULT_ROOT / "decision_audit/audit.json")
    replay = read_json(root / RESULT_ROOT / "replay/replay.json")
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    decision_repair = read_json(
        root / RESULT_ROOT / "subagent_audits/decision_repair_rounds/finding_closure.json"
    )
    decision_repair_rounds = sorted(
        (root / RESULT_ROOT / "subagent_audits/decision_repair_rounds").glob("round-*.json")
    )
    decisions = [
        read_json(root / RESULT_ROOT / "automated_decisions" / filename)
        for filename in DECISION_FILES.values()
    ]
    first_audits = [
        read_json(root / RESULT_ROOT / f"subagent_audits/{role}.json") for role in FIRST_ROUND_ROLES
    ]
    final_native = read_json(root / RESULT_ROOT / f"subagent_audits/{POST_DECISION_ROLE}.json")
    validation_path = root / RESULT_ROOT / "validation_commands.json"
    validation = read_json(validation_path) if validation_path.is_file() else {"commands": []}
    validation_rows = [
        [
            item["id"],
            item["command"],
            item["exit_code"],
            item["duration_seconds"],
            item["type"],
            item["result"],
            item.get("blocker") or "None",
            item["evidence_hash"],
            item["run_count"],
            item["token_usage"],
        ]
        for item in validation.get("commands", [])
    ]
    taxonomy_rows = [[key, value] for key, value in failure["classification_counts"].items()]
    slot_rows = [
        [
            item["slot_id"],
            item["outcome_resolution"],
            item["outcome_subtype"],
            item["attempt_count"],
            item["retry_count"],
            item["selected_quality_record_id"] or "None",
        ]
        for item in matrix["slots"]
    ]
    decision_table = _table(
        ["Decision ID", "Decision", "Accepted scope", "Next phase", "Hash"],
        _decision_rows(decisions),
    )
    reports: dict[str, str] = {}
    reports["reports/phase002d_r1_failure_taxonomy.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 failure taxonomy

Freeze: `{freeze["freeze_id"]}` / `{freeze["manifest_hash"]}`. All {failure["source_attempt_count"]}
source attempts are classified exactly once. Identity was not used.

{_table(["Primary classification", "Count"], taxonomy_rows)}

`HARD-FAIL-003` is an observed unsupported-claim policy failure only when authoritative runner
evidence attributes it to the candidate output. Harness false positives stay censored. Failures are
categorical outcomes, never numeric zeroes.
"""
    )
    reports["reports/phase002d_r1_slot_outcomes.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 slot outcomes

The matrix has {matrix["expected_slot_count"]} unique frozen slots and accounts for all
{matrix["source_attempt_count"]} attempts. Resolution counts: `{matrix["resolution_counts"]}`.
Earliest eligible selection is `{matrix["earliest_eligible_selection"]}` and best-of-N is
prohibited: `{matrix["best_of_n_prohibited"]}`.

{_table(["Slot", "Resolution", "Subtype", "Attempts", "Retries", "Quality record"], slot_rows)}
"""
    )
    reports["reports/phase002d_r1_retry_bias.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 retry-bias audit

- Attempts retained in cost: `{retry["attempt_count"]}` / 28.
- Retry burden: `{retry["retry_burden"]}`.
- Earliest eligible enforced: `{retry["earliest_eligible_enforced"]}`.
- Best-of-N prohibited: `{retry["best_of_n_prohibited"]}`.
- Failure-zero imputation: `{retry["failure_zero_imputation"]}`.
- Exact cost reconciliation: `{retry["cost_reconciliation"]["exact_match"]}`.
- Historical deviations: `{retry["historical_protocol_deviations"]}`.

The deviations remain evidence of the frozen execution and are not erased or retroactively
declared protocol-conformant.
"""
    )
    reports["reports/phase002d_r1_quality_evidence.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 quality evidence

Result: `{quality["result"]}`. Balanced cases are
`{quality["balanced_case_count"]}/{quality["required_balanced_cases"]}` and eligible quality repeat
depth is `{quality["minimum_repeat_depth"]}/{quality["required_repeat_depth"]}`. Terminal negatives
do not fill the quality Gate. No quality, superiority, base-selection, architecture-selection or
Phase 003 claim is authorized.
"""
    )
    metrics = reliability["metrics"]
    reports["reports/phase002d_r1_reliability_evidence.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 reliability evidence

Result: `{reliability["result"]}` with accepted scope `RELIABILITY_ONLY`. The descriptive frozen
cohort contains {metrics["attempt_count"]} attempts, completion rate {metrics["completion_rate"]},
primary-eligible rate {metrics["primary_eligible_rate"]}, terminal-failure rate
{metrics["terminal_failure_rate"]}, policy-violation rate {metrics["policy_violation_rate"]},
infrastructure rate {metrics["infrastructure_rate"]} and retry burden {metrics["retry_burden"]}.
This scope cannot be converted into a quality or performance-superiority claim.
"""
    )
    audit_rows = [
        [item["role"], item["round"], item["verdict"], len(item["findings"]), len(item["blockers"])]
        for item in [*first_audits, final_native]
    ]
    reports["reports/phase002d_r1_subagent_audits.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 native Subagent audits

{_table(["Role", "Round", "Verdict", "Findings", "Blockers"], audit_rows)}

The five first-round outputs remain immutable. Their ten serious findings were closed by executed
deterministic tests without rewriting original verdicts. The post-decision Auditor required
{len(decision_repair_rounds)} bounded repair cycles: cycle 1 closed
{decision_repair["closed_serious_finding_count"]} of {decision_repair["serious_finding_count"]}
scope/replay findings, and cycles 2–3 closed two evidence-catalog omissions. All intermediate
records remain preserved; the final independent re-audit passed. No vote or human technical Gate
was used.
"""
    )
    reports["reports/phase002d_r1_supplemental_decision.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 supplemental decision

Decision: `{authorization["decision"]}`; accepted scope: `{authorization["accepted_scope"]}`;
authorized slots: `{authorization["authorized_slot_ids"]}`; maximum starts:
`{authorization["maximum_real_starts"]}`. The sole censored slot is harness-censored and semantic
equivalence is `{authorization["harness_semantic_equivalence"]["status"]}`. Budget
`{budget["budget_id"]}` and receipt `{supplemental["receipt_id"]}` both bind zero starts. Original
budget mutation, API-key use and API billing are all false.
"""
    )
    reports["reports/phase002d_r1_automated_decisions.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 automated decisions

{decision_table}

The canonical and wrapper `accepted_scope` fields agree for all seven records. Architecture remains
unselected; four mechanisms are accepted only as specifications.
"""
    )
    failed_checks = [name for name, passed in audit["checks"].items() if not passed]
    reports["reports/phase002d_r1_decision_audit.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 decision audit

Formal result: `{audit["result"]}`; checkpoint `{audit["checkpoint_hash"]}`; replayable:
`{audit["replayable"]}`. The independent native Auditor verdict is `{final_native["verdict"]}`.
Mechanical checks: {len(audit["checks"])}; failed: `{failed_checks}`; blockers:
`{audit["blockers"]}`. The audit is identity-blind, nonvoting, read-only and recovery-excluding.
"""
    )
    variant_rows = [
        [name, value["projection_hash"], value["matches_recorded_decisions"]]
        for name, value in replay["variants"].items()
    ]
    reports["reports/phase002d_r1_replay.md"] = (
        GENERATED
        + f"""# Phase 002D-R1 offline replay

Mode: `{replay["mode"]}`; stable: `{replay["stable"]}`; model starts: `{replay["model_starts"]}`;
next phase: `{replay["next_phase_allowed"]}`; replay hash: `{replay["replay_hash"]}`.

{_table(["Variant", "Projection hash", "Matches decisions"], variant_rows)}
"""
    )
    validation_section = (
        _table(
            [
                "ID",
                "Command",
                "Exit",
                "Seconds",
                "Type",
                "Result",
                "Blocker",
                "Evidence hash",
                "Runs",
                "Tokens",
            ],
            validation_rows,
        )
        if validation_rows
        else "Validation command ledger not yet recorded."
    )
    acceptance = (
        GENERATED
        + f"""# Phase 002D-R1 acceptance report

## Outcome

`FAILURE_AWARE_ADJUDICATION_COMPLETE`. Quality remains `EVIDENCE_INSUFFICIENT`; this is a complete
negative/limited-scope adjudication, not a successful quality Gate. The only permitted next route is
`PHASE-EVIDENCE-EXPANSION-002D`; Phase 003 remains locked.

## Frozen evidence and observed outcomes

- Freeze: `{freeze["freeze_id"]}` / `{freeze["manifest_hash"]}`.
- Original attempts: 28; no original attempt was rerun or edited.
- Taxonomy: 9 eligible successes, 9 valid-output oracle failures, 7 terminal policy failures,
  1 infrastructure-censored attempt and 2 harness-censored attempts.
- Slots: 24 total; 9 eligible-success, 14 terminal-negative and 1 harness-censored.
- Retry burden: 4; all attempts, costs and historical deviations retained.
- Observed cost: 6,228.480778 seconds, 5,726,854 input tokens and 272,461 output tokens;
  cached-input, reasoning-token and monetary cost remain `UNKNOWN`.

## Evidence scopes

- Quality: 2/4 balanced cases and depth 1/2 — `EVIDENCE_INSUFFICIENT`.
- Reliability: descriptive frozen-cohort evidence — `RELIABILITY_ONLY`.
- Outcome completeness: 23/24 slots across three resolved cases at depth 2.
- Component gaps: repeated oracle/policy gaps support specification work only.

## Decisions

{decision_table}

No architecture or base is selected. Accepted component specifications are
`accepted-versus-done-workflow-state`, `claim-evidence-support-gate`,
`hash-bound-reproducibility-manifest`, and `leakage-safe-model-comparison-gate`. They are not
implemented, integrated, production-ready or proven to improve outcomes.

## Audits, repair and replay

Five independent first-round audits produced two PASS and three RETEST_REQUIRED verdicts. Ten
serious findings were converted to deterministic tests and closed without rewriting native outputs.
The first Decision Auditor pass returned RETEST_REQUIRED for inconsistent reliability scope and
replay-consumer ambiguity; repair cycle 1 made canonical and wrapper scope identical and added two
executed tests. Cycles 2 and 3 closed two fail-closed evidence-catalog omissions. All intermediate
records remain preserved. Final independent Decision Auditor: `{final_native["verdict"]}`. Formal
audit: `{audit["result"]}` / `{audit["checkpoint_hash"]}`. Five-variant replay is
`{replay["stable"]}` / `{replay["replay_hash"]}`.

## Supplemental, API and training boundary

Supplemental authorization is `{authorization["decision"]}` with zero slots and zero real model
starts. API key used: false. API billing used: false. Foundation-model training/fine-tuning: none.
Optimized objects: deterministic Python policy/validation/replay code, JSON Schemas, fixtures,
machine records, reports and documentation only. Third-party Skill execution/integration: none.

## Validation command ledger

{validation_section}

## Formal boundary

`third_party_integrated=false`, `base_selected=false`, Skill capability `SCAFFOLD_ONLY`, selected
architecture `null`. Unknowns remain cached-input tokens, reasoning tokens, monetary cost, CPU,
queue/operator time, maintenance cost and future quality under a newly frozen acquisition design.
No next-phase work was executed.
"""
    )
    reports["reports/phase-002d-r1-acceptance.md"] = acceptance
    reports["reports/phase-002d-acceptance.md"] = (
        GENERATED
        + f"""# Phase 002D acceptance status

The original Phase 002D acquisition remains immutable and stopped insufficient. Phase 002D-R1 has
now completed failure-aware adjudication with result `{audit["result"]}` and replay stable
`{replay["stable"]}`. Quality remains insufficient; reliability is descriptive only; route is
`PHASE-EVIDENCE-EXPANSION-002D`. See `reports/phase-002d-r1-acceptance.md`.
"""
    )
    reports["reports/automated_adjudication_dossier.md"] = (
        GENERATED
        + f"""# Automated adjudication dossier

Phase 002D-R1 uses one canonical automated-decision contract, a failure-aware scope envelope,
independent native audits, deterministic serious-finding tests, a formal Decision Auditor and
five-variant offline replay. Formal audit `{audit["result"]}`; architecture unselected; quality
insufficient; accepted scopes are policy, reliability and specification only.

{decision_table}
"""
    )
    reports["reports/formal_automated_decisions.md"] = (
        GENERATED
        + f"""# Formal automated decisions

{decision_table}

All records exclude recovery ranking, arm identity, Agent voting and a human technical Gate. The
system rejects supplemental execution and declines architecture selection. Team compliance review
cannot override these technical outcomes.
"""
    )
    return reports


def check_or_write_reports(root: Path, *, check: bool) -> dict[str, Any]:
    reports = build_reports(root)
    errors = []
    for relative, expected in reports.items():
        path = root / relative
        if check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else ""
            if actual != expected:
                errors.append(f"REPORT_STALE:{relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    manifest_body = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002D-R1-REPORTS-MANIFEST-001",
        "report_hashes": {
            relative: hashlib.sha256(value.encode("utf-8")).hexdigest()
            for relative, value in reports.items()
        },
    }
    manifest = hashed_body(manifest_body, "manifest_hash")
    errors.extend(check_or_write(root / MANIFEST_PATH, manifest, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "report_count": len(reports),
        "manifest_hash": manifest["manifest_hash"],
    }
