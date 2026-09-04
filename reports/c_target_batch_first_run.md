# C-Target Batch First-Run Report

## Frozen protocol

`C-TARGET-BATCH-001` bound three independent Development cases to formal Skill
`0.2.0-competition-rc3`, tree `a4551c8aa0b6b119823f6ce9df3f0f948339bb33`, before any
candidate result. Raw official inputs stayed ignored and immutable. At most two case workers ran in
parallel; every candidate/seed attempt was executed once, captured and sealed. Failed Runs were
retained. Answers and reference papers stayed sealed until all current first-run freezes were pushed
and the unified unlock was remotely delivered.

| Case | Runs | Successful | Passed stages | Terminal state | Manual | Recovery |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| 2022 C | 9 | 9 | 10/14 | `REJECTED` at robustness Gate | 0 | 0 |
| 2021 C | 6 | 4 | 9/14, with retained Run failures | `RUN_VALIDATED` | 0 | 3 |
| 2020 C | 6 | 6 | 14/14 | `READY_FOR_PAPER_HANDOFF` | 0 | 9 |

## 2022 C

The answer-sealed run compared a raw-centroid baseline, a composition-aware transformed linear/
hierarchical candidate and a distance-based composition candidate across three seeds. All nine Runs
were successful. The selected validation loss was `0.0` versus baseline `0.1216581282`; this result
was not promoted. Although the output contained nested quantitative perturbation results, it omitted
the generic top-level robustness, final-metric, Claim, figure-ready and uncertainty contracts. Stage
11 therefore failed hard; Final, Claim and handoff remained dependency-locked. Requirement and
main-question coverage were 13/13 and 4/4 only at design/output-key scope, not accepted Claim scope.

## 2021 C

The frozen matrix contained three candidates and two seeds. Four robust/scenario Runs succeeded and
passed 12/12 independent per-question feasibility checks. Both baseline Runs failed with
`BASELINE_MINIMUM_SUPPLIER_INFEASIBLE` and were retained without retry. The best successful-set
validation metric was `2.435657334`, but no baseline comparison could be computed. Comparison also
recorded zero authorized post-selection test accesses. The strict Gate correctly blocked on
`RC_COMPARISON_BASELINE_SUCCESS_MISSING` and `RC_COMPARISON_UNAUTHORIZED_TEST_ACCESS`; robustness,
Final, Claim and handoff were not run.

## 2020 C

All six baseline/linear/nonlinear candidate Runs succeeded. The selected candidate's mean validation
composite loss was `0.10603194565`, 30.5462% below the baseline's `0.152665348`. The test partition
was accessed once only after selection and was not used for selection; its Brier loss was
`0.073657245`, AUC `0.9035087719`, and composite loss `0.097780052`. Independent feasibility,
three robustness perturbations, six requirement-bound Claims and the paper handoff passed. All 14
stages reached `READY_FOR_PAPER_HANDOFF`.

## Freeze and chronology

The original freezes are immutable. Versioned v2 files correct two full-version metadata fields and
one post-freeze summary-hash/timing binding while preserving all original files and links. Current
freeze SHA-256 values are `5de34dec...` (2022), `a747da76...` (2021) and `a5016b63...` (2020).
Unified unlock occurred at `2026-09-05T00:59:00+08:00`, only after exact local/remote freeze and RC3
tree verification. The unlock receipt SHA-256 is
`d6a9aa50ce294fc82f2c195d76fa0a5aa745b681544f3455f2991821d100d69a`.

These are Development first runs. They do not establish Validation, held-out generalization,
external validity or production readiness.
