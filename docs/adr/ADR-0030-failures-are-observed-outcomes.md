# ADR-0030: Failures are observed outcomes

Status: Accepted

## Decision

Classify all frozen attempts once and retain failures as categorical evidence. Never discard them,
zero-impute them, or treat censoring as candidate rank.

## Consequences

Reliability and cost use all attempts; quality uses only eligible oracle PASS records; mixed causes
remain explicit and auditable.
