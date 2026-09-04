# Phase 004A Acceptance Report

## 1. Final Status

`DEVELOPMENT_EVAL_RC2_READY`. RC1 的答案封存首跑被原样冻结；RC2 只修复真实暴露的通用执行证据缺陷；同题 Development regression 与 Stress A/B/C 均完成。该状态不构成 Validation、Held-out 或单题泛化证明。

## 2. Starting RC1

- Branch：`feat/phase004-development-eval-2023c`；base/start commit：`a93a96d79890f6774552dc5ff333f833099edf83`。
- Skill：`0.2.0-competition-rc1`；tree：`49d499ab0e063a2cf72a780c89ee969a696fb02e`。
- Architecture：`ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`；capability：`COMPETITION_RC`。
- Baseline：`1804 passed, 1 skipped` in 363.70 s；strict 0 errors/0 warnings；discovery count 1；two E2E READY；30/30 negative PASS。

## 3. Development Case Registration

- Case：`CUMCM-2023-C-DEVELOPMENT-001`，2023 年全国大学生数学建模竞赛 C 题《蔬菜类商品的自动定价与补货决策》，set type `DEVELOPMENT`。
- Official source domain：`mcm.edu.cn`；problem SHA `f94818a4…d89e5`。
- Data SHA：附件 1 `311bcf78…3bd7`；附件 2 `d10ad412…d5b`；附件 3 `3a383a51…05e9`；附件 4 `d91923cc…18c`。
- Raw storage：ignored private `.cache/official_inputs/CUMCM-2023-C/`；题面、附件、参考正文未进入 Git。
- 初始 answer state `SEALED`；model prior `MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`。

## 4. Pre-Freeze Search Audit

- Query/access 仅导航 `mcm.edu.cn` 官方历年题目与原始文件；pre-freeze search log SHA `fe39e187…12e71`。
- 允许：官方题面 PDF、官方附件；主动阻止：讲评、论文、答案、题解、代码、博客、视频和培训站点。
- Accidental exposure：none；结果：`PASS_NO_SOLUTION_EXPOSURE`。未读取 `benchmark-vault`。

## 5. First-Run Freeze

- Freeze ID：`CUMCM-2023-C-DEVELOPMENT-001-FIRST-RUN-FREEZE-001`。
- Artifact SHA：`9f27706b099b187c5c6c82984fcf3e760d7cbcc6640525bbf7841014929a2fb3`。
- Subject commit：`1cd1402521d2c4cf487c01e045a6ab1b20b6e130`；freeze commit/verified remote SHA：`8e7b7ced55789232bb5d6f8ec64e1ac4926778f8`。
- Freeze time `2026-09-04T06:16:39Z`；answer state `SEALED`；Skill `0.2.0-competition-rc1`。
- Case state `MODELS_PROPOSED`；zero Run/result/handoff manifests 是真实阻塞结果。Freeze check `PASS`，首跑文件解封后未改。

## 6. RC1 First Run

| Stage | Status | Artifact / Gate | Time | Failure |
|---|---|---|---:|---|
| PROBLEM_INTAKE | PASS | problem requirements / intake | UNKNOWN | — |
| REQUIREMENT_DECOMPOSITION | PASS | six IDs / coverage | UNKNOWN | — |
| RESEARCH_AND_SOURCE_PLANNING | PASS | plan+ledger / source | UNKNOWN | — |
| ASSUMPTION_AND_SYMBOL_DEFINITION | PASS | assumptions / data gate | UNKNOWN | — |
| DATA_AUDIT | PASS | data audit / data gate | UNKNOWN | — |
| MODEL_PORTFOLIO_GENERATION | PASS | candidates / portfolio | UNKNOWN | — |
| BASELINE_DEFINITION | PASS | exactly one baseline | UNKNOWN | — |
| EXPERIMENT_DESIGN | BLOCKED | preregistered but execution not prepared | UNKNOWN | `RC_CUSTOM_EXECUTOR_UNAVAILABLE` |
| IMPLEMENTATION_AND_EXECUTION | NOT_STARTED | no manifest | 0 s | blocked upstream |
| MODEL_COMPARISON | NOT_STARTED | — | UNKNOWN | blocked upstream |
| ROBUSTNESS_AND_SENSITIVITY | NOT_STARTED | — | UNKNOWN | blocked upstream |
| FINAL_RUN | NOT_STARTED | — | UNKNOWN | blocked upstream |
| CLAIM_EVIDENCE_VALIDATION | NOT_STARTED | — | UNKNOWN | blocked upstream |
| MODELING_TO_PAPER_HANDOFF | NOT_STARTED | — | UNKNOWN | blocked upstream |

首跑总时长 1,387 s；formal Gate exit 3：`RC_EXPERIMENT_PLAN_NOT_PREREGISTERED`。没有声称未运行代码、没有伪造 Run/Claim/handoff。

## 7. Data Audit

- 4 workbooks；item master 251，sales 878,503（正销量 878,042、returns 461），wholesale 55,982；6 categories，246 个有正销量 item。
- Item/category 与 wholesale mapping 100%；exact sales duplicates 0；timestamp-item collision 1；missing cells 0；10 个销售缺日不按零填。
- 异常保留并标记：12,651 条正销量低于同日成本、35 条销量大于 10、成本范围 0.01–141、损耗率 0–29.25%。
- 单位：题面声明 kg/yuan-per-kg；82 个包装名称 item 存在业务单位歧义；损耗百分数只在派生计算转 fraction。
- Leakage：随机切分禁止；损耗快照可能对历史 fold 含未来信息；观测价格内生，不能声称 causal elasticity；未来目标未提供。
- Raw immutable；首跑 audit SHA `7247b953…c8ed`。Returns 与整店缺日排除于需求拟合，但不从 raw 删除。

## 8. Model Portfolio

| Subproblem | Baseline | Candidate/control | Assumptions | Metric/validation | Failure conditions |
|---|---|---|---|---|---|
| Q1 distributions/dependence | weekday descriptive/ECDF | hierarchical seasonal; nonparametric robust | observed sales proxy | support-aware summaries/correlation | sparse support, nonstationarity |
| Q2 price/replenishment | weekday demand + median markup | trend/weekly/annual seasonal regression; recent median robust | price association non-causal, cost recent | time-ordered WAPE + feasibility | regime change, endogenous price |
| Q3 item decision | category-covered greedy, min display repair | same two structural controls | recent items available | count/category/minimum checks | missing capacity/stockout data |
| Q4 data priority | impact-availability matrix | uncertainty/value-of-information framing | no unavailable field invented | maps each field to bias/constraint | acquisition cost/privacy unknown |

三条 pipeline 都覆盖所有 requirements；模型数量不作为成果，选择服从 preregistered baseline-normalized loss、hard constraints、解释性和证据完整性。

## 9. Actual Experiments

所有 Run 使用 case-owned `development_model.py`、code commit `21bcf1bf…1642`、seed `20260904`，input set 逐 variant 冻结；12/12 exit 0 且 included。

| Variant | Model | Validation metric | Manifest SHA prefix | Result |
|---|---|---:|---|---|
| Development | seasonal baseline | 1.00000000 | `c5f695f3` | SUCCESS |
| Development | hierarchical seasonal | 0.95115654 | `e8cb7d69` | SELECTED |
| Development | nonparametric robust | 1.13927070 | `52d88687` | SUCCESS |
| Stress A | seasonal baseline | 1.00000000 | `6c12a641` | SUCCESS |
| Stress A | hierarchical seasonal | 0.95115654 | `122b64f1` | SELECTED |
| Stress A | nonparametric robust | 1.13927070 | `f87ff367` | SUCCESS |
| Stress B | seasonal baseline | 1.00000000 | `fc45b60e` | SUCCESS |
| Stress B | hierarchical seasonal | 0.95115654 | `5ce58af7` | SELECTED |
| Stress B | nonparametric robust | 1.13927070 | `78de8c8b` | SUCCESS |
| Stress C | seasonal baseline | 1.00000000 | `27af221d` | SUCCESS |
| Stress C | hierarchical seasonal | 0.95101686 | `ff5e936a` | SELECTED |
| Stress C | nonparametric robust | 1.13911312 | `cd34081d` | SUCCESS |

Run ID 形式为 `RUN-<MODEL>-20260904`，在各隔离 case root 内唯一。Capture/manifest/output 的完整 hashes 在 tracked evidence JSON 中。

## 10. Robustness and Sensitivity

Development selected model 的真实重算 perturbations：shorter training window `0.88074853`，validation demand ×1.05 `0.98239919`，remove validation tail `0.94844323`。未使用固定比例伪造结果。

不稳定/不确定：Stress C 改变 decision hash、WAPE 和 profit proxy；缺损耗源时所有 877,160 正销量行的 loss 不确定。Stockout censoring、内生价格、缺 shelf/inventory/lead-time 与未来 outcomes 仍限制结论。

## 11. RC1 Handoff

RC1 final state `MODELS_PROPOSED`，没有 selected model、Run result、formula-bound result table、figure-ready data、Claim 或 handoff。Requirements/assumptions/data audit/model portfolio 可用；Execution 以后字段缺失。不得称为 `READY_FOR_PAPER_HANDOFF`。

## 12. Answer Unlock

- Unlock `2026-09-04T06:18:44Z`；先决条件：freeze 存在/通过、独立 commit pushed、local=remote `8e7b7ce`、无 solution exposure、problem/data hashes 不变。
- 访问 3 个 official classes：award display、annual report、commentary meeting page。SHA 分别 `633145b5…abb3`、`29f4b96c…13e4`、`e54808b8…7920`。
- No-copy：`PASS_NO_CODE_PARAMETER_FORMULA_OR_LONG_PASSAGE_COPIED`。

## 13. Gap Analysis

| ID | Classification | First-run/reference evidence | Generalizable | Action |
|---|---|---|---|---|
| 001 | GENERALIZABLE_SKILL_FAILURE | zero Run；reference only confirms real execution need | yes | ACCEPT executor |
| 002 | EVIDENCE_FAILURE | no process/log/output relation | yes | ACCEPT capture+seal |
| 003 | PROBLEM_SPECIFIC_INSIGHT | official display names methods | no | REJECT from Skill |
| 004 | REFERENCE_DISAGREEMENT | method difference is not incorrectness | no | REJECT as failure |
| 005 | MODEL_KNOWLEDGE_GAP | data cannot identify stockout/causality | no | retain limitation |

## 14. RC2 Skill Changes

- Version `0.2.0-competition-rc2`；changed formal files：Skill docs/version, `cumcm_case.py`, execution workflow/template documentation。
- `execute`：only RUNNING + preregistered candidate/seed + CASE_ROOT Git blob + bounded timeout；自动 capture。
- `seal-run`：在 decision hash 后重验 capture；log/output mutation fail closed；custom code 无 capture 不准 manifest。
- 解封回归边界：only explicit `DEVELOPMENT_REGRESSION` + first-run freeze SHA；默认仍为 `NOT_ACCESSED`。
- Originating failure：GAP-001/002；anti-hardcoding scan PASS；generic executor mutation test、two E2E、30 negative、full suite PASS。

## 15. Development Regression

- RC1→RC2：requirements/data/model portfolio 保持；valid Runs 0→3；final state MODELS_PROPOSED→READY_FOR_PAPER_HANDOFF。
- Selected：hierarchical seasonal；WAPE 0.31407446；27-item feasible plan；six requirement Claims and full handoff。
- Captured runtime 99.347647 s；first baseline 33.692685 s；manual result edits 0；failed Runs 0；token visibility UNKNOWN。
- Resolved：trusted custom execution/capture。Remaining：causal identification、stockout、capacity、future outcome、global optimality。
- Overfit：未复制 reference 方法/参数且 Skill 无题目 token；但同题已解封，仍不能排除 `REFERENCE_OVERFIT` 风险或作为泛化证据。

## 16. Stress Results

- A：workbook/file/row/column order 改变并加入 irrelevant field；new hashes；scores/decision/final metrics 精确一致；READY。
- B：quantity in grams + 0.001 conversion，dates +365；kg outputs 一致；old binding probe `STALE`；READY。
- C：删除约 0.1% 非关键记录、注入缺失、loss source unavailable；不崩溃，uncertainty 增加，metrics/decision 改变；old binding probe `STALE`；READY。
- Failures：none in model Runs；结论只属于同一 Development 题的变换检查。

## 17. Generalization Boundary

本题是 Development，不是 Validation，不是 Held-out；模型先验暴露不可验证；单题和其 Stress 变体不能证明泛化。下一步必须换结构不同且答案仍封存的历史题，先冻结 Skill commit 和答案状态再运行。

## 18. Tests and CI

- Starting baseline：1804 passed, 1 skipped；final focused：152 passed；final full：1808 passed, 1 skipped。
- Two synthetic E2E PASS；30/30 negative PASS；Development/Stress machine consistency PASS；Skill discovery 1。
- Ruff 683 files PASS；contracts 78 valid/68 invalid rejected；leakage/secrets/private paths 0；strict 0 errors/0 warnings。
- `bash scripts/ci.sh` exit 0；pytest 311.00 s，CI wall 336.75 s。Remote CI：`UNKNOWN_UNTIL_FINAL_PUSH_VERIFICATION`。

## 19. Documentation Consistency

Plan、registry、protocol、Skill、VERSION、CHANGELOG、README、state、generated current_state 和九份 Phase004A reports 已同步。`check_competition_rc_consistency.py --check` 37/37；`check_skill_training_consistency.py --check` PASS；Draft PR #7 保持 OPEN/DRAFT。

## 20. Formal State

- Phase `PHASE-SKILL-DEVELOPMENT-EVAL-004`；subphase `CUMCM-2023-C-DEVELOPMENT-RC2`。
- Technical `DEVELOPMENT_EVAL_RC2_READY`；active Skill `0.2.0-competition-rc2`；capability `COMPETITION_RC`；K1。
- Case `CUMCM-2023-C-DEVELOPMENT-001`；answer `UNLOCKED_AFTER_FIRST_RUN`；Stress A/B/C PASS；third-party false；blockers empty。
- Next `PHASE-SKILL-DEVELOPMENT-EVAL-004-B`。

## 21. Git Delivery

- Branch `feat/phase004-development-eval-2023c`；starting HEAD `a93a96d`。
- Freeze commit `8e7b7ce`；RC2 candidate commits `e0e82b3`, `21bcf1b`；evidence commit `0d55475`，均已推送并在阶段内远端核验。
- Final documentation commit/remote HEAD：在本报告写入后的 delivery receipt 中核验。
- Draft PR #7：`OPEN`, `DRAFT`, not merged/not ready。Raw inputs/reference bodies/caches 未 tracked。

## 22. Unknown and Limitations

RC1 每 Gate 精确时间、reasoning effort、token/cached token、queue/operator time、monetary/API cost 和 remote CI outcome 在最终 push 前为 UNKNOWN。No future realized sales/profit, stockout labels, inventory, shelf capacity, promotion, weather or lead-time data；profit 是 proxy；item plan 是 feasible heuristic，非全局最优证明。许可仅确认官方公开下载，重新分发权未建立，因此原文件不提交。

## 23. Exact Next Step

`PHASE-SKILL-DEVELOPMENT-EVAL-004-B`：选择结构不同、答案仍封存的历史题；在任何参考访问前冻结题面/数据/RC2 Skill commit/搜索策略，再执行完整首次运行。

## 24. Acceptance Report

Automated evidence adjudication：PASS。Hard gates：first-run freeze/remote-before-unlock PASS；generic failure evidence PASS；RC2 regression PASS；Stress A/B/C PASS；two E2E/30 negative/full CI PASS；one formal Skill；no hardcoded answer；no blocker。正式接受状态为 `DEVELOPMENT_EVAL_RC2_READY`，但接受范围严格限于 Development evidence 和 RC2 mechanism readiness。
