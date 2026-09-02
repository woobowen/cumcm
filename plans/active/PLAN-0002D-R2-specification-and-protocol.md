# PLAN-0002D-R2 — Clean-room Specification and Prospective Protocol

Status: `IN_PROGRESS`
Phase: `PHASE-EVIDENCE-EXPANSION-002D`
Subphase: `PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL`
Owner: main agent
Started: `2026-09-02T13:02:23+08:00`
Branch: `feat/phase002d-r2-spec-protocol`
Base commit: `10073a2fe5b1512a16ab9a9c7907fb2b7f5ff765`
Predecessor: `plans/completed/PLAN-0002D-R1-failure-aware-outcomes.md`

## 1. Current state and authorization

Phase 002D-R1 is complete with a passing Decision Auditor and stable replay. Architecture remains
`null`; base selection and third-party integration are false; the sole formal Skill remains
`0.1.0-foundation`/`SCAFFOLD_ONLY`. R1 accepted exactly four mechanisms at
`SPECIFICATION_ONLY`: `accepted-versus-done-workflow-state`, `claim-evidence-support-gate`,
`hash-bound-reproducibility-manifest`, and `leakage-safe-model-comparison-gate`. This authorizes
independent clean-room specifications and a prospective comparison protocol, not implementation,
integration, performance claims, architecture selection, or Phase 003.

## 2. Purpose

Freeze complete project-authored component contracts, their single-truth interaction model, a
bounded architecture candidate set, a prospective synthetic Benchmark, metrics, pre-implementation
thresholds, ablations and an experimental protocol. Attack every artifact with isolated native
read-only Subagents, convert serious findings to tests, and automatically decide only whether an
isolated shadow prototype may be built in a later phase.

## 3. Scope and non-goals

In scope: immutable historical input binding; specification/provenance Schemas; public conformance
cases; ignored hidden seeds; deterministic generators; sealed metadata; metrics and threshold
formulas; protocol, budget and ablation freeze; adversarial audits; deterministic decisions,
Decision Audit, replay, generated reports and Draft PR delivery.

Out of scope: component or prototype implementation; formal Skill behavior changes; a second Skill
or project state; old three-arm comparison; historical CUMCM questions/answers; third-party code,
Schema, Prompt or long-text copying; API-key billing; model training/fine-tuning; architecture
selection; Phase 003; PR readiness or merge.

## 4. Clean-room and source boundary

Upstream metadata may identify a source candidate, pinned commit, consulted path, abstract problem,
abstract mechanism, license and contamination status. Formal designs must be independently phrased
from project invariants and synthetic tests. `UNKNOWN`, `UNVERIFIED` or `RESTRICTED` sources permit
only `REFERENCE_ABSTRACT_MECHANISM`. Similarity scanning is a warning, never legal proof. Candidate
repositories remain ignored and are neither executed nor copied.

## 5. Component-specification method

One versioned Schema requires purpose, accepted scope, evidence, actors, I/O, read/write sets,
pre/postconditions, invariants, failures, deterministic enforcement, stale/recovery behavior,
security/privacy/cost budgets, interactions, public/hidden/model-in-loop tests, acceptance/rejection,
rollback, migration, unknowns and risks. Four isolated authors receive only their own frozen bundle
and return raw structured JSON; the main agent validates and normalizes without altering material
recommendations.

## 6. Cross-component interaction

The interaction contract preserves `state/project_state.json` as the sole project-state truth and
defines canonical append-only Run, Claim and model-comparison records. It freezes write ownership,
data order, STALE propagation, failure precedence, retry, rollback and concurrency conflicts. No
component or Agent may declare FINAL, bypass a deterministic Gate or advance formal state directly.

## 7. Architecture candidates

Freeze two or three candidates including `ARCH-S0-RETAIN-SCAFFOLD-ONLY`; no winner is selected.
Candidates describe placement, formal Skill count, truth sources, deterministic/Agent surfaces,
flows, security, cost, maintenance, falsification and prototype-only boundaries. Whole upstream
packages and any second Skill/state authority are prohibited.

## 8. Prospective Benchmark and public/hidden separation

The Benchmark is synthetic, prospective and frozen before prototype code. Tier 1 exposes at least
16 conformance cases. Tier 2 uses targeted, interaction, valid-control and gaming families whose
exact seeds/oracles stay in ignored `benchmark-vault/phase-002d-r2/`. Tier 3 pre-registers four
model-in-loop composite families for the next phase only. Tracked files contain hashes and interface
metadata, never seeds or private oracles. Isolation is
`POLICY_AND_WORKSPACE_ISOLATED_NOT_OS_ENFORCED`.

## 9. Metrics, thresholds and abstention

Freeze HARD_SAFETY, TARGET_EFFECTIVENESS, FALSE_BLOCK, REPRODUCIBILITY, STATE_CORRECTNESS,
CLAIM_SUPPORT, LEAKAGE_PREVENTION, COST and MAINTENANCE metrics before candidate results exist.
Critical violations are noncompensatory. Other thresholds are numeric or replayable baseline-derived
formulas; candidate outcomes cannot set their own line. Material unresolved disagreement produces
`RETEST_REQUIRED` or abstention.

## 10. Prospective experiment and ablation

Stage 1 is deterministic conformance/property testing. Only passing candidates may enter the later
Stage 2 model-in-loop evaluation with identical cohort, Prompt, data, timeout, sandbox, network/MCP
policy, hidden cases and grader under blocked-randomized order. Stage 3 applies frozen automatic
adjudication. Starts equal eligible candidates × four families × two repeats, infrastructure retry
allowance is at most 25% rounded up, and the absolute cap is 30. This phase executes no stage.
Stage-1 ablation covers each component, all four together, a key interaction pair and baseline;
later model ablations are selected only by the pre-registered deterministic rule.

## 11. Cost budget

Freeze token/time overhead, retry burden, tracked code surface, state-source count, formal Skill
count and maintenance surface. Correctness hard failures cannot be offset by cost. Unknown monetary,
cached/reasoning-token, operator, queue and future implementation costs remain `UNKNOWN`.

## 12. Native Subagents and independence

Round 1 uses four peer-invisible read-only Component Spec Authors. Round 2 uses independent
interaction, Benchmark, threshold, cost and provenance prosecutors. Threshold design additionally
uses independent effectiveness, false-positive/fairness and cost/maintenance proposals before the
prosecutor. Round 3 runs a separate Decision Auditor only after every decision input is frozen.
Subagents cannot write, use web/MCP/API, see peers or expected conclusions, vote, or fabricate
evidence. Unavailability makes the protocol incomplete; the main agent does not impersonate roles.

## 13. Attack-to-test rule

Every BLOCKER/ERROR becomes a Schema-valid test request, observable deterministic test and test
evidence. Non-testable assertions stay uncertainty and cannot support acceptance. Findings remain
immutable even after their tests pass.

## 14. Automatic decisions

Generate component-spec freeze, interaction contract, candidate-set freeze, prospective Benchmark
freeze, threshold-policy freeze and shadow-prototype authorization decisions. Accepted scopes are
limited to `SPECIFICATION_FROZEN`, `CANDIDATE_SET_FROZEN`, `BENCHMARK_FROZEN`, `POLICY_FROZEN` and
`EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY`. The system may reject, request retest, report insufficient
evidence or abstain. Candidate-set acceptance is never architecture selection.

## 15. Decision Audit and replay

The independent Auditor checks historical integrity, accepted-scope boundaries, implementation
embargo, Skill immutability, threshold hindsight, Benchmark leakage, voting, architecture preselection,
third-party copying, shadow scope and route. PASS is required for any next-phase authorization.
Offline replay checks original, order, label and seed-manifest variants without network/model calls.

## 16. State migration and Phase 003 boundary

Start at `SPECIFICATION_PROTOCOL_IN_PROGRESS` with current R2 plan, null architecture and next phase,
the four accepted specification IDs, false base/integration and scaffold capability. Completion may
set `SPECIFICATION_PROTOCOL_COMPLETE`; shadow authorization may route only to
`PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`. Otherwise the route remains R2 or null. Phase 003 is
always prohibited.

## 17. Milestones and acceptance

1. **M1 start:** preflight/baseline pass; R1 plan moved to completed; R2 plan/state/freeze/embargo
   validate; focused tests pass; atomic commit, push and Draft PR creation.
2. **M2 component specifications:** four isolated author outputs validate; provenance and four
   formal specs pass public/fault tests; atomic commit and push.
3. **M3 interaction/architectures:** single-truth interaction and two-to-three candidates validate
   without selection; atomic commit and push.
4. **M4 Benchmark:** public cases, deterministic generators, ignored vault, sealed manifest,
   metamorphic/negative/interaction/gaming families pass; atomic commit and push.
5. **M5 metrics/protocol:** independent threshold inputs, frozen formulas, protocol, ablation and
   budget validate before prototypes; atomic commit and push.
6. **M6 prosecutors:** five isolated audits and threshold attacks are preserved; all serious testable
   findings have passing evidence; atomic commit and push.
7. **M7 decisions:** all six decision types are Schema-valid and hash-bound.
8. **M8 audit/replay:** independent Auditor PASS and stable deterministic variants.
9. **M9 closure:** state/reports/version/docs current; at least 70 meaningful new test nodes and
   full offline CI pass; commits and Draft PR are remotely verified.

## 18. Validation

Run all task-listed Ruff, pytest, instruction, discovery, contract, upstream, leakage, secret,
historical/R2 freeze, component, interaction, architecture, Benchmark/vault, threshold, protocol,
embargo, adjudication, audit, replay, reporting, status, strict repository, CI and Git checks.
Record command, exit, duration, execution type, result, evidence hash, blocker and model visibility.
Ordinary CI remains offline with zero native/model/API/prototype/third-party executions.

## 19. Recovery and rollback

On interruption, verify branch/worktree, historical/R2 freezes and remote SHA, then resume the first
incomplete milestone. Never mutate historical inputs or hidden vault into tracked form. After three
failed repair cycles preserve evidence and report incomplete. Published changes roll back only by
scoped `git revert`; append-only artifacts are superseded, not rewritten.

## 20. Git and PR

Inspect status, whitespace, stats and full diffs; stage explicit paths only; run focused validation
before each atomic commit. Push normally to `feat/phase002d-r2-spec-protocol`; retry TLS timeouts at
most five times with bounded backoff and at most one process-local no-proxy control. Draft PR #4
remains OPEN/DRAFT and is never readied, approved, merged, force-pushed or deleted by the agent.

## 21. Progress, findings and next step

- `2026-09-02T13:02:23+08:00`: preflight passed at clean SHA `10073a2...`; root, branch, remote,
  merged PR #3 and no open R2 PR matched; baseline passed `800 passed, 1 skipped` with strict zero
  errors/warnings and one formal Skill.
- Historical Phase 002D plan is correctly archived because its technical result was incomplete;
  the complete R1 plan is moved to completed.
- R1 and Phase 002D freezes pass; no tracked vault/upstream cache, answer leakage or secrets exist.
- `2026-09-02`: M1 passed `811 passed, 1 skipped`; commit `0831506` was pushed and Draft PR #4
  was created. R2 input-freeze manifest hash is
  `52379058863de851e34b012880229fc542150989ae1c178a09318b836737245a` and the formal Skill tree
  remained `edeeaf7312e7fc1cdc008bfa799a6127787768246c90ab4c4a569615d11dde33`.
- `2026-09-02`: M2 preserved four read-only identity-blind author outputs and sealed four Schema-valid
  project-authored specifications. Resource capacity allowed three child threads plus the main
  agent, so the fourth isolated role ran sequentially on a fresh role turn instead of a fourth
  simultaneous thread; this limitation remains an audit input. Component validation passed and the
  focused suite passed `101` tests; no component or prototype behavior was implemented.
- `2026-09-02`: M2 commit `ca06c3d` was pushed. M3 froze the single-truth interaction contract at
  hash `ed7e00ab84a547a96a12d4ba7de0584f2d58085f689e4e49b43e741ed4cb7e2b` and the three-candidate
  S0/W1/K1 set at hash `c51ea5d8b583971c8d4bc79943389264cf48a521e26f30eac7fb5d8bd497694d`.
  Validation passed with `selected_architecture=null`, one formal Skill and one project-state truth;
  the focused interaction/architecture suite passed `43` tests.
- `2026-09-02`: M3 commits `671683f` and `011efde` were pushed. M4 generated 16 balanced public
  conformance cases, 20 sealed property/adversarial cases and 4 future model-in-loop families with
  two repeats each. The ignored vault was initialized once; checks used only presence/ignore status
  and did not parse private values. The sealed manifest hash is
  `1e37df1d3717670baba83f672976a08884df79cd52d30fd47b9b18c443dd907d` at isolation level
  `POLICY_AND_WORKSPACE_ISOLATED_NOT_OS_ENFORCED`; prototype/model/API executions remain zero.
  A leakage scan initially rejected a fixture containing the physical vault path; the public
  contract now uses a logical vault identifier, and the repaired leakage, secret, contract,
  generator, vault, freeze and `35` focused tests pass.
- `2026-09-02`: M4 commit `75f4c66` was pushed. Three mutually peer-invisible read-only threshold
  designers returned RETEST_REQUIRED findings. Deterministic remediation added the pre-result
  oracle-class/stratum/seed-identity denominator map and converted each material finding to tests;
  the Benchmark manifest was prospectively superseded before prototype work and is now
  `91f12beb0c2693a0fac0ae53da20dd00e1db4ab16418d7f8254521abcde291c8`.
- `2026-09-02`: M5 froze 32 separated metrics and 32 thresholds at policy hash
  `2d193049d84456c8f2b9b6c3bde3124436ad8377f88beb9cf9d70376bfbe6fcc`; candidate metrics were
  absent. The three-arm future protocol hash is
  `202870df3a8cdb007dcaaf5722e16c7fcb668c4b92f65561e7b043c8c5d1a97c`, with Stage 1 before
  Stage 2, 24 maximum primary starts for three eligible arms, 6 fresh-retry slots, absolute cap 30,
  and pre-registered ablations. No stage was executed; focused tests passed `47` cases.
- Current milestone: M5 commit/delivery. Next legal work is five independent adversarial audits and
  deterministic finding-to-test closure.

## 22. Update rule

After each milestone, failed validation, material finding, blocker or approved design change, append
factual progress, exact evidence and acceptance impact. Never rewrite completed history or alter a
threshold after candidate results. Any plan change must precede the affected execution.
