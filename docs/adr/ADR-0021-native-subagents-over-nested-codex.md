# ADR-0021 — Native Subagents over nested Codex transport

Status: Accepted
Date: 2026-09-01

## Context

Three Phase 002A Correctness starts and both Phase 002B Correctness turns failed in the Codex
Responses transport before a Schema-valid result. The last two failures were the initial
`EXEC_RESUMABLE` turn and its exact-session continuation; the role budget is exhausted. Repeating
that transport or starting App Server as a third turn is prohibited.

The current interactive Codex session exposes native multi-agent capability. Official Codex
configuration supports project-scoped `.codex/agents/*.toml` files and per-agent
`sandbox_mode="read-only"` without changing user-global configuration.

## Decision

Use native Subagents for the four independent Phase 002C attacks and the post-decision Audit. Each
project agent is read-only, narrowly scoped, non-voting, and forbidden from running nested Codex,
using API keys, writing project files, or reading first-round peer outputs. The main thread is the
only formal-state writer. Model and reasoning settings inherit from the parent session so the five
roles remain uniform without outcome-driven model switching.

## Consequences

- No nested `codex exec`, App Server, SDK, Responses API, OpenAI API, or API key is used in 002C.
- Historical transport code and diagnostics remain intact for a future phase whose deterministic
  Gate actually requires semantic adjudication.
- Native-agent outputs are E0/E1 attack records until Schema, evidence references, isolation, and
  resulting tests validate them.
- Runtime metadata that the host does not expose is recorded as unverified rather than fabricated.

## Rejected alternatives

- A third Correctness transport attempt.
- Main-agent-authored role simulations.
- Mixed models or outcome-driven model selection.
- Modifying `~/.codex/` or switching authentication/billing.
