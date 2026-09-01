# Phase 002D evidence expansion

Phase 002D is a bounded evidence-acquisition phase, not an integration phase. It used one frozen
`gpt-5.6-sol`/`medium` cohort, ChatGPT-managed Codex authentication, fresh ephemeral sessions,
blocked randomized arm order, deterministic oracles, process evidence and fail-closed primary
eligibility. Historical Phase 002–002C records remained immutable and were gap evidence only.

The terminal experiment contains 28 scored starts and 18 eligible records. Three cases are balanced;
the balanced-cell independent-repeat depth is one. Cumulative elapsed time reached 6,228.480778
seconds and crossed the frozen 6,197-second limit, so the runner is `STOPPED` with
`ELAPSED_BUDGET_REACHED`. The formal sufficiency result is `INSUFFICIENT` against minima four cases
and two repeats. Unused attempt/input/output capacity cannot override the elapsed Gate.

Because sufficiency failed, native semantic Subagents, Phase 002D automated decisions, Decision
Auditor and decision replay were not run. The deterministic closure Gate permits only a redesigned
continuation of `PHASE-EVIDENCE-EXPANSION-002D`; Phase 003 remains prohibited. The formal Skill stays
`0.1.0-foundation`/`SCAFFOLD_ONLY`.

Machine truth lives under `evals/results/phase-002d/`; the active plan, `state/project_state.json`
and generated reports summarize it. Frozen runner inputs and historical evidence must not be edited.
