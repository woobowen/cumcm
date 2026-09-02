# ADR-0028: Prohibit cross-model primary evidence aggregation

Status: Accepted
Date: 2026-09-01

## Context

Changing the base model can change task behavior independently of the arm instruction. Combining
`gpt-5.4` and `gpt-5.6-sol` as repeats would confound model and mechanism effects.

## Decision

Primary comparison, balanced sets, repeat depth, medians and effect estimates use exactly one
model/reasoning cohort. Under Phase 002D MODE B, all Phase 002 primary records are cross-model gap
evidence only. No normalization, weighting or semantic judgment may promote them into the new
cohort.

## Consequences

The active target is 24 new eligible successes. This increases execution cost but preserves a
meaningful experimental unit and prevents model drift from being attributed to an arm.
