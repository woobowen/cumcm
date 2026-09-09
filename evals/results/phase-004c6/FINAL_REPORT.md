# Phase 004C6：CI与流程修复、开发验证及候选拒绝

状态：`RC9_RELEASE_REPAIR_BLOCKED`；机器拒绝经独立Decision Auditor复核，受测内容已核验远端交付。

**本轮未达到全部目标。** 当前完整CI与十项中立规格通过，公共核心已经有真实的非预测Final无环正向路径；
两个新Development都完成真实模型计算与独立验算，但因执行端与后续Gate的缺省场景哈希语义不一致，
均在Final之前失败。RC9不激活，不能宣布工程整体闭合、两题完整交接或泛化成立。

## 三个终点

| 终点 | 结果 | 可核验边界 |
|---|---|---|
| ENGINEERING_CLOSURE | 未成立 | CI兼容修复成功；实际已知题公共完成路径仍有场景身份缺省值阻断 |
| SCOPED_DEVELOPMENT_COMPLETION | 完整路径0/2 | 两题各2真实模型、3独立checker；有限数值结果可审，Final0、handoff0 |
| GENERALIZATION_EVIDENCE | 未新增 | 旧004C5 Validation科学0/2永久不变；本轮新增独立Validation=0 |

## M1：CI、历史身份与合法扩展

原固定8案例断言改为原十案例所有历史字段不变、case唯一、逐条合同和合法扩展检查；
原phase固定断言改为显式phase/status/version/case/decision关系，保留历史终局锚点。
负例覆盖删除历史、改旧hash、重复ID、缺字段、错误tuple、错误版本/阶段/根目录及终局关系。
新registry目前12案例，旧十案例全部原字段保持不变。

首个共享subject完整CI暴露另外三处失败：Skill版本断言、active-plan断言和新registry目标合同字段。
前两项按明确版本/phase/计划关系修复，旧计划归档字节仍与历史Git对象一致；登记合同补齐，未放宽策略。
远端早期测试另缺NumPy/SciPy，已按现有bootstrap在项目dev依赖声明已有本地版本；本机未安装新包。

共享r1 `2d74ca82e2d52799e81bf5d95850570f14d93a58` 保留首次失败和零数值启动事实；
统一r2 `10e8b038d571b88ce2b7f2388da00a618c774f69` 是两题实际使用的共同subject。
r1原root、registration、design与Git对象保留，不使用同名RC8静默替换。

当前树执行RC8 live核验实际被 `RC8_CANDIDATE_CURRENT_IMPLEMENTATION_DRIFT` 拒绝；
`--historical`对原RC8 subject核验通过。历史研究资格不能覆盖当前RC9字节。

## M2/M3：公共入口与十项规格

公共核心/控制器已实现：开发核验、比较与必要稳健性 → selection freeze → 授权 → STARTED →
独立Final → 回执 → Final接受 → Claim/handoff。中立正例真实执行到handoff；
提前Final在访问/进程前拒绝并保留请求；失败/超时/部分输出消耗Final；重复回执核验不重执行。
这些结果不等于两题新Development已经走完同一路径。

未知未来真值不再是生成条件预测的必需输入；准确率主张仍需真实证据。
同实体预测保留起点前历史，特征、变换与拟合须满足可见性；新实体迁移仍执行实体隔离。
指标绑定target、单位、时点、公式、分母、样本单位、聚合、方向和零分母政策；remaining与elapsed误差不能混同。

| 原中立规格ID | 当前实际测试 |
|---|---|
| NONPRED-ORDER-POSITIVE | PASS |
| NONPRED-ORDER-NEGATIVE | PASS |
| PREDICTIVE-RELABEL-NEGATIVE | PASS |
| TEMPORAL-SAME-ENTITY-POSITIVE | PASS |
| TEMPORAL-FUTURE-LABEL-NEGATIVE | PASS |
| TARGET-DENOMINATOR-NEGATIVE | PASS |
| REGISTRY-EXTENSION-POSITIVE | PASS |
| REGISTRY-HISTORY-NEGATIVE | PASS |
| TERMINAL-PHASE-POSITIVE-NEGATIVE | PASS |
| SUBJECT-IDENTITY-POSITIVE-NEGATIVE | PASS |

优化、同实体时间预测、混合多问三类真实CLI E2E均PASS。
[101项定向测试](qualification/receipts/focused_r2.json)、[原始JUnit](qualification/receipts/focused_r2.xml)和
[十规格/三E2E映射回执](qualification/receipts/neutral_r2.json)绑定同一当前subject；不是只跑helper或全部拒绝。

## M4：两题真实新Development

| 案例/逐问 | 实际计算与独立验算 | 不能据此声称 |
|---|---|---|
| 2016 Q1 | 九电流曲线重构MRE0.0780032%；9.8V时30/40/50/60/70A剩余约591.678/429.791/326.197/277.937/254.685 min | 新电池准确率、单一紧凑全局公式 |
| 2016 Q2 | 七组留一电流MRE1.021976%；55A条件总时长1162.5881 min | 未观测55A的实际精度 |
| 2016 Q3 | 六历史起点remaining-MRE5.196575%；当前条件剩余193.4418 min | 未来精度、跨电池泛化、校准区间 |
| 2015 定义 | 月心8–12°、太阳−12至−6°，10°树梢，七城市×366日 | 唯一诗词解释 |
| 2015 参考一致性 | 168行；RMSE0.000749386°，最大绝对差0.001445385° | 现场观察/历史事件验证 |
| 2015 北京/哈尔滨/上海 | 条件时窗15/18/12个 | 实际可见概率 |
| 2015 广州/昆明/成都/乌鲁木齐 | 条件时窗12/13/13/16个；七城总99个 | 天气、地形、叶季或人类相遇概率 |

2016的184.8261–205.4755 min范围只是模型敏感性。原生只读复算确认正确remaining分母；
改用总elapsed分母会错误虚降同一批误差至约1.64877%，不能替代5.19658%。
六个起点来自同一电池的相关历史状态，不是六个独立实验。

2015基线GEOCENTRIC虽然model/checker进程exit0，REQ-VALIDATION实际false：最大差1.022691°超过0.05°阈值。
负结果保留。选中TOPOCENTRIC的独立实现高度差最大0.0000419644°、时窗端点差最大0.996308s；
实现一致性与参考星历一致性不同，两者都不是独立外部实测。

每题4次模型CLI请求包含2次错误Run ID前置拒绝和2次真实模型进程；未把请求失败从预算中删除。
每题3次注册独立checker进程，Final0；两个完整公共完成调用均真实拒绝。
[2016逐问报告](CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006/SCIENTIFIC_REPORT.md)、
[2015逐问报告](CUMCM-2015-C-POSTVALIDATION-DEVELOPMENT-007/SCIENTIFIC_REPORT.md)和
[精确失败终局/执行证据](qualification/receipts/development_results_r2.json)保留全部边界。

## 审核、候选身份与停止理由

R6原生预审仅覆盖版本/计划/目标登记/准备接口差异；不是全部协议完整独立PASS。
R7实际结果审查：有限数值摘要与负终局事实PASS，候选接受FAIL，R7-001场景缺省语义问题仍OPEN。
新的[Decision Auditor](qualification/decision_audit_001/REVIEW.md)独立运行原checker重放和元数据审计，
结论 `PASS_FOR_REJECTION`；这是对拒绝正确性的通过，RC9候选仍FAIL/BLOCK。后写入state及最终远端由主Agent另行验证。
原生审核、主Agent核验和独立Python checker进程分别记录；审计脚本中的大量行级断言不是独立科学实验。
早期一次协议审核受平台内容审查中断，其部分发现和中断均保留，未冒充完成。

[原裁决器已拒绝RC9候选](qualification/rejected_r2/rc9_candidate_decision.json)，在精确subject隔离工作树中二次重放一致。
候选归档在rejected_r2，未写入active槽位、未激活；主工作区CI的PASS不会将该拒绝变成资格PASS。
[计时澄清](qualification/rejected_r2/timing_clarification.json)与
[预审范围澄清](qualification/rejected_r2/protocol_review_scope_clarification.json)保存原件并显式限定解释。

本轮已经登记两个功能候选，且每题模型CLI请求4次已用完。继续修改共享实现或重新数值运行需要超出已登记边界，
因此没有第三subject、没有补写冻结场景哈希/时间、没有删除失败trace重试。5–7小时是工作目标，不是扩展试验预算的依据。
本轮存在预算使用失误：第一次完整CI失败消耗了统一候选修订，错误Run ID又消耗各两次CLI请求；这些代价如实保留。

历史active仍为RC8限定研究资格；当前实现Project0.3.0-competition-rc9、Skill0.2.0-competition-rc9、distribution0.2.3是未获资格的候选字节。
TEAM_COMPLIANCE_REVIEW保持NOT_RUN；无比赛资格或技术拒绝的人类覆盖。

## 交付与可复核记录

目标分支：`feat/phase004c5-p0-01-finalization-hf22-repro`；PR #12保持OPEN Draft。
共享实现/本地完整CI/远端feature SHA/PR实际merge-checkout SHA分开记录，避免提交自引用。
最终受测内容HEAD为 `99e96dc40314c6b80d5f94bdad2ce48773f228c4`，本地完整 `bash scripts/ci.sh`
通过：2240 passed、1 skipped（pytest 456.23s），见[实际回执](qualification/receipts/final_full_ci.json)。
同一feature HEAD的远端run34311473962已SUCCESS，实际PR merge checkout为
`7565ac12e799b664c026d7a34325167796ad31b9`：2240 passed、1 skipped（494.27s），
见[远端日志观察](qualification/receipts/remote_ci_99e96dc.json)。唯一skip来自已经执行过的不可变Phase002D Batch1，未跳过新增失败。

[最终交付回执](delivery/final_delivery_receipt.json)绑定上述受测内容与科学/资格负终局。
回执自身随后单独提交；其发布提交不包含自己的未来SHA，最后发布HEAD及对应当前远端CI在PR #12说明中实时核验。
registry里的 `LOCAL_FROZEN_PENDING_REMOTE_DELIVERY` 是首跑冻结当时的状态；本次交付另有已观察远端SHA，不改写该历史冻结记录。

本轮于2026-09-09 01:35:18 UTC开始；收口时的实际钟表时长及同口径token增量见
[成本观察](qualification/cost_observations.json)。5–7小时目标未满：两个已登记功能候选及每题4次CLI请求的边界已经触及，
本轮以负结论收口，不能把提前收口描述成全部目标成立。精确有效工作时长、input/cached/output拆分与费用为UNKNOWN。

[环境记录](qualification/environment_changes.json)：本机新增系统包/语言包/工具链/全局配置均0；
项目dev声明NumPy2.4.6/SciPy1.17.1并已由远端现有bootstrap验证。无付费模型API；token/cost按实际观测口径记录，未知计费字段不推算。
原题、原始数据、密集观测表、答案、缓存、凭据不上传；公开结果为派生数值与可核验哈希。

完整恢复边界及下一窗口需处理的精确问题见 [DELIVERY_AND_RECOVERY.md](DELIVERY_AND_RECOVERY.md)。
