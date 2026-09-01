# Phase 002D evidence sufficiency

- Result: `INSUFFICIENT`
- Eligible records: 18 (target implied by frozen 4 × 3 × 2 cells: 24)
- Balanced cases: 3 / 4 — CASE-001, CASE-002, CASE-004
- Independent repeats among balanced cells: 1 / 2
- Failed / recovery / superseded / NOT_RUN exclusions: 8 / 0 / 0 / 0
- Task-input hash consistency: True
- Frozen evidence valid: True
- Mandatory hard Gates over eligible evidence: True
- Semantic Subagents required/unlocked: False
- Comparative ranking allowed: False
- Reason codes: BALANCED_CASE_MINIMUM_NOT_MET, MINIMUM_REPEATS_NOT_MET
- Record hash: `cf9c9c98573615f632703b454162e38e4f65a5347e043b2eacd1392748075714`

Retry attempts do not increase independent-repeat depth unless they fill a previously missing
`case × arm × repeat` cell. The runner checkpoint's global schedule repeat depth is 0 because
CASE-006 has no complete repeat; this sufficiency record reports 1 across the three balanced cases.
Neither metric meets the frozen minimum of 2. Native semantic Subagents remain locked.
