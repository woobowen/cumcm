# IMPLEMENTATION_AND_EXECUTION

- Objective：实际运行 first-party 模型并捕获 hash-bound manifest。
- Required inputs：accepted plan、审计后的代码/数据；Required outputs：`runs/<run-id>/manifest.json`、outputs/logs。
- Deterministic gate：plan 的 `required_input_hashes` 与 accepted `data_audit.data_hashes` 精确相等并进入 freeze；manifest 的实际 input registry 必须精确覆盖该冻结集合，再绑定实际执行的 code files、可解析 Git commit 与每个 code file 在该 commit 中的 repository blob、config/seed/argv/env/output/outcome/failure/supersession/freeze；input/code/output 均真实存在，逐文件与聚合 hash 一致。
- Responsibility：Engineer 运行；Auditor 查未运行代码/依赖；Orchestrator 登记 Run；Analyst 不改结果。
- Complete：至少 baseline 与一个 candidate 成功，依次 `RUNNING → RUN_COMPLETED → RUN_VALIDATED`；Reject：异常、缺 hash、mutation、非成功冒充成功。
- STALE/recovery：失败/部分/旧 Run 保留且不排名；新 Run ID 重跑并传播 STALE。
- Next：`MODEL_COMPARISON`。

非内置 smoke 必须使用集中 CLI 的 `execute`，不得直接把手工 subprocess 结果标记为
`trusted_capture=true`。case-local Python 必须预注册并绑定 Git blob；runner 自动保留起止时间、
exit code、stdout/stderr/output hashes 和冻结集合。全部候选完成、选择决策 hash 计算后，再用
`seal-run` 生成 manifest。capture 或日志发生任何变化都必须拒绝 manifest 或传播 STALE。
非零 exit 即使已经产生可解析的诊断 output，也必须绑定显式 failure reason 并保留原 output；
不得因 output 存在而生成 `failure=null` 的 FAILED capture，也不得把该 Run 纳入排名。

每个 exit 0 output 必须再次通过与 `preflight-output` 相同的通用 selected-output contract：
覆盖全部 requirement 的唯一 Claim、至少一个有限数值 Final metric、非空 claim scope、
figure-ready data、uncertainty、limitations，以及可复算的定量 robustness perturbations。
执行时失败必须保留原 output，capture 标记 `RC_EXECUTION_OUTPUT_CONTRACT_INVALID`，不得排名。

已解封同题只允许显式标记为 `DEVELOPMENT_REGRESSION`，research plan 必须绑定不可变的首跑
freeze SHA，source ledger 必须记录 `UNLOCKED_AFTER_FIRST_RUN`。除此之外仍只接受
`NOT_ACCESSED`；该例外不得表述为 Validation、Held-out 或 blind evidence。
