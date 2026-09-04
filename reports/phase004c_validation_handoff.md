# Phase 004C Validation Handoff

## Frozen candidate

Use the sole formal Skill `cumcm-modeling-evidence` version `0.2.0-competition-rc3`, capability
`COMPETITION_RC`, architecture `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`, commit
`8a2a813ff34d8c2701c64ff9d959848e7b88c27c`, Git tree
`a4551c8aa0b6b119823f6ce9df3f0f948339bb33` and runner SHA-256
`1cdeeb04219e91dddf73eeb730782e31bef6a669061d2873137ad181b6a86f06`.

Development evidence comprises CUMCM-2023-C under RC2 plus an RC3 cross-case replay, and
CUMCM-2020-A under an answer-sealed RC2 first run followed by RC3 Development regression. Both
same-case final chains reached `READY_FOR_PAPER_HANDOFF`; both answers are now
`UNLOCKED_AFTER_FIRST_RUN`, so neither may be reused as Validation.

## Required Validation policy

Select a historical problem structurally different from both Development cases. Register it as
`VALIDATION`; keep answer access `SEALED` until the terminal result is frozen. Use the frozen RC3
commit/tree without post-result tuning. Run once under the frozen rubric and hard gates, preserving
success, blocked, rejected, infeasible and failed evidence. After observing the result, changing the
Skill and rerunning the same case may only be Development evidence, never Validation.

The rubric covers requirement coverage, physical/mathematical and numerical validity, portfolio,
execution evidence, robustness/sensitivity, Claim/handoff and contest efficiency. Missing a main
requirement, uncaptured code, major unit error, nonconverged or infeasible Final, raw mutation,
unbound Run/Claim, pre-freeze answer exposure or manually inserted result is a noncompensable hard
failure. The full Validation run limit is six hours inside a twelve-hour phase limit.

Required runtime is Python `3.11.14` with the recorded environment snapshot SHA-256
`954006bbd50c203779ee9ac2307b8935c802ca999f1c8a3c7f3c256e3ba10c36`; execution remains offline.
Actual case dependencies must be frozen before the Run. Current numerical packages include NumPy
`2.4.6`, SciPy `1.17.1`, pandas `2.3.3`, openpyxl `3.1.5`, scikit-learn `1.9.0` and statsmodels
`0.15.0`.

Known unverified areas are external validity, full ablation, production fitness, monetary cost,
mechanistic identifiability across cases and global-optimum guarantees. Machine-readable policy and
hashes are in `evals/results/phase-004b/phase004c_validation_handoff.json`.

Validation was not started. Exact next phase: `PHASE-SKILL-VALIDATION-EVAL-004-C`.
