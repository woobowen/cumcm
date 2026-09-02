# Retry-until-success bias

A retry cannot erase its predecessor. Every attempt stays in reliability, elapsed and token cost.
Slot resolution uses the first decisive terminal outcome or earliest eligible oracle-passing
success; it never chooses the best score. A terminal predecessor prevents a later result from
rewriting the slot, even when that retry historically occurred.

The frozen Phase 002D execution contains four retries across three slots, a non-monotonic retry
queue traversal and two retries after outcomes later classified terminal. R1 preserves these as
historical protocol deviations rather than repairing history. New acquisition must reject starts
after terminal resolution and enforce its frozen per-slot/global caps.
