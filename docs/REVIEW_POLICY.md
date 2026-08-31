# Review policy

Independent reviewers return structured findings with severity, claim, evidence, affected files, requested test, action, confidence, and status. They challenge evidence; they do not write formal state or decide by vote. `BLOCKER` prevents a gate, `HIGH` requires resolution/approval, `MEDIUM` requires tracked mitigation, and `LOW`/`INFO` remain traceable. Unknown evidence is `UNKNOWN`, never an implicit pass.

Every adjudication `BLOCKER` or `ERROR` becomes a `test_request`. Executed deterministic results
become `test_evidence`; non-testable claims are uncertainty and cannot independently accept or reject.
Blind Judges cannot see identities or peer outputs. A verified minority counterexample dominates any
number of supporting recommendations.
