# Phase 002D Batch 7 terminal checkpoint

- Frozen retry: `EXP-CASE-001-ARM-A-R2-A03`
- New attempts / primary eligible / excluded: 1 / 0 / 1
- New completion failures / hard failures / infrastructure failures / retries: 0 / 1 / 0 / 1
- Cumulative attempts / primary eligible: 28 / 18
- Balanced cases: `CASE-001`, `CASE-002`, `CASE-004`; global repeat depth: 0
- Runner status: `STOPPED`
- Hard-stop reason: `ELAPSED_BUDGET_REACHED`

The A03 attempt completed with a Schema-valid observation and process PASS, but wrote no publishable
files and has authoritative `HARD-FAIL-003`; it is excluded. Its oracle FAIL is retained but is not
used to decide eligibility. The 240.183696-second attempt increased cumulative elapsed time from
5,988.297082 to 6,228.480778 seconds, crossing the frozen 6,197-second absolute limit. No further
model start is permitted.

## Terminal evidence and cost

- Eligible target / achieved / shortfall: 24 / 18 / 6
- Balanced-case minimum / achieved: 4 / 3
- Repeat-depth minimum / achieved: 2 / 0
- Oracle PASS / FAIL among 18 eligible records: 9 / 9
- Completion / infrastructure failures: 8 / 1
- Observed input/output tokens: 5,726,854 / 272,461
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`
- Attempts used / absolute cap: 28 / 40
- Cost hash: `a9b97f479c53fe6b25ff9d3688ff3cb4e8e9b092161951a0be1a39972fb07d5f`
- Score-audit hash: `5b84b5a29c550936a7ba06fa9c1d15dfe049cda2c3e309eba14c237f6d59f81e`
- Attempt-ledger content hash: `9b3c1d2ad1ac778b0c0df86a2a5fcc99380cb051847b848250fb98db653aa953`
- Checkpoint content hash: `0d40d172999d566050bfe1c6ba63ba0022ec6b20db84ae0b38179e0ac39a8eee`

The runner, cost and append-only score audit all pass. This terminal status is not evidence
sufficiency and cannot be overridden by unused attempt, input, or output capacity. Four native
Subagent audits remain locked because the quantitative minima were not met.
