# PLAN-0002D-R2A-C1 — Historical Compatibility and Candidate-Bound Authorization Closure

Status: `IN_PROGRESS`
Phase: `PHASE-EVIDENCE-EXPANSION-002D`
Subphase: `PHASE-002D-R2A-C1-HISTORICAL-COMPATIBILITY-AND-CANDIDATE-BOUND-AUTHORIZATION-CLOSURE`
Owner: main agent
Started: `2026-09-03T14:26:16+08:00`
Branch: `feat/phase002d-r2a-shadow-authorization`
Starting commit: `2d117985404b21abd7f0c3a10258731e06f77852`
Draft PR: `#5`
Predecessor: `plans/completed/PLAN-0002D-R2A-shadow-authorization-closure-incomplete.md`

## 1. Current failure state

The starting baseline collected 1310 tests and returned `1288 passed, 21 failed, 1 skipped`.
Twenty failures cascade from the R1 freeze verifier comparing the historical
`rules/workflow_rules.yaml` byte hash with the current task-branch pointer. One direct failure
validates a historical R2-derived `schema_version=2.3.0` state with the current 2.4.0 contract.
Strict repository validation and Ruff pass, but full CI and remote CI fail. Terminal finding
`R2A-FINAL-002` remains preserved: the old mutation evidence predates the old candidate and does
not bind its bytes or canonical payload.

## 2. Objective

Repair historical verification without changing historical decisions; restore full offline CI;
create and freeze a new C1 candidate; build a post-freeze, exact-candidate evidence chain; obtain
independent audits; seal only after a final Auditor `PASS`; replay; and transition formal state.
Closure completeness is independent of whether the deterministic authorization result is accept,
retest, insufficient, rejected, abstained, or stale.

## 3. Non-goals and hard boundaries

Do not implement or execute a Shadow Prototype, alter the formal Skill, select an architecture,
integrate third-party code, read hidden Benchmark values, run a real model-in-loop experiment, use
an API key, enter Phase 003, merge or ready PR #5, rewrite published history, or modify `main`.

## 4. Historical freeze model

Every classified path uses exactly one versioned mode: `SUBJECT_COMMIT_BLOB` proves the recorded
historical bytes; `CURRENT_TREE_IMMUTABLE` additionally proves current bytes are identical;
`LIVE_SEMANTIC_POINTER` validates the historical bytes and current contract while permitting only
explicit field paths; `DERIVED_OBSERVATION` is recomputed from its authority and is never historical
truth. Missing objects, paths, policies, hashes, or validators fail closed with no live-file
fallback and no whole-file ignore.

## 5. Live pointer model

For `rules/workflow_rules.yaml`, only `git_delivery.preferred_task_branch` may differ from the R1
subject blob. Remote name, repository, URL, protected `main`, `allow_force_push=false`,
`allow_agent_merge=false`, and every other field remain invariant. YAML mapping order is semantic;
byte-sensitive immutable artifacts remain byte-hashed.

## 6. Versioned Schema model

Read `state.schema_version` before validation. Historical states resolve
`contracts/project_state.schema.json` from their explicit snapshot commit, bind the Schema bytes and
commit, and require matching Schema `version` and `$id`. Current state uses only the current 2.4.0
Schema. Unknown versions, missing objects, hash drift, downgrade, and cross-version substitution
fail closed. Any comparison migration is pure, derived, deterministic, security-preserving, and
never rewrites its source.

## 7. Preserved R2A evidence

The old non-active candidate, its file SHA and canonical hash, all three old final-Auditor outputs,
the terminal `R2A-FINAL-002` record, failed-remediation audit trail, old freezes, and old acceptance
report remain immutable historical context. They cannot activate or prove C1.

## 8. Candidate revision model

C1 uses candidate ID `CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C1` and proposed decision ID
`DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C1`. It supersedes only the active R2
`RETEST_REQUIRED` decision and separately records replacement of the non-active R2A candidate. C1
is never modified after freeze. At most one C2 may be created after a deterministic C1 defect, with
a wholly new evidence chain; C3 is prohibited.

## 9. Candidate hash contract

The freeze manifest stores raw `candidate_file_sha256` and a distinct
`canonical_candidate_hash`. Canonicalization is versioned UTF-8 JSON with sorted object keys and
fixed separators; arrays preserve declared order; timestamps are included; only the explicitly
reserved external hash fields are excluded; unknown fields are never discarded. The candidate does
not self-reference either final hash.

## 10. Monotonic evidence chain

The required sequence is L0 input freeze; L1 compatibility/Schema CI evidence; L2 candidate; L3
candidate freeze; L4 preconditions; L5 test plan; L6 mutation evidence; L7 closure; L8 final bundle;
L9 final audit; L10 seal; L11 replay; L12 state transition. Every L4+ artifact binds candidate ID,
file SHA, canonical hash, freeze hash, exact parent hash, and strictly increasing sequence index.
Sequence and hashes, not timestamps, prove order.

## 11. Candidate-bound preconditions

Recompute after L3 and bind all five R2 prerequisite decisions, R2 Audit and replay, serious-finding
closure, embargo, formal Skill, Benchmark, threshold, protocol, null/false selection boundaries, one
formal Skill, and zero prototype/API/model/third-party executions. The old 27/27 record is input only.

## 12. Candidate-bound attacks and tests

Use read-only copies of frozen candidate bytes and mutate only temporary in-memory or temporary-file
copies. Cover byte and semantic drift, identity, scope, route, selection, integration, vault/Skill
access, discovery, supersession, wrong candidate, pre-freeze evidence, missing hashes, parent/order
breaks, audit-bundle substitution, and report hardcoding. Each result records test code/input/output
hashes, exit code, oracle, and its chain position.

## 13. Native independent roles

After M3 full CI passes, run peer-invisible read-only
`historical_freeze_semantics_auditor`, `schema_version_compatibility_auditor`, and
`candidate_binding_prosecutor`. They cannot write, commit, push, use nested Codex, web, MCP, APIs,
peer outputs, expected conclusions, or votes; they may abstain. Convert each BLOCKER/ERROR finding
to a deterministic test. Run a fresh `final_shadow_authorization_auditor` only after L8.

## 14. Final audit, seal, replay, and state

The final bundle binds the exact candidate bytes/canonical payload and every prerequisite/evidence
hash. Only a structurally valid final Auditor `PASS` permits a seal. The active decision uses the
existing automated-decision contract, never chooses an architecture, and preserves Phase 003
prohibition. Replay covers original rebuild, order/label permutations, repeated canonicalization,
historical Schema resolution, and live-pointer normalization. Formal state changes only after stable
replay and full CI.

## 15. Milestones and acceptance

1. **M1 baseline/start:** record preflight and 21 failures; archive the old incomplete plan; create
   this plan, L0 freeze and C1 start state; focused validation; atomic commit and push.
2. **M2 history:** implement modes/policy and workflow field allowlist; all historical freeze tests
   pass; atomic commit and push.
3. **M3 Schema:** implement commit/hash/version-aware resolver and pure migration guard; all original
   21 failures, full pytest, strict validation, and CI pass; atomic commit and push.
4. **M4 compatibility audits:** run the first three independent roles only now; preserve outputs,
   turn serious findings into tests, close or fail closed; atomic commit and push.
5. **M5 C1:** deterministically generate L2, freeze L3 bytes and canonical payload, verify immutability;
   atomic commit and push.
6. **M6 bound evidence:** produce L4-L7 records and the candidate-binding prosecution; all mutations
   and chain checks pass; atomic commit and push.
7. **M7 bundle:** generate L8 only after every prerequisite and audit gate passes.
8. **M8 final audit:** run one fresh exact-candidate auditor. If it exposes a candidate logic defect,
   preserve C1 and repeat M5-M8 once as C2; otherwise stop on non-PASS.
9. **M9 decision:** after Auditor PASS, seal L10, replay L11, then transition L12 without architecture
   selection or implementation.
10. **M10 acceptance:** generate input-driven reports, run every required validation, commit, push,
    update the same Draft PR, and verify remote SHA and remote CI.

## 16. Repair limits and stop conditions

Each compatibility root cause has at most three focused repair loops. A third failure stops as
`HISTORICAL_COMPATIBILITY_INCOMPLETE`. Candidate revisions stop after C2 as
`SHADOW_AUTHORIZATION_CLOSURE_INCOMPLETE`. Missing/failing freeze, serious finding, final audit,
replay, CI, remote delivery, or immutability evidence blocks all dependent steps.

## 17. Interruption recovery

Resume by checking branch/worktree/remote SHA, L0 freeze, immutable old-tree hashes, formal Skill
hash, latest committed sequence record, and first missing milestone. Never reconstruct evidence
from caches, stash, Trash, or untracked remediation. A committed artifact is consumed only after its
recorded predecessor verifies.

## 18. Rollback

Before sealing, discard only uncommitted C1 work or append an explicit incomplete record. Published
changes use scoped `git revert`, never history rewriting. Frozen candidates, audits, and decisions
are preserved; a defect creates the next allowed revision instead of modifying an artifact in place.

## 19. Git and Draft PR #5

Inspect unstaged and staged status, full diffs, stats, and whitespace before each atomic commit;
stage explicit paths only. Push normally to the configured feature branch and verify the remote SHA.
PR #5 stays OPEN/DRAFT. No rebase, force push, approval, readiness, merge, branch deletion, or direct
`main` commit is permitted.

## 20. R3 boundary

Only an audited `AUTOMATED_ACCEPTED` decision with scope
`EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY` may route to
`PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`. This task records that route but does not enter or
execute R3. Non-accept outcomes use the frozen C1 route or null.

## 21. Phase 003 prohibition

Phase 003 is prohibited for every outcome. Formal Skill capability stays `SCAFFOLD_ONLY`, the
architecture stays null, base selection and third-party integration stay false, and implementation
and execution counters stay zero.

## 22. Validation evidence

Every validation record contains command, exit code, duration, execution type, result, evidence
hash, and blocker. Required final validation includes Ruff, all pytest, instruction/Skill/contracts,
upstream/leakage/secrets, all R2/R2A/C1 freezes, compatibility, old R2A generators, candidate-bound
generators, audit/seal/replay/state, embargo/vault, status render/check, strict repository validation,
CI, Git whitespace, remote SHA, Draft PR state, and remote CI.

## 23. Progress

- `2026-09-03T14:26:16+08:00`: preflight confirmed expected root, branch, clean starting commit,
  origin, Draft PR #5, formal boundaries, and failed remote CI. Baseline reproduced exactly
  `21 failed, 1288 passed, 1 skipped`; no dependency was installed.
- `2026-09-03`: M2 implemented four explicit historical verification modes and a contract-validated
  path policy. Both the R1 and Phase 002D freeze verifiers now read recorded Git objects, keep
  historical result trees byte-immutable, and allow only the workflow task-branch pointer to change
  semantically. Fifteen focused attack tests and all 48 affected historical tests pass; the 20-test
  history cascade is fixed. Compatibility record hash is
  `7b7a961bc0fb82aa6a4e263109fcdfa1d45d3bd53131309f6486c5ffee00037b`.
- `2026-09-03`: M3 added a commit/hash/version-aware `SchemaVersionResolver`. Historical 2.1, 2.2,
  and 2.3 states validate only against their exact committed Schemas; current 2.4 validates only
  against the L0-frozen current Schema. A non-authoritative pure 2.3-to-2.4 comparison migration
  preserves security fields and source bytes. The original failing nodes pass `56/56`, the combined
  freeze/state/Schema selection passes `162`, full pytest passes `1339` with one skip, CI exits zero,
  and strict validation reports zero errors/warnings. Schema resolution record hash is
  `3b39684cb4ba607c0826956ea7155e416754261a9ad65ff98ce0a5775040621c`.
- `2026-09-03`: M4 ran three independent native read-only audits without peer visibility, web,
  MCP, API, nested Codex, writes, votes, or an expected conclusion. Historical and Schema auditors
  returned `RETEST`; the pre-candidate prosecutor correctly returned `ABSTAIN`. Five serious
  compatibility findings became deterministic tests and were closed: immutable-root subject
  retargeting, duplicate YAML keys, missing C1 state namespace, wrong C1 freeze identity, and
  migration target-Schema validation. The derived-observation warning was also closed. Candidate
  findings remain explicitly deferred to M5/M6 and ABSTAIN is not treated as PASS. Historical
  compatibility hash is `e95a81fa08a4b2e2c496b9aee95cdb5eb4ac49eebd94de8d8e5ca9554aa85037`,
  Schema resolution hash is `7c811862095ee93945fc04afdc17cab31843b95fd5b3920b05cc7bce533b6462`,
  and compatibility-audit closure hash is
  `0e923c8c580cad513ba91fcfaf2656f67c4c092628e34252d7e1e136e7c57617`.
  One M4 repair loop fixed missing contract fixtures; the rerun passed `1352` tests with one skip,
  full CI exited zero, and strict validation reported zero errors/warnings.
- `2026-09-03`: M5 deterministically generated the non-active C1 candidate from passing frozen
  prerequisites, without candidate-specific preconditions or evidence. The candidate contains no
  self hash or timestamp. Its independent freeze records byte SHA-256
  `b02d963794ef3df29c0971083eaad957f80f7b421f05fb79b7f3189ff51eac8a`, canonical hash
  `d74ea54edf38f37d6506b066c7cd8a52ae31dddd189e3da8fd34a4c083b49702`, and freeze hash
  `cdc4142c3313d159cdc8c7b83ed234484c9daab7454e8a3c902e6486be174011`. Sixteen focused
  candidate/freeze tests pass; the formal Skill hash remains unchanged.
- `2026-09-03`: M6 regenerated 23/23 post-freeze preconditions and 30/30 exact-candidate mutation
  results. The prosecutor's first inspection of L3-L7 returned `FAIL` with six serious findings;
  its output hash `3a55c2d234fd0dd553d0187620c3b91f99fa6bda919650f60db7315c83218afd`
  remains preserved rather than relabeled. One deterministic repair loop made the C1 candidate path
  write-once, used actual mutated bytes and bundle/report/state validators, rejected rehashed failed
  preconditions, recomputed post-freeze embargo/runtime observations, and bound closure claims to
  the resulting tests. The candidate bytes and freeze stayed unchanged. Preconditions hash is
  `32bd8ae102a2d3f4173620fca5f610fa7180a289a89163c7439140680ae1d7d0`, evidence hash is
  `c7e8b9f8794421096974c2db141bdab38e20f3a70ec218bb4e198766635c962c`, and closure hash is
  `ba420be53a7dbaccd84e2137599f1e77821cc92018970b1a16f2e97669cc9e3d` with no unresolved
  finding. Focused tests pass `48/48`; full pytest and CI pass `1400` tests with one skip, and strict
  validation reports zero errors/warnings.
