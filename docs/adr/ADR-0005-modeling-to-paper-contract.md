# ADR-0005: Versioned modeling-to-paper contract

## Context
The paper team must present results without rewriting model facts, uncertainty, or provenance.
## Candidates
Free-form notes; shared mutable document; schema-valid versioned evidence package.
## Decision
Handoff through `contracts/modeling_to_paper.schema.json` with approvals and claim-evidence links.
## Evidence
A machine contract makes omissions/staleness detectable and preserves team boundaries.
## Rejected alternatives
Free-form/mutable handoffs cannot reliably prevent factual drift.
## Consequences
Corrections require a new modeling decision/run/package rather than a prose edit.
## Revisit conditions
Version the schema when real handoffs demonstrate missing fields or incompatible consumers.
