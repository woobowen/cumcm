# CUMCM Modeling Evidence Lab

Evidence-first repository for one executable CUMCM modeling Skill, covering problem intake,
requirements, sources, data audit, model portfolio/baseline, experiment execution and comparison,
robustness, Final Run, Claim validation, and a reproducible evidence package for a separate paper
team.

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

The old `FAST_TRACK_IMPLEMENTATION_BLOCKED` decision and all `phase-003f` evidence remain immutable.
RC1 is a new implementation revision, not a rewrite of that history and not proof of a selected
third-party base.

Start with `AGENTS.md`, then read `GOALS.md`, `WORKFLOW.md`, the active plan, and `state/project_state.json`. Run `bash scripts/bootstrap_dev_env.sh` and `bash scripts/ci.sh` for local validation.

The exact next task is `PHASE-SKILL-DEVELOPMENT-EVAL-004-B`: select a structurally different
answer-sealed historical problem and preserve the Development/Validation/Held-out boundary. See
`docs/DEVELOPMENT_EVAL_PROTOCOL.md`.

No project license has been selected. Third-party repositories remain isolated under ignored `.cache/upstream/` and are not part of this repository.
