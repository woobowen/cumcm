# CUMCM Modeling Evidence Lab

Evidence-first repository for one executable CUMCM modeling Skill, covering problem intake,
requirements, sources, data audit, model portfolio/baseline, experiment execution and comparison,
robustness, Final Run, Claim validation, and a reproducible evidence package for a separate paper
team.

The primary competition target is the C problem. Prior evidence contains one 2023 C Development run
and one 2020 A auxiliary-transfer Development run; it does not prove broad C-problem generalization.
The active phase therefore freezes the same RC3 across three structurally different C Development
first runs, postpones all Skill changes and reference access until every first run is frozen, and
permits only one unified cross-case revision.

Current project version: `0.3.0-competition-rc3`. The sole formal Skill is
`cumcm-modeling-evidence` `0.2.0-competition-rc3` with capability `COMPETITION_RC`. New K1 and W1
revisions both pass the unchanged eight public hard Gates (117 symmetric cases each); the frozen
K1-first rule selects the project-authored deterministic evidence kernel. The formal Skill provides
14 workflows, four bounded roles, 14 templates, an offline case CLI, strict Run/Claim/comparison
bindings and STALE propagation.

The final directed integration repair validates actual input/code/output files and a resolvable Git
commit, executes models from manifest-bound raw/processed artifacts, authenticates the full case
history/evidence chain, requires a complete candidate-by-seed comparison with successful baseline,
and automatically blocks a transition when a bound dependency is stale. The Phase 004 launcher and
freeze tool bind the private workspace and reject shallow first-run manifests. Experiment execution
is authorized only after candidates exactly match the accepted registry, baseline/metric/seeds are
valid, and train/validation/test assignments are non-empty and disjoint; recomputing an invalid
freeze does not bypass that Gate. Direct validators fail closed on hostile container types, Claims
use explicit IDs, STALE chains exactly match terminal evidence/current mismatches, public artifact
wrappers cannot bypass acceptance/hash checks, and generic Final/handoff evidence is canonically
rebuilt from current artifacts.

Two structurally different project-original cases—prediction with auditable missing/outlier/leakage controls
and bounded integer resource optimization with a retained infeasible attempt—actually run through
all case-state Gates to `READY_FOR_PAPER_HANDOFF`. Thirty fixed negative scenarios fail closed. The
RC is suitable for Development-problem training under finite assurance; it does not
establish full sealed Stage 1, Stage 2 effectiveness, full ablation, external validity, production
fitness, or monetary cost. No API call, model training, fine-tuning, or third-party integration
occurred. RC1 trusted execution-code capture was limited to the bundled deterministic runner;
caller-supplied custom executors were outside RC1 assurance.

RC2 adds a Git-blob-bound case-local Python executor with automatic subprocess capture and a
separate manifest-sealing step. It was derived from a frozen Development failure and adds no
problem-specific modeling recipe. The answer-sealed RC1 first run was remotely frozen before
reference unlock; the RC2 same-case Development regression and Stress A/B/C now reach
`READY_FOR_PAPER_HANDOFF`, while remaining explicitly non-Validation and non-Held-out evidence.

RC3 is the single bounded Phase 004B revision. It makes every nonzero case subprocess exit carry a
retained failure reason even when the program already wrote diagnostic output; failed manifests
remain sealable but ineligible for comparison, Final, Claims or handoff. The answer-sealed RC2
first run was independently committed and remotely verified before unlock. A clean six-Run 2020 A
Development regression, a three-Run 2023 C cross-case replay, and mechanistic Stress A/B/C all
completed with bound capture/manifest evidence and explicit STALE probes. These are two Development
cases, not Validation or a generalization proof.

The old `FAST_TRACK_IMPLEMENTATION_BLOCKED` decision and all `phase-003f` evidence remain immutable.
RC1 is a new implementation revision, not a rewrite of that history and not proof of a selected
third-party base.

Start with `AGENTS.md`, then read `GOALS.md`, `WORKFLOW.md`, the active plan, and `state/project_state.json`. Run `bash scripts/bootstrap_dev_env.sh` and `bash scripts/ci.sh` for local validation.

The active task is `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`. Validation cannot start until
the three answer-sealed C first runs, unified postmortem, RC4-or-no-change freeze, unified
regression, and Validation rubric freeze are complete. The cancelled 2024 A attempt had no case
registration or execution evidence and is not Validation. See `docs/TARGET_PROBLEM_POLICY.md`,
`docs/DEVELOPMENT_EVAL_PROTOCOL.md`, and `plans/active/PLAN-0004C-C-target-batch-generalization.md`.

No project license has been selected. Third-party repositories remain isolated under ignored `.cache/upstream/` and are not part of this repository.
