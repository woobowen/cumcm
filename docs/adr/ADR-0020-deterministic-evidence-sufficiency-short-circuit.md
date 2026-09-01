# ADR-0020 — Deterministic evidence-sufficiency short-circuit

Status: Accepted
Date: 2026-09-01

## Context

Phase 002A already froze `balanced_case_minimum=4`, `minimum_repeats=2`, primary-evidence
eligibility, and recovery exclusion. Its derived evidence reports only two balanced cases and one
repeat. The former execution path nevertheless required all semantic Judges before a formal
insufficiency result, so Phase 002B transport failures blocked a conclusion already determined by
the frozen quantitative prerequisites.

## Decision

Evaluate freeze integrity, mandatory target hard Gates, primary eligibility, balanced complete
cases, independent repeats, and cross-arm task-input hashes before any candidate-quality semantic
Judge. This changes execution order only; it does not change a threshold, recovery treatment, hard
Gate, candidate result, or evidence value. When a frozen minimum fails, emit a deterministic
`EVIDENCE_INSUFFICIENT` proposal, skip candidate ranking and semantic comparison, and require
independent attacks plus a passing Decision Audit before formal state changes.

`EVIDENCE_INSUFFICIENT` is a complete automated technical decision because it is reproducible from
frozen inputs, has an explicit non-accepting route, and does not infer candidate quality.

## Consequences

- Known insufficiency no longer consumes semantic transport starts.
- Transport failures remain historical engineering evidence but do not block this deterministic
  decision path.
- Candidate scores, Judge opinions, and agent votes cannot override a failed minimum.
- A broken freeze yields `STALE`/`INPUT_FREEZE_BROKEN`, never insufficiency by assumption.

## Rejected alternatives

- Lowering thresholds after observing results.
- Treating recovery or NOT_RUN cells as complete evidence.
- Requiring semantic Judges to restate a deterministic count.
- Selecting the highest-scoring candidate despite insufficient evidence.
