# 2021 C Development v6 scientific implementation notes

Scope: case-owned implementation only. Main agent owns real captured Runs, source registration,
formal scientific acceptance, repository validation, state and Git. No acceptance verdict is made
here. All original v5/first-run files remain unchanged.

## Provenance and input boundary

Before any workbook cells were requested, all four entries below were verified against the actual
`CaseConfig` in `scripts/run_c_target_rc7_development_regressions.py`:

| Official artifact | SHA-256 |
| --- | --- |
| 2021 archive | `3391573f546fce4511e9a99c24c386e28203d8fee3d29bb2dccada5921cefe7b` |
| C problem PDF | `4a592c20adad12d4f0678a783bfb47995bda03b1c7484adf254d96327f534056` |
| Supplier workbook | `1b93a7598b8f0489e3c054439967bca654a83654837908c833752617cf950e1b` |
| Carrier workbook | `29e1499b133aa88d765902081bfb827f78ffb4c091f5f75341fc37d844344685` |

The PDF was read using the already installed `pdftotext`. It establishes payment for all actual
supply, 6000 m3/carrier/week, a preferred rather than absolute single-carrier assignment, approximate
two-production-week inventory, Q2 sequential economics and losses, Q3 A/C preference and Q4 capacity.
The numerical parsers request only W001–W216. The first 168 weeks fit parameters; W169–W216 support
two chronological Development stress blocks. W217–W240 is never requested as numerical data.
Workbook byte hashing covers the registered original file; no original cells or files are changed.
No answers, new-year cases or benchmark vault were accessed by this worker.

Historical producer copied before repair:
`evals/results/phase004c5-pr12-7h/development-v5/code/CUMCM-2021-C-DEVELOPMENT-BATCH-002/c2021_supply_plan.py`
SHA-256 `1eeb338db3529d8d50f10269b0e089511505155d1e306516c159c720d9756cb8`.
Historical helper copied before repair:
`evals/results/phase-004c-c-batch/CUMCM-2021-C-DEVELOPMENT-BATCH-002/code/c2021_feasibility.py`
SHA-256 `f64bcb3942e10bbe804ae979e85f4f7d26ce8315eef650e0d9bedb397e606ef6`.

## Model and objective repairs

Every old candidate ID retains its training parameter estimator. All three now use the same
corrected scientific objective hierarchy; this is an algorithm revision, not an unchanged baseline.
A separately captured legacy baseline is needed for an actual old-method comparison.

Let x_ij be actual raw supply dispatched from supplier i through carrier j, y_i a binary supplier
indicator, c_i estimated actual supply capacity, r_i fulfillment ratio and a_i consumption per unit
product. Order q_i = sum_j x_ij/r_i. Payment is sum_ij p_i*x_ij, never p_i*q_i or p_i*x_ij/r_i.
All modeled supply must be purchased and dispatched. Carrier limits are sum_i x_ij <= 6000.
Product receipt is sum_ij x_ij*(1-loss_j)/a_i.

Q2 solves three sequential MILPs over the same full supplier pool: minimize sum_i y_i subject to
sum_j x_ij <= c_i*y_i and demand; fix this count as an upper bound; minimize all-supply purchase
cost; fix its optimum within the recorded numerical tolerance; minimize raw transport loss. The
supplier identities remain variables after the cardinality stage. No arbitrary first-stage supplier
set is frozen before minimizing economics. Every stage retains status, incumbent, dual bound, gap,
node count, frozen bound and tolerance. A time-limited incumbent is preserved, but later hierarchy
stages do not run after an unproved predecessor. Missing incumbents remain missing, not zero scores.
The stage cap is 100 seconds; Q2 has at most three stages per captured attempt.

Q3 has a separately declared interpretation: minimize C volume, maximize A volume, minimize
all-supply purchase cost, then minimize transport loss, at exactly the target product receipt. The
priority is an assumption because the problem does not uniquely specify competing A/C priorities.
Material A/B/C volumes, purchase cost and transport loss are emitted.

Q4 maximizes conditional stationary receipt, then minimizes purchase and loss at the frozen
capacity bound. Its 24-week plan uses that increased receipt as demand, with two increased-demand
weeks of initial inventory and inventory floor. This does not establish actual future deliverability
or identify whether the enterprise currently owns the additional initial inventory.

Q1 retains the four-factor min-max weights (0.45/0.25/0.15/0.15) and adds eight bounded one-factor
±20% weight perturbations with re-normalization and top-50 overlap/Jaccard measurements. Its ranking
is a conditional weighted model rather than an empirical causal importance claim.

## Independent checking and historical stress

`code/c2021_feasibility.py` is now explicitly a **producer-side diagnostic**. It is never described
as an independent acceptance check. Its purchase arithmetic is corrected.

`code/c2021_independent_check.py` imports neither the producer nor either feasibility helper. It
hashes official workbooks, parses their first 216 numerical weeks, independently reconstructs
training estimates, checks raw-to-emitted parameters and replays every emitted plan. Residuals cover
all-supply routing, order/supply bounds, carrier capacity, target production, initial stock,
inventory floor, 24-week inventory, emitted cost and losses. Q1 ranking/weight sensitivity and all
six actual CSV tables are independently recomputed as well.

For cardinality, the checker independently sorts c_i*(1-min_j loss_j)/a_i. Ignoring individual
carrier limits gives a valid optimistic capacity upper bound for any k suppliers and thus a lower
bound on needed supplier count. A feasible actual count matching that lower bound is a conditional
minimum certificate. A lower bound alone never certifies feasibility. The checker emits
`optimality_certificate` with `INDEPENDENT_BOUND`, lower/upper/objective/tolerance and the registered
scenario scope. Unequal bounds preserve `NOT_ESTABLISHED`; a solver-reported zero gap cannot replace
this independent certificate. Q4 and the full cost/loss hierarchy currently lack independently
checked dual certificates; their solver claims and independently checked feasibility remain distinct.

All Q2/Q3/Q4 plans receive W169–W192 and W193–W216 stress replays. Each starts with two target weeks
of stock and evolves inventory without clipping negative stock or discarding surplus. Historical
supply/order ratios are not upper-clipped: all simulated actual supply is paid and routed with the
fixed plan shares. When a historical order is zero, the registered fitted ratio is used and the
fallback count is reported. Zero observed carrier losses mean no transportation and use the fitted
carrier loss. Capacity overload, inventory floor violations and exhausted inventory remain explicit.
These are conditional counterfactual Development stress tests, not actual future performance,
independent Validation, Final evaluation or proof of stochastic feasibility.

The retained comparison metric name `validation_penalized_cost_per_effective_m3` now means:
mean(all realized supply purchase cost / demand) + 100*mean(two-week inventory floor shortfall /
two-week demand) + 100*mean(total carrier capacity excess / total carrier capacity).
Direct numeric comparison with v5's old metric is invalid. The checker can recompute the legacy
plan under this same formula using `--model-output` and the current registered raw inputs.

## Runtime interface and source proposal

Producer CLI:

```text
.venv/bin/python models/c2021_supply_plan.py --case-root CASE --candidate-id CANDIDATE --seed SEED --output runs/RUN/output.json
```

Independent checker CLI:

```text
.venv/bin/python models/c2021_independent_check.py --case-root CASE --run-id RUN --output runs/RUN/scientific_check.json
```

It reads `CASE/runs/RUN/output.json`, writes the requested check result and prints a bounded summary.
Optional `--model-output` selects another existing model-output file for the legacy comparison.
Checking may exit zero while its scientific findings contain infeasibility; process success and
scientific acceptance are separate.

`models/assumptions_and_symbols.json` must exist before solving; its actual byte hash binds every
scientific fact. Proposed official source IDs agreed with the main agent are
`SRC-2021-SUPPLIER-WORKBOOK` (`supplier_id`, `material_type`, `order_m3`, `supply_m3`, `SUPPLIERS_402`)
and `SRC-2021-CARRIER-WORKBOOK` (`carrier_id`, `loss_rate_pct`, `CARRIERS_8`). Availability scope uses
`W001-W168`, `W169-W216`; future conditional scope uses `FUTURE_24_WEEKS` and
`REGISTERED_CAPACITY_SCENARIO`. Main agent owns registration and artifact bytes.

Facts use globally unique `Q1.*`, `Q2.*`, `Q3.*`, `Q4.*`, `ATTACHMENTS.*` metrics, also published in
`output.final_metrics`. The independent checker emits matching numerical IDs per requirement.
`requirement_claims` preserves exactly `claim_id`, `claim_text`, `evidence_artifact_ids`.
Actual CSVs contain all suppliers and all 24 weeks, plus all supplier/carrier/week allocations.
The missing official A/B template files prevent exact named-template submission; both attachment
requirements explicitly remain insufficient. All outputs retain `PARTIAL_SCIENTIFIC_COVERAGE` and
`whole_problem_scientifically_complete=false`.

## Method-source inspection and resulting decisions

On 2026-09-08 UTC, this worker inspected the installed SciPy `milp` docstring and only these two
external primary API pages; no answer or case-method searches were made:

- [SciPy milp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html):
  use bounded binary integrality and distinguish time-limit termination, incumbent, dual bound and
  relative gap. This directly changed the solver output and prevented later lexicographic stages
  from treating an unproved timed incumbent as an optimum.
- [SciPy HiGHS linprog](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html):
  use explicit equality/upper-bound matrices and sequential frozen objective bounds for Q3/Q4.

The online pages displayed SciPy 1.18.0. The actual unchanged local environment is SciPy 1.17.1,
NumPy 2.4.6 and openpyxl 3.1.5; synthetic tests exercise that installed API. No dependency was installed
and no environment/global configuration changed. Source registration remains main-agent work.

## Implementation validation and remaining work

Executed with the existing `.venv/bin/python`:

- `-m unittest discover -s evals/results/phase-004c5/development/v6/2021/code -p test_c2021_repair.py -v`:
  10/10 synthetic checks pass, including full in-process producer/checker JSON/metric binding,
  purchase arithmetic, ratio invariance at fixed actual supply capacity, hierarchy/count,
  Q3 material priorities, Q4 stock, surplus/overload, accumulated shortage, duplicates/undershipment,
  actual CSVs, hash rejection before parsing and timed/missing incumbent preservation.
- `-m ruff check evals/results/phase-004c5/development/v6/2021/code`: passes.
- Ruff formatting, Python AST syntax and both CLI help entrypoints checked.
- Scoped `git diff --check` checked; no Git mutation performed by the worker.

No official full model has been executed by this worker before the main agent's code commit and
captured-run authorization. Therefore no real 2021 result, numerical improvement, full scientific
completion, release acceptance, or remote delivery is established by these implementation checks.
The main agent must bind code to its actual Git subject, capture each authorized candidate attempt,
run the independent checker, preserve all negatives, compare the separately captured legacy plan
under the common formula, and decide requirement-level acceptance from the resulting artifacts.

## Derived v5 algorithm control

`code/c2021_v5_control.py` preserves the old objective, greedy allocation, scoring and
solver logic. Its only changes are bounded W001–W216 input parsing/schema and the
uniquely named old-helper import. `code/c2021_v5_control_feasibility.py` is byte-identical
to the old helper. The control retains the old cost bug intentionally; its actual plans
are recomputed by the new independent checker under the common actual-supply metric.
This is a derived old-algorithm control, not a byte-identical replay of the original producer.
The main agent owns its single additional captured attempt.

Control producer SHA-256: `ad76a5c55d9142de0b1f1d2744024bfaa5e7c93f7cd7b5815e544ecc2cb4b70e`.

Control helper SHA-256: `f64bcb3942e10bbe804ae979e85f4f7d26ce8315eef650e0d9bedb397e606ef6`.

Exact producer diff from the unchanged v5 source:

```diff
--- evals/results/phase004c5-pr12-7h/development-v5/code/CUMCM-2021-C-DEVELOPMENT-BATCH-002/c2021_supply_plan.py
+++ evals/results/phase-004c5/development/v6/2021/code/c2021_v5_control.py
@@ -14,7 +14,7 @@
 from typing import Any
 
 import numpy as np
-from c2021_feasibility import CONSUMPTION, PURCHASE_PRICE, verify_plan
+from c2021_v5_control_feasibility import CONSUMPTION, PURCHASE_PRICE, verify_plan
 from openpyxl import load_workbook
 from scipy.optimize import Bounds, LinearConstraint, linprog, milp
 
@@ -62,7 +62,11 @@
 ) -> tuple[list[str], list[str], np.ndarray]:
     workbook = load_workbook(path, read_only=True, data_only=True)
     worksheet = workbook[sheet]
-    rows = [row for row in worksheet.iter_rows(values_only=True) if row[0] is not None]
+    rows = [
+        row
+        for row in worksheet.iter_rows(max_col=first_numeric_column + 216, values_only=True)
+        if row[0] is not None
+    ]
     headers = [str(value) for value in rows[0]]
     identifiers = [str(row[0]) for row in rows[1:]]
     matrix = np.asarray(
@@ -81,19 +85,21 @@
     workbook = load_workbook(supplier_path, read_only=True, data_only=True)
     worksheet = workbook["企业的订货量（m³）"]
     supplier_types = [
-        str(row[1]) for row in list(worksheet.iter_rows(values_only=True))[1:] if row[0] is not None
+        str(row[1])
+        for row in list(worksheet.iter_rows(max_col=2, values_only=True))[1:]
+        if row[0] is not None
     ]
     workbook.close()
     carrier_headers, carrier_ids, loss_pct = _sheet_matrix(carrier_path, "运输损耗率（%）", 1)
-    expected_weeks = [f"W{week:03d}" for week in range(1, 241)]
+    expected_weeks = [f"W{week:03d}" for week in range(1, 217)]
     if (
         order_ids != supply_ids
         or order_headers[2:] != expected_weeks
         or supply_headers[2:] != expected_weeks
         or carrier_headers[1:] != expected_weeks
-        or order.shape != (402, 240)
-        or supply.shape != (402, 240)
-        or loss_pct.shape != (8, 240)
+        or order.shape != (402, 216)
+        or supply.shape != (402, 216)
+        or loss_pct.shape != (8, 216)
         or any(material not in CONSUMPTION for material in supplier_types)
         or np.any(~np.isfinite(order))
         or np.any(~np.isfinite(supply))
```
