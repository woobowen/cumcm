"""Render Phase 002A reports only from current machine records."""

from __future__ import annotations

from pathlib import Path

from .models import read_json

REPORTS = (
    "automated_adjudication_dossier.md",
    "blind_judge_results.md",
    "dissent_and_counterexamples.md",
    "meta_adjudication_record.md",
    "decision_audit.md",
    "automated_architecture_decision.md",
    "automated_component_decisions.md",
    "phase-002a-acceptance.md",
)


def _table(rows: list[list[object]], headers: list[str]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(str(item).replace("|", "\\|") for item in row) + " |" for row in rows),
    ]


def load_report_inputs(root: Path) -> dict:
    base = root / "evals/results/phase-002a"
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
        "decisions": [
            read_json(path) for path in sorted((base / "automated_decisions").glob("*.json"))
        ],
        "runtime_failures": [
            read_json(path) for path in sorted((base / "runtime").glob("blind_failure_*.json"))
        ],
        "adversarial_runtime": read_json(base / "runtime/adversarial_agent_runs.json"),
    }


def render_all(inputs: dict) -> dict[str, str]:
    summary = inputs["eligibility"]["summary"]
    complete = bool(
        inputs["decisions"] and inputs["judges"] and inputs["meta"] and inputs["audits"]
    )
    status = "AUTOMATED_ADJUDICATION_COMPLETE" if complete else "AUTOMATED_ADJUDICATION_INCOMPLETE"
    decision_rows = [
        [d["decision_id"], d["decision"], d["accepted_scope"], d["next_phase_allowed"]]
        for d in inputs["decisions"]
    ]
    judge_rows = [
        [j["judge_id"], j["role"], j["recommendation"], j["identity_blind"]]
        for j in inputs["judges"]
        if "judge_id" in j
    ]
    failure_rows = [
        [
            item["attempt_id"],
            item["role"],
            item["result"],
            item["duration_seconds"],
            item["blocker"],
        ]
        for item in inputs["runtime_failures"]
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
        f"Coverage is structured coverage only; deterministic oracle pass cells: "
        f"{oracle_pass}/{len(inputs['oracles']['cells'])}; process-evidence pass cells: "
        f"{process_pass}/{len(inputs['process']['cells'])}.",
        "Recovery records are visible as gap evidence and excluded from comparative ranking.",
        "TEAM_COMPLIANCE_REVIEW is separate and cannot override a technical decision.",
    ]
    dossier = [
        "# Automated Adjudication Dossier",
        "",
        f"Status: `{status}`.",
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
        "",
        "No valid Judge row means no technical decision may be emitted.",
        "",
        *_table(failure_rows, ["Attempt", "Role", "Result", "Seconds", "Blocker"]),
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
    dissent.extend(
        [
            "The retained real Dissent was produced before candidate anonymization and is excluded",
            "from formal blind adjudication. It remains adversarial uncertainty only.",
        ]
    )
    meta = ["# Meta-Adjudication Record", ""]
    for item in inputs["meta"]:
        if "meta_id" in item:
            meta.append(
                f"- `{item['meta_id']}`: `{item['decision']}`; majority vote used: "
                f"`{item['majority_vote_used']}`; thresholds unchanged: "
                f"`{item['thresholds_unchanged']}`."
            )
    if not inputs["meta"]:
        meta.append("No Meta-Adjudicator output exists because no Blind Judge output was valid.")
    audit = ["# Decision Audit", ""]
    for item in inputs["audits"]:
        if "audit_id" in item:
            audit.append(
                f"- `{item['audit_id']}`: `{item['result']}`; failures: `{item['failures']}`."
            )
    if not inputs["audits"]:
        audit.append("No Decision Auditor output exists because no machine decision was emitted.")
    architecture = ["# Automated Architecture Decision", "", *common, ""]
    architecture.extend(
        line
        for decision in inputs["decisions"]
        if decision["decision_type"] == "ARCHITECTURE"
        for line in [
            f"Decision: `{decision['decision']}`.",
            f"Reasons: `{decision['reason_codes']}`.",
            f"Next phase: `{decision['next_phase_allowed']}`.",
        ]
    )
    if not any(d["decision_type"] == "ARCHITECTURE" for d in inputs["decisions"]):
        architecture.extend(
            [
                "No valid automated architecture decision exists.",
                "Technical status: `AUTOMATED_ADJUDICATION_INCOMPLETE`.",
                "`next_phase_allowed=null`.",
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
    if not component_rows:
        components.extend(
            [
                "",
                "No mechanism is automatically accepted, rejected, or advanced for specification",
                "because Meta-Adjudicator and Decision Auditor did not run.",
            ]
        )
    acceptance = [
        "# Phase 002A Acceptance",
        "",
        f"Status: `{status}`.",
        "",
        "Status is derived from machine records; missing decisions are never inferred.",
        "",
        *common,
        "",
        "## Blind judges and dissent",
        "",
        *_table(judge_rows, ["Judge", "Role", "Recommendation", "Identity blind"]),
        "",
        "The retained unblinded Dissent is excluded from formal adjudication.",
        "",
        "## Automated decisions",
        "",
        *_table(decision_rows, ["ID", "Decision", "Scope", "Next phase"]),
        "",
        "## Runtime failures",
        "",
        *_table(failure_rows, ["Attempt", "Role", "Result", "Seconds", "Blocker"]),
        "",
        "Three consecutive formal Blind Judge attempts failed before structured output because",
        "Codex Responses transport disconnected. No Meta-Adjudicator or Decision Auditor was run.",
        "The two output-schema capability prechecks did not start a model. The earlier unblinded",
        "Dissent did start a model and is retained but excluded from formal blind evidence.",
        "",
        "Continue only after transport recovers:",
        "`./.venv/bin/python scripts/run_blind_adjudication.py "
        "--config adjudication/configs/phase-002a.yaml`.",
        "",
        "## Unknown and unverified",
        "",
        "The frozen evidence does not establish repeat-level comparative superiority, OS-level "
        "network denial, full upstream repository behavior, implementation readiness, a valid "
        "architecture decision, or any accepted component specification. Phase 003 is not started. "
        "`next_phase_allowed` remains `null`.",
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
