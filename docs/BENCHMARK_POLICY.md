# Benchmark policy

Development cases are visible and may drive iteration. Validation cases evaluate a frozen Skill and cannot be tuned within the run. Held-out cases and answers use an excluded vault, independent access/gates, and one-way demotion to development after answer exposure. Stress cases test generic failure modes without embedding real answers. All runs record Skill version, searches, interventions, rubric, evidence, and contamination status.

`evals/adjudication/` contains project-authored protocol cases, never historical answers. They test
accept/reject/abstain, minority counterexamples, identity/order changes, social proof, recovery
contamination, keyword gaming, report mutation, replay, license, and duplicate state sources. CI runs
only mocks and deterministic cases; it never starts a real Codex Agent.

Real Phase 002D runs are local, manually invoked evaluation evidence and are never CI jobs. CI may
replay hashes, Schemas, schedules, oracle/process logic, sufficiency and the locked incomplete route
without network, model starts, native semantic Subagents or hidden-answer access.
