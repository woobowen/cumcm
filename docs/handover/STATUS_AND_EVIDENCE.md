# RC7 状态与证据

本文件是 2026-09-06 的说明性快照，不替代机器真源。正式状态以
[`state/project_state.json`](../../state/project_state.json) 为准，生命周期以
[`WORKFLOW.md`](../../WORKFLOW.md) 为准，RC7 release 以
[`rc7_release.json`](../../evals/results/phase-004c4/rc7_release.json) 为准。

## 四类能力矩阵

| 分类 | 能力/事实 | 证据 | 边界 |
|---|---|---|---|
| 已实现且有验证 | 单一 formal Skill、14-stage workflow、case state、Run capture/seal、comparison、Claim/handoff binding、STALE | [`SKILL.md`](../../.agents/skills/cumcm-modeling-evidence/SKILL.md)、[`phase004c4_acceptance.md`](../../reports/phase004c4_acceptance.md) | `COMPETITION_RC`，不是 production-ready |
| 已实现且有验证 | 实际 completion controller 调用 requirement/source/data/selection/Run/compatibility/semantic/aggregate/finalization/handoff 十个有序 Gate | [`finalize_fresh_c_validation.py`](../../scripts/finalize_fresh_c_validation.py)、004C4 acceptance 的 gate trace | neutral E2E 可完成；真实 2017 C 在第 9 Gate 阻断 |
| 已实现且有验证 | `GLOBAL_JOINT`、`PER_REQUIREMENT`、`JOINT_PORTFOLIO`，权威 manifest/output/metric/compatibility 绑定 | [`phase004c4_acceptance.md`](../../reports/phase004c4_acceptance.md) | 回归通过不等于陌生题通过 |
| 已实现且有验证 | RC7 candidate/live release、历史 read-only replay、synthetic E2E 和 fail-closed negatives | [`rc7_release.json`](../../evals/results/phase-004c4/rc7_release.json) | 本轮交接未重跑这些科研/历史场景 |
| 已实现但有已知缺陷 | Finalization 需要 selected output 中的 `sealed_test_metrics_b64`，而 released `execute` 没有合法 final/test 授权输入 | [`controller_outcome.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/controller_outcome.json)、[`phase004c4_validation_decision.md`](../../reports/phase004c4_validation_decision.md) | 阻止 accepted Final Run；不得靠改 frozen output 或加第十次 Run 绕过 |
| 已实现但有已知缺陷 | predictive semantic predicate 没有交叉绑定权威 Run/output/evaluation boundary/test access | [`HF22 challenge`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/challenges/HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json) | Gate 7/8 曾错误接受 REQ2 的 positive predicate |
| 已实现但有已知缺陷 | Python distribution metadata 与正式 competition Project 版本面不同 | [`pyproject.toml`](../../pyproject.toml)、根 [`VERSION`](../../VERSION) | 是否要求同步没有明确仓库说明；本轮不修改 |
| 已设计未实施 | 004C5/RC8 的最小 P0：先复现 Finalization 与 HF22 调用路径，再修接口与 cross-binding | [`NEXT_STEPS.md`](NEXT_STEPS.md) | 没有新代码、版本或实验结果 |
| 已设计未实施 | 让专业检索实际影响模型/实验；改进 data sufficiency、model fit、多问依赖、科学质量/效率 | [`NEXT_STEPS.md`](NEXT_STEPS.md) | 建议，不是当前能力声明 |
| 已设计未实施 | 新冻结版本的跨题 Validation、队员接手演练、条件满足后的 held-out | [`NEXT_STEPS.md`](NEXT_STEPS.md) | 2025 C 仍锁定 |
| 未知或未验证 | 陌生 C 题完成率、外部效度、2026 比赛表现、生产适用性、全局最优能力、未来维护/货币成本 | [`GOALS.md`](../../GOALS.md)、[`project_state.json`](../../state/project_state.json) risks | 不得由 CI、Run 成功数或 Development 回归推断 |
| 未知或未验证 | 新电脑从声明依赖完整重建数值运行环境 | [`ENVIRONMENT_AND_ASSETS.md`](ENVIRONMENT_AND_ASSETS.md) | 没有完整数值依赖声明/lockfile；`.venv` 不可移植承诺 |
| 未知或未验证 | 模型先验暴露、项目许可证 | [`project_state.json`](../../state/project_state.json) | `MODEL_PRIOR_EXPOSURE_UNVERIFIABLE` / `PROJECT_LICENSE_UNDECIDED` |

## 版本演进

| Project / Skill | 有证据的增量 | 保留限制 |
|---|---|---|
| RC1 / `0.2.0-competition-rc1` | K1 Competition RC、14 阶段、synthetic E2E；2023 C answer-sealed 首跑诚实阻断 | 没有 case-local executor |
| RC2 / `0.2.0-competition-rc2` | Git-blob-bound case-local executor、capture、seal；2023 C Development regression 完成 | 2020 A nonzero-exit/failure evidence 不完整 |
| RC3 / `0.2.0-competition-rc3` | 修复失败保留；2020 A regression 完成；冻结三道 C Development batch | 两道 C 首跑仍在下游 Gate 阻断 |
| RC4 / `0.2.0-competition-rc4` | selected-output contract preflight；三道 C regression 完成 | 2024 C Validation 被冻结 Claim scope 冲突阻断 |
| RC5（声明）/ `0.2.0-competition-rc5` | case-neutral Claim 修复；2019 C 运行/结构链 | frozen Skill `VERSION` 仍写 RC4，release acceptance 被阻断；2019 C 缺实证数据 |
| RC6 / `0.2.0-competition-rc6` | requirement evidence/data sufficiency/selection/semantic 设计与实现尝试 | 13 个实际 controller fail-open probe；未发布 |
| RC7 / `0.2.0-competition-rc7` | 实际 controller 十 Gate、selection modes、adversarial/neutral/replay release evidence | 2017 C Finalization 接口失败，HF22；Validation 未通过 |

正式当前版本只取根 `VERSION`、Skill `VERSION`、release manifest 与 state 的一致值；上表不把历史版本
成绩合并为当前版本成功率。

## 独立赛题记录

下表每行是一道独立题。Run 数是该次冻结 episode 内的尝试数，不是题目数；Stress、seed、同题修复和
read-only replay 不增加独立题分母。

| Case ID | 题型/用途 | 当时 Skill | answer-sealed 首跑/正式 episode | 后续回归 | 只读回放 | 证据路径 | 关键限制 |
|---|---|---|---|---|---|---|---|
| `CUMCM-2023-C-DEVELOPMENT-001` | C / Development | RC1 | 0 Run；8 阶段处因无 trusted executor 阻断，state `MODELS_PROPOSED` | RC2：3/3 Run，14 阶段到 handoff；RC3/RC4 compatibility 保留 | RC7 release 只读历史 replay，未在本轮重跑 | [`phase004a_first_run.md`](../../reports/phase004a_first_run.md)、[`phase004a_rc2_regression.md`](../../reports/phase004a_rc2_regression.md) | regression 已解封，不是 Validation |
| `CUMCM-2020-A-DEVELOPMENT-002` | A / auxiliary Development | RC2 | 6 次均无 eligible Final；stage 9 阻断，失败证据保留 | RC3 clean V2：6/6 Run，14 阶段到 handoff | RC4/RC7 compatibility scope；本轮未重跑 | [`phase004b_first_run.md`](../../reports/phase004b_first_run.md)、[`phase004b_development_regression.md`](../../reports/phase004b_development_regression.md) | A 题给予零 C-target generalization credit |
| `CUMCM-2022-C-DEVELOPMENT-BATCH-001` | C / Development batch | RC3 | 9/9 Run；10/14，robustness Gate `REJECTED` | RC4：3/3 Run、14 阶段 PASS | RC7 只读历史 replay；本轮未重跑 | [`c_target_batch_first_run.md`](../../reports/c_target_batch_first_run.md)、[`c_target_batch_regression.md`](../../reports/c_target_batch_regression.md) | 首跑数值好看但缺 top-level downstream contracts |
| `CUMCM-2021-C-DEVELOPMENT-BATCH-002` | C / Development batch | RC3 | 4/6 Run 成功；baseline 两次失败；9/14，`RUN_VALIDATED` | RC4：3/3 Run、feasible baseline、14 阶段 PASS | RC7 只读历史 replay；本轮未重跑 | 同上 | baseline success 缺失时不得比较/Final |
| `CUMCM-2020-C-DEVELOPMENT-BATCH-003` | C / Development batch | RC3 | 6/6 Run；14/14 到 `READY_FOR_PAPER_HANDOFF` | RC4：3/3 Run、14 阶段 PASS | RC7 只读历史 replay；本轮未重跑 | 同上 | 仍只是 Development，不能证明 Validation |
| `CUMCM-2024-C-VALIDATION-001` | C / Validation | RC4 | 4/4 Run，六项输出；Claim Gate 冲突后 `REJECTED`，无 accepted handoff | 禁止同题 Validation rerun；只有 diagnostic | RC5/RC6/RC7 只读诊断保留负向结论 | [`c_target_2024c_validation.md`](../../reports/c_target_2024c_validation.md)、[`c_target_validation_decision.md`](../../reports/c_target_validation_decision.md) | `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT` |
| `CUMCM-2019-C-VALIDATION-002` | C / Validation | RC5 声明，VERSION 实为 RC4 | 9/9 Run；native contracts/handoff 结构通过，但缺 Q2 实际机场/城市数据，rubric `REJECTED` | 禁止同题 Validation rerun | RC6/RC7 只读诊断；本轮未重跑 | [`phase004c2_2019c_validation.md`](../../reports/phase004c2_2019c_validation.md)、[`terminal freeze`](../../evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002/terminal_freeze/terminal_validation_freeze.json) | `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`；Q4 semantic support 不完整；release metadata blocked |
| `CUMCM-2017-C-VALIDATION-003F` | C / Validation fallback | RC7 | 9/9 Run；Gates 1–8 PASS，Gate 9 Finalization BLOCK，Gate 10 未到达 | 无；同题只能转 Development，禁止修 frozen episode | terminal integrity audit 为 read-only，返回 `CHALLENGE`/HF22 | [`phase004c4_fresh_validation.md`](../../reports/phase004c4_fresh_validation.md)、[`decision`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/DECISION-C-TARGET-VALIDATION-004C4.json)、[`terminal freeze`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/terminal_freeze/terminal_validation_freeze.json) | `C_TARGET_VALIDATION_FAILED`；0 test access；无 accepted Final/Claims/handoff |

另有 `CUMCM-2018-C-VALIDATION-003` 只完成 input suitability preflight：官方 archive 缺少题面命名的五个
附件，0 model Run；它不是一次题目结果。机器记录为
[`2018_input_preflight.json`](../../evals/results/phase-004c4/fresh_validation/2018_input_preflight.json)。

`CUMCM-2025-C-HELDOUT-RESERVED` 不进入成绩表：六项访问标志均为 false，来源见
[`project_state.json`](../../state/project_state.json)。

## 关键实现、字段与测试定位

- 实际 controller：[`scripts/finalize_fresh_c_validation.py`](../../scripts/finalize_fresh_c_validation.py)，
  `complete()` 的 `GATE_FINALIZATION` 约在第 655 行，CLI 默认 `--test-field` 约在第 749 行。
- formal runner：
  [`.agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py`](../../.agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py)，
  `validate_semantic_claim_support()` 约在第 801 行，predictive predicate 约在第 909 行，CLI parser
  约在第 5140 行。
- 2017 C builder：
  [`build_post_selection.py`](../../evals/validation_code/phase-004c4/CUMCM-2017-C-VALIDATION-003F/build_post_selection.py)，
  约第 291 行无条件写 positive held-out predicate；这是 frozen episode 证据，不得原地修。
- 现有最小测试入口：
  [`test_fresh_completion_controller.py`](../../tests/unit/test_fresh_completion_controller.py)、
  [`test_actual_controller_black_box.py`](../../tests/integration/test_actual_controller_black_box.py)、
  [`test_actual_controller_neutral_e2e.py`](../../tests/integration/test_actual_controller_neutral_e2e.py)、
  [`test_actual_controller_adversarial.py`](../../tests/integration/test_actual_controller_adversarial.py)。
- 最新技术字段：`state/project_state.json` 的 `technical_adjudication_status`、`blockers`、
  `next_phase_allowed`；2017 terminal freeze 的 `controller`、`selection`、`run_count`、
  `terminal_constraints`。

## 当前结论

RC7 release 本身有确定性验证价值，但当前陌生 C Validation 没有通过。CI、9/9 Run、neutral E2E 或
历史回归都不能补偿 Finalization/HF22，也不能把 case 写成 READY。交接后的第一项研发必须保持失败
证据和冻结历史，使用新分支、新测试与新版本化结果；不得修改 2017 terminal record。
