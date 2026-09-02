<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2 threshold policy

Metric registry `PHASE-002D-R2-METRICS-001` contains `32` metrics. Threshold
policy `PHASE-002D-R2-THRESHOLDS-001` contains `32` frozen rules at
`92a09cbc0ea7d2ef47addf2e61c6ed0e2062fd9c2a3b6ddd4798fccf564680e3`. Candidate metrics were present at freeze:
`False`. All thresholds are noncompensatory:
`True`.

The policy separates hard safety, effectiveness, false block, reproducibility, state correctness,
claim support, leakage prevention, cost and maintenance. Paired false-block inference freezes its
denominator/discordance/alpha and abstains when undefined. Baseline-derived rules are fixed before
candidate results; `ARCH-S0` is not required to improve over itself. Unknown critical cost or
evidence routes to `EVIDENCE_INSUFFICIENT`, never zero.
