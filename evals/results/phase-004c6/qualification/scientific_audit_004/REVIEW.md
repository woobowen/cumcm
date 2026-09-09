# RC9 第四轮运行前协议与数学审核

- 冻结 subject：`38fae5f09555448f690efcaf7caa2e13b114eaff`，通过 `git rev-parse` 实际解析。
- 审核者：`/root/scientific_semantics_review`；范围为普通只读协议/科学核验。唯一写入范围为本目录。未修改共享文件、Git、正式 state；未另派 Agent。
- 结论：R3 三项修复与本轮非单调逆函数改动得到下述源码/合成证据支持；当前发布资格协议仍有两项已复现的实质性缺口，不能给整个 subject 无未闭合项的 PASS。本回执不能充当实际 Development 结果审核或 Formal Gate 裁决。

1. **实际执行与材料边界**

首条命令为 `ls -la`；看到已有 `.venv`、`.agents`、`scripts`、`tests` 等，随后使用现有 `.venv/bin/python`。所有共享源码均由 `git show` / `git diff` 固定到指定 subject，未使用主 Agent 对修复的声明作为验证。

`command_log.json` 保存 21 项实际读取、快照构建、测试、纯函数计算、测试完成轮询及审核产物核对的命令和完整返回。`input_manifest.json` 保存隔离测试实际使用的 10 个冻结文件的 SHA-256；这些副本位于 `snapshot/`，收尾实际复核全部哈希一致。9 个 Python 源文件实际通过 `compile` 语法检查。另读取了冻结协议、CI 脚本、2016 design，以及指定核心/准备器/中立测试代码；完整读取内容保存在命令日志。

实际中立测试命令为：

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -c /dev/null --confcutdir=.cache/pr12-rc9/scientific-semantics-review-004/snapshot --basetemp=.cache/pr12-rc9/scientific-semantics-review-004/pytest-temp -p no:cacheprovider --junitxml=.cache/pr12-rc9/scientific-semantics-review-004/neutral_tests.xml .cache/pr12-rc9/scientific-semantics-review-004/snapshot/tests/unit/test_rc9_case_numerics.py .cache/pr12-rc9/scientific-semantics-review-004/snapshot/tests/unit/test_phase004c6_qualification.py
```

结果：**19 passed in 1.11s**，其中数值测试 4 项、资格测试 15 项。隔离 `conftest.py` 仅提供冻结快照的 `repo_root`，没有载入原仓库 conftest。纯函数补充命令为 `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python .cache/pr12-rc9/scientific-semantics-review-004/probe.py`，exit 0，结果见 `probe_results.json`。这里的合成 budget/receipt 文件是审核夹具，与真实 case/state/result 无关。

真实题 producer 启动 **0**，真实题 checker 启动 **0**，真实 Final 启动 **0**；未跑 full CI，未读取原题、原始数据、真实子 root、正式 state、已生成 Development 数值结果或其他审核报告。无安装、配置或共享文件修改。

2. **R3 修复核对**

- **BOUNDED 已落入实际 Claim 构造。** `scripts/prepare_phase004c6_development.py:515–545` 的 `propose()` Claim 字典包含 `claim_strength="BOUNDED"`，预测 Claim 继续声明 `CONDITIONAL_ESTIMATE`、`target_accuracy_verified=False`。AST 实际提取结果为 BOUNDED，与核心 `cumcm_case.py:1878` 所需值一致。本轮是构造源码/AST 核对，没有运行真实 proposal 或真实 Claim 审批。
- **Final checker 余量提前检查已闭合。** 核心 `6422–6441` 在 AUTHORIZED 前调用 `consume_start_budget(check_only=True, needed=len(selected_run_ids))`，异常留下 REQUESTED/REJECTED；`6449` 才消费 Final 名额。对实际抽取函数的合成执行证明：已用 3/4 且需 2 个 checker 被拒；用满 4/4 后请求 Final 被拒；只记录 REQUESTED、REJECTED，budget 保持 4 个合成 checker reservations，Final reservation 为 0，没有 Final ledger。此次没有启动任何子进程。`check_only` 是容量预检，不是多进程原子预留；结论适用于本任务串行 case 执行约束。
- **附件2电压/完整前缀假设已显式检查。** 准备器 `101–115` 要求 301 行电压严格下降，3 个历史状态逐行完整，第4列已知值连续从首行开始；这在有限正常数值输入下使 `voltage >= cut` 恰好等于前 N 行。合成有效输入生成 6 个历史起点及 1 个 FORECAST，所有拟合观测 available_at <= origin，未来 target_observation_id 为 null。重复电压、历史缺行、目标前缀内部缺口分别实际返回 `ATTACHMENT2_ORDER_NOT_STRICTLY_DECREASING`、`HISTORICAL_STATE_ROWS_INCOMPLETE`、`FORECAST_PREFIX_HAS_INTERIOR_GAP`。未验证真实工作簿是否满足这些约束。

前轮 SCI-001..004 的核心修复没有被本轮 diff 撤回：逐样本 origin/真值绑定、ROOT_MEAN 的平方误差限制、历史标签可用时钟和扰动重算仍保留。此次没有重跑这些修复的全部旧测试。

3. **2016 非单调逆函数与数学范围**

producer `surface()` 在归一化 knots 并集上以各阶导数重建精确分段三次多项式，再通过 `PPoly.solve` 选最后根；泰勒平移系数为 `d3/6`、`d2/2-d3*h/2`、`d1-d2*h+d3*h²/2`、`d0-d1*h+d2*h²/2-d3*h³/6`，量纲与归一化时间变换一致。checker 采用独立标量分段系数，在每段二次导数方程的实根处分割单调区间，再选择最后下降 bracket 二分；电流混合时使用两条曲线缩放后的 knots 并集与链式法则导数。

4 项已有数值测试实际通过：非单调线性、非单调 PCHIP、单段三根、非单调电流插值。额外使用不同 knots、不同持续时间、不同 current 权重构造两条合成曲线，各测 6 个电压；producer 与独立标量 checker 的逆时间最大差为：BASELINE `1.7763568394002505e-15 min`，CUBIC_LOG_AFFINE `8.881784197001252e-16 min`，代回前向曲线均在 `1e-9` 内。这支持修复对本轮合成非单调形状有效，不证明所有浮点边界或实际数据残差通过。

前轮所报逐电流 MRE/5 个 remaining 的 checker 绑定与 2015 JD 唯一集合检查仍在固定主体中；2015 checker 另明确要求 5 个扰动标签全集及参数全集（`check.py:286–299`）。本轮只静态复核该改动，没有运行天文模型或读取任何参考数值。

指标/结论范围继续限定：6 个历史 state×origin 的 remaining-time 相对误差分母为各自 `true_end-origin`，单位为无量纲比值，6 行相关且来自同一电池；不是 6 个独立电池。Q3 只利用较早完整状态和该历史目标的已知前缀拟合；状态3未来终止真值未作为 target 输入。55A 是条件电流插值，LOCO 是其他已知电流的 Development 诊断；二者不构成55A真实精度验证。参考迁移/前缀扰动范围是非校准模型敏感性，不是置信区间。实际独立 checker 重算最多支持所给数据、模型和数值实现的一致性，不能补出未来真值或新独立 Validation。

4. **R4-001：负结果启动计数与资格协议冲突——已复现，未闭合**

`check_phase004c6_rc9_release.py:218–223` 接受 `FAILED`/`INSUFFICIENT` 终态；冻结 protocol 明确不要求全部 Development 科学通过。但 `211–217` 同时要求 model/checker/Final 三类启动次数都至少为 1。诚实记录“模型启动1次，checker=0，Final=0，未到 Final 即失败”的两个合成 case，实际收到 4 项 `RC9_DEVELOPMENT_START_BUDGET_INVALID`。

这会排除本来应保留的失败/不足证据，且可能错误地迫使执行本不该启动的 Final。应依终态允许零次 checker/Final，并绑定真实启动 ledger/终态依据；成功的 scoped completion 可保留更强的完成要求。这里是负结果记录协议缺陷，不是实际模型失败判断。

5. **R4-002：native_result_review 没有结果审核对象绑定——已复现，未闭合**

同脚本 `185–195` 对 `native_protocol_review` 和 `native_result_review` 使用相同字段要求，只检查机制、任务名、subject、命令数、空未闭合项与附件哈希。它不要求结果审核声明实际观察到的新 Development case/Run/终态/结果文件，也不验证审核对象集合。

合成回执显式写入 `review_scope="PRE_EXECUTION_SOURCE_ONLY"`、`reviewed_development_artifacts=[]`，其 kind 为 `native_result_review`，实际 `validate_receipts` 返回 `[]`。这验证的是普通回执范围错配未被识别；没有声称完成任何真实结果审核。

相关边界：`development_results` 的 `question_results` 和 limitations 只要求非空；当前代码没有逐问覆盖全集或每个 Run/checker/终态的专门绑定要求，实际启动次数也来自回执字段。附件哈希证明附件没有改变，不能独自证明这些附件确实是所需结果审核对象。应为两个新 case 建立逐问及结果证据绑定，并要求 native_result_review 覆盖同一组对象。本报告仅能用于运行前 protocol/science review，不能在此字段下重复使用。

6. **R4-003：Q3 current_A 的已知/必需字段声明过宽——源码确认，输入事实未读**

准备器 `240/257` 将 Q3 的 minimum_data_fields / known_input_fields 都设为 current_A、voltage_V、elapsed_min，随后 `299–300` 将字段充分性置 SUFFICIENT 且 missing_fields 置空；producer 的 Q3 scope 也沿用三字段。但 `transfer(reference,prefix,candidate)` 只使用对应电压下的时间轨迹，不需要电流数值。Q3 的“各状态相同恒流”属于模型条件，不等于输入提供数值 current_A。

若附件2确实只有相同恒流的条件而没有电流数值，则该声明构成数据充分性误述：应将 Q3 所需/已知字段限为 voltage_V、elapsed_min，登记“相同但数值未知恒流”条件并同步输出 scope。Q1/Q2 的电流数值仍是必要输入。原始输入是否确实缺少该数值是主 Agent 提供的待独立输入审查事实，本轮没有读取 raw 去确认；不得把此条件性判断写成已经核查原题。

7. **发布记录脚本中已成立的边界与未执行部分**

资格脚本要求精确40位 subject，按实现目录/文件、两份 case code、design 和 protocol 建立内容哈希映射；校验当前实现与该映射一致。每个 command receipt 绑定 subject，命令 executed_head 的实现映射必须相同；允许仅回执/元数据后续提交，而无需把将来的提交 SHA 写回源码。

full_ci 不能由 strict 替代：必须有 `argv == ["bash", "scripts/ci.sh"]`、exit 0、足够 pytest passed、pytest_failed=0。中立资格测试实际覆盖旧 subject、错误实现、失败命令、倒置时间、修改日志、strict 冒充 full CI 等情况。冻结 CI 脚本为 `set -euo pipefail`，包含 ruff、pytest 与仓库检查；这里仅阅读脚本，没有执行整套 CI。

`record_phase004c6_command.py` 实际调用 subprocess.run，记录开始/结束时间、monotonic 耗时、exit、executed_head、命令、stdout/stderr 哈希，保留原始流并生成路径归一化日志；已有同名回执/日志会拒绝覆盖。pytest 汇总来自实际 stdout 的正则提取，Junit 若提供则作为额外哈希附件。资格脚本对 strict/historical_subjects 的命令内容没有与 full CI 同样的精确 argv 要求；非空证据及标签仍有人工制作回执时的范围责任。未运行该 recorder 的真实 CLI，未验证任何实际 full CI 回执或完整日志。

旧 `phase-004c5` 历史通过历史 subject 的 Git tree 与当前 tree 比较保持不可变；snapshot 的 old_validation 必须为 0/2、新独立 Validation 必须为0。Development 必须绑定两个新 case、相同subject并声明 independent_validation=false。candidate、decision、Auditor、activation 依次哈希绑定，映射不含这些后续证据对象，静态上没有提交自引用。active 分支会重算 decision，再检查 Auditor 与 activation 哈希；本轮没有打开这些真实对象或运行 active 判定。

以上均是运行前的源码、纯函数与限定中立测试证据。发布资格在 R4-001/002 闭合前仍不足；真实 Development 每问输出、误差数值、checker 残差、负结果、预算消耗、Final 与最终结果审核均未覆盖。
