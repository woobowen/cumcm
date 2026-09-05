# Phase 004C3 semantic Claim support

The RC6 `claim-evidence/v3` view retains v2 hash lineage and adds structured per-requirement Claim
types, scopes, evidence classes, selected Run/output/metric/comparator IDs, predicates,
uncertainty, counter-evidence, limitations, strength and status. It checks bounded predicates for
descriptive, empirical, predictive, comparative, policy, feasibility, optimality, causal and
simulation-conditional Claims; it does not claim arbitrary natural-language entailment.

Policy Claims require execution, nonzero exposure, a comparator, and recorded benefit/cost.
Feasibility requires independent recalculation; global optimality requires a certificate; causal
and predictive Claims require their declared identification/test boundaries. Counter-evidence
cannot be silently omitted.

Auditor 1 reproduced PASS results for a failed/unsealed/stale selected Run, a wrong requirement,
output not owned by the Run, missing metric binding, `scope_bounded=false`, and an aggregate
requirement mapped to the wrong Claim ID. The compatibility adapter also accepts an unknown kind,
`claim-evidence/v999` and a non-permutation. The fresh controller hardcodes every Claim as
descriptive/provided-empirical and policy exposure as positive. These fail-open paths make RC6
unreleasable after the two-cycle cap.
