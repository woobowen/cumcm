# Phase 004B Timing and Cost

## Captured modeling execution

| Activity | Execution type | Captured model seconds | Result | Evidence |
| --- | --- | ---: | --- | --- |
| RC2 answer-sealed first run | six controlled subprocesses | 16.960106 | 0 success, 6 failed and retained | first-run timing SHA `094c939b...` |
| RC3 2020 A clean regression | six controlled subprocesses | 20.771908 | 6 success, 6 sealed | RC3 regression aggregate |
| RC3 2023 C cross-case replay | three controlled subprocesses | 99.848352 | 3 success, 3 sealed | cross-case aggregate |
| Stress A | two controlled subprocesses | 2.909511 | 2 success, 2 sealed | Stress A captures |
| Stress B | two controlled subprocesses | 3.107736 | 2 success, 2 sealed | Stress B captures |
| Stress C | two controlled subprocesses | 2.994779 | 2 success, 2 sealed | Stress C captures |

The first-run five-hour limit was not approached. Exact preparation-stage durations were not
instrumented and remain unknown; they are not reconstructed from narrative timestamps. First-run
manual interventions and recoveries are both recorded as zero. Post-freeze Development work had
one excluded v1 regression for missing downstream output fields and one 2023 C command correction
before subprocess start; neither was erased or counted as a successful formal result.

No paid API, model training, fine-tuning, commercial solver or third-party code execution was used.
Monetary cost is `UNKNOWN`, not asserted zero. Existing `.venv` and ignored `libarchive-tools` were
retained; no package was installed or upgraded.

## Verification ledger

Final verification commands, exits, durations and evidence hashes are appended only after actual
execution. Current status: `FINAL_VERIFICATION_PENDING`.
