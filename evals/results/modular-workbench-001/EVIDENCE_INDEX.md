# 十四模块工作台证据索引

唯一使用入口：[START_HERE](../../../docs/modular_workbench/START_HERE.md)。
正式状态仍以 [project_state](../../../state/project_state.json) 和 active plan 为准。
本目录是建设与有界演练证据，不是参赛题 workspace，不提供整题答案或最终论文。

| 对象 | 可审查记录 | 范围 |
|---|---|---|
| 完整任务与授权 | [根任务书](../../../CUMCM_MODULAR_WORKBENCH_BUILD_PROMPT.md)、[Plan](../../../plans/active/PLAN-0004C7-modular-workbench.md) | BUILD_AND_ACCEPT仅本轮；未来逐模块 |
| R7复现与修复 | [baseline](baseline/)、[B1定向回执](b1_directed_receipt.json)、[最新定向日志](commands/final-directed-003.log) | 原始失败保留，缺省/等价显式路径与拒绝边界 |
| 真实公共CLI逐调用 | [预测54次](original/prediction/cli_commands.jsonl)、[优化54次](original/optimization/cli_commands.jsonl)、[混合54次](original/mixed/cli_commands.jsonl) | 精确保留驱动当时记录的PYTHON/WORKBENCH/CASE_ROOT别名及实际时间、退出码、结果hash |
| 14模块实际执行 | [机器矩阵](acceptance_matrix.json)、[逐模块记录](original/mixed/modules/) | 实际request/report/completion；不等于14个科学PASS |
| 预测路径 | [精确记录包](original/prediction/records.json)、[真实CLI回执](commands/public-water-prediction-006.json) | 合成历史样本与有条件外推，未来精度未知 |
| 非预测优化 | [精确记录包](original/optimization/records.json)、[真实CLI回执](commands/public-water-optimization-006.json) | 整数采购求解、约束复算、无环Final |
| 三问组合 | [精确记录包](original/mixed/records.json)、[真实CLI回执](commands/public-water-mixed-006.json) | 采购/预测/库存共享依赖，逐问选择 |
| 独立Python复算 | [实际输出](commands/independent-original-recalculation-004.log) | 与producer/checker分别实现的精确有理数复算 |
| 已知Q3第二revision | [登记与终局](CUMCM-2016-C-MODULE-USABILITY-DEVELOPMENT-008-R2/)、[控制器回执](commands/known-q3-controller-r2.log) | 仅2016C Q3接口，2模型/3checker/1Final；非整题、非新Validation |
| 十四阶段完整审查包 | [M01–M14目录与ZIP](review_packages/) | 各包约17–134KB，含本阶段实际输入/公式/代码/核验；M09无未来Final附件 |
| 实际审查小包 | [REVIEW](review_roundtrip/package/REVIEW.md)、[manifest](review_roundtrip/package/manifest.json)、[ZIP](review_roundtrip/package.zip) | 项目原创、本地导出，未自动上传 |
| 反馈回传 | [实际命令与结果](review_roundtrip/actual_exercise.json)、[精确finding/处置记录](review_roundtrip/records.json) | 真算术反例、无证据意见、替代设计、过期及恶意输入分流 |
| 新worker M04接手 | [报告](context_handoff/REVIEW.md)、[原生工作记录](context_handoff/tool_record.json)、[正式完成链](context_handoff/records.json) | 原生受限上下文、真实数学分析，M04停止；非OS隔离或严格盲审 |
| 原生协议审查 | [审查目录](native_review/) | 逐轮反例与闭合；不以多数票决定技术PASS |
| 冻结工程资格 | [候选](qualification/candidate_snapshot.json)、[机器决定](qualification/decision.json)、[Decision Auditor](qualification/decision_audit.json)、[原生报告](qualification/decision_auditor/REVIEW.md) | 精确subject与2806项独立审查；仅MODULAR_WORKBENCH_ENGINEERING_ONLY |
| 接受后复验 | [active重放](commands/active-adjudication-001.log)、[状态相关测试](commands/post-acceptance-tests-001.log)、[提交前strict时序拒绝](commands/strict-post-acceptance-001.log) | 激活RC10后的实际检查，未重新消费科学预算 |
| 完整CI | [命令与日志目录](commands/) | 只认本轮full-ci记录，不用历史2240/1替代 |
| 环境 | [实际环境输出](commands/environment-final-001.log) | 既有WSL/Linux与.venv；Windows原生NOT_RUN |
| 历史保护与隐私修正 | [未发布subject说明](unpublished_subject_notice.json)、[开发证据](development_exports/) | 旧RC8/RC9及Validation/Development终局不改；开发记录不混入最终资格 |

`records.json` 中 `raw_utf8`、`raw_sha256` 与解析内容交叉绑定。worker数值回执中的本机路径另作
脱敏视图，原始hash与视图hash分别保留；不把视图hash冒充原文件hash。原始已知题附件仅留本地，
公开的是派生运行/核验记录、代码与输入hash。完整独立重跑已知题仍需合法取得对应原始附件。

受测公共路径及最终测试/资格subject为 `d1f8532d498307e3b4755c088ce6a0fadfb432bb`。
已知Q3 R2实际运行subject为 `df430c0f0785e83b1a84726e88d25b7b2e0b9d0a`，两者346个实际已知路径
文件及Skill/指引/规则的hash一致；外部依赖和OS记录另列。R1的未发布旧subject仅为开发历史，
不列入最终统一资格，不重复使用其Final额度。

真实网页审核、队员使用验收和TEAM_COMPLIANCE_REVIEW均为NOT_RUN；通俗比赛手册等待真实网页回执后定稿。
