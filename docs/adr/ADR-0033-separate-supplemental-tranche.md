# ADR-0033: Separate supplemental tranche

Status: Accepted

## Decision

Any authorized censor-repair run belongs to a distinct immutable budget and exact allowlist. It does
not expand or rewrite the original Phase 002D budget.

## Consequences

Protocol changes require a new cohort. Missing equivalence or authorization produces zero starts.
