# CUMCM C-Problem Target Policy

`rules/target_problem_policy.yaml` is the machine source for
`DECISION-C-TARGET-TRAINING-POLICY-004C`. This document explains that policy; it does not select a
model architecture or replace project state.

## Target and allocation

The primary competition target is `CUMCM_C_PROBLEM`. Priority is: first complete solution on an
unfamiliar C problem, transfer across distinct C structures, contest-time efficiency, then only the
cross-type capability needed to avoid regressions. Independent C Development work must account for
at least 80% of the historical-plus-preregistered independent allocation. A problems are
`AUXILIARY_TRANSFER_ONLY`; B problems are `EXCLUDED_BY_DEFAULT` unless a later explicit policy
decision changes the strategy.

Planned allocation and realized evidence are reported separately. A preregistered case cannot be
claimed as a completed or strictly blind first run. Stress and same-case Development regression do
not count as independent C evidence. Success on an A problem cannot substitute for C Validation.

## Batch freeze and revision admission

`C-TARGET-BATCH-001` contains three structurally different C Development positions and binds formal
Skill `0.2.0-competition-rc3`, release commit `8a2a813ff34d8c2701c64ff9d959848e7b88c27c`,
and Skill tree `a4551c8aa0b6b119823f6ce9df3f0f948339bb33`. Every answer begins `SEALED`; model-prior
exposure is `MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`.

All three first runs must be frozen, checked, independently committed, pushed, and remote-SHA
verified before any reference unlock or formal Skill mutation. A case may freeze as successful,
partial, blocked, rejected, STALE, or failed. Failed Runs remain evidence.

Only a defect repeated independently in at least two C cases, or one universal non-compensable hard
failure, may support a formal Skill change. A neutral case-independent test is mandatory. The
formal Skill may not contain a historical year, problem number/title, attachment or field name,
entity, answer, optimum, or case-specific parameter. No acceptable general change means RC3 is
retained; producing RC4 is not itself a success criterion.

The frozen batch produced one eligible repeated failure and exactly one revision cycle. The sole
formal Skill at the 004C checkpoint was `0.2.0-competition-rc4`, implementation commit
`297cad0a29c659b18484d4f3b67d69a942ad415c`, tree
`d041ca38de030ae04813ef02dbe12f7f2b7a1c22`. RC4 remained case-neutral and was frozen for the 2024 C
one-shot Validation; the original RC3 batch identity and first-run evidence remain unchanged.

## Validation and Held-out

Validation, Held-out, and final simulation must all use C problems. Validation uses a frozen Skill,
fresh isolated worker, sealed answer, preregistered rubric, and one terminal first run. After the
terminal freeze, a new Run is prohibited; later work on that problem is Development only. Answer or
solution exposure before freeze invalidates strict Validation eligibility.

`CUMCM-2024-C-VALIDATION-001` is terminal
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`. Its four preregistered actual Runs succeeded and all six
main requirements have feasible selected-output evidence, but the frozen RC4 Claim Gate requires
the same top-level text to equal both the global Final scope and the first requirement-specific
claim. The strings differ, so the Gate blocks with `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`
and a canonical handoff cannot be generated. This is not overridden by numeric success. RC4 stays
unchanged; the same case is Development-only after freeze, and the next route is a new frozen repair
batch using another C problem.

The 2025 C Held-out is reserved in this phase by the hash of its official annual-page URL only. Its
title, archive, problem, attachments, references, and answer remain unaccessed. The reservation is
not Development or Validation evidence.

## Scope and limits

This is a training-target and evidence-accounting decision, not an architecture decision. It does
not prove broad C generalization, production readiness, or a 2026 solution. Technical acceptance
continues to depend on deterministic Gates, captured Runs, feasible Finals, Claim evidence,
reproducible handoffs, and the formal state machine; Agent votes cannot override a rejection.

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

## Phase 004C3 authorization

004C3 retains both negative Validation outcomes and repairs only the release/evidence semantics
demonstrated by them. Before expensive modeling, each primary requirement must pass a structured
data-sufficiency Gate or be isolated as partial/unsatisfiable. Simulation cannot substitute for an
empirical requirement. Final selection may be global only with exact all-requirement support;
otherwise it is per-requirement or a hash/scenario/constraint-compatible portfolio. Claim strength
is bounded by structured evidence predicates, not prose confidence.

After neutral tests, at most two revisions, full historical regression and a read-only audit, RC6
must be remotely frozen before the preregistered 2018 C (or input-only 2017 fallback) is accessed.
That answer-sealed C Validation is one-shot with a four-hour boundary and clean-context worker.
The 2025 reservation and six false access flags remain unchanged until an actual PASS authorizes
004D; failed/insufficient/incomplete Validation cannot be compensated by other evidence.

Auditor 1 blocked RC6 before release by reproducing 13 fail-open data, selection, semantic and
compatibility probes and an ineffective hardcoded global completion path. The two-cycle limit is
exhausted. Therefore neither preferred nor fallback Validation input was accessed, no Validation
case was registered, 004D remains locked, all six 2025 flags remain false, and the exact next phase
is `null`.

## Phase 004C4 runtime-pipeline closure

004C4 is an independently budgeted repair phase that preserves every 004C3 terminal fact. Its
release evidence is controller-level: frozen probes invoke the real CLI/workspace/state/finalization
and handoff path and require a bound gate trace. RC7 must pass three neutral end-to-end cases,
independent adversarial replay and all C/history regressions before candidate/live consistency and
remote freeze. Fresh Validation remains answer-sealed and inaccessible before that freeze; 2025 C
remains reserved with all access flags false.
