# Phase 004B — 2020 A Development Regression

## Scope

This is an answer-unlocked `DEVELOPMENT_REGRESSION`, never Blind, Validation or Held-out. No
reference body was accessed after unlock, so no reference method, formula, parameter or code was
copied; model-prior exposure nevertheless remains unverifiable.

An initial RC3 regression attempt reached six successful captures and seals but its case-owned
output omitted fields required by downstream Final/Claim/handoff contracts. That attempt remains in
ignored private evidence and is excluded. The clean `V2` workspace used new Run IDs, manifests,
outputs, Claim and handoff and completed every state transition through
`READY_FOR_PAPER_HANDOFF`.

## Runs and selection

| Candidate | Seeds | Successful / attempted | Selection score | Disposition |
| --- | ---: | ---: | ---: | --- |
| `BASELINE_FIRST_ORDER` | 20260904, 20260905 | 2 / 2 | 1000027.86739940 | infeasibility penalty; not selected |
| `PRIMARY_ASYMMETRIC_FIRST_ORDER` | 20260904, 20260905 | 2 / 2 | 5.80972512 | selected |
| `CONTROL_TWO_NODE` | 20260904, 20260905 | 2 / 2 | 1000020.70603219 | infeasibility penalty; not selected |

The deterministic decision hash is
`93c8f0f97e425d9a18d9589f42fa9097d2a51393fef9f99b78cba5915c4a0f68`. All six exits are zero;
all captures, outputs and manifests have distinct recorded hashes. No failed, infeasible,
unsealed, stale or nonconverged Run supports the Final.

## Scientific and numerical result

The case-owned code represents piecewise spatial zones and gaps, maps speed from cm/min to cm/s,
uses an asymmetric one-state thermal balance as primary model, exact exponential state stepping,
bounded nonlinear least squares, seeded bounded direct search and coordinate refinement. The
selected calibration has train RMSE `5.839182108` °C and held-out RMSE `5.809725115` °C. Its
parameters are `[52.50000000000021, 171.0458515027588]`; one is at its lower bound, so structural
identifiability is limited.

The selected Final reports maximum feasible Q2 speed `67.79449749` cm/min, Q3 area above 217 °C
`704.47625846` °C·s, Q4 symmetry RMSE `6.30290679` °C, explicit curve data, process metrics and
constraint residuals. A 0.5 s versus 0.125 s recomputation gives maximum absolute curve difference
`0.55413808` °C and RMSE `0.15914949` °C, below the preregistered 0.75 °C threshold.

The optimization is a feasible seeded bounded search, not a global-optimum certificate. One board
does not establish external validity. Heating-parameter bound activity, local-optimum risk and
unknown out-of-sample process behavior remain limitations.

The final handoff passes `modeling-to-paper/v1`, has SHA-256
`2f90b95a12c99c750ed3968e6f12e585c962f1225709de7da47e853dd7f1b55a` and binds six requirement
Claims. Aggregate machine evidence is
`evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002/rc3/development_regression_evidence.json`.
