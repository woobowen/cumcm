# Phase 002D cost report

- Batch: `6`
- Attempts / primary eligible / failed: 27 / 18 / 8
- Primary-eligibility success rate: 0.666667
- Oracle PASS / FAIL among eligible records: 9 / 9
- Input / output tokens: 5498280 / 261169
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 5988.297082 seconds
- Retries / infrastructure failures / operator interventions: 3 / 1 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 720254 bytes in 205 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 11 | 5 | 4 | 3298550 | 123678 | 2667.611708 |
| ARM-B | 8 | 7 | 3 | 992314 | 70823 | 1587.221685 |
| ARM-C | 8 | 6 | 3 | 1207416 | 66668 | 1733.463689 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `4ac9dfc5a1a394052e12c2d532101a18aa2ee2bfa3c7db083127d15a9b95ef12`.
