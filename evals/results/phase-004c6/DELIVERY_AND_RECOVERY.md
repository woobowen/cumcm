# 004C6 交付与恢复边界

本轮实施与已知题开发验证已产生真实证据，但未达到完整工程闭合或两个子案例的完整交付。
RC9 共享实现 `10e8b038d571b88ce2b7f2388da00a618c774f69` 不应激活。
历史 RC8 限定研究身份仍指向 `29cf1d7566809519ca92b6a29f555ce0c0b5b204`，
激活锚点 `8ef732b45cf3cb04262317cdfa13a176b47eebe0`。当前目录的 RC9 字节不能借用该资格。

## 保留与证据入口

- 本轮代码、Skill、测试与规则在现有 PR #12 功能分支，不改 main，不 Ready/merge。
- [共同 subject r1](qualification/shared_subject_r1.json) 是未执行数值实验的第一次冻结。
- [统一 r2 转换](qualification/preexecution_supersession_r2.json) 保存首轮完整 CI 的3失败与零模型/零checker/零Final前提；原r1设计、登记和root保留。
- [共同 subject r2](qualification/shared_subject_r2.json) 绑定实际执行的792文件实现与两个数值设计。
- [当前完整 CI 回执](qualification/receipts/candidate_full_ci_r2.json)：2240 passed、1 skipped，完整 `bash scripts/ci.sh` exit0；受测HEAD与共享实现映射分别记录。
- [101项定向回归](qualification/receipts/focused_r2.json) 与 [十项中立规格/三类CLI](qualification/receipts/neutral_r2.json) 均为当前subject实际执行。
- [2016失败终局](CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006/terminal/decision.json) 与 [科学报告](CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006/SCIENTIFIC_REPORT.md)。
- [2015失败终局](CUMCM-2015-C-POSTVALIDATION-DEVELOPMENT-007/terminal/decision.json) 与 [科学报告](CUMCM-2015-C-POSTVALIDATION-DEVELOPMENT-007/SCIENTIFIC_REPORT.md)。

每题4次模型CLI请求已用完：两次不合法Run ID在模型进程前拒绝，两次实际模型成功。
每题3次独立checker进程（初始两次、选中结果复算一次）；Final0，无接受的handoff。
机器start ledger统计实际进程，CLI请求计数在另一个明确字段保留，两种口径不可混同。

## 已确认的新阻断

固定公共执行器允许 `experiment_plan.scenario_hash` 缺省，执行时根据冻结输入SHA列表派生场景哈希。
固定controller与公共核心的Final前复核却把 `plan.get("scenario_hash")` 的 `None` 直接送入兼容性Gate，
再与真实capture的非空派生哈希比较。因此两个新子案例均在第6个Gate
`GATE_COMPATIBILITY_PORTFOLIO` 被 `RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND` 拒绝。

前五Gate通过；语义、聚合、Final、Claim/handoff均没有执行或被接受。
新root中的core状态保持 `RUNNING` 是其停止时的真实状态；registry的 `FROZEN` 和外部失败终局关闭该episode，
并不伪造core曾达到Final状态。controller已经写入不可覆盖的完成trace，不能删除该trace重试。

[纯参数诊断](qualification/receipts/scenario_binding_diagnostic_r2.json)证明：从原始capture输入SHA重算默认值，
只在内存中将该单Gate的参数由None替换为默认值，该Gate返回PASS。
这个诊断没有更改计划、输入、Run、时间或Gate记录，也没有证明后续语义/Final通过。
它不是已实施的修复，不能据此把真实失败改成成功。

## 本轮停止功能修订的原因

本轮维护协议已经登记两个功能候选，且两题模型CLI请求已达每题4次上限。
两题当前轮均已完成并冻结后确认同一新阻断。不会通过重命名subject、删除失败请求、
覆盖r1/r2、补写实验前哈希或扩大预算继续寻找成功。
剩余工作限于真实审查、证据复核、负决定、报告与远端交付。

## 后续新授权窗口需要处理的精确范围

1. 统一公共执行器、controller和公共Final前复核对缺省场景身份的语义。
   可选择在模型启动前要求显式合法场景哈希，或由同一个冻结输入解析函数产生并核验默认值。
   选择必须对所有公共入口一致，不能只修两题wrapper，也不能从未来Final回执补值。
2. 准备入口应在启动前验证最终将使用的完整场景/输入/配置合同；其正反规格应同时覆盖显式值、缺省值、错误值与输入重排。
3. 在新维护subject上执行中立CLI正负回归、原有HF22、独立审核和完整CI，再决定是否有资格运行新的已知题开发episode。
4. 需要重新实验时，登记新的case ID、root、预算与Run；旧004C5和本004C6失败原件均不可续跑或改写。
   新预算必须来自新授权，不能把本轮剩余钟表时间当成新的模型请求预算。
5. 即使后续完整路径通过，2016未来终止精度、跨电池迁移、校准区间以及2015现场/历史验证仍需对应独立证据。

## 数据、环境与成本

原题、原始数据、密集观测表、答案、缓存和凭据不发布。公开内容是派生数值、合同、独立验算摘要、命令回执及原始文件哈希。
完整新root和原始stdout/stderr保留在忽略目录；没有向旧Validation root写入Run、checker或Final。
科学重放需要合法原始输入匹配登记SHA；仅有公开摘要不能声称已完成原始数据的离线数值复算。

本机新增系统包、语言包、工具链、全局配置均为0。项目dev依赖声明新增已有本地版本
NumPy2.4.6/SciPy1.17.1，以便远端CI运行已加入的数值测试；详见
[环境记录](qualification/environment_changes.json)。没有付费模型API调用。
原生审核与独立Python复算分开记账；provider缓存token、模型推理token、费用和CPU成本不可见时记UNKNOWN。

旧Validation科学0/2永久不变，本轮新增独立Validation=0。没有比赛合规、泛化或技术接受的人类覆盖。

## 拒绝候选的机器重放

拒绝候选保存在 [rejected_r2](qualification/rejected_r2/rc9_candidate_snapshot.json)，
对应 [机器决定](qualification/rejected_r2/rc9_candidate_decision.json) 与
[实际裁决回执](qualification/rejected_r2/adjudication_receipt.json)。没有把它写进主工作区的active候选槽位。
主工作区CI验证实现/合同和合法未激活状态；该CI的PASS不表示归档候选获得资格。

本机已实际验证的隔离重放方式：使用已有 `.venv/bin/python`，在忽略目录的精确subject detached worktree
`.cache/pr12-rc9/qualification-replay-r2` 中运行原有
`scripts/check_phase004c6_rc9_release.py --stage candidate`。
该工作树来自subject `10e8b038...`；公共004C6证据按原相对路径复制进去，归档snapshot在工作树内恢复为
`evals/results/phase-004c6/qualification/rc9_candidate_snapshot.json`。原裁决器代码没有修改。
再次只读重放退出2、决定逐字段一致，这是预期拒绝，不应改成exit0。

在另一主机重放，需要完整Git对象、现有项目依赖与本轮公开证据。建立新的隔离detached worktree，
保持792文件subject映射不变，复制公开证据及snapshot后运行同一原checker；不要覆盖主工作区候选或任何旧决定。
机器资格重放不执行模型、不读取原始题目数据，也不替代需要合法原始输入的科学复算。

[计时澄清](qualification/rejected_r2/timing_clarification.json)保留原裁决记录的一项测量范围错误：
UTC ended_at属于第一次裁决，而elapsed_seconds采样覆盖随后第二次重放；未留存的分段时间明确UNKNOWN。
[审核范围澄清](qualification/rejected_r2/protocol_review_scope_clarification.json)明确R6仅为版本/计划/登记准备差异审查，
不能升级为全部协议完整独立PASS。两项原件均保留，澄清不改变机器拒绝。
