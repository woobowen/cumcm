# ADR-0016 — Resumable formal adjudication

Status: Accepted
Date: 2026-09-01

## Context

Phase 002A lost three Correctness attempts to transport failures and retained only sanitized traces,
not a resumable exact-session contract. Repeating a formal turn can spend the budget, change model
state, and obscure whether output belongs to the original role.

## Decision

Formal transports must capture an exact session/thread checkpoint as soon as it is observable.
After a resumable transport failure, at most one continuation may target that exact identifier with
the same role workspace, evidence bundle, policy, Schema, model, and reasoning. Exact identifiers
and raw events remain ignored; tracked records retain irreversible hashes and bounded diagnostics.
`resume --last` and implicit session discovery are prohibited.

## Consequences

- Interrupted work can continue without rerunning an earlier valid role.
- Each continuation consumes a configured model start.
- Missing, stale, or mismatched session evidence fails closed.
- A two-attempt role limit can terminate the chain while global budget remains.
