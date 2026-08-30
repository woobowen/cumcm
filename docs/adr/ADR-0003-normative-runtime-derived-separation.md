# ADR-0003: Separate normative, runtime, and derived data

## Context
Duplicated rules and hand-edited reports drift across long sessions.
## Candidates
One monolithic document; duplicated summaries; separate truth layers.
## Decision
Keep governance/rules/contracts normative, `state/` runtime, and reports generated/read-only.
## Evidence
Machine checks can detect stale derivations and a future session can recover without chat memory.
## Rejected alternatives
Monoliths exceed instruction budgets; duplicated summaries become conflicting truth.
## Consequences
Writers must update authoritative state then regenerate reports.
## Revisit conditions
Only if a transactional store replaces files while preserving versioned export and auditability.
