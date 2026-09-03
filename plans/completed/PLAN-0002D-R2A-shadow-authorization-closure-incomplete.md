# PLAN-0002D-R2A — Shadow Prototype Authorization Closure

Status: `INCOMPLETE` — continued by `plans/active/PLAN-0002D-R2A-C1-historical-compatibility-and-candidate-binding.md`
Phase: `PHASE-EVIDENCE-EXPANSION-002D`
Subphase: `PHASE-002D-R2A-SHADOW-PROTOTYPE-AUTHORIZATION-CLOSURE`
Owner: main agent
Started: `2026-09-03T02:00:00+08:00`
Branch: `feat/phase002d-r2a-shadow-authorization`
Base commit: `7769a1478940305069aab07d71290a06025206d2`
Predecessor: `plans/completed/PLAN-0002D-R2-specification-and-protocol.md`

## 1. Current state and R2 evidence

R2 is merged through PR #4. Its component, interaction, candidate-set, prospective-Benchmark and
threshold/protocol prerequisite decisions are accepted at their bounded scopes. The R2 Decision
Auditor is `PASS`, replay is stable, all 29 serious findings have passing deterministic evidence,
architecture is null, base selection and third-party integration are false, and the sole formal
Skill remains `0.1.0-foundation`/`SCAFFOLD_ONLY`.

The preserved `DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2` is `RETEST_REQUIRED`. That was the
correct M7 time snapshot: the downstream R2 audit and replay did not yet exist. It is not rewritten,
reclassified, or described as erroneous. R2A may only supersede it using the subsequently frozen
audit and replay evidence.

## 2. Objective and non-goals

Close the post-audit authorization dependency without a cycle; freeze all R2 inputs; compute
eligibility; freeze an experimental-only future shadow scope; preserve independent native attacks;
convert every serious attack to deterministic evidence; generate a candidate; obtain an independent
authorization-specific audit; seal a superseding decision; replay it; and migrate formal state.

This phase does not implement or execute a prototype, alter the prospective experiment or formal
Skill, choose an architecture, expose hidden Benchmark values, run a model experiment, reuse or
execute third-party code, release the implementation embargo, enter Phase 003, merge PR #5, or
modify `main`.

## 3. Historical preservation and supersession

Every result tree through `evals/results/phase-002d-r2/`, the R2 specifications, and the R2
prospective protocol are immutable inputs. The old authorization file is bound by exact byte hash.
A new decision may use ID `DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A` only with
`supersedes` set to the old ID and `supersession_reason=POST_AUDIT_AND_REPLAY_CLOSURE`.

## 4. Authorization dependency DAG

The only legal order is L0 frozen specifications/Benchmark/policy/embargo/provenance; L1 five
prerequisite decisions; L2 R2 Decision Audit; L3 R2 replay; L4 R2A eligibility; L5 candidate
authorization; L6 authorization-specific Auditor; and L7 final seal replay plus formal transition.
Edges are validated as a directed acyclic graph. L2 never depends on L5, L6 audits L5 only, and
state migration requires both L6 `PASS` and L7 stable replay.

## 5. Preconditions and uncertainty

Eligibility is derived from frozen files and checks all 27 required predicates: bounded accepted
decisions/scopes; audit; replay; finding closure; embargo; Skill and source boundaries; zero
prototype, third-party, API and batch-model executions; null architecture; false base/integration;
one Skill; hidden commitment hygiene; two-to-three candidates with S0; three protocol stages; cap
at most 30; experimental-only scope; and continued Phase 003 prohibition.

Clean-room legal compliance, OS-enforced vault isolation, prototype effectiveness and monetary cost
remain `UNKNOWN`/unverified. They are recorded as risks and cannot be promoted to positive evidence.

## 6. Shadow scope and rollback boundary

The scope specification permits S0 as an immutable baseline adapter and future isolated W1/K1
experiments only below frozen shadow-workspace and R3-result prefixes. It denies the formal Skill,
formal state, contracts, vault, historical evidence, third-party caches and `main`. Any future
prototype must use private temporary state and output, stay undiscoverable from production, never
emit formal FINAL/Evidence Package material, and be fully removable by deleting its isolated tree.
The only positive scope is `EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY`.

## 7. Native Subagents and attack-to-test chain

Round 1 runs three peer-invisible read-only roles: dependency prosecutor, security auditor, and
protocol/cost dissent auditor. They receive frozen allowlisted bundles, cannot write, commit, push,
use nested Codex, web, MCP or APIs, see peer output or expected conclusions, and may abstain. Their
raw structured outputs are immutable. Every `BLOCKER`/`ERROR` becomes a Schema-valid test request,
deterministic test and passing/failing evidence; non-testable claims stay uncertainty. Votes never
close findings. After L5, one fresh read-only final authorization auditor reviews only its allowlist.

## 8. Candidate, audit, seal, replay and state

The deterministic candidate engine may return accepted, retest, insufficient, rejected, abstained
or stale from evidence. It cannot write formal state. The final Auditor may return `PASS`, `FAIL` or
`RETEST_REQUIRED`. Only `PASS` permits the deterministic seal. The active record reuses the existing
automated-decision truth contract and the authorization envelope; no competing decision Schema is
created. Offline replay permutes decision/evidence order and opaque labels. State advances only
after a valid seal and stable replay; architecture remains null in every outcome.

An accepted experimental decision routes only to
`PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`. Retest routes back to this R2A closure. Other outcomes
use a frozen null/R2A route. Phase 003 is never legal.

## 9. Milestones and acceptance

1. **M1 start/freeze:** preflight and baseline pass; prior plan archived; plan/state/rules updated;
   R2A input manifest, exact old-decision binding, DAG and embargo checks pass; commit, push, create
   Draft PR #5.
2. **M2 scope:** scope, path allowlist/denylist, state isolation and rollback validate with faults;
   commit and push.
3. **M3 native attacks:** three independent raw outputs and normalized findings validate; commit
   and push.
4. **M4 attack closure:** every serious finding has test request and deterministic evidence; no
   unresolved serious finding; commit and push.
5. **M5 candidate:** all preconditions and candidate record are reproducible; formal state remains
   in progress.
6. **M6 final audit:** independent auditor output is preserved; votes are absent.
7. **M7 seal:** only an audit `PASS` seals the active superseding decision and bounded route.
8. **M8 replay/state:** offline variants are stable before formal transition; generated reports
   reflect machine truth.
9. **M9 closure:** at least 35 meaningful new tests, full offline validation and CI pass; atomic
   commits are pushed; Draft PR #5 and remote SHA are verified without merge.

Phase completion means the authorization procedure is complete, not that the outcome must be
accepted. `RETEST_REQUIRED`, insufficient, rejected, abstained or stale are legal completed outputs
when their audit/replay/state records are consistent.

## 10. Recovery, rollback, Git and PR

On interruption, verify branch, clean/dirty paths, remote SHA, exact old-decision hash, R2/R2A input
freezes and the first incomplete milestone. Never regenerate historical evidence. After at most
three repair cycles, preserve failures and stop as incomplete. Published changes roll back only by
scoped `git revert`; append-only records are superseded, never rewritten.

Before every commit inspect status, whitespace, stats, full diff and staged diff; stage explicit
paths only. Push normally to the designated task branch with bounded TLS retry. PR #5 must remain
`OPEN`/`DRAFT`; no readiness, approval, merge, deletion, force push or direct `main` work is allowed.

## 11. Validation and handoff

All ten R2A CLIs support `--help` and read-only `--check`, are offline and deterministic, never read
hidden values, and return machine JSON with non-zero failures. Run focused contract/fault tests at
each milestone, then Ruff, all pytest, all repository/security/freeze/vault/embargo checks, status
render/check, strict validation and `scripts/ci.sh`. Record command, exit, duration, execution type,
evidence hash, blockers and model visibility. The final generated acceptance report and the 21-part
handoff must state zero API, batch-model, prototype and third-party executions.

## 12. Progress

- `2026-09-03`: M1 froze 539 historical files at manifest hash
  `f524f63e8c98482a85784767c9cd539f98ad286390aac8be831061d31f0a0a95`, preserved the old
  authorization at byte hash `6150252f16889d02e643384e4229b2b77e2d00480a4c51fc474218c6cb95e291`,
  and froze a 20-node/25-edge acyclic dependency graph. Focused tests passed `60`; strict validation
  passed. Commit `b6f4699` was pushed and Draft PR #5 was created `OPEN/DRAFT`.
- `2026-09-03`: M2 froze `EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY` scope hash
  `ecb4b8675817a9fac78c2f7089090b46f7930a5671cb9e27924aee01e719da26`. S0 remains an immutable
  pathless baseline; W1/K1/common and future R3 results are the only path prefixes. Formal Skill,
  state, contracts, vault, historical evidence, upstream caches and `main` are denied. Deletion-only
  rollback, private state, no discovery/production callability and zero implementation/execution are
  enforced. Scope-focused tests passed `30`; contracts and strict validation passed.
- `2026-09-03`: M3 preserved three peer-invisible native read-only audit transports and derived
  canonical hash-bound records. The roles returned `FAIL`, `FAIL`, and `RETEST_REQUIRED`; all 19
  findings remain individually visible, including 15 `BLOCKER`/`ERROR` findings with mandatory
  deterministic tests. No peer output, expected conclusion, vote, web, MCP, API, nested Codex, or
  write capability was available. Audit-bundle/output tests passed `19`; contracts passed.
- `2026-09-03`: M4 converted all 15 `BLOCKER`/`ERROR` findings into Schema-valid requests and
  deterministic evidence. Six dependency/hash findings are closed by direct validators; nine
  future runtime, output, rollback, schedule, cost, and discrimination risks remain truthfully
  `UNVERIFIED` but no longer authorize the risky operation: file writes/execution require future
  gates, and model Stage 2 has zero authorized starts pending a new freeze. Closure hash is
  `61a68a723161f46b30ac6ac2183680b009bd6d24ede6d19068449fbf8b8078f5`; current scope hash is
  `919680d3cc8578d72d4ff960b00d61750f273e22a0634a8012daa3cb2c422501`; the 20-node/25-edge DAG
  now explicitly defines authorization-evaluation precedence and hashes to
  `df07f7e7387a410e0a90a3af13da9c712ebc1621f8145282b30f5ef9d3af4a0c`. Focused tests passed
  `130`; contracts passed `71/71` valid and `61/61` invalid rejected.
- `2026-09-03`: M5 derived all 27 authorization preconditions from frozen files; `27/27` passed at
  preconditions hash `a78cceb968f03638a777b2b8464a605cd1f57e046532ce8f99d56d84b7a1c057`.
  The deterministic candidate proposes `AUTOMATED_ACCEPTED` only for the bounded experimental
  scope, with runtime gates still unsatisfied and model Stage 2 denied. Candidate hash is
  `fc8dbec82107763fb875f5e3a06e135f86dab917a9db47f953de3058d34fb6bb`. It is explicitly non-active;
  formal state, the decision log, and routing remain unchanged pending the final auditor, seal, and
  replay. Focused tests passed `139`; contracts passed `72/72` valid and `62/62` invalid rejected.
- `2026-09-03`: M6 ran the fourth native read-only final-auditor role against three successively
  frozen bundles. The first two transports returned `RETEST_REQUIRED` for conflicting scope identity
  and missing candidate-level mutation evidence; both transports and their attempted remediation
  bundles were preserved. The third and terminal transport again
  returned `RETEST_REQUIRED`, checkpoint
  `eaf0693b11c3897d9ed2fb447d31f96d9b9fc12f333d0d53165b79b83ab04a3b`, because the evidence
  timestamp predates candidate creation and does not bind the exact candidate byte/canonical hash.
  Following the bounded retry stop rule, no fourth repair was attempted; failed remediation code and
  its competing candidate contract were removed, and the current non-active M5 candidate was restored
  at hash `fc8dbec82107763fb875f5e3a06e135f86dab917a9db47f953de3058d34fb6bb`.
  The terminal historical audit bundle hash is
  `8cbaa9080949d9e1e68206295d4bd884a3b93044b5a22b56926206032c2d31a2`. No authorization seal,
  final replay, formal state transition, R3 start, architecture selection, prototype, API call,
  third-party execution, or Phase 003 transition occurred. M7-M8 are blocked by the final-audit gate;
  M9 is limited to the incomplete acceptance report and remote evidence delivery.
- `2026-09-03`: M9 terminal validation collected `1310` tests and returned `1288 passed`, `21
  failed`, `1 skipped`; `bash scripts/ci.sh` failed with the same test set. The dominant cascade is
  the R1 historical freeze comparing the live `rules/workflow_rules.yaml` task-branch pointer with
  its earlier byte hash; an additional R2 state test applies the current `2.4.0` Schema constant to
  its historical `2.3.0` state snapshot. Three bounded repair attempts were exhausted, and the final
  incomplete compatibility attempt was rolled back. Strict validation, contracts, lint/format,
  R2/R2A freezes, current R2A candidate checks, embargo, vault and generated reports pass; seal,
  replay and state transition correctly return machine-readable `BLOCKED` because the final audit is
  `RETEST_REQUIRED`.
