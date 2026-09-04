# PLAN-0004C — C-Target Batch Generalization and One-Shot Validation

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`
Subphase: `C-TARGET-STRATEGY-MIGRATION-AND-BATCH-FIRST-RUNS`
Owner: main agent / `modeling_orchestrator`
Started: `2026-09-04T22:14:48+08:00`
Branch: `feat/phase004c-c-target-batch-generalization`
Starting commit: `a56450f7ffb78e181c5aa4d660e763ed4c59c83a`
Batch: `C-TARGET-BATCH-001`

## Purpose and current environment

Improve first-pass complete solution quality for unfamiliar C problems under contest time, while
retaining only necessary cross-type transfer. The repository begins clean at the merged
`0.2.0-competition-rc3`
checkpoint, uses its existing `.venv`, one formal `cumcm-modeling-evidence` Skill, and the designated
Git remote/task branch. Baseline CI passed with 1,816 tests and one skip before migration.

## Scope

1. Migrate strategy, rules, state, registry metadata, plan, generated status, and reports.
2. Acquire only official C-problem inputs into ignored per-case workspaces; register hashes and
   freeze one RC3 batch before results.
3. Run three isolated answer-sealed C Development first runs through all 14 stages, independently
   freeze and remotely deliver each outcome, then unlock references only as one batch.
4. Build one cross-case failure matrix; accept only repeated failures or universal hard failures;
   publish RC4 at most once or explicitly retain RC3.
5. Regress all three batch cases, 2023 C, 2020 A auxiliary evidence, two synthetic E2E cases, 30
   negative cases, and neutral failure tests.
6. Freeze and execute one fresh, answer-sealed 2024 C Validation; reserve 2025 C without accessing
   its title, archive, problem, attachments, references, or answer.
7. Publish the acceptance/handoff set, remotely deliver all commits, and leave one Draft PR open.

## Non-goals

- No 2024 A Validation, B-problem training, API-key billing, foundation-model training/fine-tuning,
  third-party solution execution, paper prose, main-branch push, force push, merge, or worktree.
- No answer search, reference access before the all-case freeze, first-run overwrite, retry-until-
  success, Agent vote, or case-specific Skill logic.
- No claim of broad generalization, production readiness, or a solved 2026 problem.

## Milestones and acceptance

### M0 — Preflight and branch (`COMPLETE`)

Root, clean status, expected commit/tree, remote identity, old-branch equality, no old PR, no 2024 A
registry evidence, formal RC3 identity, one-Skill invariant, historical evidence cleanliness, and
baseline CI all pass. New branch exists locally/remotely at the starting SHA; old branch is retained.

### M1 — C-target strategy migration (`IN_PROGRESS`)

Policy, decision, docs, plan, registry metadata, state/schema, generated report, checker/tests, and
branch pointer are consistent. Focused checks and full CI pass; one atomic content commit is pushed;
one Draft PR is created and remains Draft.

### M2 — Official inputs and batch pre-run freeze (`PENDING`)

Only official archives are acquired. Raw files remain ignored and immutable. Exact problem/data
hashes, no-solution-exposure results, environment, runner, RC3 tree, case order/fallback, search
policy, rubric, hard failures, roles, interventions, and answer states are frozen and remotely
delivered before any result.

### M3 — Three independent C first runs (`PENDING`)

At most two fresh workers run concurrently with path-level write isolation. Each case completes or
truthfully terminates across 14 stages, preserves every Run, and produces an independent checked,
pushed, remotely verified first-run freeze while all answers remain sealed and the Skill tree stays
unchanged.

### M4 — Unified postmortem and RC4 decision (`PENDING`)

All-case unlock preconditions pass. Limited references are hash-logged with no-copy declarations.
The cross-case matrix classifies every finding. Only eligible general failures enter at most two
revision cycles; otherwise the decision explicitly retains RC3.

### M5 — Unified regression (`PENDING`)

Three non-blind batch regressions, 2023 C, 2020 A auxiliary execution, two synthetic E2E, 30
negative cases, new neutral tests, anti-hardcoding, leakage, secrets, strict validation, and full CI
all pass without a universal hard failure.

### M6 — 2024 C one-shot Validation (`PENDING`)

Candidate/rubric/input/answer state are pre-frozen. A fresh isolated worker runs once within four
hours, covers all main requirements with real Runs, independent feasibility checks, robustness,
Claims and handoff, then writes a terminal freeze. No post-freeze Validation Run or Skill mutation
is allowed; the decision may fail or remain insufficient.

### M7 — Final audit and delivery (`PENDING`)

2025 C access flags remain false; scorecard/professional audit/acceptance/handoff reports match
machine truth; final validation and remote CI pass; local and remote SHA match; Draft PR stays open.

## Validation commands

```text
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_instruction_budget.py
.venv/bin/python scripts/check_skill_discovery.py --expected-name cumcm-modeling-evidence --expected-count 1
.venv/bin/python scripts/check_contracts.py
.venv/bin/python scripts/check_answer_leakage.py
.venv/bin/python scripts/check_secrets.py
.venv/bin/python scripts/check_competition_rc_consistency.py --check
.venv/bin/python scripts/check_skill_training_consistency.py --check
.venv/bin/python scripts/check_target_problem_policy.py --check
.venv/bin/python scripts/validate_repo.py --strict
.venv/bin/python scripts/render_status.py --check
bash scripts/ci.sh
git diff --check
```

## Risks and stop conditions

- Model prior exposure to historical problems is unverifiable; every case records that limitation.
- The 2020 C archive is colocated with previously used 2020 A input. Position 3 remains pending a
  pre-result contamination review; fallback is allowed only for confirmed pollution or unavailable
  official input.
- Official input failure, unsafe extraction, hash drift, answer exposure, Skill drift, case-state
  collision, uncaptured execution, time exhaustion, or infeasible/nonconverged Final selection
  freezes the affected case. Shared-state collision, Skill mutation during the batch, overwritten
  freeze, premature unlock, tracked raw input, copied third-party solution code, unrecoverable CI,
  post-terminal Validation Run, or 2025 C access stops the whole task.
- Target wall time is 16 hours. At a context/runtime boundary, preserve an exact checkpoint, commit,
  push, and resume from the only unfinished milestone; never rerun a frozen case.

## Decision record

- `DECISION-C-TARGET-TRAINING-POLICY-004C` selects C as the target and batch-first-run evidence
  accounting. It is not an architecture decision.
- The formal Skill remains RC3 until all three first runs are frozen. RC4 is conditional on evidence,
  not predetermined.
- 2024 A is `CANCELLED_BEFORE_REGISTRATION_NO_EXECUTION_EVIDENCE`; its old branch remains preserved.

## Actual progress and findings

- Preflight matched the expected root, branch, commit, remote main, old remote branch, merge base,
  and Git tree. Worktree was clean; the old branch had no unique commit and no open PR.
- Formal Skill identity, capability, architecture, discovery count, historical 2023 C/2020 A
  cleanliness, absence of 2024 A registry evidence, and baseline CI passed.
- The global workflow rules are a historical live semantic pointer. Its only existing mutable field
  is the task-branch pointer, so 004C transitions are frozen in `WORKFLOW.md`, the project-state
  schema, and `rules/target_problem_policy.yaml` without weakening the historical allowlist.
- M1 pre-delivery validation: target policy PASS at planned C share 0.80 with realized share 0.50
  reported separately; 130 focused tests passed; full CI passed with 1,834 tests and one skip;
  strict repository validation reported 0 errors and 0 warnings.

## Next step

Finish M1 focused checks, atomically commit/push the strategy migration, create the Draft PR, then
start M2 official-input acquisition and pre-run freeze. Do not start a case worker before M2 is
remotely verified.

## Rollback and update rule

No destructive rollback is allowed. A failed migration keeps the worktree for diagnosis; a failed
case or Run is frozen as evidence. Update this plan after every milestone, failed validation, new
blocker, or approved design change. Preserve old facts and mark superseded decisions instead of
rewriting them. Every validation entry records the command, exit status, counts, and warnings.
