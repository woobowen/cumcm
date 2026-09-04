# EXPERIMENT_DESIGN

- Objective：运行前冻结 questions、splits、candidate set、metric、seed、required input hashes、budget、stop/tie rule。
- Required inputs：portfolio、audited data；Required outputs：`experiments/experiment_plan.json` 与 trusted freeze registry。
- Deterministic gate：train/validation/test 非空不交叠；candidate IDs 与 accepted portfolio 精确相等，baseline 唯一；metric 非空、seed 为唯一 strict integers；`required_input_hashes` 与 accepted `data_audit.data_hashes` 精确相等且所有文件当前；全部进入可信 freeze；`preregistered=true`。
- Responsibility：Engineer 设计；Analyst 核对业务问题；Auditor 查泄漏/重试；Orchestrator 授权执行。
- Complete：`MODELS_PROPOSED → EXPERIMENT_PLAN_VALIDATED → RUNNING`；Reject：post-hoc metric、任意 freeze hash、无 stop rule。
- STALE/recovery：设计改变使 Run/结果 STALE；新 plan revision 与新 Run ID。
- Next：`IMPLEMENTATION_AND_EXECUTION`。
