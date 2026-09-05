# PLAN-0004C4 — actual-controller closure, Competition RC7 and fresh C Validation

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4`
Subphase: `C-TARGET-FRESH-VALIDATION-IN-PROGRESS`
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
- `2026-09-05T19:44:00+08:00` — Implementation loop 1 wires the actual completion entrypoint to
  ordered, hash-bound requirement, source, data-sufficiency, selection, Run eligibility,
  compatibility, semantic, aggregate, finalization and handoff Gates. Runtime-only strict
  validators add complete acquisition plans, conjunctive source coverage, manifest-backed
  portfolio hashes/dependency bridges, allowlisted bijective compatibility, Run/output/metric
  ownership, bounded scope and exact aggregate mappings. Formatting, compilation and the preserved
  RC6 neutral contract matrix passed (`57 passed`). The production files must now be Git-bound
  before the real subprocess matrix can be evaluated.
- `2026-09-05T19:58:00+08:00` — After remote-binding loop 1, the full frozen controller matrix
  passed (`14 passed`): all 13 formerly failing probes now block at the expected Gate/reason while
  preserving case state, authoritative inputs, rejected handoff and opaque values. Implementation
  milestone 2 adds canonical multi-Run `final-result/v2`, runtime Claim bindings and a portfolio
  handoff builder so a valid PER_REQUIREMENT/JOINT_PORTFOLIO case can reach the terminal state
  without restoring semantic defaults. Static checks and the legacy-neutral 57-case matrix pass;
  the modified runner again requires a Git-bound commit before actual E2E execution.
- `2026-09-05T20:15:00+08:00` — Froze three project-original neutral actual-controller E2E
  families as 17 tests: PER_REQUIREMENT success/order permutations/binding attacks;
  JOINT_PORTFOLIO success plus shared/actual/scenario hash, bridge and constraint attacks; and
  strict data sufficiency success plus external-policy, simulation-as-empirical, unregistered
  composition and PARTIAL mutations. Collection and static checks pass. The dynamic neutral model
  fixture must be committed before behavior execution because it is part of the frozen code set.
- `2026-09-05T20:22:00+08:00` — The first Git-bound neutral E2E run produced `8 passed / 9
  failed`. Seven failures were test-side assumptions about the unresolved handoff template shape;
  the correct rejection marker is an empty `approved_by`. Two runtime portfolio mutations were
  correctly blocked but by the legacy Gate-4 compatibility shortcut. Implementation milestone 3
  confines that shortcut to unversioned legacy payloads so versioned runtime portfolio consistency
  is manifest-bound at Gate 6. Static checks and the immutable RC6 57-case matrix remain green.
- `2026-09-05T20:31:00+08:00` — The Git-bound frozen controller, neutral E2E and RC6 matrices pass
  together (`88 passed`). The legacy completion-controller regression fixture now supplies explicit
  runtime-v3 requirement-selection and semantic-support artifacts; its success and all-failed
  branches pass without relying on removed defaults, and the all-failed result carries explicit
  null selection identifiers plus a deterministic no-eligible decision hash.
- `2026-09-05T20:34:00+08:00` — Historical compatibility is again read-only PASS. Successor builds
  derive the adapter hashes for the immutable RC1 historical record from the fixed Git blobs rather
  than the live successor files. The stored record is unchanged; its hash remains
  `e95a81fa08a4b2e2c496b9aee95cdb5eb4ac49eebd94de8d8e5ca9554aa85037`, with 20 fixed historical
  failures, and the focused controller/historical suite passes (`22 passed`).
- `2026-09-05T20:43:00+08:00` — Identity-separated read-only prosecutor
  `actual_controller_adversarial_prosecutor_final/Gauss` reported five static findings against
  subject commit `557f0972e14773fdf362c9549adb7d54c5abae6b`. Each was translated into a
  project-original actual-CLI test before production repair and all five reproduced (`5 failed`):
  three false successful handoffs, one untraced late payload-decode crash after durable writes, and
  one correct BLOCK that retained two new manifests. Matrix
  `PHASE-004C4-ACTUAL-CONTROLLER-ADVERSARIAL-FREEZE-001` binds the auditor report, test and
  pre-repair observation. Audit-triggered repair usage remains `0/3` until the freeze is remotely
  bound.
- `2026-09-05T20:55:00+08:00` — Audit-triggered repair loop 1/3 is remotely bound at
  `cd02e61994b906364789c65609de695b6912f1c7`. It removes comparison/selection split truth,
  moves manifest persistence after all pre-final and selected-payload validation, binds scenario
  identity through execution capture and manifest, and requires actual selected-output policy
  exposure/benefit/cost evidence. The frozen adversarial suite passes (`6 passed`) and the combined
  known, adversarial, neutral E2E and RC6 matrix passes (`94 passed`); no second audit loop is open.
- `2026-09-05T21:02:00+08:00` — Current-Skill historical and auxiliary regressions pass: six
  immutable C/A replays report PASS with zero new model Runs and no source-tree writes; two
  project-original synthetic E2E cases reach handoff; the fixed negative matrix is 30/30 with zero
  exceptions or sensitive emissions; RC4 unified and RC5 preservation checkers pass. An expanded
  pytest scope covering output preflight, Claim/aggregate, failure retention, state and all
  controller matrices passes (`239 passed`). The Phase 004C4 regression evidence checker is
  read-only PASS.
- `2026-09-05T21:19:00+08:00` — The first full candidate pytest exposed one historical-checker
  compatibility defect after `2062 passed / 1 skipped`: the old Phase 004C3 Auditor replay read the
  repaired live controller while claiming to audit commit `bf82bf4b03fb0bbd55e7ed3d010cfb6ae1352a09`.
  The checker, not the frozen history or Skill, was corrected to execute/read the exact audited Git
  blobs. Its reproduced RC6 verdict is again `PASS/BLOCK` with the original core/controller hashes.
- `2026-09-05T21:31:00+08:00` — Candidate verification subject
  `c65299a9029875ddad18836a52d5cbc4784b6f07` passed full pytest (`2063 passed / 1 skipped`),
  strict (`0 errors / 0 warnings`), generated-status check, and full local CI (including a second
  `2063 passed / 1 skipped` run and every historical checker). The two-stage RC7 Candidate checker
  reads `rc7_candidate_snapshot.json`, confirms all bound evidence/receipts and exits zero while
  live VERSION/state remain RC6/004C4-repair and `rc7_release.json` is absent. This is candidate
  PASS only; RC7 is not yet released.
- `2026-09-05T21:47:00+08:00` — Candidate snapshot commit
  `dff40dfd0100ee11c6cb7ddd1a8f7803313653bd` is remote-verified. The prescribed live mutation
  advances only the project/Skill version surfaces, ready-state, release manifest and current
  documentation. RC5/RC6 histories remain immutable; the fresh 2018 C input remains locked until
  this RC7 release commit is independently pushed and its remote SHA is verified.
- `2026-09-05T21:15:36+08:00` — RC7 release commit
  `22abe92d2b5da2e3f1be3161e8376fb83b0cee0a` is pushed to the designated task branch and the
  fetched remote SHA matches exactly. The live checker remains PASS; PR 10 is OPEN, DRAFT and
  MERGEABLE at that head. This successor record binds the delivery receipt without changing the
  frozen Skill tree, tests, rubric or evidence policy.
- The first post-freeze full CI ran all 2064 tests and exposed one stale project-version allowlist
  in the historical Competition RC consistency checker (`project_version_relationship`); the
  existing test failed closed. Repair attempt 1 adds only project `0.3.0-competition-rc7` to that
  checker. The frozen Skill tree, release manifest, controller probes and Validation rubric remain
  byte-identical; official input remains locked until the repaired full CI passes.
- Post-freeze full CI repair attempt 2 passes: pytest `2063 passed / 1 skipped` in 309.12 seconds,
  every historical checker passes, and strict reports 0 errors / 0 warnings. The live RC7 checker
  remains PASS and the frozen Skill tree hash remains
  `0b0e001c6bd12d605ad1e1e3fbfb1e4e9b1486e045b9e81c3d4e15f7d9f8f056`. This receipt must be
  remotely delivered before official 2018 C acquisition.
- After that receipt was remote-verified at `f68f7802fcce8e3d531c0d2154d08f87a05933d2`, the
  preferred 2018 official archive was acquired into ignored storage. Its official C title and five
  requirements are recognizable, but its C directory contains only the problem DOCX and an
  official notice directing teams to a separate committee channel; the five data attachments named
  by the problem are absent and the annual page exposes no second download. No model Run started.
  Preflight reason `C_INPUT_ATTACHMENTS_UNAVAILABLE_FROM_OFFICIAL_ARCHIVE` authorizes the frozen
  2017 fallback as an official-input failure, not for difficulty, result or time pressure.
- The direct preregistered 2017 official archive contains a recognizable C problem, both named
  empirical workbooks and the official variable dictionary. Input-suitability passes with three
  primary requirements, no external-data requirement, no known solution contamination and zero
  formal Runs. The fallback is registered answer-sealed as
  `CUMCM-2017-C-VALIDATION-003F`; only clean-context preparation may proceed before the independent
  remotely verified pre-run freeze.
- Fresh-worker schema audit corrected the preliminary Data2 observation count from 26 (which had
  included the header) to 25. The seven concentration levels, file hash and all raw bytes are
  unchanged; this metadata correction occurred before any model Run or pre-run freeze.
- The answer-sealed 2017 C pre-run freeze is remote-verified at
  `8cbc0c5702ba7c7d0ef536dd4b4eced7e6d5dcda` with freeze SHA-256
  `9c078468da856353a7104e6eb4a6deec273f1aae81f6537deedbfc840703940b`; the case workspace is
  `RUNNING` with zero Runs, and formal execution remains locked until the successor delivery
  receipt is itself remotely delivered.
