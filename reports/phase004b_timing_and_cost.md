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

All logs below are ignored local artifacts. Hashes bind the exact captured stdout/stderr; failed
attempts are retained.

| Command | Exit | Wall seconds | Result | Log SHA-256 |
| --- | ---: | ---: | --- | --- |
| `ruff check .` | 0 | 0.026606 | PASS | `82b3e6a6...b4f18` |
| `ruff format --check .` | 0 | 0.036311 | PASS, 701 files formatted | `4fc39b54...9e7d` |
| Skill `quick_validate.py` | 0 | 0.024723 | PASS | `db349825...5bb0` |
| focused RC3/004B suite | 0 | 0.567219 | 28 passed | `687f4fb6...af79` |
| two synthetic E2E | 0 | 1.214700 | 2 passed | `f63ed36e...40a97` |
| 30-scenario negative gate | 0 | 0.243119 | 30/30 scenario PASS | `e596cce9...d7353` |
| contract checker | 0 | 0.640129 | 78 valid, 68 invalid rejected | `21460784...bf72` |
| instruction budget | 0 | 3.519532 | PASS, 6,833 bytes | `f6adcd9c...7e14` |
| Skill discovery | 0 | 0.077291 | one formal Skill | `b9d2ff4e...5f75` |
| answer leakage | 0 | 0.045464 | 0 findings | `d340485d...8d01` |
| secrets/private paths | 0 | 1.497234 | 0 / 0 findings | `4cc2305e...c897` |
| Competition consistency | 0 | 0.052756 | 37/37 checks | `e926b374...bdb5` |
| training consistency | 0 | 0.058128 | 0 errors | `3f70ec65...6d30` |
| strict, pre-doc commit | 1 | 2.911038 | self-reference rejected; corrected by commit ordering | `4987527a...611b` |
| strict, after doc commit | 0 | 2.888451 | 0 errors, 0 warnings | `8c7ffbff...198c` |
| full pytest attempt 1 | 1 | 133.777436 | 75 historical-hash regressions | `1194eb74...a9ad` |
| full pytest attempt 2 | 1 | 307.275459 | 1815 passed, 1 failed, 1 skipped | `29f129e7...666a` |
| full pytest attempt 3 | 0 | 306.609089 | 1816 passed, 1 skipped | `de7f60ba...9582` |
| `bash scripts/ci.sh` | 0 | 312.716023 | 1816 passed, 1 skipped; strict PASS | `396b2659...a463` |

Attempt 1 was caused by an unnecessary state-schema condition changing historical freeze hashes;
the schema was restored byte-for-byte. Remaining failures showed the historical compatibility
allowlist stopped at RC2; adding exact RC3 status/version support reduced attempt 2 to one stale
fault-test branch. The final exact RC3 branch assertion closed that last failure. This exhausted the
three permitted autonomous repair attempts and ended in PASS; no retry beyond the limit occurred.

GitHub `offline-validation` for content commit
`b4f35cafa4816d255e832ec86b8ff5a65aa2484b` passed in 6m21s (run `33872400050`). The job remained
offline with respect to official inputs and did not read ignored raw workspaces. Its only annotation
is a nonblocking hosted-runner Node.js 20 deprecation warning for pinned actions.
