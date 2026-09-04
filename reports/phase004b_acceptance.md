# Phase 004B Acceptance Report

## Decision

Provisional status: `FINAL_VERIFICATION_PENDING`. Scientific, execution, regression, Stress and
handoff evidence supports `DEVELOPMENT_EVAL_RC3_READY`; final acceptance is withheld until the
complete local and remote CI batch is observed. Validation has not started.

## Starting boundary

- Branch: `feat/phase004b-development-eval-2020a` from merged PR #7 at
  `1d842a45403370916ce2c36297876e9cd1ddde1f`.
- Starting Skill: `cumcm-modeling-evidence` `0.2.0-competition-rc2`, capability
  `COMPETITION_RC`, K1 Git tree `3601313b9cddbf4c524b0b439fc0152cb1e77e5a`.
- Baseline: `1808 passed, 1 skipped`; strict repository checks passed.
- Environment: system Python `3.12.3`, project Python `3.11.14`; existing numerical environment
  retained without installation or upgrade.
- Formal discoverable Skill count: one. Third-party integration: false.

## Official Development case and answer boundary

`CUMCM-2020-A-DEVELOPMENT-002` is a Development case on the mechanistic-modeling, numerical-solver
and constrained-optimization axis. The official page and RAR were obtained only from `mcm.edu.cn`.
The archive SHA-256 is `04ea454f8a1559dac2dc5b7cf599bceb10cd6a0b6f2df55a35ca4450814239dd`;
problem SHA-256 is `5c8023b4e2b3c4ca81790c58ba69d56f0f39afe6bc5598d4aa5c0d9be8d0d386`;
attachment SHA-256 is `fc42c478d1b37796de5157125d9ea9e33c75d29ba7d7af9885b340fd41ab1e7c`.
All raw material remains in ignored `.cache/official_inputs/CUMCM-2020-A/`.

Before first-run freeze, only the official page, archive, A problem and official attachment were
accessed. No solution, commentary, award paper, code or solution-oriented query was accessed.
After the remotely verified freeze, no safe reference body was found without solution-oriented
search, so the authorized reference list is empty and no content was copied. Model-prior exposure
remains `MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`.

## RC2 answer-sealed first run

The RC2 Skill remained unchanged. Requirements, sources, assumptions/symbols, data audit, model
portfolio, baseline and experiment plan all passed. Six preregistered Runs actually executed; all
failed and were retained. One failure could be sealed, while five nonzero exits with diagnostic
output had `failure=null` and were unsealable. Consequently stage 9 blocked with
`RC_RUN_SUCCESS_SET_INSUFFICIENT`; stages 10–14 were not started and no Final, Claim or handoff was
fabricated.

| Stage | Status | Gate / evidence | Failure |
| ---: | --- | --- | --- |
| 1 Problem intake | PASS | `GATE_PROBLEM_INTAKE`; requirements | none |
| 2 Requirement decomposition | PASS | `GATE_REQUIREMENT_COVERAGE`; trace | none |
| 3 Research/source planning | PASS | `GATE_SOURCE_PLAN`; plan/ledger/search log | none |
| 4 Assumptions/symbols | PASS | accepted model specification | none |
| 5 Data audit | PASS | `GATE_ASSUMPTIONS_AND_DATA`; immutable hashes | none |
| 6 Model portfolio | PASS | `GATE_MODEL_PORTFOLIO`; three candidates | none |
| 7 Baseline definition | PASS | baseline in portfolio/plan | none |
| 8 Experiment design | PASS | `GATE_EXPERIMENT_PLAN`; frozen inputs/code/seeds | none |
| 9 Implementation/execution | BLOCKED | six captures, one failed manifest | `RC_RUN_SUCCESS_SET_INSUFFICIENT` |
| 10 Model comparison | NOT_STARTED | blocked upstream | `BLOCKED_UPSTREAM` |
| 11 Robustness/sensitivity | NOT_STARTED | blocked upstream | `BLOCKED_UPSTREAM` |
| 12 Final Run | NOT_STARTED | blocked upstream | `BLOCKED_UPSTREAM` |
| 13 Claim validation | NOT_STARTED | blocked upstream | `BLOCKED_UPSTREAM` |
| 14 Modeling-to-paper | NOT_STARTED | blocked upstream | `BLOCKED_UPSTREAM` |

Captured first-run execution time is `16.960106` seconds; exact preparation-stage timings are
unknown. Manual intervention and recovery counts are both zero.

## First-run freeze and unlock

The first run was frozen answer-sealed at `2026-09-04T11:16:00Z`. Freeze SHA-256 is
`cadb774025ae30dc871fb67bdc4ffb8ffa409773be8e01247c8fea21bf8286ff`. The independent freeze
commit is `b742e8e042a1e9f0c161806c89c1b5917abe5693`; local and remote branch heads were equal before
unlock. Answer access changed to `UNLOCKED_AFTER_FIRST_RUN` only at `2026-09-04T11:19:44Z`.
Frozen files were not overwritten.

## Gap adjudication and RC3

Four gaps were classified. `GAP-004B-001` is the sole accepted
`GENERALIZABLE_SKILL_FAILURE`: nonzero execution with an existing diagnostic output lacked a
fallback failure record. `GAP-004B-002` concerns evaluation freeze infrastructure only.
`GAP-004B-003` (physical model failure) and `GAP-004B-004` (empty optimization pool) remain
case-owned. Reference evidence is empty because no reference body was accessed.

One of two permitted revision cycles was used. RC3 attaches
`RC_EXECUTION_NONZERO_EXIT` to an otherwise unclassified nonzero exit, retains the output, permits
faithful `FAILED` sealing and keeps that Run ineligible for comparison/Final. The formal Skill is
`0.2.0-competition-rc3`, commit `8a2a813ff34d8c2701c64ff9d959848e7b88c27c`, Git tree
`a4551c8aa0b6b119823f6ce9df3f0f948339bb33`. No 2020 A title, constants, fields, equations,
parameters or answer-derived branch entered the Skill.

## RC3 2020 A Development regression

The clean regression uses new code commit, Run IDs, manifests, outputs, Claim and handoff. Six of
six Runs exit zero and seal. The primary asymmetric first-order candidate is the only scientifically
eligible model; baseline and two-node control receive explicit infeasibility penalties. Decision
hash is `93c8f0f97e425d9a18d9589f42fa9097d2a51393fef9f99b78cba5915c4a0f68`.

Calibration train/held-out RMSE is `5.839182108`/`5.809725115` °C. Q2 maximum feasible speed is
`67.79449749` cm/min; Q3 area above 217 °C is `704.47625846` °C·s; Q4 symmetry RMSE is
`6.30290679` °C. A 0.5 s versus 0.125 s grid comparison has maximum absolute difference
`0.55413808` °C under the 0.75 °C threshold. Constraints are recomputed from generated curves.
There is no global-optimum proof, one parameter is bound-active, and one calibration board cannot
establish external validity.

Final state is `READY_FOR_PAPER_HANDOFF`. Six requirement Claims and figure-ready curve data pass
`modeling-to-paper/v1`; handoff SHA-256 is
`2f90b95a12c99c750ed3968e6f12e585c962f1225709de7da47e853dd7f1b55a`.

## Cross-case and Stress evidence

The 2023 C RC3 replay uses identical official input hashes and three actual case-local executions.
All exit zero and seal. RC2 output hashes, selected hierarchical model and decision hash are
identical; Claim/handoff passes. Mutated metadata propagates `STALE` through the plan and all
manifests. A pre-execution path mistake was rejected by `RC_CASE_EXECUTION_CODE_NOT_FROZEN` without
creating a Run, then corrected to the frozen case-relative path.

Stress A converts seconds/minutes and Celsius/Kelvin reversibly; Q2 and selection are invariant
within tolerance. Stress B shuffles coordinate-defined segments and splits one equivalent zone;
coordinate sorting restores the process and key results. Stress C removes seven noncritical points,
adds seeded 0.2 °C noise and rounds to 0.1 °C; held-out RMSE moves to `5.82804722` °C and parameters
are limited to four significant digits. Each variant has two successful sealed Runs, reaches
`READY_FOR_PAPER_HANDOFF`, passes handoff and produces an explicit `STALE` probe.

Cross-case-confirmed capabilities are executor/capture/seal, success-only selection, exact
Run/Claim/handoff binding and STALE propagation. Mechanistic identifiability, step-size and
optimization-boundary guidance remains mechanistic-case-only; tabular leakage and missing-data
handling remains data-case-only. No Validation or generalization proof is claimed.

## Environment and handoff boundary

The environment snapshot includes NumPy `2.4.6`, SciPy `1.17.1`, pandas `2.3.3`, openpyxl `3.1.5`,
scikit-learn `1.9.0` and statsmodels `0.15.0`. Dependency declaration files were unchanged because
the existing environment was sufficient; the absence of fully declared case runtime dependencies
is retained as a reproducibility limitation. Ignored local `libarchive-tools` was used only to
extract the official RAR; no binary or third-party script is tracked.

The Validation handoff freezes RC3 and requires a structurally different historical problem,
answer `SEALED`, one shot, result freeze before any Skill change, no same-case post-result tuning as
Validation, the same hard gates and offline execution. Validation status is
`READY_FOR_VALIDATION_INTAKE_NOT_STARTED`; next phase is
`PHASE-SKILL-VALIDATION-EVAL-004-C`.

## Verification and delivery

Starting baseline: `1808 passed, 1 skipped`. Final local and remote verification are pending and
must replace this paragraph before acceptance. The Draft PR remains open and must not be readied,
approved or merged by this task.

## Limitations

Model-prior exposure is unverifiable. No post-unlock reference body was assessed. Exact
preparation-stage timings and monetary cost are unknown. The selected optimizer has no global
certificate; parameter identifiability and external validity are limited. Development regression,
cross-case regression, synthetic E2E and Stress do not substitute for sealed Validation, full
ablation, production fitness or independent external evidence.

## Acceptance status

`FINAL_VERIFICATION_PENDING`. Exact next step after acceptance can only be
`PHASE-SKILL-VALIDATION-EVAL-004-C`; it was not executed here.
