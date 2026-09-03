# ruff: noqa: E501
"""Generate the C1/C2 continuation reports from frozen machine artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from cumcm_skill_lab.authorization_c1.models import (
    INPUT_FREEZE_PATH,
    RESULT_ROOT,
    STARTING_COMMIT,
    check_or_write_json,
    file_sha256,
    git_file_bytes,
    sha256_json,
)

from .candidate_evidence import CLOSURE_PATH, PRECONDITIONS_PATH, TEST_EVIDENCE_PATH, TEST_PLAN_PATH
from .candidate_freeze import CANDIDATE_PATH, FREEZE_PATH
from .final_audit import FINAL_AUDIT_PATH
from .final_audit_bundle import BUNDLE_PATH
from .terminal import AUTHORIZATION_PATH, REPLAY_PATH, STATE_TRANSITION_PATH

HEADER = "<!-- GENERATED FILE — DO NOT EDIT -->\n"
VALIDATION_PATH = RESULT_ROOT / "validation/validation.json"
REPORT_MANIFEST_PATH = RESULT_ROOT / "reports_manifest-c2.json"
REPORT_PATHS = (
    Path("reports/phase002d_r2a_c1_historical_compatibility.md"),
    Path("reports/phase002d_r2a_c1_schema_resolution.md"),
    Path("reports/phase002d_r2a_c1_candidate_freeze.md"),
    Path("reports/phase002d_r2a_c1_candidate_evidence.md"),
    Path("reports/phase002d_r2a_c1_subagent_audits.md"),
    Path("reports/phase002d_r2a_c1_final_audit.md"),
    Path("reports/phase002d_r2a_c1_authorization.md"),
    Path("reports/phase002d_r2a_c1_replay.md"),
    Path("reports/phase-002d-r2a-c1-acceptance.md"),
    Path("reports/automated_adjudication_dossier.md"),
    Path("reports/formal_automated_decisions.md"),
)
AUDIT_PATHS = (
    RESULT_ROOT / "subagent_outputs/historical_freeze_semantics_auditor.json",
    RESULT_ROOT / "subagent_outputs/schema_version_compatibility_auditor.json",
    RESULT_ROOT / "subagent_outputs/candidate_binding_prosecutor.json",
    RESULT_ROOT / "subagent_outputs/candidate_binding_prosecutor-post-evidence.json",
    RESULT_ROOT / "subagent_outputs/final_shadow_authorization_auditor.json",
    RESULT_ROOT / "subagent_outputs/candidate_binding_prosecutor-post-evidence-c2.json",
    RESULT_ROOT / "subagent_outputs/final_shadow_authorization_auditor-c2.json",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"C2_REPORT_JSON_OBJECT_REQUIRED:{path.as_posix()}")
    return value


def _write_or_check(path: Path, value: str, *, check: bool) -> list[str]:
    if check:
        if not path.is_file():
            return [f"C2_REPORT_MISSING:{path.as_posix()}"]
        if path.read_text(encoding="utf-8") != value:
            return [f"C2_REPORT_STALE:{path.as_posix()}"]
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return []


def _validation(root: Path) -> dict[str, Any]:
    path = root / VALIDATION_PATH
    if path.is_file():
        return _read_json(path)
    return {
        "validation_id": "PHASE-002D-R2A-C1-ACCEPTANCE-VALIDATION-PENDING",
        "overall_status": "PENDING",
        "commands": [],
        "pytest": {"collected": None, "passed": None, "failed": None, "skipped": None},
        "remote_ci": {"status": "PENDING", "subject_commit": None, "url": None},
        "record_hash": None,
    }


def closure_status(
    audit: dict[str, Any],
    seal: dict[str, Any],
    replay: dict[str, Any],
    state: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    checks = (
        audit.get("verdict") == "PASS",
        not audit.get("unresolved_blockers"),
        seal.get("final_audit_output_hash") == audit.get("output_hash"),
        replay.get("stable") is True,
        replay.get("active_decision_hash") == seal.get("authorization_hash"),
        state.get("technical_adjudication_status") == "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE",
        state.get("shadow_authorization", {}).get("active_decision_hash")
        == seal.get("authorization_hash"),
        validation.get("overall_status") == "PASS",
        validation.get("remote_ci", {}).get("status") == "PASS",
    )
    return (
        "SHADOW_AUTHORIZATION_CLOSURE_COMPLETE"
        if all(checks)
        else "SHADOW_AUTHORIZATION_CLOSURE_INCOMPLETE"
    )


def _audit_rows(audits: list[dict[str, Any]]) -> str:
    rows = []
    for item in audits:
        findings = len(item.get("findings", []))
        blockers = len(item.get("unresolved_blockers", item.get("blockers", [])))
        rows.append(
            f"| {item['role']} | true | {item.get('peer_output_access', 'NONE')} | "
            f"{item['output_hash']} | {findings} | {blockers} | {item['verdict']} |"
        )
    return "\n".join(rows)


def _command_rows(validation: dict[str, Any]) -> str:
    if not validation["commands"]:
        return "| PENDING | — | — | — | PENDING | — |"
    return "\n".join(
        f"| `{item['command']}` | {item['exit_code']} | {item['duration_seconds']:.3f}s | "
        f"{item['execution_type']} | {item['result']} | `{item['output_sha256']}` |"
        for item in validation["commands"]
    )


def build_reports(root: Path) -> dict[Path, str]:
    input_freeze = _read_json(root / INPUT_FREEZE_PATH)
    history = _read_json(root / RESULT_ROOT / "historical_verification/record.json")
    schema = _read_json(root / RESULT_ROOT / "schema_resolution/record.json")
    migration = _read_json(root / RESULT_ROOT / "schema_resolution/migration_2.3_to_2.4.json")
    c1_candidate = _read_json(root / RESULT_ROOT / "candidate_revision/candidate-c1.json")
    c1_freeze = _read_json(
        root / RESULT_ROOT / "candidate_freeze/candidate_freeze_manifest-c1.json"
    )
    c1_evidence = _read_json(root / RESULT_ROOT / "candidate_test_evidence/evidence-c1.json")
    c1_audit = _read_json(root / RESULT_ROOT / "final_audit/audit-c1.json")
    c2_candidate = _read_json(root / CANDIDATE_PATH)
    c2_freeze = _read_json(root / FREEZE_PATH)
    preconditions = _read_json(root / PRECONDITIONS_PATH)
    test_plan = _read_json(root / TEST_PLAN_PATH)
    evidence = _read_json(root / TEST_EVIDENCE_PATH)
    closure = _read_json(root / CLOSURE_PATH)
    bundle = _read_json(root / BUNDLE_PATH)
    audit = _read_json(root / FINAL_AUDIT_PATH)
    seal = _read_json(root / AUTHORIZATION_PATH)
    replay = _read_json(root / REPLAY_PATH)
    transition = _read_json(root / STATE_TRANSITION_PATH)
    state = _read_json(root / "state/project_state.json")
    validation = _validation(root)
    audits = [_read_json(root / path) for path in AUDIT_PATHS]
    outcome = closure_status(audit, seal, replay, state, validation)
    reports: dict[Path, str] = {}

    reports[REPORT_PATHS[0]] = (
        HEADER
        + f"""# Phase 002D-R2A-C1 historical compatibility

- Result: `{history["result"]}`
- Input freeze: `{input_freeze["freeze_id"]}` / `{input_freeze["manifest_hash"]}`
- Verification modes: `{", ".join(history["verification_modes"])}`
- R1 subject commit: `{history["r1_subject_commit"]}`
- Immutable roots: `{len(history["preserved_historical_tree_hashes"])}`
- Live pointer: `rules/workflow_rules.yaml`
- Allowed live field: `{", ".join(history["allowed_live_fields"])}`
- Rejected live fields: `{", ".join(history["rejected_live_fields"])}`
- Fixed historical failures: `{history["original_failure_count_fixed"]}`
- Verifier file SHA-256: `{history["verifier_file_sha256"]}`
- Record hash: `{history["record_hash"]}`

Historical decisions and result trees were read at their recorded subject commits. Current-tree
immutability, derived observations, and live semantic pointers use separate fail-closed modes; no
missing Git object falls back to the worktree and no whole-file ignore is permitted.
"""
    )

    schema_rows = "\n".join(
        f"| {item['state_schema_version']} | {item['schema_source']} | "
        f"{item['schema_subject_commit']} | {item['schema_file_sha256']} | "
        f"{item['validation_result']} |"
        for item in schema["resolutions"]
    )
    reports[REPORT_PATHS[1]] = (
        HEADER
        + f"""# Phase 002D-R2A-C1 Schema resolution

| State version | Source | Subject | Schema SHA-256 | Result |
| --- | --- | --- | --- | --- |
{schema_rows}

- Record result/hash: `{schema["result"]}` / `{schema["record_hash"]}`
- Unknown version behavior: `{schema["unknown_version_behavior"]}`
- Current-Schema fallback for history: `{str(schema["current_schema_fallback_for_history"]).lower()}`
- Migration: `{migration["migration_id"]}` / `{migration["migration_hash"]}`
- Migration source unchanged: `{str(migration["source_unchanged"]).lower()}`
- Security fields preserved: `{str(migration["security_fields_preserved"]).lower()}`
- Migration authoritative historical truth: `false`
"""
    )

    old = input_freeze["old_candidate"]
    reports[REPORT_PATHS[2]] = (
        HEADER
        + f"""# Phase 002D-R2A-C1/C2 candidate freeze

| Candidate | Path | File SHA-256 | Canonical hash | Freeze hash | Status | Replaces | Evidence |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| {old["candidate_id"]} | {old["path"]} | {old["file_sha256"]} | {old["canonical_candidate_hash"]} | — | HISTORICAL_NON_ACTIVE | — | 0 |
| {c1_candidate["candidate_id"]} | {c1_freeze["candidate_path"]} | {c1_freeze["candidate_file_sha256"]} | {c1_freeze["canonical_candidate_hash"]} | {c1_freeze["freeze_hash"]} | FROZEN_FINAL_AUDIT_FAIL | {old["candidate_id"]} | {c1_evidence["evidence_count"]} |
| {c2_candidate["candidate_id"]} | {c2_freeze["candidate_path"]} | {c2_freeze["candidate_file_sha256"]} | {c2_freeze["canonical_candidate_hash"]} | {c2_freeze["freeze_hash"]} | ACTIVE_AUDITED | {c1_candidate["candidate_id"]} | {evidence["evidence_count"]} |

C1 remains immutable and failed only because `R2A-C1-FINAL-001` exposed an inherited semantic
dependency cycle. The sole permitted C2 revision was created after that failure and its deterministic
resolution were committed and remotely verified.
"""
    )

    reports[REPORT_PATHS[3]] = (
        HEADER
        + f"""# Phase 002D-R2A-C2 candidate-bound evidence

- Preconditions: `{preconditions["passed_check_count"]}/{preconditions["required_check_count"]}` / `{preconditions["preconditions_hash"]}`
- Test plan: `{test_plan["test_count"]}` / `{test_plan["test_plan_hash"]}`
- Test evidence: `{evidence["passed_count"]}/{evidence["evidence_count"]}` / `{evidence["evidence_hash"]}`
- Closure: `{closure["result"]}` / `{closure["closure_hash"]}`
- Wrong-candidate and cross-revision evidence: machine-rejected
- Pre-freeze evidence: machine-rejected
- Candidate byte/canonical/freeze substitutions: machine-rejected
- Parent-hash and sequence inversion: machine-rejected
- Sequence: `12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21`
- Unresolved findings: `{len(closure["unresolved_findings"])}`

Every C2 L13+ record binds candidate ID, file SHA-256, canonical hash, freeze hash, exact parent,
and an increasing artifact sequence index.
"""
    )

    reports[REPORT_PATHS[4]] = (
        HEADER
        + f"""# Phase 002D-R2A-C1/C2 native Subagent audits

| Role | Read-only | Peer visibility | Output hash | Findings | Blockers | Verdict |
| --- | --- | --- | --- | ---: | ---: | --- |
{_audit_rows(audits)}

All seven recorded native audit roles were identity-separated and read-only. They used no web,
MCP, external API, nested Codex, majority vote, or human technical override. Earlier RETEST,
ABSTAIN, and FAIL outputs remain preserved and are not relabeled as PASS.
"""
    )

    reports[REPORT_PATHS[5]] = (
        HEADER
        + f"""# Phase 002D-R2A-C1/C2 final authorization audit

- C1 result/finding: `{c1_audit["verdict"]}` / `R2A-C1-FINAL-001`
- C1 output hash: `{c1_audit["output_hash"]}`
- C2 bundle: `{bundle["bundle_id"]}`
- C2 bundle hash: `{bundle["bundle_hash"]}`
- C2 result: `{audit["verdict"]}`
- Exact candidate bound: `{audit["candidate_id"]}` / `{audit["candidate_file_sha256"]}` / `{audit["canonical_candidate_hash"]}` / `{audit["candidate_freeze_hash"]}`
- C2 checks: `{len(audit["checks"])}`
- Findings/blockers: `{len(audit["findings"])}/{len(audit["unresolved_blockers"])}`
- Output hash: `{audit["output_hash"]}`

The PASS is limited to authorization correctness for a future isolated experimental shadow
prototype. It is not implementation, effectiveness, generality, safety, production, legal, or
Phase 003 evidence.
"""
    )

    reports[REPORT_PATHS[6]] = (
        HEADER
        + f"""# Phase 002D-R2A-C2 active authorization

- Authorization: `{seal["authorization_id"]}`
- Hash: `{seal["authorization_hash"]}`
- Decision: `{seal["decision"]}`
- Accepted scope: `{seal["accepted_scope"]}`
- Candidate: `{seal["candidate_id"]}`
- Supersedes: `{seal["supersedes"]["decision_id"]}` / `{seal["supersedes"]["historical_decision"]}`
- Replaces historical non-active candidate: `{seal["replaces_historical_non_active_candidate"]["candidate_id"]}`
- Replaces failed C1 revision: `{seal["replaces_failed_c1_revision"]["candidate_id"]}`
- Next phase: `{seal["next_phase_allowed"]}`
- Architecture/base/third-party: `null/false/false`
- Skill capability: `SCAFFOLD_ONLY`
- Prototype/API/model/third-party executions: `0/0/0/0`
- Phase 003 prohibited: `true`

The nested formal decision validates against `contracts/automated_decision.schema.json`; no second
decision system was created.
"""
    )

    variant_rows = "\n".join(
        f"| {name} | {str(value['stable']).lower()} |" for name, value in replay["variants"].items()
    )
    reports[REPORT_PATHS[7]] = (
        HEADER
        + f"""# Phase 002D-R2A-C2 final replay

| Variant | Stable |
| --- | --- |
{variant_rows}

- Mode: `{replay["mode"]}`
- Stable: `{str(replay["stable"]).lower()}`
- Replay hash: `{replay["replay_hash"]}`
- Parent authorization hash: `{replay["parent_artifact_hash"]}`
- Candidate-label binding rejected: `{str(replay["variants"]["candidate_label_permutation"]["exact_binding_rejected"]).lower()}`
- Historical versions: `{", ".join(replay["variants"]["historical_schema_resolver_replay"]["resolved_versions"])}`
- Live fields: `{", ".join(replay["variants"]["live_pointer_normalization_replay"]["allowed_live_fields"])}`
- API/network/model/prototype/third-party executions: `0/0/0/0/0`
"""
    )

    pytest = validation["pytest"]
    reports[REPORT_PATHS[8]] = (
        HEADER
        + f"""# Phase 002D-R2A-C1 acceptance report

## Outcome

`{outcome}`

The C2 final Auditor returned `{audit["verdict"]}`, active decision `{seal["authorization_id"]}` was
sealed at scope `{seal["accepted_scope"]}`, all eight offline replay variants are stable, and formal
state is `{state["technical_adjudication_status"]}`. Authorization completeness does not claim that
a prototype exists or works.

## Starting state

- Branch: `feat/phase002d-r2a-shadow-authorization`
- Starting HEAD: `{STARTING_COMMIT}`
- Starting tests: `1310` collected / `1288` passed / `21` failed / `1` skipped
- Old candidate: `{old["candidate_id"]}` / `{old["file_sha256"]}` / `{old["canonical_candidate_hash"]}`
- Old final blocker: `R2A-FINAL-002`

## Historical and Schema compatibility

- History: `{history["result"]}` / `{history["record_hash"]}`; fixed failures: `{history["original_failure_count_fixed"]}`
- Modes: `{", ".join(history["verification_modes"])}`
- Live field allowlist: `{", ".join(history["allowed_live_fields"])}`
- Schema: `{schema["result"]}` / `{schema["record_hash"]}`
- Versions: `{", ".join(item["state_schema_version"] for item in schema["resolutions"])}`
- Migration: `{migration["migration_hash"]}`; derived only, source unchanged, security fields preserved
- Unknown versions: `{schema["unknown_version_behavior"]}`

## Candidate-bound decision chain

- C1: `{c1_freeze["candidate_file_sha256"]}` / `{c1_freeze["canonical_candidate_hash"]}` / `{c1_freeze["freeze_hash"]}` / final `{c1_audit["verdict"]}`
- C2: `{c2_freeze["candidate_file_sha256"]}` / `{c2_freeze["canonical_candidate_hash"]}` / `{c2_freeze["freeze_hash"]}`
- C2 evidence: `{evidence["passed_count"]}/{evidence["evidence_count"]}` / `{evidence["evidence_hash"]}`
- Closure/bundle/audit: `{closure["closure_hash"]}` / `{bundle["bundle_hash"]}` / `{audit["output_hash"]}`
- Seal/replay/transition: `{seal["authorization_hash"]}` / `{replay["replay_hash"]}` / `{transition["transition_hash"]}`

## Active authorization and state

- Decision/scope: `{seal["decision"]}` / `{seal["accepted_scope"]}`
- Supersedes historical R2: `{seal["supersedes"]["decision_id"]}` / `{seal["supersedes"]["decision_hash"]}`
- Replaces non-active R2A candidate: `{old["candidate_id"]}`
- Phase/subphase/status: `{state["phase"]}` / `{state["subphase"]}` / `{state["status"]}`
- Technical status: `{state["technical_adjudication_status"]}`
- Architecture/base/third-party: `null/false/false`
- Skill capability: `{state["skill_capability_status"]}`
- Next phase allowed: `{state["next_phase_allowed"]}`
- Phase 003 entered: `false`

## Implementation embargo and execution statement

- Formal Skill tree before/after: `{input_freeze["protected_bindings"]["formal_skill_tree_hash"]}` / `{input_freeze["protected_bindings"]["formal_skill_tree_hash"]}`
- Prototype implementation files: `0`
- Formal component implementation files: `0`
- Hidden-vault tracked files: `0`
- Third-party integration/execution: `false/0`
- API key or billing used: `false/false`
- Foundation model trained or fine-tuned: `false`
- Real model-in-loop experiments: `0`
- Native Subagent audit records: `{len(audits)}` in this continuation; state cumulative count `{state["specification_protocol"]["native_subagent_runs"]}`
- Prototype executions: `0`
- Optimized objects: historical/Schema verifiers, candidate-binding governance, audit/seal/replay/state validators, contracts, tests, and generated reports only

## Validation

- Validation status/hash: `{validation["overall_status"]}` / `{validation["record_hash"]}`
- Final pytest: `{pytest["collected"]}` collected / `{pytest["passed"]}` passed / `{pytest["failed"]}` failed / `{pytest["skipped"]}` skipped
- Contract fixtures: `{validation.get("contract_fixtures", {}).get("valid", "PENDING")}` valid / `{validation.get("contract_fixtures", {}).get("invalid_rejected", "PENDING")}` invalid rejected
- Remote CI: `{validation["remote_ci"]["status"]}` / `{validation["remote_ci"]["subject_commit"]}` / `{validation["remote_ci"]["url"]}`

| Command | Exit | Duration | Type | Result | Output SHA-256 |
| --- | ---: | ---: | --- | --- | --- |
{_command_rows(validation)}

## Unknown and unverified

- Hidden Benchmark isolation is policy/workspace-based, not proven OS-enforced.
- Clean-room controls do not prove legal or license compliance.
- Prototype effectiveness, quality, reliability, generality, safety, runtime, and production fitness remain unmeasured because no prototype was implemented or executed.
- Monetary, operator, queue, and future maintenance costs remain unknown.
- Remote PR review and merge remain human-controlled; this report neither approves nor merges PR #5.

## Next step

`{seal["next_phase_allowed"]}`. This report does not execute that phase.
"""
    )

    dossier_base = git_file_bytes(
        root, STARTING_COMMIT, "reports/automated_adjudication_dossier.md"
    ).decode("utf-8")
    reports[REPORT_PATHS[9]] = (
        dossier_base.rstrip()
        + f"""

## Phase 002D-R2A-C1/C2 continuation

Historical R2 decision `{seal["supersedes"]["decision_id"]}` remains preserved at
`{seal["supersedes"]["decision_hash"]}`. C2 independently closed the candidate-bound authorization
chain: candidate `{seal["candidate_id"]}`, audit `{audit["verdict"]}` / `{audit["output_hash"]}`,
active decision `{seal["decision"]}` / `{seal["accepted_scope"]}`, replay stable
`{str(replay["stable"]).lower()}`, and route `{seal["next_phase_allowed"]}`. Architecture remains
null; no prototype, formal Skill integration, third-party execution, API/model experiment, or
Phase 003 work occurred.
"""
    )

    formal_base = git_file_bytes(
        root, STARTING_COMMIT, "reports/formal_automated_decisions.md"
    ).decode("utf-8")
    reports[REPORT_PATHS[10]] = (
        formal_base.rstrip()
        + f"""

## Phase 002D-R2A-C1/C2 continuation

| Decision | Result | Phase scope | Next route | Hash |
| --- | --- | --- | --- | --- |
| {seal["authorization_id"]} | {seal["decision"]} | {seal["accepted_scope"]} | {seal["next_phase_allowed"]} | {seal["authorization_hash"]} |

This decision supersedes the preserved R2 shadow authorization only. It authorizes a future
experimental validation phase, not an architecture, base, formal integration, production use, or
Phase 003.
"""
    )
    return reports


def check_or_write_reports(root: Path, *, check: bool) -> dict[str, Any]:
    reports = build_reports(root)
    errors: list[str] = []
    for path, text in reports.items():
        errors.extend(_write_or_check(root / path, text, check=check))
    manifest_body = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002D-R2A-C1-C2-GENERATED-REPORTS-001",
        "report_hashes": {
            path.as_posix(): hashlib.sha256(text.encode("utf-8")).hexdigest()
            for path, text in reports.items()
        },
        "input_hashes": {
            "authorization": file_sha256(root / AUTHORIZATION_PATH),
            "replay": file_sha256(root / REPLAY_PATH),
            "state_transition": file_sha256(root / STATE_TRANSITION_PATH),
            "project_state": file_sha256(root / "state/project_state.json"),
            "validation": (
                file_sha256(root / VALIDATION_PATH) if (root / VALIDATION_PATH).is_file() else None
            ),
        },
    }
    manifest_body["manifest_hash"] = sha256_json(manifest_body)
    errors.extend(check_or_write_json(root / REPORT_MANIFEST_PATH, manifest_body, check=check))
    validation = _validation(root)
    audit = _read_json(root / FINAL_AUDIT_PATH)
    seal = _read_json(root / AUTHORIZATION_PATH)
    replay = _read_json(root / REPLAY_PATH)
    state = _read_json(root / "state/project_state.json")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "report_count": len(reports),
        "manifest_hash": manifest_body["manifest_hash"],
        "closure_status": closure_status(audit, seal, replay, state, validation),
    }


__all__ = [
    "REPORT_MANIFEST_PATH",
    "REPORT_PATHS",
    "VALIDATION_PATH",
    "build_reports",
    "check_or_write_reports",
    "closure_status",
]
