# 读取和核验记录的口径

`read_inventory.json` 是 `audit.py` 实际读取字节和 SHA256 的记录；同一文件多次读取允许重复行。其中目的字段中的“parsed/static reviewed”描述该类记录的用途，不代表每个字符串都经全文语义审阅。以下给出实际语义范围，优先于模糊用途标签。

- 全文操作文档：固定 start 包的 START_HERE、BRAIN_START、BRAIN_RESUME、OPERATOR_PLAYBOOK、WEB_PACKAGE_TRIAGE、REVIEW_EXCHANGE_GUIDE、CODEX_REVIEW_FOLLOWUP、PAPER_FACT_HANDOFF、KNOWN_LIMITATIONS、CODEX_MODULE_REQUESTS 的全部 M01–M14、WEB_REVIEW_PROMPTS 全部 A–E、WEB_ALTERNATIVE、EXPERIENCE_CARDS 全部 L01–L12、operator_kit_manifest。PROMPT_INDEX 与 experience_index 只读 hash/结构，不称全文语义研究。
- 新包数学内容：original、analysis、assumptions/symbols、producer、checker 全文静态阅读；input、plan、modeling_to_paper、两 output/checker/capture、Final ledger、M14 report、context、reading appendix/bindings/summary 按本次审核字段解析。代码只 AST 解析，不导入执行。
- 旧包数学内容：analysis、符号表全文；raw input、plan、handoff 的 claim/selection/source、两 output、checker 最优证据、manifest、context 按核验字段解析。old_reading 全文及 bindings 所有行核对。没有运行旧 producer/checker。
- 正式 CLI：cumcm_workbench.py 的 parser 686–757 行、相关命令定位；review_exchange.py 的导出/读包边界 1–110 行、导入与处置 207–388 行。仅静态核命令/schema，不调用 CLI。
- 工具代码：package_operator_kit.py 的 18–173 行静态核 canonical、verify、三类包 build 与提示词构造；rehearse.py 及 rehearsal/model.py/analysis.md 当前版本仅按 operator manifest 逐件 hash 对照，其中模型和分析与新 review 字节相同已读。未执行这些工具。
- 本地证据：input_audit 的来源/摘要与身份、input_arithmetic 全部比较值、external_feedback_receipt 全文、rehearsal summary、repeat rejection、internal checker replay receipts、feedback_exercise 的反馈与命令结果全文；public_commands 全部 JSON 解析并筛选 run/controller 顺序。records.json 的 157 个 view 全部 hash 检查，重点解析 source_ledger、model_comparison、scientific_final_ledger 及 Run 对应条目；其余仅完整性检查，不称 157 份全文专业审阅。
- native_worker：完整阅读启动摘要、原始3 finding、NO_CASE 回答、M06恢复回答、worker_validation；verification/m06_verification、命令日志、limited arithmetic 输出及候选材料的身份/适用范围核对。其余列入清单的 worker 文件仅字节 hash；没有重执行 worker 脚本，也未读取未授权原 worker ZIP。

早期交互式 shell/Python 仅用于目录/ZIP 成员枚举、打印允许文本、JSON 摘要和 hash；没有 case 程序执行。实质可重现核验已集中保存于 audit.py 及 audit_stdout.txt。首个命令 `ls -la` 的原始结果在本次工具会话；其中目录存在不代表后续获准读取。

本轮 `.venv/bin/python audit.py` 一次运行成功，没有失败后重试，没有新增环境包/配置。所有输出仅当前 scratch。最终包若变化，另存复核证据，不覆盖 RAW_FINDINGS.json 或本次 stdout/result。
