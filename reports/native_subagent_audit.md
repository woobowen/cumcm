# Native Subagent Audit

The first-round roles were independent, read-only, and denied peer-output visibility; the Decision Auditor received only frozen predecessor outputs.

| Role | Model | Reasoning | RO | Peer view | Output hash | Findings | Blockers | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_sufficiency_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | 1de280d35e959ce355d9840e09b0de8096053a50913b26bd0b97693c9c60478e | 8 | 0 | PASS |
| adjudication_policy_prosecutor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | 5ee12808550468ef78aaa4d447233f2a860c284fbf796b4bf7d9ad06e40738d6 | 9 | 0 | PASS |
| dissent_and_cost_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | df3347aa5a338e6067161b53d423b7a54b90bee5a17977992d7d3e14565d9e71 | 5 | 0 | PASS |
| reproducibility_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | NONE | 447a38914de3bea6a0d3e6c711a5dce6af865c3c7203ab0bc91fd37aaea3c8ca | 10 | 0 | PASS |
| automated_decision_auditor | INHERITED_PARENT_UNEXPOSED | INHERITED_PARENT_UNEXPOSED | True | FROZEN_PREDECESSORS_ONLY | f81d9f46553955f02c7de88f7fff3adc3c5a40ac1cc3cd745a0c0dd7570dcde1 | 7 | 0 | PASS |

Derived blocker tests: 24; all testable blockers resolved: `True`.
Majority vote used: `False`; nested Codex used: `False`; API key used: `False`; Subagent write observed: `False`.
