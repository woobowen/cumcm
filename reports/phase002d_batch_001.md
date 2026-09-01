# Phase 002D Batch 1 checkpoint

## Execution result

- Frozen block: `BLOCK-001-CASE-001-R1`
- Frozen order: `ARM-C`, `ARM-A`, `ARM-B`
- New attempts: 3; fresh sessions: 3; resume/parser recovery: 0 / 0
- Completion / Schema / process E2 / primary eligible: 3 / 3 / 3 / 3
- Failed attempts / infrastructure failures / retries / manual interventions: 0 / 0 / 0 / 0
- Oracle PASS / FAIL: 1 / 2
- Balanced cases: `CASE-001`; global repeat depth: 0
- Next frozen attempt: `EXP-CASE-001-ARM-A-R2-A01`
- Remaining attempt budget: 37

| Order | Arm | Attempt | Oracle | Input tokens | Output tokens | Duration seconds |
|---:|---|---|---|---:|---:|---:|
| 1 | ARM-C | EXP-CASE-001-ARM-C-R1-A01 | FAIL | 110798 | 5883 | 150.168568 |
| 2 | ARM-A | EXP-CASE-001-ARM-A-R1-A01 | PASS | 323805 | 12392 | 268.726587 |
| 3 | ARM-B | EXP-CASE-001-ARM-B-R1-A01 | FAIL | 98386 | 9570 | 214.176884 |

All attempts bind subject commit `981414245a20a282bb98d20d75003d51a948536c`, cohort
`db663586c...`, one task-input hash, fixture/Schema/policy/oracle/scorer/runner hashes, the fixed
model/reasoning/profile, workspace commits, raw-trace/stderr hashes and structured result hashes.
No hard failure, network/MCP event, identity leak, input mutation or prohibited action was observed.

Oracle outcome was deliberately not used to select primary records; the two FAIL observations
remain required technical outcome evidence. The coverage score is field-presence evidence only.
An append-only score audit records one ARM-A coverage-binding false positive (`HARD-FAIL-003`): the
observation's three claimed files exactly match the authoritative attempt's `files_written`, while
the coverage-only call lacked that binding. Original score bytes are retained; formal hard Gates
must use the authoritative attempt/process/oracle records.

## Cost and checkpoint

- Observed input/output tokens: 532,989 / 27,845
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`, not zero
- Total elapsed: 633.072039 seconds; average per primary record: 211.024013 seconds
- Input/output average per primary record: 177,663 / 9,281.666667
- Evidence storage at measurement: recorded in the hash-bound cost record
- Queue delay / runner CPU: `UNKNOWN` / `UNKNOWN`; replay CPU: `NOT_RUN`
- Monetary cost: `UNKNOWN`; API key/API billing: false / false
- Cost hash: `2afad1f7b33e1637b976fe1984e1397adff801514a706127160e1d95efadc8bd`
- Score-audit hash: `1c24743d07a42df52ec4c02ef74fe90d83ff79029dd8d31fa17c9a1a79825d36`
- Attempt-ledger hash: `d8d1d52d93c09512bec0e8892bee19590a754919291ec0495181b94f36bfa1bd`
- Checkpoint hash: `aad2b9bbf4f8c13f6309c5cc344ac34fec7b9a6af297d5b3b9a83c60a5ea20ab`

Minima are not satisfied. No later block was started in this batch.
