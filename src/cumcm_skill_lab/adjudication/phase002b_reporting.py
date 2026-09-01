"""Render Phase 002B reports exclusively from tracked machine records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .formal_outputs import final_decision_paths, formal_output_path
from .models import read_json
from .phase002b_status import classify_completion, phase003_allowed

REPORT_NAMES = (
    "transport_recovery.md",
    "formal_blind_judges.md",
    "formal_blind_dissent.md",
    "formal_meta_adjudication.md",
    "formal_decision_audit.md",
    "formal_automated_decisions.md",
    "phase-002b-acceptance.md",
    "automated_adjudication_dossier.md",
    "blind_judge_results.md",
    "meta_adjudication_record.md",
    "decision_audit.md",
    "automated_architecture_decision.md",
    "automated_component_decisions.md",
)


def load_inputs(root: Path) -> dict[str, Any]:
    phase = root / "evals/results/phase-002b"
    role_ledger = read_json(phase / "role_ledger.json")
    decisions = [read_json(path) for path in final_decision_paths(root)]
    common = {
        "freeze": read_json(phase / "input_freeze_manifest.json"),
        "eligibility": read_json(root / "evals/results/phase-002a/eligibility/classification.json"),
        "recovery": read_json(
            root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json"
        ),
        "old_failures": [
            read_json(path)
            for path in sorted(
                (root / "evals/results/phase-002a/runtime").glob("blind_failure_*.json")
            )
        ],
        "budget": read_json(phase / "transport_diagnostics/run_budget.json"),
        "roles": role_ledger["roles"],
    }
    replay_path = phase / "replay/replay.json"
    meta_path = formal_output_path(root, "EVIDENCE_META_ADJUDICATOR")
    audit_path = formal_output_path(root, "DECISION_AUDITOR")
    if len(decisions) != 3 or not all(
        path.is_file() for path in (replay_path, meta_path, audit_path)
    ):
        recovery_manifest = phase / "recovery_manifest.json"
        return {
            **common,
            "incomplete": True,
            "recovery_manifest": read_json(recovery_manifest),
            "diagnostics": [
                read_json(root / relative)
                for relative in read_json(recovery_manifest)["diagnostics"]
            ],
            "decisions": [],
        }
    return {
        **common,
        "incomplete": False,
        "judges": [
            read_json(formal_output_path(root, role))
            for role in (
                "CORRECTNESS_JUDGE",
                "SCIENTIFIC_VALIDITY_JUDGE",
                "ENGINEERING_REPRODUCIBILITY_JUDGE",
            )
        ],
        "dissent": read_json(formal_output_path(root, "BLIND_DISSENT_JUDGE")),
        "meta": read_json(meta_path),
        "audit": read_json(audit_path),
        "decisions": decisions,
        "replay": read_json(replay_path),
    }


def render_all(inputs: dict[str, Any]) -> dict[str, str]:
    if inputs["incomplete"]:
        return _render_incomplete(inputs)
    status = classify_completion(
        inputs["roles"], inputs["decisions"], inputs["audit"], inputs["replay"]
    )
    next_allowed = phase003_allowed(inputs["decisions"], inputs["audit"], inputs["replay"])
    role_rows = [
        [
            row["role_id"],
            row["adapter"],
            row["attempt"],
            row["status"],
            row["thread_id_hash"],
            row["output_hash"],
            row["schema_valid"],
        ]
        for row in inputs["roles"]
    ]
    judge_rows = [
        [
            item["role"],
            item["recommendation"],
            item["evidence_sufficiency"],
            item["confidence"],
            len(item["unresolved_blockers"]),
        ]
        for item in inputs["judges"]
    ]
    decision_rows = [
        [
            item["decision_id"],
            item["decision_type"],
            item["decision"],
            item["accepted_scope"],
            item["evidence_sufficiency"],
            item["decision_audit"],
            item["next_phase_allowed"],
        ]
        for item in inputs["decisions"]
    ]
    component_rows = [
        [
            component["mechanism_id"],
            component["decision"],
            component["accepted_scope"],
            component["maintenance_cost"],
        ]
        for decision in inputs["decisions"]
        for component in decision.get("component_results", [])
    ]
    starts = inputs["budget"]["starts"]
    exec_starts = sum(item["adapter"] == "EXEC_RESUMABLE" for item in starts)
    app_starts = sum(item["adapter"] == "APP_SERVER_RESUMABLE" for item in starts)
    resumes = sum(item["start_kind"] == "RESUME" for item in starts)
    token_totals = _token_totals(starts)
    transport = [
        "# Phase 002B Transport Recovery",
        "",
        f"Status: `{status}`.",
        "",
        "Phase 002A retained three failed Correctness attempts; no historical failure record "
        "was deleted or rewritten.",
        "",
        f"Phase 002B starts: {len(starts)}/8; exec: {exec_starts}; App Server: {app_starts}; "
        f"resume: {resumes}; remaining: {8 - len(starts)}.",
        f"Observed token usage: `{token_totals}`.",
        "Authentication remained the existing ChatGPT-managed Codex login. No API key or "
        "API-billing migration was used.",
        "",
        *_table(
            role_rows,
            ["Role", "Adapter", "Attempt", "Status", "Session hash", "Output hash", "Schema"],
        ),
    ]
    blind = [
        "# Formal Blind Judges",
        "",
        "These are independent, identity-blind, non-voting role records.",
        "",
        *_table(
            judge_rows,
            ["Role", "Recommendation", "Sufficiency", "Confidence", "Open blockers"],
        ),
    ]
    dissent = [
        "# Formal Blind Dissent",
        "",
        f"Recommendation: `{inputs['dissent']['recommendation']}`.",
        f"Strongest dissent: {inputs['dissent']['strongest_dissent']}",
        f"Evidence: `{inputs['dissent']['strongest_dissent_evidence_refs']}`.",
        f"Unresolved blockers: `{inputs['dissent']['unresolved_blockers']}`.",
        "The earlier unblinded Phase 002A Dissent remains excluded from this formal role.",
    ]
    meta = [
        "# Formal Meta-Adjudication",
        "",
        f"Meta ID: `{inputs['meta']['meta_id']}`.",
        f"Frozen policy: `{inputs['meta']['policy_hash']}`.",
        f"Evidence hash: `{inputs['meta']['evidence_hash']}`.",
        f"Hard Gate status: `{inputs['meta']['hard_gate_status']}`.",
        f"Evidence sufficiency: `{inputs['meta']['evidence_sufficiency']}`.",
        "Thresholds unchanged; no majority vote, human technical Gate, or recovery ranking "
        "was used.",
        "",
        *_table(
            decision_rows,
            ["Decision", "Type", "Value", "Scope", "Sufficiency", "Audit", "Next phase"],
        ),
    ]
    audit = [
        "# Formal Decision Audit",
        "",
        f"Audit ID: `{inputs['audit']['audit_id']}`.",
        f"Result: `{inputs['audit']['result']}`; replayable: `{inputs['audit']['replayable']}`.",
        f"Failures: `{inputs['audit']['failures']}`.",
        f"Blockers: `{inputs['audit']['blockers']}`.",
        "",
        *_table(
            [[name, value] for name, value in sorted(inputs["audit"]["checks"].items())],
            ["Check", "Pass"],
        ),
    ]
    decisions = [
        "# Formal Automated Decisions",
        "",
        *_table(
            decision_rows,
            ["Decision", "Type", "Value", "Scope", "Sufficiency", "Audit", "Next phase"],
        ),
        "",
        "## Component specifications",
        "",
        *_table(component_rows, ["Mechanism", "Decision", "Scope", "Maintenance"]),
    ]
    acceptance = _acceptance(
        inputs,
        status=status,
        next_allowed=next_allowed,
        role_rows=role_rows,
        decision_rows=decision_rows,
        component_rows=component_rows,
        token_totals=token_totals,
    )
    architecture = next(
        item for item in inputs["decisions"] if item["decision_type"] == "ARCHITECTURE"
    )
    architecture_report = [
        "# Automated Architecture Decision",
        "",
        f"Decision: `{architecture['decision']}`.",
        f"Accepted scope: `{architecture['accepted_scope']}`.",
        f"Reasons: `{architecture['reason_codes']}`.",
        f"Next phase: `{architecture['next_phase_allowed']}`.",
    ]
    return {
        "transport_recovery.md": _body(transport),
        "formal_blind_judges.md": _body(blind),
        "formal_blind_dissent.md": _body(dissent),
        "formal_meta_adjudication.md": _body(meta),
        "formal_decision_audit.md": _body(audit),
        "formal_automated_decisions.md": _body(decisions),
        "phase-002b-acceptance.md": _body(acceptance),
        "automated_adjudication_dossier.md": _body(
            ["# Automated Adjudication Dossier", "", *acceptance[2:]]
        ),
        "blind_judge_results.md": _body(blind).replace(
            "# Formal Blind Judges", "# Blind Judge Results", 1
        ),
        "meta_adjudication_record.md": _body(meta).replace(
            "# Formal Meta-Adjudication", "# Meta-Adjudication Record", 1
        ),
        "decision_audit.md": _body(audit).replace("# Formal Decision Audit", "# Decision Audit", 1),
        "automated_architecture_decision.md": _body(architecture_report),
        "automated_component_decisions.md": _body(
            [
                "# Automated Component Decisions",
                "",
                *_table(component_rows, ["Mechanism", "Decision", "Scope", "Maintenance"]),
            ]
        ),
    }


def write_reports(root: Path, *, check: bool) -> list[str]:
    errors: list[str] = []
    outputs = render_all(load_inputs(root))
    for name in REPORT_NAMES:
        path = root / "reports" / name
        expected = outputs[name]
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                errors.append(f"REPORT_MISMATCH:reports/{name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    return errors


def _render_incomplete(inputs: dict[str, Any]) -> dict[str, str]:
    recovery = inputs["recovery_manifest"]
    role_rows = [
        [
            row["role_id"],
            row["adapter"],
            row["attempt"],
            row["status"],
            row["thread_id_hash"],
            row["schema_valid"],
        ]
        for row in inputs["roles"]
    ]
    failure_rows = [
        [
            item["attempt"],
            item["start_kind"],
            item["adapter"],
            item["duration_seconds"],
            item["failure_class"],
            item["session_id_hash"],
            item["raw_event_hash"],
            item["next_adapter"],
        ]
        for item in inputs["diagnostics"]
    ]
    summary = inputs["eligibility"]["summary"]
    role_table = _table(
        role_rows,
        ["Role", "Adapter", "Attempt", "Status", "Session hash", "Schema"],
    )
    failure_table = _table(
        failure_rows,
        [
            "Attempt",
            "Kind",
            "Adapter",
            "Seconds",
            "Failure",
            "Session hash",
            "Raw hash",
            "Next",
        ],
    )
    transport = [
        "# Phase 002B Transport Recovery",
        "",
        "Status: `AUTOMATED_ADJUDICATION_INCOMPLETE`.",
        "",
        "Correctness used the primary persistent exec session and the one permitted exact-session "
        "resume. Both ended in `RESPONSES_CONNECT_RESET`; the two-attempt role limit then stopped "
        "the formal chain. App Server was not started because a third attempt is prohibited.",
        "",
        *failure_table,
        "",
        f"Phase 002B starts: {recovery['phase002b_model_starts']}/8; remaining: "
        f"{recovery['phase002b_remaining_budget']}. Token usage was not emitted by the failed "
        "turns.",
        "Raw events, stderr, exact session IDs and hidden reasoning remain ignored; only hashes "
        "and sanitized event counts are tracked.",
    ]
    blind = [
        "# Formal Blind Judges",
        "",
        "No Schema-valid formal Judge output exists. Correctness exhausted its two allowed "
        "transport attempts before structured output; later roles were not started.",
        "",
        *role_table,
    ]
    dissent = [
        "# Formal Blind Dissent",
        "",
        "`BLIND_DISSENT_JUDGE` was not run because Correctness did not complete. The earlier "
        "unblinded Phase 002A Dissent remains preserved and excluded from formal evidence.",
    ]
    meta = [
        "# Formal Meta-Adjudication",
        "",
        "Not run. Four valid blind role outputs are mandatory; zero were completed. Meta did not "
        "infer or synthesize missing Judge results.",
    ]
    audit = [
        "# Formal Decision Audit",
        "",
        "Not run. No Meta output or automated decision proposal exists.",
    ]
    decisions = [
        "# Formal Automated Decisions",
        "",
        "No automated technical decision was emitted. `automated_decision_ids=[]`, "
        "`selected_architecture=null`, `accepted_component_specifications=[]`, and "
        "`next_phase_allowed=null`.",
    ]
    acceptance = [
        "# Phase 002B Acceptance",
        "",
        "Status: `AUTOMATED_ADJUDICATION_INCOMPLETE`.",
        "",
        "## Frozen evidence and scope",
        "",
        f"Phase 002B input freeze `{inputs['freeze']['freeze_hash']}` and evidence hash "
        f"`{inputs['freeze']['evidence_hash']}` remain valid. Phase 002 candidate runs and the "
        "Phase 002A freeze were not modified or rerun.",
        f"Balanced complete cases remain {summary['balanced_case_count']}/"
        f"{summary['minimum_balanced_cases']}; repeats remain {summary['repeats']}/"
        f"{summary['minimum_repeats']}; frozen comparative sufficiency is "
        f"`{summary['comparative_sufficiency']}`.",
        f"All {len(inputs['recovery']['records'])} recovery-affected records remain gap-only and "
        "ranking-ineligible.",
        "",
        "## Transport attempts",
        "",
        *failure_table,
        "",
        f"Previous model starts: 4. New maximum: 8. New starts: "
        f"{recovery['phase002b_model_starts']}. Completed formal roles: 0. Failed role: "
        f"`CORRECTNESS_JUDGE`. Resume starts: 1. Remaining budget: "
        f"{recovery['phase002b_remaining_budget']}. Observed token usage: unavailable/empty.",
        "",
        "## Formal chain",
        "",
        *role_table,
        "",
        "Scientific Validity, Engineering/Reproducibility, Blind Dissent, Meta and Auditor were "
        "not started. Deterministic replay was not run because no decisions exist.",
        "",
        "## Automated decisions",
        "",
        "No architecture, recovery-policy or component decision exists. No candidate, "
        "architecture, base or component specification was accepted or rejected by a completed "
        "adjudication.",
        "",
        "## API and authentication",
        "",
        "Used the existing ChatGPT-managed Codex login. No API key was read, requested, printed or "
        "used. API billing and login mode were not changed. No credential or auth cache is "
        "tracked.",
        "",
        "## Boundary",
        "",
        "`base_selected=false`; `third_party_integrated=false`; formal Skill capability remains "
        "`SCAFFOLD_ONLY`; `next_phase_allowed=null`. `PHASE-SKILL-INTEGRATION-003` is prohibited "
        "and was not entered.",
        "",
        "## Unknown and unverified",
        "",
        "Formal correctness, scientific validity, engineering reproducibility, blind dissent, "
        "Meta conclusions, Audit result, replay stability, technical acceptance and implementation "
        "readiness remain unknown. Transport recovery did not yield a structured formal output, so "
        "none of these facts are inferred.",
    ]
    architecture = [
        "# Automated Architecture Decision",
        "",
        "No valid automated architecture decision exists. `selected_architecture=null`; "
        "`next_phase_allowed=null`.",
    ]
    components = [
        "# Automated Component Decisions",
        "",
        "No component decision exists and no specification is accepted.",
    ]
    return {
        "transport_recovery.md": _body(transport),
        "formal_blind_judges.md": _body(blind),
        "formal_blind_dissent.md": _body(dissent),
        "formal_meta_adjudication.md": _body(meta),
        "formal_decision_audit.md": _body(audit),
        "formal_automated_decisions.md": _body(decisions),
        "phase-002b-acceptance.md": _body(acceptance),
        "automated_adjudication_dossier.md": _body(
            ["# Automated Adjudication Dossier", "", *acceptance[2:]]
        ),
        "blind_judge_results.md": _body(blind).replace(
            "# Formal Blind Judges", "# Blind Judge Results", 1
        ),
        "meta_adjudication_record.md": _body(meta).replace(
            "# Formal Meta-Adjudication", "# Meta-Adjudication Record", 1
        ),
        "decision_audit.md": _body(audit).replace("# Formal Decision Audit", "# Decision Audit", 1),
        "automated_architecture_decision.md": _body(architecture),
        "automated_component_decisions.md": _body(components),
    }


def _acceptance(
    inputs: dict[str, Any],
    *,
    status: str,
    next_allowed: bool,
    role_rows: list[list[Any]],
    decision_rows: list[list[Any]],
    component_rows: list[list[Any]],
    token_totals: dict[str, int],
) -> list[str]:
    summary = inputs["eligibility"]["summary"]
    replay = inputs["replay"]
    return [
        "# Phase 002B Acceptance",
        "",
        f"Status: `{status}`.",
        "",
        "## Scope and frozen evidence",
        "",
        "Phase 002 supplied the original candidate runs; Phase 002A supplied frozen evidence "
        "and the incomplete transport history; Phase 002B supplied only transport recovery and "
        "formal automated adjudication. Phase 002 runs were not repeated.",
        f"Input freeze: `{inputs['freeze']['freeze_hash']}`; evidence: "
        f"`{inputs['freeze']['evidence_hash']}`.",
        f"Balanced complete cases: {summary['balanced_case_count']}/"
        f"{summary['minimum_balanced_cases']}; repeats: {summary['repeats']}/"
        f"{summary['minimum_repeats']}; comparative sufficiency: "
        f"`{summary['comparative_sufficiency']}`.",
        f"Recovery records retained as gap-only evidence: {len(inputs['recovery']['records'])}; "
        "ranking eligible: 0.",
        "",
        "## Formal roles",
        "",
        *_table(
            role_rows,
            ["Role", "Adapter", "Attempt", "Status", "Session hash", "Output hash", "Schema"],
        ),
        "",
        "## Automated decisions",
        "",
        *_table(
            decision_rows,
            ["Decision", "Type", "Value", "Scope", "Sufficiency", "Audit", "Next phase"],
        ),
        "",
        "## Components",
        "",
        *_table(component_rows, ["Mechanism", "Decision", "Scope", "Maintenance"]),
        "",
        "## Audit and replay",
        "",
        f"Audit: `{inputs['audit']['result']}`; failures: `{inputs['audit']['failures']}`; "
        f"blockers: `{inputs['audit']['blockers']}`.",
        f"Replay stable: `{replay['stable']}`; original hash: "
        f"`{replay['variants']['original']}`; variants: `{replay['variants']}`.",
        "",
        "## Runtime and authentication",
        "",
        f"Previous model starts: 4; Phase 002B starts: {len(inputs['budget']['starts'])}/8; "
        f"remaining: {8 - len(inputs['budget']['starts'])}; observed tokens: `{token_totals}`.",
        "Used the existing ChatGPT-managed Codex login. No API key was read, requested, printed, "
        "or used; API billing and login mode were not changed.",
        "",
        "## Boundary",
        "",
        f"Phase 003 allowed: `{next_allowed}`. `third_party_integrated=false`; "
        "`base_selected=false`; formal Skill capability remains `SCAFFOLD_ONLY`.",
        "No third-party code or candidate Skill was selected, copied, installed, or integrated.",
        "",
        "## Unknown and unverified",
        "",
        "This phase does not establish implementation readiness, production readiness, complete "
        "external validity, OS-level network denial, or any fact beyond the frozen evidence and "
        "formal role outputs. Non-acceptance is a valid completed result and is not converted into "
        "acceptance by report generation.",
    ]


def _token_totals(starts: list[dict[str, Any]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for start in starts:
        for key, value in start.get("token_usage", {}).items():
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return dict(sorted(totals.items()))


def _table(rows: list[list[Any]], headers: list[str]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *(
            "| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |"
            for row in rows
        ),
    ]


def _body(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"
