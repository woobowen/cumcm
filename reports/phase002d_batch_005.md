# Phase 002D Batch 5 checkpoint

- Frozen block: `BLOCK-008-CASE-006-R2`
- New attempts / primary eligible / excluded: 3 / 0 / 3
- New completion failures / hard failures / infrastructure failures / retries: 3 / 1 / 0 / 0
- New oracle PASS / FAIL among eligible records: 0 / 0
- Cumulative attempts / primary eligible: 24 / 17
- Balanced cases: `CASE-001`, `CASE-002`, `CASE-004`; global repeat depth: 0
- Next attempt: `EXP-CASE-001-ARM-A-R2-A02` (first frozen retry)

| Order | Arm | Attempt | Completion | Eligible | Oracle | Hard failure | Input | Output | Seconds |
|---:|---|---|---|---|---|---|---:|---:|---:|
| 1 | ARM-A | EXP-CASE-006-ARM-A-R2-A01 | FAILED | false | NOT_RUN | HARD-FAIL-003 | 272127 | 9181 | 195.816241 |
| 2 | ARM-B | EXP-CASE-006-ARM-B-R2-A01 | FAILED | false | NOT_RUN | — | 100964 | 7281 | 159.629946 |
| 3 | ARM-C | EXP-CASE-006-ARM-C-R2-A01 | FAILED | false | NOT_RUN | — | 76072 | 3222 | 100.386507 |

All three attempts were fresh starts in frozen order. Each is retained as a Schema-invalid
`POLICY_VIOLATION` exclusion with process E0 and oracle NOT_RUN; ARM-A additionally has authoritative
`HARD-FAIL-003`. No transport or infrastructure failure, retry, resume, parser recovery, or operator
intervention occurred. Exhausting the primary queue is not evidence sufficiency.

## Cumulative evidence and cost

- Oracle PASS / FAIL among 17 eligible records: 9 / 8
- Observed input/output tokens: 4,703,413 / 232,395
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`
- Elapsed / remaining elapsed: 5,305.163500 / 891.836500 seconds
- Remaining attempts/input/output: 16 / 5,296,587 / 102,048
- Cost hash: `0f0e0f56794d2fe8d8209087f5a9b0ae11d2653bb0b70d5faead544f5fd50b8e`
- Score-audit hash: `18407b4d33453b0a3b6bb96d5d5251ae5162b3ae628c564482d04f066280a6ee`
- Attempt-ledger content hash: `8bf23f2d2cc29150c2d1ea6b122b961464827e6f337e84452a8f242ff6cb1b63`
- Checkpoint content hash: `46f34520c1ed22c9d4008f59747ba6ef8ca97378f5116e601853c141ce0f5854`

Score audit and cost checks pass; six failed attempts without valid observations are explicitly
noncomparable, and five comparable coverage-binding mismatches remain excluded from hard Gates.
Minima remain unsatisfied. Retry execution is locked until this checkpoint is remotely delivered.
