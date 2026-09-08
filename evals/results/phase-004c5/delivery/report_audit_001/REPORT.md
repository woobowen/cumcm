# RC8 M5 交付报告一致性独立审核

**报告一致性意见：FAIL，须修正已确认的指标语义误述。** 该意见只审查固定版 FINAL_REPORT.md 与允许证据的一致性，不是重新作科学模型审核、技术 Gate 判定、候选资格接受或交付放行。修订后可按下列定位做定向报告复核，不能把本意见或脚本 exit 0 称为技术通过。

受审报告 SHA256：df12b02f92ed07811ab9d8752f8dcac08339f978ed096cd2d20941abcac8d6c8。
输入 bundle：RC8-M5-DELIVERY-REPORT-CONSISTENCY-001，文件 SHA256 为 82f680580f96bce0f09dcd76207a23d281a6159a1949d8530ec6a562daaff3f7。
严格限定于其中 31 个文件；首末哈希核验结果分别见 pre_hash_check.json、post_hash_check.json。没有追读这些文件指向的其他证据。

## 需要修正的表述

| 编号 | 严重度 | FINAL_REPORT 定位 | 证据与问题 | 明确修正建议 |
|---|---|---|---|---|
| M5-001 | ERROR | 77 | “168实际可用供应商”改变了数字含义。v6/SCIENCE_REPORT.md:19–29 的 168 是旧算法对照实际使用数；399 是候选池，当前使用数是 14。证据没有给出“全部可用只有168”的结论。 | 改为“候选池399；旧对照实际使用168家，当前基线使用14家，并达到限定固定参数模型中的数量下界14”。 |
| M5-002 | WARNING | 78–79 | 9.705398 / 1.758417 的数值和方向正确，但“forecast相关指标”没有保留其具体口径。v6/SCIENCE_REPORT.md:27、31–34 明确是统一独立 checker 当前支付/库存/超载公式的历史压力指标；旧 producer 2.137603 还明确不可等价比较。 | 改为“同一定义的独立历史综合压力指标（越小越好）9.7054，对照1.7584”；不要将其用作预测准确率。 |
| M5-003 | ERROR | 122–123 | “独立剩余时间MRE为4.1001%/8.1186%”给单个历史目标误差加上了均值含义。2016 native REPORT.md:44–54 和 decision.json 的 F04 分别给出状态1、2在前缀末端的剩余时间相对误差；每个数对应一个终止时刻目标。0.599134% / 1.086915% 才是原尾段已放电时间 MRE。 | 改为“独立复算的历史状态1/2前缀末端剩余时间相对误差为4.1001%/8.1186%；原尾段已放电时间MRE为0.5991%/1.0869%”。保留状态3真实误差未知、不同目标与分母的限制。 |
| M5-004 | WARNING | 91–92 | 三个值被统称为“Hellinger选择值”，容易把三个候选值归给一个模型或一个 Hellinger 指标。v6/SCIENCE_REPORT.md:70–73 称它们为三个候选的 validation composite loss，随后才说 Hellinger/KNN 被选中。 | 改为“三候选在12个validation文物组上的 composite loss 分别为0.121658、0.019885、0；Hellinger/KNN按该指标被选中”。 |
| M5-005 | WARNING | 70–73 | “15个实际CLI captures”之后紧接单一“实际科学代码subject为d9…”会让读者把全部15次执行归给d9。v6/SCIENCE_REPORT.md:14–17、36–39、57 明确保留旧对照4515597、早期改进候选4d2a0b8及当前候选d9a43b8的不同身份。 | 把d9限定为“当前RC8候选数值运行的subject”；明确15次capture各自保留实际subject，旧对照与早期候选不迁移到d9或29cf1d7。 |

可选澄清：FINAL_REPORT.md:111 的“完整episode”建议改为“登记预算窗口（非实际运行时长）”。两段均为7200秒预算，终局均提前冻结；窗口重叠不证明实际worker并行。registry记录实际worker开始分别为20:47:03Z、21:56:33.948200Z，第一题终局远端记录21:53:34.072276Z先于第二worker开始。报告的“串行实跑”与这些记录一致。

## 本次已独立核对、可保留的主要内容

- **身份与范围**：候选、state、registry及两题决定绑定同一共享subject 29cf1d7566809519ca92b6a29f555ce0c0b5b204；snapshot有772项映射。接受范围明确为 RESEARCH_AND_FRESH_VALIDATION_ELIGIBILITY_ONLY，TEAM_COMPLIANCE_REVIEW=NOT_RUN；Project/Skill两个版本分别为0.3.0-competition-rc8与0.2.0-competition-rc8。活跃资格不能解释为新题通过。
- **分母与终局**：独立从两份决定汇总启动2、执行2、终局完成2、科学通过0，与主编排器批次记录和registry一致；每题2个模型capture、2个原checker。2016正式 EVIDENCE_INSUFFICIENT，2015正式 FAILED；全题科学接受均false，state仍IN_PROGRESS，next_phase_allowed=null。
- **2015正式顺序**：既有审核字段显示config lock在22:25:58.148546Z；Final于22:28:14.968512Z开始、22:28:18.872464Z结束；selection-check、compare-check、robustness接受依次在22:28:18.886247Z、22:28:18.951645Z、22:28:19.086355Z。早期数值比较与锁定不满足正式前置Gate。case-owned native READY、common wrapper未执行、初次原生审核FAIL、负面复审记录PASS和主编排器冻结FAILED在报告中得到正确区分。三次额外checker重放≠三个Final，也≠三次独立科学审查。
- **2015汇总算术**：从允许科学报告各城市表求和得到99个名义窗口；五类扰动为96+98+129+81+99=503；7×366=2562日历行；3×(99+503)=1806个既有场景检查时刻；7686+2475=10161日历检查时刻。与正式决定一致。这里只复算表与记录的汇总，未重新搜索天文事件。
- **Development数字**：2021的8次capture含5成功/3失败，2022的7次均成功，合计15；额外Q4构造计2021第9/9次数值试验，不伪造第9个CLI Run。采购成本、损耗、47/48对48/48运输超载、23/48对12/48库存违约的数值和比较方向与v6表一致。44×2=88，56×5=280，56−44=12，3×999=2997；排除暴露标签不能恢复盲性，11/13有限支持不能变成未知预测准确率。
- **Q4展示界**：独立使用 Fraction 读取已发布精确界，验证40246.40307264614≤L≤U≤40246.40311289260，以及U−L精确等于发布gap且≤1/1000。发布slack项数为402、8、3216，总3626。未重算LP、原始参数、对偶约束或执行既有verifier；本次不扩大历史Q4审核的第一目标静态十进制参数LP范围。
- **CI受测对象**：资格CI回执绑定29cf1d7、exit0、2153 passed。本机交付CI回执绑定6be924e和tracked tree 1349ce00d0cf60acc9d158f7dfee51e1366dcc4c，2151 passed/2 failed/1 skipped、pytest349.95秒、exit1。远端观测绑定PR merge checkout 22c097256777009083e107768992c14de822685b、2151/2/1、461.27秒；未单独feature checkout。15项补查均有exit0记录且绑定6be924e，明确不消除full CI失败。两个失败测试文件都在772映射内；registry确有10个case。报告没有把资格CI或补查移用为当前CI成功。
- **审核归属**：2016/Q4报告及JSON的作用范围与FINAL_REPORT一致；2015报告明确由主代理从独立角色JSON渲染落盘。允许的三个原始audit JSON均通过既有schema与canonical output_hash核验。2015批次计数和全局state属于主编排器核验范围，不能归给其单题auditor。Q4两次最初工具输出未完整离线归档的限制也被保留。

## 范围限制与证据不足

本次不单独验证本轮所有Git历史，也没有调用Git、网络、模型、原checker、Final或CI。历史commit内容、远端push事件、Draft状态、最终HEAD/remote SHA和本机merge-tree只可依赖已绑定记录；不能称为本角色独立观察。主代理后来产生的交付回执不在本bundle，未读取、未背书。

以下内容在31文件范围内没有足够底层证据可作完整独立核验，但不能仅因本bundle未包含而判其虚假：

- 100项资格定向测试、资格CI的1 skipped、继承HF22的22项定向测试、当前checker修复的全部正反例/实际执行和全部旧历史不变性。snapshot含外部回执hash引用，当前full_ci.json只直接列2153 passed，没有skip数；本角色不追读引用。
- 研发起始/8小时授权与平台Goal 4,545,021 tokens、20,294 seconds的原始计量；23:35附近、实际收口、现金/缓存/排队成本。能够核对给定起止的算术，并不等于核实授权或平台原始观察。
- 2015 pre-run远端时间22:23:38Z在本bundle未找到独立于受审报告的精确时间来源；registry可确认其commit/ref身份。资格接受20:35:29和激活远端20:37:30等则有允许记录支持。
- 2015第二次原始Decision Auditor JSON未列入bundle；其PASS由formal decision和主代理渲染REPORT交叉支持，本角色没有验证第二份JSON自身hash/schema/原生transport。事实绑定与资格审查的原始工具轨迹同样不在本bundle。
- 原始输入、答案封存与所有代理未发生未记录访问、全新环境安装与跨平台完整replay均不在本审核保证内。注册的封存字段和历史报告可核对，不能据此作系统级“从未访问”证明。未读取raw、答案、vault或保留题内容。
- 首个按要求执行的ls -la没有捕获起止UTC；其真实工具输出、exit0和工具wall字段保留，不补造时间。其余外层命令用实际clock调用夹取UTC，但早期工具只提供合并stdout/stderr；分别记UNKNOWN，不伪造分流。独立算术脚本则有精确起止UTC、monotonic、exit及分别保存的stdout/stderr与hash。

执行与复核产物见 independent_cross_checks.py、independent_cross_checks.json、cross_checks_execution_receipt.json、tool_receipts.json、execution_manifest.json。脚本通过只表示上述记录/算术一致性检查通过，不能消除本报告的两个ERROR或给予技术接受。

本角色仅在指定新ignored输出目录写文件；没有修改任何受审文件、公开文件、formal state或Git。新增系统包、语言包、工具链、配置均0。实际运行model、reasoning、token与现金cost均为UNKNOWN。audit.json使用reproducibility_auditor与FROZEN_PREDECESSORS_ONLY，因为允许输入包含受审对象的历史review；没有接收同级新review或执行多数投票。
