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

## Competition RC to contest-candidate route

The post-shadow capability route is:

`FORMAL_SKILL_RC → DEVELOPMENT_EVAL → VALIDATION → HELD_OUT → COMPETITION_CANDIDATE`.

- `FORMAL_SKILL_RC` requires one discoverable project-owned Skill, an unchanged architecture selection
  rule, all eight public hard Gates, two structurally different project-original E2E cases, the fixed
  negative matrix, full CI, and a read-only integration audit. It authorizes only
  `COMPETITION_RC_IMPLEMENTATION_ONLY`.
- `DEVELOPMENT_EVAL` selects an answer-sealed historical Development problem, binds the exact Skill
  commit/model/reasoning, freezes the first run before answer access, and separates generalizable
  failures from problem-specific findings.
- `VALIDATION` and `HELD_OUT` use frozen Skills and sealed answers. Any answer exposure permanently
  demotes the case to Development; results cannot tune the same frozen candidate.
- `COMPETITION_CANDIDATE` requires later validation/held-out contracts and decisions. RC readiness,
  file existence, two smokes, or Agent claims cannot substitute for those gates.

For RC1, `COMPETITION_SKILL_RC_READY` permits only
`PHASE-SKILL-DEVELOPMENT-EVAL-004`. Full R3 sealed Stage 1/Stage 2, ablation, external validity,
production fitness, and monetary cost remain `DEFERRED_NOT_PASSED`.

## Phase 004 answer-sealed Development route

`COMPETITION_SKILL_RC_READY → DEVELOPMENT_FIRST_RUN_IN_PROGRESS` requires a clean non-main task
branch based on the merged RC commit, one discoverable formal Skill, passing baseline CI, an empty
or non-conflicting Development registry entry, official/hash-bound immutable problem inputs, and
`answer_access_status=SEALED`. The case binds the RC Skill commit/tree, model and reasoning
visibility, search policy, scoring rubric, time budget, and private workspace before modeling.

The first run follows the 14 contest-run stages without modifying the formal Skill. Success,
partial progress, deterministic rejection, STALE, and bounded execution failure are all freezeable
outcomes; failed Runs remain evidence. Any answer access before a verified first-run freeze yields
`FIRST_RUN_CONTAMINATION_SUSPECTED`. Unsafe official-input acquisition yields
`OFFICIAL_INPUTS_REQUIRED`. Infrastructure that prevents an honest run yields
`INFRASTRUCTURE_BLOCKED`; none of these labels authorize fabricated execution.

Only an independently committed first-run freeze whose remote SHA matches may change the answer
state to `UNLOCKED_AFTER_FIRST_RUN`. Post-unlock review separates generalizable Skill failures from
knowledge, search, data-engineering, modeling, experiment, evidence, efficiency, problem-specific,
and reference-disagreement findings. At most two major Skill revisions are allowed. A revision must
be supported by first-run evidence, expressible without this case's identifiers/fields/values, and
must preserve the synthetic smokes, negative matrix, one-Skill invariant, and deterministic state
truth.

An accepted revision may terminate at `DEVELOPMENT_EVAL_RC2_READY` only after same-case
`DEVELOPMENT_REGRESSION`, Stress A/B/C, full CI, leakage/secrets/consistency checks, and remote
delivery. No accepted generic change terminates at `DEVELOPMENT_EVAL_COMPLETE_NO_SKILL_CHANGE`.
Unresolved core work after the revision cap terminates at `DEVELOPMENT_EVAL_INCOMPLETE`. Successful
completion may route only to `PHASE-SKILL-DEVELOPMENT-EVAL-004-B`, using a structurally different
answer-sealed Development problem; this case never becomes Validation or Held-out evidence.

## Phase 004C C-target batch generalization route

The C-target route is:

`RC3_FROZEN → THREE_C_BATCH_FIRST_RUNS → ALL_FIRST_RUNS_FROZEN → UNIFIED_CROSS_CASE_POSTMORTEM → SINGLE_RC4_OR_NO_CHANGE → UNIFIED_REGRESSION → C_VALIDATION → C_HELD_OUT → C_FULL_SIMULATION`.

`PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C` starts only from the remotely delivered RC3
checkpoint, one discoverable formal Skill, clean baseline CI, an answer-sealed three-case C batch,
and a frozen batch policy/rubric. All three Development cases bind the same formal Skill
version/commit/tree. Every first run is independently frozen and remotely verified, including
partial, blocked, rejected, or failed outcomes. Until all three freezes pass, the formal Skill tree
must not change and references for every batch case remain locked.

After all three freezes, a bounded reference review may produce one cross-case failure matrix. A
formal Skill change is eligible only when the same defect independently occurs in at least two C
cases, or when one observed defect is a universal non-compensable hard failure. Every accepted
change needs a neutral, case-independent test and must contain no year, problem number, title,
attachment name, field, entity, answer, optimum, or case-specific parameter. At most two revision
cycles may produce `0.2.0-competition-rc4`; lack of an eligible general change retains RC3.

Unified regression covers the three batch cases as non-blind Development regressions, the preserved
2023 C main chain, 2020 A only as auxiliary transfer evidence, the two synthetic E2E cases, the 30
negative cases, and new neutral tests. Only after that evidence and the Validation rubric are frozen
may a fresh worker run one answer-sealed 2024 C case once. A terminal Validation freeze forbids any
new Validation Run; a failed or contaminated case is permanently non-Validation. The 2025 C
Held-out is registered only by annual-page hash in this phase and its archive, title, problem,
attachments, references, and answers remain unaccessed.

After unified regression, the active status may be
`C_TARGET_BATCH_RC4_READY_VALIDATION_PENDING` with subphase
`C-TARGET-RC4-FROZEN-VALIDATION-PENDING`, active Skill RC4, and `next_phase_allowed=null`. Terminal
routes are `C_TARGET_VALIDATION_PASSED`, `C_TARGET_BATCH_RC4_READY_VALIDATION_PENDING`,
`C_TARGET_BATCH_COMPLETE_NO_SKILL_CHANGE`, `C_TARGET_VALIDATION_FAILED`,
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`, `C_TARGET_VALIDATION_INCOMPLETE`,
`C_TARGET_BATCH_INCOMPLETE`, `OFFICIAL_INPUTS_REQUIRED`,
`FIRST_RUN_CONTAMINATION_SUSPECTED`, or `INFRASTRUCTURE_BLOCKED`. Technical hard failures cannot be
averaged away by a score or Agent vote.

The 2024 C one-shot terminal path is
`FINAL_CANDIDATE → REJECTED(GATE_CLAIM_EVIDENCE)`. Although all four frozen Runs succeeded and all
six main requirements have feasible numeric outputs, RC4 requires the top-level Claim text to equal
both the global Final scope and the first requirement-specific claim text. Those frozen strings
differ, so `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID` is deterministic and no accepted handoff
can exist. `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT` routes only to
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`; the 2024 C case is terminal and any later same-case work
is Development only.

## Contest-run lifecycle

The formal RC case state is:

`CREATED → INTAKE_COMPLETE → REQUIREMENTS_VALIDATED → SOURCES_PLANNED → DATA_AUDITED → MODELS_PROPOSED → EXPERIMENT_PLAN_VALIDATED → RUNNING → RUN_COMPLETED → RUN_VALIDATED → ROBUSTNESS_VALIDATED → FINAL_CANDIDATE → EVIDENCE_VALIDATED → READY_FOR_PAPER_HANDOFF`, with terminal `STALE` and `REJECTED`.

The case state is accepted only when its exact fields, ordered history, transition Gates and evidence
bindings form one chain. Raw and processed inputs are bound at data audit; every forward transition
first recomputes existing dependency hashes. A mismatch records or reports `STALE` before any later
Gate may run. Run manifests and handoffs are verified against actual files, not declarations alone.

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

## Phase 004C2 terminal result

The case-neutral Claim implementation passed the frozen tests within two revision cycles.
Post-decision audit found an unresolved release blocker: the frozen Skill VERSION file still says
RC4 while the runner, SKILL.md and manifest say RC5. Release acceptance is BLOCKED_VERSION_METADATA;
the frozen Skill cannot be changed in this episode.
The one Skill runs the hash-frozen `0.2.0-competition-rc5` implementation, K1, `COMPETITION_RC`;
its inconsistent VERSION label is preserved as audited evidence.
Release truth: `evals/results/phase-004c2/rc5_release.json`; execution record:
`plans/active/PLAN-0004C2-claim-scope-repair-and-fresh-validation.md`.
The 2024 terminal verdict and original artifacts remain unchanged.
RC5 release `24265710b3f4b154ccf6eff19614eea7fb3fb0d4` was remotely verified before
2019 official input access. The pre-run freeze was remotely delivered before all nine actual Runs.
`CUMCM-2019-C-VALIDATION-002` terminated as `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`:
Q2 requires actual airport/city observations, which are absent. Native Run/Claim/handoff contracts
passed structurally; Q4 semantic support is incomplete in the selected baseline Claim.
The frozen rubric rejected paper dispatch and the
final case state is `REJECTED`. No whole-problem completion or joint optimum is claimed.
The machine decision and terminal freeze live under
`evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002/`.
RC5, case code, rubric and neutral tests remain frozen; no model retry or later same-case Validation
is permitted. Answers remain sealed. The next phase is `null`; Held-out 004D is locked and all six
2025 access flags remain false. Later work on this case can only be Development under new scope.

## Phase 004C3 RC6 evidence-repair and fresh-Validation route

`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT + RC5_VERSION_FILE_MISMATCH ->
C_TARGET_EVIDENCE_REPAIR_IN_PROGRESS` is a newly frozen successor phase. It preserves RC5 and the
2024/2019 terminal histories, then freezes neutral requirements before changing the formal Skill.
The only implementation scope is release consistency, requirement evidence/data sufficiency,
source acquisition planning, per-requirement or compatible portfolio selection, and structured
semantic Claim predicates. K1, execute/capture/seal, raw immutability, failure retention, STALE,
one formal Skill and one project state remain unchanged.

`C_TARGET_EVIDENCE_REPAIR_IN_PROGRESS -> C_TARGET_RC6_READY_VALIDATION_PENDING` requires no more
than two implementation cycles, all neutral/historical/synthetic/negative evidence, read-only 2019
and 2024 diagnostics, one read-only release/evidence Auditor without BLOCKER, full offline CI and a
remotely verified RC6 freeze. New Validation inputs cannot be read before that remote receipt.

The preferred 2018 C case, or input-failure/contamination-only 2017 fallback, then follows an
answer-sealed input-suitability preflight and remotely delivered pre-run freeze. A clean-context
worker executes the existing 14-stage lifecycle once within four hours. Requirement data status,
evidence class, selection, selected Run/output and Claim predicates are mandatory. Missing evidence,
zero policy exposure, incompatible portfolio, incomplete aggregate coverage, unbound source,
answer exposure, Skill drift or post-freeze Run is a non-compensable failure.

The terminal decision is independently frozen and remotely delivered before the second and final
read-only Auditor. `C_TARGET_VALIDATION_PASSED` may route only to
`PHASE-SKILL-C-TARGET-HELDOUT-004D`; failed, insufficient or incomplete evidence routes to
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C4`; release repair failure keeps 004C3 and null. The 2025 C
reservation remains `SEALED_NOT_ACCESSED` throughout.

The Phase 004C3 pre-release audit is terminal `RC6_RELEASE_REPAIR_BLOCKED`. Auditor 1 reproduced
fail-open acquisition/scope, portfolio/hash/dependency, semantic binding/eligibility and
compatibility cases, while the fresh-completion controller hardcodes a global descriptive path.
Because both formal revision cycles are exhausted, no third Skill repair, RC6 release, fresh input
access, Validation worker or Run is permitted in this phase. `next_phase_allowed` is `null`.

## Phase 004C4 actual-controller and RC7 route

`RC6_RELEASE_REPAIR_BLOCKED -> C_TARGET_RUNTIME_PIPELINE_REPAIR_IN_PROGRESS` is a new phase, not a
third 004C3 cycle. It preserves RC5, blocked RC6, both old Validation freezes and all 13 audit
findings. The observable top-level completion command must fail closed through ordered,
input/output-hash-bound Gates; helper-only calls cannot satisfy release evidence. The expected
counterexamples are frozen before code, then three neutral actual-controller workspaces exercise
per-requirement selection, joint portfolio compatibility and partial data completion.

`C_TARGET_RUNTIME_PIPELINE_REPAIR_IN_PROGRESS -> C_TARGET_RC7_READY_VALIDATION_PENDING` requires
all frozen/new controller probes, independent adversarial replay, neutral E2E traces, historical
diagnostics/regressions, candidate checking, live checking, full offline CI and remote RC7 delivery.
Until then, RC7 is a candidate only and fresh official input access is prohibited.

After the remotely verified RC7 pre-run freeze, exactly one fresh worker runs the sealed 2018 C
case, with 2017 allowed only for input failure/corruption/unrecognizable input or pre-result
contamination. PASS routes to 004D; failed, insufficient or incomplete evidence routes to 004C5;
release failure keeps 004C4 with `next_phase_allowed=null`. Terminal freeze prohibits later Runs or
same-case Validation repair. The 2025 reservation remains untouched throughout.
