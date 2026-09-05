# Phase 004C4 historical and auxiliary regression

The binding record is `evals/results/phase-004c4/historical_and_auxiliary_regressions.json`,
SHA-256 `f15a7df4171fc7e6f6eceb8f7b4a5f58c7381eeb7c297685f73dcc21bbb033cc`.

| Case/suite | Result | Scope |
|---|---|---|
| 2020 C | PASS | 6 requirements, 3 preserved Runs |
| 2021 C | PASS | 17 requirements, 3 preserved Runs |
| 2022 C | PASS | 13 requirements, 3 preserved Runs |
| 2023 C | PASS | 6 requirements, 3 preserved Runs |
| 2020 A auxiliary | PASS | 6 requirements, 3 Runs, one failed Run retained |
| 2019 C diagnostic | PASS read-only | Q2 insufficiency/preflight and policy-exposure limitations preserved; verdict unchanged |
| 2024 C diagnostic | PASS read-only | six Claim mappings and aggregate diagnostic preserved; no retrospective credit |
| synthetic E2E | 2/2 PASS | prediction and optimization reach handoff |
| original negatives | 30/30 PASS | zero exceptions and zero sensitive emissions |
| focused regression | 239/239 PASS | output preflight, Claim/aggregate, execution, state and controller matrices |

The replay produced zero new historical model Runs and zero historical mutations. RC4/RC5/RC6
negative outcomes remain unchanged. Formal Skill count is one; hardcoding, answer-leakage, secret,
third-party-execution and 2025-access counts are all zero.
