# Phase 004C4 fresh C one-shot Validation

## Registration and freeze

The preferred 2018 C archive was retrieved only after RC7 remote delivery. Its title was verified as
“大型百货商场会员画像描绘”, but the official C directory contained only the problem and a notice;
Attachments 1–5 named by the problem were absent. Preflight reason
`C_INPUT_ATTACHMENTS_UNAVAILABLE_FROM_OFFICIAL_ARCHIVE` activated the preregistered input-failure
fallback before any Run.

The selected case is `CUMCM-2017-C-VALIDATION-003F`, title “颜色与物质浓度辨识”. Its official problem,
`Data1.xls`, `Data2.xls` and readme hashes are registered without committing raw files. The answer
remained `SEALED/NOT_ACCESSED`; model-prior status is
`MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`. The pre-run freeze SHA-256 is
`9c078468da856353a7104e6eb4a6deec273f1aae81f6537deedbfc840703940b`, commit/remote SHA
`8cbc0c5702ba7c7d0ef536dd4b4eced7e6d5dcda`. Formal execution began only after the successor
delivery receipt was remotely verified.

## Fourteen-stage episode

| Stage | Status | Evidence/failure |
|---|---|---|
| 1 Problem intake | PASS | 3 primary requirements |
| 2 Requirement decomposition | PASS | explicit evidence/selection/output predicates |
| 3 Source planning | PASS | official attachments only; no external acquisition |
| 4 Assumptions/symbols | PASS | bounded, non-causal scope |
| 5 Data audit | PASS_WITH_LIMITATIONS | Data1 79 rows/5 substances; Data2 25 rows/7 levels |
| 6 Model portfolio | PASS | median baseline, ridge, RBF kernel ridge |
| 7 Baseline | PASS | `BASELINE_MEDIAN` |
| 8 Experiment design | PASS | grouped splits, 3 seeds, no row leakage |
| 9 Execution | PASS_9_OF_9 | all first invocations exit 0; no retries |
| 10 Comparison | PASS_DEVELOPMENT_SELECTION | per-requirement selection |
| 11 Robustness | PASS_DEVELOPMENT_SCOPE | sample-size/features, uncertainty and failure cases |
| 12 Final Run | BLOCK | RC7 finalization interface cannot receive authorized test payload |
| 13 Claim evidence | semantic Gate PASS; final not accepted | finalization short-circuit |
| 14 Paper handoff | NOT_REACHED_BLOCK | Gate 10 not invoked; template remains unapproved |

The formal clock was `2026-09-05T22:27:46+08:00` to terminal freeze
`2026-09-05T22:37:38+08:00`, 592 seconds against a 14,400-second maximum.

## Models, Runs and selection

Each candidate ran seeds 17001, 17017 and 17033. All nine capture, output, manifest and independent
check bindings are recorded in the terminal freeze; all manifests and independent checks pass.

| Requirement | Selected model/Run | Development metric | Evidence |
|---|---|---|---|
| REQ1 relationship/data quality | Ridge / `RUN-RIDGE_LINEAR-17001` | grouped macro NMAE 0.281780084091 | provided empirical Data1 |
| REQ2 concentration prediction | RBF kernel ridge / `RUN-KERNEL_RBF_RIDGE-17001` | grouped MAE 30.0363373862 ppm | provided empirical Data2 |
| REQ3 size/dimension sensitivity | same RBF kernel Run | inherits REQ2; half-sample and all-subset ablations | provided empirical Data2 |

Baseline Req2 MAE is 80.0 ppm; ridge is 31.0760616748 ppm. REQ1 candidate values are baseline
0.438608779843, kernel 0.367234134016 and ridge 0.281780084091. These are frozen development grouped
out-of-concentration results, not final-test credit.

## Terminal controller outcome

The controller was invoked once. Gates 1–8 passed; `GATE_FINALIZATION` blocked with
`RC_GATE_EXECUTION_FAILED`; handoff was not reached. The selected outputs truthfully record
test-access count zero and omit `sealed_test_metrics_b64`. RC7 `execute` has no final-phase,
authorization or sealed-test input, while the frozen ledger allows exactly nine selection attempts.
Adding a result-derived tenth Run or mutating an output would violate HF10/HF11/HF13/HF15.

No recovery, rerun, tuning, case-code change or Skill change occurred. The answer and 2025 C remain
sealed. HF14, HF21 and HF23 make the outcome `C_TARGET_VALIDATION_FAILED`; paper dispatch is false
and the same case is Development-only after freeze.

## Independent integrity challenge

The required identity-separated read-only auditor preserved the failed verdict but returned
`CHALLENGE`. It found `HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION`: the REQ2 semantic artifact declared
`held_out_test_valid=true`, while the selected Run output binds the evaluation boundary to
`DEVELOPMENT_GROUPED_OOS`, test access to `NOT_AUTHORIZED/0`, and
`held_out_test_valid=false`. The frozen post-selection builder created the positive predicate
unconditionally, and the semantic validator did not cross-bind it to those authoritative output
facts. This is an additional hard failure, not a reason to modify the terminal decision or rerun
the case. It is routed to 004C5.
