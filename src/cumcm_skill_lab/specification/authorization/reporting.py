"""Generate truthful terminal reports for the incomplete R2A authorization closure."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import check_or_write, read_json, read_yaml

from .adversarial_closure import CLOSURE_PATH, EVIDENCE_PATH, REQUESTS_PATH
from .candidate import CANDIDATE_PATH
from .models import DEPENDENCY_PATH, FREEZE_PATH, RESULT_ROOT
from .native_audits import FINAL_AUDIT_PATH, FIRST_ROUND_ROLES, OUTPUT_ROOT
from .preconditions import PRECONDITIONS_PATH
from .scope import SCOPE_PATH

REPORT_PATHS = (
    "reports/phase002d_r2a_dependency_graph.md",
    "reports/phase002d_r2a_preconditions.md",
    "reports/phase002d_r2a_shadow_scope.md",
    "reports/phase002d_r2a_subagent_audits.md",
    "reports/phase002d_r2a_adversarial_tests.md",
    "reports/phase002d_r2a_authorization.md",
    "reports/phase002d_r2a_decision_audit.md",
    "reports/phase002d_r2a_replay.md",
    "reports/phase-002d-r2a-acceptance.md",
)
MANIFEST_PATH = RESULT_ROOT / "reports_manifest.json"
HEADER = "<!-- GENERATED FILE — DO NOT EDIT -->\n"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _check_or_write_text(path: Path, value: str, *, check: bool) -> list[str]:
    if check:
        if not path.is_file():
            return [f"MISSING:{path}"]
        if path.read_text(encoding="utf-8") != value:
            return [f"MISMATCH:{path}"]
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return []


def build_reports(root: Path) -> dict[str, str]:
    freeze = read_json(root / FREEZE_PATH)
    graph = read_json(root / DEPENDENCY_PATH)
    preconditions = read_json(root / PRECONDITIONS_PATH)
    scope = read_yaml(root / SCOPE_PATH)
    closure = read_json(root / CLOSURE_PATH)
    requests = read_json(root / REQUESTS_PATH)
    evidence = read_json(root / EVIDENCE_PATH)
    candidate = read_json(root / CANDIDATE_PATH)
    audit = read_json(root / FINAL_AUDIT_PATH)
    first = [read_json(root / OUTPUT_ROOT / f"{role}.json") for role in FIRST_ROUND_ROLES]
    reports: dict[str, str] = {}
    reports[REPORT_PATHS[0]] = (
        HEADER
        + f"""# Phase 002D-R2A authorization dependency graph

- Nodes: `{len(graph["nodes"])}`
- Edges: `{len(graph["edges"])}`
- Cycle detected: `{str(graph["cycle_detected"]).lower()}`
- Graph hash: `{graph["graph_hash"]}`
- Prerequisite audit: `{graph["prerequisite_audit_node"]}`
- Final audit: `{graph["final_authorization_audit_node"]}`
- State transition remains blocked because the final audit did not pass.
"""
    )
    reports[REPORT_PATHS[1]] = (
        HEADER
        + f"""# Phase 002D-R2A authorization preconditions

- Passed: `{preconditions["passed_check_count"]}/{preconditions["required_check_count"]}`
- Eligibility: `{preconditions["eligibility"]}`
- Preconditions hash: `{preconditions["preconditions_hash"]}`
- Unknowns: `{", ".join(preconditions["unknowns"])}`

These L4 checks support a non-active candidate only. They do not override the later final-audit
`RETEST_REQUIRED` result.
"""
    )
    reports[REPORT_PATHS[2]] = (
        HEADER
        + f"""# Phase 002D-R2A shadow scope

- Scope: `{scope["accepted_scope"]}`
- Candidates: `{", ".join(scope["candidate_ids"])}`
- Baseline: `ARCH-S0-RETAIN-SCAFFOLD-ONLY`
- Scope hash: `{scope["scope_hash"]}`
- Architecture selected: `null`
- Prototype implemented/executed: `false/false`
- Phase 003 prohibited: `true`
- Hidden vault OS enforcement: `false`
"""
    )
    rows = [
        f"| {item['role']} | {item['verdict']} | {item['output_hash']} | "
        f"{len(item['findings'])} | {len(item['blockers'])} |"
        for item in first
    ]
    rows.append(
        f"| {audit['role']} | {audit['verdict']} | {audit['output_hash']} | "
        f"{len(audit['findings'])} | {len(audit['blockers'])} |"
    )
    reports[REPORT_PATHS[3]] = (
        HEADER
        + """# Phase 002D-R2A native Subagent audits

| Role | Verdict | Output hash | Findings | Blockers |
| --- | --- | --- | ---: | ---: |
"""
        + "\n".join(rows)
        + "\n\nAll roles were native, read-only, no-vote and API/web/MCP-free.\n"
    )
    passed_evidence = sum(item["status"] == "PASSED" for item in evidence["test_evidence"])
    failed_evidence = sum(item["status"] != "PASSED" for item in evidence["test_evidence"])
    reports[REPORT_PATHS[4]] = (
        HEADER
        + f"""# Phase 002D-R2A adversarial tests

- Registered serious findings: `{closure["serious_finding_count"]}`
- Test requests: `{len(requests["test_requests"])}`
- Passing recorded evidence: `{passed_evidence}`
- Failing recorded evidence: `{failed_evidence}`
- Closure hash: `{closure["closure_hash"]}`

The terminal auditor nevertheless opened `R2A-FINAL-002`: the scope test evidence predates and
does not hash-bind the exact remediation candidate it audited. The registry PASS is therefore
insufficient for sealing; the failed remediation was rolled back to the non-active M5 candidate.
"""
    )
    reports[REPORT_PATHS[5]] = (
        HEADER
        + f"""# Phase 002D-R2A authorization

- Candidate ID: `{candidate["candidate_id"]}`
- Candidate hash: `{candidate["candidate_hash"]}`
- Candidate proposed decision: `{candidate["proposed_automated_decision"]["decision"]}`
- Proposed scope: `{candidate["proposed_accepted_scope"]}`
- Active: `{str(candidate["active"]).lower()}`
- Old decision preserved: `{candidate["supersedes"]["decision_id"]}` / `RETEST_REQUIRED`
- Active R2A authorization seal: `NOT_CREATED`
- Effective next route: `null`

The candidate is not an active decision, architecture selection, formal Skill integration, R3
start, or Phase 003 authorization.
"""
    )
    reports[REPORT_PATHS[6]] = (
        HEADER
        + f"""# Phase 002D-R2A final authorization audit

- Audit ID: `{audit["audit_id"]}`
- Result: `{audit["verdict"]}`
- Checkpoint hash: `{audit["output_hash"]}`
- Open blockers: `{", ".join(audit["blockers"])}`
- Bundle hash: `{audit["bundle_hash"]}`

Three bounded transports returned `RETEST_REQUIRED`; earlier outputs remain preserved. The terminal
blocker requires candidate-first freezing, later monotonic evidence, and exact candidate byte and
canonical hash bindings. No fourth repair was attempted, and the failed remediation was not retained
as the live candidate.
"""
    )
    reports[REPORT_PATHS[7]] = (
        HEADER
        + """# Phase 002D-R2A final replay

- Final replay: `NOT_RUN`
- Stable: `false`
- Active decision hash: `null`
- Audit checkpoint binding: `null`

Replay is prohibited because the final authorization audit did not pass and no active seal exists.
"""
    )
    reports[REPORT_PATHS[8]] = (
        HEADER
        + f"""# Phase 002D-R2A acceptance report

## Outcome

`SHADOW_AUTHORIZATION_INCOMPLETE`. The final authorization auditor returned `RETEST_REQUIRED`
after three bounded transports. No active authorization was sealed and no final replay or formal
state acceptance transition occurred.

## Evidence snapshot

- Branch: `feat/phase002d-r2a-shadow-authorization`
- Frozen input ID/hash: `{freeze["freeze_id"]}` / `{freeze["manifest_hash"]}`
- Frozen files: `{len(freeze["immutable_file_hashes"])}`
- DAG: `{len(graph["nodes"])}` nodes / `{len(graph["edges"])}` edges / cycle `false`
- Preconditions: `{preconditions["passed_check_count"]}/{preconditions["required_check_count"]}`
- Candidate: `{candidate["candidate_id"]}` / `{candidate["candidate_hash"]}` / active `false`
- Final audit: `{audit["verdict"]}` / `{audit["output_hash"]}`
- Terminal blocker: `R2A-FINAL-002`
- Active decision: `NOT_CREATED`
- Final replay: `NOT_RUN`
- Effective next phase: `null`

## Terminal blocker

`R2A-FINAL-SINGLE-SCOPE-001` evidence completed before the failed remediation candidate audited in
the terminal bundle was created and omits that candidate's byte SHA-256 and canonical candidate
hash. The final auditor therefore could not prove that the recorded 20 mutation checks tested the
exact audited instance. The failed remediation was rolled back to the non-active M5 candidate. The
bounded repair limit is exhausted; a newly authorized continuation must freeze its candidate first
and only then produce monotonic, hash-bound evidence, closure, preconditions and another final audit
bundle.

## Preserved boundaries

- The old R2 `RETEST_REQUIRED` decision remains byte-for-byte unchanged and is not described as
  erroneous.
- Authorization is not architecture selection or formal Skill integration.
- Selected architecture is `null`; base selected and third-party integrated are `false`.
- The formal Skill remains scaffold-only and unmodified.
- Prototype implementation/execution, real model experiments, API calls, API-key use, training,
  fine-tuning and third-party executions are all zero/false.
- R3 did not start and Phase 003 remains prohibited.
- Hidden-vault OS isolation, legal compliance, effectiveness and monetary cost remain unknown.

## Validation status

- Baseline before R2A work: `1139 passed, 1 skipped`.
- Final full pytest: `21 failed, 1288 passed, 1 skipped` across `1310` collected nodes.
- Strict repository validation: `PASS`; contracts: `72/72` valid and `62/62` invalid rejected.
- Ruff lint/format, R2 freeze, R2A freeze, DAG, preconditions, scope, candidate, audit-record,
  implementation-embargo, vault, report and generated-status checks: `PASS`.
- Seal, replay and state-transition checks: `BLOCKED` as required because the final audit is not
  `PASS`; no artifact was created.
- Full CI: `FAIL` with the same 21 pytest failures. The primary cascade is an older R1 frozen hash
  for `rules/workflow_rules.yaml` versus M1's required live task-branch update; one independent R2
  historical-state test applies the current `2.4.0` project-state Schema to a `2.3.0` snapshot.
- Three bounded repair attempts were exhausted. The final attempted compatibility repair was rolled
  back after it did not close both R1 and R2 historical-freeze semantics.

## Delivery status

This report records an incomplete gate. The final commit and remote SHA are reported after this
generated content is committed and pushed; Draft PR #5 must remain OPEN/DRAFT.
"""
    )
    return reports


def generate_reports(root: Path, *, check: bool) -> dict[str, Any]:
    reports = build_reports(root)
    errors: list[str] = []
    for relative, value in reports.items():
        errors.extend(_check_or_write_text(root / relative, value, check=check))
    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "phase": "PHASE-002D-R2A-SHADOW-PROTOTYPE-AUTHORIZATION-CLOSURE",
        "status": "SHADOW_AUTHORIZATION_INCOMPLETE",
        "report_hashes": {path: _sha256_text(value) for path, value in sorted(reports.items())},
        "active_decision_created": False,
        "final_replay_run": False,
        "next_phase_allowed": None,
    }
    errors.extend(check_or_write(root / MANIFEST_PATH, manifest, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "report_count": len(reports),
        "acceptance_status": manifest["status"],
    }


__all__ = ["MANIFEST_PATH", "REPORT_PATHS", "build_reports", "generate_reports"]
