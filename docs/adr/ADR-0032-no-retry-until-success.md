# ADR-0032: No retry until success

Status: Accepted

## Decision

Resolve slots by the first decisive terminal outcome or earliest eligible success and retain every
attempt in reliability and cost. Prohibit best-of-N and later-success erasure.

## Consequences

Historical deviations stay visible; future start preflight rejects retries after terminal outcomes.
