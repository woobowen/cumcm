# Phase 002D cost report

- Batch: `7`
- Attempts / primary eligible / failed: 28 / 18 / 8
- Primary-eligibility success rate: 0.642857
- Oracle PASS / FAIL among eligible records: 9 / 9
- Input / output tokens: 5726854 / 272461
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 6228.480778 seconds
- Retries / infrastructure failures / operator interventions: 4 / 1 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 763511 bytes in 213 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 12 | 5 | 4 | 3527124 | 134970 | 2907.795404 |
| ARM-B | 8 | 7 | 3 | 992314 | 70823 | 1587.221685 |
| ARM-C | 8 | 6 | 3 | 1207416 | 66668 | 1733.463689 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `a9b97f479c53fe6b25ff9d3688ff3cb4e8e9b092161951a0be1a39972fb07d5f`.
