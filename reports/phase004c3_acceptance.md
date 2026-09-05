# Phase 004C3 acceptance report

## Verdict

`RC6_RELEASE_REPAIR_BLOCKED`.

RC6 is not released. The active release remains `0.2.0-competition-rc5-blocked`, the repository
contains only an unreleased `0.2.0-competition-rc6` candidate, no fresh C Validation was started,
and `next_phase_allowed` is `null`.

## Starting checkpoint

- Branch: `feat/phase004c2-claim-scope-repair-validation-2019c`.
- Starting HEAD: `fc35ab844d7256615acb15d82a8d91260945dfe2`.
- Draft PR: #10, OPEN/DRAFT/MERGEABLE; it was never merged or marked ready.
- RC5 blocker: `RC5_VERSION_FILE_MISMATCH`.
- Prior Validation outcomes: 2024 C and 2019 C both
  `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`.
- Baseline local CI: Ruff PASS, pytest `1940 passed / 1 skipped`, strict 0 errors / 0 warnings.

## Work completed before the release audit

The project froze 56 case-neutral behavior expectations plus one completeness/anti-hardcoding
meta-test before implementation. The frozen test SHA-256 is
`242963976022ba7449fbd8ea8488cd65acd4a05744d3f7ee88344c81a76c7adc`. Exactly two formal Skill
revision cycles produced candidate project `0.3.0-competition-rc6`, Skill
`0.2.0-competition-rc6`, implementation commit
`12ecd586fd46ae7a63037435b7fef6b697d85a21`, Skill tree
`0d0d65a7148d146424e31318ba003bdab80db6e5`, and runner SHA-256
`2dbc4ce2d9cb5cd1ebb22f4039011ec30d4102f08e8e794c3f22f90c46c31879`.

Candidate capabilities added `requirement-evidence/v1`, `data-sufficiency/v1`,
`requirement-selection/v1`, and `claim-evidence/v3`; declared evidence classes and source
provenance; `GLOBAL_JOINT`, `PER_REQUIREMENT`, and `JOINT_PORTFOLIO`; and bounded semantic Claim
types. Frozen neutral tests passed 57/57. Historical regression passed three RC4 batch cases, two
synthetic E2E cases and 30/30 original negatives. Full pre-audit pytest passed
`2008 passed / 1 skipped`; strict validation was 0/0. A later exit-code audit found that the
enclosing CI invocation had continued past pytest and failed on stale historical-checker bindings;
the delivery section records that harness correction.

## Independent Auditor 1

Auditor 1 reviewed commit `bf82bf4b03fb0bbd55e7ed3d010cfb6ae1352a09` read-only. It verified
the aligned version surfaces, one formal Skill, frozen test/tree/runner hashes, two-cycle chronology,
historical immutability, regressions, leakage/secrets/provenance, and the six false 2025 access flags.
It then returned `BLOCK` with five reason codes:

1. `RC6_DATA_SUFFICIENCY_ACQUISITION_FAIL_OPEN`.
2. `RC6_SELECTION_GATE_FAIL_OPEN_PORTFOLIO_BINDING`.
3. `RC6_SEMANTIC_GATE_FAIL_OPEN_BINDING`.
4. `RC6_COMPATIBILITY_GATE_VACUOUS`.
5. `RC6_PER_REQUIREMENT_PIPELINE_NOT_EFFECTIVE`.

The main agent reproduced every probe through a separate read-only checker. Audit evidence SHA-256
is `93ba67c90734624343dc1431090bb955d4ffeae9c63160ba581c1131cae3463b`.

| Probe | Required safe result | Actual result | Audit result |
|---|---|---|---|
| External acquired source when external data are forbidden | BLOCK | SUFFICIENT | defect reproduced |
| Acquisition plan missing required planning fields | BLOCK | ACQUISITION_REQUIRED | defect reproduced |
| Fields/time/entities split across sources with no conjunctively sufficient source | BLOCK | SUFFICIENT | defect reproduced |
| Dependent requirements split across independent Runs | BLOCK | PASS | defect reproduced |
| Portfolio input/scenario hashes missing | BLOCK | PASS | defect reproduced |
| Declared shared hashes disagree with actual Run hashes | BLOCK | PASS | defect reproduced |
| FAILED, unsealed and non-current selected Run | BLOCK | PASS | defect reproduced |
| Claim requirement unsupported by selected Run | BLOCK | PASS | defect reproduced |
| Claim output not owned by selected Run | BLOCK | PASS | defect reproduced |
| Claim has no metric binding | BLOCK | PASS | defect reproduced |
| Descriptive Claim has `scope_bounded=false` | BLOCK | PASS | defect reproduced |
| Aggregate requirement maps to wrong Claim ID | BLOCK | PASS | defect reproduced |
| Unknown compatibility kind/version and non-permutation | BLOCK | PASS | defect reproduced |

The controller inspection also reproduced five pipeline facts: it hardcodes `GLOBAL_JOINT`, maps one
Run to every requirement, emits every semantic Claim as `DESCRIPTIVE`, assigns
`PROVIDED_EMPIRICAL`, and assigns positive policy exposure. Therefore per-requirement/portfolio and
Claim-type semantics do not control the actual fresh completion chain.

## Release Gate disposition

| Required release condition | Result |
|---|---|
| Declared version surfaces aligned | PASS for candidate surfaces |
| Live release consistency | BLOCK; no release manifest and state remains RC5-blocked |
| Frozen neutral tests | PASS, but insufficient coverage established by Auditor 1 |
| 2019 read-only diagnostic | PASS, no Validation credit |
| 2024 read-only diagnostic | PASS, no Validation credit |
| Historical regressions | PASS |
| Two synthetic E2E | PASS |
| 30 negatives | PASS |
| Anti-hardcoding | PASS for frozen test/Skill scan; controller semantic hardcoding found |
| Skill discovery | PASS, exactly one |
| Answer leakage | PASS, zero findings |
| Secrets/private paths | PASS, zero findings |
| Full pre-audit pytest | PASS, `2008 passed / 1 skipped` |
| Strict validation | PASS, 0 errors / 0 warnings |
| Auditor 1 without blocker | FAIL: five release-blocking classes |

Because all 15 conditions were mandatory, passing regressions cannot compensate for the Auditor 1
hard failures. The two formal revision cycles are exhausted and the Skill modification window is
closed. No third cycle was attempted. `rc6_release.json` was not created.

## Historical preservation

- 2019 pre-run freeze, nine Runs, decision and terminal freeze are byte-identical to commit
  `b289f2dfcaebe8edca5335ed4bf89f383c67eb51`; no later Run commit exists.
- 2024 pre-run freeze, decision and terminal freeze are byte-identical to commit
  `197f62bc75ebe832e9dd3ced0306740f336b80d6`; its only later case-path addition is a delivery receipt.
- The RC5 release and `RC5_VERSION_FILE_MISMATCH` acceptance block remain immutable.
- No old verdict, Claim, case code, Run, terminal freeze or answer state was changed.
- One accidentally invoked legacy diagnostic created an untracked derived summary only; it was
  removed immediately and was not used as evidence.

The 2019 diagnostic correctly identifies absent empirical evidence before execution and rejects the
selected baseline's zero-exposure policy Claim. The 2024 diagnostic permits a bounded descriptive
view and legacy read compatibility while preserving its evidence-insufficient verdict. Both are
`READ_ONLY_DERIVED_NO_VALIDATION_CREDIT`.

## Fresh Validation disposition

Release failure occurred before official-input acquisition. Neither preferred 2018 C nor fallback
2017 C was selected, registered, downloaded or read. Official title, problem, attachments, source
hashes and suitability are therefore `NOT_ACCESSED`/`NOT_APPLICABLE`, not guessed. There was no
fallback decision, contamination finding, pre-run freeze, clean-context worker, timebox start, case
code, model, Run, comparison, Final, Claim, handoff or terminal Validation freeze.

All 14 lifecycle stages are `NOT_RUN`: PROBLEM_INTAKE, REQUIREMENT_DECOMPOSITION,
RESEARCH_AND_SOURCE_PLANNING, ASSUMPTION_AND_SYMBOL_DEFINITION, DATA_AUDIT,
MODEL_PORTFOLIO_GENERATION, BASELINE_DEFINITION, EXPERIMENT_DESIGN,
IMPLEMENTATION_AND_EXECUTION, MODEL_COMPARISON, ROBUSTNESS_AND_SENSITIVITY, FINAL_RUN,
CLAIM_EVIDENCE_VALIDATION, and MODELING_TO_PAPER_HANDOFF. Actual fresh model Run count is zero.
Auditor 2 was not run because its trigger—an actual fresh Validation terminal decision—never
occurred.

## 2025 reservation

`CUMCM-2025-C-HELDOUT-RESERVED` remains `SEALED_NOT_ACCESSED`:

- `archive_accessed=false`
- `title_accessed=false`
- `problem_accessed=false`
- `attachments_accessed=false`
- `references_accessed=false`
- `answer_accessed=false`

## Machine truth and terminal state

- Decision: `evals/results/phase-004c3/DECISION-C-TARGET-VALIDATION-004C3.json`, SHA-256
  `29f9427f0039c83a08fbc6f2aeb5a04faf5c4fca7bb5e0d96f96a15cce8e7055`.
- Release block: `evals/results/phase-004c3/rc6_release_acceptance_block.json`, SHA-256
  `a546f4c81dd41c928ff04299581123c37431d63698b57c451fc95e3cc35f56c1`.
- Terminal freeze: `evals/results/phase-004c3/rc6_release_terminal_freeze.json`, SHA-256
  `3cce1a49ceb93a9a7a046b6905da16be8edf2c47dcadcc1fde0cd557f338e272`.
- Phase: `PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3`.
- Subphase: `C-TARGET-FRESH-VALIDATION-BLOCKED`.
- Technical status: `RC6_RELEASE_REPAIR_BLOCKED`.
- Active Skill release: `0.2.0-competition-rc5-blocked`.
- Selected architecture: `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`.
- Current Validation case: `null`.
- Blockers: the five Auditor 1 reason codes above.
- Next phase: `null`.

## Delivery and verification

Milestone commits through historical regression were remotely delivered through
`bf82bf4b03fb0bbd55e7ed3d010cfb6ae1352a09`. Terminal block commit
`b02d3ac276e6971f56f66d7b6af97b091b3b7c38` was pushed and the remote branch returned that exact
SHA at `2026-09-05T16:35:11+08:00`. Receipt
`evals/results/phase-004c3/rc6_release_block_delivery.json` has SHA-256
`c99e87fbabd788939e84bb1564fed75ddedb40c5bf6a147458b33026826cd8c1`. The Draft PR remains open,
draft and unmerged.

Terminal-state verification passed 68 focused tests. The first full run retained one compatibility
failure because the new live blocker list no longer carried the literal historical RC5 reason code;
the state risk record was corrected to preserve `RC5_VERSION_FILE_MISMATCH` without changing any
frozen artifact or Skill file. The second full pytest passed `2009 passed / 1 skipped` in 307.33s.
The initial terminal `scripts/ci.sh` run passed Ruff, format and pytest
`2009 passed / 1 skipped` in 304.68s but then exited 1 because the legacy RC5 and 2019 checkers
compared current authorized RC6 successor files to historical bytes. Remote run `33955748397`
reproduced the same post-pytest failure. Those two non-Skill checkers were then time-qualified: RC5
Skill bytes are read at the recorded RC5 implementation commit, and 2019 freeze artifacts are read
at the recorded terminal-freeze commit. Both checkers returned zero errors, and final local
`scripts/ci.sh` exited 0 after pytest `2009 passed / 1 skipped` in 306.25s plus every historical and
strict check. This repair does not alter the frozen neutral test, formal Skill, frozen decisions or
`BLOCK` verdict. The separate release checker correctly returns exit 3 / `BLOCK`.

## Unknowns and limitations

- The RC6 candidate is not safe for formal use; the audit proves specific fail-open paths, not an
  exhaustive enumeration of all defects.
- Frozen neutral tests passing does not establish completeness.
- Exactly two cycles are recorded in the candidate/Plan, but intermediate executions are not each
  independently hash-bound as separate artifacts.
- Historical diagnostics do not retroactively validate 2019 or 2024.
- No claim can be made about 2018/2017 input suitability, modeling performance or completion because
  those inputs were intentionally never accessed.
- No broad C generalization, Held-out readiness, production readiness or 2026 solution is proven.
- Project license remains undecided; model-prior exposure and full OS-level answer isolation remain
  unverifiable.
- No new system package, Python/npm/cargo package, toolchain or configuration was installed or
  changed during Phase 004C3.

## Exact next step

`null`.

Further work requires explicit new authorization and a newly designed phase; this terminal phase
cannot silently reopen a third RC6 Skill revision cycle.
