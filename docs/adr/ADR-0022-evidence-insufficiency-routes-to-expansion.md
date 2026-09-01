# ADR-0022 — Evidence insufficiency routes to expansion

Status: Accepted
Date: 2026-09-01

## Context

An insufficient comparison cannot authorize architecture or component integration, yet treating it
as a failed project terminal would preserve the Phase 002B deadlock. The missing evidence is
measurable: balanced complete cases and repeat depth must satisfy their frozen minima.

## Decision

After Decision Audit `PASS`, an architecture/evidence result of `EVIDENCE_INSUFFICIENT` may set
`next_phase_allowed=PHASE-EVIDENCE-EXPANSION-002D`. It must set `selected_architecture=null`, keep
`base_selected=false`, `third_party_integrated=false`, and retain the formal Skill as
`SCAFFOLD_ONLY`. It must not authorize `PHASE-SKILL-INTEGRATION-003`.

Phase 002C writes only a self-contained 002D plan. It does not execute new cases, repeats, semantic
roles, integration, or historical-answer access.

## Consequences

- Insufficiency is actionable without being mistaken for acceptance.
- Evidence expansion has explicit missing cells, costs, budgets, and stop rules.
- Phase 003 remains conditional on a later sufficient, audited, replay-stable acceptance.

## Rejected alternatives

- Routing insufficiency directly to integration.
- Rerunning Phase 002 inside 002C.
- Leaving `next_phase_allowed` permanently null after a complete audited insufficiency result.
