# Phase 002D cost report

- Batch: `2`
- Attempts / primary eligible / failed: 9 / 8 / 0
- Primary-eligibility success rate: 0.888889
- Oracle PASS / FAIL among eligible records: 6 / 2
- Input / output tokens: 1465168 / 82245
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 1771.976218 seconds
- Retries / infrastructure failures / operator interventions: 0 / 0 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 332080 bytes in 82 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 3 | 2 | 3 | 772693 | 33573 | 701.578376 |
| ARM-B | 3 | 3 | 2 | 329891 | 27515 | 593.55482 |
| ARM-C | 3 | 3 | 2 | 362584 | 21157 | 476.843022 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `e065e64f25abc5ffced3f16a8d6e5d89bfd0557a9925223635cde45cc44c0ba1`.
