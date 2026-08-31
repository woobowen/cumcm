# Formal state machine

This is the sole normative lifecycle. Technical gates are automated, evidence-first, lexicographic,
and non-voting. Humans record `TEAM_COMPLIANCE_REVIEW` or submit evidence-backed challenges; they
cannot select a model, architecture, or component and cannot override technical rejection.

## Automated adjudication lifecycle

| State | Required evidence/check | Allowed next | Failure/uncertainty |
|---|---|---|---|
| `CANDIDATES_FROZEN` | candidate set, policy hash, evidence freeze | `ADVERSARIAL_REVIEW_COMPLETE` | `STALE` |
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

The nominal success path is:

`CANDIDATES_FROZEN → ADVERSARIAL_REVIEW_COMPLETE → TESTS_SYNTHESIZED → EVIDENCE_EXECUTED → BLIND_ADJUDICATION_COMPLETE → META_ADJUDICATION_COMPLETE → DECISION_AUDIT_COMPLETE → AUTOMATED_ACCEPTED`.

Transport recovery does not create a lifecycle shortcut. Resume uses the exact recorded
session/thread and unchanged role inputs; an eligible fallback Adapter still consumes the same
versioned per-role/global budget. Exhausted budget, missing role output, or broken checkpoint yields
`AUTOMATED_ADJUDICATION_INCOMPLETE` and locks all dependent roles. Remaining global starts do not
override a per-role limit. See `docs/TRANSPORT_RECOVERY_POLICY.md`.

Phase 003 additionally requires an accepted architecture, Auditor `PASS`, at least one accepted
`SPECIFICATION_ONLY` component, no unresolved hard gate/BLOCKER, stable replay, and clean CI. This
phase never starts merely because a plan or report recommends it.

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
