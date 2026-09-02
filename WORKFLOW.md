# Formal state machine

This is the sole normative lifecycle. Technical gates are automated, evidence-first, lexicographic,
and non-voting. Humans record `TEAM_COMPLIANCE_REVIEW` or submit evidence-backed challenges; they
cannot select a model, architecture, or component and cannot override technical rejection.

## Automated adjudication lifecycle

| State | Required evidence/check | Allowed next | Failure/uncertainty |
|---|---|---|---|
| `CANDIDATES_FROZEN` | candidate set, policy hash, evidence freeze | `PRE_ADJUDICATION_EVIDENCE_GATE` | `STALE` |
| `PRE_ADJUDICATION_EVIDENCE_GATE` | freeze integrity, target hard Gates, primary eligibility, balanced complete cases, independent repeats | `ADVERSARIAL_REVIEW_COMPLETE` only when comparison is sufficient; otherwise audited terminal decision | `EVIDENCE_INSUFFICIENT`, `AUTOMATED_REJECTED`, or `STALE` |
| `ADVERSARIAL_REVIEW_COMPLETE` | six independent attack roles; no result sharing | `TESTS_SYNTHESIZED` | `AUTOMATED_ADJUDICATION_INCOMPLETE` |
| `TESTS_SYNTHESIZED` | each BLOCKER/ERROR has test request or non-testable marker | `EVIDENCE_EXECUTED` | `RETEST_REQUIRED` |
| `EVIDENCE_EXECUTED` | deterministic test evidence; recovery excluded from rank | `BLIND_ADJUDICATION_COMPLETE` | `EVIDENCE_INSUFFICIENT` |
| `BLIND_ADJUDICATION_COMPLETE` | three identity-blind Judges and independent Dissent | `META_ADJUDICATION_COMPLETE` | `AUTOMATED_ADJUDICATION_INCOMPLETE` |
| `META_ADJUDICATION_COMPLETE` | frozen policy applied without votes or threshold change | `DECISION_AUDIT_COMPLETE` | `AUTOMATED_ABSTAINED` |
| `DECISION_AUDIT_COMPLETE` | independent Auditor validates evidence, rules, replay, identity, recovery | decision terminal | `STALE` |
| `AUTOMATED_ACCEPTED` | all target-specific hard gates and sufficiency rules pass | eligible next phase only if transition policy passes | `STALE` |
| `AUTOMATED_REJECTED` | hard gate or verified counterexample fails | new frozen plan | `STALE` |
| `RETEST_REQUIRED` | registered experiment can resolve the gap | `EVIDENCE_EXECUTED` | `STALE` |
| `EVIDENCE_INSUFFICIENT` | balanced-case/repeat/evidence minimum fails | new frozen evidence plan | `STALE` |
| `AUTOMATED_ABSTAINED` | conflict, instability, or unresolved blocker prevents decision | new frozen evidence plan | `STALE` |
| `STALE` | dependency or supported challenge changed | earliest valid predecessor | remain `STALE` |

The nominal acceptance path is:

`CANDIDATES_FROZEN → PRE_ADJUDICATION_EVIDENCE_GATE → ADVERSARIAL_REVIEW_COMPLETE → TESTS_SYNTHESIZED → EVIDENCE_EXECUTED → BLIND_ADJUDICATION_COMPLETE → META_ADJUDICATION_COMPLETE → DECISION_AUDIT_COMPLETE → AUTOMATED_ACCEPTED`.

The pre-adjudication Gate is deterministic and non-voting. It does not change thresholds. When a
frozen balanced-case or repeat minimum fails, candidate-quality semantic Judges and ranking are
skipped; independent attacks and Decision Audit validate the deterministic
`EVIDENCE_INSUFFICIENT` record, which may route only to a new frozen evidence-expansion plan. A
target-specific mandatory hard Gate may similarly produce `AUTOMATED_REJECTED` without asking a
semantic Judge to average it away.

Transport recovery does not create a lifecycle shortcut. Resume uses the exact recorded
session/thread and unchanged role inputs; an eligible fallback Adapter still consumes the same
versioned per-role/global budget. Exhausted budget, missing role output, or broken checkpoint yields
`AUTOMATED_ADJUDICATION_INCOMPLETE` and locks all dependent roles. Remaining global starts do not
override a per-role limit. See `docs/TRANSPORT_RECOVERY_POLICY.md`.

Phase 003 additionally requires an accepted architecture, Auditor `PASS`, at least one accepted
`SPECIFICATION_ONLY` component, no unresolved hard gate/BLOCKER, stable replay, and clean CI. This
phase never starts merely because a plan or report recommends it.

## Phase 002D evidence-expansion route

`PILOT_PASS → COHORT/BUDGET/SCHEDULE_FROZEN → BATCHED_PRIMARY/RETRY_EVIDENCE →
PRE_ADJUDICATION_EVIDENCE_GATE`. Meeting four balanced cases and two independent repeats unlocks
native semantic audits. Budget exhaustion before those minima yields
`EVIDENCE_EXPANSION_INCOMPLETE`, permits only a newly frozen continuation of the same Phase 002D and
keeps Phase 003 locked. It does not create automated decisions or a Decision Auditor output.

## Phase 002D-R1 failure-aware outcome-adjudication route

`EVIDENCE_EXPANSION_INCOMPLETE → FAILURE_AWARE_ADJUDICATION_IN_PROGRESS` is a registered
continuation inside Phase 002D, not a new formal Phase and not renewed generic acquisition. It
freezes the completed Phase 002D attempts and resolves eligible success, terminal negative,
infrastructure censoring, harness censoring, and unknown outcomes under separate quality,
reliability, outcome-completeness, and component-gap scopes. While this status is active,
`subphase` is `PHASE-002D-R1-FAILURE-AWARE-OUTCOME-ADJUDICATION`, `next_phase_allowed` is null,
architecture and accepted components remain unset, base selection and third-party integration are
false, and the Skill remains `SCAFFOLD_ONLY`.

The legal `technical_adjudication_status` enum and its state invariants are machine-owned by
`contracts/project_state.schema.json`; the versioned
`rules/phase002d_r1_workflow_rules.yaml` owns R1 transition edges without mutating the Phase 002D
freeze-bound global workflow policy. Only a passing failure-aware Decision Auditor and stable
replay may establish a terminal R1 status. Neither an in-progress label nor completion of
deterministic preprocessing is an automated technical decision.

`FAILURE_AWARE_ADJUDICATION_IN_PROGRESS → FAILURE_AWARE_ADJUDICATION_COMPLETE` requires all 28
attempt classifications, the 24-slot matrix, separate evidence scopes, retry audit, five first-round
audits with test-bound serious findings, supplemental decision, seven automated decisions,
Decision Auditor PASS and stable five-variant replay. Completion may retain
`EVIDENCE_INSUFFICIENT` quality and route only to `PHASE-EVIDENCE-EXPANSION-002D`; it does not imply
architecture selection or Phase 003 eligibility.

## Phase 002D-R2 clean-room specification and prospective-protocol route

`FAILURE_AWARE_ADJUDICATION_COMPLETE → SPECIFICATION_PROTOCOL_IN_PROGRESS` is a bounded Phase 002D
continuation authorized only by the four R1 `SPECIFICATION_ONLY` component decisions. R2 freezes
project-authored component and interaction contracts, a two-to-three-arm architecture candidate set
including retain-scaffold, a prospective synthetic Benchmark, hidden-seed metadata, metrics,
pre-implementation thresholds, ablations and a later shadow-prototype protocol. It does not
implement a component, modify the formal Skill, select an architecture or execute an experiment.

`SPECIFICATION_PROTOCOL_IN_PROGRESS → SPECIFICATION_PROTOCOL_COMPLETE` requires immutable historical
inputs, passing component/interaction/candidate/Benchmark/threshold/embargo decisions, test-bound
serious findings, an independent Decision Auditor PASS and stable offline replay. Completion does
not require prototype authorization. If and only if that separate authorization is accepted at
`EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY`, the next route may be
`PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`; otherwise it is R2 or null. Architecture remains null,
the Skill remains `SCAFFOLD_ONLY`, and Phase 003 stays locked.

## Project lifecycle

`INIT → FOUNDATION_READY → UPSTREAMS_INVENTORIED → UPSTREAMS_STATIC_REVIEWED → CANDIDATES_FROZEN`
then follows automated adjudication. Later Skill development, validation, held-out evaluation, and
contest release each require their machine contracts, frozen inputs, executable tests, independent
review evidence, and an audited automated decision. Missing evidence yields `RETEST_REQUIRED`,
`EVIDENCE_INSUFFICIENT`, `AUTOMATED_ABSTAINED`, or `STALE`; no state requires a subjective human
technical gate.

## Contest-run lifecycle

`PROBLEM_INGESTED → PROBLEM_ANALYZED → DATA_VALIDATED → BASELINE_READY → MODEL_CANDIDATES_READY → MODEL_SELECTED → IMPLEMENTED → PILOT_RUN_READY → EXPERIMENTS_RUNNING → VALIDATED → ROBUSTNESS_CHECKED → FINAL_RUN_READY → EVIDENCE_PACKAGE_READY`.

Problem interpretation, model selection, Final Run freeze, and evidence-package readiness use the
same automated evidence sequence at the appropriate scope. Before external submission, record
`TEAM_COMPLIANCE_REVIEW_RECORDED` for competition rules, attribution, packaging, and operational
constraints. It cannot change a technical decision. A supported `TEAM_CHALLENGE` adds evidence,
marks dependencies `STALE`, and triggers automated replay.

## STALE propagation

A changed input invalidates dependent audits, models, runs, metrics, decisions, and packages. A
changed source invalidates dependent claims. A changed implementation/config/environment invalidates
runs. A superseded Final Run invalidates downstream tables, figures, claims, and handoffs. A changed
policy/evidence/Judge output invalidates Meta, Audit, decisions, state, and reports. Clear `STALE` only
by recomputing from the earliest affected predecessor; editing a report or team-review record never
clears it.
