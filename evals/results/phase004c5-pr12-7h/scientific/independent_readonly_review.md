# Independent read-only review

Review role: a separate read-only Python process and a separate source review
of the generated artifacts. The reviewer did not modify repository files, did
not call `evaluate-final`, did not read answer material, and did not rely on
the selected model's feasibility helper for the 2021 numerical recomputation.

## Evidence binding

- The post-iteration routes bind both cases to commit
  `385246bd5734df68d179543897d5cd5a0ebd63f7` and their registered official
  input hashes.
- Both evidence records state `DEVELOPMENT_NO_FINAL_EVALUATION`,
  `authorized=false`, `count=0`, and no final-evaluation ledger.
- The 2022 semantic bundle contains 3 `DESCRIPTIVE`, 6 `EMPIRICAL`, and 4
  `SIMULATION_CONDITIONAL` claims; the 2021 bundle contains 2 `DESCRIPTIVE`,
  10 `FEASIBILITY`, and 5 `SIMULATION_CONDITIONAL` claims. Neither route
  silently labels every requirement `DESCRIPTIVE` or claims `PREDICTIVE`.

## Scientific findings

1. The 2022 fixed-split zero is reproducible as a classification result, but
   the committed repeated grouped diagnostic has a nonzero Brier-loss upper
   tail (`0.0017828516`) even with 1.0 accuracy. The correct conclusion is
   stable observed class separation with unresolved probability calibration and
   external validity, not a Validation pass.
2. The independent 2021 parser reproduced the selected baseline validation
   score to `3.72e-10` and the forecast receipt to `3.47e-7 m3`. The plan passes
   the declared numerical tolerance, but its receipt is not exact equality.
3. The 2021 baseline wins the registered Development metric in the fixed and
   two rolling windows. The 399 supplier value is explicitly an upper-bound
   candidate pool; the emitted Q2 weekly plan uses 168 suppliers. No global
   economic-optimality claim is supported.

## Review disposition

The Development evidence repair and scientific caveat repair are accepted for
continued work. The formal Validation gate remains blocked by missing frozen
release identity and the required fresh isolated unfamiliar-case route. This
review does not authorize calling either historical case a blind test.
