# Supplemental 2021 Q4 certificate preregistration

Scope: Development arithmetic/proof supplement to the existing fixed
`RUN-RC8-BASELINE_MEAN_GREEDY-S20210904` at implementation `d9a43b8`.
It does not rerun the original models, revise v6, select a new model, change a fresh
case, or grant a formal Skill Gate. The shared RC8 subject remains `29cf1d7`.

Consume the remaining ninth 2021 Development numerical attempt conservatively:
one dual-witness construction, maximum900seconds, no retry after a failed numeric
capture. Existing usage8/9 and every failure remain recorded. Independent exact
verification and synthetic corruption checks are audit operations, not additional
model candidates. Final access0. No package or environment changes.

The original stationary Q4 first objective is a linear transportation problem:
maximize sum(c_ij x_ij), with nonnegative flows, supplier totals no greater than
registered supply capacities and carrier totals no greater than6000m3. Coefficients
are (1-loss_j)/consumption_i. For nonnegative multipliers u_i,v_j satisfying
u_i+v_j>=c_ij, weak duality gives an upper bound sum(cap_i u_i)+6000sum(v_j).
The constructor uses the existing installed HiGHS only to propose multipliers,
then rationally repairs every inequality. Solver status is not the proof.

A separate solver-free verifier checks every multiplier, all3216 dual inequalities,
all402 supplier constraints and8 carrier constraints with exact rational arithmetic.
The feasible lower-bound plan must be the original recorded flow multiplied by one
common scale in(0,1], solely removing floating-point constraint overshoot. No new
allocation or post-selection optimization of the original plan is permitted.
Acceptance requires an exact nonnegative upper-minus-lower gap no greater than
0.001m3. All individual slacks and rational bounds are published, not merely counts.

The exact certificate targets the explicitly serialized decimal-parameter LP.
An independent workbook reader recomputes all baseline parameter estimates from
W001–W168 only, without importing the original producer/checker/constructor, and
compares them within1e-9. Raw workbook hashes and original output/capture hashes
must match the pre-run binding. W169–W240 cells are not read by this supplement.
The distinction between approximate raw parameter reproduction and exact proof of
the declared decimal model must remain explicit.

This may narrow the missing conditional Q4 optimality evidence. It cannot establish
future capacity, stochastic feasibility, startup inventory availability, costs,
prescribed attachment completion or whole-problem scientific completion. It does
not erase the original plan's historical stress failures. The first-party code and
this protocol must be committed and remotely verified before numerical construction.
Construction/checker command receipts bind actual Git subject, input/output hashes,
start/end/exit and the original Run. They are supplemental evidence, not fabricated
native CLI Final records or an independent multi-agent review.
