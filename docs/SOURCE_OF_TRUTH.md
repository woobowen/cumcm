# Source-of-truth ownership

| Concern | Sole normative source | Derived/consumer |
|---|---|---|
| Project objective/scope | `GOALS.md` | README, reports |
| Formal state machine | `WORKFLOW.md` | state, status report |
| Machine contracts | `contracts/` | fixtures, validators |
| Mandatory rules | `rules/` | scripts, tests, Skill |
| Target-problem policy and evidence accounting | `rules/target_problem_policy.yaml` | `docs/TARGET_PROBLEM_POLICY.md`, registry, plan, reports |
| Architecture decisions | `docs/adr/` | architecture summary |
| Current execution plan | `plans/active/` | status/report |
| Runtime state/ledgers | `state/` | `reports/current_state.md` |
| Automated decision policy | `rules/automated_adjudication_rules.yaml` and `adjudication/policies/phase-002a.yaml` | Judge prompts, Meta, reports |
| Versioned formal execution config | `adjudication/configs/` | transport, role prompts, checkpoints |
| Transport recovery policy | `docs/TRANSPORT_RECOVERY_POLICY.md` | recovery implementation and runbook |
| Formal execution records | `evals/results/phase-002b/` | state transitions and reports |
| Phase 002D experiment and closure | `evals/results/phase-002d/` | generated Phase 002D reports and state |
| Phase 002D-R1 failure-aware adjudication | `evals/results/phase-002d-r1/` | generated R1 reports and state |
| Failure-aware evidence policy | `docs/FAILURE_AWARE_EVIDENCE_POLICY.md` and `rules/phase002d_r1_workflow_rules.yaml` | R1 engines/tests |
| Automated technical decisions | versioned `evals/results/*/automated_decisions/` | state transitions and reports |
| Team compliance/challenge | `contracts/team_compliance_challenge.schema.json` records | STALE trigger only |
| Upstream candidate facts | `research/upstream_candidates/manifest.yaml` | CSV/reviews/notices |
| Designated Git delivery target | `rules/workflow_rules.yaml` → `git_delivery` | local Git config, runbook, release/report evidence |
| Human status summary | generated `reports/current_state.md` | read-only |
| Paper handoff | `contracts/modeling_to_paper.schema.json` | packages/paper team |

Normative text is referenced, not copied into a second authority. When summaries disagree, the listed source wins and the summary is stale. Schema versions are never forked outside `contracts/`; generated reports are never edited manually. `content_verified_commit` names a prior content subject; `delivery_receipt_for_commit` verifies delivery of that existing commit, so neither is self-referential.
