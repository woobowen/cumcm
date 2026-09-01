# Phase 002D Batch 3 checkpoint

- Frozen blocks: `BLOCK-004-CASE-002-R2`, then `BLOCK-005-CASE-004-R1`
- New attempts / primary eligible / excluded: 6 / 6 / 0
- New completion failures / hard failures / infrastructure failures / retries: 0 / 0 / 0 / 0
- New oracle PASS / FAIL: 3 / 3
- Cumulative attempts / primary eligible: 15 / 14
- Balanced cases: `CASE-001`, `CASE-002`, `CASE-004`; global repeat depth: 0
- Next attempt: `EXP-CASE-004-ARM-C-R2-A01`

| Order | Arm | Attempt | Oracle | Input | Output | Seconds |
|---:|---|---|---|---:|---:|---:|
| 1 | ARM-C | EXP-CASE-002-ARM-C-R2-A01 | PASS | 96673 | 7496 | 191.957610 |
| 2 | ARM-B | EXP-CASE-002-ARM-B-R2-A01 | PASS | 147651 | 12577 | 267.054820 |
| 3 | ARM-A | EXP-CASE-002-ARM-A-R2-A01 | PASS | 349592 | 13186 | 278.259572 |
| 4 | ARM-A | EXP-CASE-004-ARM-A-R1-A01 | FAIL | 411410 | 15286 | 306.506821 |
| 5 | ARM-C | EXP-CASE-004-ARM-C-R1-A01 | FAIL | 167950 | 11130 | 244.029922 |
| 6 | ARM-B | EXP-CASE-004-ARM-B-R1-A01 | FAIL | 101216 | 5755 | 132.978988 |

All six attempts are fresh, Schema-valid, process E2, input-preserving, hard-failure-free and bound
to the frozen cohort/configuration. CASE-004 failures are deterministic oracle outcomes caused by
the missing `identity baseline / not a fitted regression` validation-selection evidence; they are
retained as outcomes and do not alter primary eligibility.

## Cumulative evidence and cost

- Oracle PASS / FAIL among 14 eligible records: 9 / 5
- Observed input/output tokens: 2,739,660 / 147,675
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`
- Elapsed / remaining elapsed: 3,192.763951 / 3,004.236049 seconds
- Remaining attempts/input/output: 25 / 7,260,340 / 186,768
- Cost hash: `37657847724f963ae9afc714e9e67a00ea22b70843ded679da4a2d41e20dd96d`
- Score-audit hash: `1be00ad26c38f1bd1d1d506ea01db3770e14f798ddfcec983312959cbcf05a8a`
- Attempt-ledger content hash: `65e22120b81f3756a0589f8bf9c4883d72bd17b1e462a6265803541adbfb71a9`
- Checkpoint content hash: `7efcbf5f06f8e6c4b96dcc151752a01f7d9a85f63789c92ce370caa28c1b1e72`

The score audit passes authoritative recomputation and isolates four coverage-only binding
limitations, all excluded from hard Gates. Minima remain unsatisfied and Batch 4 is locked until
this checkpoint is remotely delivered.
