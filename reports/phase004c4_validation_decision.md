# Phase 004C4 fresh Validation decision

Decision: `DECISION-C-TARGET-VALIDATION-004C4`
Verdict: `C_TARGET_VALIDATION_FAILED`
Case: `CUMCM-2017-C-VALIDATION-003F`
Next route: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`

RC7 candidate/live release checks passed and the frozen Skill did not change. All three primary
requirements have scoped provided-empirical data. The baseline and both main candidates executed for
all three seeds; 9/9 Runs, manifests and independent recomputations pass. PER_REQUIREMENT development
selection and semantic/aggregate pre-final checks also pass.

PASS is nevertheless forbidden. The single actual controller invocation blocks at
`GATE_FINALIZATION`, emits `RC_GATE_EXECUTION_FAILED`, leaves the state `RUNNING`, does not access the
sealed test, and never invokes `GATE_HANDOFF`. The released execute interface cannot provide the
controller-required authorized `sealed_test_metrics_b64` field without changing frozen code/output
or adding an unplanned Run.

Non-compensable hard failures:

- HF14 — the selected-output/final execution contract is not operationally satisfiable;
- HF21 — no current, selected, final-test-validated Final Run/portfolio exists;
- HF23 — aggregate completion/handoff is not accepted and case state is not
  `READY_FOR_PAPER_HANDOFF`.

The post-freeze read-only integrity audit added
`HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION`: REQ2's semantic-support artifact claimed held-out-test
validity even though the selected output is `DEVELOPMENT_GROUPED_OOS`, records test access
`NOT_AUTHORIZED/0`, and sets `held_out_test_valid=false`. This challenge does not rewrite the frozen
decision; it independently reinforces that PASS was forbidden and adds a required 004C5
cross-binding repair.

There is also no final-test metric, accepted final Claim package or paper handoff. Strong
development metrics cannot compensate. The answer remains sealed, paper dispatch is false, the
terminal freeze prohibits another Validation Run, and later same-case work is Development only.

The terminal freeze file SHA-256 is
`984ccfe2616769020443c4f873303f9d5f584793f8b865e3c3b1e159d316559a`; payload hash is
`5f840eb821c8e58215f276baf0e2be86c122f13f55690800cf5ea7886437ccf1`; freeze commit/remote SHA is
`8bf82ebc56d00bbcfd756b9d3d2b77c7a35ffcd6`. The successor delivery receipt is commit
`2f3b5b8a5668f37194bc180daeaaf4475b57034e`.
