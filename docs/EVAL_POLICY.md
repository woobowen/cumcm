# Evaluation policy

Historical Phase 002 compared a no-Skill baseline and two sanitized candidates on six synthetic
development tasks. Its lexical score is `STRUCTURED_COVERAGE_ONLY`, never correctness. Phase 002A
separately computes deterministic oracle correctness and process evidence. Only primary complete
cells enter comparison; failed and recovery-affected cells remain visible but cannot affect rank.
Balanced-case and repeat minima are computed from data. The engine may report insufficient evidence
or abstain, and validation/held-out results remain unavailable for direct tuning.

Phase 002D uses only its selected new cohort for primary minima. Fresh retries may fill missing
cells but do not add repeat depth for the same repeat ID. Oracle outcome is separate from eligibility;
failed, hard-failed, recovered, cross-model and `NOT_RUN` records stay visible but cannot fill.

Phase 002D-R1 does not reopen acquisition. It treats terminal failures as observed outcomes,
preserves all attempts in reliability/cost, selects the earliest oracle-passing eligible record for
quality and forbids best-of-N. Terminal negatives may resolve completeness or repeated gap evidence
but never fill quality. See `FAILURE_AWARE_EVIDENCE_POLICY.md`.
