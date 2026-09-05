# Phase 004C2 Acceptance Report

**整体未全部验收。** Claim 合同实现通过已冻结的测试和跨题 artifact 回归；RC5 完整发布验收被 `RC5_VERSION_FILE_MISMATCH` 阻塞。2019 C 一次性 Validation 终局为 `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`，病例 `REJECTED`，`next_phase_allowed=null`。负向终局及未解决缺陷均已封存，不将未通过结果包装为完成。

## 起点与历史保护

任务分支为 `feat/phase004c2-claim-scope-repair-validation-2019c`；起点 `f3812dcd0b1c1bb76224168454719dd3eb112801`，PR #9 已合并。起始 Skill 为 RC4，baseline CI 为 1868 passed / 1 skipped，strict 0 errors / 0 warnings。

2024 原终局提交 `197f62bc75ebe832e9dd3ced0306740f336b80d6`、原 decision、REJECTED 状态、旧报告和数值工作区均未改。34 个受保护 tracked 文件及六个历史病例完整清单哈希通过复核。2024 terminal 文件 SHA256 为 `6e78a9c047b0c2673c17c1e9b055dfa342f681ca5aa86c7b789929aadd138373`。2025 archive/title/problem/attachments/references/answer 六项访问标记均为 false。

## 修复与发布缺陷

旧合同将总体 Claim 同时约束为全局 Final 文本和第一项 requirement 的局部文本。修复采用独立 aggregate ID、PRIMARY 集合精确覆盖、各局部 Claim 的严格 Run/input/code/config/output/manifest/decision 绑定和范围包含检查。optional/diagnostic/supporting 不替代 PRIMARY；legacy 通过纯派生迁移兼容，原工件不覆盖。

两轮正式 Skill 修订已用尽。53 项冻结 Claim/formula/identity 测试、10 项原 output preflight、30 项原 negatives、2 项 synthetic E2E、2020/2021/2022/2023 C 和 2020 A artifact 回归通过。2024 仅执行派生诊断，未产生新数值 Run、未改 verdict、未获得新 Validation 证据。

实现提交 `5673aab61a648be1cd9b87364110cb01c13cd033`；Skill tree `0c27a6aa25d5f591277707fd2343b34e65a703fb`；发布冻结提交 `24265710b3f4b154ccf6eff19614eea7fb3fb0d4`。runner、SKILL.md 和清单声明 RC5，但 Skill 内 VERSION 文件仍为 RC4。Auditor 的 Git blob 比对证明此差异已存在于冻结版本，未发生运行后漂移。不可在本次 Validation 内修正该文件或启动第三修订循环，因此完整发布验收保持 BLOCK。

## 新 C 题一次性运行

`CUMCM-2019-C-VALIDATION-002` 官方题名“机场的出租车问题”。官方获取晚于 RC5 远端回执。题面 PDF SHA256：`e6c3bcbfdb92c633d49712fff7a2ef4bfc9dbaf540b1de4036b0e71503d962d0`；archive SHA256：`f4d17f2dd80990680fcf00b27103b9c349bc1e943a8b852e948183fab882355f`。题面和归档留在 ignored 缓存，未提交正文。工作区未发现已知内容污染；模型先验接触不可核实。

pre-run freeze 提交 `9f7f3ed2d88d8eaffd0ce2468221f65fec4a46de` 经远端核验后，fresh worker 执行 3 candidates × seeds 101/202/303，共 9 次 Run：12:25:35–12:25:39（UTC+8），全部 exit 0 / SUCCESS，累计子进程 1.510821 秒。无重试、无结果后修改，全部 captures/manifests/outputs 保留。

三候选 Q1 平均损失均为 0.10367490253038847 CNY，按冻结字典序规则选择 BASELINE_STATIC_FCFS，所选 Run seed 为 101。一次所选 test 解码发生在 selection 写入之后。Q1-only 排序不能证明联合最优。主要候选 Q4 平均 Gini 为 0.0502965871，高于 baseline 的 0.0453937359；退化结果保留。

独立复算检查了 1,728 个 Q3 批次和 2,871 条 Q4 派车记录；Gini 最大差为 3.0531e-16。数值证据只支持注册假设和有限配置，不能证明真实机场安全或实证有效性。

## Claim、handoff 与裁决

原生合同的 4 个局部 Claim、aggregate coverage 和哈希链结构检查通过；七项公式、符号、结果表、图表数据、局限和复现信息进入候选 native handoff。但所选 baseline 的 Q4 output 为 FCFS，priority 使用次数为 0，不能单独支持局部 Claim 中的优先补偿评价；非零优先策略结果位于其他 Runs。因此不能宣称四问语义 Claim 全部有效。

Q2 明确要求真实机场与城市数据，本次注册输入无此数据。假设仿真不替代实测。native READY 历史保留后，主代理按冻结 rubric 追加 REJECTED；论文交接被拒绝。decision v1 完整保留，v2 仅澄清上述语义与发布缺陷，verdict 未变。

终局提交 `b289f2dfcaebe8edca5335ed4bf89f383c67eb51` 已远端核验。terminal 文件 SHA256：`d8e52a286126b2d4f6848b29c7eaa2e19e963de8d28ab95dc7df0bb0224acc64`；payload SHA256：`64972527ca7c09afbacd70b98047a80d6c714c690a3dbfbdbdd1db90cf0cccad`。保守 whole-episode 计时 3,179 秒。答案在冻结时仍 SEALED；冻结后不再新增 Run 或修改病例。

## 验证与交付

验证主体提交 `77c38237f09b86eb0944a69d5074cf6e3da67c80` 已远端核验。本地完整 `bash scripts/ci.sh` exit 0：1940 passed / 1 skipped（pytest 305.56 秒），strict 0 errors / 0 warnings。远程 CI #33945912145 为 success：1940 passed / 1 skipped（487.25 秒），strict 0/0。render-status、终局哈希/Run 集合和 diff 检查通过。唯一 skip 用于保护已有不可变 Batch 1 证据。检查通过只表示负向记录一致，不消除 `RC5_VERSION_FILE_MISMATCH`。Draft PR #10 保持 OPEN/DRAFT，禁止自动合并。

中间失败已保留：旧阶段/登记表测试的兼容性错误、历史回放环境上下文错误、预结果 controller evidence-list 修正、导出/建目录的记账错误，以及回执引用尚未成为前序提交时的 strict 拒绝。上述错误未导致 2019 模型重试、Skill 漂移或失败 Run 删除。

## 未知、环境与下一步

模型先验、精确模型与 reasoning 标识、真实机场参数、现场几何安全、外部有效性、联合最优、自然语言蕴含和货币成本未得到证明。base64 test 守卫不是加密或 OS 隔离，Monte Carlo 区间仅描述假设条件下的模拟误差。

新增系统包、语言包、工具链、字体及全局配置修改均为 0；复用既有 .venv 和解包工具，无新增安装项需要清理。

唯一下一阶段值：`null`。2025 Held-out 不解锁。本轮保留未解决发布阻塞，不修复并重跑同题；任何后续修订需要新的授权范围和冻结设计。
