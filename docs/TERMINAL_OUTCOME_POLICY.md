# Terminal outcome policy

An eligible oracle PASS resolves a slot as `RESOLVED_ELIGIBLE_SUCCESS`. An authoritative oracle
failure or candidate-attributed policy/schema/unsupported-claim failure resolves it as
`RESOLVED_TERMINAL_NEGATIVE`. Infrastructure-only, harness-only and unknown outcomes remain
censored. Mixed evidence follows deterministic precedence and retains all secondary causes.

Terminal negatives count toward outcome completeness and repeated component-gap observations. They
do not become quality scores, do not prove that a proposed mechanism improves outcomes and cannot
authorize retry-until-success.
