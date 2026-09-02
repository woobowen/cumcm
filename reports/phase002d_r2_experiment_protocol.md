<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2 prospective experiment protocol

Protocol `PHASE-002D-R2-PROSPECTIVE-PROTOCOL-001` is `POLICY_FROZEN` at
`cfc17c89ca79f40cc1889fd0bdd5c03fe91ec1ae8de70cf65f114e25f416d081` and executed in R2: `False`.
Stages are deterministic conformance, future model comparison and automatic adjudication. The
three arms use equal cohorts, Prompt, data, timeout, sandbox, network/MCP policy, hidden cases and
grader. Maximum primary starts are `24`;
retry slots `6`; global absolute cap
`30`. Retry burden is
`retry_attempt_count / max(1, planned_primary_slot_count)`.

Stage-1 ablations are `['baseline', 'accepted-versus-done-workflow-state-only', 'claim-evidence-support-gate-only', 'hash-bound-reproducibility-manifest-only', 'leakage-safe-model-comparison-gate-only', 'all-four-components', 'reproducibility-plus-claim-support-interaction']`; candidate-result-informed and post-hoc ablation
selection are both false. No Stage was executed, no model/API/prototype call occurred, and the two
upstream candidates are prohibited as arms.
