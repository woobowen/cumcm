<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2 interaction contract

Contract `PHASE-002D-R2-COMPONENT-INTERACTION-001` is `SPECIFICATION_FROZEN` at hash
`7625f36e18a52777ba85155c3a34b18525ae831ffe548669d4eede3e6b92e7ab`. State truth remains `state/project_state.json`; formal Skill
count remains `1`.

| Producer | Consumer | From type | To type |
| --- | --- | --- | --- |
| hash-bound-reproducibility-manifest | claim-evidence-support-gate | SOURCE_RUN_MANIFEST | CLAIM_REVISION |
| hash-bound-reproducibility-manifest | leakage-safe-model-comparison-gate | SOURCE_RUN_MANIFEST | COMPARISON_EXECUTION |
| claim-evidence-support-gate | accepted-versus-done-workflow-state | CLAIM_REVISION | STATE_PROPOSAL |
| leakage-safe-model-comparison-gate | accepted-versus-done-workflow-state | DECISION | STATE_PROPOSAL |

All edges require artifact SHA-256, immutable revision/prior-hash binding, currentness and Decision
Audit. The six-rank failure-precedence table is noncompensatory; no component advances formal state
directly and no competing Run, Claim, comparison or project-state truth is created.
