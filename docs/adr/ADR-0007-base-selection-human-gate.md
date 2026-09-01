# ADR-0007 — Base selection requires a human Gate

Status: Superseded by ADR-0010; retained as historical Phase 002 evidence only.

## Context

A weighted score cannot resolve license rights, contamination tolerance, integration conflict,
maintenance burden, or whether measured gains justify contest-time cost. These are governance and
risk decisions, not purely technical facts.

## Decision

Phase 002 may publish `RECOMMEND_*`, `INSUFFICIENT_EVIDENCE`, `REJECT_AS_BASE`, or
`DYNAMIC_TEST_BLOCKED` proposals. It must not set `base_selected=true`, integrate content, or enter
Phase 003. The project remains `IN_PROGRESS` with `GATE_BASE_SELECTION_PENDING` until a named human
decision is appended through the formal workflow.

## Consequences

Strong dynamic performance cannot bypass legal or safety blockers. Rejection retains all evidence
and permits a clean-room/no-upstream fallback.
