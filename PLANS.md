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

`PHASE-SKILL-DEVELOPMENT-EVAL-004-A` is the active real-problem sprint in
`plans/active/PLAN-0004A-2023c-development-eval.md`. It binds the merged RC1 commit to one official,
answer-sealed historical Development case, freezes the first run before any reference unlock, and
accepts at most two evidence-backed, problem-independent RC2 revisions. It then runs a same-case
Development regression and three semantics-preserving Stress checks. This case is never promoted to
Validation/Held-out evidence, and one problem cannot prove generalization.
