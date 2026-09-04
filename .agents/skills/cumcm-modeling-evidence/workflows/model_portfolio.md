# MODEL_PORTFOLIO_GENERATION / BASELINE_DEFINITION

- Objective：给出机制不同的候选，并定义唯一最简单可复现 baseline。
- Required inputs：formalization、data audit、evidence；Required outputs：`models/model_candidates.json`、候选卡/失败预期。
- Deterministic gate：至少两个候选、恰一 baseline、每个候选有适用条件；不看 test。
- Responsibility：Analyst 提议；Engineer 评估可实现性；Auditor 查 method-first/cherry-pick；Orchestrator 冻结集合。
- Complete：`DATA_AUDITED → MODELS_PROPOSED`；Reject：无 baseline、候选源于 test、没有可证伪条件。
- STALE/recovery：候选集合变化使 experiment/comparison STALE；重新冻结，不追改旧 Run。
- Next：`EXPERIMENT_DESIGN`。
