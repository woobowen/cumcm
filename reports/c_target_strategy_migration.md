# C-Target Strategy Migration

Status: `PASS_REMOTE_DELIVERED`
Decision: `DECISION-C-TARGET-TRAINING-POLICY-004C`
Phase: `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`
Batch: `C-TARGET-BATCH-001`

## Starting evidence

- Starting branch: `feat/phase004c-validation-eval-2024a`
- Starting/local/main/old-remote SHA: `a56450f7ffb78e181c5aa4d660e763ed4c59c83a`
- Starting Git tree: `4447e41c7c3823b6fffcf6786a214ed36e0af3fb`
- New branch: `feat/phase004c-c-target-batch-generalization`
- Old branch: preserved, no unique commit, no open PR
- Worktree at preflight: clean
- Formal Skill: `cumcm-modeling-evidence` `0.2.0-competition-rc3`, one discoverable Skill,
  `COMPETITION_RC`, `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`
- Baseline: `1816 passed, 1 skipped`; strict repository validation `PASS`

## Migration result

The prior route treated 2024 A as the next Validation candidate. It was cancelled before case
registration, created no unique commit, had no open PR, and has no tracked Run/freeze evidence:
`CANCELLED_BEFORE_REGISTRATION_NO_EXECUTION_EVIDENCE`. The old branch and the historical Phase 004B
Validation handoff remain unmodified evidence of the earlier plan.

The new policy makes C the primary target, freezes one RC3 across three independent C Development
positions, delays every Skill modification and reference unlock until all first-run freezes are
remotely verified, admits only repeated cross-case or universal hard failures, and requires C for
Validation, Held-out, and final simulation. A is auxiliary transfer only; B is excluded by default.

Planned allocation and realized evidence are distinct. The registered independent allocation is
four C problems and one A auxiliary problem (80% C) after including the three preregistered batch
positions. At migration time only historical first runs are realized; preregistration is not claimed
as execution, strict blindness, or generalization evidence.

## Consistency boundary

The formal Skill is unchanged. Existing 2023 C and 2020 A evidence remains byte-preserved. New
phase transitions are owned by `WORKFLOW.md`, `contracts/project_state.schema.json`, and
`rules/target_problem_policy.yaml`. The older global workflow-rule live pointer changes only its
authorized task-branch field. `reports/current_state.md` is generated from project state.

## Validation before delivery

- Target policy: `PASS`; planned independent allocation 4 C / 5 total = `0.80`; realized historical
  evidence 1 C / 2 total = `0.50` and explicitly not used as the planned-allocation Gate.
- Project-state Schema: `PASS`.
- Competition RC consistency: 37/37 checks pass.
- Skill training consistency: 0 errors; historical runnable case count remains 2.
- Focused regression: 130 tests pass.
- Full local CI: `1834 passed, 1 skipped`; strict repository validation has 0 errors and 0 warnings.
- Contract fixtures: 78 valid accepted and 68 invalid rejected.
- Leakage, private-path, and secret findings: 0.

## Delivery

- Content commit: `e62fdbc034487589f8da4865967c644bae989ee5`
- Verified remote SHA: `e62fdbc034487589f8da4865967c644bae989ee5`
- Draft PR: `https://github.com/woobowen/cumcm/pull/9`
- PR state: `OPEN`, `DRAFT`
- Old branch: preserved
- Formal Skill mutation: none
