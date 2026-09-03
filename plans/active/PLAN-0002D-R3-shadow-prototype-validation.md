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
