# 004C2 Validation decision

`DECISION-C-TARGET-VALIDATION-004C2`: `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`.
Controlling reason: `VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING`.

The frozen priority adjudicator first checks Skill/answer/episode boundary and uncompensable
model failures, then primary empirical coverage, then the complete native pipeline. All 9 actual
Runs and native gates pass; no detected uncompensable model failure is offset by scores.
Q2 empirical completion is false. Native scoped Claims include a truthful missing-evidence finding;
they do not make Q2 complete. The terminal state is REJECTED; canonical native handoff is retained
as conditional diagnostic evidence with paper_dispatch_accepted=false. Next phase is null.

Decision SHA256: `62b04b3654de11f95f1df12fb2bd0dfcad31d7901b192f68f33f062cb4adf588`.
Machine truth: `evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002/validation/`.
Uncertainty includes unverified model prior, assumption-only demand/fare/geometry, policy-only test
isolation, Q1-only tied ranking, conditional simulation intervals and adverse Q4 fairness.

Revision 1 is preserved byte-for-byte in decision_history. Revision 2 records incomplete selected
Q4 semantic support and the RC5 VERSION-file mismatch. Native structural flags are retained
separately; semantic requirement_claims_valid and handoff_valid are false. Verdict is unchanged.
Release acceptance is BLOCKED_VERSION_METADATA with unresolved RC5_VERSION_FILE_MISMATCH.
