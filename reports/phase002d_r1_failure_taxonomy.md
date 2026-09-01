<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R1 failure taxonomy

Freeze: `PHASE-002D-R1-INPUT-FREEZE-001` / `4a03c2d840e0defff8df87a9dae68b76a3b9bbcec279e5298c971771ebe91c85`. All 28
source attempts are classified exactly once. Identity was not used.

| Primary classification | Count |
| --- | --- |
| ELIGIBLE_SUCCESS | 9 |
| HARNESS_CENSORED | 2 |
| INFRASTRUCTURE_CENSORED | 1 |
| SUPERSEDED | 0 |
| TERMINAL_MODEL_SCHEMA_FAILURE | 0 |
| TERMINAL_POLICY_FAILURE | 7 |
| TERMINAL_UNSUPPORTED_CLAIM_FAILURE | 0 |
| UNKNOWN_CENSORED | 0 |
| VALID_OUTPUT_ORACLE_FAIL | 9 |

`HARD-FAIL-003` is an observed unsupported-claim policy failure only when authoritative runner
evidence attributes it to the candidate output. Harness false positives stay censored. Failures are
categorical outcomes, never numeric zeroes.
