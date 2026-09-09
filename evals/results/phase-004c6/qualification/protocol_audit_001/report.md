# PR12 / Phase004C6 独立公共协议审查

verdict: **FAIL**；subject: `bcf498907cbf282e2c79580ea56b043fc1a7b52b`。

本判断仅针对该冻结公共实现满足 RC9 M2/M3/M8 的能力，不改写历史 Validation 结论，不是新候选或项目技术接受。审查没有读取主 Agent 修复自述、同行输出、历史 case 数学结果文件、答案、原题或真实 raw 输入；不联网、不安装、不调用 API、不 spawn。根 state/active plan 依规定作为治理上下文读取，其中含历史状态摘要；这些不是本报告技术判断依据。全部可执行技术输入从 subject 用 `git show` 导出。原生模型、reasoning、token、货币成本细项为 UNKNOWN。

## 独立发现

### PA-001 — 非预测开发比较要求未来的核验计数，而自声明计数足以通过（BLOCKER）

证据：`cumcm_case.py:2988–3000`、`finalize_fresh_c_validation.py:336–343`；原件均位于 `subject/.agents/skills/cumcm-modeling-evidence/scripts/` 或 `subject/scripts/`。

实际公共 CLI：`nonpred_honest_count_zero.stdout` 返回 exit 3 / `RC_NONPREDICTIVE_FINAL_VERIFICATION_INVALID`；`nonpred_claimed_count_one.stdout` 返回 exit 0 / `RC_LEAKAGE_SAFE_COMPARISON_VALID`。两次使用同一已完成真实 subprocess 捕获并封存的合成非预测 case，三个 split 为空；没有 scientific checker capture、Final ledger 或 Final 运行。两次差异只有 `test_access.scientific_verification_count` 从 0 改为 1，完整 argv、前后文件 SHA 和 stdout/stderr 在 `execution_receipts.json`。CLI 不推进 state，也不产生 handoff；这里证明的是 comparison Gate 接受了不存在的事实，并非伪造出完整 handoff。

控制器进一步在最终核验前构造该 count=1 的 comparison（336），执行科学核验（669），然后才落盘 `selection_before_test_access`、comparison 和 robustness（728–757）。最终核验没有独立 STARTED/FAILED/SEALED 一次性事务协议；此部分是静态顺序发现，本轮没有执行完整非预测 controller 的并发/超时攻击。

修复要求：开发比较依赖真实开发核验；在真实已接受 comparison/逐问 selection/预声明开发 robustness 及 selection freeze 后授权 Final。Final 单独绑定全部所选 run/code/input/config、predecessor hashes 和顺序事件，提前请求在 checker 前拒绝；STARTED 后失败保留且预算已消耗；重复调用只复核原不可变回执。不能靠调用方手填 count，也不能把未发生的核验计数填成 1 解锁开发阶段。

### PA-002 — 实体重叠误拒绝，时间可见性仍是调用方 bool（BLOCKER）

证据：`cumcm_case.py:2930–2970`；`finalize_fresh_c_validation.py:327–335`；Development adapter 同样在 `run_c_target_rc7_development_regressions.py:1119–1126` 固定 leakage bool。

实际公共 CLI：`future_visibility_declared.stdout` 为 exit 0 / PASS；该预登记合成 plan 明示 `SAME_ENTITY_FUTURE`、forecast origins [2,5]、两个实体，以及 features/labels/fit/preprocessing 的最大可见时间均为 9，冻结后两个合成 producer 成功执行。核心未消费此 visibility contract，controller 仍构造 future_information=False/time_order_valid=True。随后在同 case 的比较副本中诚实标记 group_overlap=True，`same_entity_overlap.stdout` 为 exit 3 / `RC_COMPARISON_LEAKAGE:group_overlap`。

精确边界：新 visibility 字段是本审查提出的合成协议声明，旧实现没有承诺支持这一字段；实测证明声明不受验证、group bool 一刀切。合成 producer 不实际用这些时间列，故本报告不声称已经重现模型读取未来数据或完整科学错误接受。公开代码静态检查支持“缺少时间可见性事实 enforcing”的结论。

修复要求：首先冻结评估目标（同实体未来、新实体迁移、跨条件插值/外推）和 sample/forecast origin 身份，再核对 feature、label、transform fit、model fit、selection 与窗口的可见时间。合法同实体前缀可重复实体 ID；新实体迁移必须实体隔离。至少以多个实体/切点执行真实轨迹正例及未来 label、后时点 feature、跨切点窗口、全数据预处理负例，并检查没有非法执行或状态推进。身份重叠本身不能替代这些时间约束。

### PA-003 — metric freeze 只有名称/方向/排名规则，没有目标和误差语义（BLOCKER）

证据：`cumcm_case.py:3076–3084,4781–4789`；`metric_semantics.json`。

实际公共核心纯函数探针：将合成 plan 的 metric_definition 从 elapsed time / process_start / elapsed denominator 改为 remaining time / forecast_cut / remaining denominator，`trusted_freezes(case)` 两次全部返回相同 hash；metric hash 为 `da0e78e13f0c1073a001feb7afcc03749904465852566769624bab190a87c488`。数值反例：真实终点100、估计101、当前时点99；终点相对误差为0.01，剩余时间相对误差为1.0。二者可能产生相同模型排序，却不能交换误差解释。

精确边界：此操作仅检验 freeze 函数，在合成目录中修改 plan 后立即恢复，没有产生新 Run 或绕过 state；完整 plan artifact 的 evidence hash / STALE 机制仍能发现已接受 plan 内容变化，不能据此声称存在已执行 Run 的无痕篡改。风险在于冻结模型选择协议本身没有足够语义，也不会因为 arbitrary JSON 被哈希就自动验证公式正确。

修复要求：每项 metric 冻结 target definition、origin、unit、公式/分母、sample/entity unit、aggregation、weights、direction、零/近零分母规则，Run 输出及独立 checker 精确回绑。增加尺度/排列/实体数变化的中立反例。禁止临时 epsilon；undefined、绝对误差或其它量必须依预登记规则使用。误差量相似或排名一致不是等价证明。

## 保留的正向控制

冻结 `test_p0_01_finalization_hf22_reproduction.py` 两个测试函数已经实际调用导出的公共 controller：无 Final payload 的诚实 Development 输出在 Finalization 拒绝；HF22 自证 held-out predicate 在 semantic Gate 拒绝。两项断言均 PASS，stdout/stderr、argv、时间和 SHA 见 `p0_regression_receipt.json`。它们证明已有防伪边界应保持，不表示新 M2/M3 要求满足。

Fixture 准备只覆盖 `current_git_commit()` 的返回值为 subject，确保 real code blobs 绑定冻结 subject；所有执行 CLI、Git blob validator 和产物验证代码字节未修改。没有 patch 目标实现，没有执行 full CI。

## 科学解释与回归边界

条件预测可计算、模型/假设有依据、历史评估成立、未知目标实际误差已观测，是四个不同命题。未知未来标签不应成为计算条件估计的必需输入；也不能把数值可计算写成已证明准确率。现有 `SIMULATION_CONDITIONAL` 可允许 generation_method=PREDICTION，并绑定 assumptions；修复需要在模型运行前由题意冻结所需科学支持强度，不能在观察结果后改 Claim 类型求通过。题目确需实测精度时缺证据仍为 PARTIAL/INSUFFICIENT。

混合多问必须逐问选择合法评价路径；某问条件估计、另一问经验精度或优化可行性不能互相代偿。模型离散范围、敏感性区间、bootstrap 参数区间及预测覆盖区间必须分别命名；独立算术一致不能证明概率校准。以上是原则性审查建议，本轮未声称执行三个完整 E2E 新正例，也未将未执行用例计入 PASS。

## 证据和局限

`export_receipt.json` 登记技术输入；`execution_receipts.json` 登记四个 public CLI 调用及合成 case 前后 SHA；`p0_regression_receipt.json` 登记继承测试；真实 producer `execution_capture.json` 保留各自实际 argv/time/exit/stdout/stderr/output/code/input hash；`metric_semantics.json` 保存算术反例。`evidence_index.json` 记录本目录证据 SHA，`audit.json` 适配冻结 native subagent Schema。

只有本 ignored 目录存在审查写入，没有修改 Git、正式 state、decision 或共享源文件；不据 Agent 意见投票。所有 blocker 仍需 main 注册到正式测试/decision 账本；本地审查索引不替代正式接受程序。安装系统包/语言包/工具链均为0，配置变动0。
