# 十四模块操作卡与完整请求

所有请求默认 GUIDED_SINGLE_MODULE。只替换方括号内容；不要照抄旧case ID。case真实revision/request ID/hash由Codex定位，不要求用户手填。模块产物路径以公共prepare模板为准。早期完成只表示本阶段工作通过，不能提前要求未来Final。

四维回执必须分开：执行COMPLETED/PREPARED/FAILED；工程检查通过或具体拒绝；科学SUPPORTED/PARTIAL/EVIDENCE_INSUFFICIENT及条件；人工核验NOT_RUN或真实记录。原生状态不必每步改变。

## M01 题目接收

**目的**：弄清收到的到底是什么，附件是否足以开始分析。

**最低输入/前置**：原题与附件；case ID；本次范围。上游模块：无；原题/附件未提供时不能完成接题。

**具体动作**：逐件阅读题面、注释、附件与表头；建立原件清单/sha256及附件关系，写题意概述。

**产物与读法**：problem/original.md、data/raw原件、intake_registry及work/M01.json；原题缺页时列精确缺口。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：清点文件与题面提到的附件；抽读表头/表尾；区分原件、派生数据、未提供材料。

**网页审核重点**：原题、附件是否完整？是否遗漏表注或模板？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M01
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M01任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M01：逐件阅读题面、注释、附件与表头；建立原件清单/sha256及附件关系，写题意概述。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：清点文件与题面提到的附件；抽读表头/表尾；区分原件、派生数据、未提供材料。
返回：problem/original.md、data/raw原件、intake_registry及work/M01.json；原题缺页时列精确缺口。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。缺附件不造数据；可完成已收到材料的登记，但不得写整题接收完整。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：缺附件不造数据；可完成已收到材料的登记，但不得写整题接收完整。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M02 需求拆解

**目的**：每个问题究竟要计算、解释、预测还是证明什么。

**最低输入/前置**：已登记原题；各问目标与特殊限制。上游模块：M01。

**具体动作**：逐问提取动词、对象、硬约束、交付物和可检验条件；画出依赖，分PRIMARY与辅助要求，额外建议标假设。

**产物与读法**：problem/problem_requirements.json及需求—产物对照、人读摘要。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：从原题逐句反查需求；检查每问输出/单位/评价目标；不能只看字段存在。

**网页审核重点**：每个必须回答的问题是否有可检验交付物？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M02
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M02任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M02：逐问提取动词、对象、硬约束、交付物和可检验条件；画出依赖，分PRIMARY与辅助要求，额外建议标假设。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：从原题逐句反查需求；检查每问输出/单位/评价目标；不能只看字段存在。
返回：problem/problem_requirements.json及需求—产物对照、人读摘要。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。漏问先修M02；输出尚无数值属阶段正常，不能要求先有最终准确率。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：漏问先修M02；输出尚无数值属阶段正常，不能要求先有最终准确率。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M03 专业研究

**目的**：哪些专业概念和资料真正改变建模选择。

**最低输入/前置**：概念缺口；允许的专业资料或检索政策。上游模块：M02。

**具体动作**：列概念缺口，读获准一般理论/原始来源；每项来源记录版本、支持语句和采用决策。离线原创推导单列，不伪造外部引用。

**产物与读法**：research/research_plan.json、source_ledger.json及论证笔记。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：核对真实可见来源是否支持具体主张；分事实、机制假说、推导和未知。

**网页审核重点**：来源是否真支持所采用的方法与假设？哪些知识仍未知？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M03
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M03任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M03：列概念缺口，读获准一般理论/原始来源；每项来源记录版本、支持语句和采用决策。离线原创推导单列，不伪造外部引用。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：核对真实可见来源是否支持具体主张；分事实、机制假说、推导和未知。
返回：research/research_plan.json、source_ledger.json及论证笔记。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。来源不可得记录EVIDENCE_GAP；不得搜索题解补齐；仅在必要范围请求材料。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：来源不可得记录EVIDENCE_GAP；不得搜索题解补齐；仅在必要范围请求材料。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M04 假设公式

**目的**：每个符号和假设如何进入目标或约束。

**最低输入/前置**：对象粒度、单位、变量；已有需求和来源。上游模块：M03。

**具体动作**：定义对象粒度；逐个列符号含义/单位/时间坐标/范围；写目标、方程、约束、假设理由与失效后果。

**产物与读法**：models/assumptions_and_symbols.json及可自包含的公式说明。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：量纲检查、极值/零值代入、索引范围和约束方向；公式所有符号均有定义。

**网页审核重点**：单位与量纲是否一致？哪条假设一旦失败会推翻哪些结论？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M04
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M04任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M04：定义对象粒度；逐个列符号含义/单位/时间坐标/范围；写目标、方程、约束、假设理由与失效后果。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：量纲检查、极值/零值代入、索引范围和约束方向；公式所有符号均有定义。
返回：models/assumptions_and_symbols.json及可自包含的公式说明。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。公式未获实验证实不伪造支持；前提冲突回M02/M03，仅影响范围返工。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：公式未获实验证实不伪造支持；前提冲突回M02/M03，仅影响范围返工。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M05 数据审计

**目的**：数据对每问够不够，记录是否可比较。

**最低输入/前置**：已登记数据；字段含义、时间/实体信息。上游模块：M04。

**具体动作**：实际解析数据；核主键/连接粒度、重复、缺失与零、单位、时间可见性、预处理拟合范围；做逐问充分性检查。

**产物与读法**：data/data_audit.json（以模板实际路径为准）、data_sufficiency及数据字典/缺口清单。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：重算有效样本分母和连接前后行数；时间起点前已可用的同实体前缀允许，未来标签不得作特征。

**网页审核重点**：是否用到了预测起点后信息？输入是实测、仿真还是推导？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M05
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M05任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M05：实际解析数据；核主键/连接粒度、重复、缺失与零、单位、时间可见性、预处理拟合范围；做逐问充分性检查。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：重算有效样本分母和连接前后行数；时间起点前已可用的同实体前缀允许，未来标签不得作特征。
返回：data/data_audit.json（以模板实际路径为准）、data_sufficiency及数据字典/缺口清单。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。UNKNOWN/ACQUISITION_REQUIRED不假装充分；允许的PARTIAL只限已支持需求，不能整体READY。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：UNKNOWN/ACQUISITION_REQUIRED不假装充分；允许的PARTIAL只限已支持需求，不能整体READY。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M06 候选方案

**目的**：少量候选分别解决哪种问题，为什么值得试。

**最低输入/前置**：需求、数据限制；计算时间或资源限制。上游模块：M05。

**具体动作**：构造合理baseline与有机制差异的候选；说明假设、所需数据、失败条件和能区分它们的实验。

**产物与读法**：models/model_candidates.json及路线比较表。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：两候选覆盖同一目标与范围，资源可行；不故意削弱baseline，不以算法名数量当质量。

**网页审核重点**：候选是否解决原目标？是否有可区分实验而非只换算法名？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M06
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M06任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M06：构造合理baseline与有机制差异的候选；说明假设、所需数据、失败条件和能区分它们的实验。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：两候选覆盖同一目标与范围，资源可行；不故意削弱baseline，不以算法名数量当质量。
返回：models/model_candidates.json及路线比较表。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。缺少可辨证据时登记设计争议，不能预写候选胜出；需补数据回M05。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：缺少可辨证据时登记设计争议，不能预写候选胜出；需补数据回M05。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M07 基线定义

**目的**：基线是一把公平标尺，代码接口是什么。

**最低输入/前置**：候选中的baseline；计划实现的代码。上游模块：M06。

**具体动作**：实现可解释且可行的基线与候选接口；写独立checker，语法检查和非正式小例；正式冻结运行留M08/M09。

**产物与读法**：models内case-local代码、checker、输入输出规范和预检记录。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：单位、符号、异常/不可行返回；checker不导入producer求解函数；小例不登记为正式Run。

**网页审核重点**：基线是否公平、合法可行且具有实际解释？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M07
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M07任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M07：实现可解释且可行的基线与候选接口；写独立checker，语法检查和非正式小例；正式冻结运行留M08/M09。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：单位、符号、异常/不可行返回；checker不导入producer求解函数；小例不登记为正式Run。
返回：models内case-local代码、checker、输入输出规范和预检记录。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。实现失败保留错误与原因，修好当前模块再继续；prepare或编译成功不等于求解。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：实现失败保留错误与原因，修好当前模块再继续；prepare或编译成功不等于求解。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M08 实验设计

**目的**：怎样在看结果前冻结公平的实验。

**最低输入/前置**：候选/基线代码与checker；预算、指标、划分、Final方式。上游模块：M07。

**具体动作**：定义候选×seed、指标公式/方向/单位/分母/聚合/零分母、可见性和划分；冻结代码/输入/计划，显式标contract probe是非结果。

**产物与读法**：experiments/experiment_plan.json、output contract probe、code freeze和停止条件。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：验证公共preflight；对预测目标选择合法评价方式，优化使用独立约束/界核验；未来真值缺失时不宣称精度已验证。

**网页审核重点**：指标是否衡量原问？独立Final是否与选模严格隔离？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M08
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M08任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M08：定义候选×seed、指标公式/方向/单位/分母/聚合/零分母、可见性和划分；冻结代码/输入/计划，显式标contract probe是非结果。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：验证公共preflight；对预测目标选择合法评价方式，优化使用独立约束/界核验；未来真值缺失时不宣称精度已验证。
返回：experiments/experiment_plan.json、output contract probe、code freeze和停止条件。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。前置不满足先停；不可用虚构test补循环；新实验需新设计，旧Final额度不退款。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：前置不满足先停；不可用虚构test补循环；新实验需新设计，旧Final额度不退款。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M09 编程实算

**目的**：现在真正运行冻结的模型，并核对计算有没有错。

**最低输入/前置**：已冻结计划；待执行candidate/seed/code。上游模块：M08。

**具体动作**：逐个调用公共run model，再run checker；记录完整capture、退出/失败、实际输出与复算，覆盖冻结组合。

**产物与读法**：runs/<Run ID>/output.json、execution_capture、scientific_check/capture；模块报告和局部审查包。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：独立复算向量/目标/约束/单位/指标口径，核完整样本；区分真实启动和预检拒绝。

**网页审核重点**：是否真的运行？输出及负结果是否全部绑定输入/代码/配置？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M09
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M09任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M09：逐个调用公共run model，再run checker；记录完整capture、退出/失败、实际输出与复算，覆盖冻结组合。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：独立复算向量/目标/约束/单位/指标口径，核完整样本；区分真实启动和预检拒绝。
返回：runs/<Run ID>/output.json、execution_capture、scientific_check/capture；模块报告和局部审查包。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。失败Run保留，不能删除凑齐成功；本模块不选模、不运行Final，给出恢复位置后停止。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：失败Run保留，不能删除凑齐成功；本模块不选模、不运行Final，给出恢复位置后停止。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M10 比较选择

**目的**：依据实际开发证据选择哪一方案支持哪一问。

**最低输入/前置**：实际captures；逐问选择proposal与指标。上游模块：M09。

**具体动作**：读取成功且CURRENT的captures，按冻结指标生成逐问选择proposal与依赖桥，调用当前模块controller。

**产物与读法**：results中的model_comparison、requirement_selection及公共gate trace。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：候选×seed覆盖、baseline、指标可比性、上下游版本；平局按冻结规则，baseline胜出正常。

**网页审核重点**：选择依据是否逐问正确？共享依赖与portfolio是否兼容？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M10
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M10任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M10：读取成功且CURRENT的captures，按冻结指标生成逐问选择proposal与依赖桥，调用当前模块controller。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：候选×seed覆盖、baseline、指标可比性、上下游版本；平局按冻结规则，baseline胜出正常。
返回：results中的model_comparison、requirement_selection及公共gate trace。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。无合法方案允许拒绝/不足；不能按网页偏好改排名；比较完不进入Final。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：无合法方案允许拒绝/不足；不能按网页偏好改排名；比较完不进入Final。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M11 稳健误差

**目的**：哪些扰动能改变结论，结论的稳健范围有多大。

**最低输入/前置**：选定Run；已计划扰动的真实输出。上游模块：M10。

**具体动作**：核选中Run已冻结扰动的实际计算、边界/失败及误差；解释敏感性范围，不伪称概率区间。

**产物与读法**：robustness_analysis及绑定当前Run的定量扰动证据。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：确认扰动实改参数或数据且保持可解释；原样重跑仅检重复性，不能代替扰动或独立实现。

**网页审核重点**：扰动是否确实改变输入？区间是敏感性范围还是校准概率区间？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M11
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M11任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M11：核选中Run已冻结扰动的实际计算、边界/失败及误差；解释敏感性范围，不伪称概率区间。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：确认扰动实改参数或数据且保持可解释；原样重跑仅检重复性，不能代替扰动或独立实现。
返回：robustness_analysis及绑定当前Run的定量扰动证据。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。不足的新实验返回M08新范围，不事后加结果到冻结Run；完成后停在Final之前。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：不足的新实验返回M08新范围，不事后加结果到冻结Run；完成后停在Final之前。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M12 最终核验

**目的**：在选择和稳健性已冻结后，进行唯一最终核验。

**最低输入/前置**：比较/稳健性/语义proposal；冻结Final授权范围。上游模块：M11。

**具体动作**：先核选择/语义/稳健性前置和Final账本；用绑定M12的公共controller启动适当独立Final，核实际STARTED/终局。

**产物与读法**：final_result、scientific_final_ledger或适用final_evaluation_ledger、final_check与capture。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：启动前消耗规则、选中Run/输入/代码绑定、Final未用于选择；失败不退款，重复请求复用或拒绝不再执行。

**网页审核重点**：独立核验是否验证原目标？失败预算是否被保留？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M12
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M12任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M12：先核选择/语义/稳健性前置和Final账本；用绑定M12的公共controller启动适当独立Final，核实际STARTED/终局。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：启动前消耗规则、选中Run/输入/代码绑定、Final未用于选择；失败不退款，重复请求复用或拒绝不再执行。
返回：final_result、scientific_final_ledger或适用final_evaluation_ledger、final_check与capture。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。Final失败保留终局；文案反馈不重启Final；停止在FINAL_CANDIDATE，不自动M13/M14。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：Final失败保留终局；文案反馈不重启Final；停止在FINAL_CANDIDATE，不自动M13/M14。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M13 结论检查

**目的**：哪些话可以由当前证据支持，哪些必须保留条件。

**最低输入/前置**：Final及逐问Claim；范围、反证和不确定性。上游模块：M12。

**具体动作**：逐问核Claim ID—Run—指标—字段—条件；调用claim/semantic链，列可以写/不能写的结论。

**产物与读法**：claim_evidence、semantic_claim_support与逐问中文事实草表。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：分描述/关联/因果、模拟/实测、预测/验证、可行/最优；每个primary均有适用支持，禁止以一问代表全题。

**网页审核重点**：是否把条件结论写成真实未来精度、把可行性写成全局最优？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M13
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M13任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M13：逐问核Claim ID—Run—指标—字段—条件；调用claim/semantic链，列可以写/不能写的结论。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：分描述/关联/因果、模拟/实测、预测/验证、可行/最优；每个primary均有适用支持，禁止以一问代表全题。
返回：claim_evidence、semantic_claim_support与逐问中文事实草表。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。支持不足列PARTIAL/缺口；改变数值必须回合法上游新subject，不靠改措辞制造科学PASS。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：支持不足列PARTIAL/缺口；改变数值必须回合法上游新subject，不靠改措辞制造科学PASS。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。

## M14 论文交接

**目的**：把事实交给写作和作图流程时，阅读者能否独立找回证据。

**最低输入/前置**：结论及证据；论文/图表组需要的范围。上游模块：M13。

**具体动作**：通过既有handoff合同生成正式交接；另附逐符号定义、逐问中文结论、表格/作图数据及复现限制，标DERIVED_READING_VIEW。

**产物与读法**：handoff/modeling_to_paper.json、阅读附页、figure-ready data、数据表、来源/失败/限制及审查包。 先读summary_cn与negative_results，再沿artifact到实际数据；以当前完成回执确认完成，PREPARED只是任务模板。

**内部检查**：交叉核正文/摘要/表/图的Run、revision、单位和数值；占位statement不能直接作结论；附页hash回连原字段。

**网页审核重点**：每个正文数字和图表数据是否能追溯到同一有效Run？ 按五类审核选相应视角；先声明实际可见材料与是否执行代码。

**完整请求（复制整段）**：

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[本机case目录或新题合法材料目录]
module=M14
scope=[本次要求范围；尚未拆解用ALL]
本次目标=[希望当前模块回答的具体问题]
特殊限制=[数据/资源/允许来源；没有则写无新增限制]
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M14任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M14：通过既有handoff合同生成正式交接；另附逐符号定义、逐问中文结论、表格/作图数据及复现限制，标DERIVED_READING_VIEW。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：交叉核正文/摘要/表/图的Run、revision、单位和数值；占位statement不能直接作结论；附页hash回连原字段。
返回：handoff/modeling_to_paper.json、阅读附页、figure-ready data、数据表、来源/失败/限制及审查包。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。部分需求未支持不可整体READY；阅读/导出不重启Final；事实争议交回指定模块，排版不改实验真相。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```

**停止与恢复**：部分需求未支持不可整体READY；阅读/导出不重启Final；事实争议交回指定模块，排版不改实验真相。 用status/resume核原请求；不删除失败。共享上游改变时解释依赖并在明确的新范围下创建新root，不能静默复用旧意见或旧Run。普通用户需再次明确调用下一模块。
