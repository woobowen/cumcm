# Phase 004C C-Target Batch Generalization Acceptance

Status: `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`  
Phase: `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`  
Controlling blocker: `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`  
Next phase: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`

## Acceptance conclusion

The requested C-target migration, three-case RC3 Development batch, batch-wide postmortem, one
evidence-admitted RC4 revision, unified regression, and fresh 2024 C one-shot execution were
performed and preserved. The 2024 C numeric/modeling layer completed successfully: 4/4 frozen Runs
succeeded, all six requirements had outputs, four independent feasibility records found zero
violations, three official workbook templates retained their structure, and three quantitative
perturbations were recorded. This is not an accepted Validation. The frozen RC4 Claim Gate requires
one top-level claim string to equal two unequal frozen scopes, so both independent Claim checks
failed, formal state became `REJECTED`, and no canonical paper handoff was accepted. Under the
predeclared fail-closed rule, the terminal decision is therefore
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`.

The evidence-insufficient outcome is the accepted truthful terminal result of this phase; it is not
a technical PASS, broad-generalization claim, or permission to enter Held-out.

## Strategy and repository

- Decision `DECISION-C-TARGET-TRAINING-POLICY-004C` cancelled the proposed 2024 A route before
  registration or execution and made C the primary target. A remains auxiliary transfer evidence;
  B remains excluded by default.
- The new method freezes one Skill across a multi-case batch, delays references and Skill mutation
  until every first run is independently frozen and remotely delivered, and admits only repeated
  cross-case defects or universal hard failures.
- Work began from `a56450f7ffb78e181c5aa4d660e763ed4c59c83a` on preserved branch
  `feat/phase004c-validation-eval-2024a`. Work is delivered on
  `feat/phase004c-c-target-batch-generalization`; Draft PR 9 remains open and Draft.
- The preflight baseline passed with 1,816 tests and one skip. The starting Skill was the only
  discoverable formal Skill and was `0.2.0-competition-rc3` at release commit
  `8a2a813ff34d8c2701c64ff9d959848e7b88c27c`, tree
  `a4551c8aa0b6b119823f6ce9df3f0f948339bb33`.

## Batch registration and freeze

| Case | Official title | Archive SHA-256 | Problem SHA-256 | Data SHA-256 | Pre-run status |
| --- | --- | --- | --- | --- | --- |
| 2022 C | 古代玻璃制品的成分分析与鉴别 | `c27eb1b665f070341e134f5dc13bb2af469230424ff2eedabf594eee708bfee4` | `573ee0f2865af13f8b2fbd12dab7f8efa68cf61ec6b8edf132a2120424480dbd` | `ffb82a8e209a005f26883e115de3ddea42ab6e0a34986d312a52a3cea6b1063c` | `SEALED`; eligible, model prior unverifiable |
| 2021 C | 生产企业原材料的订购与运输 | `3391573f546fce4511e9a99c24c386e28203d8fee3d29bb2dccada5921cefe7b` | `4a592c20adad12d4f0678a783bfb47995bda03b1c7484adf254d96327f534056` | `1b93a759…`, `29e1499b…`, `3119bcd2…`, `807187bf…` | `SEALED`; eligible, model prior unverifiable |
| 2020 C | 中小微企业的信贷决策 | `04ea454f8a1559dac2dc5b7cf599bceb10cd6a0b6f2df55a35ca4450814239dd` | `d16b3e230eb616ac88ae5d5c172a4434d1814322d158e975c0959c95d49bb67d` | `450df5f7…`, `1399075d…`, `abdbdf68…` | `SEALED`; eligible with colocated-archive limitation |

Raw official inputs remained ignored and immutable. No solution material was accessed before the
freeze. The 2020 archive matched the earlier official cache, but only prior `A/` extraction was
found; no prior C artifact was found, so the preregistered 2019 fallback was not activated. This
does not establish absence of model-prior exposure.

Freeze `C-TARGET-BATCH-001-PRE-RUN-FREEZE-001` binds RC3, three cases, exact input hashes, Python
3.11.14 and 35 distributions, runner, 25 metrics, 11 hard failures, roles, answer/search controls,
two-worker maximum, and the 10,800-second per-case timebox. Its payload SHA-256 is
`1c075ede5dfe636e6f6ca946bc19b2dc71b8f36e1601653f58de7a8df7fb8a09`; commit
`af1e0c158cbce131cab8c6f193167b79fe021a7e` is remotely delivered.

## Independent first runs

| Case | Actual models/Runs | Fourteen-stage result | Robustness and handoff | Current freeze |
| --- | --- | --- | --- | --- |
| 2022 C | raw-centroid baseline, transformed linear/hierarchical and composition-distance candidates; 9/9 successful Runs | Stages 1–10 PASS; Stage 11 BLOCK; Stages 12–14 not reached; terminal `REJECTED` | Nested perturbations existed, but mandatory generic top-level output fields were absent; no accepted handoff | v2 SHA `5de34dec79b8b8aa0273b16d6ce0f1d4115178cd9e8410cc241adcaa79c61a87`; commit `7688b6a3f55052a5ba55396783c48eb5dc12d409` |
| 2021 C | three candidates × two seeds; 4 successes and 2 retained baseline infeasibility failures | Stages 1–9 PASS; Stage 10 BLOCK; Stages 11–14 not reached; terminal `RUN_VALIDATED` | 12/12 feasibility checks passed for successful outputs; no successful baseline and no authorized test access, so no comparison/robustness/handoff | v2 SHA `a747da766bb319c989c273afad476de6a8518df5bde2e1abc564d7b7b5d3ac9d`; commit `7688b6a3f55052a5ba55396783c48eb5dc12d409` |
| 2020 C | baseline, linear and nonlinear candidates × two seeds; 6/6 successful Runs | Stages 1–14 PASS; `READY_FOR_PAPER_HANDOFF` | Three perturbations, six requirement Claims and canonical handoff passed; one post-selection test access was unused for selection | v2 SHA `a5016b6336001bf840247aa6135b4beba15d3a695da498ac1e9149afe332ccfb`; commit `29ad3c3f3971e23a36dc7094abdfe86dc5fc6505` |

Batch first-pass handoff completion was 1/3 (33.33%). Valid Runs were 19/21 (90.48%); design/run-
output requirement coverage was 100%, but accepted Claim/handoff coverage was 1/3. There was one
batch hard failure and zero manual interventions during Run phases. Registration-to-terminal
windows were 56, 73 and 109 minutes. Median time to first baseline was 1,968.305244 seconds; median
time to first valid result was 2,441 seconds. Only 2020 C reached handoff, after 2,210.663201
seconds, so no all-case handoff median exists.

## Unlock, bounded references, and failure adjudication

All original and corrected first-run freezes were separately committed, pushed and verified before
one atomic unlock at `2026-09-05T00:59:00+08:00`. Unlock receipt SHA-256 is
`d6a9aa50ce294fc82f2c195d76fa0a5aa745b681544f3455f2991821d100d69a`.
Only one official page and one DOI-published follow-up analysis per case were then accessed. Bodies
remain ignored; metadata/body hashes, use limits and no-copy declarations are tracked. No code,
parameters, formulas, prose or results were copied into the Skill.

The six adjudicated findings were:

1. `C004C-CROSS-OUTPUT-CONTRACT-PREFLIGHT-001`: all three cases, repeat count 3, hard and
   noncompensable after sealing; generalizable and accepted.
2. 2021 infeasible baseline: one case, case-specific modeling failure; rejected because the
   existing successful-baseline Gate behaved correctly.
3. 2021 missing authorized test access: one case, leakage-control block; rejected because the
   fail-closed Gate behaved correctly.
4. 2022 sparse inverse identifiability: one case, bounded modeling limitation; rejected as
   problem-specific and not a neutral hard threshold.
5. 2022 perfect small-split score: one case, cautionary evidence; rejected as non-generalizable and
   non-testable as a Skill rule.
6. Published-method disagreement: all three cases, repeat count 3 but not a failure; rejected under
   the anti-oracle/anti-hardcoding rule.

## RC4 and unified regression

Exactly one generic change set produced `0.2.0-competition-rc4`: shared function
`validate_selected_output_contract`, a non-result/non-ranking placeholder `preflight-output` route,
the same validation on every successful `execute` output, and retention of invalid outputs as
failed evidence. Formal Skill files changed only for this contract, workflows, fixture and version;
neutral prediction/optimization tests cover missing/nonfinite metrics, Claims, robustness, figures,
uncertainty, limitations, read-only behavior and failed-output retention. No year, title, attachment,
entity, source field, model family, parameter, answer or optimum was added.

RC4 implementation commit is `297cad0a29c659b18484d4f3b67d69a942ad415c`; its Skill tree is
`d041ca38de030ae04813ef02dbe12f7f2b7a1c22`. Maintenance cost is one validator, one CLI route, two
workflow additions, fixtures and tests. The release gate then passed:

- three C batch regressions: 9/9 Runs, all three 14-stage chains PASS;
- preserved 2023 C: three Runs, handoff and STALE propagation PASS;
- 2020 A auxiliary: two successes plus one retained exit-23 failure; success-only selection PASS,
  with zero C-target credit;
- two synthetic E2E chains PASS;
- original negative matrix: 30/30 correctly rejected;
- one formal Skill, no answer leakage, secrets or third-party execution;
- full release CI: 1,865 passed and one skipped.

Release commit `46e13d31a3d22fe12a2cffe65a52558da3ecfa82` froze RC4 before Validation.

## 2024 C one-shot Validation

The official case “农作物的种植策略”, problem, two data workbooks and three official output
templates were hash-bound while answer/reference material remained `SEALED`. Pre-run freeze bound
RC4, release commit/tree, Python 3.11.14 and 35 distributions, 25 metrics, 12 hard failures, 14
stages, fresh-worker isolation and a 14,400-second limit. Its canonical payload SHA-256 is
`d1b5456f…`; pre-result code SHA-256 is
`4602b194d44a9888e0ddef031bb29066c1fec35ce14678ca03a0a9aac59f9b6b`, bound at commit
`f12aa707cdf756c657dde0d69556b9f575b748ed`.

The frozen grid executed baseline and risk-aware greedy candidates at seeds 104729 and 130363 once
each. All four Runs succeeded with no retry, recovery, result-driven code edit or run-phase manual
intervention. The primary aggregate score `169264118.00319` exceeded baseline
`110079957.9191615`; `PRIMARY_RISK_GREEDY`/seed 104729 was selected. Exactly one test access occurred
after selection and was not used for selection.

Six of six main requirements had outputs. Four selected-plan feasibility records had zero
violations; three workbooks preserved official sheet structure. Three quantitative perturbations
were bound to the selected Run. Reported model outputs include Q1 waste profit 37,599,028.25 yuan,
Q1 discount profit 54,436,325.625 yuan, Q2 risk-adjusted profit 38,654,170.051186 yuan, and Q3
profit 38,549,231.473884 yuan, 80,154.715582 yuan below the Q2 plan under the registered dependent
scenarios. These are assumption-bound heuristic outputs, not realized profit or global optima.

Final reached `FINAL_CANDIDATE`, but the frozen validator requires top-level Claim text/scope to
equal both the global Final scope and the first Q1-specific requirement Claim. Those immutable
strings differ. Independent `claim-check` and `validate --check` calls each exited 3 with only
`RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`. Formal case state is `REJECTED`; no accepted Claim
or canonical handoff exists.

Terminal freeze `CUMCM-2024-C-VALIDATION-001-TERMINAL-FREEZE-001` has payload SHA-256
`d53c4280f09b369c4ab09a66c6bbba454c8b739e710f21f7481a375454523033` and file SHA-256
`6e78a9c047b0c2673c17c1e9b055dfa342f681ca5aa86c7b789929aadd138373`. Commit
`197f62bc75ebe832e9dd3ced0306740f336b80d6` is remotely delivered. Terminal freeze occurred after
3,219 seconds, within the four-hour limit. No Run occurred after terminal freeze; RC4 and the sealed
answer were unchanged. The case cannot be reused as Validation.

## Scorecard and professional boundary

- Five independent C problems have execution evidence: 2023 C, the three batch cases, and 2024 C.
  Phase 004C contains four process-strict answer/reference-sealed first runs; model-prior exposure
  remains unverifiable.
- Phase end-to-end handoff rate is 1/4 (25%). Batch first-pass completion is 1/3. Across batch and
  Validation, valid Runs are 23/25 (92%). Design/run-output main-question coverage is 100%; it does
  not substitute for Claim/handoff acceptance.
- Engineering generalization passes for capture, failure retention, preflight, hashing, STALE and
  regression, but fails for the newly exposed multi-requirement Claim-scope contract.
- Modeling generalization is partial. Evidence spans composition classification, supplier/transport
  optimization, credit risk/decision and crop planning, but only one RC3 batch case reached handoff
  and Validation did not pass.
- 2024 data quality and deterministic feasibility recomputation pass within registered semantics.
  Model and statistical appropriateness are partial: whole-plot greedy allocation narrows the
  feasible set, has no MIP/global-optimality bound, and Q3 dependence parameters are simulation
  assumptions rather than causally estimated quantities.
- Robustness passes the frozen quantitative contract, but only for the registered perturbations.
  Handoff quality fails because the Claim prerequisite is unsatisfied.

## Formal boundaries, held-out, and state

The repository still contains exactly one formal Skill with architecture
`ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`; no third-party candidate Skill/code was
integrated or executed. RC3 stayed byte-stable throughout all three first runs, and RC4 stayed
unchanged throughout Validation. Anti-hardcoding, answer-leakage, secret and single-Skill checks
pass.

`CUMCM-2025-C-HELDOUT-RESERVED` remains `SEALED_NOT_ACCESSED`. Only its official annual-page URL
SHA-256, `83e2b2a88e81213252c4aa8212558a738a95f44d2d03de80e849b154d31a468f`, is recorded. Archive,
title, problem, attachments, references and answer access flags are all false. Held-out execution is
not authorized.

Formal state is phase `PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`, subphase
`C-TARGET-2024C-VALIDATION-TERMINAL-EVIDENCE-INSUFFICIENT`, status `IN_PROGRESS` under the state
schema, technical status `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`, active Skill RC4, primary
target C, batch `C-TARGET-BATCH-001`, one blocker, and next phase
`PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`.

## Verification and delivery

- Local final content CI: `bash scripts/ci.sh` PASS; 1,868 passed, zero failed, one skipped; strict
  repository validation 0 errors and 0 warnings; generated status current; `git diff --check` PASS.
- Remote CI for content commit `b71d762e9031b9d18656f43904cb7fc5145ba2ef`: PASS, GitHub Actions
  run `33914904042`.
- Final acceptance/state receipt commit and its remote CI are recorded by the final delivery response
  after this report is committed, avoiding a self-referential file hash/commit claim.
- No system, Python, npm, cargo, TeX, font, database or other dependency was installed. No shell or
  global Codex configuration was changed.
- API key used: no. API billing: none. Foundation-model training: no. Fine-tuning: no. Execution used
  native worker sessions plus local deterministic code. The optimized objects were case-level
  models, parameters, schedules/allocations and evidence workflow contracts—not model weights.
  Unaudited third-party code execution: none.

## Unknowns and limitations

Model-prior exposure to historical problems cannot be verified. Reference bodies are ignored local
evidence rather than remotely reconstructible tracked content. No official 2024 solution was
accessed, so substantive accuracy against an official answer is unknown. Validation output access
is controlled by provenance records, not OS-level suppression. Early-stage operator time, exact
token consumption and monetary/operator cost are not fully instrumented. The 2024 method is a
contest-time deterministic heuristic, not a proof of optimality or external validity. The terminal
Claim defect cannot be repaired and rerun on the same case without destroying Validation status.

## Exact next step

Start only `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2`: before any new result, freeze a case-neutral
Claim-scope repair and neutral multi-requirement tests; then evaluate it on a different answer-sealed
C case. Do not rerun 2024 C as Validation and do not access reserved 2025 C in this phase.
