# 2024 C One-Shot Validation

## Frozen setup

Case `CUMCM-2024-C-VALIDATION-001` was verified from the official archive as
“农作物的种植策略”. Its problem, two data workbooks, and three output templates are hash-bound; the
answer and all solution/reference material remained `SEALED`. The pre-run freeze bound RC4
`0.2.0-competition-rc4`, release commit `46e13d31a3d22fe12a2cffe65a52558da3ecfa82`, Skill tree
`d041ca38de030ae04813ef02dbe12f7f2b7a1c22`, Python 3.11.14, 35 distributions, a 25-metric rubric,
12 hard failures, 14 stages, and a 4-hour limit. A fresh isolated worker could read only the frozen
Skill/protocol/rubric, official 2024 C inputs, and generic domain sources.

Pre-result model code SHA-256 is
`4602b194d44a9888e0ddef031bb29066c1fec35ce14678ca03a0a9aac59f9b6b`, bound at commit
`f12aa707cdf756c657dde0d69556b9f575b748ed`. RC4 was not modified.

## Actual execution and selection

The frozen grid had `BASELINE_RULE_ROTATION` and `PRIMARY_RISK_GREEDY`, seeds 104729 and 130363.
All four Runs executed and sealed exactly once; all returned `SUCCESS`; retry, recovery,
result-driven edit, and run-phase manual intervention counts are zero. The baseline aggregate
validation score was `110079957.9191615`; primary was `169264118.00319`, so the frozen maximize
rule selected `PRIMARY_RISK_GREEDY` and Run `RUN-PRIMARY_RISK_GREEDY-104729`. Test access was
authorized once after selection and was not used for selection.

All six rubric requirements passed the independent output audit. Four selected-plan feasibility
records have zero violations. All three selected workbooks preserve official sheet structure. Q1,
Q2, Q3, constraints, and management assumptions are covered, and three quantitative robustness
perturbations are present.

## Terminal Gate

Final reached `FINAL_CANDIDATE`. The Claim proposal precisely binds the selected manifest, output,
decision, all six unique requirement Claim IDs, comparison, robustness, and Final. Nevertheless,
the frozen validator requires top-level `claim_text`/`supported_scope` to equal both:

1. the global Final scope; and
2. the first requirement's Q1-waste-specific claim text.

Those immutable strings differ. Independent `claim-check` and `validate --check` calls each exited
3 with only `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`. The case therefore entered
`REJECTED`; Claim evidence is not formally complete and handoff was not reached. Numeric success
cannot compensate for this Gate.

## Decision and freeze

Decision `DECISION-C-TARGET-VALIDATION-004C` is
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`. No rubric hard failure was observed, but two mandatory
pass conditions—Claim evidence and handoff completeness—failed. Terminal freeze payload SHA-256 is
`d53c4280f09b369c4ab09a66c6bbba454c8b739e710f21f7481a375454523033`; freeze file SHA-256 is
`6e78a9c047b0c2673c17c1e9b055dfa342f681ca5aa86c7b789929aadd138373`; remote freeze commit is
`197f62bc75ebe832e9dd3ced0306740f336b80d6`. The terminal freeze occurred 3219 seconds after the
registry start, within 14400 seconds. No new Validation Run is permitted; same-case future work is
Development only.
