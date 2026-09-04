# PLAN-0004B — 2020 A Cross-Type Development Eval

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-DEVELOPMENT-EVAL-004`
Subphase: `CUMCM-2020-A-POST-FREEZE-DIAGNOSIS`
Owner: main agent / `modeling_orchestrator`
Started: `2026-09-04T10:53:46Z`
Branch: `feat/phase004b-development-eval-2020a`
Starting commit: `1d842a45403370916ce2c36297876e9cd1ddde1f`
Case: `CUMCM-2020-A-DEVELOPMENT-002`

## Objective and frozen boundary

Run the unchanged `0.2.0-competition-rc2` Skill on the official 2020 A mechanistic problem while
answers remain sealed, execute all 14 business stages with captured case-local code, freeze and
remotely verify the first run, then inspect at most the authorized reference classes. The already
unlocked 2023 C case remains Development evidence only and is used solely for cross-case regression.
This phase does not select a new architecture, create a Benchmark, start Validation, or claim
generalization from two Development cases.

## Execution and evaluation

1. Bind the official archive, problem, attachment, output template, RC2 commit/tree, Python and
   dependency snapshot, allowed tools, immutable-input rule, answer state, search policy, rubric and
   five-hour first-run limit before model design.
2. Execute in order: problem intake, requirement decomposition, source planning, assumptions and
   symbols, data audit, model portfolio, baseline, experiment design, implementation/execution,
   comparison, robustness, Final Run, Claim validation and modeling-to-paper handoff.
3. Evaluate requirement coverage, physical/units validity, initial and boundary conditions,
   identifiability, solver convergence, residuals, constraint feasibility, optimization stability,
   robustness, evidence completeness and contest efficiency. Hard gates are non-compensable.
4. Every executable result must pass RC2 `execute → capture → seal-run → manifest`; failed,
   nonconverged, infeasible, superseded and stale Runs remain preserved and cannot support Final.
5. Freeze the first run regardless of terminal state, commit it independently, push it and verify
   local/remote SHA equality before changing answer access to `UNLOCKED_AFTER_FIRST_RUN`.
6. Classify post-unlock gaps once. Accept at most two major RC3 revision cycles, only for
   answer-independent, cross-problem workflow failures with non-hardcoded tests.
7. If a generic revision is accepted, run 2020 A Development regression, the preserved 2023 C
   executor/seal/handoff/stale regression, and mechanistic Stress A/B/C for units, equivalent
   segments and degraded observations. Otherwise keep RC2 and run the same evidence checks.
8. Freeze the accepted Skill commit/tree and produce the Validation handoff for
   `PHASE-SKILL-VALIDATION-EVAL-004-C`; do not start a Validation case.

## Checkpoints and stop conditions

The first deterministic registration commit and the independent first-run-freeze commit are pushed
and remotely verified before unlock. Final delivery requires focused tests, two synthetic E2E, 30
negative cases, both Development regressions, Stress A/B/C, leakage/secrets/training consistency,
strict validation, full CI, Draft PR and remote SHA verification.

The RC2 first run is frozen at `cadb774025ae30dc871fb67bdc4ffb8ffa409773be8e01247c8fea21bf8286ff`
and its independent commit `b742e8e042a1e9f0c161806c89c1b5917abe5693` is remotely verified. Answer
access was unlocked at `2026-09-04T11:19:44Z`; no reference body was accessed. Gap classification
accepted only the generic nonzero-exit evidence defect for one RC3 revision cycle.

Stop with the exact bounded status for unsafe official input acquisition, solution exposure before
freeze, raw mutation, uncaptured execution, nonconverged or infeasible Final selection,
non-replayable freeze, hardcoded case content, exhausted revision cycles, unrecoverable CI, or
tracked raw/reference/credential material. Preserve all completed Runs and checkpoints.
