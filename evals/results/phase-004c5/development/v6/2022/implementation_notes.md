# 2022 C Development v6 implementation notes

This is bounded case-owned implementation, not an independent agent audit or formal acceptance.
The worker owns only this directory's code and this note. The main agent owns source registration,
assumption bytes, case intake/semantics, captured Runs, repository validation, acceptance and Git.
No 2021, shared Skill, state, registry or Git files were changed during this task.

## Input provenance and access

Before raw workbook parsing, the 2022 `CaseConfig` in
`scripts/run_c_target_rc7_development_regressions.py` verified:

| Artifact | SHA-256 |
| --- | --- |
| Official archive | `c27eb1b665f070341e134f5dc13bb2af469230424ff2eedabf594eee708bfee4` |
| Official C PDF | `573ee0f2865af13f8b2fbd12dab7f8efa68cf61ec6b8edf132a2120424480dbd` |
| Official workbook | `ffb82a8e209a005f26883e115de3ddea42ab6e0a34986d312a52a3cea6b1063c` |
| Inner C archive | `cda2851e819c4b95a32209240ad047badb0479d91bae904bcfb3c42c1f4ef5c6` |

No original bytes are modified.
Both new entrypoints independently hash the workbook before parsing. A read-only raw schema check
of the new producer, independent parser and derived v5 control agreed on 58 metadata artifacts,
69 known sampling rows, 67 valid known rows, 56 valid artifact groups and 8 unknown samples.
That schema check did not fit any official model. No official full model, Validation/Final
experiment, answer lookup, new-year input or benchmark vault access occurred in this worker task.

The original v5 producer remains byte-for-byte unchanged at
`evals/results/phase004c5-pr12-7h/development-v5/code/CUMCM-2022-C-DEVELOPMENT-BATCH-001/model_pipeline.py`,
SHA-256 `f7c45d65c803f1c18db9f818d960acdb2fe15d39fcb016df6a32fe6385555f4a`.

## Bounded scientific changes

The three historical candidate IDs retain their raw-centroid, CLR/logistic and Hellinger/KNN
classifier families. No large new model or numerical dependency is introduced. All following
budgets are code constants frozen before the main agent's official captures:

| Computation | Bound and scope |
| --- | --- |
| Fixed classification split | Existing deterministic artifact split; train fit, validation scoring |
| Repeated CV | Up to 4 folds × 2 repeats, effective train-plus-validation artifacts only |
| Sparse-table permutations | 999 seeded weather-label shuffles per eligible table |
| Subtype stability | 20 artifact bootstrap resamples per type, fixed selected k/features |
| Known composition sensitivity | 2 seeded perturbations with additive 0.01 simplex-unit noise |
| Unknown sensitivity | 50 seeded perturbations per unknown sample |
| Association differences | 30 artifact bootstrap replicates per type comparison |

V5's 56-group × 5-repeat CV includes the 12 old internal test groups, so 280 predictions are
56 artifacts evaluated repeatedly, not 280 independent units. New CV uses only the effective
train-plus-validation groups (44 expected from the frozen official split) and counts actual
memberships. Each effective artifact receives two evaluation predictions. Fold fit/evaluation IDs
are emitted and independently checked for overlap, partition coverage and internal-test exclusion.
The whole case is already contaminated Development: old internal test labels remain exposed. It
is not restored to blind status. All-known descriptive/subtype analyses may use the old groups as
Development data. `test_accessed=false` at the new output root refers to the formal Final evaluator;
explicit internal-label contamination fields preserve the separate historical access fact.

Q1 now performs actual 999-shuffle permutation calculations for weathering versus glass type,
pattern and recorded color. It reports table counts, missing exclusions, chi-square diagnostics,
Cramer's V, sparse expected cells, permutation exceedances, seed and the plus-one p-value.
Degenerate tables retain insufficient/undefined output rather than fabricated significance.
These are exploratory associations without causal or multiplicity-adjusted claims.

Q1 composition centers average sampling-point CLR vectors within each artifact first, then give
each artifact equal weight within type/weathering strata. Paired artifact IDs/counts are reported.
Backcasts produce one weathered-artifact vector under a declared type exchangeability model.
The baseline uses its type's unweathered center; the other candidates undo the estimated CLR
shift. Two paired artifacts cannot identify causal weathering or validate original compositions.
Backcasts remain conditional simulation, never observed truth or causal estimation.

Q2 exploratory subtypes retain a bounded k=2..4 internal-silhouette rule, then report actual artifact
assignments/counts and equal-artifact chemical centers for every cluster. Internal silhouette is
explicitly geometric rather than scientific validation. Twenty bootstrap resamples retain fixed
k/features, emit sampled artifact IDs, pair observation/same-cluster counts, co-membership fractions
and label-invariant ARI diagnostics. Failed resamples remain explicit. The independent checker
recomputes sampling exposure counts and ratio consistency; it does not independently refit all
clustering models.

The old zero-fraction perturbation was an identity for Hellinger. New sensitivity changes the
actual composition: independent Gaussian noise with standard deviation one percentage point is
added to closed proportions, negative values are floored and the vector is closed again. Both
transformed matrices are genuinely different. The output contains the seed, perturbed compositions,
actual transformed-matrix Frobenius norm, validation diagnostic and subtype ARIs. This protocol is
not a relative 1% multiplicative measurement-error model; that distinction is explicit in names.

Q3 delivers all eight predictions with an uncalibrated decision score or neighbor vote, never a
calibrated probability. For each prediction it reports nearest predicted-class training distance,
the 95th percentile of within-class leave-one-artifact-out nearest distances, and whether the
sample lies inside that training-distance domain. Fifty actual composition perturbations report
feature-change norms, raw decision scores, flip counts/rates and exploratory score ranges.
Training-distance applicability and perturbation stability do not establish accuracy on unlabeled
unknown samples. REQ-3A remains generation method `PREDICTION` with `INSUFFICIENT` status; it is never
renamed descriptive to bypass a Final-evaluation requirement.

Q4 computes artifact-equal CLR associations, preserving undefined correlations as JSON null.
Thirty whole-artifact bootstrap draws produce exploratory differences and percentile ranges for
all 91 component pairs. Counts of finite bootstrap values remain explicit. Constant/undefined
correlation is not replaced by zero. The ranges do not promise nominal coverage, multiplicity
control, chemical causality or external validity.

## Runtime contract

Producer:

```text
.venv/bin/python models/model_pipeline.py --case-root CASE --candidate-id CANDIDATE --seed SEED --output runs/RUN/output.json
```

Independent checker:

```text
.venv/bin/python models/scientific_checks.py --case-root CASE --run-id RUN --output runs/RUN/scientific_check.json
```

The checker reads `CASE/runs/RUN/output.json`, writes the requested result, and supports optional
`--model-output` for the legacy control. Root results bind run ID, output hash, checker hash,
registered workbook hash and actual `models/assumptions_and_symbols.json` hash. Every requirement
has numeric residuals in the agreed value/limit/relation/tolerance format, a feasibility result and
actual matching metric IDs. A successful checker process may report scientific failures.

The producer requires the assumption artifact before solving. Main-agent assumption registration
should cover nondetection replacement, deterministic artifact splits, historical internal-test
contamination, equal-artifact aggregation, conditional backcast exchangeability, exploratory
subtyping, one-percentage-point perturbations, uncalibrated scores and bounded bootstrap budgets.

`scientific_evidence` uses the agreed `SRC-2022-GLASS-WORKBOOK`, source fields
`artifact_id/glass_type/pattern/color/weathering/composition_14`, undated collection scope and
known/unknown entity identifiers. Metrics use globally unique `DATA.*`, `Q1.*`, `Q2.*`, `Q3.*`,
`Q4.*` IDs and the same actual values in `final_metrics`. Requirements retain exactly the three
Claim fields. Q1 backcasts are conditional; Q2 CV is Development diagnostic; Q3 unknown predictions
remain predictive and insufficient; Q4 is descriptive. The main source ledger must preserve that
unknown samples lack observed glass-type labels even though the same workbook has known labels.
`PARTIAL_SCIENTIFIC_COVERAGE` and `whole_problem_scientifically_complete=false` remain explicit.

The independent checker does **not** import the producer or a shared case helper. It independently
recomputes workbook validity/counts, closure, permutation tests, artifact-equal centers/backcasts,
CV group membership, subtype chemical centers, actual perturbation compositions/transforms,
bootstrap exposure arithmetic, training distances and all association/bootstrap matrices/ranges.
Classifier scores and clustering assignments receive consistency checks, not an independently
repeated model fit. Flip rates are reconstructed from recorded model scores while raw perturbation
feature changes are independently reproduced. These limits are machine-readable and documented;
Python-process separation is not represented as an independent agent audit.

## Primary method sources consulted

Only the following generic official documentation was opened, on 2026-09-08 UTC; no problem-answer
or case-method search was performed:

- [SciPy permutation_test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html):
  informed finite randomized permutations, fixed seeded generators and the numerator/denominator
  plus-one adjustment. This directly replaced unsupported reliance on sparse-table asymptotic
  p-values in the Q1 interpretation.
- [SciPy spearmanr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html):
  confirms undefined constant-input correlation and motivates preserving null entries rather than
  writing false zero correlations. Small-sample inference remains bounded and exploratory.

The pages displayed SciPy 1.18.0; execution uses the existing local SciPy 1.17.1, NumPy 2.4.6,
openpyxl 3.1.5 and scikit-learn 1.9.0. No package, toolchain or configuration was installed or changed.
The main agent owns formal source-ledger registration.

## Executed validation and remaining official work

- Seven synthetic tests pass. One test executes all three actual producer families on synthetic
  artifacts, serializes outputs, invokes the current shared core's
  `validate_selected_output_contract` and then the standalone independent checker. All three
  output contracts pass; every emitted scientific metric matches independent per-requirement
  values, while REQ-3A and REQ-EVIDENCE correctly remain negative.
- Other tests cover historical-test exclusion, true Hellinger feature perturbation, artifact-equal
  weighting despite duplicate sampling points, bounded nonzero permutation p-values, undefined
  correlations and rejection of a bad raw hash before workbook parsing.
- Actual official **schema-only** loading passed through all three readers, as described above.
- Ruff formatting/checks, checker CLI help and scoped `git diff --check` passed.

No official full model has been fitted in this worker task. The main agent must freeze the code,
capture the three authorized candidates and one separately budgeted control, run the independent
checks, preserve every failed/insufficient requirement and make its own formal acceptance decision.
No scientific release, all-question completion, Validation improvement or remote delivery is claimed.

## Derived v5 control exact diff

`code/model_v5_control.py` retains all old numerical algorithms and budgets, including 56-group
5-repeat CV and the old Hellinger identity sensitivity. Only its false internal-label access flags
and corresponding docstring are corrected. The raw loader passed unchanged; no parser workaround
was required. This is an old-algorithm control with truthful metadata, not a byte-identical v5 replay.

Control SHA-256: `18c1dcf4fd48948f05879c2078d7cb306ec72225745fd5b64ba8fe8d70502f0a`.

```diff
--- evals/results/phase004c5-pr12-7h/development-v5/code/CUMCM-2022-C-DEVELOPMENT-BATCH-001/model_pipeline.py
+++ evals/results/phase-004c5/development/v6/2022/code/model_v5_control.py
@@ -622,7 +622,8 @@
         ),
         "validation_brier_loss": loss,
         "validation_accuracy_diagnostic": accuracy,
-        "test_labels_accessed": False,
+        "test_labels_accessed": True,
+        "access_scope": "DEVELOPMENT_ALREADY_EXPOSED_INTERNAL_KNOWN_TEST_LABELS",
     }
 
 
@@ -635,8 +636,8 @@
 ) -> dict[str, Any]:
     """Measure artifact-level stability without changing the preregistered winner.
 
-    This is a Development diagnostic only.  It deliberately never touches the
-    unknown/test groups and is not a substitute for the formal Final evaluator.
+    This historical algorithm includes the old internal known test groups.
+    It is contaminated Development evidence, never a sealed Final evaluation.
     """
 
     ids, matrix, labels = artifact_level_dataset(metadata, known, candidate_id, fraction)
@@ -670,7 +671,8 @@
             "maximum": finite_float(np.max(accuracies)),
         },
         "selection_role": "DIAGNOSTIC_ONLY_NOT_USED_FOR_CANDIDATE_SELECTION",
-        "test_labels_accessed": False,
+        "test_labels_accessed": True,
+        "access_scope": "DEVELOPMENT_ALREADY_EXPOSED_INTERNAL_KNOWN_TEST_LABELS",
         "external_validity_status": "UNESTABLISHED",
     }
 
```
