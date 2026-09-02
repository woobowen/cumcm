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
