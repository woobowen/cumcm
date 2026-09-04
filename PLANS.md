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

The only active execution is `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C` in
`plans/active/PLAN-0004C-C-target-batch-generalization.md`. It froze RC3 across three structurally
different, answer-sealed C Development first runs, unlocked references only after all three remote
freezes, admitted one unified RC4 revision, and passed unified regression. RC4 is frozen while the
2024 C inputs and rubric are prepared for one fresh answer-sealed Validation run. The next eligible
project phase is a C Held-out phase only if the formal Validation decision permits it; otherwise the
route is C batch repair or null.
