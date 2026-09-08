# RC8 M5 五项文案修正短复审

**PASS，仅指五项修正文案与既有允许证据一致。** 原始审查 FAIL 保持原样；本次不重新判定科学模型、RC8资格、技术Gate、当前CI、远端交付或全题接受。

受审 FINAL_REPORT.md SHA256：d0c206f7f0f7a236c986b9479f73d3128f1832c29767e5f3ba5871323a4e2819。
bundle SHA256：14606e9bf00d2ccc4bbad5faf82bb05eecc3654b3b0ef084c7e5ce5b6928d46d。
32个文件首末hash全部匹配。相对上轮bundle，30个原有证据文件hash不变，仅FINAL_REPORT改变并新增main_disposition.json；详见bundle_delta.json。

| 原发现 | 修订报告位置 | 复审结果 |
|---|---|---|
| M5-001 | 78–79 | 明确399候选池、旧对照实际使用168、当前使用14及限定条件最小数14，与v6表一致。 |
| M5-002 | 80–81 | 改为同定义独立历史综合压力指标，保留9.705398比1.758417更差，未变成预测准确率。 |
| M5-003 | 124–125 | 明确历史状态1/2前缀末端单目标剩余时间相对误差，与原elapsed-time MRE区分目标、分母和聚合。 |
| M5-004 | 93–94 | 明确三个值为三候选validation composite loss，另列Hellinger/KNN被选中，保留非校准/非外部准确率限制。 |
| M5-005 | 72–74 | d9仅归当前候选运行；旧对照4515597、较早候选4d2a0b8单列，不再把全部15次capture归到d9。 |

报告仍明确科学通过0/2、2016 EVIDENCE_INSUFFICIENT、2015因正式Final前置顺序违规而FAILED；native READY没有变成全题接受。资格29cf1d7、本机6be924e和PR merge22c0972的CI对象与结论仍分开，本机及远端2 failed没有被修正复审PASS或15项补查覆盖。新增“十项中立正反例”明确SPECIFICATION_ONLY_NOT_EXECUTED；本复审未读取或审查该新增引用，不能背书其内容或数量。

main_disposition的原audit canonical hash cb75335a5fd6525f9bbc35aebf8b4a78c609ec87e9b0c761f9dc8763fb969951、原报告hash、FAIL及五项处置与本角色上轮记录一致。公开副本/完整publication映射不在本bundle，未另行读取或验证。

本次仅哈希、读取限定原文及验证本审查JSON结构；没有重跑独立数字程序、模型、checker、Final或CI，没有Git/网络/安装/新增代理。保留上轮证据范围限制，包括不独立验证全部Git历史、远端事件、原始输入/封存、完整审查transport、平台计量和未列入bundle的资格测试细节。可选的episode预算窗口标题澄清不在本轮五项关闭条件内，不能将预算窗口解释为实际worker连续运行时长。

仅写入own NEW ignored output_002目录。实际命令、clock夹取UTC、exit、工具返回合并输出与hash已保存；工具未提供分别stdout/stderr或精确进程边界时记UNKNOWN，不推断。model/reasoning/token/cash cost均UNKNOWN；新增依赖、工具链及配置0。
