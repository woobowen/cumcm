# ADR-0026: Use a fixed blocked randomized anonymous-arm order

Status: Accepted
Date: 2026-09-01

## Context

Running all attempts for one arm before the next would confound instruction effects with service
time, quota and transport state. Immediate unlimited retry would create a second order bias.

## Decision

Freeze eight `case_id × repeat_id` blocks for four cases and two repeats. Use seed `20260901` to
permute `ARM-A`, `ARM-B`, and `ARM-C` once inside each block. Predeclare 24 primary attempt IDs and
two potential retry IDs per cell. Finish a block before retrying; consume the frozen retry queue
without post-result reordering. Never repeat a successful cell and never exceed three fresh starts
per cell.

## Consequences

All arms experience the same block structure and no real identity determines order. Failures remain
visible, while retries cannot be selected opportunistically. The global budget may stop before all
potential retry slots are used.
