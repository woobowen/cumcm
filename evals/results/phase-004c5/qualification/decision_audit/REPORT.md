# RC8 Candidate POST_DECISION Audit

结论：**PASS，仅限 `RESEARCH_AND_FRESH_VALIDATION_ELIGIBILITY_ONLY` proposal 决策链。** 本审查不执行 acceptance/activation；不证明陌生题、比赛或任何旧题全题成功。

- Implementation subject: `29cf1d7566809519ca92b6a29f555ce0c0b5b204`。
- Evidence commit: `2b2aa24a83b44baf595cb189755e182c33da4953`。
- Bundle: `RC8-CANDIDATE-POST-DECISION-AUDIT-004C5`，文件 SHA256 `1cfd099e30c92d2a6189f42b074fabfae85293fc2a811420a7f1523ae6c973cb`。
- 独立原生角色为 `automated_decision_auditor`；只接收固定 proposal 与冻结前置审查。model/reasoning 均 UNKNOWN，没有投票。

## 实际核验

首个命令 `ls -la`，观察既有 .venv、contracts/state/active plan。阅读项目框架及相关政策后，沿用 `.venv/bin/python -B`。

29/29 bundle 文件 hash 匹配；完整 subject mapping 共 772 个共享实现/测试文件，与 Git subject/current 字节相同。29 个 bundle 文件也均能在指定 evidence commit 找到完全相同字节。六类 receipt、其 evidence、实际 stdout/stderr、native 02/03/incremental29 原始命令和 streams 全部 hash 匹配。元数据/hash 核验共 1891 项，0 mismatch；全部实际输入路径/hash 与只读 Git 命令、退出码及输出 hash 见 independent_verification.json。

| 本审查实际 CLI | exit | 结果 |
|---|---:|---|
| RC8 candidate | 0 | PASS |
| RC8 live，active RC7 | 1 | RC8_RELEASE_ACTIVATION_INVALID，符合未激活状态 |
| RC7 candidate | 0 | PASS，历史 subject |
| RC7 live | 0 | PASS，历史 subject |
| release consistency | 0 | CANDIDATE_STAGED_NOT_ACCEPTED，active RC7 |
| RC5 claim-scope history | 0 | PASS，保留原版本阻断与旧历史 |
| 2019 terminal，require-delivery | 0 | PASS，原 subject，workspace_verified=false |

精确 argv、cwd、时间、exit、stdout/stderr 在 01–07.command.json 与对应 logs；tool_receipts.json 汇总。本审查未重跑 full CI：其冻结真实回执 exit0、原始和 tracked 日志完全一致，记录 **2153 passed, 1 skipped**；focused 为 **100 passed**，strict 为 PASS。测试/CI不等于全题科学通过。前置原生审查从703775b到1b508aa再到29cf1d7保留原始反例和针对性 closure，本次没有用这些意见投票。

## 数值和来源边界

15 次真实 Development captures 保留：2021 8/9（5 SUCCESS、3 FAILED），2022 7/9（7 SUCCESS）。本次核验汇总到原始 regression receipts/output/checker/capture hash 与 actual subject 的绑定，不读取 raw 工作簿、不重算科学模型。raw input 的再次 hash 核验仍归属主编排器，不能改称本原生审查亲读。

只有当前 d9 的 4 次 candidate Run 被声明可迁移到资格 subject：2021 单 baseline 的 core/producer/helper/checker，2022 三 Run 的 core/producer/checker；另列 core、finalizer、Development controller 三路径 runtime 等同。所有这些路径在 d9、29/current bytes 一致。其他11次执行没有重标 subject；这是字节一致性核验，非新执行。2021当前仅非排名复算，17 requirements 未接受 semantic selection；2022 11/13 有限支持，REQ-3A/REQ-EVIDENCE不足；两题 whole=false、Final访问0。

2021历史压力库存/运输违约、原生A/B模板与Q4独立全局证书等缺口保留。2022独立model/cluster fit复核有限、未知真值不存在、分数未校准、风化因果效应不可识别。这些缺口影响科学可声称范围，未被计算一致性或进程分离消除。既定protocol不要求Development全题通过才能取得受限Validation资格，因此它们在本proposal内为明确未完成项，不是可被隐藏的成功。

四个方法Source注册了具体决策用途，但content_hash均null；本审查未联网重取，因此不声称完整来源内容冻结或外部独立验证。环境Python/platform/package版本与现有.venv实际观察完全一致；它是本机观察，不是portable lockfile。installed cumcm-skill-lab为0.1.0、repo声明0.2.3，是已记录的环境差异。

## 激活和新题边界

本次终止观察active仍RC7，current_validation_case=null、next_phase_allowed=null、TEAM_COMPLIANCE_REVIEW=NOT_RUN。proposal effective=false、activation pending。当前state中的两个旧pending blocker标签仍由主编排器在正式审查接纳时据证据处理；本审查不写正式状态。

主应以本冻结proposal+审查生成正式acceptance记录，保持已接受772文件映射和环境字节，执行live验证与远端冻结后才开放输入。environment与before-input protocol已在snapshot/bundle/evidence commit绑定，本审查实际hash核对；不得把future remote freeze写成已完成。

预注册分母固定2：2016 C后2015 C，2014仅输入不可用/损坏缺附件/结果前污染替换。串行一个fresh worker+main；每题7200秒完整窗口，第二题须全局截止前至少8100秒。共享Skill/environment/rubric在输入前冻结；case protocol在主数值结果前远端冻结；selection在Final前冻结；所有主问题科学PASS还要求适当独立检查和无重大未解科学异议。预算不足保持NOT_RUN_BUDGET且分母不变。无2025/2026/新题内容访问。

## 写操作、验证和限制

没有公共文件、Git、state、配置写操作；没有spawn、安装、付费API、网络/MCP、答案/vault/raw-input访问或新Run。只读Git show/ls-tree由受测checker和本hash核验用于已授权subject验证，没有Git mutation。自有写入全部在 `.cache/pr12-rc8/candidate-decision-audit/`：输入快照、核验JSON、命令/stdout/stderr/exit、此报告与audit.json；不把这些ignored证据写入算作公共write。

一次辅助读取错用了initial_registration的父目录，得到FileNotFoundError（exit1）；随后rg定位qualification/initial_registration.json并成功读取。该路径查询错误未参与任何技术或科学判定。其余阅读命令为cat/sed/rg和Python只读摘要；实际工具对话保留全文，读取文件hash集中于independent_verification.json。

结构化audit以contracts/subagent_audit.schema.json实际验证；output_hash按移除自身字段后的canonical JSON SHA256计算。审查不代替未来fresh终审、人类合规或远端交付。
