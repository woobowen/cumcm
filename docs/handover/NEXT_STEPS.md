# 后续研发任务卡

这些任务是从 RC7 证据提炼的建议，不是已实施 RC8，也不是要求机械执行旧大提示词。每项都应在新的
功能分支和新计划中重新冻结 scope/acceptance；不得修改 2017 C frozen case、terminal decision、Run、
output 或 challenge。默认先做最小可证伪工作，不把“新增几十个 Gate、跑多道题”作为第一步。

## P0：恢复真实完成链

### P0-01 — 定位调用路径并建立最小黑盒复现（首项任务）

- 现象：2017 C 的 actual controller 通过 Gates 1–8，在 `GATE_FINALIZATION` 以
  `RC_GATE_EXECUTION_FAILED` 阻断；同一 episode 另有 HF22 semantic false declaration。
- 影响：尚不清楚最小修复应落在 execution output contract、final/test authorization boundary、
  controller orchestration 还是 semantic validator 的哪一层；直接改大框架会放大风险。
- 来源证据：
  [`controller_outcome.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/controller_outcome.json)、
  [`HF22 challenge`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/challenges/HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json)、
  [`phase004c4_acceptance.md`](../../reports/phase004c4_acceptance.md)。
- 代码入口：[`scripts/finalize_fresh_c_validation.py`](../../scripts/finalize_fresh_c_validation.py)
  的 `complete()`/`GATE_FINALIZATION`；formal runner 的 `execute`、runtime finalization 和 semantic
  validators；2017 builder 只作为 frozen root-cause evidence。
- 相关测试：`tests/unit/test_fresh_completion_controller.py`、
  `tests/integration/test_actual_controller_{black_box,neutral_e2e,adversarial}.py`。
- 最小复现：先用现有 project-original temporary case fixture 重现“selection Run output 没有合法 final
  payload → Gate 9 BLOCK”；再构造一个 authoritative output 为 development-only、semantic predicate
  声称 held-out-valid 的 fixture，观察现有 Gate 错误 PASS。禁止读取/运行 2017 raw workspace。
- 建议方向：画出 `execute → capture/output → selection → final authorization/payload → semantic → final →
  handoff` 的数据所有权与时序；记录每字段唯一 authority、谁可写、何时可访问 test，以及现有 contract
  是否表达得出合法状态。先提交复现和差距说明，再决定修复面。
- 非目标：实现整份 RC8、升级版本、重跑任何历史题、设计新模型、增加完整新状态机。
- 禁止捷径：把 test payload 预塞进 Development output；修改 frozen 2017 output/builder；添加结果导向的
  第十次 Run；mock 掉 actual CLI；只测试 helper 不走 formal entrypoint。
- 验收条件：两个独立最小 fixture 稳定重现 Finalization 与 HF22；调用/authority 图能解释现有失败；
  proposed fix surface 明确且没有 production mutation；定向测试命令和预期 reason code 已冻结。
- 预期资源级别：`LOW`，只读代码 + project-original fixtures + 定向 pytest；不需网络、raw input 或模型
  Run。

### P0-02 — 修复 Finalization/test-authorization 接口

- 现象：released `execute` 只有 candidate/seed/code/timeout 输入，输出在 Development 阶段生成；actual
  controller 却要求 selected output 同时携带 `sealed_test_metrics_b64`。
- 影响：真实、未预知 selected candidate 的 episode 无法合法产生 Final payload；9/9 successful Runs 也
  不能形成 accepted Final Run 或 handoff。
- 来源证据：004C4 decision 的 HF14/HF21/HF23、controller trace 和
  [`terminal freeze`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/terminal_freeze/terminal_validation_freeze.json)。
- 代码入口：`cumcm_case.py` 的 `execute`/capture/seal/finalization helpers；
  `finalize_fresh_c_validation.py` 的 `_decode_selected_test()` 与 Gate 9。
- 相关测试：P0-01 冻结的新黑盒 test，加现有 controller neutral/adversarial/failure-retention tests。
- 最小复现：由 synthetic case 先完成候选选择，再只给 selected Run 一次明确、hash-bound 的 test access；
  未授权、提前访问、非 selected candidate、重复访问、payload/output hash 不匹配均必须 BLOCK。
- 建议方向：选择一个唯一 authority 的 post-selection Final evaluation contract；授权、test-access ledger、
  input/output/capture/manifest/decision hashes 和一次性时序都必须可验证。接口设计先于实现。
- 非目标：以新模型提高分数、放宽 one-shot、回填 2017 结果、把 test 用于 selection。
- 禁止捷径：接受 self-attested base64；复用 Development metric 冒充 Final test；静默修改 Run/output；
  controller 直接读未登记 raw test；允许多次 test access。
- 验收条件：actual CLI 的合法 synthetic path 到 `GATE_HANDOFF`；所有授权/时序/ownership attacks fail
  closed；失败不产生 accepted Final/Claims/handoff；旧负向历史只读 replay 不变；定向 + relevant full
  regression 通过。
- 预期资源级别：`MEDIUM`，contract/runner/controller/test 修改；不需真实题或模型 API。

### P0-03 — HF22 predicate-to-authoritative-facts 交叉绑定

- 现象：2017 REQ2 semantic artifact 声称 held-out valid，而 selected output 与 test ledger 明确否定；
  validator 只检查 predicate 为 true，没有核对 authoritative facts。
- 影响：semantic/aggregate Gate 可能为无依据的 predictive Claim 发 PASS，破坏 paper handoff 可信度。
- 来源证据：[`fresh_integrity_audit.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/fresh_integrity_audit.json)
  的 `additional_deterministic_blocker` 与 HF22 challenge。
- 代码入口：`cumcm_case.py::validate_semantic_claim_support()`/runtime semantic bundle；
  2017 `build_post_selection.py` 第约 291 行仅作 frozen defect evidence。
- 相关测试：P0-01 HF22 reproduction、RC6 neutral semantic contracts、actual controller black-box/
  adversarial tests。
- 最小复现：selected output=`DEVELOPMENT_GROUPED_OOS`、test access=`NOT_AUTHORIZED/0`、predicate=true；
  新 validator 必须以稳定 reason code BLOCK。再加入正确 held-out、错误 Run/output ownership、stale ledger、
  repeated access 和 aggregate propagation cases。
- 建议方向：semantic predicate 从 authoritative selected Run/output/final-evaluation ledger 派生或逐字段
  cross-bind；缺失/UNKNOWN/矛盾一律 fail closed；aggregate 只能消费已验证的 local Claims。
- 非目标：重写历史 challenge、人工解释 Claim、用文字 limitation 补偿 false predicate。
- 禁止捷径：只改 2017 builder；默认 unknown=true；允许 semantic payload 自证 authorization；把
  diagnostic metric 当 held-out。
- 验收条件：HF22 fixture 从错误 PASS 变为确定 BLOCK；合法 predictive fixture PASS；ownership、boundary、
  authorization、access count 和 hash lineage 全部被实际 entrypoint 检查；历史 freeze byte-identical。
- 预期资源级别：`MEDIUM`，deterministic contracts/tests；不需新题或模型 Run。

## P1：提升科学建模质量，而非只增加文件检查

### P1-01 — 让专业资料检索实际改变模型与实验

- 现象：当前 evidence chain 能登记 Source，但没有跨题证据证明一般专业资料会系统地改变候选机制、
  assumption、metric 或 experiment design。
- 影响：可能形成“有 source ledger、无 modeling consequence”的合规外壳，无法提升陌生题科学质量。
- 来源证据：[`GOALS.md`](../../GOALS.md) 的 evidence-first 目标、历史 Development/Validation 限制和
  [`STATUS_AND_EVIDENCE.md`](STATUS_AND_EVIDENCE.md) 的 UNKNOWN 项。
- 代码入口：research/source planning、assumption/model portfolio/experiment plan artifacts 和相应 Gate；
  具体文件应在新 phase 设计中定位。
- 相关测试：case-neutral source-to-decision lineage fixtures；当前尚无足够验收覆盖，属
  `PROPOSED_NOT_IMPLEMENTED`。
- 最小复现：用一个 synthetic domain fact，要求它产生可观察的 candidate/assumption/metric change；
  无影响、错误影响和未绑定影响分别 fail closed。
- 建议方向：记录 `source claim → modeling decision → alternative rejected/retained → experiment observable`
  的结构化 lineage，而不是只计来源数量。
- 非目标：自动复制论文方法、把搜索排名当质量、访问答案或候选第三方 code。
- 禁止捷径：source 存在即 PASS；用通用背景段落冒充模型影响；在 freeze 后为结果补来源。
- 验收条件：至少一个 neutral positive/negative contract；影响字段可复算、可追踪、缺失时 BLOCK；人工
  科研判断仍由队员核验。
- 预期资源级别：`MEDIUM`；设计/fixture 为主，后续真实资料验证另行预算。

### P1-02 — 数据充分性、模型适配与多问依赖

- 现象：2019 C 缺主问题所需实证数据；历史 cases 也暴露 simulation-as-empirical、portfolio dependency、
  baseline feasibility 和多问继承边界。
- 影响：结构合同可通过，但整题科学要求仍不满足；逐问局部结果可能被错误聚合成整体完成。
- 来源证据：[`phase004c2_2019c_validation.md`](../../reports/phase004c2_2019c_validation.md)、004C4
  black-box matrix 和 data-sufficiency/selection tests。
- 代码入口：runtime requirements/sources/data-sufficiency/selection/compatibility/aggregate validators。
- 相关测试：`test_actual_controller_black_box.py`、`test_actual_controller_neutral_e2e.py`、RC6 neutral
  evidence contracts。
- 最小复现：一项 empirical requirement 缺 observation、另一项 simulation 可完成，并有第三项依赖前
  两项；aggregate 必须明确 partial/blocked，不能用 simulation 填 empirical gap。
- 建议方向：把 requirement evidence class、data coverage、model applicability、dependency bridge 和
  Claim strength 放进同一 authority graph；允许诚实 partial，不把 partial 写 whole-problem PASS。
- 非目标：要求每题都有外部数据、自动选择复杂模型、追求文件数量。
- 禁止捷径：假设数据当 observation；依赖项只按 ID 对齐；baseline infeasible 后仍给相对改进；局部
  handoff 冒充整题 handoff。
- 验收条件：neutral mixed-evidence case 表达清楚 completed/partial/blocked；跨问 lineage 和 aggregate
  强度一致；现有 2019/2021 negative history 保持负向。
- 预期资源级别：`MEDIUM`。

### P1-03 — 科学质量、效率与 Development/Final 边界

- 现象：现有 gate coverage 偏重格式、hash、合同；陌生题科学质量、计算效率和正常开发修错与 sealed
  final evaluation 的边界仍不足。
- 影响：可能得到 schema-valid 但方法不适配、验证设计弱、计算超时或不可解释的产物；也可能因过度
  one-shot 化妨碍正常 Development debugging。
- 来源证据：GOALS 的专业质量/效率目标、2020/2021/2022/2019/2017 cases 的不同失败类型。
- 代码入口：experiment design、comparison、robustness、Final authorization 和 run ledger policies；具体
  改动需新 design freeze。
- 相关测试：需新增 case-neutral resource/quality decision fixtures；真实质量不能只靠 unit test 证明。
- 最小复现：明确 `DEVELOPMENT_DEBUG` 可在 predeclared budget 内修语法/运行错误并保留旧 Run；一旦进入
  frozen Validation/Final，禁止 result-driven retry。两者 ledger 和 Claim credit 必须不同。
- 建议方向：分别记录 correctness repair、model revision、resource use、scientific validation；用明确
  stop conditions 和最小 baseline，而不是只加 Gate 数量。
- 非目标：把 contest performance 自动化、承诺全局最优、用单一分数替代领域判断。
- 禁止捷径：删除失败 Run；把 Development retry 当 one-shot；把 CI runtime 当模型效率；把格式完整度
  当科学质量。
- 验收条件：状态/ledger 能区分开发修错与 sealed final；失败保留；resource/quality evidence 不互相
  替代；团队能按 runbook 演练。
- 预期资源级别：`MEDIUM_TO_HIGH`，需要设计、tests 和后续独立 case evidence。

## P2：验证与团队接手

### P2-01 — 冻结新版本后的跨题 Validation

- 现象：RC7 的 fresh C Validation 失败；Development regression 不能补齐。
- 影响：没有正向陌生 C completion evidence。
- 来源证据：004C4 terminal decision/state；2024/2019/2017 三个负向 Validation history。
- 代码入口：release/freeze/registration/controller/handoff chain，必须等 P0/P1 的新版本 acceptance。
- 相关测试：完整 deterministic regression、new release checker、prospective case rubric。
- 最小复现：先在 synthetic/Development 上证明新完成链，再 preregister 一个不同、answer-sealed C case；
  任何 freeze/remote/input 条件未满足均不得开始。
- 建议方向：一个新冻结版本、一个新 case、one-shot、明确资源/stop rule；失败同样是有效证据。
- 非目标：追求成功率分子、重跑 2017/2019/2024、访问 2025 reserve。
- 禁止捷径：挑结果后选 case；同题 seed 当独立题；在 run 后改 Skill/rubric；CI 代替 Validation。
- 验收条件：pre-run freeze、remote receipt、actual run、terminal decision/audit 全部独立绑定；结论按
  machine evidence，允许 FAILED/INSUFFICIENT。
- 预期资源级别：`HIGH`，仅在新设计和预算获批后。

### P2-02 — 队员接手演练

- 现象：当前环境含本地 `.venv`/cache/Git history 隐性依赖；文档尚未由陌生队员实操验证。
- 影响：文档存在不保证新电脑能独立定位状态、运行轻量 checks 或正确解释负向结果。
- 来源证据：[`ENVIRONMENT_AND_ASSETS.md`](ENVIRONMENT_AND_ASSETS.md)、[`RUNBOOK.md`](RUNBOOK.md)。
- 代码入口：无 production code；只使用公开 clone、handover docs 与 core checks。
- 相关测试：一名未参与开发的队员按 `CODEX_TAKEOVER.md` 走 `TAKEOVER_ONLY`，记录命令/exit/gap。
- 最小复现：无 ignored cache、无 GitHub write 权限的干净环境完成只读接手回执。
- 建议方向：修文档/依赖声明，不向个人配置靠拢；把 GitHub 权限与本地接手分开。
- 非目标：真实题运行、人工科研验收、自动授权发布。
- 禁止捷径：复制旧 `.venv`/`.cache`；共享 token；由原开发者口头补全部隐含步骤。
- 验收条件：队员能定位四个 blocker、版本面差异、历史/本次 checks，且没有访问受限资产；所有 gap
  明确记录。
- 预期资源级别：`LOW`。

### P2-03 — 条件满足后的保留题使用

- 现象：2025 C 仍 `SEALED_NOT_ACCESSED`，目前 004D 被锁。
- 影响：提前访问会永久破坏 held-out 身份，且 RC7 当前没有资格进入 004D。
- 来源证据：`state/project_state.json` 的 `next_phase_allowed`、2025 六项 access flags、WORKFLOW。
- 代码入口：未来 newly frozen Held-out plan/registry/access ledger；当前没有执行授权。
- 相关测试：访问前 deterministic preconditions、remote freeze、identity separation、post-run audit；均属
  `PROPOSED_NOT_IMPLEMENTED` 或未来计划。
- 最小复现：只对 synthetic placeholder 测访问 Gate；不得读取 2025 标题、题面、附件或答案。
- 建议方向：只有前序 Validation/authorization、团队合规、环境和资源条件全部满足，才另行请求明确
  用户授权并冻结使用协议。
- 非目标：当前接手、首个修复或 ordinary regression。
- 禁止捷径：目录探测/metadata 预览、以“只看标题”例外、使用旧聊天泄漏、把保留题当 Development。
- 验收条件：新的 formal route 明确允许 004D，pre-access audit 全 PASS，用户明确授权；否则保持六项
  false。
- 预期资源级别：`HIGH_AND_CONDITIONAL`。
