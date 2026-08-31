# ADR-0017 — Exec-to-App-Server fallback

Status: Accepted
Date: 2026-09-01

## Context

Codex exec is the simplest isolated formal transport, but some failures do not yield a usable exec
session or cannot satisfy exact resume. An alternate transport is needed without changing formal
inputs or authentication.

## Decision

Use `EXEC_RESUMABLE` as primary and the bundled stdio Codex App Server as the sole fallback.
Fallback is allowed only within the existing role/global start budgets and only when exec has no
resumable session, exact resume fails, or the exec resume contract cannot be met. The App Server
client must preserve role isolation, model/reasoning, bundle, policy, Schema, sandbox, and
ChatGPT-managed authentication. It may not install an SDK or change global configuration.

## Consequences

- Adapter choice is deterministic and audited in the checkpoint.
- Fallback cannot be used as an extra attempt after the role budget is exhausted.
- App Server availability does not imply a successful formal result.
- Phase 002B did not start App Server because doing so after two Correctness starts would have been
  a prohibited third attempt.
