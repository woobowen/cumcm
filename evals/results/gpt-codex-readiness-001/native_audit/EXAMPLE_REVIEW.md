# EXAMPLE_ONLY 固定包的有限装配检查

结论：**NO_ASSEMBLY_BLOCKER_WITHIN_VERIFIED_FIXED_ARCHIVE**。12 项检查全部通过，未发现本次教学包装配范围内的阻断问题。旧 example/context 的 25 份载荷与已审快照 hash 全部一致，原反馈保持原 case/package 身份，与新例隔离。此结论是装配审核，不授予旧 Final 重跑许可，不是新的科学接受、CI 或人工验收。

受审 ZIP 为 `example-audit.zip`，100878 bytes，SHA256 `8be545f774343af5b2a063dce7f4c0076fe358a78851d6fd37feae3a379798f3`。只读范围为此文件、本 auditor 既有 scratch，以及补充精确授权的旧 `input_snapshot/original_example_context/CONTEXT.md`；该旧 MD 仅作 hash/compare，SHA256 为 `0aa7c92f9641b1854ab86d1eb12c05d0eb1cab434b3abd6d6bff33e9811b33e2`，1286 bytes。没有扩展读取旧 case 或其他资料。

首个 shell 为 scratch 目录 `ls -la`，可见前次冻结报告、finding、核验代码/结果、start/next 提取目录及补证回执。随后自写标准库程序 `example_audit.py` 一次运行成功、退出码 0；具体代码、stdout、逐件 hash、检查和范围见 `example_audit.py`、`example_stdout.txt`、`EXAMPLE_REVIEW.json`。没有运行包内脚本、模型、checker、Final 或 case CLI，没有写 formal state，没有网络访问或新增依赖。

## 装配与身份证据

- 外层 50 个成员无重复，CRC 及安全路径/非符号链接检查通过；49 个载荷逐件 SHA256 与 manifest 一致，payload_set hash 为 `dd3837bdcd42b2894469b2adc403209c6a93df6c01a5a2f2907558d4e93795cf`。28 个离线 Markdown 链接目标均在包内。
- `example/` 的 23 个成员、`context/context.json` 和 `context/CONTEXT.md` 共 25 份旧载荷与已审快照 hash 一致。前 24 份使用前次实际读取的 hash 记录，旧 CONTEXT.md 使用本次新增精确只读授权完成比较，没有未闭合的基线文件。
- 内层身份保持 `ORIGINAL-WATER-MIXED / M14 / revision 1`；package hash 为 `09784e197709c5c5657d5eedac9959c7a72312e0ea30631a7bbeeb46afe05c71`。内层 file/view 与 canonical package hash 再核一致；context canonical hash 仍为 `ae22c16c443303cad2c19eb2fe32b4adbc6ab47e9e1436b68c6d5e4e87efeba9`。旧 CONTEXT.md 的 case、context hash 和模块记录与包内历史 JSON 一致。
- `support/WEB_FEEDBACK_ORIGINAL_WATER_M14.json` SHA256 为 `f44257672f89343d216f45adc6714f61bc4d914614e20f2876ba62370aae3eea`，与原 receipt/input audit 记录一致。九顶层字段、两条 finding 的八字段、location/visible_materials 归属均通过检查；case/module/revision/package 与旧内层 manifest 完全一致。文件的 executed_code=true 描述原网页审核者自写算术，不能改称本轮运行了旧包程序。
- 教学包没有 `review/` 新例载荷，也没有新例 ID `READINESS-COOLANT-001`。五份已审 support 文件（receipt、input audit/arithmetic、old reading/bindings）字节不变；根目录既有操作资料也与本 auditor 原受审内容一致。

## 使用边界的定位

`READ_FIRST.txt` 明示 package kind=EXAMPLE_ONLY、无执行授权、completed example 不可变、仅随包字节离线可见。`START_HERE.md` 最后一段明确旧例不可重跑、READY 不属于新题。`support/EXAMPLE_REVIEW_GUIDE.md` 首段明确源 case 当前不可得，不能声称本机 CURRENT 或重跑 Final；第二段将阅读附页标为 DERIVED_READING_VIEW，并明确原反馈仅绑定旧 case/package、实际未做 native import，状态为 NATIVE_IMPORT_NOT_RUN_IMMUTABLE_SOURCE。

`support/external_feedback_receipt.json` 同时保留 original_root_available=false、original_export_index_available=false、source_current_claimed=false、human_acceptance=NOT_RUN。因此未修改的历史 CONTEXT 标题“当前上下文”和 READY 只描述原快照，在包外教学用途说明下不能当作新题或当前 live case 的事实。没有为导入反馈造索引，也没有更换反馈身份。

旧中文附页、原始反馈和旧数学载荷未变，本次没有重新判断已冻结数值或撤销既有结论。真实外部反馈的来源沿用用户提供的原件及 receipt；本轮没有连接网页独立认证其来源，没有代填用户网页或人工验收。

## 未核范围

本报告不覆盖旧 live case 当前性、完整环境复现、网页重审、native feedback-import、模型/Final 重放或完整 CI。当前包的 operator manifest 仍写 FINAL_AUDIT_CI_PENDING，未计为 CI PASS。主编排器之后如更新描述性 CI 元数据或重建 ZIP，新 archive hash 及新增字段不在本次固定字节检查范围内，需另有差异/完整性证据。原 REVIEW_SUMMARY、RAW_FINDINGS 和前次 F001 closure 均未改写。
