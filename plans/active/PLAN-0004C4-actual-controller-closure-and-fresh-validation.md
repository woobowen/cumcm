# PLAN-0004C4 — actual-controller closure, Competition RC7 and fresh C Validation

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4`
Subphase: `ACTUAL-CONTROLLER-BLACK-BOX-REPAIR`
Owner: main agent / `modeling_orchestrator`
Branch: `feat/phase004c2-claim-scope-repair-validation-2019c`
Starting commit: `7060ab136b88a158be6dfe3b46801e6cc2c65c64`

## Starting boundary and blockers

Phase 004C3 is terminal `RC6_RELEASE_REPAIR_BLOCKED`. RC5 remains the active blocked release,
RC6 remains a distinct blocked candidate, both 004C3 formal revision cycles remain closed, and the
2019/2024 terminal histories and the 2025 C reservation are immutable. The five inherited blockers
are `RC6_DATA_SUFFICIENCY_ACQUISITION_FAIL_OPEN`,
`RC6_SELECTION_GATE_FAIL_OPEN_PORTFOLIO_BINDING`,
`RC6_SEMANTIC_GATE_FAIL_OPEN_BINDING`, `RC6_COMPATIBILITY_GATE_VACUOUS`, and
`RC6_PER_REQUIREMENT_PIPELINE_NOT_EFFECTIVE`.

Auditor 1's 13 known counterexamples cover forbidden external empirical data, incomplete
acquisition plans, non-conjunctive source coverage, dependency-split selections, missing and false
portfolio hashes, ineligible selected Runs, wrong requirement/output bindings, absent metrics,
unbounded Claims, wrong aggregate mappings, and unknown/non-bijective compatibility. Helper-level
success is not controller-level success: every new probe must invoke the formal CLI over a real
temporary case workspace and observe state, trace, finalization and handoff behavior.

## Authorized implementation and evidence

The actual completion controller must derive evidence class, selection mode, Run/output/metric
ownership, policy exposure, scope, dependencies and compatibility only from authoritative case
artifacts. Missing values stay `UNKNOWN`/`UNRESOLVED` and block completion. The controller must
execute and bind ten ordered Gates in `gate_execution_trace.json`: requirement, source/evidence,
data-sufficiency preflight, comparison/selection, Run eligibility, compatibility/portfolio,
semantic Claim, aggregate Claim, finalization and handoff.

Data sufficiency permits only conjunctive `SINGLE_SOURCE` coverage or an explicit hash-bound
`REGISTERED_COMPOSITION`; incomplete external acquisition plans block and simulation cannot support
an empirical requirement. Selection must operationally support `GLOBAL_JOINT`, `PER_REQUIREMENT`
and `JOINT_PORTFOLIO`, including actual manifest/hash/dependency/output checks. Claim validation
must enforce claim-type predicates, current successful sealed Runs, output and metric ownership,
bounded scope, policy exposure/comparators, counter-evidence and exact aggregate mapping.

Before implementation, freeze all 13 black-box expectations and their hashes. After initial
implementation, run three neutral actual-controller cases: per-requirement selection, compatible
joint portfolio, and data-sufficiency partial completion, including every specified valid/invalid
mutation. Then run one identity-separated read-only adversarial prosecutor, reproduce up to 20 new
findings through the CLI, and permit at most three audit-triggered repair loops. Every loop freezes
the failure test first and reruns the complete controller matrix and three neutral cases.

## Release, regression and fresh Validation

RC7 targets project `0.3.0-competition-rc7` and Skill `0.2.0-competition-rc7`. Candidate release
checking precedes live-state/version mutation; live release checking must later exit zero. The
release manifest binds the implementation/subject commit, Skill tree, runner, contracts, known and
new probes, neutral E2E, historical regressions, pytest, strict and local CI without self-reference.
The 2019 and 2024 diagnostics remain read-only, and regressions cover 2020–2023 C, 2020 A, two
synthetic E2E cases, 30 negatives, RC4 output preflight, RC5 claims and the RC6 neutral matrix.

Only a candidate/live-PASS, remotely verified and frozen RC7 may unlock the official 2018 C input.
The 2017 C fallback is legal only for official-input failure, corruption, unrecognizable C inputs or
pre-result contamination. Raw official files remain ignored; tracked records retain hashes and
metadata only. An input-suitability preflight and answer-sealed pre-run freeze are committed,
pushed and remote-verified before a clean-context worker starts the four-hour one-shot. The worker
executes all 14 formal stages and the execute/capture/seal/validate/compare/select/finalize/claim/
handoff chain with actual case-owned code. RC7, tests, rubric and evidence policy remain frozen.

Every outcome receives a terminal decision and freeze, independent commit/push/remote verification,
and a read-only integrity audit. Terminal freeze forbids later Runs, code changes, verdict edits or
same-case Validation retries. PASS routes only to `PHASE-SKILL-C-TARGET-HELDOUT-004D`; a released
RC7 with failed/insufficient/incomplete Validation routes to
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`; an unreleased RC7 keeps 004C4 with null next phase.

## Limits, stop rules and progress

- Actual-controller implementation milestones: at most 3.
- Audit-triggered repair loops: at most 3.
- Total formal Skill code modification loops: at most 6.
- Task wall-time target: at most 14 hours; Validation modeling timebox: at most 4 hours.
- Stop on historical drift, 2025 access, answer exposure, Skill drift, post-freeze Run, deterministic
  unresolved release blocker, exhausted repair budget, or irrecoverable infrastructure failure.
- Never read `benchmark-vault`, search for answers, execute third-party code, create another Skill,
  branch/worktree/PR, rewrite history, merge PR 10, or modify `main`.

Progress:

- `2026-09-05T18:59:02+08:00` — Preflight matched the required branch, clean worktree, local/remote
  HEAD `7060ab136b88a158be6dfe3b46801e6cc2c65c64`, OPEN/DRAFT/MERGEABLE PR 10, blocked RC5/RC6
  identities, five blockers, one formal Skill, false third-party integration and six false 2025
  access flags. A serial baseline `bash scripts/ci.sh` passed with pytest `2009 passed / 1 skipped`
  in 293.37 seconds and strict 0 errors / 0 warnings. One accidental non-check historical verifier
  invocation was immediately restored byte-for-byte before the valid serial baseline; final
  worktree and the historical blob matched HEAD. No dependency or configuration changed.
- `2026-09-05T19:26:14+08:00` — Froze 13 actual-entrypoint black-box probes before any formal
  Skill/controller edit. Matrix freeze
  `PHASE-004C4-ACTUAL-CONTROLLER-BLACK-BOX-FREEZE-001` binds the base controller, core, test and
  project-original deterministic fixture hashes. Static checks passed, the matrix self-hash test
  passed, and pytest collected the expected 1 freeze-integrity test plus 13 behavioral probes.
  Behavioral execution is intentionally deferred until the fixture is Git-bound by the freeze
  commit; the pre-repair failures will then be recorded as expected-failure evidence.
- `2026-09-05T19:29:17+08:00` — Remote-verified freeze commit
  `150340915858acd8271d567303fe330afbad4078`. The first Git-bound run exposed a test-fixture seed
  schedule mismatch before reaching the controller; the fixture builder was corrected without
  changing probe mutations or expectations and its hash binding was renewed. The corrected full
  pre-repair run yielded `1 passed / 13 failed`: AC-001/002 blocked with only the coarse legacy
  handoff reason, while AC-003 through AC-013 exited zero. This is the frozen expected-failure
  baseline; implementation loop 1 may now begin.
