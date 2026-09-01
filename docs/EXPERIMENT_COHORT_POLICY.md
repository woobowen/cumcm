# Experiment cohort policy

Primary comparative evidence must come from exactly one cohort: identical model, reasoning setting,
transport profile, Codex CLI version, sandbox, prompt/package/policy/oracle/scorer hashes and task
input per case. Phase 002D selected MODE B, cohort
`PHASE-002D-NEW_MODEL_COHORT-GPT-5-6-SOL-MEDIUM`, because the historical model was unavailable.

Cross-model, historical, recovered, resumed, parser-recovered, superseded, failed and `NOT_RUN`
records cannot fill Phase 002D minima. Every scored attempt is a fresh start. A cohort or hash change
after the first scored run is a hard stop and makes dependent records stale; it is never repaired by
relabelling or post-hoc pooling.

The cohort record and compatibility result are in `evals/results/phase-002d/cohort/`. Availability
is local-account evidence, not a general statement about public model availability.
