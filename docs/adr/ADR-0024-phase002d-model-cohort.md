# ADR-0024: Freeze Phase 002D as a new-model cohort

Status: Accepted
Date: 2026-09-01

## Context

Phase 002 primary evidence used `gpt-5.4` with reasoning `medium`. Phase 002D may reuse those records
only when every content, safety, execution and model-cohort condition is exact and a compatibility
pilot passes. A web catalog is not proof of local availability.

The current local ChatGPT-managed Codex App Server `model/list` returned `gpt-5.2`, `gpt-5.5`,
`gpt-5.6-luna`, `gpt-5.6-sol`, and `gpt-5.6-terra`; it did not return `gpt-5.4`. The probe started
zero models, used no API key, and preserved a sanitized record plus a raw ignored trace hash.
`gpt-5.6-sol` is the only replacement allowed by the frozen config; it is visible, supports
`medium`, and has prior repository evidence of an actual start, although Phase 002D still requires
its own pilot.

## Decision

Select `NEW_MODEL_COHORT` with `gpt-5.6-sol`/`medium`. Use one model, reasoning setting, transport
profile, prompt, Schema, case set, packages, scorer, oracle and safety policy for all arms. Do not
switch models after freeze. The code-derived target is 4 cases × 3 anonymous arms × 2 fresh
repeats = 24 successful eligible primary runs.

Phase 002 records are retained only as `CROSS_MODEL_EXPLORATORY_GAP_EVIDENCE_ONLY`; they cannot
contribute repeats, balanced sets, medians, effects, superiority, architecture selection or
component selection in this cohort.

## Consequences

The historical continuation shortfall remains machine-computed as 14 for auditability, but it is
not the active target. A failed Phase 002D pilot blocks the experiment; it does not authorize a
different model. Scored work remains locked until the pilot and budget freeze pass.
