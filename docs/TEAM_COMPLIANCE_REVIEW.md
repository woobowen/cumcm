# Team compliance review

`TEAM_COMPLIANCE_REVIEW` checks current competition rules, attribution, allowed resources, submission
packaging, deadlines, and operational responsibilities. It uses
`contracts/team_compliance_challenge.schema.json` and is never embedded in `automated_decision`.

The team cannot technically accept, reject, rank, or override a model, architecture, component, or
Final Run. A supported challenge supplies new evidence. The main agent records the affected decision
as `STALE`, clears phase eligibility, and replays automated adjudication. An unsupported preference is
recorded as E0 uncertainty and has no decision force.
