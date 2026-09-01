# Phase 002D cost report

- Batch: `1`
- Attempts / primary eligible / failed: 3 / 3 / 0
- Primary-eligibility success rate: 1.0
- Oracle PASS / FAIL among eligible records: 1 / 2
- Input / output tokens: 532989 / 27845
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 633.072039 seconds
- Retries / infrastructure failures / operator interventions: 0 / 0 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 174597 bytes in 39 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 1 | 1 | 1 | 323805 | 12392 | 268.726587 |
| ARM-B | 1 | 1 | 0 | 98386 | 9570 | 214.176884 |
| ARM-C | 1 | 1 | 0 | 110798 | 5883 | 150.168568 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `2afad1f7b33e1637b976fe1984e1397adff801514a706127160e1d95efadc8bd`.
