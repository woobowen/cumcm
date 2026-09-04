# MODEL_COMPARISON

- Objective：按预注册 validation metric 选择成功模型，再一次性评估 test。
- Required inputs：verified Runs、freeze registry；Required outputs：`results/model_comparison.json`、decision hash、失败 denominator。
- Deterministic gate：freeze registry 必须由 candidate/metric/direction/seed schedule 重新推导并精确相等；candidate×seed attempt 矩阵完整且 baseline 成功；strict finite numeric score；bool/string/NaN/Inf 与 FAILED/PARTIAL/SUPERSEDED 拒绝排名；argmin/argmax/tie 精确。
- Responsibility：Engineer 计算；Analyst 解释；Auditor 查 candidate/feature/threshold/time/group/target/future leakage；Orchestrator 接受决策。
- Complete：Leakage Gate PASS；Reject：baseline 缺失、test 参与选择、未授权/多次 test、selection mismatch。
- STALE/recovery：任一绑定变化使 comparison/final/claim/handoff STALE；按冻结规则重跑。
- Next：`ROBUSTNESS_AND_SENSITIVITY`。
