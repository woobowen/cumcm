# ExecPlan standard

Every complex phase has exactly one active plan under `plans/active/`. A plan is self-contained and must include: purpose, current environment, scope, non-goals, milestones, per-milestone acceptance criteria, validation commands, risks, decision record, actual progress, findings, next step, rollback, and update rule.

Update a plan after a milestone, failed validation, new blocker, material discovery, or approved design change. Preserve factual history; mark superseded decisions instead of silently rewriting them. Validation entries include exact command, exit code, counts, and relevant warnings.

Move a plan to `plans/completed/` only after acceptance, status/report regeneration, and local commits. Move cancelled or replaced plans to `plans/archived/` with reason and successor. Plans guide execution but do not replace `GOALS.md`, `WORKFLOW.md`, rules, contracts, or runtime state.

Phase 002A freezes evidence and policy before Agent execution. After three failed autonomous repair
cycles it records `AUTOMATED_ADJUDICATION_INCOMPLETE`, preserves failures, keeps
`next_phase_allowed=null`, and provides a continuation command instead of fabricating outputs.

Phase 002D plans checkpoint and remotely deliver every real batch. If a frozen budget stops before
the four-case/two-repeat minima, the plan records `EVIDENCE_EXPANSION_INCOMPLETE`, locks semantic
Subagents/decisions and describes redesign conditions; it does not move to completed plans.

Phase 002D-R1 may complete a failure-aware adjudication even when quality remains insufficient.
Completion requires the independent Decision Auditor and stable replay, records only bounded
accepted scopes, and routes a new acquisition design back to Phase 002D without executing it.

Phase 002D-R2 may complete as a specification/protocol phase when every frozen artifact, serious
finding closure, bounded automated decision, independent Decision Audit and offline replay passes.
A pre-audit shadow decision may remain `RETEST_REQUIRED`; it authorizes no implementation and routes
only another newly frozen R2 design. Completion never selects architecture/base, mutates the formal
Skill, executes a prototype/model/API experiment, or opens Phase 003.

## Current sprint and next execution

Phase 004A (2023 C Development) and Phase 004B (2020 A auxiliary Development) are complete. The
planned 2024 A Validation was cancelled before registration and produced no formal execution
evidence or commit (`CANCELLED_BEFORE_REGISTRATION_NO_EXECUTION_EVIDENCE`).

The completed predecessor record is `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C` in
`plans/completed/PLAN-0004C-C-target-batch-generalization.md`. It froze RC3 across three structurally
different, answer-sealed C Development first runs, unlocked references only after all three remote
freezes, admitted one unified RC4 revision, and passed unified regression. The fresh answer-sealed
2024 C Validation is terminal `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`: all Runs and main outputs
succeeded, but the frozen Claim Gate is contradictory and blocked handoff. RC4 and the 2024 C
terminal evidence remain immutable. The exact next route is
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2` with a newly frozen design and a different C case.

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
