# Phase 002D failure summary

- Completion failures: 8
- Completed but excluded: 2
- Infrastructure failures: 1
- Operator interventions: 0
- Terminal hard stop: `ELAPSED_BUDGET_REACHED`

| Completion-failure class | Count |
|---|---:|
| HTTPS_FALLBACK_DISCONNECT | 1 |
| POLICY_VIOLATION | 7 |

| Authoritative hard-failure code | Count |
|---|---:|
| HARD-FAIL-003 | 6 |

All failures and exclusions remain append-only. They are not zero-valued scores and cannot fill
balanced/repeat minima. Coverage-only hard-failure fields remain outside authoritative Gates.
