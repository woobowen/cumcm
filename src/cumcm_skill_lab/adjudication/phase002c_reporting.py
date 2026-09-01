"""Render Phase 002C reports from authoritative machine records only."""

# Report prose is intentionally kept as complete source strings.
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import check_or_write, file_sha256, read_json, sha256_bytes, sha256_json
from .native_subagent_audits import FIRST_ROUND_ROLES, POST_DECISION_ROLE, audit_path
from .phase002c_audit import AUDIT_PATH, ROUTE_PATH
from .phase002c_records import DECISION_ROOT, TEST_LEDGER_PATH
from .phase002c_replay import REPLAY_PATH
from .pre_adjudication import FREEZE_PATH, PRE_RECORD_PATH, SUFFICIENCY_PATH

REPORT_NAMES = (
    "phase002c_evidence_sufficiency.md",
    "native_subagent_audit.md",
    "pre_adjudication_decisions.md",
    "phase002c_decision_audit.md",
    "phase002c_replay.md",
    "phase002d_evidence_expansion_plan.md",
    "phase-002c-acceptance.md",
    "automated_adjudication_dossier.md",
    "formal_automated_decisions.md",
)
MANIFEST_PATH = Path("evals/results/phase-002c/reports_manifest.json")


def load_inputs(root: Path) -> dict[str, Any]:
    return {
        "freeze": read_json(root / FREEZE_PATH),
        "sufficiency": read_json(root / SUFFICIENCY_PATH),
        "pre": read_json(root / PRE_RECORD_PATH),
        "audits": [
            read_json(audit_path(root, role)) for role in (*FIRST_ROUND_ROLES, POST_DECISION_ROLE)
        ],
        "tests": read_json(root / TEST_LEDGER_PATH),
        "decisions": [read_json(path) for path in sorted((root / DECISION_ROOT).glob("*.json"))],
        "audit": read_json(root / AUDIT_PATH),
        "route": read_json(root / ROUTE_PATH),
        "replay": read_json(root / REPLAY_PATH),
        "state": read_json(root / "state/project_state.json"),
        "transport": read_json(root / "evals/results/phase-002b/recovery_manifest.json"),
    }


def _table(rows: list[list[Any]], headers: list[str]) -> list[str]:
    clean = [[str(cell).replace("|", "\\|") for cell in row] for row in rows]
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(row) + " |" for row in clean),
    ]


def _body(lines: list[str]) -> str:
    return "\n".join(lines).rstrip() + "\n"


def render_all(data: dict[str, Any]) -> dict[str, str]:
    suff = data["sufficiency"]
    actual = suff["actual"]
    thresholds = suff["thresholds"]
    decisions = data["decisions"]
    runtime = runtime_facts(data)
    decision_rows = [
        [
            item["decision_id"],
            item["decision_type"],
            ", ".join(item["target_ids"]),
            item["decision"],
            item["accepted_scope"],
            item["evidence_sufficiency"],
            item["decision_audit"],
            item["next_phase_allowed"],
        ]
        for item in decisions
    ]
    audit_rows = [
        [
            item["role"],
            item["model"],
            item["reasoning_setting"],
            item["read_only"],
            item["peer_output_access"],
            item["output_hash"],
            len(item["findings"]),
            len(item["blockers"]),
            item["verdict"],
        ]
        for item in data["audits"]
    ]
    evidence = _body(
        [
            "# Phase 002C Evidence Sufficiency",
            "",
            f"Decision: `{suff['result']}`; semantic Judges required: `{suff['semantic_judges_required']}`.",
            f"Frozen minima: balanced cases >= {thresholds['balanced_case_minimum']}; independent repeats >= {thresholds['minimum_repeats']}.",
            f"Actual: {actual['balanced_case_count']} balanced cases `{actual['balanced_cases']}`; minimum repeat depth {actual['independent_repeats']}.",
            f"Eligible primary records: {actual['eligible_primary_count']}; recovery excluded: {actual['recovery_excluded_count']}; failed excluded: {actual['failed_excluded_count']}; superseded excluded: {actual['superseded_excluded_count']}; NOT_RUN excluded: {actual['not_run_excluded_count']}.",
            f"Hard conditions: `{suff['conditions']}`. Reasons: `{suff['reason_codes']}`.",
            "Candidate aggregate scores, votes, and recovery-affected evidence were not used.",
        ]
    )
    native = _body(
        [
            "# Native Subagent Audit",
            "",
            "The first-round roles were independent, read-only, and denied peer-output visibility; the Decision Auditor received only frozen predecessor outputs.",
            "",
            *_table(
                audit_rows,
                [
                    "Role",
                    "Model",
                    "Reasoning",
                    "RO",
                    "Peer view",
                    "Output hash",
                    "Findings",
                    "Blockers",
                    "Verdict",
                ],
            ),
            "",
            f"Derived blocker tests: {len(data['tests']['tests'])}; all testable blockers resolved: `{data['tests']['all_testable_blockers_resolved']}`.",
            f"Majority vote used: `{data['audit']['majority_vote_used']}`; nested Codex used: `{runtime['nested_codex_used']}`; API key used: `{runtime['api_key_used']}`; Subagent write observed: `{runtime['writes_observed']}`.",
        ]
    )
    decisions_report = _body(
        [
            "# Pre-Adjudication Decisions",
            "",
            f"Pre-gate: `{data['pre']['decision']}`; short circuit: `{data['pre']['short_circuit']}`; semantic Judges: `{data['pre']['semantic_judges_status']}`.",
            "",
            *_table(
                decision_rows,
                [
                    "Decision ID",
                    "Type",
                    "Target",
                    "Decision",
                    "Scope",
                    "Sufficiency",
                    "Audit",
                    "Next phase",
                ],
            ),
        ]
    )
    formal = _body(["# Formal Automated Decisions", "", *decision_rows_as_markdown(decisions)])
    audit = _body(
        [
            "# Phase 002C Decision Audit",
            "",
            f"Audit `{data['audit']['audit_id']}`: `{data['audit']['result']}`; replayable: `{data['audit']['replayable']}`.",
            f"Failures: `{data['audit']['failures']}`. Blockers: `{data['audit']['blockers']}`.",
            "",
            *_table(
                [[key, value] for key, value in sorted(data["audit"]["checks"].items())],
                ["Mechanical check", "Pass"],
            ),
        ]
    )
    replay = _body(
        [
            "# Phase 002C Replay",
            "",
            f"Mode: `{data['replay']['mode']}`; stable: `{data['replay']['stable']}`; action: `{data['replay']['resulting_action']}`.",
            f"Route: `{data['route']['next_phase_allowed']}`; Phase 003 allowed: `{data['route']['phase003_allowed']}`; Phase 002D started: `{data['route']['phase002d_started']}`.",
            "",
            *_table(
                [[key, value] for key, value in sorted(data["replay"]["variants"].items())],
                ["Variant", "Normalized hash"],
            ),
        ]
    )
    expansion = _render_expansion(data)
    acceptance_lines = _acceptance_lines(data, decision_rows, audit_rows)
    acceptance = _body(["# Phase 002C Acceptance", "", *acceptance_lines])
    dossier = _body(
        [
            "# Automated Adjudication Dossier",
            "",
            f"Phase 002 produced candidate dynamic runs; Phase 002A rebuilt deterministic evidence classification; Phase 002B preserved {runtime['transport_attempt_count']} `{runtime['transport_failure_class']}` recovery failures and transport-repaired is `{runtime['transport_repaired']}`; {runtime['phase002c_outcome_summary']}",
            "",
            *acceptance_lines,
        ]
    )
    return {
        "phase002c_evidence_sufficiency.md": evidence,
        "native_subagent_audit.md": native,
        "pre_adjudication_decisions.md": decisions_report,
        "phase002c_decision_audit.md": audit,
        "phase002c_replay.md": replay,
        "phase002d_evidence_expansion_plan.md": expansion,
        "phase-002c-acceptance.md": acceptance,
        "automated_adjudication_dossier.md": dossier,
        "formal_automated_decisions.md": formal,
    }


def decision_rows_as_markdown(decisions: list[dict[str, Any]]) -> list[str]:
    rows = [
        [
            item["decision_id"],
            item["decision_type"],
            item["decision"],
            item["accepted_scope"],
            item["decision_audit"],
            item["next_phase_allowed"],
        ]
        for item in decisions
    ]
    return _table(rows, ["Decision ID", "Type", "Decision", "Scope", "Audit", "Next phase"])


def runtime_facts(data: dict[str, Any]) -> dict[str, Any]:
    audits = data["audits"]
    pre = data["pre"]
    state = data["state"]
    transport = data["transport"]
    phase002d_started = data["route"]["phase002d_started"]
    if pre["short_circuit"]:
        phase002c_outcome_summary = (
            f"Phase 002C recorded `{pre['decision']}` through an evidence-sufficiency "
            f"short circuit; semantic Judges are `{pre['semantic_judges_status']}`."
        )
    else:
        phase002c_outcome_summary = (
            f"Phase 002C recorded `{pre['decision']}` without an evidence-sufficiency "
            f"short circuit; semantic Judges are `{pre['semantic_judges_status']}`."
        )
    return {
        "phase002d_started": phase002d_started,
        "phase002d_report_status": "Execution Recorded"
        if phase002d_started
        else "Draft; Not Executed",
        "phase002c_outcome_summary": phase002c_outcome_summary,
        "selected_architecture": state["selected_architecture"],
        "third_party_integrated": state["third_party_integrated"],
        "skill_capability_status": state["skill_capability_status"],
        "nested_codex_used": any(item["nested_codex_used"] for item in audits),
        "api_key_used": any(item["api_key_used"] for item in audits),
        "writes_observed": any(item["writes_observed"] for item in audits),
        "transport_repaired": transport["status"] != "AUTOMATED_ADJUDICATION_INCOMPLETE",
        "transport_attempt_count": len(transport["diagnostics"]),
        "transport_failure_class": transport["terminal_failure_class"],
    }


def _render_expansion(data: dict[str, Any]) -> str:
    suff = data["sufficiency"]
    runtime = runtime_facts(data)
    cost_audit = next(item for item in data["audits"] if item["role"] == "dissent_and_cost_auditor")
    cost = cost_audit["cost_assessment"]
    arms = suff["required_arms"]
    minimum_cases = suff["thresholds"]["balanced_case_minimum"]
    minimum_repeats = suff["thresholds"]["minimum_repeats"]
    counts = suff["actual"]["cell_repeat_counts"]
    costs = {
        case: sum(max(0, minimum_repeats - arm_counts.get(arm, 0)) for arm in arms)
        for case, arm_counts in counts.items()
    }
    selected_cases = sorted(
        counts,
        key=lambda case: (0 if case in suff["actual"]["balanced_cases"] else 1, costs[case], case),
    )[:minimum_cases]
    missing = [
        f"{case}:{arm}×{minimum_repeats - counts[case].get(arm, 0)}"
        for case in selected_cases
        for arm in arms
        if counts[case].get(arm, 0) < minimum_repeats
    ]
    minimum_new_runs = sum(costs[case] for case in selected_cases)
    return _body(
        [
            f"# Phase 002D Evidence Expansion Plan ({runtime['phase002d_report_status']})",
            "",
            f"Goal: at least {minimum_cases} balanced cases with at least {minimum_repeats} independent primary repeats for every required arm.",
            f"Currently balanced: `{suff['actual']['balanced_cases']}`; all balanced cells and newly completed cells require repeat depth {minimum_repeats}.",
            f"Minimum frozen completion batch: {minimum_new_runs} successful new primary runs across cases `{selected_cases}`; arm × case shortfalls: `{missing}`. Recovery-affected cells remain missing for ranking purposes.",
            "Add numerical-ground-truth synthetic cases only where they enlarge model classes without exposing held-out answers. Prefer deterministic oracles and compact, case-scoped inputs; never resend the full repository or historical transcripts.",
            "Run ordinary Codex and the formal Skill against identical hash-bound prompts, seeds, limits, and oracle checks. Candidate labels remain anonymous. Any revealed validation answer permanently demotes that case to development.",
            f"Token-cost evidence: {cost['token_cost']}",
            f"Time-cost evidence: {cost['time_cost']}",
            "Before any expansion batch, run one compact hash-bound deterministic-oracle pilot with the intended model. Freeze separate successful-run, retry, token, elapsed-time, and total-spend limits from that pilot; do not reuse an unsupported fixed per-run ceiling.",
            "Stop when minima pass, any mandatory hard gate fails, the frozen run budget is exhausted, input hashes diverge, leakage is detected, or two consecutive infrastructure failures make the planned cell non-comparable.",
            "Reassess only after expansion: accepted-versus-done workflow state, claim-evidence support gate, hash-bound reproducibility manifest, and leakage-safe model comparison gate. Do not integrate in Phase 002D.",
        ]
    )


def _acceptance_lines(
    data: dict[str, Any], decision_rows: list[list[Any]], audit_rows: list[list[Any]]
) -> list[str]:
    suff = data["sufficiency"]
    route = data["route"]
    runtime = runtime_facts(data)
    return [
        f"Technical status: `{'AUTOMATED_ADJUDICATION_COMPLETE' if data['audit']['result'] == 'PASS' and data['replay']['stable'] else 'AUTOMATED_ADJUDICATION_INCOMPLETE'}`.",
        f"Evidence sufficiency: `{suff['result']}`; balanced cases {suff['actual']['balanced_case_count']}/{suff['thresholds']['balanced_case_minimum']}; repeats {suff['actual']['independent_repeats']}/{suff['thresholds']['minimum_repeats']}.",
        f"Decision audit: `{data['audit']['result']}`; deterministic replay: `{data['replay']['stable']}`.",
        f"Next phase allowed: `{route['next_phase_allowed']}`. Phase 003 allowed: `{route['phase003_allowed']}`. Phase 002D started: `{runtime['phase002d_started']}`.",
        f"Selected architecture: `{runtime['selected_architecture']}`; third-party integrated: `{runtime['third_party_integrated']}`; Skill capability: `{runtime['skill_capability_status']}`.",
        f"Phase 002B transport repaired: `{runtime['transport_repaired']}`. Preserved recovery attempts: {runtime['transport_attempt_count']} with `{runtime['transport_failure_class']}`; nested Codex used: `{runtime['nested_codex_used']}`; API key used: `{runtime['api_key_used']}`.",
        "",
        "## Native audits",
        "",
        *_table(
            audit_rows,
            [
                "Role",
                "Model",
                "Reasoning",
                "RO",
                "Peer view",
                "Output hash",
                "Findings",
                "Blockers",
                "Verdict",
            ],
        ),
        "",
        "## Decisions",
        "",
        *_table(
            decision_rows,
            [
                "Decision ID",
                "Type",
                "Target",
                "Decision",
                "Scope",
                "Sufficiency",
                "Audit",
                "Next phase",
            ],
        ),
        "",
        "## Integrity",
        "",
        f"Input freeze: `{data['freeze']['freeze_hash']}`; evidence: `{data['freeze']['evidence_hash']}`; report inputs are machine records only.",
    ]


def write_reports(root: Path, *, check: bool) -> dict[str, Any]:
    rendered = render_all(load_inputs(root))
    errors: list[str] = []
    for name in REPORT_NAMES:
        path = root / "reports" / name
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered[name]:
                errors.append(f"REPORT_MISMATCH:{path.relative_to(root)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered[name], encoding="utf-8")
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002C-REPORTS",
        "source_record_hashes": _report_source_hashes(root),
        "reports": {
            f"reports/{name}": sha256_bytes(rendered[name].encode()) for name in REPORT_NAMES
        },
    }
    manifest["content_hash"] = sha256_json(manifest)
    errors.extend(check_or_write(root / MANIFEST_PATH, manifest, check=check))
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _report_source_hashes(root: Path) -> dict[str, str]:
    paths = [
        FREEZE_PATH,
        SUFFICIENCY_PATH,
        PRE_RECORD_PATH,
        TEST_LEDGER_PATH,
        AUDIT_PATH,
        ROUTE_PATH,
        REPLAY_PATH,
        Path("state/project_state.json"),
        Path("evals/results/phase-002b/recovery_manifest.json"),
        *[path.relative_to(root) for path in sorted((root / DECISION_ROOT).glob("*.json"))],
        *[
            audit_path(root, role).relative_to(root)
            for role in (*FIRST_ROUND_ROLES, POST_DECISION_ROLE)
        ],
    ]
    return {path.as_posix(): file_sha256(root / path) for path in paths}
