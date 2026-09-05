# Phase 004C4 acceptance report

## Final disposition

`C_TARGET_VALIDATION_FAILED`.

Competition RC7 is a valid remotely frozen release, but the answer-sealed fresh C Validation did
not produce an accepted Final Run or paper handoff. The sole actual controller invocation blocked
at `GATE_FINALIZATION`; the read-only integrity audit then found an additional false semantic
support declaration. These are separate from release acceptance. The exact next phase is
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`; 004D is not authorized.

## Starting checkpoint and historical preservation

- Branch: `feat/phase004c2-claim-scope-repair-validation-2019c`.
- Starting HEAD/remote: `7060ab136b88a158be6dfe3b46801e6cc2c65c64`.
- Draft PR: #10, OPEN/DRAFT/MERGEABLE at preflight.
- Starting active release: `0.2.0-competition-rc5-blocked`.
- Blocked candidate: `0.2.0-competition-rc6`, tree
  `0d0d65a7148d146424e31318ba003bdab80db6e5`.
- Inherited blockers: acquisition fail-open, portfolio-selection fail-open, semantic-binding
  fail-open, vacuous compatibility, and ineffective per-requirement execution.
- Baseline local CI: exit 0, pytest `2009 passed / 1 skipped` in 293.37 seconds, strict 0 errors / 0
  warnings.

RC5's version mismatch, the RC6 release block and its two exhausted cycles, the 57 frozen neutral
tests, the original 13 Auditor probes, the 2019 and 2024 terminal histories, their Runs/Claims/
handoffs/freezes, and the 2025 reservation remain unchanged. No old verdict was promoted and no old
Validation was rerun. Formal Skill count remains one and `third_party_integrated=false`.

## Actual-controller repair and gate trace

The real completion entrypoint is `scripts/finalize_fresh_c_validation.py`, backed by the formal
runner `.agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py`. RC6's executable path had
invented a `GLOBAL_JOINT` selection, reused one Run for every requirement, declared every Claim
`DESCRIPTIVE`, defaulted evidence to `PROVIDED_EMPIRICAL`, and assumed positive policy exposure.
Strict helper behavior therefore did not control completion.

Implementation commit `cd02e61994b906364789c65609de695b6912f1c7` removed those defaults and made
the controller read authoritative requirement, source, audit, sufficiency, plan, capture/manifest,
comparison, selection, semantic, final and handoff artifacts. Missing or inconsistent evidence now
blocks. The actual ordered trace is:

1. `GATE_PROBLEM_REQUIREMENT` — `cumcm_case.validate_runtime_requirements`.
2. `GATE_SOURCE_EVIDENCE` — `cumcm_case.validate_runtime_sources`.
3. `GATE_DATA_SUFFICIENCY_PREFLIGHT` — `cumcm_case.validate_data_sufficiency_record`.
4. `GATE_COMPARISON_SELECTION` — capture registry plus requirement selection.
5. `GATE_RUN_ELIGIBILITY` — `cumcm_case.validate_runtime_run_eligibility`.
6. `GATE_COMPATIBILITY_PORTFOLIO` —
   `cumcm_case.validate_runtime_selection_compatibility`.
7. `GATE_SEMANTIC_CLAIM` — `cumcm_case.validate_runtime_semantic_claims`.
8. `GATE_AGGREGATE_CLAIM` — `cumcm_case.validate_runtime_aggregate_mapping`.
9. `GATE_FINALIZATION` — selected-test payload and final/Claim checks.
10. `GATE_HANDOFF` — `cumcm_case.validate_handoff`.

Trace v1 binds case/controller identity, state and artifact hashes, implementation entrypoints,
per-Gate input/output hashes, result/reason/duration, disposition and canonical trace hash. It is
evidence of the actual path, not a second state truth. Neutral successes execute all ten Gates. The
fresh negative trace executes Gates 1–9, blocks at Gate 9, and correctly omits Gate 10.

## Frozen black-box matrix

The known matrix SHA-256 is
`d28276eaf6616b808c6d5700d27e66f731ed4b33e21d8796d0ea47fe36d40eb2`. Each probe invokes the
formal CLI over an actual case workspace and verifies exit, structured reason, state
non-progression, rejected handoff, immutable input, invoked Gate and non-leakage.

| Probe | Mutation | Expected and actual reason | Result |
|---|---|---|---|
| AC-001 | external forbidden with acquired empirical only | `RC_EXTERNAL_DATA_POLICY_FORBIDDEN` | PASS/BLOCK |
| AC-002 | incomplete acquisition plan | `RC_DATA_ACQUISITION_PLAN_INCOMPLETE` | PASS/BLOCK |
| AC-003 | split coverage without registered composition | `RC_DATA_SOURCE_COMPOSITION_UNREGISTERED` | PASS/BLOCK |
| AC-004 | dependent Runs without bridge | `RC_SELECTION_DEPENDENCY_BRIDGE_MISSING` | PASS/BLOCK |
| AC-005 | portfolio/shared hashes missing | `RC_SELECTION_PORTFOLIO_HASHES_MISSING` | PASS/BLOCK |
| AC-006 | declared shared hashes mismatch manifests | `RC_SELECTION_PORTFOLIO_HASH_MISMATCH` | PASS/BLOCK |
| AC-007 | failed/unsealed/stale/non-current selected Run | `RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS` | PASS/BLOCK |
| AC-008 | selected Run lacks requirement coverage | `RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH` | PASS/BLOCK |
| AC-009 | selected output owned by another Run | `RC_REQUIREMENT_SELECTED_OUTPUT_NOT_OWNED` | PASS/BLOCK |
| AC-010 | required metric binding absent | `RC_CLAIM_METRIC_BINDING_MISSING` | PASS/BLOCK |
| AC-011 | `scope_bounded=false` | `RC_CLAIM_SCOPE_UNBOUNDED` | PASS/BLOCK |
| AC-012 | aggregate maps requirement to wrong Claim | `RC_AGGREGATE_CLAIM_MAPPING_INVALID` | PASS/BLOCK |
| AC-013 | unknown compatibility/non-bijection | `RC_EVIDENCE_COMPATIBILITY_KIND_INVALID` | PASS/BLOCK |

Final known-probe result is 14/14 including freeze integrity. Data sufficiency now supports only a
conjunctively sufficient `SINGLE_SOURCE` or an explicit `REGISTERED_COMPOSITION`; forbidden
external evidence, incomplete acquisition, unregistered composition, simulation-as-empirical and
partial coverage cannot complete. `GLOBAL_JOINT`, `PER_REQUIREMENT` and `JOINT_PORTFOLIO` are
operational and bind actual manifests, inputs, scenarios, dependencies, outputs and compatibility.
Claims bind type-specific support predicates, current successful sealed Runs, owned output/metric,
bounded scope, policy exposure/comparator/cost/benefit when required, counter-evidence and exact
aggregate mapping.

## Neutral E2E and adversarial audit

The neutral E2E test hash is
`1d92eadec573a81f90e18fef8a66f86d5b3e1f3fb64fd3faae0dbd5255c8969d`.

- Case A: valid `PER_REQUIREMENT` selection reaches `READY_FOR_PAPER_HANDOFF`; legal order
  permutations are stable and wrong Run/output/metric bindings block.
- Case B: valid `JOINT_PORTFOLIO` reaches handoff; missing/mismatched shared or scenario hashes,
  missing dependency bridges and incompatible constraints block.
- Case C: registered data composition reaches handoff; forbidden external evidence,
  simulation-as-empirical, unregistered composition and `PARTIAL` coverage block.

All 17 neutral E2E tests pass and traces bind the correct paths. Identity-separated prosecutor
Gauss supplied five further attacks against commit `557f0972e14773fdf362c9549adb7d54c5abae6b`:
comparison/selection split brain, late invalid selected-test base64, manifest retention after later
portfolio rejection, coordinated scenario-hash tampering, and self-attested policy evidence. All
five reproduced before repair. Repair loop 1/3 closed them at
`cd02e61994b906364789c65609de695b6912f1c7`; adversarial 6/6 and the combined controller matrix
94/94 pass. No RC7-release audit finding remained unresolved. Frozen adversarial matrix SHA-256 is
`bb358a40d6cfe388376fe757bcabfa16382c19026e02751e908a6d2a53773736`.

## RC7 release and regressions

- Project version: `0.3.0-competition-rc7`.
- Skill version: `0.2.0-competition-rc7`.
- Implementation commit: `cd02e61994b906364789c65609de695b6912f1c7`.
- Skill tree: `0b0e001c6bd12d605ad1e1e3fbfb1e4e9b1486e045b9e81c3d4e15f7d9f8f056`.
- Runner SHA-256: `fda1db2fbc709ea85967a1363abd649fcc0111f2bd83b72e8bd65469cc478dc4`.
- Release manifest SHA-256:
  `747d6c47d89855dcc0acddd96593d2076c28e26b1b3dbd90a1fad8425f058434`.
- Release commit/remote SHA: `22abe92d2b5da2e3f1be3161e8376fb83b0cee0a`.

Candidate and live checkers both exited zero. Candidate evidence includes 14 known probes, 6
adversarial tests, 17 neutral E2E, 57 frozen RC6 cases, 239 focused regressions, two synthetic E2E,
30 negatives, hardcoding/discovery/leakage/secrets checks, full pytest, strict and local CI. The
post-release checker-only compatibility repair did not change the Skill tree; its full CI passed
`2063 passed / 1 skipped` in 309.12 seconds with strict 0/0.

Historical regression evidence SHA-256 is
`f15a7df4171fc7e6f6eceb8f7b4a5f58c7381eeb7c297685f73dcc21bbb033cc`: 2020–2023 C and 2020 A
replays pass without new model Runs or history mutation; 2019 and 2024 diagnostics pass read-only
without changing their negative terminal outcomes; two synthetic E2E reach handoff; 30/30 original
negatives have zero unhandled exceptions or sensitive emissions.

## Fresh registration and pre-run freeze

The preferred 2018 C title was verified as “大型百货商场会员画像描绘”, but the official C package
contained only its problem and a notice; Attachments 1–5 named by the problem were unavailable.
Preflight reason `C_INPUT_ATTACHMENTS_UNAVAILABLE_FROM_OFFICIAL_ARCHIVE` activated the
preregistered official-input fallback before any Run.

Fallback `CUMCM-2017-C-VALIDATION-003F`, “颜色与物质浓度辨识”, contains the official problem,
`Data1.xls`, `Data2.xls` and variable dictionary. Problem SHA-256 is
`f447d3ab2c5a9c70e21a52cf9fa7ccfde4b243615cd1dbfc7d154e9415615adf`; data SHA-256 values are
`ee7982ae98ee3d3f9a5762d49e2fa6a780db61ad25fcb09519228d86689636ad`,
`6766f5317fd256f86ce28c2c46e101a3c7057af84b9419158bbe824c8c36d723`, and
`bb46f621f6a0aa4d504de3493e92521ce63bb3d78a959f3196dc9b83637acbdf`. Raw inputs remain ignored.
No answer, solution or reference was accessed; model prior is
`MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`.

The remotely delivered pre-run freeze binds RC7, problem/data/environment, evidence requirements,
three selection modes, rubric, exact 3-candidate by 3-seed matrix and 14,400-second timebox. Freeze
SHA-256 is `9c078468da856353a7104e6eb4a6deec273f1aae81f6537deedbfc840703940b`;
freeze/remote commit is `8cbc0c5702ba7c7d0ef536dd4b4eced7e6d5dcda`; successor delivery commit is
`28c87994e880500720e2686c3cfe6ade8fcfc7b8`.

## Fourteen-stage episode

| Stage | Status | Artifact/time | Failure/recovery |
|---|---|---|---|
| 1 Problem intake | PASS | `problem/problem_requirements.json`, pre-run | none |
| 2 Requirement decomposition | PASS | same, pre-run | none |
| 3 Source planning | PASS | `research/source_ledger.json`, pre-run | none |
| 4 Assumptions/symbols | PASS | `models/assumptions_and_symbols.json`, pre-run | none |
| 5 Data audit | PASS_WITH_LIMITATIONS | `data/data_audit.json`, pre-run | none |
| 6 Model portfolio | PASS | `models/model_candidates.json`, pre-run | none |
| 7 Baseline | PASS | `experiments/experiment_plan.json`, pre-run | none |
| 8 Experiment design | PASS | same, pre-run | none |
| 9 Execution | PASS_9_OF_9 | 22:28:38.507–22:30:07.996 | none |
| 10 Comparison | PASS_DEVELOPMENT_SELECTION | `results/requirement_selection.json` | none |
| 11 Robustness | PASS_DEVELOPMENT_SCOPE | `results/robustness.json` | none |
| 12 Final Run | BLOCK | 22:33:20, `controller_outcome.json` | finalization interface unsatisfied; no recovery |
| 13 Claim evidence | REPORTED_PASS_PRE_FINAL_NOT_ACCEPTED | `semantic_claim_support.json` | later audit found HF22; no recovery |
| 14 Paper handoff | NOT_REACHED_BLOCK | `modeling_to_paper.json` | Gate 10 absent/unapproved; no recovery |

The formal episode ran 592 seconds, within 14,400 seconds. One-shot was preserved: 9 planned and 9
actual first invocations, 9 successes, zero retry, zero candidate/parameter change, zero sealed-test
access, and no post-result tuning.

## Actual models, Runs and selection

The three candidates were `BASELINE_MEDIAN`, `RIDGE_LINEAR` and `KERNEL_RBF_RIDGE`; each ran seeds
17001, 17017 and 17033. All captures exited zero, all manifests validate and all independent
recomputations pass.

| Run | Capture SHA-256 | Manifest SHA-256 | Result |
|---|---|---|---|
| `RUN-BASELINE_MEDIAN-17001` | `d6305d85506d...bac3c` | `e924371c38c0...8cd26` | SUCCESS |
| `RUN-BASELINE_MEDIAN-17017` | `6cd1e1838b02...4808f` | `e3e62e0201f4...7dbde` | SUCCESS |
| `RUN-BASELINE_MEDIAN-17033` | `684269e63bac...c098` | `f2106a7d889b...3e5ad` | SUCCESS |
| `RUN-RIDGE_LINEAR-17001` | `e3481ce8b9fb...d425` | `1a5fb820109c...d79a` | SUCCESS |
| `RUN-RIDGE_LINEAR-17017` | `03869b531360...58b` | `e106e2adf98a...eccf0` | SUCCESS |
| `RUN-RIDGE_LINEAR-17033` | `d5ee29c9e683...b092` | `28e918dc085c...dbf2` | SUCCESS |
| `RUN-KERNEL_RBF_RIDGE-17001` | `2169022f9504...c5af` | `cda7846baefd...a2d7` | SUCCESS |
| `RUN-KERNEL_RBF_RIDGE-17017` | `90f79cb60eed...9ff5` | `577ca39ac98a...5d44` | SUCCESS |
| `RUN-KERNEL_RBF_RIDGE-17033` | `7c2dba1b6a81...7573` | `0ea99e1593da...e78` | SUCCESS |

Development `PER_REQUIREMENT` selection chose:

- REQ1 → `RUN-RIDGE_LINEAR-17001`, grouped macro NMAE `0.281780084091` versus baseline
  `0.438608779843` and kernel `0.367234134016`.
- REQ2 → `RUN-KERNEL_RBF_RIDGE-17001`, grouped MAE `30.0363373862` ppm versus baseline `80.0`
  and ridge `31.0760616748`.
- REQ3 → the exact REQ2 kernel Run through `INHERIT_REQ2_EXACT_RUN`; it carries sample-size and
  feature-dimension ablations and inherits the REQ2 development metric.

These are grouped development/out-of-concentration metrics, not held-out final-test credit.
Selection decision hash is
`44805ce05649f29e855c6a043f34403e5c62585ca7955c3558ad04a0e4bdcc5b`.

## Controller terminal, Claims, audit and decision

The main orchestrator invoked the actual controller exactly once. Gates 1–8 reported PASS;
`GATE_FINALIZATION` returned `RC_GATE_EXECUTION_FAILED`; `GATE_HANDOFF` was not reached. State hash
before/after remained
`cc5c81bc50d25a07425c242e49d595fb57556be235d2e20ece391d41f91fef80`; no accepted Final Claim
package or handoff exists. Trace file SHA-256 is
`57ae4e788f0bfb30d53c2fa5343f2d9f49aa7707a6eb355fbc933ed5b71985da`; canonical trace hash is
`4271f4db556fab99e1342c1e3bc5893a083b85209de19cd707eb01de5f963574`.

The released execute CLI has no final-phase/test-authorization input, while the controller requires
`sealed_test_metrics_b64` in an honest selected output. The frozen ledger permits only the nine
selection attempts. Mutating output or adding a result-derived tenth Run would violate the
one-shot. The terminal decision therefore records non-compensable HF14, HF21 and HF23.

Identity-separated read-only auditor McClintock confirmed RC7 identity/tree, chronology, timebox,
three requirements, data sufficiency, selection, 9/9 Run integrity, terminal rejection, no tuning,
no post-freeze Run and no 2025 access. It returned `CHALLENGE` because REQ2's semantic artifact
declares `held_out_test_valid=true`, while selected output SHA-256
`78408903d0dc49c801c12c6fb76c8c0c81af86f7e587be5089aa76c800acb57e` says
`DEVELOPMENT_GROUPED_OOS`, test access `NOT_AUTHORIZED/0`, and `held_out_test_valid=false`. Frozen
builder SHA-256 `f854056e0521f176e4d7ab37b80a883621f2869200de8f596230e7c6a21cf9f7`
created the positive predicate unconditionally; the semantic validator trusted it instead of
cross-binding it to authoritative output facts. This is
`HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION`.

HF22 is a post-freeze additional blocker, not a rewrite of the decision. Audit SHA-256 is
`57f682820e0280d510bc0468f2269f86fa5901fe19737cd54521c7dbbbaf63d3`; challenge SHA-256 is
`140228ebd1c499c98319eff4ef663e428636d3ff634d1db72ad9318894e68cbf`.

Final verdict remains `C_TARGET_VALIDATION_FAILED`; evidence insufficiency includes no authorized
final-test metric, no accepted Final Run/portfolio, no accepted final Claims and no handoff. Strong
development metrics cannot compensate.

## Terminal freeze and formal state

- Freeze ID: `CUMCM-2017-C-VALIDATION-003F-TERMINAL-FREEZE-001`.
- Freeze file SHA-256:
  `984ccfe2616769020443c4f873303f9d5f584793f8b865e3c3b1e159d316559a`.
- Canonical payload SHA-256:
  `5f840eb821c8e58215f276baf0e2be86c122f13f55690800cf5ea7886437ccf1`.
- Freeze commit/remote SHA: `8bf82ebc56d00bbcfd756b9d3d2b77c7a35ffcd6`.
- Delivery receipt commit/remote SHA: `2f3b5b8a5668f37194bc180daeaaf4475b57034e`.
- Answer: `SEALED_AT_TERMINAL_FREEZE`; reference unlock remains locked.
- Frozen Skill unchanged; Run count remains nine; no post-freeze Run or same-case repair.
- Phase: `PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4`.
- Subphase: `C-TARGET-FRESH-VALIDATION-TERMINAL`.
- Active Skill: `0.2.0-competition-rc7`.
- Architecture: `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`.
- Current case: `CUMCM-2017-C-VALIDATION-003F`.
- Blockers: finalization interface failure, missing accepted Final Run, handoff not reached, and
  HF22 false semantic support declaration.
- Next phase: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`.

## 2025 reservation

`CUMCM-2025-C-HELDOUT-RESERVED` is `SEALED_NOT_ACCESSED`:

- `archive_accessed=false`
- `title_accessed=false`
- `problem_accessed=false`
- `attachments_accessed=false`
- `references_accessed=false`
- `answer_accessed=false`

## Final acceptance verification

Final local verification is PASS. The machine record is
`evals/results/phase-004c4/verification/final_acceptance.json`.

| Scope | Command/result | Duration | Evidence |
|---|---|---:|---|
| RC6 neutral | pytest: 57/57 | 0.24 s | known matrix `d28276...40eb2` |
| known controller | pytest: 14/14 | 2.02 s | known matrix `d28276...40eb2` |
| adversarial controller | pytest: 6/6 | 3.81 s | adversarial matrix `bb358a...73736` |
| neutral controller E2E | pytest: 17/17 | 6.45 s | test hash `1d92ea...8969d` |
| output/Claim/aggregate | pytest: 63/63 | 0.85 s | result binding `7fd780...a1b8` |
| live RC7 | checker PASS | 0.04 s | release `747d6c...8434` |
| regressions | checker PASS | 0.03 s | regression `f15a7d...33cc` |
| 2019/2024 diagnostic | read-only PASS/no credit | 0.04 s | `1276d8...6365` |
| fresh terminal/audit | workspace+delivery PASS | 0.08 s | audit `57f682...3d3` |
| discovery/leakage/secrets | 1 Skill / 0 / 0 | 3.07 s | `f79f9e...0f49` |
| full pytest | 2068 passed / 1 skipped | 310.20 s | `3527a4...da8b` |
| strict | 0 errors / 0 warnings | 6.35 s | `00f73d...89e` |
| local CI | 2068 passed / 1 skipped; strict 0/0 | 373.78 s | `28c13a...5320` |

The first final full pytest attempt ended `2066 passed / 2 failed / 1 skipped`: two old tests had
not enumerated the terminal 004C4 route or eighth registry case. Repair 1/3 added exact assertions;
the final full run passed. One earlier focused command named a nonexistent test file and ran zero
tests before the corrected 63-test command. The post-live candidate-stage checker also returned its
designed nonzero guard because candidate mode requires pre-release RC6 surfaces; the frozen
pre-release candidate PASS remains bound by candidate snapshot SHA-256
`a535b04635b91144918e5e179eba3b4dbf51f8d61d950f6e88086ecb2f2f5c25`. No failed harness
attempt changed Skill/case code, ran a model, accessed an answer, or touched 2025.

Remote CI PASS is bound to acceptance subject/remote SHA
`64a7647d8c196e52e6c43f73095a56f232e1a23f`: GitHub Actions run `33975187408`, job
`101330529964`, completed in 8m45s. Its sole CI command passed 825-file formatting, pytest
`2068 passed / 1 skipped` in 509.30 seconds, all historical checkers, and strict 0 errors / 0
warnings. The sole annotation is the GitHub-hosted Actions Node.js 20 deprecation/forced Node.js 24
notice; it did not fail the job. The workflow remained offline and did not read ignored inputs,
answers, historical workspaces or 2025.

## Delivery and PR

Starting HEAD is `7060ab136b88a158be6dfe3b46801e6cc2c65c64`. The probe freeze, three
implementation milestones, adversarial freeze/repair, regressions, RC7 candidate/release,
post-release CI receipt, 2018 fallback, 2017 registration/pre-run freeze, terminal freeze and
terminal delivery are separate commits on the required task branch. Acceptance content commit and
remote SHA are `64a7647d8c196e52e6c43f73095a56f232e1a23f`; remote CI run `33975187408` passed.
The non-self-referential successor receipt carrying this remote result is delivered separately and
its final SHA is reported in the handoff response. PR #10 remains OPEN/DRAFT/MERGEABLE and
unmerged.

## Unknowns and limitations

- RC7 passes the frozen release evidence but the single fresh C outcome is negative; broad C
  generalization and Held-out readiness are not established.
- The finalization interface is operationally unsatisfiable for the frozen honest output, and its
  top-level reason code is coarser than the underlying defect.
- Semantic Gate PASS in this episode is not trustworthy final-test support because HF22 proves a
  false, non-cross-bound predicate; the aggregate pre-final PASS inherits that limitation.
- The 2017 selection metrics are development-only. There is no authorized final-test score.
- Exact foundation-model prior exposure and reasoning-effort identifier are unverifiable.
- Answer isolation is policy/workspace based, not cryptographic or OS-enforced.
- Project license remains undecided. The official 2018 attachments were unavailable from the
  retrieved official package/channel; this does not prove they cannot exist elsewhere.
- Three attempted LibreOffice conversions failed because the executable was absent; no system
  install was made because privileged installation was unavailable. `xlrd==2.0.2` was installed in
  the project `.venv`; no apt/npm/cargo package, toolchain or shell/environment configuration was
  changed. Retention or cleanup of this one Python dependency remains a user choice.

## Exact next step

`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`.

004C5 must freeze a new repair design, add an explicit final-phase/test-authorization and payload
contract, cross-bind all semantic support predicates to authoritative selected Run/output,
evaluation-boundary and test-access facts, and validate the repair on a different future case. It
must not reopen or rerun this frozen Validation.
