# Neutral Claim tests

Expectations frozen at `4a194b012bcf59e900552af8c75393a843ce13a8` before implementation.
RC4: 32 failed / 8 passed. Revision 1: 40 passed; no expectation changes.

| Case | Expected | Actual | Reason code | Result |
|---|---|---|---|---|
| single | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| two_scopes | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| six_scopes | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| claim_order | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| support_order | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| different_statement | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| same_statement | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| missing | BLOCK | BLOCK | RC_CLAIM_PRIMARY_REQUIREMENT_MISSING | PASS |
| duplicate | BLOCK | BLOCK | RC_CLAIM_PRIMARY_REQUIREMENT_DUPLICATE | PASS |
| unknown | BLOCK | BLOCK | RC_CLAIM_PRIMARY_REQUIREMENT_UNKNOWN | PASS |
| optional_missing | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| optional_as_primary | BLOCK | BLOCK | RC_CLAIM_AGGREGATE_COVERAGE_INVALID | PASS |
| output_hash | BLOCK | BLOCK | RC_CLAIM_OUTPUT_BINDING_MISMATCH | PASS |
| manifest_hash | BLOCK | BLOCK | RC_CLAIM_MANIFEST_HASH_MISMATCH | PASS |
| decision_hash | BLOCK | BLOCK | RC_CLAIM_FINAL_DECISION_BINDING_MISMATCH | PASS |
| stale | BLOCK | BLOCK | RC_CLAIM_EVIDENCE_STALE | PASS |
| superseded | BLOCK | BLOCK | RC_CLAIM_RUN_NOT_CURRENT_SUCCESS | PASS |
| failed | BLOCK | BLOCK | RC_CLAIM_RUN_NOT_CURRENT_SUCCESS | PASS |
| unsealed | BLOCK | BLOCK | RC_CLAIM_RUN_UNSEALED | PASS |
| contradiction | BLOCK | BLOCK | RC_CLAIM_CONTRADICTED | PASS |
| overreach | BLOCK | BLOCK | RC_CLAIM_AGGREGATE_SCOPE_OVERREACH | PASS |
| coverage_subset | BLOCK | BLOCK | RC_CLAIM_AGGREGATE_COVERAGE_INVALID | PASS |
| coverage_extra | BLOCK | BLOCK | RC_CLAIM_AGGREGATE_COVERAGE_INVALID | PASS |
| trace_order | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| file_order | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| first_changed | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| legacy_single | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| legacy_invalid | BLOCK | BLOCK | RC_CLAIM_PRIMARY_REQUIREMENT_MISSING | PASS |
| handoff_complete | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| handoff_missing | BLOCK | BLOCK | RC_CLAIM_PRIMARY_REQUIREMENT_MISSING | PASS |
| wrong_run | BLOCK | BLOCK | RC_CLAIM_RUN_BINDING_MISMATCH | PASS |
| coverage_order | PASS | PASS | RC_CLAIM_EXACT_SUPPORT_VALID | PASS |
| coverage_duplicate | BLOCK | BLOCK | RC_CLAIM_AGGREGATE_COVERAGE_INVALID | PASS |
| support_duplicate | BLOCK | BLOCK | RC_CLAIM_AGGREGATE_COVERAGE_INVALID | PASS |
| output_missing | BLOCK | BLOCK | RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING | PASS |
| output_mutation | BLOCK | BLOCK | RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING | PASS |
| final_lineage | BLOCK | BLOCK | RC_CLAIM_FINAL_RESULT_BINDING_MISMATCH | PASS |
| statement_overclaim | BLOCK | BLOCK | RC_CLAIM_FINAL_SCOPE_MISMATCH | PASS |
| uncaptured_claim | BLOCK | BLOCK | RC_CLAIM_OUTPUT_BINDING_MISMATCH | PASS |

The additional freeze-matrix check passed. Fixtures are synthetic unit contexts, not contest Runs.
No network, model call or historical raw input is used.
