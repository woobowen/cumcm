# Phase 002D Batch 6 retry checkpoint

- Frozen retries: CASE-001/ARM-A/R2/A02, CASE-004/ARM-A/R2/A02, CASE-006/ARM-A/R1/A02
- New attempts / primary eligible / excluded: 3 / 1 / 2
- New completion failures / hard failures / infrastructure failures / retries: 2 / 1 / 1 / 3
- New oracle PASS / FAIL among eligible records: 0 / 1
- Cumulative attempts / primary eligible: 27 / 18
- Balanced cases: `CASE-001`, `CASE-002`, `CASE-004`; global repeat depth: 0
- Next attempt: `EXP-CASE-001-ARM-A-R2-A03`

| Order | Attempt | Completion | Eligible | Failure class | Oracle | Seconds |
|---:|---|---|---|---|---|---:|
| 1 | EXP-CASE-001-ARM-A-R2-A02 | FAILED | false | HTTPS_FALLBACK_DISCONNECT | FAIL | 185.511887 |
| 2 | EXP-CASE-004-ARM-A-R2-A02 | COMPLETED | true | — | FAIL | 300.355950 |
| 3 | EXP-CASE-006-ARM-A-R1-A02 | FAILED | false | POLICY_VIOLATION | NOT_RUN | 197.265745 |

All three attempts are fresh, append-only retries bound to their A01 records. The transport-failed
CASE-001 record is Schema-valid but fails completion/process Gates and has authoritative
`HARD-FAIL-003`; it is not primary evidence. CASE-006 is a Schema-invalid exclusion. CASE-004 is
eligible and its oracle FAIL is retained. No resume, parser recovery, or operator intervention was
used.

## Cumulative evidence and cost

- Oracle PASS / FAIL among 18 eligible records: 9 / 9
- Observed input/output tokens: 5,498,280 / 261,169
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`
- Elapsed / remaining elapsed: 5,988.297082 / 208.702918 seconds
- Remaining attempts/input/output: 13 / 4,501,720 / 73,274
- Cost hash: `4ac9dfc5a1a394052e12c2d532101a18aa2ee2bfa3c7db083127d15a9b95ef12`
- Score-audit hash: `86b4728889371087309aa3e0e6ec397f119511ceaceb16e5e500db5aef8140da`
- Attempt-ledger content hash: `2c309f1b4f36bcaa9aabf9ced1c7cfebe26cca4aa17da03870f47ed51bcf941e`
- Checkpoint content hash: `a2ce42c0351a1500eae4f7f90e297a41e77d882eec9d1ffee7cab5b6b8305e6f`

Minima remain unsatisfied by six eligible records. Runner status is still READY because the frozen
elapsed hard limit is checked before the next start; only the final A03 for the first cell may run
after this checkpoint is remotely delivered.
