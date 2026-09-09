# RC9 第六轮限定运行前差异审核

reviewed_subject：`10e8b038d571b88ce2b7f2388da00a618c774f69`。已审比较基线：`2d74ca82e2d52799e81bf5d95850570f14d93a58`。审核者：`/root/scientific_semantics_review`。

**限定结论：PASS_WITHIN_REVIEWED_PRE_EXECUTION_SCOPE。本轮未发现重大未闭合数学或准备合同异议。** 指定16项定向测试实际通过，版本化 registration 的准备前置条件通过纯函数验证；此结论不能作为实际 Development 数值结果审核、实际 checker/Final 验证或 Formal Gate 判定。

1. 实际命令与证据边界

首个执行命令为 `ls -la`，确认现有 `.venv`、scripts、tests、src 等目录；使用现有 `.venv/bin/python`，无安装。`git rev-parse` 实际返回上述完整 subject。共享文件通过固定 Git subject 读取，未跟随主 Agent 正在更新的工作区。

`command_log.json` 保存每个实际命令的 UTC 开始/结束时间、工具退出状态、耗时和输出；`input_manifest.json` 保存冻结快照220个源码/必要测试元数据文件的 SHA-256。快照包含测试导入所需第一方 src 代码、指定测试及其策略/状态/schema/计划元数据，不含问题文件、附件、答案、真实子 root、隐藏 vault 或数值产物。

测试前已向主 Agent指出原16项测试内部会解析既有 registry/state/保留标志等元数据，并得到明确授权：允许这些正常 policy 测试内部消费既有登记元数据，不显示 held-out 条目、不访问题目内容。本轮没有打开2025题目档案、原题、数据、答案或 vault，也没有读取旧完整实验历史。本模型直接检查 registry 的部分仅为 `git diff --unified=0` 新增两个 child 的登记字段；旧条目由限定测试内部按合同使用。

只写 `.cache/pr12-rc9/scientific-semantics-review-006/`，没有修改共享源码、正式 registry/state、Git 或撤销他人修改。没有执行会消耗真实 case 预算的命令。

2. 16项原定向测试——实际 PASS

在冻结快照目录中，使用 snapshot/src 和 snapshot 的 PYTHONPATH、关闭 bytecode 与 pytest cache、将 basetemp/JUnit 固定在本审核目录，实际运行：

```text
tests/unit/test_target_problem_policy.py
tests/unit/test_competition_rc_skill.py::test_skill_is_competition_rc_and_has_one_workflow_set
tests/unit/test_phase002d_r2a_start_freeze_dependencies.py::test_r3_plan_is_preserved_after_successor_advances
```

完整命令见 command_log.json；结果 **16 passed in 2.47s，exit 0**，JUnit 为 `targeted_tests.xml`。其中 policy 文件14项、版本/Skill关系1项、plan关系及旧plan保留1项。没有运行其他历史测试，也没有 full CI。

新版版本测试通过明确 `phase -> project_version, skill_version` 映射，交叉检查项目 VERSION、Skill VERSION、core.VERSION 与 SKILL.md；004C6 另检查 target_candidate_version。它不再用旧rc8字面值拒绝合法rc9，同时仍检查14个workflow、4个agent等既有结构。

新版 plan 测试先按项目 schema 验证元数据，要求 phase 对应唯一 active plan，且 state.current_plan 与其路径一致；004C6 对归档旧004C5 plan 使用 `bcf498907cbf282e2c79580ea56b043fc1a7b52b` 的 Git 字节相等锚点。这一旧plan字节比较在上述实际测试中通过；并非仅检查文件存在或改用宽泛版本字符串。

新增 child target 合同字段包含 C 类、DEVELOPMENT_AFTER_VALIDATION、批次位置、formal_skill_version/commit alias、LOCKED、first_run_freeze=null，以及 KNOWN_CASE_DEVELOPMENT_ONLY/NO_NEW_INDEPENDENT_VALIDATION 轴。新增4个定向变体验证分别拒绝 commit alias、version alias、空 generalization_axis 和缺 target_problem_type。新 child 的 independent_problem=false 不会增加独立题泛化样本数。

3. 版本化 registration 的准备合同——实际纯函数验证

`scripts/prepare_phase004c6_development.py` 的源 SHA-256 为 `26c0b8ae59dff024ac75e7ea294a625c894c9b6de91d46672c708767bb0b05ce`。修改后的顺序为：确认 root 尚不存在和精确 subject；从 registry 选择唯一 child；使用该条 registration.path；检查路径属于该 child 的 registration 目录及 SHA；读取 registration；核对 shared_subject、case_id、case_root 与 development_design SHA；随后才 initialize_case。prepare receipt 最后记录的 registration_sha256 也改为实际选中的版本化 registration，而非旧固定文件名。

`prepare_contract_probe.py` 实际抽取该 `prepare()` 函数从起点到 `initialize_case` 之前的原始 AST，保留这些条件判断，仅在原初始化调用处停止。使用独占目录内的合成 YAML/JSON，git subject 解析与 core JSON/hash 方法被限定替身提供；没有执行 initialize_case 或后续 prepare。

实际结果：

- 两个年份的合成 registry 指向 `case_registration_r2.json` 时接受，即使旧固定文件名仍保留过期内容，也准确使用 registry 所指的版本。
- 重复 child 拒绝：`UNIQUE_CHILD_REGISTRATION_REQUIRED`。
- 指向该 child registration 目录外的登记拒绝：`CHILD_REGISTRATION_PATH_INVALID`。
- registration SHA 错配拒绝：`CHILD_REGISTRATION_HASH_MISMATCH`。
- subject、case_id、root、design SHA 任一错配均拒绝：`SHARED_SUBJECT_REGISTRATION_MISMATCH`。
- 已存在 root 拒绝：`NEW_CHILD_ROOT_ALREADY_EXISTS`。

结果见 `prepare_contract_probe_results.json`，命令 exit 0。该探针验证准备前置合同的实际行为；没有测试真实 parent 文件复制、真实 preflight/状态推进或真实 root 完整准备过程。

4. R1保留与R2 design范围

两份 `design_versions/r1.json` 实际与已审基线2d74中的 development_design Git字节完全相等：2016归档 SHA-256 为 `525bebb400dd75e0bb2bc519f0d4d8847d32f0ed46b4ce480923a184aeb2021b`；2015为 `0332ce81f75497d498620433b7605bc9b755a298d0a0288be331e5ade2ba2490`。

分别去除 case_root 后，r1归档与r2 design JSON对象完全相等；唯一变化为 `case-r1 -> case-r2`。预算4 model/4 checker/1 Final、有限科学方案、逐问集合、旧题Development身份、新独立Validation=0等设计内容未改变。未打开真实r1/r2 root，因此这里只证明设计归档及源码不覆盖旧root的检查，不声称已验证真实r1磁盘状态或真实数值启动计数。

固定10e8b038的 registry/registration 仍保存此前r1登记，当前 design 已指向r2；这是 subject先固定、再以版本化registration登记新执行对象的准备顺序。原r1登记无法通过新的root/design绑定检查，必须先登记与当前subject/design一致的r2。主 Agent随后告知1b34732及真实r2已准备至EXPERIMENT_PLAN_VALIDATED；本审核没有把这些消息当作自己对该后续元数据提交或真实root的验证。

5. 数学与最终结论的边界

实际 `git diff` 确认本轮公共 core 与2016/2015 scientific producer/checker 没有改动。前轮已经审核的时间可见性、remaining-time分母/样本单位、55A条件插值与LOCO区别、非校准模型范围及独立数值验算限制仍适用。本轮没有重复执行科学模型或更改指标定义，也没有以原测试中的策略统计替代新的独立Validation。

本审核实际调用 initialize_case **0**、真实 model **0**、真实 independent checker **0**、真实 Final **0**。没有实际结果审核，不能证明任何真实误差、精度、checker残差或Final结论。

本轮限定PASS支持将10e8b038作为经运行前差异审核的实现subject，按版本化登记合同继续既有授权流程。真实r2登记一致性、准备完成、真实执行预算、逐问结果和后续独立结果审查仍须依其实际证据确认。
