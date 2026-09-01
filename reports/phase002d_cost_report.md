# Phase 002D cost report

- Batch: `5`
- Attempts / primary eligible / failed: 24 / 17 / 6
- Primary-eligibility success rate: 0.708333
- Oracle PASS / FAIL among eligible records: 9 / 8
- Input / output tokens: 4703413 / 232395
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 5305.1635 seconds
- Retries / infrastructure failures / operator interventions: 0 / 0 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 643743 bytes in 184 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 8 | 4 | 4 | 2503683 | 94904 | 1984.478126 |
| ARM-B | 8 | 7 | 3 | 992314 | 70823 | 1587.221685 |
| ARM-C | 8 | 6 | 3 | 1207416 | 66668 | 1733.463689 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `0f0e0f56794d2fe8d8209087f5a9b0ae11d2653bb0b70d5faead544f5fd50b8e`.
