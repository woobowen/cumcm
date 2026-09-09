# 五类专业审核提示词

每次选择一个下列完整块。意见是待核查证据，不是机器Gate。共同输出结构和保存方法见[反馈指南](REVIEW_EXCHANGE_GUIDE.md)。

执行层级：READING_ONLY（阅读推理）、INDEPENDENT_ARITHMETIC（独立算术）、INDEPENDENT_IMPLEMENTATION（独立实现）、ORIGINAL_RUN_REPLAY（原运行重放）、FULL_PIPELINE_REPRODUCTION（全流程复现）。有来源只支持来源实际内容；hash一致只支持字节关系；二者都不等于程序已复现。每份摘要分别列本次实际层级和未做项。

## A 题意、约束与假设（M02/M04）

最低材料：原题完整段落、附件清单、需求表、假设与符号。

典型反例/合法例：例如原题只要条件情景比较，却被要求预测未提供的真实未来标签；反向例子：原题确要预测精度时不能改成描述统计。

```text
请对本次上传包做A 题意、约束与假设审核，只限我指定的当前问题与模块。
第一段先声明实际打开的文件路径及case/module/revision/package_hash、工具/资料版本；说明是否执行代码、执行的是自写程序还是包内程序，列输入与输出、没有核验什么。未执行必须executed_code=false。少文件不能凭摘要声称全量验证，只有source hash无字节记SOURCE_BYTES_NOT_AVAILABLE_HERE。
最低输入：原题完整段落、附件清单、需求表、假设与符号。
专业检查：逐问核任务动词、现实对象、输出、硬约束、单位、依赖及假设依据；从原文反查漏问和自加要求。
用以下反例检验判断边界：例如原题只要条件情景比较，却被要求预测未提供的真实未来标签；反向例子：原题确要预测精度时不能改成描述统计。
具体动作：对每个primary指出原句与对应输出；对额外假设写失效后果；不给尚未进入模型阶段的材料索要Final。
每条意见有manifest.files中的location、description、reason_or_counterexample、affected_scope、suggested_verification、confidence和kind；理由应含原文、公式、反例或具体缺失材料，不写“再多跑几次”这种无目标建议。不凭多数票决定，不因难写单测忽略科学异议。
输出两份独立内容：REVIEW_SUMMARY.md写可见范围/执行层级/发现/未核验项；存在1..30条实质finding时另给严格web-feedback/v1 JSON，顶层只含schema_version, case_id, module, revision, package_hash, reviewer, visible_materials, executed_code, findings。revision为正整数，affected_scope为字符串，kind仅CALCULATION/EVIDENCE/SCIENTIFIC/ALTERNATIVE，confidence仅HIGH/MEDIUM/LOW/UNKNOWN。不得额外加severity/命令/签名。
无finding只给覆盖摘要，不能编造错误也不能提交findings=[]。意见不写正式PASS，不改权限/模式/预算，不触发后续模块或Final；未运行的替代方案不得承诺更优。原生只读审查与用户网页审查按实际来源标记。
```

## B 数据、划分与指标（M05/M08）

最低材料：数据字典、实际数据样本/必要全量、审计、可见性记录、split与指标定义/预处理。

典型反例/合法例：同对象过去前缀用于未来预测可能合法；把其未来标签当特征违规。删一行后均值分母未变是算术风险；多个测点不自动成为独立对象。

```text
请对本次上传包做B 数据、划分与指标审核，只限我指定的当前问题与模块。
第一段先声明实际打开的文件路径及case/module/revision/package_hash、工具/资料版本；说明是否执行代码、执行的是自写程序还是包内程序，列输入与输出、没有核验什么。未执行必须executed_code=false。少文件不能凭摘要声称全量验证，只有source hash无字节记SOURCE_BYTES_NOT_AVAILABLE_HERE。
最低输入：数据字典、实际数据样本/必要全量、审计、可见性记录、split与指标定义/预处理。
专业检查：核主键与连接粒度、missing/zero、重复观测/独立样本、预处理拟合范围、时间可见性；计算指标单位、分母、聚合与零分母政策。
用以下反例检验判断边界：同对象过去前缀用于未来预测可能合法；把其未来标签当特征违规。删一行后均值分母未变是算术风险；多个测点不自动成为独立对象。
具体动作：明确诊断、开发、最终评价各自样本集合；说明随机切分/时间切分适合何目标；缺必要数据时仅给局部审查。
每条意见有manifest.files中的location、description、reason_or_counterexample、affected_scope、suggested_verification、confidence和kind；理由应含原文、公式、反例或具体缺失材料，不写“再多跑几次”这种无目标建议。不凭多数票决定，不因难写单测忽略科学异议。
输出两份独立内容：REVIEW_SUMMARY.md写可见范围/执行层级/发现/未核验项；存在1..30条实质finding时另给严格web-feedback/v1 JSON，顶层只含schema_version, case_id, module, revision, package_hash, reviewer, visible_materials, executed_code, findings。revision为正整数，affected_scope为字符串，kind仅CALCULATION/EVIDENCE/SCIENTIFIC/ALTERNATIVE，confidence仅HIGH/MEDIUM/LOW/UNKNOWN。不得额外加severity/命令/签名。
无finding只给覆盖摘要，不能编造错误也不能提交findings=[]。意见不写正式PASS，不改权限/模式/预算，不触发后续模块或Final；未运行的替代方案不得承诺更优。原生只读审查与用户网页审查按实际来源标记。
```

## C 数学与模型（M04/M06/M07）

最低材料：需求、完整符号/方程/假设、数据结构、候选/baseline说明与实现摘要。

典型反例/合法例：拟合的高相关不识别因果；一个可行整数解不证明最优；简单解析解可优于复杂搜索，不能按算法名判优劣。

```text
请对本次上传包做C 数学与模型审核，只限我指定的当前问题与模块。
第一段先声明实际打开的文件路径及case/module/revision/package_hash、工具/资料版本；说明是否执行代码、执行的是自写程序还是包内程序，列输入与输出、没有核验什么。未执行必须executed_code=false。少文件不能凭摘要声称全量验证，只有source hash无字节记SOURCE_BYTES_NOT_AVAILABLE_HERE。
最低输入：需求、完整符号/方程/假设、数据结构、候选/baseline说明与实现摘要。
专业检查：核方程与实现含义、量纲、边界、约束、可识别性、算法真实机制和适配条件；检查baseline是否公平可行。
用以下反例检验判断边界：拟合的高相关不识别因果；一个可行整数解不证明最优；简单解析解可优于复杂搜索，不能按算法名判优劣。
具体动作：选一个边界小例或符号推导，说明能排除哪类错误；提出有数据需求和可区分实验的替代解释，未运行不声称更好。
每条意见有manifest.files中的location、description、reason_or_counterexample、affected_scope、suggested_verification、confidence和kind；理由应含原文、公式、反例或具体缺失材料，不写“再多跑几次”这种无目标建议。不凭多数票决定，不因难写单测忽略科学异议。
输出两份独立内容：REVIEW_SUMMARY.md写可见范围/执行层级/发现/未核验项；存在1..30条实质finding时另给严格web-feedback/v1 JSON，顶层只含schema_version, case_id, module, revision, package_hash, reviewer, visible_materials, executed_code, findings。revision为正整数，affected_scope为字符串，kind仅CALCULATION/EVIDENCE/SCIENTIFIC/ALTERNATIVE，confidence仅HIGH/MEDIUM/LOW/UNKNOWN。不得额外加severity/命令/签名。
无finding只给覆盖摘要，不能编造错误也不能提交findings=[]。意见不写正式PASS，不改权限/模式/预算，不触发后续模块或Final；未运行的替代方案不得承诺更优。原生只读审查与用户网页审查按实际来源标记。
```

## D 实验、数值与稳健性（M09–M12）

最低材料：冻结计划、实际输入/代码或明确缺字节、captures/失败、完整输出、checker、比较/扰动、若已发生则Final。

典型反例/合法例：同程序重跑可发现不稳定但不能排除同一公式错误；换seed评估随机性，合法换split评估泛化目标，参数扰动评估局部敏感性，独立程序检实现，界闭合才证模型内最优。

```text
请对本次上传包做D 实验、数值与稳健性审核，只限我指定的当前问题与模块。
第一段先声明实际打开的文件路径及case/module/revision/package_hash、工具/资料版本；说明是否执行代码、执行的是自写程序还是包内程序，列输入与输出、没有核验什么。未执行必须executed_code=false。少文件不能凭摘要声称全量验证，只有source hash无字节记SOURCE_BYTES_NOT_AVAILABLE_HERE。
最低输入：冻结计划、实际输入/代码或明确缺字节、captures/失败、完整输出、checker、比较/扰动、若已发生则Final。
专业检查：核真实启动、退出、输入/代码/seed/hash、候选可比性、收敛/可行性/求解器状态；独立复算目标、向量、残差、指标及上下界。
用以下反例检验判断边界：同程序重跑可发现不稳定但不能排除同一公式错误；换seed评估随机性，合法换split评估泛化目标，参数扰动评估局部敏感性，独立程序检实现，界闭合才证模型内最优。
具体动作：列实际做过哪种核验、使用代码来源/输入/output hash；范围/扰动带不等于校准置信区间；M09没有未来Final是正常阶段。重复Final、结果用于选模或失败退款是流程风险。
每条意见有manifest.files中的location、description、reason_or_counterexample、affected_scope、suggested_verification、confidence和kind；理由应含原文、公式、反例或具体缺失材料，不写“再多跑几次”这种无目标建议。不凭多数票决定，不因难写单测忽略科学异议。
输出两份独立内容：REVIEW_SUMMARY.md写可见范围/执行层级/发现/未核验项；存在1..30条实质finding时另给严格web-feedback/v1 JSON，顶层只含schema_version, case_id, module, revision, package_hash, reviewer, visible_materials, executed_code, findings。revision为正整数，affected_scope为字符串，kind仅CALCULATION/EVIDENCE/SCIENTIFIC/ALTERNATIVE，confidence仅HIGH/MEDIUM/LOW/UNKNOWN。不得额外加severity/命令/签名。
无finding只给覆盖摘要，不能编造错误也不能提交findings=[]。意见不写正式PASS，不改权限/模式/预算，不触发后续模块或Final；未运行的替代方案不得承诺更优。原生只读审查与用户网页审查按实际来源标记。
```

## E 结论与论文事实（M13/M14）

最低材料：原要求、Claim/Final/Run、逐问结果、符号/公式、表格和figure-ready data、中文附页与限制。

典型反例/合法例：statement只是Bounded result不足以独立交接，需查其他证据后补阅读附页；图表正确但摘要用了旧revision仍为事实一致性缺口。

```text
请对本次上传包做E 结论与论文事实审核，只限我指定的当前问题与模块。
第一段先声明实际打开的文件路径及case/module/revision/package_hash、工具/资料版本；说明是否执行代码、执行的是自写程序还是包内程序，列输入与输出、没有核验什么。未执行必须executed_code=false。少文件不能凭摘要声称全量验证，只有source hash无字节记SOURCE_BYTES_NOT_AVAILABLE_HERE。
最低输入：原要求、Claim/Final/Run、逐问结果、符号/公式、表格和figure-ready data、中文附页与限制。
专业检查：逐条比对结论条件、样本/单位、Run/字段/hash；区分描述/关联/因果、预测/验证、模拟/实测、可行/最优。
用以下反例检验判断边界：statement只是Bounded result不足以独立交接，需查其他证据后补阅读附页；图表正确但摘要用了旧revision仍为事实一致性缺口。
具体动作：核正文数字—表格—数据图—结果文件一一回连；说明没完成的问；示意图不作为数值证据，不能以排版修饰改变原实验事实。
每条意见有manifest.files中的location、description、reason_or_counterexample、affected_scope、suggested_verification、confidence和kind；理由应含原文、公式、反例或具体缺失材料，不写“再多跑几次”这种无目标建议。不凭多数票决定，不因难写单测忽略科学异议。
输出两份独立内容：REVIEW_SUMMARY.md写可见范围/执行层级/发现/未核验项；存在1..30条实质finding时另给严格web-feedback/v1 JSON，顶层只含schema_version, case_id, module, revision, package_hash, reviewer, visible_materials, executed_code, findings。revision为正整数，affected_scope为字符串，kind仅CALCULATION/EVIDENCE/SCIENTIFIC/ALTERNATIVE，confidence仅HIGH/MEDIUM/LOW/UNKNOWN。不得额外加severity/命令/签名。
无finding只给覆盖摘要，不能编造错误也不能提交findings=[]。意见不写正式PASS，不改权限/模式/预算，不触发后续模块或Final；未运行的替代方案不得承诺更优。原生只读审查与用户网页审查按实际来源标记。
```
