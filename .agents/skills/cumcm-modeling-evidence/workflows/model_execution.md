# IMPLEMENTATION_AND_EXECUTION

- Objective：实际运行 first-party 模型并捕获 hash-bound manifest。
- Required inputs：accepted plan、审计后的代码/数据；Required outputs：`runs/<run-id>/manifest.json`、outputs/logs。
- Deterministic gate：manifest 绑定实际消费的 input files、实际执行的 code files、可解析 Git commit、config/seed/argv/env/output/outcome/failure/supersession/freeze；input/code/output 均真实存在，逐文件与聚合 hash 一致。
- Responsibility：Engineer 运行；Auditor 查未运行代码/依赖；Orchestrator 登记 Run；Analyst 不改结果。
- Complete：至少 baseline 与一个 candidate 成功，依次 `RUNNING → RUN_COMPLETED → RUN_VALIDATED`；Reject：异常、缺 hash、mutation、非成功冒充成功。
- STALE/recovery：失败/部分/旧 Run 保留且不排名；新 Run ID 重跑并传播 STALE。
- Next：`MODEL_COMPARISON`。
