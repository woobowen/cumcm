# Phase 004B — Cross-Case Generalization Analysis

## Evidence contrast

2023 C uses large tabular sales/cost/loss data, time-ordered prediction and replenishment/pricing
decisions, statistical/seasonal pipelines, WAPE-style validation, missing-data perturbations and
table-oriented handoff. 2020 A uses process coordinates and calibration observations, thermal ODE
approximations, bounded parameter identification and constrained search, residual/feasibility and
time-step checks, plus curve/parameter/constraint-oriented handoff.

| Axis | 2023 C | 2020 A |
| --- | --- | --- |
| data | large relational workbooks | process geometry and one temperature trace |
| task | forecasting and operational decision | physical process simulation and constrained optimization |
| model | weekday/seasonal/robust statistical pipelines | first-order/asymmetric/two-node thermal systems |
| executor | dataframe pipeline | numerical solver and bounded optimizer |
| validation | chronological split | calibration holdout, residuals, constraints, grid refinement |
| robustness | ordering, unit/date shift, missing loss source | units/time, equivalent segments, degraded calibration |
| handoff | forecasts and decision tables | equations, parameters, curves, extrema, areas and feasible settings |

## Classification

- `CROSS_CASE_CONFIRMED`: Git-blob-bound case-local execution, immutable capture, separate sealing,
  success-only model selection, exact Claim/handoff binding and dependency-driven STALE behavior
  operated on both the tabular pipeline and numerical-solver code.
- `MECHANISTIC_CASE_ONLY`: parameter-bound identifiability warnings, step-size evidence, process
  constraint residuals and local/global optimization boundary were demonstrated only on 2020 A.
- `DATA_CASE_ONLY`: time-split leakage control, relational-key audit, missing-loss degradation and
  category/item decision-table production were demonstrated only on 2023 C.
- `UNVERIFIED_GENERALIZATION`: RC3's deterministic fallback for nonzero exits with pre-existing
  diagnostic output is directly tested generically and derived from the 2020 A failure, but has not
  passed a sealed Validation case. External validity, production fitness, full ablation and monetary
  cost remain unverified.

The current boundary is two answer-unlocked Development regressions plus project-original synthetic
and Stress evidence. This supports a frozen Validation candidate, not a claim that the Skill has
passed Validation or proven generalization.
