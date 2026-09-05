# PLAN-0004C3 — RC6 release evidence repair and fresh C Validation

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3`
Subphase: `RC6-RELEASE-AND-EVIDENCE-SEMANTICS-REPAIR`
Owner: main agent / `modeling_orchestrator`
Branch: `feat/phase004c2-claim-scope-repair-validation-2019c`
Starting commit: `fc35ab844d7256615acb15d82a8d91260945dfe2`
Design: `docs/RC6_REQUIREMENT_EVIDENCE_DESIGN.md`

## Purpose, environment, scope and non-goals

Produce a release-consistent `0.2.0-competition-rc6` Skill / `0.3.0-competition-rc6` project,
repair requirement-level data sufficiency, per-requirement/portfolio selection, and bounded semantic
Claim support, then run exactly one fresh answer-sealed C Validation. Use existing Python 3.11.14
`.venv`, K1, one formal Skill, one project state, Draft PR 10, and the designated task branch.

Preserve RC5 and the terminal 2024/2019 Validation histories. Do not recompare K1/W1, add an
architecture or fifth formal Skill Agent, train a model, integrate third party content, rerun old
Validation cases, access 2025 C, search for answers, or create new branches/worktrees/PRs. Formal
Skill changes are limited to two revision cycles and stop when fresh Validation starts.

## Historical boundary and starting evidence

- HEAD and remote task branch: `fc35ab844d7256615acb15d82a8d91260945dfe2`; worktree clean.
- PR 10: `OPEN`, `DRAFT`, `MERGEABLE`; baseline `offline-validation` passed.
- Baseline local CI: Ruff PASS; pytest `1940 passed, 1 skipped` in 308.25s; strict 0/0.
- 2024 pre-run freeze, decision and terminal freeze are byte-identical to terminal commit
  `197f62bc75ebe832e9dd3ced0306740f336b80d6`; no successor Run is allowed.
- 2019 pre-run, nine Runs, decision and terminal freeze are byte-identical to terminal commit
  `b289f2dfcaebe8edca5335ed4bf89f383c67eb51`; no later Run commit exists.
- RC5 blocker is `RC5_VERSION_FILE_MISMATCH`; root is project RC5, runner/SKILL/manifest are Skill
  RC5, and the Skill `VERSION` is RC4. The mismatch remains historical evidence after RC6 exists.
- `CUMCM-2025-C-HELDOUT-RESERVED` is `SEALED_NOT_ACCESSED`; all six access flags are false.

## Milestones and acceptance criteria

### M0 — Preflight and phase start

Verify directory, exact branch, clean worktree, remote SHAs, merge-base, PR/auth/checks, tool versions,
all `AGENTS.md`, baseline CI, historical immutability, no post-freeze Runs, 2025 flags, one Skill,
`third_party_integrated=false`, and the real version mismatch. Move completed 004C2 Plan, freeze this
design/plan, migrate live state to 004C3, render status, test, commit, push, and verify remote SHA.

### M1 — Neutral expectations frozen before implementation

Freeze deterministic offline, temporary-workspace tests for release consistency (8), evidence/data
sufficiency and acquisition (17), selection/portfolio (10), semantic support (11), and legacy/order
compatibility (7): all 53 requested cases. Tests contain no historical year, problem number/title,
entity, attachment, or domain field. Record expected status/reason code and test-tree hash; commit and
push the failing expectation checkpoint before any formal Skill implementation.

### M2 — RC6 implementation, at most two cycles

In the existing runner/templates/workflows, add evidence classes and source provenance,
`DATA_SUFFICIENCY_PREFLIGHT`, acquisition planning/recheck, `GLOBAL_JOINT` / `PER_REQUIREMENT` /
`JOINT_PORTFOLIO`, compatibility checks, and structured Claim predicates. Preserve execute/capture/
seal, failure retention, input immutability, STALE, leakage, and v1/v2 derived compatibility. Add
`scripts/check_skill_release_consistency.py --check` and its fault tests. Each cycle records root
cause, failing neutral tests, changed files, focused/historical results, Skill tree, and blockers.

### M3 — Read-only diagnostics and regression

Produce new 004C3 derived diagnostics without writing old workspaces: 2019 must identify missing
empirical data before expensive execution and reject zero-exposure policy support; 2024 must retain
its verdict while replaying bounded Claim support. Regress 2020/2021/2022/2023 C, auxiliary 2020 A,
two synthetic E2E, 30 negatives, RC4 output preflight, RC5 Claims, one-Skill, anti-hardcoding,
leakage, secrets, provenance and historical hashes.

### M4 — Auditor 1 and RC6 release freeze

Provide one read-only identity-separated Auditor only the hash-bound release/regression bundle.
Every BLOCKER needs deterministic test evidence. Release only when consistency, 53 neutral tests,
diagnostics, all regressions, full pytest, strict, local CI, discovery, leakage/secrets and Auditor 1
have no BLOCKER. Freeze Skill/project versions, commit/tree/runner/contracts/tests/regressions/
diagnostics/environment, commit and push. Verify local HEAD equals remote branch before any new
Validation input is read.

### M5 — Fresh Validation registration and pre-run freeze

Directly access only the supplied official 2018 page/archive after M4. Log URL/archive/problem/data
hashes, type, size, time, suitability and `SEALED` answer state; never access solutions or 2025.
Fallback to the supplied official 2017 case only for pre-result contamination or unrecoverable input
failure, recording `VALIDATION_PREFLIGHT_DISQUALIFIED`. Bind RC6 identity, environment, inputs,
requirements/evidence, sufficiency/acquisition plan, selection mode, rubric, hard failures, four-hour
boundary and one-shot policy. Commit/push/remote-verify this freeze before execution.

### M6 — Fresh-worker four-hour one-shot

Use a clean-context worker that sees only frozen RC6, generic protocol, official inputs, and allowed
general primary sources. Run all 14 stages and the exact execute -> capture -> seal-run -> validate
-> compare -> finalize -> claim-check -> handoff chain. Case code may change only before terminal
freeze and every Run binds the exact blob/commit. Do not change Skill/tests/rubric/evidence policy or
extend the deadline. Retain partial, failed, infeasible, stale and evidence-insufficient outcomes.

### M7 — Terminal decision, Auditor 2 and delivery

Stop case mutation/Runs, create `DECISION-C-TARGET-VALIDATION-004C3` and terminal freeze, run freeze
check, commit, push and verify remote SHA before any optional reference access. Then run the second
and final read-only Auditor on RC6 constancy, chronology, one-shot, requirement/data/selection/Claim
support, failure retention, no result tuning, and 2025 non-access. No post-freeze Run or verdict edit.

### M8 — Final regression, docs, state and Draft PR

Run Ruff lint/format, focused suites, historical diagnostics/regressions, Validation checks, full
pytest, instruction/discovery/contracts/leakage/secrets/release/RC/training/target checks, strict,
local CI, diff/status, and offline GitHub Actions. Sync GOALS, WORKFLOW, PLANS, README, CHANGELOG,
VERSION, target/development protocols, registry, state, generated current status, 004C3 reports and
acceptance. Update PR 10 title/body; keep it OPEN/DRAFT and never merge.

## Required reports

Create `reports/phase004c3_release_integrity.md`, `phase004c3_data_sufficiency.md`,
`phase004c3_requirement_selection.md`, `phase004c3_semantic_claim_support.md`,
`phase004c3_neutral_tests.md`, `phase004c3_historical_regression.md`,
`phase004c3_2019_diagnostic.md`, `phase004c3_2024_diagnostic.md`,
`phase004c3_rc6_release.md`, `phase004c3_fresh_validation.md`,
`phase004c3_validation_decision.md`, `phase004d_heldout_handoff.md`, and
`phase004c3_acceptance.md`. Reports summarize machine truth and never replace it.

## Validation commands

Use the exact requested focused suites followed by `.venv/bin/python -m pytest -q`, instruction
budget, Skill discovery, contracts, leakage, secrets, release/RC/training/target consistency,
`.venv/bin/python scripts/validate_repo.py --strict`, `bash scripts/ci.sh`, status render check,
`git diff --check`, status, remote SHA verification, and PR checks. GitHub Actions remain offline and
must not download official inputs, read ignored raw inputs/answers, or rerun Validation.

## Risks, stop rules, rollback and routing

Stop without rollback for historical evidence drift, 2025 access, contaminated/corrupt official
input, unlogged external data, answer exposure, hardcoding, two failed Skill cycles, Skill drift,
post-freeze Run, or irrecoverable CI. Never reset/clean or overwrite user work. Pre-release edits can
be corrected by a new atomic commit; frozen evidence is superseded only by new versioned artifacts.

Validation PASS routes only to `PHASE-SKILL-C-TARGET-HELDOUT-004D`. A valid RC6 with failed,
insufficient, or incomplete Validation routes to `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C4`. RC6
repair failure retains this phase with `next_phase_allowed=null`. Never claim full generalization,
production readiness, or that 2026 C is solved.

## Decision record, progress and update rule

The user authorized `DIRECT-REPAIR-AND-FRESH-VALIDATION`, supplied exact official preferred/fallback
URLs, required a fresh worker and at most two read-only Auditors, and said to start immediately.
M0 preflight passed with the one documented 2024 live-workspace replay caveat: the pre-run checker's
optional workspace mode is inapplicable after terminal evolution; tracked freeze/decision/delivery
bindings and exact immutable-file diffs pass. No package, toolchain, or configuration was installed.

Update this Plan after every milestone, failed validation, revision cycle, blocker, route decision,
commit and remote receipt. Preserve prior entries; append corrections rather than rewriting facts.

### Progress log

- `2026-09-05T14:55:56+08:00` — M0 local acceptance complete. Initial preflight matched the
  designated path/branch/remote and expected HEAD `fc35ab8`; worktree was clean; PR 10 was
  OPEN/DRAFT/MERGEABLE with passing `offline-validation`. Baseline `bash scripts/ci.sh` passed
  Ruff, pytest `1940 passed / 1 skipped` in 308.25s, and strict 0/0. Exact file diffs proved both
  historical terminal chains unchanged and 2019 had no post-terminal Run commit; 2025 six flags
  remained false; formal Skill count was one and third-party integration false.
- The first successor-state focused attempt exposed two obsolete current-state assertions and was
  repaired by separating immutable 004C2 truth from legal 004C3 live state. The first full-CI
  attempt then reported 89 failures caused by one missing `competition_rc_successor` phase/version
  registration plus three local phase allowlists. No frozen artifact was changed. A proposed 2.5
  schema bump was withdrawn before commit to avoid an unnecessary migration subsystem; 004C3 uses
  the backward-compatible 2.4 schema line with explicit fail-closed phase branches.
- After the second and final M0 compatibility repair, focused state tests passed `30/30`, full
  pytest passed `1950/1 skipped` in 310.28s, and final `bash scripts/ci.sh` passed
  `1950/1 skipped` in 310.04s plus strict 0/0. Contracts accepted 78 valid fixtures and rejected
  68 invalid fixtures; release acceptance remained truthfully `BLOCK`, RC5 version consistency
  remained false, Skill discovery remained one, and all target/training/history checkers passed.
  No dependency, package, toolchain, or configuration was installed or changed.
- Startup commit `6782c2f2b275ac7a8902ae2f3045344931f7e8f3` was pushed and local/remote
  task-branch SHAs matched. PR 10 remained OPEN/DRAFT/MERGEABLE; its offline CI was still pending
  when M1 test authoring began.
- `2026-09-05T15:02:10+08:00` — M1 expectations frozen before implementation. The case-neutral
  matrix contains all 53 requested cases plus three release faults (project version mismatch,
  illegal prerelease, missing blocked-history record). Collection is 57 tests: the completeness/
  anti-hardcoding meta-test passed and all 56 behavior cases failed solely because the new checker
  or one of four declared contract functions was absent. Test SHA-256 is
  `242963976022ba7449fbd8ea8488cd65acd4a05744d3f7ee88344c81a76c7adc`; RC5 Skill tree remained
  `0c27a6aa25d5f591277707fd2343b34e65a703fb`. Frozen expectations may not be edited during M2.
- `2026-09-05T15:38:10+08:00` — M2 completed in exactly two formal revision cycles; the Skill
  modification window is closed. Cycle 1 implemented the four pure contract evaluators, three
  hash-bound supporting artifacts/CLI Gates, release checker and RC6 surfaces. Its first focused
  run was `56 passed / 1 failed`; the lone selection failure was corrected by short-circuiting
  derivative metric/output findings behind the wrong-Run semantic root cause. Both E2E cases then
  exposed the expected Git-blob precondition while the candidate was uncommitted.
- Candidate commit `12ecd586fd46ae7a63037435b7fef6b697d85a21` supplied the required Git identity.
  Both synthetic E2E cases passed, then the first full suite reported `1998 passed / 1 skipped /
  9 failed`. Cycle 2 fixed four successor-compatibility checks, three RC6 test fixtures/helper
  callers, and one leakage-scanner phrase; it also integrated generic selection/semantic artifacts
  into the captured-episode completion controller. Focused compatibility passed `125/125`, E2E and
  controller passed `4/4`, and the final full pytest passed `2007/1 skipped` in 311.78s.
- RC6 candidate Skill tree is `0d0d65a7148d146424e31318ba003bdab80db6e5`; runner SHA-256 is
  `2dbc4ce2d9cb5cd1ebb22f4039011ec30d4102f08e8e794c3f22f90c46c31879`. The frozen neutral
  test SHA remains unchanged. RC5 historical artifacts and all 2025 access flags remain unchanged;
  no dependency, package, toolchain or configuration was installed. RC6 remains unreleased until
  M3 regressions and M4 Auditor 1/release consistency pass.
- `2026-09-05T15:46:09+08:00` — M3 read-only historical diagnostics and regression checks passed.
  The 2019 diagnostic identifies an empirical-data pre-execution stop and rejects a policy Claim
  bound to the selected Run's zero priority exposure. The 2024 bounded descriptive view and v2
  compatibility adapter pass without changing the evidence-insufficient verdict. Exact Git diffs
  confirm both frozen chains are unchanged and no post-freeze numerical Run exists. RC4 batch
  regressions passed 3/3, unified coverage passed three batch plus two synthetic cases, and RC6
  negative coverage passed 30/30 with zero unhandled exceptions or sensitive values. Leakage,
  secret/private-path, provenance, one-Skill and target-policy checks passed. Legacy RC5 whole-file
  integrity checkers predictably report authorized RC6 code drift and are recorded as non-Gates;
  frozen case-path diffs are the immutability evidence. Focused RC6/historical tests passed 136/136;
  full CI passed Ruff and pytest `2008 passed / 1 skipped` in 310.90s, strict validation returned
  0 errors / 0 warnings, generated status was current, and `git diff --check` passed. The frozen
  neutral-test SHA and RC6 Skill tree stayed unchanged. Auditor 1 remains pending before RC6 freeze.
