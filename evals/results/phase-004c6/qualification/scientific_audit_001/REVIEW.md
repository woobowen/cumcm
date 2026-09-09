# RC9 条件预测与指标数学语义初步独立审核

审核对象：Git `7ed9dd18c35bed79cc9dd4e96926fef9b35b7e81`。本回执是原生只读子 Agent 的初步数学审查，不是正式技术 Gate 或项目接受决定。

结论：该 subject 的剩余时间误差主公式、同实体前缀可见性和条件预测/未来精度分离具有正确实现；但尚不足以判定 M3 科学语义闭合。逐样本指标绑定和 ROOT_MEAN 量纲存在已实际复现的缺陷；选择时间可见性缺少表达；中立 fixture 的预测扰动数值与其声明不一致。

## 方法、范围与可见性

- 先执行 `ls -la`，确认项目已有 `.venv`；所有 Python 探针使用 `.venv/bin/python`，未新增依赖或修改配置。
- 读取指定提交中的 Skill/test 局部 AGENTS、RC9 science contracts、`cumcm_case.py` 四个目标函数及其必要邻近定义/调用点、两个 fixture、指定 integration test 源码、任务书 M3。
- `math_probe.py` 用 AST 从冻结 Git blob 中提取八个列明的函数定义，只运行指标/条件/时间设计局部校验；路径、读取、哈希辅助函数仅处理审核缓存内的合成输入或内存映射。没有 import 整个运行器，没有执行 producer/checker 的 main、公共 CLI、真实题、Final 或 full CI。
- 另用 `fractions.Fraction` 独立推导仿射终点、相对误差和扰动数值。此处的“实际复现”指局部函数/算术探针，不代表已执行公共入口端到端复现。
- 可见范围偏差：首次任务书定位命令 `rg -n -A 125 -B 8 'M3|科学'` 过宽，显示了任务书中旧 Validation 结果摘要与其他章节。已即时向主 Agent 披露并获要求如实保留；没有打开本轮 Development/历史结果文件、其他审核文件或 state。本审核不宣称对任务书历史摘要完全盲化。
- 读取了候选名称 CAND/BASE 和 fixture 人工偏置规则；对这些模型身份不盲。没有参考主 Agent 对数学问题的结论来生成初步发现；初步发现之后主 Agent 告知将修复其中问题，审核对象仍保持原 subject。

## 分项结果

### SCI-001：逐条样本身份、起点与目标真值未形成独立交叉绑定（高，局部已复现）

证据：`cumcm_case.py:1788–1808` 独立检查历史 sample_ids 声明，`1825–1853` 检查 producer/checker 的指标样本彼此相等并重算总分，但没有把每条样本映射至冻结时间索引。`rc9_science_checker.py:73–89` 仅按列表位置比较预测终点及预测值；`110` 将 producer 的 metric_samples 原样复制到 checker 输出。

实际探针：将两条指标样本 ID 替换为不在设计中的 ID，`metric_output_binding_codes` 返回空集合。进一步保持两条预测终点均为 21、真实终点均为 20，把原点从 4、8 改为 0、220/23：

`原 MAPE = 50 × (1/16 + 1/12) = 175/24 %`

`改后 MAPE = 50 × (1/20 + 23/240) = 175/24 %`

实际计算中，改后 binding codes 仍为空、checker 当前比较方式对应的终点残差与总分残差均为 0。这不是浮点公差问题；分母已经变为另两个数，均值却精确相同。当前独立总分一致不足以保证每条样本的分母、真实终点和身份正确。

建议：根据稳定 sample_id，从冻结 design/index 独立生成 expected origin、entity、target、observed_end_time、单位及完整样本集合，再逐项核对；checker 输出自己重建的样本，不回填 producer 的原列表。数值字段可以使用冻结公差，身份与时间索引关系不能只依赖汇总值。

### SCI-002：ROOT_MEAN 的组合校验允许错误量纲（高，局部已复现）

证据：`cumcm_case.py:1526` 允许 ROOT_MEAN；`1549–1554` 只要求 SQUARED_ERROR 使用 ROOT_MEAN，没有反向限制；`1619–1622` 对任何 ROOT_MEAN 都执行开方。

实际探针：`ABSOLUTE_ERROR + ROOT_MEAN + unit=min` 的定义校验返回空集合。单样本绝对误差为 4 min，输出为 2，并继续标为 min。实际量纲为 sqrt(min)。对照 `SQUARED_ERROR + ROOT_MEAN` 正确输出 RMSE=4 min。

建议：在当前支持范围内，ROOT_MEAN 仅允许与 SQUARED_ERROR 组合；若要扩展其他开方统计量，必须另行定义正确量纲，不能沿用原目标单位。

### SCI-003：选择所消耗标签的可见时间未被表示（高，设计缺口；局部时间校验已复现）

证据：M3 要求 feature、变换、拟合、选择的可见时间均受约束。`cumcm_case.py:1675–1688` 只遍历 feature/preprocess_fit/model_fit 三类；指定 fixture/test 的历史验证标签 A-end 在 20 可见，而待预测 B 的 origin 为 12（test `53–77`）。

实际探针：该时间关系被 `validate_temporal_design` 接受。若最终候选依据 A-end 历史误差选择，则在 B 的 origin=12 不能知道选择结果。仅冻结代码或验证“拟合只读历史前缀”不能消除选择阶段的时间泄漏。

限定判断：本次未执行或完整审查实际选择控制器，故不声称已证明任意真实运行发生泄漏。已证明的是时间设计局部检查不表达这一必要前提；指定正例本身不能支持“全流程仅使用 origin 当时信息”的强结论。

建议：冻结 selection_observation_ids/候选选择时间边界并逐 forecast origin 校验；或明确该输出是已知历史开发分析，不宣称它重现当时可部署预测。不能把同实体历史合法性扩大为选择标签可跨时点使用。

### SCI-004：中立 fixture 的敏感性扰动只改指标，没有对应目标量复算（中高，独立算术已复现）

证据：`rc9_science_model.py:151–160` 声明 `FORECAST_END_PLUS_ONE_OR_DEMAND_PLUS_ONE`，但 result 固定为 `values["metric_a"] + 1`，并标注为确定性输入复算。checker 未重算该 robustness_evidence。

实际算术：仿射轨迹的 endpoint=20，历史 origin=4、8。预测终点增加 1 min 后，MAPE 增加 `175/24 = 7.291666666666667` 个百分点；fixture 却加 1 个百分点。优化需求加一在该玩具模型下可以是目标量加一，但预测时间加一不能沿用同一数值规则。

影响：此 fixture 可作为协议形状示例，不能把该字段当成已独立验证的预测敏感性结果。公共 E2E 完成断言没有针对这一扰动数值做验证（本次只读测试源码，未运行 E2E）。

建议：分别扰动原始目标/输入，重新计算每条样本误差和聚合，再由 checker 独立重算；或准确标明该数据仅为合成协议占位，不把它计入科学稳健性成立。

### SCI-005：样本单位、区间内容和近零处理的支持范围需限制（中，局部已复现/范围审查）

1. `sample_unit` 目前仅作为非空字符串校验，计算始终按行等权。探针声明 sample_unit=entity，给 A 两个 origin（10%、20%）与 B 一个 origin（100%），仍输出行均值 43.3333%，不是实体等权 57.5%。现有 fixture 明确使用 historical_origin 时，其行均值口径正确；不能因此声称已支持实体等权聚合。应限制可用 sample_unit 或显式实现实体分组/权重。
2. `MODEL_SENSITIVITY, calibrated=false` 在没有 bounds、扰动集合或敏感性复算时，条件预测局部函数仍接受。当前检查可以约束标签及禁止概率校准升级，不能单凭标签证明敏感性范围内容。支持模型离散范围、bootstrap 参数区间或校准预测区间还需要新契约与对应证据；当前不能宣称这些类型已获支持。
3. 真正零分母被 REJECT 正确拒绝；EXCLUDE_WITH_COUNT 保留剔除 ID，全部剔除时拒绝聚合。对于真实剩余时间 `1e-12`、预测 `1e-6`，当前输出 `99,999,900%`，不使用临时 epsilon，算术本身正确。但契约没有显式近零阈值/切换绝对误差规则；需要这种处理的任务必须预先扩展，不能把当前 exact-zero 规则解释为已经解决近零稳定性。

## 已成立的数学性质与有限支持

- 对 origin=90、prediction_end=101、observed_end=100，实际重算 remaining relative error=10%，elapsed relative error=1%。公式真实区分了目标分母；排名相同不能替代口径相同。elapsed 路径以统一零点计算终点时间，若输入是绝对时间戳，仍需外部明确初始零点语义。
- 同实体 prefix 允许合法历史数据；未来标签放入 feature 列表实际返回 `RC_TEMPORAL_FUTURE_INFORMATION:feature_observation_ids`。源码同样检查 preprocess_fit/model_fit 的 observed_at 和 available_at；本次没有重复执行这两个 usage 的探针，指定 integration test 源码包含相应参数化负例。
- 新实体任务对 fit_entities 与 target_entities 重叠实际返回 `RC_TEMPORAL_NEW_ENTITY_GROUP_OVERLAP`。目前指定测试只证明负例，未提供合法新实体迁移的正向数值证据；跨条件插值/外推也未在此局部设计中单独表达。
- 条件预测 baseline 局部接受；把 empirical_accuracy_required 置 true 并同步证据 spec hash 后，实际仅返回 `RC_PREDICTIVE_EMPIRICAL_ACCURACY_UNVERIFIED`。要求契约也禁止把 future_truth_field 放入 minimum_data_fields（`cumcm_case.py:413–427`）。这支持“未来真值不是条件预测输入”，同时保留“未来精度尚未实测”的界限。
- 独立有理数 OLS 对 noiseless affine 轨迹重算 slope=-1/10、终点=20，origins 4/8/12 的 remaining 分别为 16/12/8。producer 中心化 OLS 和 checker 正规方程在这一假设下表达同一数学模型；不能由此推出对未知未来真实轨迹的准确率。
- 两个 validation origin 共用实体 A 的同一终点标签。它们是两个历史状态起点误差，只有一个已观测终点实体；不能把 included_count=2 当成两个独立实体或两个独立泛化试验，也不能据此估计独立样本意义的置信区间。
- 程序复算可以支持指定输入下的代数一致、局部约束和正确口径的已观测历史误差；不支持模型机制真实性、未建模工况持续性、未知未来精度、概率校准或题外泛化。MODEL_SENSITIVITY 更不能因算术复算一致而升级为校准预测区间。

## 未覆盖与收口边界

未运行指定 integration tests、公共 controller/Final、full CI，未读取实际题输入/Development 数值/其他审核/state，未检查本轮修复后 subject。未审查实际候选选择全流程、所有 schema/helper 或 arbitrary 模型的实际数据消费隔离。对排序、奇异 OLS、噪声/异常值/工况变化、合法新实体正向路径、跨条件外推没有完整测试证据。报告没有代替主 Agent 修改任何 formal state、决定或接受结果。

本次无安装、无依赖或配置变更。所有新增文件仅在 `.cache/pr12-rc9/scientific-semantics-review-001/`。修订 subject 后应对 SCI-001/002 跑有真实身份/分母反例的定向测试，并对 SCI-003/004 给出实际可核验边界；本回执不授予任何新 subject 接受资格。

## 本地证据文件

- `math_probe.py`：可重放的局部函数及独立算术探针。
- `math_probe_results.json`：最后一次实际运行的分项数值/错误码；源码 SHA256 为 `c685698cc633b75b43e07d555f3da41c50cf9092128d34280665f5d04c12aee4`。
- `command_log.json`：实际源码读取、定位和两次探针运行的命令及原输出；保留过宽任务书读取与第一次 probe 的原始输出。
- `input_manifest.json`：指定 Git 输入 blob 与 SHA256，及审核写入文件的身份。
