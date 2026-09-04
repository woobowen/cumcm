# C-Target RC4 Unified Regression

## Result

The RC4 release regression passed every preregistered scope before the 2024 C one-shot began. The
machine record is `evals/results/phase-004c-c-batch/rc4/unified_regression_evidence.json`.

| Scope | Actual evidence | Result |
| --- | --- | --- |
| 2022 C Development regression | 3/3 successful Runs, all 14 stages | PASS |
| 2021 C Development regression | 3/3 successful Runs, feasible baseline, all 14 stages | PASS |
| 2020 C Development regression | 3/3 successful Runs, all 14 stages | PASS |
| Preserved 2023 C main chain | 3 Runs, handoff and STALE probe | PASS |
| 2020 A auxiliary executor | 2 successful + 1 retained exit-23 failure; success-only selection | PASS, no C credit |
| Synthetic prediction E2E | 2 Runs to handoff | PASS |
| Synthetic optimization E2E | 3 Runs to handoff | PASS |
| Original negative matrix | 30/30 rejected as expected | PASS |
| New output-contract neutral faults | case-neutral preflight and execute checks | PASS |

The three batch regressions had 9/9 valid Runs, no failed Run, and no universal hard failure. The
2023 C and 2020 A scopes are compatibility evidence, not fresh C Validation. The auxiliary A run
demonstrates nonzero-failure retention and success-only selection but receives zero C-target
generalization credit.

The release gate recorded one formal Skill, answer leakage 0, secrets 0, third-party execution 0,
two synthetic E2E passes, 30 negative passes, and full CI `1865 passed, 1 skipped`. RC4 was then
frozen without further mutation for the independent 2024 C run.

## Preserved failures

Pre-success development attempts remain evidence: 2022 RC4 attempt 1 stopped at handoff formula
shape; 2020 C attempt 1 omitted a plan extension; 2020 A attempts exposed test-access and Claim
binding errors. They were not counted as the clean final regression chains. No failure was erased,
and no Validation outcome was inferred from Development regression success.
