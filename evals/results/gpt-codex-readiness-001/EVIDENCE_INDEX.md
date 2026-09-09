# Operator kit v1.0.0 证据入口

本目录是用户授权的 `BUILD_OPERATOR_KIT_AND_VERIFY` 支持证据，不是新科学 Gate、第二项目 state 或 RC10 资格升级。当前结果见 [FINAL_REPORT.md](FINAL_REPORT.md)；任务过程及失败见 [WORK_LOG.md](WORK_LOG.md)。

|核验对象|证据|
|---|---|
|真实用户包、38/38 外层与 22/22 内层|[input_audit.json](input_audit.json)|
|网页标准库程序的九项有限算术复核|[input_arithmetic.json](input_arithmetic.json)|
|两条真实网页意见的核查与不可变来源限制|[external_feedback_receipt.json](external_feedback_receipt.json)|
|旧示例中文阅读附页及源字段绑定|[old_reading.md](old_reading.md)、[old_reading_bindings.json](old_reading_bindings.json)|
|受限新 worker 启动、M06 独立建议及算术|[native_worker/view_manifest.json](native_worker/view_manifest.json)、[native_worker/worker_validation.json](native_worker/worker_validation.json)|
|另一原生只读审核及独立程序|[native_audit/REVIEW_SUMMARY.md](native_audit/REVIEW_SUMMARY.md)、[native_audit/view_manifest.json](native_audit/view_manifest.json)|
|新原创 case M01–M14、实际模型/checker/Final|[rehearsal/summary.json](rehearsal/summary.json)、[rehearsal/records.json](rehearsal/records.json)、[rehearsal/public_commands.jsonl](rehearsal/public_commands.jsonl)|
|四次内置 checker 重放的实际回执|[rehearsal/internal_checker_replays.json](rehearsal/internal_checker_replays.json)|
|Final 前置及一次性拒绝|[rehearsal/final_precheck.json](rehearsal/final_precheck.json)、[rehearsal/repeat_final_rejection.json](rehearsal/repeat_final_rejection.json)|
|本地反馈正反练习（不是网页回复）|[rehearsal/feedback_exercise.json](rehearsal/feedback_exercise.json)|
|旧 context 拒绝、同一新工作区持久保存|[rehearsal/stale_context_rejection.json](rehearsal/stale_context_rejection.json)、[rehearsal/workspace_relocation.json](rehearsal/workspace_relocation.json)|
|新 M14 中文结论和符号|[rehearsal/READING_APPENDIX.md](rehearsal/READING_APPENDIX.md)、[rehearsal/reading_bindings.json](rehearsal/reading_bindings.json)|
|经验边界、真实 Bash 操作、定向测试|[lesson_boundary_checks.json](lesson_boundary_checks.json)、[commands/log_manifest.json](commands/log_manifest.json)|
|18 项任务支持验收|[acceptance_matrix.json](acceptance_matrix.json)|
|1989 项历史保护及本次环境变化|[historical_protection_check.json](historical_protection_check.json)、[environment.json](environment.json)|

原始用户 ZIP、原反馈、完整 case、实际运行目录、原生会话原件、最终上传 ZIP 和含本机绝对路径的 DELIVERY_INDEX 留在本地。公开记录中 raw SHA 绑定本机原件，view SHA 绑定公开脱敏文本；有原始 hash 不等于这里提供了原字节。源码只有引用时为 `SOURCE_BYTES_NOT_AVAILABLE_HERE`。

运行 subject：早期模块 `0ad91e3b73228c3fa8b5b77795055bb5d406b8d0`；实际数值与 Final `637d102d2db3a63596a20931df96080a8c29d76f`。最终 CI subject 与远端交付 HEAD 分开记录，不能用后来的文档提交冒充原 Run subject。

恢复时先看本轮 WORK_LOG、Git 状态和 case 的公共 `status/resume`。已消费 Final 不能重跑；新 Git HEAD 后重新导出并核验 context，不改旧 context。下一次真实网页上传与人工验收仍由用户执行。
