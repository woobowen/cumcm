# ADR-0009 — Synthetic benchmarks precede historical problems

Status: Accepted for Phase 002

## Context

Historical CUMCM problems have public answers, excellent papers, candidate demos, and memorized
solution patterns. Using them during upstream selection risks answer leakage and invalid comparison.

## Decision

Phase 002 uses six project-authored synthetic cases with fixed seeds, local data, injected faults,
known optima or explicit dependency/source oracles, and frozen hashes. Historical cases do not enter
this phase.

## Later lifecycle

After human-gated integration, visible historical cases may enter development; a frozen Skill is
then assessed on separate validation cases, and held-out cases remain vault-governed. Any exposed
answer permanently demotes that case to development.

## Consequences

Synthetic cases provide deterministic truth for requirement coverage, leakage, feasibility,
optimality, STALE propagation, and evidence support. They cannot reproduce full contest ambiguity,
domain breadth, data scale, model creativity, or writing pressure, so they do not replace later
development/validation/held-out testing.
