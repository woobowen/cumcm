# Formal adjudication execution

Formal technical adjudication is a strict six-role external chain:

1. Correctness Judge
2. Scientific Validity Judge
3. Engineering/Reproducibility Judge
4. Blind Dissent Judge
5. Evidence Meta-Adjudicator
6. Decision Auditor

The first three Judges cannot see candidate identities, peer outputs, historical recommendations,
Dissent, Meta expectations, human preferences, or orchestrator preferences. Blind Dissent cannot
see the first three outputs. Meta starts only after four valid blind outputs. Auditor starts only
after Meta and all required Schema-valid decisions. The orchestrator and in-process collaborators
cannot substitute for a formal role.

## Inputs and validation

Each role receives a deterministic role-specific evidence bundle derived from the frozen manifest.
Bundles preserve evidence IDs and hashes, numerical results, hard Gates, every BLOCKER, unresolved
Dissent, recovery exclusion, and licensing/contamination limits. They exclude identities, raw
third-party content, raw transport traces, private paths, and peer-role results. Size limits fail
closed; arbitrary truncation is prohibited.

After each role, validate output Schema, identity blindness, evidence references, frozen policy and
artifact hashes, configured model/reasoning, output hash, checkpoint, and absence of majority-vote
or human technical-gate logic. Only then append the ledger and unlock the next role.

## Decision semantics

Meta applies the frozen lexicographic policy and may accept, reject, request retest, declare
evidence insufficient, or abstain. It must not change thresholds or count role votes. Auditor
independently checks evidence use, identity separation, recovery exclusion, policy application,
scope, unsupported claims, contamination, and replayability. Only Auditor `PASS` permits the main
agent to update formal technical state.

Missing any role, Meta, Auditor, required decision, or replay is
`AUTOMATED_ADJUDICATION_INCOMPLETE`, not an implicit rejection or abstention. Phase 003 remains
prohibited unless the complete audited result and transition gates explicitly allow it.

## Phase 002B outcome

Phase 002B used `gpt-5.6-sol` with `medium` reasoning uniformly under ADR-0019. Correctness initial
exec and its only exact-session resume both ended in `RESPONSES_CONNECT_RESET`; the role exhausted
its two-start limit. The remaining five roles and replay were not run. No automated decision exists.
