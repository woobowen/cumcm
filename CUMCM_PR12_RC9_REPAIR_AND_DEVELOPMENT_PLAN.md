# PR #12 下一轮：研究流程纠偏、CI 修复与开发验证

任务标识：`PR12-RC8-TO-RC9-BOUNDED-REPAIR-004C6`
建议工作窗口：5–7 小时，最长 7 小时；以有效工作和实验证据为目标，不空转凑时长。
本任务书编写所依据的远程提交：`bcf498907cbf282e2c79580ea56b043fc1a7b52b`。
仓库：`woobowen/cumcm`；PR：`#12`。
本文件是用户发出的新任务授权与执行规格，不是已有实验结果，也不授予比赛作品合规通过。

## 0. 本轮目标和完成含义

当前 RC8 已获 `RESEARCH_AND_FRESH_VALIDATION_ELIGIBILITY_ONLY`，不是尚未实现的 RC7 候选。本轮不要重新做接手、重新建设 K1 架构或从头实现 P0-02/P0-03。

本轮必须集中完成：

1. 用新的维护/候选 subject 修复两项历史固定断言导致的 CI 失败。
2. 修复非预测任务的比较/选择与 Final 验证前置循环，在实际公共 CLI/controller 中形成可执行、无环且不放行伪证据的流程。
3. 修复条件预测的输入充分性、同实体时间划分和目标指标语义，避免既错误放行也错误阻断。
4. 将已登记十项中立反例变成真实测试；增加跨结构正向完整路径、负向攻击和独立审查。
5. 新建两个明确的 post-Validation Development episode，实际检验上述修复，不改变旧 Validation 的结果或分母。
6. 候选通过适用检查后才给予新版本的限定研究资格；交付当前 HEAD 的完整 CI、可用入口和诚实能力报告。

本轮不再消耗新的陌生历史题。不打开 2014 C、2025 C 保留题、2026 当届题或 benchmark-vault。不以“再换一道题直到通过”为任务路径。

既有 RC8 双题 Validation 的科学通过率永久保持该次记录的 0/2。新开发 episode 的成功只能说明修复后的已知题开发能力和工程可用性，不能变成新的盲测成功。

定义三个独立终点：

- `ENGINEERING_CLOSURE`：当前完整 CI 通过，历史身份可重放，当前资格记录一致，已知核心接口反例闭合。
- `SCOPED_DEVELOPMENT_COMPLETION`：两个新开发 episode 对题面要求、条件假设、实际计算和结论支持分别形成可核验结果。
- `GENERALIZATION_EVIDENCE`：本轮不新增独立盲测，因此不得宣布泛化已经成立。

任何一点没有成立都要如实报告；“任务窗口已结束”“提交已推送”不替代上述结果。

## 1. 授权、自动推进与安全边界

这是上一轮已结束后的新授权窗口，不延长或重置上一轮的八小时和案例尝试预算。先核验现状，随后直接实施；不在读完资料或修复一项后询问“是否继续”。

允许：

- 在 PR #12 现有功能分支续做，更新新的活动计划、必要代码/Skill/测试、当前规则/Schema/registry/state 与派生报告；
- 修改当前工作树中属于旧 772 文件映射的实现或测试，但必须形成新 subject 并重新验证；不得宣称它仍是旧 RC8 冻结内容；
- 在新目录登记本轮受限 Development episode，读取合法原始历史输入、拟合题内模型、求解、独立复算与导出结果；
- 使用现有原生子代理和项目虚拟环境，普通 commit/push、更新同一个 Draft PR；
- 依据已核实规则记录明确的新维护路由和候选生命周期，不能因旧 state 的 `next_phase_allowed=null` 而只写报告。该 null 继续如实描述旧终局，本轮通过合法新转换进入新任务。

不允许：

- 自动 Ready、approve、merge、直接 push main、force-push、rebase 已发布历史；
- reset/clean/stash/覆盖不明本地工作，或未经核查切换分支；
- 改写旧 RC8 subject、snapshot、接受决定、终局、Run、原审计、旧完整 CI 失败或旧哈希；
- 删除合法 registry 案例、把失败移出分母、放宽判定来掩盖错误；
- 访问答案、保留题、当届题、付费模型 API，读取凭据，改变全局认证/安全/代理策略；
- 自行扩预算、关闭沙箱、伪造独立审核或人工 `TEAM_COMPLIANCE_REVIEW`。

宿主审批、平台额度及用户设置的更低上限始终有效。无法在权限内继续某一动作时保存准确阻断，转做不受影响的有价值任务；不能绕过权限。

## 2. 快速继承核验与渐进阅读

先读适用 AGENTS.md。确认实际 OS/shell、Git 根目录、remote、工作区、目标分支、本地/实时远端 SHA、PR 状态及未提交内容。

目标分支：`feat/phase004c5-p0-01-finalization-hf22-repro`。

观察锚点：

- 任务起点参考：`bcf498907cbf282e2c79580ea56b043fc1a7b52b`；
- RC8 共享受测 subject：`29cf1d7566809519ca92b6a29f555ce0c0b5b204`；
- RC8 激活：`8ef732b45cf3cb04262317cdfa13a176b47eebe0`；
- 2016 终局：`a03597be9a83a38ce4bcc4dba76cf8c574327045`；
- 2015 终局：`6be924e7903a201236a9cdd93ee75d66b839d1d6`；
- 原交付内容：`4c4550d92c12ffbba4f4a438fe1cbb648855a5bf`。

这些是定位锚点，不是要求当前分支回退。远端有合法增量则检查差异后继承；分叉或他人并发写入先保护工作，不自动合并。安全同步只允许 fast-forward；API 超时不能当作分支不存在。

按顺序读取：

1. `GOALS.md`、`WORKFLOW.md`、`PLANS.md`、当前活动计划、`state/project_state.json`。
2. `HANDOVER.md` 与交接资料索引；旧 TAKEOVER_ONLY/暂停研发属于历史工作范围，本轮已授权继续。
3. `evals/results/phase-004c5/FINAL_REPORT.md`。
4. 同目录 `DELIVERY_AND_RECOVERY.md`、`delivery/next_subject_neutral_cases.json`、`delivery/final_delivery_receipt.json`。
5. `qualification/accepted_decision.json`、snapshot/subject 映射和 current checker。
6. 两个新题的 `terminal/decision.json`、对应 native audit、必要事件记录与科学报告。
7. 本轮涉及的训练/评审/发布/来源政策、正式 Skill 工作流、公共 controller 与两项失败测试。

重点实现入口：

- `.agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py`
- `scripts/finalize_fresh_c_validation.py`
- `scripts/run_c_target_rc7_development_regressions.py`

不要每个角色重复读全仓库，不全文加载巨大输出表。先键名/函数/范围定位，按需展开。不要全文导出 749 文件 PR patch。

## 3. 当前事实必须原样继承

启动核验预期：Project `0.3.0-competition-rc8`，Skill `0.2.0-competition-rc8`，Python distribution `0.2.3`；这些版本维度不必相等。

本轮前的完整 CI：2151 passed / 2 failed / 1 skipped。旧候选 subject CI 2153 passed / 1 skipped，不代表当前 HEAD CI 通过。

两项明确失败：

- `tests/unit/test_competition_rc_development_eval.py::test_case_registry_declares_required_training_fields`：当前合法案例为十个，断言仍把集合总数固定为八个。
- `tests/fault_injection/test_eval_policy_faults.py::test_human_gate_and_integration_flags_remain_false`：把 `C_TARGET_VALIDATION_FAILED` 固定绑定到旧 004C4 phase，无法接受已定义的合法 004C5 终局。

2026-09-09 的远程 run `34294448658` 测试的是 PR merge commit `93a4b7794afd56af59716a1381d5cbc68bb9c126`，不是 main 已经合并，也不是单独 feature checkout 的测试。

两个 Validation：

- 2016：EVIDENCE_INSUFFICIENT，模型2、Final0，阶段11–14未接受；保留过严未来真值/分组规则、目标分母错误等异议。
- 2015：FAILED，模型2、非预测 Final1、预测test0；正式选择/比较/稳健性接受发生在Final之后，公共完成 wrapper未运行，case-owned READY不能覆盖负面终局。

15次 Development captures与额外一次Q4证书构造是不同执行类型。限定LP证书只证明其固定参数下第一目标区间，不证明企业真实未来产能、库存闭合或其他目标最优。

不要把候选准入、数值局部成立、终局审计PASS、工程CI、整题科学通过和团队合规合并为一个PASS。

## 4. 新 subject 与历史冻结的最小正确处理

本轮优先采用新的维护候选 RC9（该版本未被后续合法占用时）：

- Project：`0.3.0-competition-rc9`
- Skill：`0.2.0-competition-rc9`
- Python distribution 保持现有含义，不仅为表面一致而改版本。

先创建本轮活动计划和 proposal，记录上轮终局、需要修改的边界与新的独立预算。可以使用 004C6 或仓库已登记的等价维护 route；不要制造长串平行状态。

历史 RC8 使用旧 subject 的 Git blobs与旧 snapshot 验证。当前候选使用自己的精确文件映射、代码/规则/测试身份、环境和接受决定验证。

必须区分：

1. 修改当前工作树中的未来实现，是允许的新研发。
2. 改写已经冻结的历史对象及其哈希，是禁止的历史篡改。
3. 用旧 RC8 哈希豁免当前变更，是禁止的资格冒用。

复用现有历史兼容能力，不重建通用Schema平台。不得把所有 current-tree 校验一律改成只查历史，以隐藏当前漏洞。

新 subject 构建期间应允许合法的 candidate lifecycle，active仍指向历史RC8并不意味着不能测试候选。实现、候选资格、live激活、远程回执按有向依赖依次记录，不能要求未发布候选提前已经是active才能通过自己的检查。

保护所有既有 `phase-004c5/` 结果/终局/审计/证书原件；本轮结果使用新的 `evals/results/phase-004c6/` 或已存在等价目录。旧活动计划原文可归档到 completed/archived 并通过原提交读取，不删失。

## 5. M1：CI 的正确修复，不是改常数凑绿

先复现两项失败，读取断言原意与当前Schema/登记规则，再写新增正负例。

### 案例登记

历史八案例集合可以作为历史必须保留的锚点子集，但不是所有未来案例的闭集。

当前规则至少验证：

- case ID全局唯一、每个新旧record满足字段与合法类型；
- 历史输入/首跑/终局/答案状态的不可变投影按各自subject受保护；
- 新案例来自合法的登记/设计/冻结记录，不能任意插入一条空record；
- 新 Development child 的父案例、污染状态和证据类别明确；
- 阶段、版本、case与decision关系一致。

测试包括合法扩展、少字段、重复ID、移除历史案例、篡改历史freeze、错用case类型。

不能只把 `8` 改成 `10` 或 `>=8`；也不能删掉历史集合、skip/xfail原测试，或从待验证集合移除两道新题。

### 阶段语义

将通用不变量与历史快照要求分开；合法phase/status/version/case/decision组合按明确规则验证。保留旧004C2/004C4的原义，同时支持实际004C5和本轮合法维护转换。非法组合仍应拒绝。

不能只检查status出现在宽泛enum中，也不能接受任意phase字符串。

### 本轮完成要求

当前完整CI必须最终真实通过，旧subject也能按其历史上下文复验。初始baseline失败是本任务要修的对象，不应让Codex在preflight直接终止。

## 6. M2：修复非预测 Final 的循环前置关系

以十项中立规格中的 `NONPRED-ORDER-POSITIVE/NEGATIVE` 为起点。它们目前仅是 SPECIFICATION_ONLY_NOT_EXECUTED，不能计作已运行测试。

先在真实公共CLI/controller复现：compare/selection需要Final verification，而Final又要求compare/selection/robustness已接受，导致合法非预测任务无路可走。

最小设计原则：

- 区分开发阶段候选核验、开发比较选择、冻结选定方案、独立最终核验与最终接受。
- 开发comparison可以依赖真实的开发验证/独立复算，不应该依赖尚未发生的Final回执。
- 最终接受仍必须依赖独立Final核验，不能因拆分前置关系而省略它。
- 当前需求指定必须在Final之前完成的selection/comparison/robustness，必须有真实、当前且绑定正确的接受记录。
- 若某项稳定性检查本质上属于最终核验套件，必须在设计时声明为post-selection、不会影响已冻结选模；不能要求该套件完成后才能开始自身。

建议逻辑图（实际命令复用现有接口）：

题意/数据/实验设计 → 候选执行与开发核验 → 逐问比较/选择/必要开发稳健性接受 → selection freeze → 最终核验授权 → 写入STARTED访问事件 → 执行独立核验 → capture/seal/receipt → Final接受 → 局部/总体Claim → handoff。

必须在公共核心 enforcing，不是仅给2015写一个特例wrapper。case adapter不得构造假接受记录绕过真实入口。

提前Final必须在任何checker子进程和真实输入访问之前拒绝；保留拒绝请求但不伪称一次已执行Final。已经STARTED的失败、超时、部分输出按实际访问记录，不允许反复偷看。重复调用只能复核原不可变回执，不能重执行。

至少覆盖：先Final、改选定代码、改config、换输入、比较过期、缺稳健性、失败/部分回执、并发重复请求、两requirements不同模型、非预测无测试集、mixed任务。

过去2015的事件不能排序重写。新规则不使其旧FAILED变成PASS。

## 7. M3：合理的条件预测与防泄漏，不是全面放宽

### 7.1 从题意建立需求与科学支持强度

区分四个问题：是否具备计算一个条件预测所需输入；模型与假设是否有证据支持；是否在适当历史数据上验证；未知目标的实际误差是否已观测。

未知未来真值不能被当成预测本身必须输入。反过来，能计算数值也不能宣称准确率已证实。

预先登记：题面要求、目标量、预测时点、可见数据、适用实体、假设、评估方法、可允许的结论强度。不在结果后通过重贴标签降级要求以获PASS。

题目确实只要求条件模型估计时，允许交付有合理模型依据、适当回测或独立检查、清楚局限的条件预测；不强迫不可取得的实际未来标签。题目明确要求实测验证或精度保证时，证据不足仍必须PARTIAL/INSUFFICIENT。

保留以下区分：`COMPUTABLE_CONDITIONAL_ESTIMATE`不等于`TARGET_ACCURACY_DEMONSTRATED`；标签示意，优先映射到现有字段，避免新增状态泛滥。

### 7.2 数据划分与主张目标匹配

合法同实体时间预测允许使用预测时点前已观测历史；必须约束feature及其变换、拟合、选择的可见时间。

至少表达以下不同评估目标：

- 同实体、未来时点的条件延续；
- 新实体或新总体的外部迁移；
- 跨条件插值/外推。

对新实体迁移，保留严格实体隔离。对同实体未来预测，不只因ID重叠就拒绝，但未来标签、后时点特征、跨预测时点窗口、用全数据拟合的预处理必须拒绝。

正负例采用中立合成轨迹；使用多个切点与不同实体。不要写入“电池”“55A”或历史题号作为通用规则。

### 7.3 指标必须回答同一个问题

每个selection/validation metric绑定：目标定义、时间起点、单位、误差公式、分母、样本/实体单位、聚合、权重、方向和零分母处理。不能以变量名相似或模型排名相同视为等价。

针对剩余时间问题，中立测试中明确区分：elapsed time的相对误差、remaining time的相对误差、单终点误差与多时点平均。两者即使选到相同模型，也不能互换。

分母为零/接近零时按预登记规则报告不可定义、绝对误差或其他合法指标；不能临时加epsilon制造低误差。

区间标签分清模型离散范围、敏感性区间、bootstrap参数区间、经过覆盖率评估的预测区间。独立算术一致不代表概率校准。

## 8. 十项已登记规格的完整闭合

逐一读取并映射 `delivery/next_subject_neutral_cases.json` 的原十项ID：

1. NONPRED-ORDER-POSITIVE
2. NONPRED-ORDER-NEGATIVE
3. PREDICTIVE-RELABEL-NEGATIVE
4. TEMPORAL-SAME-ENTITY-POSITIVE
5. TEMPORAL-FUTURE-LABEL-NEGATIVE
6. TARGET-DENOMINATOR-NEGATIVE
7. REGISTRY-EXTENSION-POSITIVE
8. REGISTRY-HISTORY-NEGATIVE
9. TERMINAL-PHASE-POSITIVE-NEGATIVE
10. SUBJECT-IDENTITY-POSITIVE-NEGATIVE

先保存本轮中立测试设计，再实现。每项记录实际入口、输入变化、预期、旧实现观察、新实现观察及证据。

正例必须真正运行到对应完成节点；负例除检查reason code，还要检查实际无非法执行、无错误状态推进、无错误接受包。

至少三个真实公共入口端到端样例：

- 确定性优化：比较和稳健性先于独立Final，不存在监督test set，完整交接。
- 同实体时间预测：合法历史前缀训练、开发评估、最终协议和条件范围；篡入未来字段即拒绝。
- 混合多问：描述统计、条件预测与优化共存，逐问正确评估和聚合；某问缺证据则整体不冒充全完成。

原有P0/HF22、source/output/Run绑定、失败保留、STALE和已发布历史保护必须回归。相关中立案例变换字段名、实体数、排列与尺度后结论稳定，避免对某一个fixture硬编码。

## 9. M4：新建 Development episode，不能续跑旧 Validation

本轮显式允许在核心修复中立验证通过后，使用2016/2015的合法原始输入创建新的Development子案例。这样既能真实验证通用改动，又不消耗新盲测题。

旧两题的终局目录、Run/Final账本、candidate代码、答案访问状态与0/2分母全部不变。禁止在原case root执行任何会写入的数值命令。

建议子案例ID（若已存在，不覆盖，按登记规则生成新attempt）：

- `CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-004C6-001`
- `CUMCM-2015-C-POSTVALIDATION-DEVELOPMENT-004C6-002`

每个子案例记录：父Validation ID与terminal hash、已知题目/结果、`DEVELOPMENT_AFTER_VALIDATION`、独立工作区、新代码/预算/Run ID。答案继续不访问；“答案未打开”不使其重新成为未知题。

在新结果前冻结：两题选择、同一共享候选、输入与题内代码、指标、数据切分、算法预算、模型变化范围、Final模式及计数。

默认每题最多4次新的模型CLI启动、独立数值checker最多4次、最终核验最多1次；补充模型实验占用模型启动预算，不藏进“审计”规避预算。预先规划的同一次数值程序内部可包含有限CV或敏感性套件，规模需要声明。终局失败后不追加Final；达限如实保存。

每题必须至少有一次真正拟合/求解、一次独立结果核验，不能只复制原JSON改版本。

### 2016 Development

根据实际题面拆解问题；修复后使用题意一致的目标、分母和可见时间。可以复用已有合理模型作为基线，不为追求新颖强换模型。

比较“固定旧输出按正确指标只读复算”与“新合法开发运行”，二者单列。新切分因为已知题目仍是开发证据，不写为重新获得盲性。明确条件预测值、可验证历史误差、未知未来误差及区间性质。

### 2015 Development

优先复用已有可复算数值模型，在新的实际公共完成入口验证无环流程。不要重写星历系统或把科学服务的理论计算数据称实测。

必须从候选开发到comparison/selection/robustness接受，再进入一次非预测Final核验，最后Claim/handoff。展示真实事件序列、父子哈希、选定代码/参数与Final输出；仅有case-owned READY不算完成。

保留窄时间窗口的物理假设和敏感性，不用机器精度掩盖折射、天气、地形等未建模因素。当前任务是否全题完成按题面和预先scope审查，不自动要求实地观测，也不假装已获得实地观测。

两个Development使用同一冻结共享候选；首轮完成前不修改通用Skill。若发现新通用blocker，先冻结两题当前结果，再进行最多一次明确的新候选修订与必要开发回归。不要反复“一题一版本”。

## 10. 三种审核必须分清

沿用主编排器、实现/实验角色、只读审核。最多两个并发执行单元；公共state、Git、共享代码由主编排器串行写。

至少实施：

1. 自动测试/实际controller黑盒；
2. 独立程序的算术、目标、可行性复算；
3. 真实原生只读审查：一次检查协议/泄漏/误拒绝，一次检查新开发结果与结论范围。

可以同一审查角色分阶段使用，不增加审计层数。审查者使用受限证据包，先给独立判断再看开发者自述；记录实际调用、输入输出hash、可见模型身份与未知项。不暴露私人链路或凭据，不把主Agent自审写成独立Agent。

没有相关原生能力时明示NOT_RUN，只完成已授权的其他部分，不伪造通过；对应资格不得冒充已审查。

重大异议必须定位证据、可复现输入或数学论证。可程序化者执行测试；不能机械化的专业异议仍需保留并约束结论，不因“没有单测”就忽略。

Audit对负面判定的PASS不等于题目PASS。审计器自身可能误判CSV顺序或指标口径，应按稳定身份键独立核验并保留原误判及更正记录。

## 11. M5：候选资格、CI与发布收敛

本輪不是必须发新版。核心修改与回归通过时，才按现有研究资格机制接受并激活RC9；否则保存candidate及明确阻断，历史RC8身份不回滚或篡改。

顺序：

- 当前新规则和候选代码一致 → 提交共享subject；
- 该subject完整CI、独立审查与中立/开发证据通过；
- 保存接受决定，激活当前资格（限研究/开发/未来Validation）；
- activation与新增child registry/state也必须经当前测试；
- 最终content commit再跑完整CI；
- 普通push核验远端HEAD和实际CI；交付回执在后继提交或PR评论中记录已知事实。

在候选测试中提前模拟“增加合法案例、进入合法终局”场景，避免冻结完又因新registry记录使CI失败。旧phase绝不能要求所有未来终局都回到它自己。

RC9身份必须覆盖实际运行会调用的Skill、controller、相关规则/contract及测试；不能只hash SKILL.md。集合应由执行依赖确定，不为了减少漂移任意删掉核心路径；也不把每份生成报告都放进共享实现冻结。

历史subject解析不绕过当前检查。当前失败不能用15项补查/strict或旧subject成功覆盖。

完整CI不重复与独立full pytest先后执行；优先局部测试，候选与最终交付各在必要点跑一次sole CI。遵守已核实完整交付规则。

不能以“修了两条旧测试所以已经全题成功”总结。当前工程、两个开发题、旧Validation和比赛合规分别记录。

## 12. 时间、额度和继续执行

这是约5–7小时有效工作量的计划，不是保证运行时长的定时器。

建议时间分配：

- 0–0.4h：继承和新任务范围；
- 0.4–1.2h：两项CI与subject/lifecycle最小修复；
- 1.2–3h：无环Final、时间任务与指标绑定、实际正负例；
- 3–5.5h：两个新Development实际运行、独立复算及审核；
- 5.5–7h：必要修订、候选资格、完整CI及交付。

前2.5小时检查是否在元治理上过度耗时；已有机制够用时立即回到实际科学任务。预计不能全部完成时，保留最关键事实，不虚报进度。

连续推进，不在每一小步请求确认。每30–45分钟更新一份短checkpoint，包括完成事实、未解决blocker、版本身份、预算与下一安全操作，然后继续。

同根因最多三个有实质不同方案的修复循环；不能靠更换reason code或扩大白名单算新方案。全局最多两次功能候选修订，后续仅必要测试/文档收口，若必须再改shared则如实停止候选接受。

额度方面：上轮4,977,634 tokens只是观察，不是本轮默认可用额度、计费或必须花完的预算。不自行移除已设置Goal/token限制。记录同口径可见的本轮新增input/cached/output/总量；不可见写UNKNOWN，不估算金额。主流程不重复全文读报告、巨大JSON或49万行PR。最多两个并发单元，反馈摘要优先。

不因为“尚未满五小时”空转，也不因为“已提交CI修复”在仍有明确可执行的M2–M5时提前结束。合法任务全部完成可以提前收口；达到预算/平台/权限边界则保存恢复点，不能规避限制。

局部阻断后的替代任务仅限本轮相关：中立反例、旧终局只读重算、新开发可执行性、命令与恢复说明、依赖可复现性盘点；不得用旁支文档完成替代原目标完成。

## 13. Git交付与文档

继续现有PR #12，不先合并有已知失败的PR，也不创建并行工作树。无自动Ready/merge/main push授权。

采用少量有意义的里程碑提交，建议6–10个（不是为了凑数量）：启动与测试预期、核心修复、定向回归、新开发冻结/结果、资格与当前CI、最终报告。不要为了保存每条日志制造数十次重复提交和全CI。

每次明确暂存相关路径；检查diff及隐私；普通push后读取实时远端SHA。网络错误不能当作分支不存在，最多三次退避；状态变更重试前核对是否已成功。

不上传原题、原始附件、答案、缓存、凭据、未清权正文；原始数据按来源/哈希在ignored区域使用。不要全局改变CRLF规则或格式化旧冻结CSV来通过检查。

至少维护：当前Plan、GOALS/WORKFLOW/PLANS的必要增量、Skill版本与工作流、registry/state、自动派生current_state、Runbook与handover当前入口。旧报告原件保持，追加当前说明，不重写旧FAIL。

本轮输出可以精简为：

- 新计划；
- 中立反例与验证证据矩阵；
- 两个Development子案例各自结果和独立审核；
- 新candidate身份/qualification及当前CI；
- 一份综合REPORT、一份恢复入口、一份delivery receipt。

不为每个小命题新增单独Schema或几十份重复报告。

## 14. 本轮验收与最终回复

最终返回：

1. 本轮状态：工程闭合/部分闭合/阻断，不自动写科学通过。
2. 起止时间、墙钟、平台计时、可见tokens及未知计费。
3. 分支、起止HEAD、候选subject、旧RC8身份保护。
4. 两项原CI失败的根因、修改及正负例；最终完整CI实际结果。
5. 十项中立规格逐项：旧观察/新结果/真实入口/测试与证据。
6. 无环Final顺序的实际trace，提前请求是否在执行前拒绝。
7. 条件预测、同实体隔离、目标分母规则与反例，仍不能证明的能力。
8. 三个中立公共E2E结果，不把synthetic当历史题。
9. 两个新Development子案例：父案例、Run/Final数、数据/指标、独立复算、有效问题覆盖、限制、完整或部分交接。
10. 原2016/2015 Validation仍为0/2、未改终局；本轮新增独立Validation=0。
11. 原生审查、程序复算、主编排器自检分别列出；人工合规NOT_RUN时保留。
12. 是否真正修改通用工作方法、数据/实验决策；不能只统计检查器数。
13. 新candidate资格是否接受、当前live身份、研究/比赛界限。
14. 本地完整CI、远端PR merge-tree CI和feature HEAD检查分别标注。
15. PR状态、普通push、远端SHA、工作区及剩余问题。
16. 最多三个下一步建议，不能直接启动下一轮或消耗保留题。

最终最低交付要求：无伪造、无历史篡改、准确负面结果、可继续的恢复入口。理想目标：当前完整CI通过、十项反例闭合、公共路径可用、两道开发问题在合理条件范围内获得实质改善。

未达到理想目标不要求强制成功，也不能只因时间到就把未完成任务从清单删除。

## 15. 已核对的来源索引

以下均属于起始HEAD下的仓库证据，不是新实验：

- PR #12 metadata及正文；
- `evals/results/phase-004c5/FINAL_REPORT.md`；
- `evals/results/phase-004c5/DELIVERY_AND_RECOVERY.md`；
- `evals/results/phase-004c5/delivery/next_subject_neutral_cases.json`；
- `evals/results/phase-004c5/delivery/final_delivery_receipt.json`；
- `evals/results/phase-004c5/qualification/accepted_decision.json`；
- 两题各自 `terminal/decision.json` 及其引用的原生审计；
- `state/project_state.json`；
- Actions run `34294448658` / job `102287899557` 的实际日志。

报告中的推测性根因需要实际测试证实后才能成为新修复决定。本任务书提出的新设计、预算、candidate命名和Development授权是本轮方案，不得倒写为历史事实。
