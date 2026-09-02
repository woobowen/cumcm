"""Generate the complete Phase 002D-R2 report set from machine records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import read_json, read_yaml, sha256_bytes, sha256_json

from .adjudication import DECISION_FILES, DECISION_ROOT, SHADOW_DECISION_ID
from .models import COMPONENT_IDS, CREATED_AT, RESULT_ROOT
from .provenance_validator import PROVENANCE_ROOT
from .replay import REPLAY_PATH
from .validation import VALIDATION_COMMANDS

GENERATED = "<!-- GENERATED FILE — DO NOT EDIT -->\n"
MANIFEST_PATH = RESULT_ROOT / "reports_manifest.json"
REPORT_PATHS = (
    "reports/phase002d_r2_component_specs.md",
    "reports/phase002d_r2_clean_room_provenance.md",
    "reports/phase002d_r2_interaction_contract.md",
    "reports/phase002d_r2_architecture_candidates.md",
    "reports/phase002d_r2_benchmark_design.md",
    "reports/phase002d_r2_threshold_policy.md",
    "reports/phase002d_r2_experiment_protocol.md",
    "reports/phase002d_r2_subagent_audits.md",
    "reports/phase002d_r2_automated_decisions.md",
    "reports/phase002d_r2_decision_audit.md",
    "reports/phase002d_r2_replay.md",
    "reports/phase-002d-r2-acceptance.md",
    "reports/automated_adjudication_dossier.md",
    "reports/formal_automated_decisions.md",
)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _decisions(root: Path) -> list[dict[str, Any]]:
    return [
        read_json(root / DECISION_ROOT / DECISION_FILES[decision_id])
        for decision_id in sorted(DECISION_FILES)
    ]


def _decision_table(decisions: list[dict[str, Any]]) -> str:
    return _table(
        ["Decision", "Result", "Phase scope", "Next route", "Hash"],
        [
            [
                item["automated_decision"]["decision_id"],
                item["automated_decision"]["decision"],
                item["phase_scope"] or "NONE",
                item["automated_decision"]["next_phase_allowed"] or "NONE",
                item["decision_hash"],
            ]
            for item in decisions
        ],
    )


def build_reports(root: Path) -> dict[str, str]:
    specs = [
        read_yaml(root / f"specifications/components/{component_id}.yaml")
        for component_id in COMPONENT_IDS
    ]
    provenance_registry = read_yaml(root / "specifications/clean_room_provenance.yaml")
    source_complete = read_json(root / PROVENANCE_ROOT / "source_completeness.json")
    role_chain = read_json(root / PROVENANCE_ROOT / "role_chain.json")
    access = read_json(root / PROVENANCE_ROOT / "role_access_ledger.json")
    contamination = read_json(root / PROVENANCE_ROOT / "contamination_scan.json")
    embargo = read_json(root / PROVENANCE_ROOT / "embargo_scan.json")
    interaction = read_yaml(
        root / "specifications/interactions/component_interaction_contract.yaml"
    )
    architecture = read_yaml(root / "specifications/architectures/architecture_candidate_set.yaml")
    benchmark = read_yaml(root / "evals/prospective/phase-002d-r2/benchmark_protocol.yaml")
    sealed = read_json(root / "evals/prospective/phase-002d-r2/sealed_manifest.json")
    separation = read_json(
        root / "evals/prospective/phase-002d-r2/manifests/separation_report.json"
    )
    metric = read_yaml(root / "evals/prospective/phase-002d-r2/metric_registry.yaml")
    threshold = read_yaml(root / "evals/prospective/phase-002d-r2/threshold_policy.yaml")
    protocol = read_yaml(
        root / "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml"
    )
    ablation = read_yaml(root / "evals/prospective/phase-002d-r2/ablation_policy.yaml")
    budget = read_yaml(root / "evals/prospective/phase-002d-r2/budget_policy.yaml")
    findings = read_json(root / RESULT_ROOT / "adversarial_findings/findings.json")["findings"]
    evidence = read_json(root / RESULT_ROOT / "test_evidence/evidence.json")["test_evidence"]
    audits = [
        read_json(root / RESULT_ROOT / f"audit_outputs/{name}")
        for name in (
            "cross_component_interaction_prosecutor.json",
            "prospective_benchmark_integrity_auditor.json",
            "threshold_and_metric_prosecutor.json",
            "cost_complexity_dissent_auditor.json",
            "clean_room_provenance_auditor.json",
        )
    ]
    decisions = _decisions(root)
    by_id = {item["automated_decision"]["decision_id"]: item for item in decisions}
    shadow = by_id[SHADOW_DECISION_ID]["authorization"]
    audit = read_json(root / RESULT_ROOT / "decision_audit/audit.json")
    replay = read_json(root / REPLAY_PATH)
    state = read_json(root / "state/project_state.json")
    command_rows = [[item[0], " ".join(item[1])] for item in VALIDATION_COMMANDS]
    reports: dict[str, str] = {}

    spec_rows = [
        [
            item["component_id"],
            item["status"],
            item["accepted_scope"],
            item["specification_hash"],
        ]
        for item in specs
    ]
    reports["reports/phase002d_r2_component_specs.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 component specifications

{_table(["Component", "Status", "Accepted scope", "Specification hash"], spec_rows)}

All four artifacts are project-authored specifications only. They do not implement component
behavior, alter the formal Skill, select an architecture, or establish performance. Every component
has an empty direct formal-state write set; only the main agent may update project state.
"""
    )

    provenance_rows = [
        [
            item["component_id"],
            item["license_status"],
            item["allowed_reuse_mode"],
            item["contamination_status"],
        ]
        for item in provenance_registry["records"]
    ]
    reports["reports/phase002d_r2_clean_room_provenance.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 clean-room provenance

{_table(["Component", "License", "Reuse", "Contamination"], provenance_rows)}

- Source-completeness records: `{len(source_complete["records"])}`.
- Fresh author identities unique: `{role_chain["author_identities_unique"]}`.
- Authors disjoint from prosecutors: `{role_chain["authors_disjoint_from_auditors"]}`.
- Hidden-answer accesses: `{access["hidden_answer_access_count"]}`; vault accesses:
  `{access["vault_access_count"]}`.
- Restricted-copy warning matches: `{contamination["restricted_copy_match_count"]}`.
- Prohibited implementation files: `{embargo["prohibited_implementation_count"]}`.

The process uses metadata-only abstract-mechanism reference and records content not copied. It is
clean-room evidence, not a legal-opinion or license-compliance proof; `UNKNOWN`/`UNVERIFIED` source
rights remain bounded to `REFERENCE_ABSTRACT_MECHANISM`.
"""
    )

    edge_rows = [
        [item["from"], item["to"], item["from_node_type"], item["to_node_type"]]
        for item in interaction["data_dependencies"]
    ]
    reports["reports/phase002d_r2_interaction_contract.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 interaction contract

Contract `{interaction["contract_id"]}` is `{interaction["status"]}` at hash
`{interaction["contract_hash"]}`. State truth remains `{interaction["state_truth"]}`; formal Skill
count remains `{interaction["formal_skill_count"]}`.

{_table(["Producer", "Consumer", "From type", "To type"], edge_rows)}

All edges require artifact SHA-256, immutable revision/prior-hash binding, currentness and Decision
Audit. The six-rank failure-precedence table is noncompensatory; no component advances formal state
directly and no competing Run, Claim, comparison or project-state truth is created.
"""
    )

    architecture_rows = [
        [
            item["architecture_id"],
            item["estimated_complexity"],
            item["formal_skill_count"],
            len(item["implementation_surface"]),
        ]
        for item in architecture["candidates"]
    ]
    reports["reports/phase002d_r2_architecture_candidates.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 architecture candidates

{_table(["Candidate", "Complexity", "Formal Skills", "Future surface"], architecture_rows)}

Candidate set hash: `{architecture["candidate_set_hash"]}`. Baseline:
`{architecture["baseline_id"]}`. Selected architecture: `{architecture["selected_architecture"]}`.
Acceptance freezes only the 3-arm prospective comparison set; it is not architecture selection,
base selection, implementation authorization or evidence that any candidate is superior.
"""
    )

    reports["reports/phase002d_r2_benchmark_design.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 prospective Benchmark design

- Cohort: `{sealed["cohort_id"]}` / `{sealed["manifest_hash"]}`.
- Public conformance: `{benchmark["public_case_count"]}` cases.
- Sealed synthetic: `{benchmark["sealed_case_count"]}` cases.
- Future model-in-loop: `{benchmark["model_in_loop_case_count"]}` cases, not executed.
- Prospective/synthetic/no historical answers: `{benchmark["prospective"]}` /
  `{benchmark["synthetic_only"]}` / `{not benchmark["historical_answers_used"]}`.
- Public/sealed exact, ancestry, semantic-template and transformation-closure overlaps:
  `{separation["exact_overlap_count"]}`, `{separation["ancestry_overlap_count"]}`,
  `{separation["semantic_template_overlap_count"]}`,
  `{separation["transformation_closure_overlap_count"]}`.
- Isolation: `{sealed["isolation_level"]}`; private values read: `false`.

Tracked artifacts expose opaque case IDs, aggregate commitments and oracle-interface hashes, never
hidden seeds or private oracle mappings. The vault is ignored and policy/workspace isolated, not
OS-enforced. A clean checkout may validate the tracked commitments with the vault unmounted; that
proves public-manifest consistency and non-leakage, not private-vault availability. A partial mount
fails closed. Future execution requires stronger denial and an access ledger.
"""
    )

    reports["reports/phase002d_r2_threshold_policy.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 threshold policy

Metric registry `{metric["registry_id"]}` contains `{len(metric["metrics"])}` metrics. Threshold
policy `{threshold["policy_id"]}` contains `{len(threshold["thresholds"])}` frozen rules at
`{threshold["policy_hash"]}`. Candidate metrics were present at freeze:
`{threshold["candidate_metrics_present_at_freeze"]}`. All thresholds are noncompensatory:
`{all(item["noncompensatory"] for item in threshold["thresholds"])}`.

The policy separates hard safety, effectiveness, false block, reproducibility, state correctness,
claim support, leakage prevention, cost and maintenance. Paired false-block inference freezes its
denominator/discordance/alpha and abstains when undefined. Baseline-derived rules are fixed before
candidate results; `ARCH-S0` is not required to improve over itself. Unknown critical cost or
evidence routes to `EVIDENCE_INSUFFICIENT`, never zero.
"""
    )

    reports["reports/phase002d_r2_experiment_protocol.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 prospective experiment protocol

Protocol `{protocol["protocol_id"]}` is `{protocol["status"]}` at
`{protocol["protocol_hash"]}` and executed in R2: `{protocol["executed_in_phase_002d_r2"]}`.
Stages are deterministic conformance, future model comparison and automatic adjudication. The
three arms use equal cohorts, Prompt, data, timeout, sandbox, network/MCP policy, hidden cases and
grader. Maximum primary starts are `{budget["maximum_main_starts_for_three_eligible_arms"]}`;
retry slots `{budget["maximum_retry_starts_for_three_eligible_arms"]}`; global absolute cap
`{budget["absolute_start_cap"]}`. Retry burden is
`{protocol["retry_burden_formula"]}`.

Stage-1 ablations are `{ablation["stage1_arms"]}`; candidate-result-informed and post-hoc ablation
selection are both false. No Stage was executed, no model/API/prototype call occurred, and the two
upstream candidates are prohibited as arms.
"""
    )

    audit_rows = [[item["role"], item["verdict"], len(item["findings"])] for item in audits]
    total_audit_findings = sum(len(item["findings"]) for item in audits)
    passing_finding_evidence = sum(item["status"] == "PASSED" for item in evidence)
    reports["reports/phase002d_r2_subagent_audits.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 native Subagent audits

{_table(["Role", "Verdict", "Findings"], audit_rows)}

This phase recorded 17 native read-only Subagent runs: 4 original specification authors, 3
threshold designers, 5 independent prosecutors, 4 fresh role-disjoint re-authors and 1 final
Decision Auditor. Raw outputs are immutable. The five prosecutors produced
`{total_audit_findings}` findings; `{len(findings)}` BLOCKER/ERROR findings each have a test request
and passing deterministic evidence (`{passing_finding_evidence}/{len(evidence)}`). No Agent vote
closed a finding and no Subagent wrote formal state.
"""
    )

    decision_table = _decision_table(decisions)
    reports["reports/phase002d_r2_automated_decisions.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 automated decisions

{decision_table}

The frozen native automated-decision core is reused; the envelope records the exact R2 phase scope
without creating a competing decision contract. The first five decisions accept only frozen
specification/protocol artifacts. Shadow authorization is `{shadow["decision"]}` with accepted
scope `{shadow["accepted_scope"]}` and route `{shadow["next_phase_allowed"]}` because its M7
snapshot correctly predates the M8 Auditor and replay. Architecture remains unselected.
"""
    )

    reports["reports/phase002d_r2_decision_audit.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 Decision Audit

Independent result: `{audit["result"]}`; replayable: `{audit["replayable"]}`; confidence:
`{audit["confidence"]}`; checkpoint: `{audit["checkpoint_hash"]}`. Checks:
`{sum(audit["checks"].values())}/{len(audit["checks"])}`; failures: `{audit["failures"]}`;
blockers: `{audit["blockers"]}`.

The identity-blind Auditor was read-only and used no web, MCP, nested Codex, API key, vote, human
technical Gate, hidden vault or peer raw output. The formal record differs from its raw JSON only by
the declared checkpoint-hash normalization.
"""
    )

    replay_rows = [[name, passed] for name, passed in replay["variants"].items()]
    reports["reports/phase002d_r2_replay.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 offline replay

Replay `{replay["replay_id"]}` is stable: `{replay["stable"]}` at hash
`{replay["replay_hash"]}`.

{_table(["Variant", "Stable"], replay_rows)}

Network calls: `{replay["network_calls"]}`; model calls: `{replay["model_calls"]}`; API calls:
`{replay["api_calls"]}`; prototype executions: `{replay["prototype_executions"]}`; third-party
executions: `{replay["third_party_executions"]}`. Seed-manifest verification used tracked
commitments plus vault stat/ignore checks and did not read private values.
"""
    )

    validation_table = _table(["ID", "Command"], command_rows)
    reports["reports/phase-002d-r2-acceptance.md"] = (
        GENERATED
        + f"""# Phase 002D-R2 acceptance report

## Outcome

`{state["technical_adjudication_status"]}`. This is a complete specification/protocol phase, not a
component implementation, architecture selection, performance result or formal Skill integration.
The shadow decision is `{shadow["decision"]}` and does not block phase completeness; its next route
is `{shadow["next_phase_allowed"]}`. Phase 003 remains prohibited.

## Frozen artifacts and evidence

- Four component specifications and one single-truth interaction contract are frozen.
- Three architecture candidates including the scaffold baseline are frozen; winner is null.
- Prospective V2 Benchmark has 16 public, 36 sealed and 8 future model-in-loop cases.
- 32 metrics and 32 thresholds are frozen before candidate or prototype results.
- Five prosecutors produced 29 serious testable findings; all 29 have passing evidence.
- Independent Decision Auditor: `{audit["result"]}` / `{audit["checkpoint_hash"]}`.
- Five-variant offline replay: `{replay["stable"]}` / `{replay["replay_hash"]}`.

## Boundaries and unknowns

The formal Skill remains `0.1.0-foundation`/`SCAFFOLD_ONLY`.
The architecture and base remain null/false; third-party integration is false. Benchmark isolation
is not OS-enforced. Clean-room process evidence is not legal proof.
Shadow effectiveness, future model quality, monetary/operator cost and API behavior are unmeasured.
There was no prototype, model experiment, API call, training or fine-tuning.

## Required offline validation matrix

{validation_table}

Machine results are recorded separately in
`evals/results/phase-002d-r2/validation_commands.json` so recording durations and stdout hashes does
not rewrite these substantive conclusions.
"""
    )

    reports["reports/automated_adjudication_dossier.md"] = (
        GENERATED
        + f"""# Automated adjudication dossier

## Current Phase 002D-R2 decision set

{decision_table}

Decision Audit is `{audit["result"]}` and offline replay is `{replay["stable"]}`. The current
technical state is `{state["technical_adjudication_status"]}`. Architecture remains null, the
formal Skill remains scaffold-only, and shadow authorization is RETEST_REQUIRED. Historical Phase
002A–002D-R1 machine records remain immutable under their versioned result directories and are not
superseded by a positive performance claim.
"""
    )

    reports["reports/formal_automated_decisions.md"] = (
        GENERATED
        + f"""# Formal automated decisions

{decision_table}

Only the five frozen artifact scopes are accepted. Candidate-set acceptance is not architecture
selection. The shadow decision accepts no scope, routes to R2 and prohibits formal implementation,
integration, production, direct reuse and Phase 003. No Agent majority or human technical approval
contributed to these outcomes.
"""
    )
    return reports


def _manifest(reports: dict[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002D-R2-REPORTS-MANIFEST-001",
        "created_at": CREATED_AT,
        "report_hashes": {
            path: sha256_bytes(content.encode("utf-8")) for path, content in sorted(reports.items())
        },
        "report_count": len(reports),
    }
    return {**body, "manifest_hash": sha256_json(body)}


def check_or_write_reports(root: Path, *, check: bool) -> dict[str, Any]:
    reports = build_reports(root)
    manifest = _manifest(reports)
    errors: list[str] = []
    for relative, expected in reports.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                errors.append(f"PHASE002D_R2_REPORT_DRIFT:{relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if check:
        if not (root / MANIFEST_PATH).is_file() or read_json(root / MANIFEST_PATH) != manifest:
            errors.append("PHASE002D_R2_REPORT_MANIFEST_DRIFT")
    else:
        from cumcm_skill_lab.adjudication.models import write_json

        write_json(root / MANIFEST_PATH, manifest)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "report_count": len(reports),
        "manifest_hash": manifest["manifest_hash"],
    }


__all__ = ["MANIFEST_PATH", "REPORT_PATHS", "build_reports", "check_or_write_reports"]
