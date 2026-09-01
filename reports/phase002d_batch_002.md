# Phase 002D Batch 2 checkpoint

## Execution result

- Frozen blocks: `BLOCK-002-CASE-001-R2`, then `BLOCK-003-CASE-002-R1`
- New attempts / completed / Schema-valid / process E2: 6 / 6 / 6 / 6
- New primary eligible / excluded: 5 / 1
- New oracle PASS / FAIL: 6 / 0
- Infrastructure failures / retries / manual interventions: 0 / 0 / 0
- Cumulative attempts / primary eligible: 9 / 8
- Balanced cases: `CASE-001`, `CASE-002`; global repeat depth: 0
- Next frozen attempt: `EXP-CASE-002-ARM-C-R2-A01`

| Block order | Arm | Attempt | Eligible | Oracle | Input | Output | Seconds |
|---:|---|---|---|---|---:|---:|---:|
| 1 | ARM-A | EXP-CASE-001-ARM-A-R2-A01 | no | PASS | 238417 | 10921 | 225.098311 |
| 2 | ARM-B | EXP-CASE-001-ARM-B-R2-A01 | yes | PASS | 113946 | 8698 | 178.916091 |
| 3 | ARM-C | EXP-CASE-001-ARM-C-R2-A01 | yes | PASS | 93134 | 4960 | 104.197607 |
| 4 | ARM-A | EXP-CASE-002-ARM-A-R1-A01 | yes | PASS | 210471 | 10260 | 207.753478 |
| 5 | ARM-C | EXP-CASE-002-ARM-C-R1-A01 | yes | PASS | 158652 | 10314 | 222.476847 |
| 6 | ARM-B | EXP-CASE-002-ARM-B-R1-A01 | yes | PASS | 117559 | 9247 | 200.461845 |

`EXP-CASE-001-ARM-A-R2-A01` is permanently retained but excluded. It wrote its claimed artifacts
under `.harness/`, which the frozen protocol reserves for runner-private output and excludes from
publishable `files_written`; authoritative `HARD-FAIL-003` and `NO_HARD_FAILURE` exclusion are
therefore correct. Oracle/process PASS cannot override that hard failure. No immediate retry was
allowed; the cell waits for its frozen retry-queue turn after the primary queue.

## Cumulative checkpoint and cost

- Observed input/output tokens: 1,465,168 / 82,245
- Cached-input/reasoning tokens: `UNKNOWN` / `UNKNOWN`
- Total elapsed: 1,771.976218 seconds
- Completion failures / infrastructure failures / retries: 0 / 0 / 0
- Remaining attempts/input/output/elapsed: 31 / 8,534,832 / 252,198 / 4,425.023782
- Oracle PASS / FAIL among eligible: 6 / 2
- Cost hash: `e065e64f25abc5ffced3f16a8d6e5d89bfd0557a9925223635cde45cc44c0ba1`
- Score-audit hash: `88ffff41b1eddd7b680145c2f216acf763876299f9386abae9fdae0585fe23bb`
- Attempt-ledger content hash: `0e81280047849919481da98412976ca3b699de456fa0bb073dc725a3b71a6057`
- Checkpoint content hash: `fd28bf15e4e81b3c5e5b604e4c1f5ddb7538e36d228857b4fdb3bee449352d99`

The score audit recomputes authoritative hard failures from complete attempt bindings and passes.
It isolates two older/current coverage-only false positives without modifying original scores.
Minima remain unsatisfied; Batch 3 is locked until this checkpoint is remotely delivered.
