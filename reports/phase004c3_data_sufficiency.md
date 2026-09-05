# Phase 004C3 data sufficiency

RC6 adds `requirement-evidence/v1` and `data-sufficiency/v1`. Every primary requirement declares
required/allowed evidence classes, minimum fields, time/entity scope, acquisition/substitution
policy, dependencies and completion rule. Every source declares supported requirements, evidence
class, provenance, authority, retrieval/licence, geographic/time/entity scope, schema, hash,
freshness and limitations.

`data-sufficiency` executes after `DATA_AUDIT` and before candidate modeling. Only `SUFFICIENT` or
bounded `PARTIAL` may continue; acquisition must be planned and rechecked, while unknown,
simulation-as-empirical, missing provenance and insufficient scope fail closed. Partial work cannot
be promoted to aggregate completion.

Auditor 1 found that this intended model is not fully enforced. The Gate accepts acquired evidence
when external data are forbidden, accepts an acquisition plan containing only requirement ID and
status, and combines fields/time/entities across different sources without one conjunctively
sufficient source. These three deterministic probes block RC6 release.
