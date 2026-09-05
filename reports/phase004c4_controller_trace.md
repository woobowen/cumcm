# Phase 004C4 controller Gate traces

`gate-execution-trace/v1` records controller version/command, state before and after, authoritative
input hashes, ordered Gate identifiers and implementation entrypoints, per-Gate input/output hashes,
duration, reason codes, final disposition and a canonical trace hash. A trace is evidence of the
actual path, not a second state truth.

Neutral successful workspaces exercise this order:

1. `GATE_PROBLEM_REQUIREMENT` — `cumcm_case.validate_runtime_requirements`
2. `GATE_SOURCE_EVIDENCE` — `cumcm_case.validate_runtime_sources`
3. `GATE_DATA_SUFFICIENCY_PREFLIGHT` — `cumcm_case.validate_data_sufficiency_record`
4. `GATE_COMPARISON_SELECTION` — capture registry plus requirement selection
5. `GATE_RUN_ELIGIBILITY` — `cumcm_case.validate_runtime_run_eligibility`
6. `GATE_COMPATIBILITY_PORTFOLIO` — `cumcm_case.validate_runtime_selection_compatibility`
7. `GATE_SEMANTIC_CLAIM` — `cumcm_case.validate_runtime_semantic_claims`
8. `GATE_AGGREGATE_CLAIM` — `cumcm_case.validate_runtime_aggregate_mapping`
9. `GATE_FINALIZATION` — final/Claim checks plus selected-test payload validation
10. `GATE_HANDOFF` — `cumcm_case.validate_handoff`

The fresh 2017 trace is an intentional negative terminal observation. Its file SHA-256 is
`57ae4e788f0bfb30d53c2fa5343f2d9f49aa7707a6eb355fbc933ed5b71985da` and canonical trace hash is
`4271f4db556fab99e1342c1e3bc5893a083b85209de19cd707eb01de5f963574`. Gates 1–8 passed with bound
artifact hashes. Gate 9 blocked with `RC_GATE_EXECUTION_FAILED`; Gate 10 is absent because fail-closed
short-circuiting correctly prevented handoff. State before/after is the same
`cc5c81bc50d25a07425c242e49d595fb57556be235d2e20ece391d41f91fef80`, final disposition is BLOCK,
and sealed-test access count is zero.
