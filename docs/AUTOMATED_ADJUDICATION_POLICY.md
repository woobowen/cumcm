# Automated adjudication policy

Technical decisions use the frozen rules in `rules/automated_adjudication_rules.yaml` and the phase
policy hash. Evidence is ordered E3→E2→E1→E0. Freeze integrity and hard failures precede sufficiency,
oracle/process evidence, Dissent tests, stability, and Audit; a soft total cannot cancel a hard gate.
Agent recommendations are non-voting. The engine may reject every target, request retest, report
insufficient evidence, or abstain.

Coverage measures structured field presence only. Correctness requires a case-specific deterministic
oracle. Process evidence binds observation/run identity, commands, inputs, outputs, schema, and
prohibited actions. Recovery-affected cells are gap evidence only. An unsupported Agent claim is E0;
a serious testable claim becomes executed test evidence before Meta-Adjudication.

Meta reads only frozen policy/evidence, independent Judge/Dissent records, and test evidence. It may
not change thresholds or invent facts. Formal state changes only when the Decision Auditor passes.
`TEAM_COMPLIANCE_REVIEW` remains a separate non-technical record.
