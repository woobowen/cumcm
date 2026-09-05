# PLAN-0004C2 — Claim scope repair and fresh C Validation

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`
Owner: main agent / `modeling_orchestrator`
Branch: `feat/phase004c2-claim-scope-repair-validation-2019c`
Starting commit: `f3812dcd0b1c1bb76224168454719dd3eb112801`

## Purpose, environment and scope

Repair the case-neutral multi-requirement Claim contract, retain K1 and one formal Skill,
and freeze RC5 before a different answer-sealed C one-shot. Use the existing Python 3.11.14
`.venv`, offline CI and designated task branch. No new architecture or third-party integration.

## Historical boundary and decision

004C is `TERMINAL_EVIDENCE_INSUFFICIENT`: `DECISION-C-TARGET-VALIDATION-004C` rejected
`CUMCM-2024-C-VALIDATION-001` at `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`.
Freeze commit `197f62bc75ebe832e9dd3ced0306740f336b80d6`, old decision, workspace,
`evals/results/phase-004c-c-batch/`, old acceptance and 2025 reservation remain byte-identical.
The defect equates global scope, local scope and the first requirement's identity.
Structured primary coverage, exact lineage and aggregate containment replace that special identity.
2024 can only supply a read-only derived `POST_VALIDATION_DIAGNOSTIC_REPLAY`, with no new Run,
no changed verdict, no answer access and no independent Validation credit.

## Milestones and acceptance

- M0 PRELIGHT COMPLETE: merged PR 9, clean task branch at merged main, RC4 tree and terminal
  workspace verified; baseline 1868 passed / 1 skipped, strict 0 errors / 0 warnings.
- M1 START IN_PROGRESS: minimal plan/state/policy/checker migration; focused checks, atomic commit,
  push and remote SHA verification; create one open Draft PR.
- M2 NEUTRAL TEST FREEZE PENDING: freeze at least 30 deterministic, offline case-neutral
  expectations before implementation and before new Validation input. Never change expected
  PASS criteria to match implementation.
- M3 REPAIR PENDING: at most two formal Skill revision cycles; independent aggregate identity,
  order-independent exact primary coverage, explicit optional/diagnostic/supporting roles,
  local Run/output/decision binding, scope containment and old-format compatibility.
  Keep execute/capture/seal and selected-output evidence semantics intact.
- M4 REGRESSION PENDING: existing 2020/2021/2022/2023 C and auxiliary 2020 A artifacts,
  two synthetic E2E, 30 original negatives, RC4 preflight, STALE and leakage checks.
  Derive a separate 2024 diagnostic bundle. Auditor 1 reads only after these results exist.
- M5 RELEASE PENDING: all required tests, anti-hardcoding, discovery, strict and local CI pass;
  freeze version/implementation commit/tree/runner/contract/tests/regressions/environment.
  Commit and remotely verify RC5 before any fresh Validation input acquisition.
- M6 FRESH VALIDATION PENDING: only after M5, check contamination then obtain official 2019 C
  inputs; register `CUMCM-2019-C-VALIDATION-002`, `VALIDATION`, `SEALED`, and unverifiable model
  prior. Freeze rubric, primary requirements/output contract, environment, 4-hour timebox and
  one-shot protocol; commit/push pre-run freeze before actual model execution. One fresh worker
  owns case code/artifacts only; main agent remains sole formal-state writer.
- M7 TERMINAL PENDING: run all 14 stages with frozen RC5, preserve failures, no result-driven
  Skill/test/rubric mutation, and no success-forcing retries. Record actual terminal decision;
  Auditor 2 reads only after decision. Freeze/check/commit/push the terminal outcome before
  references; no post-freeze Run or verdict change.
- M8 DELIVERY PENDING: minimal docs/state/registry/reports/acceptance, full local and remote CI,
  exact remote SHA; single PR remains OPEN/DRAFT. 2025 six access flags remain false.

## Validation and Git checkpoints

Use `bash scripts/ci.sh`, `.venv/bin/python scripts/validate_repo.py --strict`,
`.venv/bin/python scripts/render_status.py --check`, focused neutral/regression/freeze checks,
Skill discovery, instruction budget, contracts, leakage, secrets and `git diff --check`.
Record command/exit/duration/type/version/case/answer state/result/hash/blocker.
Explicitly stage related files; no `git add .`, reset, clean, force push, main push or merge.
Checkpoints: start; neutral tests; implementation; regressions; RC5 release; fresh registration
and pre-run freeze; terminal freeze; acceptance delivery.

## Risks, stopping and next route

Model prior is unverifiable. Scope strings cannot prove arbitrary natural-language truth;
all accepted statements still require captured output and structured support.
Stop for historical mutation, expectation drift, first-requirement dependence, missing-primary
acceptance, single-case or C regression, hardcoding, two failed revision cycles, premature
Validation access, contamination, unsafe official acquisition, Skill drift during Validation,
answer exposure, post-terminal Run, 2025 access or unrecoverable CI. Preserve failures.
Only fresh Validation PASS permits `PHASE-SKILL-C-TARGET-HELDOUT-004D`; otherwise use the existing
repair route or null. Never revalidate 2024 or use 2025 in this phase.

## Actual progress and update rule

M0 verified at task start; no package or configuration installation. Update this one plan with
observed milestone evidence and blockers. Preserve old files and decisions; no destructive rollback.
