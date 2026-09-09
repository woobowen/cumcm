# 触发式经验卡

版本1.0.0；当前适用core RC10。所有卡均为 **LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE**。只按当前问题触发读取，未触发不通读历史。来源中的旧拒绝/错误是历史事实；现行规则以RC10为准，不能复活过度门禁。以下中立例子不是历年题答案或固定参数路由。

## L01 主问覆盖

触发：需求表字段齐全但仍无法回答原问。相关模块：M02 M05 M13 M14。

来源/版本：[a3d2279的GOALS.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/GOALS.md)；源文件sha256 `3a00dc22cee7a4e0d03ad97864189d1b742c8f234508ca50f9ab3a6e2d7b9eea`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：旧数据不足终局说明：结构成功不能补足主问的实际数据。

当前应看证据及可检验动作：从每个PRIMARY原句追到输出和可用数据，列支持/不足。

中立例子：原题要求两类对象比较，数据只含一类时逐项标缺口。

合法反例/不适用：合法单问scoped-child可交局部，但不代表全题。

不能推出：存在同名字段不推出科学支持。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L02 缺失、零与连接

触发：缺值处理或多表连接改变样本数。相关模块：M05 M08。

来源/版本：[a3d2279的docs/modular_workbench/MODULES.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/docs/modular_workbench/MODULES.md)；源文件sha256 `0b5a53a0364522666f8773134554729be4de2ef5ad4927f3714de4e7662e4fc3`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：RC10数据审计职责要求实际检查主键、重复、缺失和单位。

当前应看证据及可检验动作：独立算连接前后行数、有效计数和总量；零与NA分别计。

中立例子：两行主表连到三条明细可能重复计算主表金额。

合法反例/不适用：一对多明细总和是原目标时，增加行数本身合法。

不能推出：行数增加不必然是错误；零不能自动删。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L03 测点与独立样本

触发：同对象多次记录被当多对象证据。相关模块：M05 M08。

来源/版本：[a3d2279的tests/integration/test_rc9_science_semantics.py](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/tests/integration/test_rc9_science_semantics.py)；源文件sha256 `09e7dbbe570e4d968cafc61f95457fa887be92ddb943677780f812dd2ba0e522`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：当前可见性设计显式区分entity与observation；不可把测点数当外部独立样本数。

当前应看证据及可检验动作：统计实体数、起点数和测点数；按研究目标解释相关性。

中立例子：单设备多次读数可拟合轨迹，但不是多设备验证。

合法反例/不适用：任务就是同对象轨迹估计时可使用其多测点。

不能推出：样本行数不证明独立样本深度。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L04 同实体前缀与未来

触发：预测出现同一实体重叠或未来信息。相关模块：M05 M08 M09。

来源/版本：[a3d2279的tests/integration/test_rc9_science_semantics.py](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/tests/integration/test_rc9_science_semantics.py)；源文件sha256 `09e7dbbe570e4d968cafc61f95457fa887be92ddb943677780f812dd2ba0e522`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：RC9/RC10纠正粗粒度实体一律排斥；现行以observed_at/available_at及任务目标判断。

当前应看证据及可检验动作：逐feature/preprocess/model_fit ID核origin前可见；未来target只作评价。

中立例子：起点10可用时刻8且8已发布的记录；时刻12或起点后发布则不可用。

合法反例/不适用：新实体迁移目标仍须实体隔离；同实体前缀允许规则不适用。

不能推出：不能复活“同实体信息全部违规”。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L05 开发、Final与条件预测

触发：把开发指标当Final或缺未来标签。相关模块：M08 M10 M12 M13。

来源/版本：[a3d2279的HANDOVER.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/HANDOVER.md)；源文件sha256 `0e0489206845f70d6fe151ec4430efbab2c436135a361ffeb403ffc1c9d8c9cf`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：旧Final顺序失败与条件结果边界保留；后来RC10允许按适当模式独立核验。

当前应看证据及可检验动作：查选择/稳健性与Final实际时间及ledger；条件预测单列未观测未来真值。

中立例子：条件公式可给未来量的估计，真实准确性尚未知。

合法反例/不适用：题目明确要求经验精度时，独立算术不能补标签。

不能推出：不强制所有预测先有未来真值，也不把条件估计升级精度验证。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L06 指标的目标与分母

触发：同排名掩盖指标语义不同。相关模块：M02 M08 M09。

来源/版本：[a3d2279的tests/integration/test_rc9_science_semantics.py](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/tests/integration/test_rc9_science_semantics.py)；源文件sha256 `09e7dbbe570e4d968cafc61f95457fa887be92ddb943677780f812dd2ba0e522`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：remaining与elapsed错误即使排名一样仍不同；冻结需覆盖口径。

当前应看证据及可检验动作：用逐样本记录独立重算目标、分母、单位、聚合与零分母政策。

中立例子：结束时刻误差除剩余时长，与除已运行时长不同。

合法反例/不适用：研究目标就是累计时长时，另一分母可合法但须重新定义。

不能推出：排名一致不推出评价正确。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L07 完美小样本

触发：合成或少量数据近零误差。相关模块：M09 M13。

来源/版本：[a3d2279的evals/results/modular-workbench-001/original_analysis.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/evals/results/modular-workbench-001/original_analysis.md)；源文件sha256 `6ed3bc7aa4fe9554b3ed60abdb11e1c92730a5d1789fcc5d26e4e166a762bdc1`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：既有严格仿射原创例说明精确算术仅限所声明生成机制。

当前应看证据及可检验动作：查生成机制、实体/起点数、是否含噪声；逐条限定范围。

中立例子：人为直线样本零误差可验证公式实现。

合法反例/不适用：目标仅为代数恒等式证明时，不能要求真实抽样泛化。

不能推出：小样本完美不推出外部效度。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L08 可靠基线

触发：候选改进幅度被当成功必要条件。相关模块：M06 M07 M10。

来源/版本：[a3d2279的docs/modular_workbench/MODULES.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/docs/modular_workbench/MODULES.md)；源文件sha256 `0b5a53a0364522666f8773134554729be4de2ef5ad4927f3714de4e7662e4fc3`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：RC10候选/选择职责与冻结规则允许选择有效参照；旧纯预测延迟示例不成为通用baseline。

当前应看证据及可检验动作：核同一目标/信息/资源；至少找一个简单方案可最优或平局的中立输入。

中立例子：整除需求下简单整箱购买可与精确求解相同。

合法反例/不适用：有严格额外约束使简单方案不可行时不能强行保留为公平参照。

不能推出：不把候选必须获胜设为Gate。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L09 可行与最优

触发：求解成功或有可行方案就称全局最优。相关模块：M06 M09 M12 M13。

来源/版本：[a3d2279的tests/fixtures/workbench_water_checker.py](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/tests/fixtures/workbench_water_checker.py)；源文件sha256 `54f124c119699166a5686a289de9daef84431b342306d1e5e4ab6dbdefee87e0`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：独立checker以正价格可行上界限制枚举并闭合界。

当前应看证据及可检验动作：独立重算约束/目标；另验证上下界范围和差，区分局部/模型内最优。

中立例子：可行成本14但独立可行成本12时，前者不是最优。

合法反例/不适用：只要求可行计划的题不强加最优证书。

不能推出：模型内最优不推出现实效果。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L10 来源与生成方法

触发：source真实被误当所有推导都实测。相关模块：M03 M05 M13。

来源/版本：[a3d2279的GOALS.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/GOALS.md)；源文件sha256 `3a00dc22cee7a4e0d03ad97864189d1b742c8f234508ca50f9ab3a6e2d7b9eea`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：旧数据缺口与条件仿真范围提示：来源、生成过程、结论强度要分别记录。

当前应看证据及可检验动作：标每个量为实测/推导/仿真/假设；追到来源字节与当前Run。

中立例子：用实测输入进行假设情景模拟，其未来输出仍是模拟。

合法反例/不适用：纯数学构造无需伪造实测来源。

不能推出：真实引用或hash本身不证明科学结论。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L11 区间含义

触发：把扰动范围叫置信或预测区间。相关模块：M11 M13 M14。

来源/版本：[a3d2279的evals/results/modular-workbench-001/original_analysis.md](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/evals/results/modular-workbench-001/original_analysis.md)；源文件sha256 `6ed3bc7aa4fe9554b3ed60abdb11e1c92730a5d1789fcc5d26e4e166a762bdc1`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：既有需求加一属于一点敏感性，没有频率覆盖或校准。

当前应看证据及可检验动作：列区间生成机制/参数集/概率含义；若主张覆盖率需独立校准数据。

中立例子：参数上下浮动得到的结果带是情景范围。

合法反例/不适用：纯区间算术的确定性包含界不需要概率校准，但不能叫置信区间。

不能推出：有上下限不推出覆盖概率。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。

## L12 多问、场景与阅读血缘

触发：上游变化、图表摘要或附页版本错位。相关模块：M04 M10 M13 M14。

来源/版本：[a3d2279的tests/integration/test_modular_workbench.py](https://github.com/woobowen/cumcm/blob/a3d2279b439a332239bab2ff75362bb070100042/tests/integration/test_modular_workbench.py)；源文件sha256 `360728febaad7ff522c5bd45a29b21aa33204d402f143835fb467e5ddd3f4594`。当前资料版本1.0.0，适用RC10。离线来源含义见本卡摘要，不宣称附有源文件全部字节。

过去问题/来源摘要：当前测试传播STALE并拒绝漏问整体交接；实际网页另指出符号与占位statement阅读不足。

当前应看证据及可检验动作：对每问Claim/Run/输出字段/hash、单位、scenario、revision、图表数据逐一核对。

中立例子：旧图沿用新摘要会断开证据；需要回到同一有效Run。

合法反例/不适用：单独中文阅读附页可补说明，不改旧结果；附页必须DERIVED_READING_VIEW。

不能推出：文案改善不证明模型性能或允许重启Final。

标记：LESSON_OR_HEURISTIC_NOT_AUTOMATIC_GATE。
