# 第三轮运行前协议与科学核验

固定 subject：`ee0159c68aaeb1a60eba947ad73f1ed0de8b4e2a`。本轮为只读运行前审查：**发现一个已局部复现的正常调用阻断（Claim 缺 claim_strength），另有两项应在启动前闭合的预算/数据排列条件。未执行任何真实题 producer、checker、Final，不能称真实 Development 数值已核验。**

主 Agent 已告知正在修订若干问题；本回执只评价该 subject，不把未提交变更或主 Agent 自述计作证据。

## 实际范围与方法

首个命令为 `ls -la`，确认仍使用项目 `.venv`。读取固定 Git blob 的准备器、core 相关函数与普通调用上下文、公共完成 controller、两题 code/design 的定向差异；没有打开实际 raw、已生成 Development 结果、project/case state 或其他审核文件。本轮未进行安全测试、越权探针、网络访问或并发代理派生。

`protocol_probe.py` 使用 AST 提取指定函数，以内存中的模拟需求/plan/output、合成 workbook provider 和本审核目录的临时计数账本核验正常接口。没有导入完整运行器或调用真实模型 main。模拟的 state/Run 描述明确是单元测试输入，不是项目状态或实际实验事实；仅预算测试在审核目录下写入 synthetic_budget_case/state/。其计数代表合成预算预留，真实数值程序启动数为0。

预算探针保留一次性账本；重放应把脚本复制到新的空审核目录，避免复用已耗尽的合成账本。命令和返回在 command_log.json，完整探针结果在 protocol_probe_results.json，源码与产物 hash 在 input_manifest.json。未安装依赖或修改共享文件。

## 前两轮问题的保留与修复

- SCI-001 至 SCI-004 的核心/中立 fixture 修复相对上轮 subject 未被撤销。本轮检查定向 Git diff，没有重新执行已通过的上一轮数学探针，也未运行中立 E2E。
- 2016 checker 新增对 `Q1.per_current_MRE[str(i)]` 的九电流逐项比较，并在丢弃辅助 q1_metrics 之前，把五个 `remaining_at_9_8V_min` 按电流键逐项比较（新 checker `164`、`284–291` 附近）。上一轮所报主要输出覆盖缺口在源码中闭合；本轮未验证真实数值公差是否通过。
- 2015 checker 新增每 city/body 的原始行数一致、selected jd 唯一和 jd 全集相等检查（`177–181` 附近），补上重复合法时点不能代表12个参考位置的缺口。
- 2016 producer 新增限制：前缀平移是固定预测起点下的拟合输入扰动，不是整体时钟平移。该解释与实际减固定 last_time 的计算一致。
- ee0159c 中2016 checker 的逆函数仍是全区间二分，2015 checker 仍从输出读取扰动参数而未强制五组标签/参数全集。这两项上轮已记录的限制尚未在本 subject 闭合；不据此声称实际数据数值错误。

## R3-01：proposal 缺 claim_strength，正常预测 Claim 必然被拒绝（已局部复现，运行前 blocker）

`scripts/prepare_phase004c6_development.py:500–529` 构造 Claim 和 CONDITIONAL_ESTIMATE 谓词，但不写 claim_strength。公共 core `validate_conditional_prediction:1878–1879` 要求 `claim_strength == "BOUNDED"`。

本轮实际提取并执行该 subject 的 `propose()`，全部外部依赖使用内存合成数据，捕获其生成的原 Claim，然后交给该 subject 的实际条件预测函数（上游科学设计/哈希依赖由显式模拟满足，测试只隔离本内容约束）：

| 合成需求 | 原 proposal 的返回 | 仅增加 claim_strength=BOUNDED |
|---|---|---|
| REQ-Q2 | RC_CONDITIONAL_PREDICTION_SCOPE_INVALID | 无错误码 |
| REQ-Q3 | RC_CONDITIONAL_PREDICTION_SCOPE_INVALID | 无错误码 |

这证明准备器与 core 的对象内容契约不匹配；不需要真实数值运行即可发现。应在统一新 subject 修复后再开始昂贵计算。

对准备器的42个直接 `core.*` 调用做了 AST 函数签名匹配，参数数量、关键字和位置均匹配，包括 initialize_case、select_development_candidate、build_captured_run_manifest、write_json、artifact 等。因此这里是返回/输入对象的必填内容缺项，不是这些调用的 Python 参数签名错误。动态数据、继承父 artifacts 的完整 schema 一致性未由该签名检查证明。

## 指标与时间索引的运行前核对

1. 准备器实际 `metric_definitions(2016/2015)` 全部通过 core `validate_metric_definition`。2016 的 Q1/Q2/Q3 MRE 都为 `unit="1"`，Q3 remaining 为 `min`，与当前 producer 的未乘100数值一致。Q1/Q2 是按电压网格的 elapsed-time SCALAR 相对误差；Q3 才是 REMAINING_TIME/TRUE_REMAINING_TIME。2015 altitude RMSE 是 SQUARED_ERROR+ROOT_MEAN，最大绝对误差是 VALUE+MAX，单位 degree；事件数/日历数用 count。
2. `prepare:90–162` 明确 `10000*state+elapsed` 是状态顺序坐标，不是日历，并检查每个 elapsed 在 `[0,10000)` 内，因此更早完整状态的坐标早于下一状态。feature 列表是目标 prefix，fit/preprocess 列表是更早状态加目标 prefix。没有制造 state3 终点，forecast 使用 target_event、null target_time 和 null target_observation_id。
3. 用纯内存合成 workbook 调用实际 temporal_index，生成六个 validation 和一个 forecast；再用 core 实际 validate_temporal_design 检查，错误码为空。合成 forecast origin=30035、当前前缀6行。原始 workbook 未打开，source hash 使用显式占位，因此该结果只证明构造器与局部验证器在合规合成数据下可对接。
4. condition_design 的55A查询与七个 LOCO 电流标识分开；55A查询的 origin=0是电流曲线的 elapsed 坐标，不代表“所有历史电流数据在绝对时间0可见”。core 的时间选择约束针对状态延续轴，当前 condition-query 仍依赖“参考曲线已知”的冻结假设，不能解释为逐日可部署预测审计。

### R3-02：索引的电压过滤与模型的前N行切片需要排列前提（运行前条件未显式断言）

准备器 `124` 使用过滤 `voltage>=cut`；2016 producer `378–379`/checker 对应逻辑使用满足阈值的行数 size，再取 `[:size]`。只有电压按行非增且状态列/缺失模式对齐时，两者才是同一集合。

纯数学反例：电压行 `[10.0,9.6,9.95,9.85]`，cut=9.9，索引取位置 `[0,2]`，模型取前2行 `[0,1]`。本轮未读取真实 workbook，不声称它无序；但 ee0159c 的准备器没有显式确保这一必要条件。建议实际数值运行前验证附件2电压非增、状态列完整性、有效前缀/行对齐以及非空切点；不可仅依赖模型和 checker 复制同一 count 算法。

## selected domain gate 与执行预算

`require_selected_scientific_domain` 对真正被该 Run 支持的选中 requirements 同时要求 feasible=true 与有限、满足方向/公差的 constraint_residuals。实际纯函数例中，合法记录接受，feasible=false 或超出约束的残差均拒绝 `RC_FINAL_SELECTED_DOMAIN_NOT_VERIFIED:R`。该 gate 在 prefinal preparation、重复 prefinal revalidation 和 Final receipt 验证出现；不会要求所有未选候选都满足被选结果的科学域，这个范围合理。

其作用是选中结果的域/可行性门槛；不是误差较小即完成，不替代其他独立 recalc/metric 检查，也不建立未来精度或全题解释有效性。

`consume_start_budget` 把 model/checker/Final 分别限制为最多4/4/1，checker 的独立 replay 也计数。合成计数探针前四次 checker 预留接受，第五次拒绝 `RC_EXECUTION_BUDGET_EXHAUSTED:independent_checker_starts`。既有4/4/1上限未放宽。

### R3-03：Final 预算与 checker 余量未联合预检（运行前协议缺口）

Final 路径 `6433` 先扣 final_starts，然后写 AUTHORIZED/STARTED；直到逐 Run 准备实际 checker 时 `6468` 才扣 independent_checker_starts。合成纯预算函数实测：checker 四次已耗尽后，final_starts 的预留仍接受。结合源码可知，此时 Final 会先形成 STARTED 再因 checker 无余量失败，没有任何 Final checker 真正启动。

本轮没有调用 evaluate_scientific_final 或模拟其完整执行，只验证计数函数与静态先后关系。它不会导致超预算启动，但会消耗唯一 Final 槽并把“不能开始”写成开始后失败。建议在 AUTHORIZED/STARTED 前确认余量足以覆盖全部 selected_run_ids，预算不足保留拒绝请求。预算事件在子进程启动前扣除，执行次数仍应依据实际 capture 区分，不能仅凭计数账本宣称程序已执行。

## 普通完成路径与预算可达性

- prepare 只推进到 EXPERIMENT_PLAN_VALIDATED；正常模型 CLI 前还必须经公共 advance 到 RUNNING。propose 则要求 RUNNING 下已存在合法开发 capture。它会生成供 controller 验证的对象，不代替后续科学接受。
- 两个 producer 启动后，`propose` 再运行公共 `finalize_fresh_c_validation.py --check-code models/check.py` 的同进程路径，可在 controller 内执行两次开发 checker，重用该进程的验证缓存，再运行一次选中 Final checker；正常合计 checker=3，留一预算供明确的额外复算。
- 这一计数是源码路径推导，未执行真实路径。`verify_scientific_check` 的缓存仅限进程，跨 CLI 重验会启动并计数；不可把它当永久缓存。若先独立执行开发 checker，又向 controller 提供同一 --check-code，会遇到已有输出拒绝；若从多个进程反复验证，则可能耗尽4次预算。运行命令必须与已选路径一致。
- 比较选择、语义/聚合和必要 robustness 接受在 prepare_final_selection 之前；selected domain 再约束 Final 前置。当前 missing claim_strength 会在这一链前部阻断，必须先修复。

## 未覆盖与最终限定

未运行完整 prepare/propose/controller 生命周期、已有中立 pytest、真实输入下两模型的耗时/公差/数值和 Final。未读取父 artifacts、registration、实际 case state；因此继承字段、候选集合、source scope、父数据充分性及最终 code/input registry 的一致性仍需在新 subject 的运行前准备中实际检查。当前 subject 的 prepare 会把依赖文件/预算/设计哈希冻结，但不是本次已执行事实。

未核验主 Agent 正在修订的 claim_strength、排序断言、checker 最后下穿实现、五扰动全集或 Final 余量预检。收到统一新 subject 后才可独立判断这些修复。报告不是 Formal Gate、接受决定、多数票或真实开发数值通过记录。
