"""Generate Phase 002D terminal reports from machine records."""

# Markdown metric rows intentionally remain one source line per generated report line.
# ruff: noqa: E501

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .attempt_ledger import load_attempts
from .models import RESULT_ROOT, hashed_body, read_json, write_json

COMMAND_LEDGER_PATH = RESULT_ROOT / "closure/command_ledger.json"
DOSSIER_PATH = Path("reports/automated_adjudication_dossier.md")
FORMAL_DECISIONS_PATH = Path("reports/formal_automated_decisions.md")
START_MARKER = "<!-- PHASE002D:START -->"
END_MARKER = "<!-- PHASE002D:END -->"


def _upsert(original: str, section: str) -> str:
    if START_MARKER in original:
        prefix = original.split(START_MARKER, 1)[0].rstrip()
    else:
        prefix = original.rstrip()
    return f"{prefix}\n\n{START_MARKER}\n{section.rstrip()}\n{END_MARKER}\n"


def build_command_ledger(root: Path) -> dict[str, Any]:
    pilot = read_json(root / RESULT_ROOT / "pilot/pilot.json")
    attempts = load_attempts(root)
    corrections = {
        item["attempt_id"]: item["corrected_failure_class"]
        for item in pilot["classification_corrections"]
    }
    entries = []
    for attempt in pilot["attempts"]:
        entries.append(
            {
                "command_id": f"CMD:{attempt['attempt_id']}",
                "command": "codex exec --ephemeral --model gpt-5.6-sol --sandbox workspace-write --output-schema <pilot-schema> -",
                "exit_code": attempt["exit_code"],
                "duration_seconds": attempt["duration_seconds"],
                "execution_type": "REAL_CODEX_PILOT",
                "cohort_id": pilot["cohort_id"],
                "model": attempt["model"],
                "reasoning_setting": attempt["reasoning_setting"],
                "transport_profile": attempt["transport_profile"],
                "attempt_id": attempt["attempt_id"],
                "result": attempt["completion_status"],
                "blocker": corrections.get(attempt["attempt_id"], attempt["failure_class"]),
                "evidence_hash": attempt["attempt_hash"],
                "token_usage": attempt["token_usage"],
            }
        )
    for attempt in attempts:
        entries.append(
            {
                "command_id": f"CMD:{attempt['attempt_id']}",
                "command": "codex exec --ephemeral --model gpt-5.6-sol --sandbox workspace-write --output-schema <frozen-observation-schema> -",
                "exit_code": attempt["exit_code"],
                "duration_seconds": attempt["duration_seconds"],
                "execution_type": "REAL_CODEX_SCORED",
                "cohort_id": attempt["cohort_id"],
                "model": attempt["model"],
                "reasoning_setting": attempt["reasoning_setting"],
                "transport_profile": attempt["transport_profile"],
                "attempt_id": attempt["attempt_id"],
                "result": attempt["completion_status"],
                "blocker": attempt["failure_class"]
                or (",".join(attempt["hard_failures"]) if attempt["hard_failures"] else None),
                "evidence_hash": attempt["attempt_hash"],
                "token_usage": {
                    "input_tokens": attempt["input_tokens"],
                    "cached_input_tokens": attempt["cached_input_tokens"],
                    "output_tokens": attempt["output_tokens"],
                    "reasoning_tokens": attempt["reasoning_tokens"],
                },
            }
        )
    return hashed_body(
        {
            "schema_version": "1.0.0",
            "ledger_id": "PHASE-002D-COMMAND-LEDGER",
            "entry_count": len(entries),
            "real_pilot_starts": len(pilot["attempts"]),
            "real_scored_starts": len(attempts),
            "native_subagent_runs": 0,
            "deterministic_ci_starts": 0,
            "entries": entries,
        },
        "ledger_hash",
    )


def _arm_rows(attempts: list[dict[str, Any]]) -> str:
    rows = []
    for arm in sorted({attempt["anonymous_arm_id"] for attempt in attempts}):
        selected = [attempt for attempt in attempts if attempt["anonymous_arm_id"] == arm]
        rows.append(
            f"| {arm} | {len(selected)} | {sum(a['primary_eligible'] for a in selected)} | "
            f"{sum(a['oracle_status'] == 'PASS' for a in selected)} | "
            f"{sum(a['oracle_status'] == 'FAIL' for a in selected)} | "
            f"{sum(a['input_tokens'] for a in selected):,} | "
            f"{sum(a['output_tokens'] for a in selected):,} | "
            f"{sum(a['duration_seconds'] for a in selected):.6f} |"
        )
    return "\n".join(rows)


def build_reports(root: Path, command_ledger: dict[str, Any]) -> dict[Path, str]:
    pilot = read_json(root / RESULT_ROOT / "pilot/pilot.json")
    budget = read_json(root / RESULT_ROOT / "budget/frozen_budget.json")
    schedule = read_json(root / RESULT_ROOT / "schedule/schedule.json")
    checkpoint = read_json(root / RESULT_ROOT / "checkpoint.json")
    cost = read_json(root / RESULT_ROOT / "cost/cost.json")
    sufficiency = read_json(root / RESULT_ROOT / "sufficiency/evidence_sufficiency.json")
    closure = read_json(root / RESULT_ROOT / "closure/adjudication_gate.json")
    state = read_json(root / "state/project_state.json")
    attempts = load_attempts(root)
    completion_failures = [
        attempt for attempt in attempts if attempt["completion_status"] == "FAILED"
    ]
    excluded = [attempt for attempt in attempts if not attempt["primary_eligible"]]
    failure_classes = Counter(attempt["failure_class"] or "NONE" for attempt in completion_failures)
    hard_failures = Counter(code for attempt in attempts for code in attempt["hard_failures"])
    retry_count = sum(attempt["retry_of"] is not None for attempt in attempts)
    pilot_rows = "\n".join(
        f"| {attempt['attempt_id']} | {attempt['completion_status']} | {attempt['schema_valid']} | "
        f"{attempt['oracle_status']} | {attempt['duration_seconds']:.6f} |"
        for attempt in pilot["attempts"]
    )
    failure_rows = "\n".join(
        f"| {name} | {count} |" for name, count in sorted(failure_classes.items())
    )
    hard_rows = "\n".join(f"| {name} | {count} |" for name, count in sorted(hard_failures.items()))
    block_rows = "\n".join(
        f"| {block['block_number']} | {block['case_id']} | {block['repeat_id']} | "
        f"{', '.join(block['anonymous_arm_order'])} |"
        for block in schedule["blocks"]
    )
    subagent_roles = (
        "expanded_correctness_auditor",
        "expanded_scientific_validity_auditor",
        "expanded_engineering_reproducibility_auditor",
        "expanded_dissent_and_cost_auditor",
        "expanded_decision_auditor",
    )
    subagent_rows = "\n".join(
        f"| {role} | true | NONE | HIDDEN | NOT_RUN | 0 | 0 | PRECONDITION_LOCKED |"
        for role in subagent_roles
    )
    blockers = ", ".join(state["blockers"]) if state["blockers"] else "None"
    reports = {
        Path(
            "reports/phase002d_evidence_expansion_plan.md"
        ): f"""# Phase 002D evidence expansion outcome

The frozen objective was 24 eligible records forming four balanced cases with two independent
repeats. Acquisition used eight primary blocks followed by the frozen retry queue. It stopped after
{len(attempts)} scored starts with {sum(a["primary_eligible"] for a in attempts)} eligible records,
{sufficiency["actual"]["balanced_case_count"]} balanced cases and
{sufficiency["actual"]["independent_repeats"]} independent repeat.

The terminal condition is `{", ".join(checkpoint["hard_stop_reasons"])}` at
{checkpoint["elapsed_seconds"]:.6f} seconds. Formal status is
`{closure["technical_adjudication_status"]}`; the next legal route is
`{closure["next_phase_allowed"]}` after a new reviewed design/freeze. No semantic audit, decision,
integration or Phase 003 execution occurred.
""",
        Path("reports/phase002d_pilot.md"): f"""# Phase 002D pilot

- Status: `{pilot["status"]}`; model starts: {pilot["model_start_count"]} / {pilot["maximum_model_starts"]}
- Cohort/model/reasoning/profile: `{pilot["cohort_id"]}` / `{pilot["model"]}` / `{pilot["reasoning_setting"]}` / `{pilot["selected_transport_profile"]}`
- Primary/repeat evidence contribution: false / false
- API key/billing: {pilot["api_key_used"]} / {pilot["api_billing_used"]}; monetary cost: `{pilot["monetary_cost"]}`

| Attempt | Result | Schema | Oracle | Seconds |
|---|---|---|---|---:|
{pilot_rows}

Attempt 1's preserved correction is `RUNNER_SCHEMA_REJECTED`; attempt 2 passed. Result hash:
`{pilot["result_hash"]}`.
""",
        Path("reports/phase002d_budget.md"): f"""# Phase 002D frozen budget

- Target eligible records: {budget["target_successes"]}
- Attempts / absolute cap / per-cell cap: {budget["maximum_total_attempts"]} / {budget["absolute_attempt_cap"]} / {budget["maximum_attempts_per_cell"]}
- Input / output / elapsed caps: {budget["maximum_total_input_tokens"]:,} / {budget["maximum_total_output_tokens"]:,} / {budget["maximum_total_elapsed_seconds"]} seconds
- Expected attempts/input/output/elapsed: {budget["formula_values"]["base_attempts"]} / {budget["formula_values"]["expected_total_input_tokens"]:,} / {budget["formula_values"]["expected_total_output_tokens"]:,} / {budget["formula_values"]["expected_total_elapsed_seconds"]} seconds
- Concurrency / later batch max: {budget["concurrency"]} / {budget["maximum_later_batch_size"]}
- Cached-input/reasoning/monetary cost: `UNKNOWN` / `UNKNOWN` / `UNKNOWN`
- API key/billing: false / false
- Budget hash: `{budget["budget_hash"]}`

The formula was frozen before scored starts and may not expand after results.
""",
        Path("reports/phase002d_schedule.md"): f"""# Phase 002D frozen schedule

- Schedule/seed/hash: `{schedule["schedule_id"]}` / {schedule["seed"]} / `{schedule["schedule_hash"]}`
- Mode/cohort: `{schedule["mode"]}` / `{schedule["cohort_id"]}`
- Blocks / primary slots / retry slots: {len(schedule["blocks"])} / {schedule["primary_attempt_count"]} / {schedule["maximum_retry_slots"]}
- Cases/arms/repeats: {", ".join(schedule["cases"])} / {", ".join(schedule["anonymous_arms"])} / {schedule["repeats"]}

| Block | Case | Repeat | Frozen arm order |
|---:|---|---:|---|
{block_rows}

All 24 primary slots ran before the frozen retry queue. No immediate or identity-aware reorder occurred.
""",
        Path("reports/phase002d_run_summary.md"): f"""# Phase 002D run summary

- Real Codex starts: {command_ledger["entry_count"]} = {command_ledger["real_pilot_starts"]} pilot + {command_ledger["real_scored_starts"]} scored
- Scored attempts / eligible / excluded: {len(attempts)} / {sum(a["primary_eligible"] for a in attempts)} / {len(excluded)}
- Completion failures / retries / infrastructure failures: {len(completion_failures)} / {retry_count} / {cost["infrastructure_failures"]}
- Oracle PASS / FAIL among eligible: {cost["oracle_passes"]} / {cost["oracle_failures"]}
- Runner status/reason: `{checkpoint["status"]}` / `{", ".join(checkpoint["hard_stop_reasons"])}`
- Command-ledger hash: `{command_ledger["ledger_hash"]}`

| Arm | Attempts | Eligible | Oracle PASS | Oracle FAIL | Input | Output | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
{_arm_rows(attempts)}

Historical Phase 002–002C evidence is immutable gap evidence and contributes zero current-cohort
primary records. Recovery/resume/parser-recovery and cross-model evidence contribute zero. Current
cohort eligible records alone feed sufficiency; semantic review and automated decisions were not run.
""",
        Path("reports/phase002d_failure_summary.md"): f"""# Phase 002D failure summary

- Completion failures: {len(completion_failures)}
- Completed but excluded: {sum(a["completion_status"] == "COMPLETED" for a in excluded)}
- Infrastructure failures: {cost["infrastructure_failures"]}
- Operator interventions: {cost["operator_interventions"]}
- Terminal hard stop: `{", ".join(checkpoint["hard_stop_reasons"])}`

| Completion-failure class | Count |
|---|---:|
{failure_rows}

| Authoritative hard-failure code | Count |
|---|---:|
{hard_rows}

All failures and exclusions remain append-only. They are not zero-valued scores and cannot fill
balanced/repeat minima. Coverage-only hard-failure fields remain outside authoritative Gates.
""",
        Path("reports/phase002d_subagent_audit.md"): f"""# Phase 002D native Subagent audit

Evidence sufficiency is `{sufficiency["result"]}`. The frozen ordering requires sufficiency before
native semantic roles, so zero Subagents ran and no peer/identity/model-output hashes exist.

| Role | Read-only | Peer visibility | Identity | Output hash | Findings | Blockers | Verdict |
|---|---|---|---|---|---:|---:|---|
{subagent_rows}

This is a precondition lock, not a PASS verdict or an abstention by an Agent.
""",
        Path("reports/phase002d_automated_decisions.md"): f"""# Phase 002D automated decisions

- Phase 002D decision IDs: none
- Decision generation: `{closure["automated_decisions_generated"]}`
- Gate status: `{closure["status"]}`
- Evidence sufficiency: `{closure["evidence_sufficiency"]}`
- Sole decision contract remains: `{closure["automated_decision_contract"]}`

No architecture, component, direct-adoption or recovery-policy decision was generated in Phase
002D because native audits were not unlocked. Historical Phase 002C decisions remain immutable and
are not relabelled as Phase 002D outputs.
""",
        Path("reports/phase002d_decision_audit.md"): f"""# Phase 002D Decision Auditor

- Decision Auditor: `{closure["decision_auditor"]}`
- Decisions available to audit: 0
- Native first-round audits available: 0
- Phase 003 allowed/started: {closure["phase_003_allowed"]} / {closure["phase_003_started"]}

`PASS` is not claimed. The Auditor did not run because its validated predecessors do not exist.
The deterministic precondition Gate itself validates under `phase002d_decision.schema.json`.
""",
        Path("reports/phase002d_replay.md"): f"""# Phase 002D replay and route

- Decision replay: `{closure["decision_replay"]}`
- Deterministic incomplete-route replay: `{closure["route_replay"]}`
- Technical status: `{closure["technical_adjudication_status"]}`
- Next phase allowed: `{closure["next_phase_allowed"]}`
- Phase 003 allowed/started: {closure["phase_003_allowed"]} / {closure["phase_003_started"]}
- Closure hash: `{closure["record_hash"]}`

Label/order decision variants are not applicable because no Phase 002D automated decision exists.
The only replayed claim is the fail-closed route from insufficient evidence to the same phase.
""",
        Path("reports/phase-002d-acceptance.md"): f"""# Phase 002D acceptance

- Stage result: `EVIDENCE_EXPANSION_INCOMPLETE`
- State status/technical status: `{state["status"]}` / `{state["technical_adjudication_status"]}`
- Evidence sufficiency: `{sufficiency["result"]}` ({sufficiency["actual"]["balanced_case_count"]}/4 balanced, {sufficiency["actual"]["independent_repeats"]}/2 repeats)
- Runner: `{checkpoint["status"]}` — `{", ".join(checkpoint["hard_stop_reasons"])}`
- Selected architecture/base/components: none / false / none
- Third-party integrated / Skill capability: false / `SCAFFOLD_ONLY`
- Phase 003 allowed/started: false / false
- Next phase allowed: `{state["next_phase_allowed"]}`
- Native Subagents / Phase 002D decisions / Decision Auditor: 0 / 0 / NOT_RUN
- API key/billing/training: false / false / false
- Current blockers: {blockers}
- Content-verified commit: `{state["content_verified_commit"]}`
- Draft PR: `https://github.com/woobowen/cumcm/pull/3` (must remain OPEN/DRAFT)

The incomplete outcome satisfies fail-closed reporting, not the `PHASE_002D_COMPLETE` criteria.
No acceptance scope, implementation readiness, direct reuse or Phase 003 authorization is implied.
""",
    }
    dossier_section = f"""## Phase 002D terminal addendum

Phase 002D ran 28 scored starts in one new cohort and retained 18 eligible records. Its formal
sufficiency is `INSUFFICIENT` at {sufficiency["actual"]["balanced_case_count"]}/4 balanced cases and
{sufficiency["actual"]["independent_repeats"]}/2 repeats. Elapsed budget stopped the runner. Native
Subagents, Phase 002D decisions, Decision Auditor and decision replay were not run. The deterministic
route permits only `PHASE-EVIDENCE-EXPANSION-002D`; Phase 003 remains false.
"""
    formal_section = """## Phase 002D

No Phase 002D automated decision exists. Evidence insufficiency locked the semantic-audit and
decision chain before decision generation. Historical Phase 002C decision IDs above remain the
only formal automated decisions and are not superseded by this absence record.
"""
    reports[DOSSIER_PATH] = _upsert(
        (root / DOSSIER_PATH).read_text(encoding="utf-8"), dossier_section
    )
    reports[FORMAL_DECISIONS_PATH] = _upsert(
        (root / FORMAL_DECISIONS_PATH).read_text(encoding="utf-8"), formal_section
    )
    return reports


def check_or_write_reports(root: Path, *, check: bool) -> dict[str, Any]:
    command_ledger = build_command_ledger(root)
    errors = []
    ledger_path = root / COMMAND_LEDGER_PATH
    if check:
        if not ledger_path.is_file() or read_json(ledger_path) != command_ledger:
            errors.append("PHASE002D_COMMAND_LEDGER_MISMATCH")
    else:
        write_json(ledger_path, command_ledger)
    reports = build_reports(root, command_ledger)
    for relative, expected in reports.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                errors.append(f"PHASE002D_REPORT_MISMATCH:{relative.as_posix()}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    required_external = (
        "reports/phase002d_cohort.md",
        "reports/phase002d_evidence_sufficiency.md",
        "reports/phase002d_cost_report.md",
    )
    errors.extend(path for path in required_external if not (root / path).is_file())
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "generated_report_count": len(reports) + len(required_external),
        "real_model_starts": command_ledger["entry_count"],
        "native_subagent_runs": command_ledger["native_subagent_runs"],
        "command_ledger_hash": command_ledger["ledger_hash"],
    }
