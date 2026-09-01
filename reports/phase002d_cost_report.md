# Phase 002D cost report

- Batch: `4`
- Attempts / primary eligible / failed: 21 / 17 / 3
- Primary-eligibility success rate: 0.809524
- Oracle PASS / FAIL among eligible records: 9 / 8
- Input / output tokens: 4254250 / 212711
- Cached input / reasoning tokens: UNKNOWN / UNKNOWN
- Total duration: 4849.330806 seconds
- Retries / infrastructure failures / operator interventions: 0 / 0 / 0
- Queue delay / runner CPU / replay CPU: UNKNOWN / UNKNOWN / NOT_RUN
- Evidence storage: 603013 bytes in 165 files
- Maintenance surface: 1545 lines in 12 frozen files
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
| ARM-A | 7 | 4 | 4 | 2231556 | 85723 | 1788.661885 |
| ARM-B | 7 | 7 | 3 | 891350 | 63542 | 1427.591739 |
| ARM-C | 7 | 6 | 3 | 1131344 | 63446 | 1633.077182 |

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `30538e0d6769e8d4f28f8655ab3cf65a8d2d468680ce71bcfd4efc2d5896921c`.
