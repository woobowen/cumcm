"""Render Phase 002A reports only from current machine records."""

from __future__ import annotations

from pathlib import Path

from .models import read_json

REPORTS = {
    "automated_adjudication_dossier.md": "Automated Adjudication Dossier",
    "blind_judge_results.md": "Blind Judge Results",
    "dissent_and_counterexamples.md": "Dissent and Counterexamples",
    "meta_adjudication_record.md": "Meta-Adjudication Record",
    "decision_audit.md": "Decision Audit",
    "automated_architecture_decision.md": "Automated Architecture Decision",
    "automated_component_decisions.md": "Automated Component Decisions",
    "phase-002a-acceptance.md": "Phase 002A Acceptance",
}


def _table(rows: list[list[object]], headers: list[str]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(str(item).replace("|", "\\|") for item in row) + " |" for row in rows),
    ]


def load_report_inputs(root: Path) -> dict:
    base = root / "evals/results/phase-002a"
    decisions = [read_json(path) for path in sorted((base / "automated_decisions").glob("*.json"))]
    return {
        "freeze": read_json(base / "evidence_freeze_manifest.json"),
        "eligibility": read_json(base / "eligibility/classification.json"),
        "coverage": read_json(base / "structured_coverage/coverage.json"),
        "oracles": read_json(base / "oracle_correctness/oracles.json"),
        "process": read_json(base / "process_evidence/process.json"),
        "recovery": read_json(base / "recovery_gap_evidence/recovery.json"),
        "judges": [read_json(path) for path in sorted((base / "blind_judges").glob("*.json"))],
        "dissent": [read_json(path) for path in sorted((base / "dissent").glob("*.json"))],
        "meta": [read_json(path) for path in sorted((base / "meta_adjudication").glob("*.json"))],
        "audits": [read_json(path) for path in sorted((base / "decision_audit").glob("*.json"))],
        "decisions": decisions,
    }


def render_all(inputs: dict) -> dict[str, str]:
    summary = inputs["eligibility"]["summary"]
    decision_rows = [
        [d["decision_id"], d["decision"], d["accepted_scope"], d["next_phase_allowed"]]
        for d in inputs["decisions"]
    ]
    judge_rows = [
        [j["judge_id"], j["role"], j["recommendation"], j["identity_blind"]]
        for j in inputs["judges"]
    ]
    oracle_pass = sum(item["passed"] for item in inputs["oracles"]["cells"])
    process_pass = sum(item["passed"] for item in inputs["process"]["cells"])
    common = [
        f"Evidence freeze: `{inputs['freeze']['freeze_hash']}` (`PASS`).",
        f"Phase 002 retained {inputs['freeze']['counts']['run_attempts']} attempts: "
        f"{inputs['freeze']['counts']['completed']} completed, "
        f"{inputs['freeze']['counts']['failed']} failed, "
        f"{inputs['freeze']['counts']['recovery_affected']} recovery-affected.",
        f"Ranking-eligible primary cells: {summary['primary_complete']}; recovery-ranked cells: 0.",
        f"Balanced complete-case set: {', '.join(summary['balanced_cases'])} "
        f"({summary['balanced_case_count']} < frozen minimum {summary['minimum_balanced_cases']}); "
        f"repeats {summary['repeats']} < {summary['minimum_repeats']}.",
        f"Coverage is reported only as structured coverage; deterministic oracle pass cells: "
        f"{oracle_pass}/{len(inputs['oracles']['cells'])}; process-evidence pass cells: "
        f"{process_pass}/{len(inputs['process']['cells'])}.",
        "Recovery records are visible as gap evidence and excluded from comparative ranking.",
        "TEAM_COMPLIANCE_REVIEW is separate and cannot override a technical decision.",
    ]
    dossier = [
        "# Automated Adjudication Dossier",
        "",
        *common,
        "",
        "## Decisions",
        "",
        *_table(decision_rows, ["ID", "Decision", "Scope", "Next phase"]),
    ]
    judges = [
        "# Blind Judge Results",
        "",
        "Judge recommendations are non-voting inputs; executable evidence and hard gates dominate.",
        "",
        *_table(judge_rows, ["Judge", "Role", "Recommendation", "Identity blind"]),
    ]
    dissent = ["# Dissent and Counterexamples", ""]
    for item in inputs["dissent"]:
        dissent.extend(
            [
                f"## {item['dissent_id']}",
                "",
                item["strongest_counterexample"],
                "",
                f"Unresolved blockers: `{item['unresolved_blockers']}`.",
                "",
            ]
        )
    meta = ["# Meta-Adjudication Record", ""]
    for item in inputs["meta"]:
        meta.extend(
            [
                f"- `{item['meta_id']}`: `{item['decision']}`; majority vote used: "
                f"`{item['majority_vote_used']}`; thresholds unchanged: "
                f"`{item['thresholds_unchanged']}`."
            ]
        )
    audit = ["# Decision Audit", ""]
    for item in inputs["audits"]:
        audit.append(f"- `{item['audit_id']}`: `{item['result']}`; failures: `{item['failures']}`.")
    architecture = ["# Automated Architecture Decision", "", *common, ""]
    architecture.extend(
        line
        for d in inputs["decisions"]
        if d["decision_type"] == "ARCHITECTURE"
        for line in [
            f"Decision: `{d['decision']}`.",
            f"Reasons: `{d['reason_codes']}`.",
            f"Next phase: `{d['next_phase_allowed']}`.",
        ]
    )
    component_rows = [
        [row["mechanism_id"], row["decision"], row["accepted_scope"], row["maintenance_cost"]]
        for decision in inputs["decisions"]
        for row in decision.get("component_results", [])
    ]
    components = [
        "# Automated Component Decisions",
        "",
        "Acceptance, when present, is limited to `SPECIFICATION_ONLY`.",
        "",
        *_table(component_rows, ["Mechanism", "Decision", "Scope", "Maintenance"]),
    ]
    acceptance = [
        "# Phase 002A Acceptance",
        "",
        "Status is derived from the automated decision records and Decision Auditor outputs.",
        "",
        *common,
        "",
        "## Blind judges and dissent",
        "",
        *_table(judge_rows, ["Judge", "Role", "Recommendation", "Identity blind"]),
        "",
        "## Automated decisions",
        "",
        *_table(decision_rows, ["ID", "Decision", "Scope", "Next phase"]),
        "",
        "## Unknown and unverified",
        "",
        "The frozen evidence does not establish repeat-level comparative superiority, OS-level "
        "network denial, full upstream repository behavior, or implementation readiness. "
        "Phase 003 is not started by this report.",
    ]
    bodies = [dossier, judges, dissent, meta, audit, architecture, components, acceptance]
    return {name: "\n".join(body) + "\n" for name, body in zip(REPORTS, bodies, strict=True)}


def write_reports(root: Path, *, check: bool) -> list[str]:
    errors = []
    for name, content in render_all(load_report_inputs(root)).items():
        path = root / "reports" / name
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                errors.append(f"REPORT_MISMATCH:{path.relative_to(root)}")
        else:
            path.write_text(content, encoding="utf-8")
    return errors
