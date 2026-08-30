# Source-of-truth ownership

| Concern | Sole normative source | Derived/consumer |
|---|---|---|
| Project objective/scope | `GOALS.md` | README, reports |
| Formal state machine | `WORKFLOW.md` | state, status report |
| Machine contracts | `contracts/` | fixtures, validators |
| Mandatory rules | `rules/` | scripts, tests, Skill |
| Architecture decisions | `docs/adr/` | architecture summary |
| Current execution plan | `plans/active/` | status/report |
| Runtime state/ledgers | `state/` | `reports/current_state.md` |
| Upstream candidate facts | `research/upstream_candidates/manifest.yaml` | CSV/reviews/notices |
| Designated Git delivery target | `rules/workflow_rules.yaml` → `git_delivery` | local Git config, runbook, release/report evidence |
| Human status summary | generated `reports/current_state.md` | read-only |
| Paper handoff | `contracts/modeling_to_paper.schema.json` | packages/paper team |

Normative text is referenced, not copied into a second authority. When summaries disagree, the listed source wins and the summary is stale. Schema versions are never forked outside `contracts/`; generated reports are never edited manually.
