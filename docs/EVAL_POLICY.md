# Evaluation policy

Historical Phase 002 compared a no-Skill baseline and two sanitized candidates on six synthetic
development tasks. Its lexical score is `STRUCTURED_COVERAGE_ONLY`, never correctness. Phase 002A
separately computes deterministic oracle correctness and process evidence. Only primary complete
cells enter comparison; failed and recovery-affected cells remain visible but cannot affect rank.
Balanced-case and repeat minima are computed from data. The engine may report insufficient evidence
or abstain, and validation/held-out results remain unavailable for direct tuning.
