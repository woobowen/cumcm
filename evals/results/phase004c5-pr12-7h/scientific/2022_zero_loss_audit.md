# 2022 C Development: zero validation loss audit

This is a read-only scientific audit of the isolated Development workspaces,
with the final route receipt at
`CUMCM-2022-C-DEVELOPMENT-RC7-REGRESSION-ATTEMPT-011`. It does not access the
unknown-answer material or invoke the Final evaluator.

## Bound data and effective sample size

- The official workbook hash is the registered `ffb82a8e...a6b1063c` value.
- Form 1 contains 58 artifact records; Form 2 contains 69 sampling records.
- Two known records have totals below the official 85--105 validity interval
  (sample IDs 15 and 17), leaving 67 valid sampling records.
- After artifact-level median aggregation there are 56 effective artifact IDs:
  16 high-potassium and 40 lead-barium. The fixed Development validation split
  contains only 12 artifact IDs (4 high-potassium and 8 lead-barium); the test
  groups remain unaccessed.

## Reproduction

The registered candidates reproduce the current fixed split exactly:

| candidate | Brier loss | accuracy | validation groups |
| --- | ---: | ---: | ---: |
| `BASELINE_RAW_CENTROID` | 0.1216581282 | 0.75 | 12 |
| `CLR_RIDGE_WARD` | 0.0198854699 | 1.00 | 12 |
| `HELLINGER_KNN_COMPLETE` | 0.0000000000 | 1.00 | 12 |

The zero is produced by the distance-weighted KNN returning exactly 0 or 1
for all 12 validation groups. This is not evidence of test-label access: the
pipeline groups by artifact ID, excludes invalid artifacts, and records
`test_labels_accessed=false`. It is nevertheless an overconfident diagnostic
on a small fixed validation set, not a scientific or external-validation pass.

## Independent robustness diagnostic

The committed route now persists an artifact-level repeated stratified 4-fold
cross-validation diagnostic with 5 repeats and 280 held-out group predictions.
At the preregistered seed, the selected Hellinger KNN has accuracy
`1.0/1.0/1.0` (mean/min/max) and Brier loss
`0.0000891426/0/0.00178285` (mean/min/max). The nonzero upper tail is the
important correction to the fixed-split zero; the diagnostic is explicitly not
used for candidate selection. A separate seed sensitivity run gave zero Brier
loss for all folds, so the exact probability result is split-seed sensitive
even though the class accuracy remained perfect.

This narrows the diagnosis: the fixed-split zero is consistent with the
observed 56-artifact feature separation, but the probability loss varies under
group partitioning and no unknown-sample labels exist. The KNN probabilities
remain uncalibrated for external use. The result remains
`DEVELOPMENT_REGRESSION`, with no Validation claim.

## Route follow-up status

The repeated grouped diagnostic and the calibration/external-validity limitation
are now persisted in the case output and in the v3 Development receipt. The
route still does not convert this score into a predictive or Validation Claim.
