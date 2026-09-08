# PR #12 RC8 原生独立审查 02（非候选接受意见）

**本轮冻结结论（截至 703775b）：在本次已审事实绑定、checker 调用链与已明确限定的科学声明范围内，没有由本次证据确立且仍开放的 release BLOCKER。下文 B01/B02/T01 保留原始发现，其针对性修复与复验见末尾附录。此结论不是整个 PR、RC8 候选或 release 的接受意见；主编排器后续 Development empty-test design、RC8 profile 与最终 subject 不在此冻结意见内。**

角色：adversarial_evidence_auditor。审查范围为事实绑定、Development 实际路由、runtime/controller、2021/2022 v6 现有科学回执。本审查不写正式状态、不执行 Git 写操作、不运行官方完整模型、不访问新题、答案或 vault；探针与本报告写本 ignored 目录；后续经主编排器明确授权的唯一 replay 目录见末尾附录。

## Subject 与证据链

- 最初 subject：`ff2f7ba2cd1b9a8995d4f65b9936855b6cbb00e1`。第一组实际探针运行时 HEAD 已为 `e55f470228fa5ebb2eaa625ce0000b6bf4a34755`；26 个冻结读取文件均与初始字节相同，见 `input_manifest.json`、`inputs/`、`drift_check_after_probes.json`。
- 修复后复验 subject：`57661f3b5caaafd6ecf2f5c15fefa8e140aefd7c`。完整读取快照与 SHA256 见 `post_subject_manifest.json` 和 `subjects/57661f3b5caaafd6ecf2f5c15fefa8e140aefd7c/`。
- 初始 core SHA256：`8ba9d1dda8f49771ea14efc2ba8127abf0418763cfca325856e24ae359da7020`；57661f3 core：`a8401b5f82710c7d783e58b606c3ba50c28197cadab8af9bbae0b926ec9624af`。
- controller SHA256：`fb00a12f89514c79b539fa28a423dd694b2e4847fca574bbcdd23fb25e16844f`；Development route SHA256：`f6e6ff8c044679f9042876b1838b6ea39c46d0624ec20190d12e9e38a6a87f22`。
- 六个 v6 Run 的 output/checker 和两份 selection semantic 文件读取 hash、逐项事实对照在 `science_output_comparison.json`。其中数字来自既有回执的独立对照，本轮没有重新从官方 raw 求解或重跑 checker。

## Findings

### B01 — BLOCKER（原 subject 已复现；57661f3 同一攻击已关闭）

位置：初始 core `verify_scientific_check` 4935–4978；controller 非预测 Final 分支调用此函数。

原 verifier 仅检查 SUCCESS、Run、代码及文件 hash，未要求原生 checker 捕获的完整 schema、exit、时序、日志、Final access 等事实。构造一个完全未执行 checker 的最小 JSON ledger，并用 `irrelevant_identity = 1` 当残差，即得到实际 controller exit 0、10 gates PASS、`READY_FOR_PAPER_HANDOFF`、`scientific_final_verification_count=1`。另一组真实执行后改成 exit_code=23、final_test_access=true，仍得到同样接受。

证据：`probes/forged_unexecuted_checker/`、`probes/contradictory_exit_code/`。每目录保留 case 输入、命令、stdout/stderr、exitcode 和 observation；汇总为 `probe_observations.json`。合法真实 checker 控制组通过，missing checker 负例阻断。

57661f3 复验：`post57661f3/probe_observations.json` 中合法原生 checker 仍通过，missing、minimal-forged、contradictory-exit 三组全部 exit 1，在语义 gate 因 `RC_FEASIBILITY_INDEPENDENT_RECALC_MISSING` 阻断。这里只确认原攻击的局部修复，不代表所有 provenance 威胁已排除。

最小建议：保留原四组正负探针；新 schema 对历史已有回执的升级应明确是否要求重新捕获，不以补字段假装历史执行。

### B02 — BLOCKER（57661f3 仍开放；缺失/失败核验被 Development 与 semantic CLI 忽略）

位置：`scripts/run_c_target_rc7_development_regressions.py:688` 到 `:741`；core `_scientific_claim_facts:1254` 到 `:1393`。实际 builder 吞掉 verifier 异常；仅 FEASIBILITY/OPTIMALITY 将独立核验作为必要条件。DESCRIPTIVE 与 SIMULATION_CONDITIONAL 虽有 `scientific_facts_required=true`，仍可仅凭 producer 自报的 facts 与 metrics 得到 SUPPORTED。

实际可复现：用仓库既有、Git 绑定的 neutral fixture 构建两组临时 case，冻结注册 checker。缺 checker 时两个 requirement 均 SUPPORTED；真实 `verify-evidence` 运行 checker 后因 fixture 缺 quantity 而失败（CLI exit 3，capture FAILED），实际 builder 仍两项 SUPPORTED，真实 `semantic-check` exit 0/PASS，且没有 reason code。描述与条件模拟两类均成立。该失败来自刻意不匹配的中立 fixture，用于证明核验失败被忽略，不是声称官方两题出现这种数值错误。

证据：`development_probes_r2/descriptive/observation.json`、`development_probes_r3/simulation_conditional/observation.json`；各目录保存实际命令/stdout/stderr 与 builder JSON。另有显式函数级注入：让 verifier 返回 feasible=false、失败残差、metric_a/metric_b=999、mismatch_count=2，真实 builder 仍 SUPPORTED；此部分只证明消费逻辑，**不是**真实独立 checker 执行，见 `negative_verifier_injection_builder.json`。

最小建议：Development 每条 claim 必须有成功核验；通用 runtime 至少对显式要求 scientific facts 的 requirement 强制执行。逐项绑定 claim 对应 requirement 的独立 metric_values，拒绝缺 key、非数、差异；不要默认用另一 requirement 的同名 root metric 借证。若保留 root fallback，应要求其来源映射与 req 所属关系明确。FEAS/OPT 再追加领域约束/证书判定。

数值一致性与科学目标达成必须分开：2021 Q2/Q3 EFFECT 原文在报告历史压力及失败，所以 checker feasible=false 本身不构成否定“观察到失败”声明的证据；相反，checker 算得数值与 claim 不同、或 checker 根本失败，应阻断该声明。2022 顶层 `scientific_metric_binding_mismatch_count`（checker:704–717）目前不改变 requirements.feasible，也没有被 core 消费，应避免这个漏项。

### T01 — 明确的信任边界（完整伪造回执仍可接受；不能称作 OS 证明）

位置：57661f3 core `verify_scientific_check:4935`；controller 的非预测 Final verification 使用回执验证，没有当场重新执行 checker。

在新的 synthetic case 中不执行任何 checker，借用真实控制组的完整 v2 schema 和空日志，重算所有文件 hash、合法时间/env/argv/commit，并放入 irrelevant_identity 残差，实际 controller 仍 exit 0/READY_FOR_PAPER_HANDOFF。证据：`full_ledger_boundary_probe/observation.json` 与同目录全部输入、命令、stdout/stderr。

这说明内部一致的 JSON 及 hash 不能认证“谁运行过什么”。本探针假定同权限可写 case，未证明 OS sandbox 逃逸，也不能据此宣称现有 v6 科学回执伪造。若产品要在此威胁模型下证明当次重新计算，应在可信 controller 中直接执行已冻结 checker 到独立临时目标、立即验证并消费结果，或依靠明确的外部不可改捕获机制；不能仅追加更多自报字段。即使重新执行，数学充分性仍取决于 checker 真正重算了什么，单独进程并不构成独立科学论证。

## 科学覆盖与保留缺口

| 范围 | 可核验的当前证据 | 尚未证明的内容与最小建议 |
|---|---|---|
| 2021 Q1 | checker 从 W001–168 自行派生四因素/供货参数，复算排名与权重扰动；所选 top50=50，最差交集48 | 条件权重排名不证明普适重要性；保留权重/时间范围，避免同类权重扫描替代采购目标求解。 |
| 2021 Q2 最少供应商 | 所选实际34，独立乐观容量下界34；checker 还复核该方案运输/产量/库存约束及 supplied-volume 成本。证明只在登记容量情景、初始库存与稳态假设内成立 | 399候选池、历史168个实际使用和 v6 条件最小34是不同量。全局/现实最少仍需声明完整假设。采购与运输 lexicographic 阶段的最优值没有独立对偶证书，不能因可行证书称全部目标最优。 |
| 2021 Q2/Q3 效果 | 复算每周全部供货采购成本、库存、运输容量压力；所选 Q2/Q3 48个历史周均有 carrier violation；inventory violation 分别28、9 | 压力失败应保留为负面科学结果；不应将“正确复算出失败”改成“目标通过”。补目标方案需更改 case-owned 库存/采购/运输方案，重复同一压力测试无增益。 |
| 2021 Q3 | 所选148个供应商，Q3 A供货7411.367614071917、C供货6535.982308075016；名义方案及成本复算存在 | checker 对 MATERIAL-PREFERENCE 复用计划可行性记录（:638），没有独立验证 C-min/A-max 的词典序最优性。最小补证是对应阶段 primal/dual 界与先前目标锁定残差；不能把 material mix 数值当最优证明。 |
| 2021 Q4、附件 | 所选产能29388.566659002314，较28200增加1188.5666590023138；独立核验是可行条件计划，Q4明确无独立最优证书；6张派生计划表得到数值核对 | 原生 A/B 模板未交付、最大产能未独立证明；whole complete=false 正确保留。上述科学未完成不自动否定通用软件修复。 |
| 2022 Q1 | 69样本/67有效；2个配对 artifact；3张关联表、共2997次置换、分层中心与27个条件 backcast 得到独立复算 | 2配对不足以识别风化因果效应；交换性假设下回推不能表述为恢复真实原始成分。 |
| 2022 Q2 | 56个有效 artifact；当前CV仅44个train+validation组，2 repeats=88预测，内部test overlap=0；所选56 artifact分5簇；真实扰动最小特征变化1.298520473929392 | checker 检查CV成员/重复次数，不重拟合分类器；检查簇成员/化学中心/计数，不重新聚类；bootstrap重算采样覆盖与比值，未重算same-cluster判定。20次请求数与非零扰动是诊断事实，不能等价于分类/聚类科学有效性。旧全56组五次CV包含历史暴露test，重复该CV不能恢复独立验证价值。 |
| 2022 Q3 | 8未知预测、0可用真实标签；所选7在训练距离域，报告的扰动score导出flip均值0；checker重新算距离和扰动特征变化 | flip是从producer报告的分数计数，未重新评估分类score函数；不是已校准概率，也不是未知准确率。REQ3A/EVIDENCE仍INSUFFICIENT，不应被共识或过程SUCCESS升级。 |
| 2022 Q4 | artifact等权 CLR Spearman 与30 bootstrap、91化学组分对区间得到独立复算 | 范围为有限集合的探索性关联，30 bootstrap不足以稳健估计尾部分位，不含多重比较校正或因果识别。明确范围可支持描述性结果，无须伪造整体完成。 |

2022 六类主要统计复算的实现范围说明与实际代码一致（checker 文件头、:398–435、:438–535、:537–620）；三个 Run 的 scientific metric mismatch count 都为0。2021 checker root metric_values 来源于自身 recompute_stress/plan 与各 req scoped metrics（:694–719），未发现从 producer 总分直接 fallback 的路径；其对 producer 总分另给一致性布尔值，目前同样需要明确消费。

## 执行记录与限制

- 主脚本：`run_probes.py`、`run_probes_post57661f3.py`、`run_development_probes.py`、`run_development_conditional_probe.py`、`run_full_ledger_boundary_probe.py`。所有 CLI 均使用既有 `.venv/bin/python`，每个 probe 的 `*.command.json` 记录 argv、cwd、exitcode、开始时间和耗时，`*.stdout`/`*.stderr` 保留实际输出。
- 探针开发中一次解包 builder 返回值错误（selection/semantic顺序）导致外层 exit1；一次 SIM fixture 的 empirical requirement 未改为允许 simulation 被原 gate 正确拒绝。保留 `development_probes/` 和 `development_probes_r2/simulation_conditional/`，随后 r2描述组及 r3条件组完成。没有把这两次探针装配失败计作生产漏洞。
- 无新安装、无依赖或全局配置改动。没有修改公共代码、Skill、正式结果或 state。部分临时 synthetic 执行依赖当前 Git blob；未来代码变更会让旧case产生正常STALE，复验应重建新后缀目录，不能覆盖已保存证据。
- 本意见只针对已读取字节及明确执行的探针；不做 PR/release 接受宣告、不按票数判科学成立。后续修复 subject 需要针对开放 findings 独立复验。

## 703775b 独立复验附录（本轮最后 subject）

Subject：`703775b99fe4c3a260965e653eaa72b36b59f6d6`；core SHA256：`ffd8273e4d8a2b798b19ef847d66dd1261501783a0da6e4aad9d75ff4dcda04f`。本 subject 实际读取 hash 和源文件快照见 `final_subject_manifest.json`、`subjects/703775b99fe4c3a260965e653eaa72b36b59f6d6/`。本轮没有审阅其后的实现。

| 实际测试 | 703775b 观察 | 证据 |
|---|---|---|
| 原四组 ledger/controller | 真 checker 正例 exit0/handoff；missing、minimal-forged、exit23/finaltrue 均 exit1/semantic BLOCK | `post703775b/probe_observations.json` |
| 完整错误 ledger、无前置 checker 执行 | controller 真的执行 checker，完整重算结果不相等，exit1 BLOCK | `full_ledger_boundary_probe_post703775b/` |
| 完整自造 ledger，算术结果恰好正确 | 前置未调用 checker；controller 实际重新计算且结果一致后 exit0/handoff | `equivalent_full_ledger_post703775b/` |
| DESCRIPTIVE、SIMULATION_CONDITIONAL 缺/失败 checker | 两组均 INSUFFICIENT；实际 semantic CLI exit3/BLOCK | `development_probes_post703775b/` |
| 分离计算一致性和领域成败 | verifier 返回值的明确函数注入：domain=false、计算残差通过且指标相等时支持；metric不符、缺metric、计算残差失败、缺计算残差全部拒绝；2类×5种共10组 | `calculation_vs_domain_post703775b.json`、同名 command/stdout/stderr，输入脚本 `check_calculation_vs_domain.py` |

最后一行是对实际 builder 的函数级输入检验，不冒充独立 checker 进程。完整错误 ledger 目录原 observation 的旧字段 `actual_checker_executed=false` 由复用脚本固定填写，仅指**探针在调用 controller 前未执行 checker**；703775b controller 内部实际执行 checker 的事实以 `native_replay_index.json` 所列原生 execution.json 为准。相应更明确字段已经用于等价结果控制组。

主编排器在本轮明确扩展权限，允许本审查调用的 core 在 `.cache/scientific-check-replays/` 下用 mkdtemp 写唯一临时目录，仅留 actual checker replay 派生回执，未增加公共 state/Git 写权限。本审查实际产生的目录及每文件 SHA256 全在 `native_replay_index.json`：

- `RUN-CAND-20260906-tcn00oue`：真实控制组，PASS。
- `RUN-CAND-20260906-fevzjf0p`、`RUN-CAND-20260906-1m6loswn`：同一完整错误 ledger 的两条 requirement，checker process exit0，但结果比较失败。
- `RUN-CAND-20260906-jlnsqn88`：完整等价结果控制组，实际重新计算后 PASS。

原始回执、命令和进程日志均保留，没有用新结果覆盖旧 Run。原始 B01 在57661f3的格式/矛盾字段攻击被关闭；T01 的错误完整结果在703775b通过实际执行关闭；B02 的缺失/失败核验和计算残差消费缺口在703775b的已测试路径被关闭。仍不宣称文件权限隔离或进程分离自动证明数学正确。

703775b 科学残差实现审查：

- core `scientific_metric_binding_codes:1422` 要求对应 req 的非空 `recalculation_residuals` 全通过，再用该 req 自己的 metric_values 逐项绑定；没有 root fallback。Development 对所有 claim 调用它；runtime 对显式 scientific_facts_required 的需求调用。历史未声明该要求的合法临时接口仍是保留路径，不应据此宣称所有历史运行都接受了同样的独立复算。
- 2022 `check_record:63` 保留实际计算残差，只排除未知准确率缺失两项领域目标条件。中心与 backcast 的全向量误差、置换误差、关联/区间误差因此进入计算一致性检查；原先“数量仍正确但具体数值错误”的绕过点已经有对应阻断条件。REQ-EVIDENCE 排除后计算残差为空，仍会不足，符合其保留的负面状态。
- 2021 checker:702–740 从参数误差、报告成本/损失误差、逐周历史压力完整公共字段差异构造计算一致性残差，另保留名义计划/历史压力的领域可行性。这样正确复算的历史失败不会被误当计算错误。Q1/表格继续用实际数值核验残差。先前报告的独立最优证书缺口及模板不足没有被这项软件修复消除。
- 独立 fit、聚类 bootstrap 同簇判定、概率校准、未知样本准确率和因果识别的范围限制继续存在；本次代码没有悄悄增加这些科学证明。将它们保持为局限或未完成，和当前 bounded 声明范围相容。

可后续改进：本次完整错误 ledger 对同一绑定发生两次失败 replay；可把同一请求内、同一完整 hash 的失败也缓存，减少昂贵 checker 的重复失败执行。此项为成本改进，非本次 release BLOCKER。

完整证据入口为 `evidence_index.json`（角色、各 subject、原生命令索引、输入快照/报告/观察/日志的 SHA256）。本报告冻结后不随主编排器下一轮开发静默更新。
