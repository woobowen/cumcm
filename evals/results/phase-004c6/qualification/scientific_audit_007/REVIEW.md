# RC9 实际 Development 结果只读审核 007

- reviewed_subject: `10e8b038d571b88ce2b7f2388da00a618c774f69`
- review_scope: `ACTUAL_POSTVALIDATION_DEVELOPMENT_RESULTS`
- 审核开始：2026-09-09 03:54:30 UTC。独占写目录：`.cache/pr12-rc9/scientific-semantics-review-007/`。
- 本回执由原有科学审核 Agent 独立核对源码、真实 root 和公开证据形成；不是完全身份盲 Formal Gate，不使用多数票。主 Agent 声明只作为待核验线索。
- 候选接受：**FAIL**。两题真实公共链均阻断，RC9 不具备本轮接受依据。
- 负终局事实与有限数值摘要：**PASS（限定范围）**。已核对两题 FAILED、每题模型进程 2 / checker 3 / Final 0、无 accepted claim/handoff；不能把此 PASS 用作候选/Final 接受。

## 实际读取与执行

首命令 `ls -la` 实际 exit 0，发现 .venv、.agents、scripts、tests、evals、state、.cache 等目录；完整输出在 commands.json。后续只读指定 subject 源码、两题 case-r2 的计划/requirements/derived output/temporal lineage/capture/checker/trace/ledger，以及本轮公开 execution、terminal、summary、report、replay receipt。材料 SHA 清单见 material_manifest.json（135 项；这是被哈希的材料子集，全部读取命令另存日志）。

必要原始证据抽查仅限 2016 已获准工作簿两张 sheet 的前两行表头：附件1、附件2均明确“放电时间（min）”；没有读取原题全文或答案。2015 仅额外读 processed/settings.json 中年份、名义坐标和几何条件；没有打开原始天文数据、原题或答案。

自己实际执行的 `arithmetic_review.py` 仅使用 Python 标准库解析现有文件和进行算术，不 import core/producer/checker，不启动真实模型或 Final。最后一次执行 04:09:26 UTC，exit 0；8381 项逐行/哈希/汇总断言均成立。此数量主要来自逐行分母检查，**不是 8381 个独立科学实验或 CI 测试**。实际题模型/checker/Final 新 starts 均为 0。没有安装依赖、改环境或写共享文件。

自写读取/审核程序中实际遇到两类字段读取错误（dict/list 与 envelope），以及一个将合法目标前缀误排除出拟合输入的过严断言。先检查实际 schema 和源码后修正；初始 14 条断言失败结果及所有 exit 1 日志完整保留于 initial_arithmetic_results.json、initial_arithmetic_checks.json 和 commands.json。这些是本审核程序的问题，未冒充真实题的科学失败。

## R7-001：场景默认值语义不一致，重大未闭合

真实两题的 experiment_plan.content 均无 scenario_hash。subject core 的执行器在 cumcm_case.py:5593–5599 用按 path 排序的 input_files SHA 列表 canonical hash 生成默认值，再写入 capture/manifest。本次独立标准库重算得到：

| 题 | 默认 scenario_hash |
|---|---|
| 2016 | 6125b5fb0afcd5caedafcc374f9b21f0450832e51e1e33e1f362328ee5aa171f |
| 2015 | b993bac3a526d38def4e133cd4112a60ac58bb04c1b623a5986e79116eff42e6 |

每题两 capture 和 manifest 均与该默认值相同。但 finalize_fresh_c_validation.py:619 直接传 `plan.get("scenario_hash")`，实际为 None；core:1168–1169 与 manifest hash 比较，产生 `RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND`。core:6190–6195 的 Final 路径也直接读取 plan.get。问题是执行器与调用方对可缺省字段采用不同语义；不能仅称输入损坏。

实际 complete 命令两题 exit 1，trace 均是前五 Gate PASS、第六 GATE_COMPATIBILITY_PORTFOLIO BLOCK；语义、聚合及后续 Final Gate **未到达**。checker 在该兼容性检查之前运行，故成功 checker 与此阻断并不矛盾。本审核没有执行 memory-only 修补 Gate，也没有修改实际 plan/trace。

实际 plan 字节 SHA 与 trace input hash 一致：2016 为 8947aa5e0e98a69176ba8d97af4f4329861332337b4fc0c8848459dd902f62dc；2015 为 c946d7daf39cfaefaadc3016c0ae6dbe6da85af99a73e70ccfc98d5243ddb53b。所有 trace input hashes 与当前实际文件一致，before/after case_state hash 一致。root Final 仍为空 DRAFT；prefinal freeze、Final evaluation ledger、scientific Final ledger、Final protocol events 均不存在。故当前证据支持真实失败终局，不支持修复已生效或接受已完成。

## 2016：逐问可支持与不可支持结论

| 问题 | BASELINE | CUBIC_LOG_AFFINE（开发选中） | 解释 |
|---|---:|---:|---|
| Q1 elapsed-at-voltage MRE | 0.3009290% | 0.0780032% | 9 电流 × 231 电压点 = 2079；题内曲线拟合诊断 |
| Q2 LOCO elapsed MRE | 4.8930522% | 1.0219759% | 7 留一电流 × 231 = 1617；开发插值诊断 |
| Q3 remaining-time MRE | 5.9408550% | 5.1965754% | 2 历史状态 × 3 起点；6 个相关状态起点 |
| Q3 当前条件剩余时间 | 192.2672 min | 193.4418 min | 未来 9V 终止真值缺失 |

这些汇总均从现有 metric_samples 独立重算，并核对唯一 sample_id、无排除、计数、metric_accounting、公开 summary 和 terminal。末位浮点差在 1e-10 容差内。

Q1/Q2 分母为电压点的真实 elapsed time；没有把这两个误差解释为剩余寿命误差。Q1 是分段曲线表示，不是一个紧凑全局经验公式，也不是新电池泛化精度。Q1 已输出并由已有 checker 核对的 30/40/50/60/70A、9.8V 剩余时间分别为 591.678153、429.791455、326.197390、277.936587、254.685484 min。自有算术审核检查了输出到公开摘要的一致性，未重新求这五个逆函数。

Q2 55A 条件总时长 1162.588117 min，位于训练电流范围 20–100A 内；没有 55A 真值。LOCO MRE 不能作为 55A 已验证精度。行数也不等于独立电池数。

Q3 每样本计算 `abs(predicted_end-observed_end)/(observed_end-origin)`。选中候选的六项误差为 3.013385%、3.585902%、4.100089%、5.605498%、6.755980%、8.118599%，等权均值 5.1965754%。若错误使用各状态完整 elapsed termination 作分母，同样输出会得到 1.6487695%；当前实现和公开报告没有该分母错误。分母单位 min，结果无量纲。

实际 temporal_index 使用 `10000*state+elapsed_min` 作为状态排序坐标，不是日历。全部 lineage IDs 有效、同一 BATTERY-1；可见时间与观测时间均不晚于 origin。每个目标状态的同状态拟合 ID 恰等于该起点完整连续前缀（111、131、148 行），其他拟合数据只来自更早状态。状态1仅引用0；状态2引用0/1；状态3引用0/1/2。六个测试终止标签均在对应起点之后，且不在该次 fit/features 中；它们又均早于状态3预测起点。因此历史标签用于开发选择在时间上可用，但不是六个独立电池或未接触验证集。这里核对的是声明 lineage 和源码逻辑，没有重新物理拟合真实数据。

当前 elapsed 596.2 min；条件总时长789.641777 min 减去该起点得到193.441777 min。三个参考状态给出184.826077、192.963867、205.475497 min。这是模型敏感性范围，无覆盖率校准，不能称置信区间或预测区间。Q3 电流数值未知，合同仅要求 voltage/elapsed，并以相同恒流为条件，未冒充已知数值电流。

既有独立 checker 报告 Q1 全2079逆时差最大8.64e-12 min、Q2 LOCO/55A向量差最大7.96e-12 min、Q3衰减/扰动差最大3.64e-12 min；相应 tolerances 为1e-7 min。它支持独立数值实现一致性，不能验证未来衰减不变性或未来真值。前缀扰动是固定 forecast origin 下重拟合的输入敏感性，不能代替误差分布。

## 2015：逐问可支持与不可支持结论

| requirement | TOPOCENTRIC 实际结果 | 审核界限 |
|---|---|---|
| REQ-DEFINITION | 10°名义树梢角；2562城市日 | 7城市×2016年366个唯一日期；预设几何解释 |
| REQ-VALIDATION | 168参考行；RMSE0.000749386°；最大绝对差0.001445385° | 7城市×2天体×12唯一epoch；同JPL参考族一致性 |
| REQ-BEIJING | 15时窗 | 条件几何模拟 |
| REQ-HARBIN | 18时窗 | 条件几何模拟 |
| REQ-SHANGHAI | 12时窗 | 条件几何模拟 |
| REQ-GUANGZHOU | 12时窗 | 条件几何模拟 |
| REQ-KUNMING | 13时窗 | 条件几何模拟 |
| REQ-CHENGDU | 13时窗 | 条件几何模拟 |
| REQ-URUMQI | 16时窗 | 条件几何模拟 |

本审核从现有 reference metric samples 重算 RMSE（平方误差均值开方，仍为 degree）和最大绝对差；检查事件计数合计99、每个已报告事件为正时长、JD差×1440与duration_minutes一致、名义事件中点落在月心8–12°及太阳−12至−6°内。没有独立重新搜索未报告时窗；该完整性依赖已运行的独立 checker。

GEOCENTRIC 基线 RMSE0.528066345°，最大绝对差1.022691391°，超过0.05°预登记阈值。其 REQ-VALIDATION.feasible=false 被真实 checker、公开 summary 保留。正常 exit0 仅表示计算/复算正常完成，不能宣布该基线科学阈值通过。

TOPOCENTRIC 的参考误差与独立实现差异是不同量：后者已有 checker 的最大高度差约0.0000419644°、端点最大差0.996308 s，分别满足0.002°、2s的计算一致性容差。root求根0.1s或显示到秒不等于现实天文/观测精度。

五项预登记扰动的计数也在输出/公开summary间一致：LOWER_TREE96、HIGHER_TREE98、WIDER_TREE_BAND129、CIVIL_TWILIGHT81、LATITUDE_PLUS_00599。没有把这些变体范围当作统计区间。名义坐标、零椭球高度、无折射月心、平坦无遮挡地平线、UTC近似UT1等条件限制均在公开报告保留。不能推出现场能见概率、天气/地形/叶季影响、真实人类相遇概率或诗词历史事件真实。

## 证据、独立性及发布核验

两题每题4次CLI请求中，前2次 Run ID 无 RUN- 前缀，RC_RUN_ID_INVALID exit3且未产生模型capture；后2次模型进程SUCCESS。每题初始两checker各覆盖一个候选，第三次为主Agent在fresh Python进程调用已冻结checker。审核已读第三次replay的公开绑定日志、时刻及实际ledger；它是复用该独立checker实现的复算，不是额外独立算法或外部真值。

各capture记录的 core/producer/checker bytes 均与 Git subject 10e8 的对象逐字节SHA一致（12项 run×code 对照）。两题共70个 execution artifact 绑定，以及每个 raw_to_public_provenance 原文件hash、四个summary的输入output/checker/capture hash、summary数值/requirement residual、terminal逐问全集和metric、development_results_r2精确tuple均验证一致。精确terminal/execution绑定见 receipt.json 的 reviewed_development_artifacts。

公开 SCIENTIFIC_REPORT 的失效相对链接经提示修正后实际检查目标均存在。2015报告已明确说明执行器默认值与controller None的不一致。其开头“缺显式scenario_hash”可读作触发条件，不能理解为原plan已违反必填合同。两份报告区分elapsed/remaining误差，2015区分星历参考误差/实现差异，均保留无Final/handoff边界。未发现需要阻止如实发布负结果的新重大数学问题。

2015 CSV只核对了SHA、99行及source_output_sha256 provenance，未逐单元格审核全部CSV；真实output中的事件计数、时长、中点另已核对。该CSV为派生条件模拟，不是正式handoff。

## 未覆盖与结论

未重跑任何真实题producer/checker/Final、未另开模型候选或增加真实starts；未复核原题全文/答案、原始数据全量转录、天文外部文档、外部观测或新电池真值；未运行本轮full CI，不把主Agent报告的CI通过计作本审核实验；未验证未到达的semantic/aggregation/Final/handoff Gates；未逐条重算全部物理曲线/天文位置或所有时窗边界；未完整逐单元格审CSV；未证明真实系统的跨题泛化。

R7-001 仍是候选接受的重大阻断。可以如实保存这两份 FAILED Development 终局及有明确边界的计算结果；不应激活RC9、补写旧冻结plan、把独立数值复算改称外部验证，或用前轮预运行PASS覆盖本轮真实失败。

