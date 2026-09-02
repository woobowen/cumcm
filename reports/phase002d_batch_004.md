# Phase 002D Batch 4 checkpoint

- Frozen blocks: `BLOCK-006-CASE-004-R2`, then `BLOCK-007-CASE-006-R1`
- New attempts / primary eligible / excluded: 6 / 3 / 3
- New completion failures / hard failures / infrastructure failures / retries: 3 / 2 / 0 / 0
- New oracle PASS / FAIL among eligible records: 0 / 3
- Cumulative attempts / primary eligible: 21 / 17
- Balanced cases: `CASE-001`, `CASE-002`, `CASE-004`; global repeat depth: 0
- Next attempt: `EXP-CASE-006-ARM-A-R2-A01`

| Block order | Arm | Attempt | Completion | Eligible | Oracle | Hard failure | Input | Output | Seconds |
|---:|---|---|---|---|---|---|---:|---:|---:|
| 1 | ARM-C | EXP-CASE-004-ARM-C-R2-A01 | COMPLETED | true | FAIL | — | 310216 | 13722 | 503.477581 |
| 2 | ARM-B | EXP-CASE-004-ARM-B-R2-A01 | COMPLETED | true | FAIL | — | 196292 | 11238 | 254.840098 |
| 3 | ARM-A | EXP-CASE-004-ARM-A-R2-A01 | FAILED | false | NOT_RUN | HARD-FAIL-003 | 323593 | 12734 | 259.621277 |
| 1 | ARM-A | EXP-CASE-006-ARM-A-R1-A01 | FAILED | false | NOT_RUN | — | 374268 | 10944 | 242.695839 |
| 2 | ARM-C | EXP-CASE-006-ARM-C-R1-A01 | FAILED | false | NOT_RUN | HARD-FAIL-003 | 193921 | 9941 | 216.769047 |
| 3 | ARM-B | EXP-CASE-006-ARM-B-R1-A01 | COMPLETED | true | FAIL | — | 116300 | 6457 | 179.163013 |

All six attempts were fresh starts in frozen order. The three failed records are retained as
`POLICY_VIOLATION`/Schema-invalid exclusions: two also have authoritative `HARD-FAIL-003`, while
CASE-006/ARM-A wrote publishable files but did not produce a valid observation. Their oracles were
not run and they cannot enter primary comparison. The three eligible records passed process and
hard Gates; their FAIL oracle outcomes are retained independently of eligibility.

## Cumulative evidence and cost

- Oracle PASS / FAIL among 17 eligible records: 9 / 8
- Observed input/output tokens: 4,254,250 / 212,711
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`
- Elapsed / remaining elapsed: 4,849.330806 / 1,347.669194 seconds
- Remaining attempts/input/output: 19 / 5,745,750 / 121,732
- Cost hash: `30538e0d6769e8d4f28f8655ab3cf65a8d2d468680ce71bcfd4efc2d5896921c`
- Score-audit hash: `9126fbb062ede4ba0688f79f8e75ebff061471b0d018e58d53fef255086ec53b`
- Attempt-ledger content hash: `03c7802cbfc201d8a53ad44480a6acc609de180266a31f971ef14bdec9529cc6`
- Checkpoint content hash: `0aaafd797d0d7dbaa0cdc38fc0f99f8da33051f29c7412def5f7afdb0f757dd2`

The append-only score audit was extended to classify missing-observation failures as
`NOT_APPLICABLE_NO_OBSERVATION`; it does not fabricate a recomputation or use coverage as a hard
Gate. Five comparable coverage-binding mismatches remain isolated. Minima remain unsatisfied and
Batch 5 is locked until this checkpoint is remotely delivered.
