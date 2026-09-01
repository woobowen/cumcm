# Automated Adjudication Dossier

Phase 002 produced candidate dynamic runs; Phase 002A rebuilt deterministic evidence classification; Phase 002B preserved 2 `RESPONSES_CONNECT_RESET` recovery failures and transport-repaired is `False`; Phase 002C recorded `EVIDENCE_INSUFFICIENT` through an evidence-sufficiency short circuit; semantic Judges are `SKIPPED`.

Technical status: `AUTOMATED_ADJUDICATION_COMPLETE`.
Evidence sufficiency: `INSUFFICIENT`; balanced cases 2/4; repeats 1/2.
Decision audit: `PASS`; deterministic replay: `True`.
Next phase allowed: `PHASE-EVIDENCE-EXPANSION-002D`. Phase 003 allowed: `False`. Phase 002D started: `False`.
Selected architecture: `None`; third-party integrated: `False`; Skill capability: `SCAFFOLD_ONLY`.
Phase 002B transport repaired: `False`. Preserved recovery attempts: 2 with `RESPONSES_CONNECT_RESET`; nested Codex used: `False`; API key used: `False`.

## Native audits

| Role | Model | Reasoning | RO | Peer view | Output hash | Findings | Blockers | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_sufficiency_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | 1de280d35e959ce355d9840e09b0de8096053a50913b26bd0b97693c9c60478e | 8 | 0 | PASS |
| adjudication_policy_prosecutor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | 5ee12808550468ef78aaa4d447233f2a860c284fbf796b4bf7d9ad06e40738d6 | 9 | 0 | PASS |
| dissent_and_cost_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | df3347aa5a338e6067161b53d423b7a54b90bee5a17977992d7d3e14565d9e71 | 5 | 0 | PASS |
| reproducibility_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | 447a38914de3bea6a0d3e6c711a5dce6af865c3c7203ab0bc91fd37aaea3c8ca | 10 | 0 | PASS |
| automated_decision_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | FROZEN_PREDECESSORS_ONLY | f81d9f46553955f02c7de88f7fff3adc3c5a40ac1cc3cd745a0c0dd7570dcde1 | 7 | 0 | PASS |

## Decisions

| Decision ID | Type | Target | Decision | Scope | Sufficiency | Audit | Next phase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DECISION-COMPONENT-READINESS-002C | COMPONENT_READINESS | accepted-versus-done-workflow-state, claim-evidence-support-gate, hash-bound-reproducibility-manifest, leakage-safe-model-comparison-gate | EVIDENCE_INSUFFICIENT | NONE | INSUFFICIENT | DECISION-AUDIT-002C | None |
| DECISION-DIRECT-UPSTREAM-ADOPTION-002C | DIRECT_UPSTREAM_ADOPTION | HANDSOMEZR_WHOLE_PACKAGE, YUSHUI_WHOLE_PACKAGE | AUTOMATED_REJECTED | NONE | INSUFFICIENT | DECISION-AUDIT-002C | None |
| DECISION-EVIDENCE-SUFFICIENCY-002C | EVIDENCE_SUFFICIENCY | ARCHITECTURE_SELECTION, COMPONENT_COMBINATION_SELECTION | EVIDENCE_INSUFFICIENT | NONE | INSUFFICIENT | DECISION-AUDIT-002C | PHASE-EVIDENCE-EXPANSION-002D |
| DECISION-RECOVERY-POLICY-002C | RECOVERY_POLICY | RECOVERY_AFFECTED_EVIDENCE_USAGE | AUTOMATED_ACCEPTED | POLICY_ONLY | SUFFICIENT | DECISION-AUDIT-002C | None |

## Integrity

Input freeze: `cc6397b0aea83d910105b15c5fb2f701ac4ff4def2858deb55c283d7cc396aa9`; evidence: `19f5bf98cd1337763a415e086121bdf73b4d92ffa1f6d0ac74ba49d1c058029c`; report inputs are machine records only.
