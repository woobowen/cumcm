# Phase 002D schedule and runner freeze

## Frozen design

- Schedule: `PHASE-002D-BLOCKED-SCHEDULE-001`
- Seed: `20260901`
- Schedule hash: `5d0351aa4e00885131aedfefdbaa8e311cf2c299652a38f42f6ecad762c045aa`
- Cases / repeats / anonymous arms: 4 / 2 / 3
- Blocks / primary attempts / retry slots: 8 / 24 / 48
- First block: `CASE-001 × repeat 1`, order `ARM-C`, `ARM-A`, `ARM-B`
- Retry policy: complete the primary queue before the frozen retry queue; never retry a successful
  cell; maximum three fresh starts per cell; no post-result reordering

## Runner Gate

- Status: `READY`
- Scored attempts / primary eligible / failures: 0 / 0 / 0
- Balanced cases / repeat depth: 0 / 0
- Next attempt: `EXP-CASE-001-ARM-C-R1-A01`
- Remaining attempt budget: 40
- Fixed model/reasoning/profile: `gpt-5.6-sol` / `medium` / `PROXY_INHERITED`
- Session policy: fresh `codex exec --ephemeral`; no resume/parser recovery as primary evidence
- Sandbox/network/MCP: `workspace-write` / disabled-required / disabled-required
- Per-run timeout / concurrency: 900 seconds / 1
- Raw traces and stderr: ignored cache only; tracked records contain hashes and sanitized summaries
- Append-only attempt ledger and atomic derived ledger/checkpoint: enabled
- Input freeze: `ddcb409eaadf69d965acc1b29992a5f83aa242508f1f3c38b19a0cf1b33f2bfa`

Primary eligibility verifies execution and frozen provenance without filtering on oracle PASS/FAIL.
The deterministic oracle must execute; its outcome remains separate correctness evidence. Coverage
is explicitly non-correctness evidence. Recovery-affected, mock, failed, schema-invalid, resumed,
mutated, contaminated, network/MCP-violating or identity-leaking attempts cannot count.

Validation before scored work: Ruff PASS; 49 focused deterministic tests PASS; 43 Schema positive
fixtures accepted; 33 negative fixtures rejected; input/schedule/runner checks PASS; dry-run showed
exactly the frozen first three attempt IDs and did not start a model.
