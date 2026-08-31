# Recovery

- **Conversation interrupted:** read the startup truth chain, active plan, state, `git status`, and latest commits; run status check and resume the earliest incomplete milestone.
- **State damaged:** retain the invalid file as evidence, validate append-only ledgers, reconstruct a new schema-valid state through a reviewed decision, regenerate reports, and mark uncertain descendants `STALE`.
- **Git conflict:** do not discard either side. Resolve truth-source files manually with owner review; rerun schemas/tests/status checks before commit.
- **Upstream unavailable:** retain last exact commit evidence, mark fetch `NOT_FETCHED`/fact `UNVERIFIED`, avoid stale-cache claims, and defer dynamic work.
- **Tests fail:** locate the first stable error ID, fix root cause, rerun focused then full checks; after three failed repair cycles record `FOUNDATION_INCOMPLETE` and evidence.
- **Schema upgrade fails:** do not mutate old records in place. Add a versioned migration plan/fixture, retain the previous schema, and block release until round-trip validation passes.
- **Third-party files entered tracked tree:** stop; identify exact paths, remove only those project additions through a reviewed patch, verify Git index/cache ignore, and record the incident. Never use broad clean/reset commands.
- **Candidate Skill entered discovery:** stop Codex use in that tree, move the candidate only to its exact ignored cache through a reviewed operation, run discovery checks, and inspect for copied text.
- **Upstream/result changed:** record dependency change, propagate `STALE` from the earliest affected artifact, rerun validation/review, and require approval before clearing.
- **Adjudication transport fails:** atomically checkpoint the exact session/thread in ignored local
  state, retain raw trace only in ignored cache, and track hashes plus a bounded risk summary.
  Resume or fall back only as allowed by the active versioned role/global budget. A role whose
  budget is exhausted stops the chain as `AUTOMATED_ADJUDICATION_INCOMPLETE`; unused global starts
  cannot override it. Never run a dependent role, Meta, Auditor, replay, or decision generation
  without valid prerequisites. See `TRANSPORT_RECOVERY_POLICY.md`.
- **Team challenge:** validate the separate challenge record, mark the decision and descendants
  `STALE`, and replay automated adjudication. Team review cannot reverse the technical record.
