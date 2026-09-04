# Phase 004A RC2 Development Regression

This is `DEVELOPMENT_REGRESSION` after reference unlock, not blind, Validation, Held-out or a
generalization proof. Code commit is `21bcf1bf4659cad6880d5a73973d0c1f8f8f1642`; seed is
`20260904`.

| Candidate | Exit | Validation score (baseline-normalized, lower better) | Capture SHA prefix | Elapsed |
|---|---:|---:|---|---:|
| PIPELINE-SEASONAL-BASELINE | 0 | 1.00000000 | `e72c25a7` | 33.692685 s |
| PIPELINE-HIERARCHICAL-STOCHASTIC | 0 | 0.95115654 | `e829510f` | 33.130758 s |
| PIPELINE-NONPARAMETRIC-ROBUST | 0 | 1.13927070 | `09cf5321` | 32.524204 s |

Selection hash `39c62b36…` chooses `PIPELINE-HIERARCHICAL-STOCHASTIC`. The terminal state is
`READY_FOR_PAPER_HANDOFF`; final WAPE is `0.31407446`, seven-day forecast total `3076.35706056 kg`,
and the feasible item plan has 27 items. Profit is explicitly a proxy (`5230.45542049 yuan`), not a
realized or globally optimal profit claim.

All six requirements have exact output evidence. Three robustness values were recomputed from bound
inputs: shorter training window `0.88074853`, demand-scale perturbation `0.98239919`, and validation
tail removal `0.94844323`. Stockout censoring, endogenous price, absent shelf/inventory constraints
and unavailable future outcomes remain limitations. Total captured execution time was `99.347647 s`;
manual intervention count for result editing was zero. Exact token use is `UNKNOWN`.
