# Competition RC1 End-to-End Evidence

## Prediction case

`SYNTH-RC1-PREDICTION-001` uses a project-original time regression dataset containing one missing
target, one outlier and a `future_target` leakage field. The executed pipeline reads the raw JSON,
derives a separate processed artifact with recorded Theil-Sen trend imputation/outlier lineage, and
binds both files in state and Run manifests. The audit rejects the future field; train, validation
and test are time-ordered. A train-mean baseline and least-squares trend actually run from the
processed artifact,
selection uses validation MAE, and test is accessed once after selection. `P-LINEAR-TREND` is selected
and obtains deterministic test MAE `0.0`. Two target perturbations and a structural-break limitation
are retained. The case reaches `READY_FOR_PAPER_HANDOFF`; evidence hash is
`ec744f61f5efac91c5017245921a5cfd427b45a6231dde1ed9225d10468fe791`.

## Optimization case

`SYNTH-RC1-OPTIMIZATION-002` maximizes `4*x_A+5*x_B` under two bounded integer resource constraints.
It reads those capacities, coefficients and profits from the bound raw problem JSON, then actually
runs an A-only baseline, complete integer enumeration and a deliberately infeasible
negative control. The infeasible attempt is retained with outcome `INFEASIBLE` and excluded from
ranking. Enumeration selects `(x_A,x_B)=(3,2)` with verified objective `22`; labor-capacity 7/9
perturbations are recorded. The case reaches `READY_FOR_PAPER_HANDOFF`; evidence hash is
`15fe6fc0c6d6de92c5cfdfcc38b997eb69ab3b6527ac961e792a59c3be563160`.

## Shared acceptance

Each case traverses 13 ordered transitions from `CREATED`, with a PASS Gate recorded at every edge.
Both handoffs contain all 23 required fields and validate against
`contracts/modeling_to_paper.schema.json`; formulas, symbols, tables, figure-ready series, Claims,
reproduction and limitations are non-empty. The combined result is
`evals/results/phase-003f-r1/end_to_end/result.json`, SHA-256
`3beefd5190547246a361e6829a2236224927af8a9673cc0344ff62f78676fa99`. Each case also mutates the
bound raw file after READY in its disposable workspace and independently receives
`RC_UPSTREAM_DEPENDENCY_STALE` with a nonempty dependency chain; a byte comparison proves the check
probe does not mutate state.

The fixed negative matrix covers 30 specified failure paths: 30 passed, 0 failed, 0 unhandled
exceptions, 0 sensitive values reported and no case reached READY. Its result SHA-256 is
`5c46849aee853b1bb1d9af43f7ea22d827681852e6a2150da6ad4bd0cd2f5f60`. The zero sensitive-value
count is computed by scanning serialized case records for both injected canaries; it is not a
hard-coded assertion.
