# 第二轮独立数学核验：8f5ad25

Subject：`8f5ad2514454cad8dd830c31fd1c4eb3aed9b0b7`。结论：SCI-001/002/003 的原有局部反例已被拒绝；SCI-004 的中立 fixture 已改为按终点扰动真实重算。2016 新适配器的六起点剩余时间指标和前缀拟合逻辑在本轮源码/合成算术范围内成立。但仍有两项具体 checker 覆盖缺口，以及需明确的敏感性与逆函数边界，不能把本回执当成整题完成或 Formal Gate 接受。

## 核验方法

- 首个命令为 `ls -la`；使用已有 `.venv/bin/python`，无安装和配置变更。
- 所有代码从固定 Git subject 读取；未切换到主 Agent 并发修改的工作树代码。只读取核心指定函数/调用上下文、中立 fixture/test 的定向 diff、两个指定 Development 的 code 与 development_design.json。没有读取原题、原始数据、实际模型结果、其他审核或 state。
- AST 提取核心六个无运行器副作用的函数，以及 2016 checker 的五个纯数值辅助函数；依赖注入仅处理审核目录中的合成索引/内存 plan。另用标准库 Fraction 做独立精确算术。没有导入整个 producer/checker，没有执行真实题、main、Final、公共 CLI 或 pytest。
- 2016/2015 的数字例子均为审核者构造，绝非实际题结果。实际读取/计算命令和工具返回保存在 command_log.json；最后完整数值输出在 math_probe_results.json。第二次探针的终端输出因 token 限制截断，JSON 文件为完整输出。
- 继承上一轮已知发现，不重新声明身份盲；本轮没有新增超范围结果暴露。对子 Agent 自身的审核目录有写权，共享代码/Git/state 均未写入。

## SCI-001 至 SCI-004 的处理

| 项目 | 新版证据 | 本轮结论与实测 |
|---|---|---|
| SCI-001 时间样本交叉绑定 | core `1887–1959`：新增 case_root、冻结 sample 集合、origin、observed_end_time、time_unit 绑定；中立 checker 比较每条非预测值字段 | 原合法样本返回空错误码；改 ID/少样本分别返回 `RC_METRIC_TEMPORAL_SAMPLE_COVERAGE_INVALID`，原“改分母但同均值”及改真实终点返回 `RC_METRIC_TEMPORAL_SAMPLE_MISMATCH`。此反例已闭合，范围为这一路时间指标；不能延伸为所有 SCALAR 指标的样本全集已经绑定。 |
| SCI-002 ROOT_MEAN 量纲 | core `1551–1556`：ROOT_MEAN 仅允许 SQUARED_ERROR | 实际返回 `RC_METRIC_AGGREGATION_UNIT_MISMATCH`；合法 RMSE 的 4 min 单样本仍输出 4。原缺陷已闭合。 |
| SCI-003 选择标签的时间可见性 | core `1717–1723`：所有验证标签 available_at 不晚于最早 forecast origin；中立例 B 的时间原点后移，未知终点改为 target_event | 合法历史局部接受；标签 available_at=200、forecast origin=112 实际拒绝 `RC_TEMPORAL_SELECTION_LABEL_NOT_AVAILABLE`。对“共享候选由这些历史标签选择、随后预测”的当前结构合理且保守。未验证逐 forecast 更新选模或更一般嵌套滚动选择协议。 |
| SCI-004 中立预测扰动 | fixture producer 先把每条 predicted_end_time 加 1，再重算 relative error；checker 使用自己的 ends 重算同项 | 独立精确算术确认 origins=4/8、真终点=20、预测终点由20到21，误差应为 `175/24%=7.2916666667%`，与新版源码公式一致。未执行 fixture main 或其 E2E，结论是源码与算术一致。 |

此外，core `1861–1870` 已要求 MODEL_SENSITIVITY 至少两个有限 variant_values，且上下界等于其最小/最大值；`1871–1877` 要求 checker 返回同一预测证据。这修正了单纯标签无数值的原限制，但复核强度仍取决于 checker 是否真正独立计算这些数值。

## 2016 的数学口径与信息边界

源码缩写：`produce.py` 和 `check.py` 均位于 `evals/results/phase-004c6/CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006/code/`。

1. **六个状态×起点，不是六个独立电池。** producer `375–393` 对 states 1、2 各取 9.95、9.85、9.765 V 三个切点；`436–444` 使用 `mean(abs(predicted_end-observed_end)/(observed_end-origin))`，得到无量纲比例。checker `250–282` 独立重建同六条记录及分母。design `103–114` 明确是单电池相关起点的 Development selection。不能将该均值称为无偏外部泛化误差；选择后再报告同六点误差也没有恢复独立验证性。
2. **拟合使用更早状态和当前前缀。** producer `376` 的 reference 只含 `refs[:, :state]`，`379` 的 target 是当前状态 `[:size]`；transfer `125–131` 拟合时也只使用 reference 的相同前缀。更早状态的完整尾部可作为已经结束状态的信息，当前目标尾部只用于计算验证误差。checker 的手算回归 `94–106` 与历史循环 `253–258` 按同一可见范围重建。
3. **实际合成验证。** 构造两状态×三起点，用有理数 OLS 独立复算均值为 `387004123/3174132780 = 0.12192436480240754`。在每一切点之后任意修改目标尾部，提取的 checker 回归系数与预测保持不变；`state*10000` 同时加入 origin/真终点/预测终点会在 remaining 误差中抵消。该 offset 是人为顺序编码，不能替代实际观测时间来源。因未读取 workbook 或 root 准备器，不能验证真实列序、电压排序、索引 available_at 或 10000 间隔是否覆盖真实时长。
4. **55A 条件插值与 LOCO 不同。** producer `95–122` 只取电流左右邻居；BASELINE 在线性电流和时长上插值，另候选使用 log-current 权重与几何时长。`159–172` 的 LOCO 去掉目标 current 的 polynomial，虽然 durations 字典仍有该键，实际 surface 只读取剩余邻居时长，没有使用被留出电流的时长。55A 正式条件曲线用50/60A；例如 LOCO 50A 用40/60A。合成时长100/80 min 对应线性55A时长90，log/geometric时长88.9896395534。两者是条件模型值，不是55A实测误差；design 已正确声明这一区别。
5. **模型范围并非校准区间。** producer `479–489` 的上下界是三个参考状态分别拟合所给 remaining 的 min/max，并有 calibrated=false、independent_battery_count=1。checker `245–249` 独立重算三个数，`355–357` 绑定 variant_values；core 再检查边界。此证据可支持“所枚举参考选择导致的模型范围”，不能支持概率覆盖率、bootstrap 参数置信区间或新电池预测区间。均值参考模型的中心值也不因三个变体范围而自动获得概率含义。

## 2016 checker 的具体缺口与限制

### R2-2016-01：五个 Q1 剩余时间及逐电流 MRE 输出未被逐项核对（需修复）

checker `169–170` 计算了30–70A在9.8V的五个剩余时间，`164` 也记录逐电流 MRE；但 `283` 把 q1_metrics 缩减为仅 `q1_mean_fitted_MRE`。整个 checker 未将这五个数与 producer `Q1.remaining_at_9_8V_min` 比较，也未核对 `Q1.per_current_MRE`/每行声称 MRE 的数值。它核对全部曲线系数、逆函数向量和聚合 MRE，因此能间接重新算出这些量，却尚未证明实际交付的相应字段与复算相等。

这是一项静态明确缺口，不是声称真实输出已错误。本轮未运行 checker main。建议按 current_A 稳定键逐项绑定五个 remaining 和九个 per-current MRE，不要用总均值替代分项数值。主 Agent 已告知计划修复；本回执不把未提交修复计入本 subject。

### R2-2016-02：前缀敏感性需写清固定的预测起点（解释限制）

producer `192–199` 变动拟合 prefix，但始终减未变的 last_time；checker `238–244` 同样独立重算。合成 affine 例中，原 remaining=10；prefix 全加1后，固定原 reporting origin 得11，而把 reporting origin 同步加1则仍为10。

当前数值可以解释为“固定预测时点下，对拟合输入的扰动”，其中 DROP_LAST_10 是少用历史输入但仍预测原时点的剩余时间。它不能解释为全部测量时间戳连同当前时刻一起平移。design 只列 PLUS_1/MINUS_1/DROP_LAST_10，建议明确固定 estimand/origin，避免两种数学问题混用。

### R2-2016-03：全区间二分需要目标电压处于单支穿越范围（未验证真实输入）

producer `75–92` 取最后一次模型交点/原始向下穿越；checker `63–74` 对全区间直接二分。一般非单调函数上两者不等价：合成折线 `(0,12),(1,8),(2,8),(3,12),(4,8)` 在10V的最后下穿为3.5，而该 checker 函数实际返回0.5。

producer 注释称评估电压低于早期瞬态/平台；若真实曲线在这些电压上只有一条相关穿越支，该限制可以满足。但本轮未读取原始曲线，因此无法确认；不能把这个合成反例当作真实输入失败。若要声称一般“last downward crossing”的独立核对，需要先枚举各区间最后下穿或记录可核验单支条件。

## 2015 指标与边界审查

源码位于相应 `CUMCM-2015-C-POSTVALIDATION-DEVELOPMENT-007/code/`。

- `solve.py:243–245` 的 altitude RMSE 为残差平方均值再开方，单位 deg；max absolute residual 取绝对残差最大值。`162–205` 为核心契约生成相应样本，core 新增 MAX 聚合可表达后者。七城市×366天=2562日历行，七城市×两天体×12时点=168参考位置，是设计计数，不是本轮实际运行计数。
- producer 以地心坐标/站点视差构建位置，用 spline/brentq；checker 用局部四点 Lagrange、另一组视差表达式和网格二分重建名义事件及 producer 提供的扰动事件，核对窗口数量、起止时刻、UTC+08字段、部分几何条件及参考位置数值。producer 生成设计中的五个扰动，但 checker 从输出读取参数，本轮未证明这五组参数/标签全集被另行独立冻结核对。这具有程序级复算价值。两者仍共享底层星历；design 和源码明确区分星历一致性与实地观测，并保留天气/地形/叶季/历史诗境/真实遇见概率未验证等限制。
- 0.1秒的根数值标签、2秒的跨实现核对公差、角度误差和物理事件可信精度是不同概念。当前 design 已声明数值根公差不等于窄时间窗的真实物理精度；本轮没有根据缺失的原始星历/站点数据检验这些具体公差是否通过。

### R2-2015-01：168参考位置的原始时点集合未强制完整唯一（需修复）

checker `174–181` 对每个 city/body 只要求 selected 与 raw 各12条，然后按每条 row.jd 查原始位置；缺少 selected jd 唯一性与键集合相等检查。`360–368` 的 REF-i 是行号身份，不能替代原始 `(city,body,jd)`。

实际合成局部例：12个原始时点对应残差0..11，完整集合 RMSE=6.4935865796；把输出复制为首个合法时点12次，该数量与查表条件仍为真，unique epoch 只有1，均值误差变0。这里复现的是局部覆盖条件和算术后果，没有运行真实物理变换或整个 checker，未声称实际结果已发生该问题。

建议按 `(city, body, jd)` 核对唯一且完整集合，随后以稳定键逐条对照模型/参考值；允许输出顺序变化。否则不能声称“全部168个预登记参考位置已独立验算”。

## 尚不能核验的内容

没有观察真实运行、原始输入、实际输出、Final、完整 controller 或本轮 root 准备器。两个 development_design.json 尚以 shared_candidate 待冻结占位，完整 metric_definitions 在运行时从 experiment_plan 读取，设计文件未列全每个公式/单位/聚合字段；因此本轮无法验证实际注册 plan 与代码是否完全一致。尤其2016的 Q1/Q2/Q3 MRE 输出是比例 `unit=1`，若计划写为百分比则需显式乘100，不能混用。

未证明真实数据电压序列排序/单根性、prefix切点对应关系、时间编码和原始时间来源、正分母、OLS 非退化性、真实数据下的全部公差，以及物理模型机制或未来实测精度。也未覆盖更广义 SCALAR 指标样本全集绑定；SCI-001 的成功不能替代 R2-2015-01 等具体覆盖检查。

证据文件：math_probe.py、math_probe_results.json、command_log.json、input_manifest.json。所有写入仅在本审核目录；无新依赖，无 formal state/接受决定修改。本回执不是多数票、Formal Gate 或新 subject 资格。
