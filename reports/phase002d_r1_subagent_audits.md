<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R1 native Subagent audits

| Role | Round | Verdict | Findings | Blockers |
| --- | --- | --- | --- | --- |
| failure_attribution_auditor | FIRST_ROUND | RETEST_REQUIRED | 7 | 3 |
| retry_bias_prosecutor | FIRST_ROUND | RETEST_REQUIRED | 7 | 2 |
| evidence_scope_statistician | FIRST_ROUND | PASS | 5 | 0 |
| experiment_protocol_auditor | FIRST_ROUND | RETEST_REQUIRED | 5 | 4 |
| cost_and_stop_auditor | FIRST_ROUND | PASS | 7 | 0 |
| failure_aware_decision_auditor | POST_DECISION | PASS | 13 | 0 |

The five first-round outputs remain immutable. Their ten serious findings were closed by executed
deterministic tests without rewriting original verdicts. The post-decision Auditor required
3 bounded repair cycles: cycle 1 closed
2 of 2
scope/replay findings, and cycles 2–3 closed two evidence-catalog omissions. All intermediate
records remain preserved; the final independent re-audit passed. No vote or human technical Gate
was used.
