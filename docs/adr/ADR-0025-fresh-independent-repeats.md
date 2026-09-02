# ADR-0025: Count only fresh complete sessions as independent repeats

Status: Accepted
Date: 2026-09-01

## Context

Transport recovery can preserve work, but it does not create statistically independent evidence.
Phase 002 contained recovery-affected cells and Phase 002B demonstrated that exact-session resume
is useful only as transport diagnosis.

## Decision

A Phase 002D primary repeat must start a fresh ephemeral Codex session from frozen inputs and pass
the output Schema, deterministic oracle, process-evidence, input-integrity, cohort, policy and
safety checks. A failed attempt is retained. A later fresh start may qualify independently, but
resume, parser recovery, raw-output recovery, manual repair, partial output, model/profile drift and
cross-model history never qualify.

## Consequences

Attempt count and primary-success count are separate. Recovery evidence remains useful for gap and
infrastructure analysis but is excluded from ranking, repeat depth and balanced-case completion.
