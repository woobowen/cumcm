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
