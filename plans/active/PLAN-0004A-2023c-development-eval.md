# PLAN-0004A — 2023 C Development Eval

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-DEVELOPMENT-EVAL-004`
Subphase: `CUMCM-2023-C-DEVELOPMENT-FIRST-RUN`
Owner: main agent / `modeling_orchestrator`
Started: `2026-09-04T05:51:52Z`
Branch: `feat/phase004-development-eval-2023c`
Starting commit: `a93a96d79890f6774552dc5ff333f833099edf83`
Case: `CUMCM-2023-C-DEVELOPMENT-001`

## 1. Objective and boundary

Run the formal `cumcm-modeling-evidence` RC1 Skill on one answer-sealed historical Development
problem, freeze the unaltered first run before any answer access, diagnose observed failures, and
accept only problem-independent improvements into at most two RC2 revision cycles. Then run a
Development regression and three semantics-preserving Stress transformations. This phase does not
prove Validation, Held-out, or competition-candidate generalization.

The official problem and raw attachments remain untracked and immutable in the ignored private
workspace `.cache/official_inputs/CUMCM-2023-C/`. Repository policy forbids reading
`benchmark-vault`; that path is not used. No solution, commentary, awarded paper, problem-specific
article, code repository, blog, or video is accessed before the first-run freeze.

## 2. Current environment and frozen start

- Root and branch: the expected repository root on
  `feat/phase004-development-eval-2023c`; not `main`.
- Base/HEAD: `a93a96d79890f6774552dc5ff333f833099edf83`, equal to `origin/main` and the
  remote task branch after merged PR #6.
- Formal Skill: `0.2.0-competition-rc1`, `COMPETITION_RC`, K1 tree
  `49d499ab0e063a2cf72a780c89ee969a696fb02e`.
- Baseline: `bash scripts/ci.sh` exit 0; `1804 passed, 1 skipped` in `363.70s`; strict
  validation `0 errors, 0 warnings`; one formal Skill.
- Runtime identity: `gpt-5-codex`; reasoning visibility is unavailable and is frozen as `UNKNOWN`.
  Prior exposure to the historical problem is unverifiable.

## 3. Execution design and budgets

1. Register the official PDF and four workbooks by SHA-256 under `DEVELOPMENT` / `SEALED`.
2. Pre-register requirement/data/model/execution/evidence/efficiency scoring and all hard gates.
3. Execute the 14 formal stages in order with RC1; preserve every failure and intervention.
4. Freeze regardless of success or failure, commit the freeze independently, push it, and verify the
   remote SHA before any reference unlock.
5. Access at most the permitted official/high-quality reference classes, classify gaps, and reject
   problem-specific or reference-only changes.
6. Use at most two Skill revision cycles; run focused, smoke, negative, full-regression, discovery,
   consistency, answer-leakage, and secret checks after each accepted revision.
7. Run one same-case Development regression plus Stress A/B/C without overwriting the first run.
8. Publish acceptance evidence, keep the PR open and Draft, and route only to 004-B or continued
   004-A.

The sprint wall-time target is 12 hours: official input/registration at most 30 minutes; first run at
most 6 hours; freeze at most 30 minutes; postmortem at most 90 minutes; RC2/regression/Stress at most
3.5 hours. Real-problem execution receives at least 60% of effort; Skill changes about 25%; state,
documentation, and regression at most about 15%.

## 4. Roles and write ownership

- `modeling_orchestrator` is the sole case/project-state and acceptance writer.
- `problem_and_model_analyst` proposes requirements, assumptions, sources, models, and baseline.
- `data_and_experiment_engineer` audits official inputs and executes first-party code with complete
  logs; any write scope must be explicitly conflict-free.
- `adversarial_evidence_auditor` is read-only and cannot advance state or vote on a result.

Paths are shared and not OS-isolated, so formal roles execute serially unless a write scope is
explicitly granted. Deterministic Gates, not role majority, decide acceptance.

## 5. Acceptance and stop conditions

The first run is accepted as frozen only when the answer state is `SEALED`, source/problem/data/Skill
and search hashes recompute, failures remain present, Run manifests validate, the freeze has its own
commit, and the remote task branch reports that exact SHA. RC2 is accepted only for an observed
generalizable failure, an answer-independent test, no problem-specific token, and full non-regression.

Stop immediately for unsafe input acquisition, answer exposure before freeze, input mutation,
unexecuted code presented as execution, leakage, non-replayable freeze, hardcoded problem answers,
two exhausted revision cycles, unrecoverable full CI, or tracked raw/reference/credential content.
The terminal result may legitimately be RC2 ready, no Skill change, incomplete, inputs required,
contamination suspected, or infrastructure blocked.

## 6. Validation and delivery

Use the repository-prescribed Ruff, focused Skill tests, freeze/registry/RC1/RC2/Stress checks,
`pytest`, instruction/discovery/contracts/leakage/secrets/consistency/strict checks,
`bash scripts/ci.sh`, `git diff --check`, and branch status. Each record includes command, exit,
duration, execution type, Skill version, case, answer state, result, blocker, and evidence hash.

Commits are scoped and explicitly staged; never use `git add .` or `git add -A`. The first-run freeze
is an independent pushed commit. Later commits and the open Draft PR must remain on the task branch;
no force push, ready-for-review transition, merge, or direct feature push to `main` is allowed.

## 7. Progress

- `2026-09-04T13:38:47+08:00`: preflight confirmed correct root/branch, clean worktree, merged PR
  #6, matching local/remote/base SHA `a93a96d`, authenticated GitHub, and no open task-branch PR.
- Baseline CI passed at `1804 passed, 1 skipped` in `363.70s`, strict `0/0`; RC1 discovery count is
  one. No tracked historical problem, answer, solution, code, or vault artifact was found.
- The official archive was reached only through the `mcm.edu.cn` historical-problem index. The
  downloaded RAR5 is `41,797,492` bytes with SHA-256
  `37b1010672adcf35831e798264cc69db616027f2287cfeae3c4ee6daf03ae4e6`; it contained only the
  format document and A–E problem archives. The C archive contained one official PDF and four XLSX
  inputs; no answer/reference class was opened.
- The launcher dry-run and actual registration both passed. The case is `CREATED`, first run
  `IN_PROGRESS`, and answer `SEALED`; no RC1 Skill file has changed.
- Environment note: system installation of `unar` was attempted once and failed before installation
  because `sudo` required a terminal password. A local ignored `libarchive-tools` package was used
  instead. The existing `.venv` was bootstrapped with pip and received the data/modeling libraries
  listed in the final dependency report.

## 8. Update, rollback, and exact next step

Update this file after every milestone, failed validation, blocker, accepted revision, freeze,
unlock, and delivery receipt. Preserve factual failures; never rewrite the first run after unlock.
Before publication, remove only uncommitted scoped work; published corrections use `git revert` and
retain frozen evidence.

Exact next step while this plan is active: `继续 PHASE-SKILL-DEVELOPMENT-EVAL-004-A`.
