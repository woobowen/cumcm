# PLAN-0004C — C-Target Batch Generalization and One-Shot Validation

Status: `TERMINAL_EVIDENCE_INSUFFICIENT`
Phase: `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`
Subphase: `C-TARGET-2024C-VALIDATION-TERMINAL-EVIDENCE-INSUFFICIENT`
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

### M1 — C-target strategy migration (`COMPLETE`)

Policy, decision, docs, plan, registry metadata, state/schema, generated report, checker/tests, and
branch pointer are consistent. Focused checks and full CI pass; one atomic content commit is pushed;
one Draft PR is created and remains Draft.

### M2 — Official inputs and batch pre-run freeze (`COMPLETE`)

Only official archives are acquired. Raw files remain ignored and immutable. Exact problem/data
hashes, no-solution-exposure results, environment, runner, RC3 tree, case order/fallback, search
policy, rubric, hard failures, roles, interventions, and answer states are frozen and remotely
delivered before any result.

### M3 — Three independent C first runs (`COMPLETE`)

At most two fresh workers run concurrently with path-level write isolation. Each case completes or
truthfully terminates across 14 stages, preserves every Run, and produces an independent checked,
pushed, remotely verified first-run freeze while all answers remain sealed and the Skill tree stays
unchanged.

### M4 — Unified postmortem and RC4 decision (`COMPLETE`)

All-case unlock preconditions pass. Limited references are hash-logged with no-copy declarations.
The cross-case matrix classifies every finding. Only eligible general failures enter at most two
revision cycles; otherwise the decision explicitly retains RC3.

### M5 — Unified regression (`COMPLETE`)

Three non-blind batch regressions, 2023 C, 2020 A auxiliary execution, two synthetic E2E, 30
negative cases, new neutral tests, anti-hardcoding, leakage, secrets, strict validation, and full CI
all pass without a universal hard failure.

### M6 — 2024 C one-shot Validation (`TERMINAL_EVIDENCE_INSUFFICIENT`)

Candidate/rubric/input/answer state were pre-frozen. A fresh isolated worker completed four actual
Runs within four hours; all six main requirements, independent feasibility and robustness have
valid outputs. The frozen Claim Gate is contradictory, so Claim acceptance failed and handoff was
not reached. The remotely delivered terminal decision is
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`. No post-freeze Validation Run or Skill mutation is
allowed.

### M7 — Final audit and delivery (`IN_PROGRESS`)

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
- M1 content commit `e62fdbc034487589f8da4865967c644bae989ee5` is pushed and matches the
  remote branch. Draft PR 9 is open and remains Draft.
- M2 input acquisition is complete: all three official archives and only their C members are in
  ignored isolated workspaces; titles, archive/problem/data hashes, MIME, sizes, retrieval times,
  answer state, and no-solution-exposure results are registered. All three runnable records remain
  `IN_PROGRESS` only in the registration sense; no candidate Run or modeling result exists.
- The 2020 archive matches the previously cached official package. Prior extracted raw files are
  confined to `A/`, and no prior C registration/result was found, so the 2019 fallback was not
  activated before results. The model-prior limitation remains unverifiable.
- Batch freeze `C-TARGET-BATCH-001-PRE-RUN-FREEZE-001` binds input-registration commit
  `1196689281704d7dcc801952f6b2ce4f5e958624`, all three `SEALED` cases, RC3 tree
  `a4551c8aa0b6b119823f6ce9df3f0f948339bb33`, the deterministic runner, Python 3.11.14, a
  35-package name/version snapshot, target/search policies, the 25-metric rubric, 11 hard failures,
  four formal roles, two-worker maximum, per-case timebox, and zero initial interventions. Its
  canonical payload SHA-256 is `1c075ede5dfe636e6f6ca946bc19b2dc71b8f36e1601653f58de7a8df7fb8a09`;
  no case state had advanced beyond `CREATED` and no Run existed when frozen. Freeze commit
  `af1e0c158cbce131cab8c6f193167b79fe021a7e` is pushed and verified at the same remote SHA.
- M3 executed three isolated RC3 first runs with no formal-Skill mutation and at most two workers.
  2022 C completed nine candidate Runs and terminated truthfully at Stage 11 because the selected
  output omitted required robustness/claim/handoff fields. 2021 C completed six attempts (four
  successes and two preserved infeasible baseline failures) and stopped at comparison because the
  baseline-success and authorized-test-access contracts failed. 2020 C completed six successful
  attempts, passed all 14 stages, and reached `READY_FOR_PAPER_HANDOFF`; its post-selection test was
  accessed once and was not used for selection. No answer/reference was accessed before freezing.
- Each first run was independently committed, pushed, and verified before unified unlock. Original
  freezes remain immutable. Versioned v2 freezes transparently correct two full-version metadata
  fields (2022/2021) and one post-freeze summary-hash timing correction (2020); every original is
  preserved and linked. Current freeze commits are
  `7688b6a3f55052a5ba55396783c48eb5dc12d409` (2022/2021) and
  `29ad3c3f3971e23a36dc7094abdfe86dc5fc6505` (2020).
- The post-freeze full CI passed with 1,850 tests and one skip; strict validation, target policy,
  batch freeze, and all first-run freeze checks passed. Unified unlock tooling commit
  `49f5dd98b7d546f1e380e8b48d39078a1e176fc0` is remotely verified. Its dry run and write run both
  passed against the exact three freeze commits and the unchanged RC3 tree. Receipt SHA-256 is
  `d6a9aa50ce294fc82f2c195d76fa0a5aa745b681544f3455f2991821d100d69a`; all three cases changed
  together to `UNLOCKED_AFTER_FIRST_RUN` at `2026-09-05T00:59:00+08:00`.
- Bounded post-unlock review used exactly one official page and one published analysis per case;
  all six bodies remain ignored, hash-logged, and uncopied. The cross-case matrix classified six
  findings and admitted exactly one change set: the output-contract failure appeared independently
  in all three cases and becomes hard/noncompensable when discovered after sealing. The five
  case-specific, method-difference, or already-correctly-blocked findings produce no Skill change.
- Revision cycle 1 implemented the sole RC4 candidate at commit
  `297cad0a29c659b18484d4f3b67d69a942ad415c`, Skill tree
  `d041ca38de030ae04813ef02dbe12f7f2b7a1c22`. It adds a non-result, non-ranking placeholder
  selected-output preflight before experiment freeze and reuses the exact Gate in `execute`, while
  retaining invalid output as failed evidence. Focused tests passed 21/21; the full Competition RC
  unit set passed 144/144 after the version-aware candidate receipt. Added-line anti-hardcoding,
  one-Skill, no-second-state, and no-third-party checks pass. At that checkpoint it was a remotely
  verified candidate rather than a formal release; M5 subsequently satisfied its release gate.
- M5 completed three clean non-blind C batch regressions, the 2023 C main chain with STALE probe,
  the 2020 A auxiliary executor path with one sealed exit-23 failure and success-only selection, two
  synthetic E2E cases, and all 30 original negatives. Full CI passed with 1,865 tests and one skip;
  strict validation reported zero errors/warnings and no batch universal hard failure was found.
- RC4 (`0.2.0-competition-rc4`) is formally frozen for one-shot 2024 C Validation. Its implementation commit is
  `297cad0a29c659b18484d4f3b67d69a942ad415c`, Skill tree
  `d041ca38de030ae04813ef02dbe12f7f2b7a1c22`, and release evidence subject commit is
  `9607e7f6f85c4af2ce0423bdca4f52019d68e649`.
- M6 registered the official 2024 C title and six input/template hashes, then remotely froze the
  answer-sealed protocol, rubric, RC4 tree, environment and fresh-worker boundary before results.
  The pre-run freeze payload is `d1b5456f...`, and its remote CI passed.
- The fresh worker wrote pre-result code, which the main Orchestrator bound at commit
  `f12aa707cdf756c657dde0d69556b9f575b748ed`. The frozen grid contained baseline and primary
  candidates at seeds 104729 and 130363. All four attempts were executed and sealed once, with no
  retry, recovery, run-phase manual intervention or result-driven code change.
- The primary candidate won the frozen validation metric (`169264118.00319` versus baseline
  `110079957.9191615`). Post-selection test access was exactly one and not used for selection. The
  selected output covered 6/6 requirements, four independent feasibility records with zero
  violations, three structure-preserved workbooks and three quantitative perturbations.
- Final reached `FINAL_CANDIDATE`, but `claim-check` and `validate --check` each returned only
  `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`. RC4 requires the top-level Claim text to equal
  both the global Final scope and the first requirement-specific claim text; those frozen strings
  differ. The case was formally recorded as `REJECTED`; no accepted handoff was generated.
- Terminal freeze `CUMCM-2024-C-VALIDATION-001-TERMINAL-FREEZE-001` and decision
  `DECISION-C-TARGET-VALIDATION-004C` were committed and remotely verified at
  `197f62bc75ebe832e9dd3ced0306740f336b80d6`. Answer state remains `SEALED`, RC4 is unchanged, and
  the terminal decision is `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`.

## Next step

After final report/CI delivery, start only
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`: freeze a generic Claim-scope repair and neutral tests,
then validate it on a different answer-sealed C case. Do not rerun 2024 C as Validation and do not
access the reserved 2025 C in this phase.

## Rollback and update rule

No destructive rollback is allowed. A failed migration keeps the worktree for diagnosis; a failed
case or Run is frozen as evidence. Update this plan after every milestone, failed validation, new
blocker, or approved design change. Preserve old facts and mark superseded decisions instead of
rewriting them. Every validation entry records the command, exit status, counts, and warnings.
