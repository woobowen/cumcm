# PLAN-0002D-R3 — Shadow Prototype Validation

Status: `IN_PROGRESS`
Phase: `PHASE-EVIDENCE-EXPANSION-002D`
Subphase: `PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`
Owner: main agent
Started: `2026-09-03T20:59:57+08:00`
Branch: `feat/phase002d-r3-shadow-validation`
Starting commit: `69147942f5bad0877c549b3a882ab5b1e711341b`
Authorization: `DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2`
Accepted scope: `EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY`

## 1. Objective and boundary

Implement and prospectively compare only the frozen S0, W1, and K1 architectures against only the
four frozen component specifications. Component code stays under `experiments/shadow_prototypes/`;
R3-only orchestration stays under `src/cumcm_skill_lab/shadow_validation/`; results stay under
`evals/results/phase-002d-r3/`. The formal Skill, historical evidence, raw Benchmark, frozen metrics,
thresholds, protocols, and third-party material are immutable. Phase 003 is not executed.

The operational branch-name decision is `feat/phase002d-r3-shadow-validation`. It corrects only the
current live branch pointer; historical branch names and authorization records remain unchanged.

## 2. Architectures and components

- `ARCH-S0-RETAIN-SCAFFOLD-ONLY`: immutable behavior baseline with format-only adapter.
- `ARCH-W1-WORKFLOW-ONLY-GUARDS`: lightweight workflow/checklist guards using existing validators.
- `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`: minimal project-owned deterministic kernel.
- Components: accepted-versus-done workflow state; claim-evidence support; hash-bound
  reproducibility; leakage-safe model comparison.

## 3. Frozen execution design

- Stage 1: identical offline public, sealed-property, interaction, valid-control, adversarial,
  metamorphic, hard-safety, false-block, and static-cost evaluation; any hard failure is terminal.
- Stage 2: only Stage-1-eligible arms; one unscored pilot; one ChatGPT-managed Codex model/reasoning
  cohort; four composite families, two fresh repeats, blocked randomized order, at most 30 starts;
  failed attempts remain in the ledger and only classified infrastructure failures may retry.
- Stage 3: apply the frozen 32 metrics, 32 thresholds, lexicographic layers, tie-breaker, component
  ablations, Decision Audit, and offline replay. No vote or post-hoc threshold change is admissible.

## 4. Isolation, budgets, and checkpoints

Candidate processes receive ordinary case inputs only and cannot access `benchmark-vault/`, sealed
metadata, formal state writes, network, MCP, or third-party code. The grader alone may consume the
sealed interface and records only hashes, metrics, and sanitized failure classes. Public repair loops
are capped at three per W1/K1; a candidate-independent harness repair is capped at one after freeze;
the final decision audit repair is capped at one. Checkpoint and push after every model block of at
most six starts.

## 5. Milestones and acceptance

1. M1: preflight, this Plan, R3 start state, live branch pointer, baseline CI, atomic commit/push.
2. M2: R3 input freeze, common interface/harness, S0 adapter, focused tests, atomic commit/push, Draft
   PR #6.
3. M3: W1 four components, public tests, independent read-only W1 audit, commit/push.
4. M4: K1 four kernels, public tests, independent read-only K1 audit, commit/push.
5. M5: prototype freeze, sealed Stage 1, Benchmark integrity audit, eligibility, commit/push.
6. M6: cohort pilot, frozen schedule, budget, batched Stage 2 attempts and checkpoints.
7. M7: frozen metrics, hard gates, cost, and preregistered deterministic/model ablations.
8. M8: architecture/component decisions, correctness and cost dissent audits, final Decision Audit.
9. M9: replay, formal state, Phase 003 handoff if eligible, generated reports, full CI, final delivery.

Each milestone requires applicable focused tests, `git diff --check`, exact evidence hashes, no
unresolved BLOCKER, and remote delivery before its evidence is consumed downstream.

## 6. Validation

Run Ruff check/format, full pytest, instruction/Skill/contracts/leakage/secrets checks, every R3
freeze/stage/score/ablation/decision/audit/replay/state/report checker, embargo/vault checks, generated
status check, strict repository validation, full offline CI, Git whitespace/status, remote SHA, Draft
PR state, and remote CI. Record command, exit code, duration, execution type, model/arm/run counts,
evidence hash, and blocker rather than a summary-only pass.

## 7. Risks and stop conditions

The vault is policy/workspace isolated rather than OS-enforced; inability to establish the frozen
execution boundary blocks sealed evidence. Transport pilot failure after one fresh retry yields
`MODEL_INFRASTRUCTURE_BLOCKED`. Changed historical/frozen inputs yield `STALE`. Missing denominators,
unknown costs, incomplete runs, failed audit, or unstable replay prevent Phase 003 routing. Stage 1
hard failure prevents that arm from Stage 2.

## 8. Decision, handoff, and rollback

The decision engine may select S0/W1/K1, abstain, require retest, or mark stale; it must select when a
candidate uniquely satisfies the frozen policy. A successful selection emits the versioned Phase 003
handoff but performs no integration. Before publication, remove only uncommitted R3 work; published
changes use scoped `git revert`. Frozen attempts, failures, audits, decisions, and hashes remain
append-only. Update this Plan after each milestone, failed validation, blocker, or approved design
change; preserve factual history.

## 9. Progress

- `2026-09-03T20:59:57+08:00`: preflight confirmed branch/root/remote, clean worktree, HEAD equals
  `origin/main`, PR #5 merged, no current-branch PR, C2 authorization/Auditor/replay PASS, all frozen
  inputs current, one formal Skill, zero prior prototype/model execution, and baseline CI at
  `1484 passed, 1 skipped` with strict validation at zero errors/warnings. No dependency installed.
- `2026-09-03`: M1 start state and operational live branch pointer are active. One compatibility
  repair made completed C2 replay use its committed historical state/Schema evidence under the R3
  successor instead of retargeting live state. The affected 258 tests and full CI pass at
  `1484 passed, 1 skipped`; strict validation reports zero errors/warnings.
- `2026-09-03T21:31:00+08:00`: R3 input freeze
  `707af8b8456aecf45a79b3f8c86622b20459ba46f74945651ea74ec3ddb2c00b` binds the C2 authorization,
  frozen specifications/protocols, nine historical evidence trees, formal Skill, start-state Git
  snapshot, and candidate-neutral runner/scorer/grader. The immutable common interface and
  format-only S0 adapter passed all 16 public interface executions; no model or vault access ran.
- `2026-09-03`: the first full-CI pass attempt exposed authorization-time verifiers that treated
  successor R3 files as pre-C2 files. A bounded compatibility correction retains the original
  C1/C2 code hashes and replays their evidence at its historical checkpoint while current R3
  embargo enforcement remains active. The targeted 221-test set and full CI now pass at
  `1490 passed, 1 skipped`; no frozen evidence artifact was modified.
- `2026-09-03T22:18:03+08:00`: W1 implements all four public workflow checklists and completed the
  maximum three public repair loops. Its 39 focused tests, 32 S0/W1 common-interface executions,
  input-freeze check, strict validation, and full CI (`1523 passed, 1 skipped`) pass. The independent
  final W1 audit nevertheless found one uncaught malformed-input BLOCKER (`W1-FINAL-001`); the
  repair limit is exhausted, no fourth repair is performed, and W1 is recorded ineligible rather
  than silently fixed or promoted. Three native read-only audit runs occurred; none accessed hidden
  or sealed values and no model run occurred.
- `2026-09-03`: K1 initial public audit identified seven BLOCKERs and four ERRORs. Repair loop 1/3
  converts them to deterministic public tests covering trusted lifecycle graphs and dispositions,
  frozen claim vocabulary/strength and Run lineage, independently registered manifests/captures,
  frozen comparison design/attempt/access ledgers, canonical values, semantic-set invariance, and
  shadow-only execution. The same audit confirmed a candidate-neutral persistent-output confinement
  bug in the common runner. Before Prototype/Stage 1 freeze and before any sealed result existed, the
  one permitted common-harness repair restricted persistent writes to `evals/results/phase-002d-r3/`;
  all arms receive the same correction. R3 input freeze was re-signed from
  `707af8b8456aecf45a79b3f8c86622b20459ba46f74945651ea74ec3ddb2c00b` to
  `325f5a26959e1006b382a709abdc75e40244853f64941a10f8e0863a8aae2bb2`; the original remains in Git
  history, the subject state snapshot remains commit `4d55d5e`, and no frozen benchmark, metric,
  threshold, protocol, grader, scorer, hidden value, or candidate-specific result changed.

## 10. COMPETITION_FAST_TRACK_DECISION

- Reason: `COMPETITION_DEADLINE`.
- Attempted release target: `COMPETITION_RC1`; the target was not reached.
- Full R3 status: `DEFERRED_NOT_PASSED`; full sealed Stage 1, Stage 2 model-in-loop comparison,
  full ablation, full six-agent audit, and the full metric portfolio evaluation are not executed.
- Retained hard gates: malformed-input fail-closed; done-versus-accepted; exact claim-evidence
  support; hash-bound reproducibility manifest; model-comparison leakage; input immutability;
  no Prototype formal-state write; no answer, secret, or third-party contamination; end-to-end
  Skill smoke; and full repository CI.
- The fast track may select only K1 or W1 through the pre-frozen eight-gate rule at
  `evals/prospective/phase-003f/minimum_competition_architecture_gate.json`. S0 remains a
  behavior-missing baseline and cannot be presented as a complete Skill.
- Fast-track repairs were capped at two targeted loops per candidate, overriding the three-loop
  budget of the deferred full-R3 design. Both budgets are exhausted for this fast-track attempt.
- Final minimum-Gate outcome: `FAST_TRACK_IMPLEMENTATION_BLOCKED`. K1 and W1 each pass only G2 and
  G7, and each fails G1, G3, G4, G5, G6, and G8. No architecture is selected. The formal Skill is
  intentionally retained at `0.1.0-foundation` / `SCAFFOLD_ONLY`; no false RC, handoff, or Phase 003
  transition is emitted.
- The candidate-neutral common runner now verifies result case/input bindings and rejects nested
  formal outcome markers. The re-signed R3 freeze also includes common interface/public-case hashes.
- One additional read-only auditor run produced deterministic counterexamples without reading the
  hidden vault, using a model, executing third-party code, or voting on the outcome.
- The corrected public Gate executed 118 candidate cases and six candidate-composition probes. Its
  decision hash is `2ed22c0e6ba08159077ae891bfb310947fa007e84dd38fdde2af54beeef25b5d`;
  the normalized read-only audit SHA-256 is
  `d3e19c1d1e5b95843e581f928eaa52d8b9516f88dfa3f13f0d96210c19e0c54d`.
- Final local validation for this blocked fast-track record: focused Gate/R3 tests `110 passed`,
  state/report/contract focus `147 passed`, full pytest `1594 passed, 1 skipped`, strict repository
  validation `0 errors, 0 warnings`, generated report current, and `scripts/ci.sh` PASS with the same
  full-test count. The expected Gate CLI exit is 1 because no architecture is selectable.
- This decision does not assert full R3 validation, sealed Benchmark passage, Stage 2
  effectiveness, production readiness, or generalization to unseen CUMCM problems.
