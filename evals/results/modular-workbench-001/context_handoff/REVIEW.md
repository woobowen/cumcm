# R2 受限 M04 身份复核与独立算术回执

本轮对象：ORIGINAL-BRAIN-R2 / revision 2 / BRAIN-M04 / REQ-A、REQ-B、REQ-C。只复核新身份、保留原数学推导并实际复跑小算例。正式 case、公共代码与 Git 均由主 Agent 唯一写入。本包不是正式 complete 或整题接受结果。

## 身份与恢复

2026-09-09 09:42:56 UTC，实际执行新 root 的 status、resume --request BRAIN-M04、context-verify --context contexts/handoff-r2/context.json，三者 exit 0：

- 原生状态 SOURCES_PLANNED，M01–M03 COMPLETED，M04 PREPARED。
- resume operations 为空、automatic_starts=0。
- context CONTEXT_CURRENT、scripts_executed=0；逻辑 context hash 为 a96abe43c88c87c5f4f0bbd195a726e6d8e3a2e19e811deae3207e83a69254bf。
- 实际公共 identity：commit 7e5bd4297c74cfa3b6c0920bc553d56181097afc；implementation SHA-256 73fbd01944221102b2c3e09ed05f49ca3057ecd7aeb6f23b95fd29f7db9603ff。
- 新 request 字节 hash：90146de24e46d4f40191925e7a934517bd463b2278817bcdde4817ab6c762b1a；新 template 字节 hash：659e503964b17ecdd005e6de2cf8fd97e925282e19e1cb3ef45ee20aa0e70190。
- 新 context 文件字节 hash：bde0b9775630670e8fa7a73089f9988cd8d69c0a009d2ce63cb62bccb8cbf3ef。文件 hash 与逻辑 context hash 是不同对象，未混用。

新 report 和 assumptions 的 case、revision、request、scope 均从实际新 request/template 读取，不手填新的内部 hash。旧 output 和旧 STALE_IMPLEMENTATION 记录保持不变。

## 输入和数学问题复核

实际读取 input-r2 的 12 个文件，并与本人旧 output/tool_record.json 中保存的先前输入 hash/内容对照。未重新打开旧 input 目录。

- input.json、source_ledger.json、TASK.md 及 START_HERE、PROJECT_BRIEF、ROLE_PROMPTS、M04 字节不变。
- problem_requirements 内容除 case_id 外完全一致；包装 content_hash 随身份改变。REQ-A/B/C 目标、单位、依赖和 prediction_spec 未改。
- original.md 未列入直接允许输入，因此没有直接打开；两次 request 登记的 original.md hash 相同。不能把该登记核对表述成重新读取原题文件。
- 独立 Python 的数学函数 AST 完全相同，只调整 main 内的身份断言及输出 revision/implementation 元数据。
- 假设、42 个符号、7 个公式、requirement trace、时长取整分歧及失效条件保持一致。input_comparison.json 保存具体复核结果。

## 实际算术与结构核验

已在 R2 输入上真实执行 independent_m04_check.py，exit 0；新 numerical_results.json 字节 hash 为 8cb9df3543f3e4985ae4705e61f7522aff35f800f6856a1c41292272ca881fd2。所有非身份字段与旧轮算术结果逐字段完全一致，旧轮五个分析文件实际 hash 均未改变。

条件结果仍为：EB 起点 112 min，末拟合水量 10.8 L，斜率 −0.1 L/min，剩余 8 min，备水 8 L；3 L 与 5 L 各一件，成本 11 元；库存 8,7,6,5,4,3,2,1,0 L。120 min 是条件外推终点，未来实际终点 UNKNOWN。

精确有理数核验覆盖容量闭合枚举、9 个需求边界、逐时库存守恒、量纲、信息可见性、零/正斜率及零分母等拒绝情景。EA 的四个历史起点仍属于一个合成实体，不作为未来精度或独立外部验证。不存在原题未给出的置信区间。

Python 语法、JSON 解析、符号唯一性、公式作用域、新 template 根字段与身份匹配已核验。原生 report 空数组元素 schema 仍未在受限包给出，主 Agent 需规范该部分并执行真实 complete；本人没有声称此项已通过。

## 保留的用法缺口

连续 1 L/min 与每个开始分钟整批 1 L 在非整数时长下不同；本例 8 min 两者一致。完整采购单元、零额外初始库存、立即到位、无损耗/限购为显式运营条件，仍待挑战。fixed_demand_litres、baseline_delay、x/y 不代替题意；泛化 scope 标签仍需后续具体绑定。

assumptions_and_symbols.json 是 content-only，未伪造 ACCEPTED 包装或内容 hash。work-report.proposal.json 仅供主 Agent 安装和按原生 schema 规范。独立小算例的 --input-root 参数接收本次给出的扁平输入包目录（input.json、request.json 等同层），不能直接假设它接受原生 case 目录层级。

## 四维范围与文件

执行：R2 复核与私有算术复跑 PASS。工程：上述公共恢复和私有检查 PASS，正式 complete 待主 Agent。科学：原创合成数据上的明确条件算术；未来趋势与运营假设未证实。网页/队员核验 NOT_RUN。

文件全部写在 .cache/modular-workbench-001/restricted-worker/output-r2/：

- assumptions_and_symbols.json：新身份 content-only 提案。
- analysis.md：原数学推导及 R2 说明。
- independent_m04_check.py：身份可复核的独立精确算术程序。
- numerical_results.json：本次真实执行结果。
- work-report.proposal.json：按新 template 绑定身份的原生字段提案。
- input_comparison.json：原件/需求/数学内容对照。
- verification.json：结构、算术一致性与旧证据未变检查。
- tool_record.json：本次全部 9 条 shell/Python 命令、UTC、退出码、输入/输出 hash 和完整回执。
- REVIEW.md：本说明。

所有实际读取均限于新输入包、本人原 output 与新 output-r2。正式 Skill/workflow 沿用本会话此前允许且已读取的 M04 指引；本轮未重读全量文件、producer/checker、历史底稿、其他 case 或网页。原生上下文访问由名单约束，不构成 OS 隔离或严格盲审证明。

没有调用 prepare、complete、run、M05、Final 或 Git，没有新增依赖、工具链或配置。交回主 Agent 正式验收后停止。
