# ADR-0018 — Role-specific evidence bundles

Status: Accepted
Date: 2026-09-01

## Context

A single large prompt increases transport load and risks cross-role leakage, candidate identity
exposure, and accidental omission through free-form summarization.

## Decision

Build each formal role input as a deterministic structured projection of frozen evidence. Preserve
all evidence identifiers and hashes, numeric results, hard Gates, BLOCKERs, unresolved Dissent,
recovery exclusions, and licensing/contamination limits relevant to the role. Exclude candidate
identity, peer outputs, historical answers, raw third-party content, raw traces, and private paths.
Bind each ignored bundle by a tracked manifest and enforce byte/token budgets by deterministic
de-duplication or sharding; never arbitrarily truncate.

## Consequences

- Role independence and evidence coverage are machine-checkable.
- Bundle construction is reproducible and consumes no model start.
- An oversize or incomplete bundle stops the role before transport.
- Phase 002B produced six valid compact bundles even though the formal chain later failed.
