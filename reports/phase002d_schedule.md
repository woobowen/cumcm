# Phase 002D frozen schedule

- Schedule/seed/hash: `PHASE-002D-BLOCKED-SCHEDULE-001` / 20260901 / `5d0351aa4e00885131aedfefdbaa8e311cf2c299652a38f42f6ecad762c045aa`
- Mode/cohort: `NEW_MODEL_COHORT` / `PHASE-002D-NEW_MODEL_COHORT-GPT-5-6-SOL-MEDIUM`
- Blocks / primary slots / retry slots: 8 / 24 / 48
- Cases/arms/repeats: CASE-001, CASE-002, CASE-004, CASE-006 / ARM-A, ARM-B, ARM-C / 2

| Block | Case | Repeat | Frozen arm order |
|---:|---|---:|---|
| 1 | CASE-001 | 1 | ARM-C, ARM-A, ARM-B |
| 2 | CASE-001 | 2 | ARM-A, ARM-B, ARM-C |
| 3 | CASE-002 | 1 | ARM-A, ARM-C, ARM-B |
| 4 | CASE-002 | 2 | ARM-C, ARM-B, ARM-A |
| 5 | CASE-004 | 1 | ARM-A, ARM-C, ARM-B |
| 6 | CASE-004 | 2 | ARM-C, ARM-B, ARM-A |
| 7 | CASE-006 | 1 | ARM-A, ARM-C, ARM-B |
| 8 | CASE-006 | 2 | ARM-A, ARM-B, ARM-C |

All 24 primary slots ran before the frozen retry queue. No immediate or identity-aware reorder occurred.
