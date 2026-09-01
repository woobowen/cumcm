# Phase 002D cost report

- Batch: `3`
- Attempts / primary eligible / failed: 15 / 14 / 0
- Primary-eligibility success rate: 0.933333
- Oracle PASS / FAIL among eligible records: 9 / 5
- Input / output tokens: 2739660 / 147675
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 3192.763951 seconds
- Retries / infrastructure failures / operator interventions: 0 / 0 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 492421 bytes in 125 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 5 | 4 | 4 | 1533695 | 62045 | 1286.344769 |
| ARM-B | 5 | 5 | 3 | 578758 | 45847 | 993.588628 |
| ARM-C | 5 | 5 | 3 | 627207 | 39783 | 912.830554 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `37657847724f963ae9afc714e9e67a00ea22b70843ded679da4a2d41e20dd96d`.
