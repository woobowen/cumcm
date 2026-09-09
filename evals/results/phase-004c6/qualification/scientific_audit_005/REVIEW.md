# RC9 第五轮限定 diff 复核

**最终 reviewed_subject：`2d74ca82e2d52799e81bf5d95850570f14d93a58`。第1–6项保留对1696c9d的原始范围和结果；第7项记录最终小差异核验并闭合 canonical terminal 待核对项。最终结论为：限定运行前范围内通过，无本轮重大未闭合发现；真实结果审核尚未执行。**

固定 subject：`1696c9d2014b9be6ba6aec0a4656336e60aacd4e`。比较基线：`38fae5f09555448f690efcaf7caa2e13b114eaff`。审核者：`/root/scientific_semantics_review`。

**运行前结论：本轮限定 diff 中，R4-001、R4-002、R4-003 的对应修复已得到实际中立测试/纯函数证据支持；未发现新增的重大数学或运行前协议缺陷。最终回执与 registry 的 canonical terminal 同一性仍须在真实收口时确认，见第5项。本结论不表示实际 Development 数值、full CI、正式资格、真实 checker 或 Final 已通过。**

1. 实际命令及范围

首条命令为 `ls -la`，看到现有 `.venv`、scripts、tests、src 等。固定 Git 对象解析得到上述完整 SHA。只读本轮指定源码、code、design、protocol 的 diff 及所需函数上下文；只写 `.cache/pr12-rc9/scientific-semantics-review-005/`。未读取原题、raw、真实子 root、真实 registry/state/terminal、已生成数值结果或其他审核结果，未运行历史/现行 state 审核。

9 个实际使用的冻结文件保存在 `snapshot/`，SHA-256 见 `input_manifest.json`；其中 6 个 Python 文件通过实际 `compile` 语法检查。`command_log.json` 保存实际命令及完整输出。共享工作区、Git、正式 state 均未修改，无新增依赖或配置变更。

实际运行：

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -c /dev/null --confcutdir=.cache/pr12-rc9/scientific-semantics-review-005/snapshot --basetemp=.cache/pr12-rc9/scientific-semantics-review-005/pytest-temp -p no:cacheprovider --junitxml=.cache/pr12-rc9/scientific-semantics-review-005/neutral_tests.xml .cache/pr12-rc9/scientific-semantics-review-005/snapshot/tests/unit/test_phase004c6_qualification.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python .cache/pr12-rc9/scientific-semantics-review-005/probe.py
```

结果分别为 **16 passed in 0.11s**、**exit 0**。JUnit、纯函数源码和完整结果分别为 `neutral_tests.xml`、`probe.py`、`probe_results.json`。原 registry 测试文件中的 extension()/历史测试会读取真实历史 registry/state，故仅阅读源码，没有运行该整文件；新 tuple 验证改用完全自造的 registry、history、registration、terminal 字典调用实际函数。未把主 Agent 报告的45项测试算成本审核实跑结果。

真实 producer/checker/Final 启动数均为 **0**；没有 full CI，也没有真实案例 numerical result review。

2. R4-003：Q3 字段和条件已分开

准备器 `prepare()` 的实际赋值块经 AST 抽取执行：Q1/Q2 继续要求 `current_A, voltage_V, elapsed_min`；Q3 的 minimum_data_fields 与 prediction_spec.known_input_fields 均为 `voltage_V, elapsed_min`，conditions 明确“各放电状态共享一个恒流，其数值未知”。Q3 仍是 TIME_CONTINUATION、future_remaining_time 的 CONDITIONAL_ESTIMATE，真实状态3终止标签为未来真值字段，empirical_accuracy_required=False。

2016 producer `rc9_science()` 本轮将输出 facts.scope.fields 同步为实际 requirement.minimum_data_fields，避免旧 scope 保留虚构的 Q3 电流数值。该改动只调整输入和声明边界，不改变已有 transfer 的时间轨迹算法。原始附件是否确实只提供相同恒流的条件，本轮仍未读取核查；现有源码的已知字段声明已经与指定模型所需输入一致。

3. R4-001：负终局可登记，最低独立验算不足另报

冻结 protocol 新增 model/checker 最低次数各1，并明确负终局登记不要求满足任务资格最低次数，Final 只对 SCOPED_DEVELOPMENT_COMPLETE 必须为1。资格函数现在先检查 `0 <= starts <= maximum`，再以 `RC9_DEVELOPMENT_MINIMUM_EXECUTION_EVIDENCE_NOT_MET` 区分启动不足。

实际合成结果：

- 有 model/checker、Final=0 的 INSUFFICIENT 终态，Development 回执验证返回 `[]`。
- 将 checker 改为0并同步 ledger、terminal 后，只收到 `RC9_DEVELOPMENT_MINIMUM_EXECUTION_EVIDENCE_NOT_MET`，不再误报 START_BUDGET_INVALID。
- 同一个 model=1/checker=0/Final=0 的 FAILED 终态可由实际 `validate_registry()` 接受登记；这不是任务资格 PASS。
- SCOPED_DEVELOPMENT_COMPLETE 的 Final 必须为1，源码中的专门检查保持生效；不因收集次数而要求在科学拒绝后启动 Final。

这修复了“如实登记失败”与“完成任务最低验算要求”的概念冲突。它没有把失败结果转换成成功得分，也没有解除任何真实执行限额。

4. R4-002：逐问、执行证据和结果审核对象已绑定

两份 development_design 现在冻结 required_question_ids：2016 为 Q1/Q2/Q3，2015 为 DEFINITION、VALIDATION 和7个城市。qualifier 要求问题集合及数量一致，receipt 与 terminal 的逐问结果相等，case/subject/status 相符；execution_evidence 绑定同一 case/subject。

启动次数由哈希绑定的 budget ledger 逐类计数，必须与回执和 terminal 相等、limits 必须与冻结 design 相等；execution artifacts 的文件哈希也逐项检查。实际合成测试已拒绝：逐问缺失、terminal subject 错配、execution subject 错配、ledger 次数错配、ledger limits 错配、artifact SHA 错配。完整一致的合成回执返回 `[]`。

native_result_review 必须明确 `ACTUAL_POSTVALIDATION_DEVELOPMENT_RESULTS`，并精确覆盖 Development 回执所列两 case 的 terminal 与 execution_evidence binding。实际测试中：完整合成绑定接受；`PRE_EXECUTION_SOURCE_ONLY` 被拒；少一个 case 被拒，均返回 `RC9_NATIVE_RESULT_ARTIFACT_BINDING_INVALID`。本审核属于运行前源码/纯函数审查，不能作为 native_result_review 使用。

这里验证的是字段、集合、哈希和对象绑定关系。执行附件是否包含完整、真实且解释正确的数值证据仍必须由后续实际结果审核确认；不能把一般性附件哈希检查当作已验证模型精度。

5. 新 child terminal 身份及生命周期

`training_registry.validate_development_terminal()` 要求固定 schema、phase、case_id、skill_version、subject_commit、parent_terminal_sha256、decision_id 和 independent_validation=False，且 terminal_decision_id 必须为 `DECISION-{case_id}`。实际合成验证：正确负终局接受；phase、case、version、subject、decision、independent_validation、parent hash 7项分别错配均拒绝。

生命周期纯函数测试：NOT_STARTED 且两个时间为空接受；IN_PROGRESS 具有带时区 start 且 freeze 为空接受；FROZEN 的 freeze 早于 start 被拒。源码中 `repository_registry_errors()` 对真实冻结 child 另强制 canonical 路径 `evals/results/phase-004c6/{case_id}/terminal/decision.json` 并核对 registry 中的 SHA；本轮没有运行会读取真实 registry/terminal 的该入口。

**收口时的窄范围待核对项：** qualifier 当前允许 receipt.terminal 绑定 phase-004c6 下任一满足字段/哈希的文件，而 registry 入口强制上述 canonical 路径。后续实际回执必须使用 registry 所绑定的同一个 canonical terminal 文件，不能用另一份同 case 的副本替代这项交叉绑定。本轮仅指出两个校验入口的连接要求，没有执行真实登记和资格联动；若新增 canonical-path 等式，应按新 subject 单独核对该小差异。

6. 本轮没有扩大的结论

本轮没有修改或重审数值模型主体；前轮已测的 remaining-time 分母/单位、六个相关历史起点、严格更早状态和前缀、55A 条件插值与 LOCO 的区别、非校准模型范围等边界继续适用。也没有复跑前轮19项中立测试、公共 core 的全部 SCI 回归或完整 CLI/Final 链。

后续仍必须从真实执行证据核验：实际读取数据满足准备器前置条件，运行按冻结 subject，预算及失败尝试完整，逐问数值与 checker 残差、局限、terminal 和结果审核对象一致。旧0/2和新独立Validation=0不能因这次运行前通过而变化。此回执不是代理多数票，也不是 Formal Gate 的自动裁决或实际结果审核。

7. 最终小差异核验：2d74ca82e2d52799e81bf5d95850570f14d93a58

精确 SHA 通过实际 `git rev-parse` 解析。只补读1696c9d到此提交的 qualifier、对应测试夹具和 pyproject 差异；`--name-only` 还列出 environment_changes.json、neutral_spec_test_map.json，两者属于额外记录，本审核未读取其内容，未将它们作为他人结果证据。先前已经审核的数值模型、core、prepare、registry、design 和 protocol 没有在这段差异中改变。

qualifier 新增 `case.terminal.path == evals/results/phase-004c6/{case_id}/terminal/decision.json`，与 registry 的 canonical 路径相同。实际纯数据测试证明：完整 canonical fixture 返回 `[]`；复制完全相同的 JSON 字节、保持相同 SHA，仅把回执路径指向另一份副本时，返回 `RC9_DEVELOPMENT_RESULT_BINDING_INVALID`。第5项所列两个入口的路径连接缺口因此在最终 subject 闭合。真实收口仍要核验实际附件及 registry，但无须为了这个已修复等式继续改动框架。

本轮实际构建独立 `snapshot-final/`，包含最终 qualifier、其测试文件与 pyproject，哈希见 `input_manifest_final_delta.json`。最终冻结资格文件再次实际运行 **16 passed in 0.12s**，JUnit 为 `neutral_tests_final.xml`；`probe_final_delta.py` 实际 exit 0，结果见 `probe_final_delta_results.json`。没有复跑数值模型、真实 checker 或 Final，也没有把主 Agent 的20项结果算成自己的实跑结果。

pyproject 的 dev 依赖新增 `numpy==2.4.6`、`scipy==1.17.1`。本审核实际读取当前安装版本与包 metadata，两者匹配这些版本且 Requires-Python 均为 `>=3.11`，与项目声明一致；没有安装或升级任何包。没有测试全新远端环境的下载/安装，因此只确认声明与当前已验证环境一致。

最终范围结论：R4-001至003及本轮 canonical terminal 连接要求均已按指定范围核对闭合。可以把本回执用于 `2d74ca82e2d52799e81bf5d95850570f14d93a58` 的运行前 protocol/science 审查材料；不具备 `native_result_review` 资格。本轮未发现阻止按已冻结限额计划开始两个 Development 案例的新增数学或协议源码问题。最终 Formal Gate、full CI、真实逐问数值结论、negative outcomes 及实际结果审核依旧未验证，须由相应后续证据建立。
