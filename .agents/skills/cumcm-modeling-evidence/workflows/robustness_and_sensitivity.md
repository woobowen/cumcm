# ROBUSTNESS_AND_SENSITIVITY

- Objective：量化参数、输入、约束和假设扰动及 failure modes。
- Required inputs：selected verified Run、预注册扰动；Required outputs：`results/robustness.json`、uncertainty、failure cases。
- Deterministic gate：至少一个实际扰动、完整结果、失败不隐藏、结论不超出范围。
- Responsibility：Engineer 运行；Analyst 解释 validity；Auditor 查只报好结果；Orchestrator 绑定 Run。
- Complete：comparison 与 robustness 均 PASS 后 `RUN_VALIDATED → ROBUSTNESS_VALIDATED`；Reject：未运行、丢失败、无 lineage。
- STALE/recovery：模型/数据/扰动变化使 final 下游 STALE；新 robustness revision。
- Next：`FINAL_RUN`。
