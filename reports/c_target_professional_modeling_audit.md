# C-Target Professional Modeling Audit

## Overall result

`PARTIAL_NUMERIC_SUCCESS_EVIDENCE_CHAIN_REJECTED`. The 2024 C work is a feasible, reproducible
contest-time heuristic analysis with complete main-question outputs, but it is neither a proof of
global optimality nor an accepted end-to-end modeling handoff. The frozen Claim Gate rejection is
controlling.

## Audit dimensions

- Data quality: PASS with limitations. Both official data workbooks and all three official output
  templates are hash-bound. Row/column interpretation and template structure are audited; raw files
  remain immutable. Domain semantics are inferred from the official statement and workbooks, not
  externally validated observations.
- Model appropriateness: PARTIAL. The baseline rotation rule and primary risk-aware greedy method
  address multi-year, multi-season land allocation and uncertainty within contest time. Restricting
  allocations to whole plots is conservative and operationally simple, but narrows the feasible set.
- Mathematical validity: PASS for the stated heuristic scope. Land/season compatibility,
  plot-season capacity, nonnegativity, 2023-history rotation, rolling three-year legumes, minimum
  area, dispersion, and template years are independently recomputed for four selected plans with
  zero violations.
- Statistical validity: PARTIAL. Q2 uses 16 registered demand/yield/cost/price scenarios and reports
  risk-adjusted outcomes. Q3's substitutability, complementarity, elasticity, climate, and market
  factors are simulation assumptions, not estimated causal parameters; external calibration is
  absent.
- Optimization validity: PARTIAL. All accepted numeric plans are feasible and objectives are
  recomputed, but the deterministic greedy procedure is not a MIP solver and gives no global
  optimality bound. `MIXED_INTEGER_OPTIMIZATION` is represented by discrete whole-plot decisions,
  not an optimality certificate.
- Robustness: PASS for the frozen evidence contract. Three quantitative perturbations are bound to
  the selected Run, and Q2/Q3 scenario comparisons are finite. Coverage is limited to registered
  perturbations and cannot establish general distributional robustness.
- Result interpretation: PASS with bounded claims. Q1 waste profit is `37,599,028.25` yuan; Q1
  discount profit is `54,436,325.625` yuan; Q2 risk-adjusted profit is `38,654,170.051186` yuan;
  Q3 is `38,549,231.473884` yuan and is `80,154.715582` yuan below the Q2 plan evaluated under the
  registered dependent scenarios. These are model outputs under assumptions, not realized profit.
- Handoff quality: FAIL. A canonical `modeling-to-paper/v1` handoff cannot be accepted because the
  prerequisite Claim Gate is unsatisfiable for the frozen global and first-requirement scopes.
- Contest efficiency: PASS for the 4-hour bound and actual execution grid; all four Runs completed
  once with no retry. Early-stage operator time and seal command start times are only partially
  instrumented.

## Unresolved weaknesses

The Claim schema cannot encode the requested per-requirement pointer/scope/limitation/uncertainty
enrichment, because nested records must exactly equal the selected output's three-field records.
Validation-output access timing is enforced by the comparison record; the model code computed
robustness fields for each Run, so there is no OS-level suppression of unselected output fields.
Model-prior exposure is unverifiable. No reference answer was accessed, so substantive accuracy
against an official solution remains unknown. The terminal case cannot be rerun as Validation.
