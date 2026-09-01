# ADR-0023 — Semantic Judges are conditional, not mandatory

Status: Accepted
Date: 2026-09-01

## Context

Semantic Judges can examine mathematical, scientific, and engineering quality, but they cannot
repair missing balanced cases, manufacture independent repeats, clear a legal hard Gate, or convert
recovery evidence into primary comparison evidence. Making them unconditional caused transport to
block deterministic non-accepting outcomes.

## Decision

Candidate-quality semantic Judges run only when the deterministic evidence-sufficiency Gate passes
and no mandatory hard Gate already blocks the target. Judges remain required for any future
semantic acceptance path. They cannot replace hard Gates, alter thresholds, count votes, or infer
missing runs. Missing semantic Judge output does not block an audited deterministic
`EVIDENCE_INSUFFICIENT`, `AUTOMATED_REJECTED`, or `STALE` short-circuit.

Native Phase 002C auditors are adversarial validators of the deterministic procedure, not substitute
candidate-quality Judges and not a ranking panel.

## Consequences

- Model usage is reserved for questions that deterministic evidence cannot answer.
- A hard Gate remains non-compensable.
- Acceptance still requires all semantic predecessors and an independent passing Audit.

## Rejected alternatives

- Treating every agent role as interchangeable.
- Allowing Judge consensus to override a hard Gate.
- Inferring acceptance when Judges are skipped.
