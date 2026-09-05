# RC7 诚实交接

> 当前状态：**研发暂停，交接资料就绪不等于 Skill 研发完成。** 目前正式技术结论仍是
> `C_TARGET_VALIDATION_FAILED`。RC7 已发布，但没有 accepted Final Run、accepted final
> Claims 或 accepted paper handoff。不要用 9/9 Run 成功、回归通过或 CI 通过替代该结论。

## 先看风险

1. 2017 C 的实际 controller 在 `GATE_FINALIZATION` 阻断。RC7 的 `execute`/output 接口没有
   final-phase/test-authorization 输入，却要求所选 output 提供 `sealed_test_metrics_b64`；在已冻结的
   9 次尝试之外补 Run 或改 output 都会破坏 one-shot 约束。
2. `HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION`：REQ2 的 semantic support 声称
   `held_out_test_valid=true`，但权威 selected output 记录的是
   `DEVELOPMENT_GROUPED_OOS`、`NOT_AUTHORIZED/0` 且 `held_out_test_valid=false`。当前 Gate 没有把
   support predicate 交叉绑定到 Run/output/test-access 事实。
3. `CUMCM-2025-C-HELDOUT-RESERVED` 仍为 `SEALED_NOT_ACCESSED`，六项访问标志均为 false；接手、
   文档检查或首个修复都不得访问它。
4. 当前 `.venv` 与 ignored `.cache/` 是本机资产，不是可移植发布物；数值运行依赖没有完整写入
   `pyproject.toml` 或 lockfile。完整 Git 历史也是部分冻结/replay 检查的依赖。

权威状态见 [state/project_state.json](state/project_state.json)，最新失败结论见
[reports/phase004c4_validation_decision.md](reports/phase004c4_validation_decision.md)，机器证据见
[controller_outcome.json](evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/controller_outcome.json)
与 [HF22 challenge](evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/challenges/HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json)。

## 项目与团队边界

本仓库为三人 CUMCM 团队维护一个 evidence-first 建模 Skill，主目标是陌生 C 题。它负责从题目接收、
需求拆解、资料与数据审计、模型和实验、真实 Run、比较、稳健性、Final Run、Claim 验证，到版本化
evidence package。正式 Skill 是
[cumcm-modeling-evidence](.agents/skills/cumcm-modeling-evidence/SKILL.md)。

论文/绘图组消费 [modeling-to-paper/v1](contracts/modeling_to_paper.schema.json) 中的公式、符号、结果表、
figure-ready data、Claim、来源、局限和复现信息，可以调整表达和视觉呈现，但不能改写实验事实。最终论文
文笔、图形美化、排版和提交打包不属于本 Skill 的主要责任。候选 handoff 文件存在不表示 handoff 已被
接受；失败 Validation 的候选材料只能作为诊断或明确标注的部分成果。

## 当前基线与能力边界

- 交接代码基线：`f194c5c0e46708a4b084e63d0beab0ec05b21c09`，即 PR #10 的 main merge commit。
- 正式 Project 版本：`0.3.0-competition-rc7`；正式 Skill 版本：
  `0.2.0-competition-rc7`。
- 架构：`ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`；能力标签：
  `COMPETITION_RC`。
- RC8/004C5 仅有后续建议，**尚未实施**；预备分支的存在不是研发证据。
- RC7 的实际 controller、十 Gate trace、三种 selection mode、Run/Claim/handoff contracts、失败保留、
  STALE 传播和离线检查均有实现与回归证据。
- RC7 不能保证陌生题完成率、外部效度、生产适用性、全局最优、完整 sealed Stage 1/Stage 2、完整消融
  或成本；当前 Validation 也未通过。

根 `VERSION`、RC7 manifest 和 state 对正式 competition release 的版本一致；
`pyproject.toml` 的 Python distribution metadata 仍为 `0.2.3`，仓库没有找到两者同步语义的明确说明。
接手者应把它视为待澄清的版本面差异，而不是擅自升级或合并版本号。

## 怎样理解现有证据

| 证据类型 | 含义 | 不能推出 |
|---|---|---|
| answer-sealed Development 首跑 | 在参考答案解封前，按冻结 Skill 得到一次真实结果，失败也保留 | Validation、Held-out 或泛化通过 |
| Development regression | 参考解封后验证修复和兼容性，可正常修错 | 新题首跑能力或独立泛化 |
| Validation | 不同题、冻结版本、one-shot、答案封存的正式评估 | 若 Gate 阻断，即使 Run 成功也不能写 PASS |
| diagnostic/read-only replay | 对历史 artifact/commit 做只读一致性检查 | 新模型执行、新科研结果或历史结论升级 |
| synthetic smoke/E2E | 项目原创小用例验证合同主链 | 真实赛题质量或 C 题泛化 |
| CI | 代码、合同和历史检查在该提交上通过 | 科学结论正确、未知题完成或 paper handoff 被接受 |

案例的真实分母、版本与边界见
[STATUS_AND_EVIDENCE.md](docs/handover/STATUS_AND_EVIDENCE.md)。seed、Stress、同题回归均不作为独立题目；
不同 Skill 版本的结果不合并为“当前版本成功率”。

## 接手顺序

第一步：使用完整 Git 仓库，确认工作区 clean、分支/HEAD、根 `VERSION`、Skill `VERSION` 和
`state/project_state.json`；不要先运行模型，不要读取 ignored 官方输入。

第一小时建议：

1. 读本文件、[CODEX_TAKEOVER.md](CODEX_TAKEOVER.md) 和
   [NEXT_STEPS.md](docs/handover/NEXT_STEPS.md)。
2. 按项目启动顺序读 `GOALS.md`、`WORKFLOW.md`、唯一 active plan、project state，再读正式 Skill
   `SKILL.md`。
3. 用 [RUNBOOK.md](docs/handover/RUNBOOK.md) 的只读命令核验版本、Git 历史、CLI help 和状态。
4. 查看 [ENVIRONMENT_AND_ASSETS.md](docs/handover/ENVIRONMENT_AND_ASSETS.md)，区分声明依赖、本机
   包、ignored raw input、tracked derived evidence 和不可交付的凭据/个人配置。
5. 返回接手回执：已核验事实、UNKNOWN/NOT_VERIFIED、未访问范围，以及首个最小任务建议。

首次开发任务不要展开整份 RC8，也不要先加几十个 Gate 或跑多道题。先定位 Finalization 与 HF22 的
真实调用路径，用现有 project-original fixture 建立最小黑盒复现，再提出最小接口/交叉绑定修复。

最短阅读路径：

1. 本文件；
2. [current state](reports/current_state.md)；
3. [004C4 validation decision](reports/phase004c4_validation_decision.md)；
4. [STATUS_AND_EVIDENCE.md](docs/handover/STATUS_AND_EVIDENCE.md)；
5. [NEXT_STEPS.md](docs/handover/NEXT_STEPS.md)；
6. [RUNBOOK.md](docs/handover/RUNBOOK.md)。

## 环境、资产与合规

不要复制 `.venv` 到新电脑后承诺可用，也不要交付整个 `.cache`。2017/2018 官方输入只在 ignored
cache 可见；tracked `evals/results/` 保存公开派生证据和哈希，不包含将原始题面再次发布为交接材料。
缓存缺失不影响读代码和部分轻量检查，但会阻止依赖 raw input 的复现。ZIP 源码包或浅克隆不能未经
验证替代完整 Git 仓库，因为 checker 需要历史 commit/blob。项目许可证仍是
`PROJECT_LICENSE_UNDECIDED`。

本次于 2026-09-06 核验了组委会官方
[《全国大学生数学建模竞赛人工智能工具使用规定（2026年试行）》](https://www.mcm.edu.cn/html_cn/node/fef94648f2836ab6cc81586f4c38512b.html)：
页面日期为 2026-08-03，规定自 2026-09-01 起试行。自动技术检查不能替代参赛队对原创性、真实性和
准确性的责任；AI 使用、采纳、修改与人工核验应如实记录，不能由 Agent 代填“已人工审核”。赛时协作和
资料发布必须以当届官方规则为准，公开仓库交接流程不能机械套用为赛时公开题解流程。

## 后续优先级与启动 Codex

- P0：先复现真实 Finalization/HF22 调用路径，再做最小接口与 predicate-to-authoritative-fact 修复。
- P1：让专业资料、数据充分性、模型适配、多问依赖、科学质量与效率真正进入实验决策。
- P2：冻结新版本后再做跨题 Validation、队员接手演练，并仅在全部条件满足时考虑保留题。

完整任务卡见 [NEXT_STEPS.md](docs/handover/NEXT_STEPS.md)。把
[CODEX_TAKEOVER.md](CODEX_TAKEOVER.md) 原文交给新的 Codex 即可：默认 `TAKEOVER_ONLY` 只读接手；
只有接手者明确指定 `RESUME_FIRST_FIX` 才在新功能分支处理首个最小任务。该提示词不携带本次交接 PR
的合并授权。

**收口声明：本次交接可以完成，RC7 的研发和陌生题验证仍未完成。**
