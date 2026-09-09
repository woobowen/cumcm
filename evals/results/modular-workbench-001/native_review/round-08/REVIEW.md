# Round 08：需求顺序回归语义与执行代码身份

只读裁定支持本次测试语义修正：将“需求顺序任意”的正例放在冻结/实际捕获之前；保留捕获后反序、再用测试 helper 重绑状态的显式 STALE 负例。无需放松 runtime 的冻结身份。另已实际确认 known 执行 subject `df430c0` 与最终测试/资格 subject `929d287` 的指定 runtime 源文件映射相同。两个 subject 的角色必须分别记录，不能重标旧 Run。

本轮没有给整体工程、科学、known 或 Decision Auditor PASS。模型、科学 checker、Final、known 数据/数值读取、全 CI、网络、Git mutation、公共/state 写入均为 0。只读允许的代码、规则、失败日志和 Git 源码映射；写入仅本 round08。

## 测试语义裁定

受读 core SHA-256 一直为 `da5d02c792f4bfdd84f979d1d019b72071764d8de01ef743e68957527f808384`。

- `resolve_scenario_identity` 第 5337 行起把 `problem_requirements.content` 整体纳入 `scenario-input/v2`。它只将显式 `scenario.requirement_ids` 作为集合排序；requirements 数组的顺序保留在 payload 内。
- `validate_execution_capture` 第 3433 行附近和 `verify_current_capture_files` 第 6077 行起，均比较 capture 中的 scenario hash 与当前 resolver 结果。数组反序改变其值，因此旧 capture 必须 STALE。
- `_sync_bound_hashes`（`test_actual_controller_black_box.py:444`）仅重写 `case_state.evidence_bindings`，不产生新过程、也不重新绑定旧 capture 的场景身份。不能通过这个测试辅助函数授权冻结后的新场景。
- 活动计划第 29–33 行明确绑定 requirements、assumptions/constraints 和 experiment semantics；`WORKFLOW.md:211` / `:224` 要求依赖变更在后继 Gate 前传播 STALE，并从最早受影响前置重新计算。根/Skill AGENTS 的 hash-bound Run 与 STALE 规则方向一致。

准确措辞是“冻结的 canonical requirement content（包括该数组顺序）”，不是“整个 artifact 原始字节”。resolver 不纳入 artifact 外层元数据，JSON 空白和对象键顺序由 canonicalization 消除；不应声称任何字节变化都必然改变 scenario hash。

实际原创最小 probe 验证：

- 初始 scenario hash：`d3170e82d6ccc4e9f33057cbe8f6ebe542f28d8135b3e8ca3e982aef4adfb247`。
- 仅显式 requirement scope 集合反序、仅 artifact JSON 空白变化：hash 不变。
- requirements 数组反序：变为 `57abff2c8c93d7acdd5f33e1e205b55091333d9deed395879d80d738a0568916`。
- 将旧 hash 交给复用 guard：`RC_EXECUTION_CAPTURE_SCENARIO_STALE`。

该 probe 没有创建真实 capture、没有重绑 case_state、没有执行完整模型/Final。它只独立验证 resolver 和 guard 的这条语义。

首次实际读取的 `final-directed-001.log` 明确为 `1 failed, 189 passed in 148.86s`，失败项正是 REQUIREMENT_ORDER，controller reason 为 `RC_EXECUTION_CAPTURE_SCENARIO_STALE`。这是主 Agent 已执行日志的只读观察，不是本 reviewer 重跑测试。首次该日志 hash=`8c2976ba2df967d98ac3aac66308f0076bfb74efba311078ce6cb2a98d17041e`；后续文件 hash 发生变化，均保留在首尾身份记录中，不把后来的内容冒认为最初受读字节。

已看到当前正例通过 `reverse_requirements_before_freeze` 在 requirements 首次登记前反序。负例继续在实际 capture 后反序并调用 `_sync_bound_hashes`。本 reviewer 指出 test_access_count=0 不单独等于 Final0 后，当前代码已补充 scientific Final ledger、Final evaluation ledger 均不存在及原 capture hash 不变的断言。主 Agent 报告相关 3 个测试实际通过；本 reviewer 未执行该数值测试，未把这条转成自己的测试成绩。

## known runtime 映射边界

新增核查只读取 imports/复制路径/映射，不读取 known 原题、数据、指标、运行输出或终态记录，也不运行任何 known 入口。

实际代码路径：`prepare_workbench_known.py` 使用 `prepare_phase004c6_development.py`、Skill core/synthetic，复制 `known_code/produce.py` 与 `check.py`；controller 加载同一 Skill core，workbench 共用该 controller。以上仓库内路径均落入 `KNOWN_RUNTIME_PREFIXES` / `KNOWN_RUNTIME_EXACT`。未观察到这条准备/执行链导入 tests 模块；测试与 q 自身可以排除出该运行代码映射，但仍受完整 candidate map 和最终 CI 约束。

q 的 known detail 验证要求：executed_subject 保持 registration.skill_commit；terminal.subject_commit 与 capture.code_commit 也保持这个实际执行 commit；运行代码映射须与当前 HEAD 一致。这个机制允许后续仅测试/资格代码修正，不伪造旧 Run 的执行 SHA。

最新实际只读计算：

| 项 | 观察 |
| --- | --- |
| 执行 subject 参数 | `df430c0f0785e83b1a84726e88d25b7b2e0b9d0a` |
| 实际 `git rev-parse HEAD` | `929d2874e711ca4dd58484555009b028555898a3` |
| q SHA-256 | `5368a7318d41c96ae6583d2ad9e372fa8c3481df3ee43c4894996a3e59366f8c` |
| runtime 文件数 | 346 |
| 执行 subject / 新 HEAD / 当前 working runtime 映射 | 三者逐文件 hash 相等 |
| 三者共同 canonical mapping hash | `bad03abd428352a45cf2b6ecabdc2566bc27b39beaa00205b3432c6165fbddd2` |
| 最终完整 candidate map 文件数 | 828；包括 q、相关测试及新增原始单测 packet |

映射身份只证明所列仓库源代码相同，不证明输入/环境或执行结果。numpy、openpyxl、yaml 等外部依赖仍属于环境证据；本轮没有核验其环境等价。known R2 的 2/3/1 与到达 handoff 是主 Agent 的报告，本 reviewer 没有读取或重新裁定这些实际记录。最终文案应表述为“R2 实际执行于 df430c0；测试/资格 subject 为 929d287；经验证两者生产 runtime 源文件映射相同”，不得写“R2 实际执行于 929d287”。

## 实际命令、UTC 与漂移

首先执行 `ls -la`；随后仅用定向 `rg` / `sed` / `tail` 和 `.venv/bin/python -B`。开始 snapshot UTC `2026-09-09T10:17:16.085182+00:00`，当时 HEAD=df430c0。旧测试、计划、失败日志及 q 的中途变化未覆盖原有日志；`source_start.json`、`source_end.json`、`source_final.json` 分别保留观察时刻。

| 实际命令 | UTC 起止 | 记录 |
| --- | --- | --- |
| `.venv/bin/python -B .cache/modular-workbench-001/protocol-review/round-08/resolver_semantics.py` | 10:18:43.650959–10:18:43.690574 | `resolver-20260909T101843650959Z/results.json`，exit 0，无 core 漂移 |
| `.venv/bin/python -B .cache/modular-workbench-001/protocol-review/round-08/runtime_identity.py` | 10:20:56.990349–10:20:58.694180 | `runtime-identity-20260909T102056990349Z.json`，exit 0；当时 HEAD=df430c0、q=d919558d…，完整 map=826 |
| 同一 runtime_identity.py，新 HEAD 复核 | 10:22:40.417484–10:22:43.667684 | `runtime-identity-20260909T102240417484Z.json`，exit 0；HEAD=929d287、q=5368a731…，完整 map=828，调用内无源漂移 |

一次只读 rg 查询包含并不存在的猜测路径 `scripts/prepare_rc9_development_case.py`，工具返回明确 missing；随即按源码显式路径改查真实 `scripts/prepare_phase004c6_development.py`。没有执行猜测路径或切换环境。

本轮两个授权范围内无剩余 material finding。最终定向重跑/全 CI 和统一 candidate decision 的实际结果尚未由本 reviewer 核验；本报告只裁定上述测试语义和源文件身份边界。
