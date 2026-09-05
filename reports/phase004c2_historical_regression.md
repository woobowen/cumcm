# Historical artifact regression

All original numerical Runs are replay-verified with their hash-bound original Git kernel; RC5 checks the derived Claim/handoff. No new numerical Runs or independent Validation credit.

| Case | Original state | Requirements | Runs retained | Claim | Handoff | Source unchanged |
|---|---|---:|---:|---|---|---|
| CUMCM-2020-C-DEVELOPMENT-RC4-REGRESSION | READY_FOR_PAPER_HANDOFF | 6 | 3 | PASS | PASS | True |
| CUMCM-2021-C-DEVELOPMENT-RC4-REGRESSION | READY_FOR_PAPER_HANDOFF | 17 | 3 | PASS | PASS | True |
| CUMCM-2022-C-DEVELOPMENT-RC4-REGRESSION | READY_FOR_PAPER_HANDOFF | 13 | 3 | PASS | PASS | True |
| CUMCM-2023-C-DEVELOPMENT-RC4-REGRESSION | READY_FOR_PAPER_HANDOFF | 6 | 3 | PASS | PASS | True |
| CUMCM-2020-A-RC4-AUXILIARY-REGRESSION | READY_FOR_PAPER_HANDOFF | 6 | 3 | PASS | PASS | True |

Two fresh synthetic E2E reached READY_FOR_PAPER_HANDOFF; original 30 negatives passed with zero exceptions. Existing RC4 preflight tests pass. The unchanged execution/capture/seal/manifest/comparison/final/robustness/preflight functions are AST-verified in anti_hardcoding.json.

Earlier harness code/version-context failures and the native structured-formula handoff rejection remain recorded. The old report filename collision was resolved with a commit-versioned report; no source artifact was overwritten.
