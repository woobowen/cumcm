# ADR-0006 — Controlled dynamic evaluation method

Status: Accepted for Phase 002

## Context

Static review proves only that files and claimed mechanisms exist. It cannot establish observable
agent behavior, correctness, evidence discipline, reproducibility, latency, or failure handling.

## Decision

Evaluate three arms on identical synthetic cases using isolated temporary Git repositories, fixed
configuration, structured outputs, observable event summaries, deterministic graders, and an
anonymous reviewer layer. The no-project-modeling-Skill baseline and both sanitized base candidates
receive equal inputs, tooling, model, reasoning, timeout, and budget. Initial scores freeze before
identity reveal; hard failures remain non-compensable.

## Consequences

Dynamic evidence becomes reproducible and auditable without integrating candidates. Results remain
small-sample estimates and selection proposals. Raw traces and candidate text stay local/ignored.
