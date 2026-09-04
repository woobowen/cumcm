# Phase 004A Skill Changes

## Released candidate

- Formal Skill version: `0.2.0-competition-rc2`.
- Capability/architecture unchanged: `COMPETITION_RC`, K1 thin Skill plus deterministic kernel.
- Formal Skill discovery count remains one.

## Accepted changes

1. `execute` authorizes only `RUNNING` cases, preregistered candidates/seeds and a CASE_ROOT Python
   file whose SHA matches its repository blob at the frozen commit. Runtime is bounded to 1–900 s.
2. The runner captures start/end/elapsed time, exit, exact argv, allowlisted environment,
   stdout/stderr/output hashes, inputs, code, configuration and freeze registry. Run IDs are
   immutable.
3. `seal-run` revalidates capture bytes before producing a manifest; custom case code without a
   capture is rejected. Later log or output mutation invalidates the manifest and propagates STALE.
4. An unlocked same-case run is accepted only when explicitly labeled `DEVELOPMENT_REGRESSION` and
   bound to the immutable first-run freeze SHA. It cannot be represented as blind, Validation or
   Held-out evidence.

The case-owned model and Stress transformer are outside `.agents/skills/`; they are not reusable
Skill policy. Generic execution/capture tests, two original synthetic E2E cases and all 30 negative
scenarios pass in focused testing.
