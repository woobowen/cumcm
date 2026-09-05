# CUMCM Modeling Evidence Lab

Evidence-first repository for one executable CUMCM modeling Skill, covering problem intake,
requirements, sources, data audit, model portfolio/baseline, experiment execution and comparison,
robustness, Final Run, Claim validation, and a reproducible evidence package for a separate paper
team.

The primary competition target is the C problem. Prior evidence contains one 2023 C Development run
and one 2020 A auxiliary-transfer Development run; it does not prove broad C-problem generalization.
The active phase froze the same RC3 across three structurally different C Development first runs,
postponed every Skill change and reference access until all three runs were independently frozen,
and admitted one unified cross-case revision after the bounded postmortem.

Current repository candidate version: `0.3.0-competition-rc6`. The sole formal Skill code is
`cumcm-modeling-evidence` `0.2.0-competition-rc6` with capability `COMPETITION_RC`; the active
release state remains `0.2.0-competition-rc5-blocked` because RC6 failed its independent release
audit. New K1 and W1
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

RC4 adds one neutral selected-output contract preflight and applies the identical validator to each
exit-zero captured output. Its unified regression passed all three C batch cases, the preserved
2023 C main chain, the 2020 A auxiliary execution path, two synthetic E2E cases, the original 30
negative scenarios, and full CI. In the separate answer-sealed one-shot 2024 C Validation, 4/4
actual Runs succeeded and all six main requirements had feasible outputs, but RC4's frozen Claim
Gate required one scope to equal two different frozen strings. The Gate blocked with
`RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`; no handoff was accepted and the terminal decision is
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`. No Development regression is counted as that
Validation result.

The old `FAST_TRACK_IMPLEMENTATION_BLOCKED` decision and all `phase-003f` evidence remain immutable.
RC1 is a new implementation revision, not a rewrite of that history and not proof of a selected
third-party base.

Start with `AGENTS.md`, then read `GOALS.md`, `WORKFLOW.md`, the active plan, and `state/project_state.json`. Run `bash scripts/bootstrap_dev_env.sh` and `bash scripts/ci.sh` for local validation.

The completed predecessor is `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`. RC4 and its unified regression
are frozen; the 2024 C terminal outcome is remotely frozen and the same case cannot be rerun as
Validation. Its authorized successor was `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`. The cancelled
2024 A attempt had no case registration or execution evidence and is not Validation. See
`docs/TARGET_PROBLEM_POLICY.md`,
`docs/DEVELOPMENT_EVAL_PROTOCOL.md`, and `plans/completed/PLAN-0004C-C-target-batch-generalization.md`.

No project license has been selected. Third-party repositories remain isolated under ignored `.cache/upstream/` and are not part of this repository.

## Phase 004C2 terminal result

The case-neutral Claim implementation passed the frozen tests within two revision cycles.
Post-decision audit found an unresolved release blocker: the frozen Skill VERSION file still says
RC4 while the runner, SKILL.md and manifest say RC5. Release acceptance is BLOCKED_VERSION_METADATA;
the frozen Skill cannot be changed in this episode.
The historical RC5 freeze remains release-blocked by its inconsistent VERSION label and is
preserved as audited evidence. Phase 004C3 tested the sole K1 `COMPETITION_RC` Skill candidate
`0.2.0-competition-rc6`. Its consistency/regression bundle passed, but Auditor 1 reproduced 13
fail-open probes and found the fresh-completion controller does not operationalize per-requirement
or portfolio selection. Both formal revision cycles are exhausted. RC6 is not released; no fresh
2018/2017 input, worker or Run was started, and formal status is `RC6_RELEASE_REPAIR_BLOCKED` with
`next_phase_allowed=null`.
Release truth: `evals/results/phase-004c2/rc5_release.json`; execution record:
`plans/active/PLAN-0004C2-claim-scope-repair-and-fresh-validation.md`.
The 2024 terminal verdict and original artifacts remain unchanged.
RC5 release `24265710b3f4b154ccf6eff19614eea7fb3fb0d4` was remotely verified before
2019 official input access. The pre-run freeze was remotely delivered before all nine actual Runs.
`CUMCM-2019-C-VALIDATION-002` terminated as `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`:
Q2 requires actual airport/city observations, which are absent. Native Run/Claim/handoff contracts
passed structurally; Q4 semantic support is incomplete in the selected baseline Claim.
The frozen rubric rejected paper dispatch and the
final case state is `REJECTED`. No whole-problem completion or joint optimum is claimed.
The machine decision and terminal freeze live under
`evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002/`.
RC5, case code, rubric and neutral tests remain frozen; no model retry or later same-case Validation
is permitted. Answers remain sealed. The next phase is `null`; Held-out 004D is locked and all six
2025 access flags remain false. Later work on this case can only be Development under new scope.
