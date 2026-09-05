# MODEL_COMPARISON

- Objective：按预注册 validation metric 选择成功模型，再一次性评估 test。
- Required inputs：verified Runs、freeze registry、逐 requirement metrics/constraints；Required outputs：
  `results/model_comparison.json`、`results/requirement_selection.json`、decision hash、失败 denominator。
- Deterministic gate：freeze registry 必须由 candidate/baseline/split/metric/direction/seed schedule/required input registry/aggregation/selection 重新推导并精确相等；candidate×seed attempt 矩阵完整且 baseline 成功；strict finite numeric score；bool/string/NaN/Inf 与 FAILED/PARTIAL/SUPERSEDED 拒绝排名；argmin/argmax/tie 精确。
- Responsibility：Engineer 计算；Analyst 解释；Auditor 查 candidate/feature/threshold/time/group/target/future leakage；Orchestrator 接受决策。
- Selection Gate：`GLOBAL_JOINT` 要求同一 current sealed successful Run/output 真正覆盖全部 primary；
  `PER_REQUIREMENT` 允许独立问题选择不同 Run；`JOINT_PORTFOLIO` 还必须验证 input/scenario hashes
  和跨问题约束一致。每项绑定自己的 metric、direction、Run、output 和 predicate。baseline 只可
  比较，不得替代零暴露的 policy evidence；tie 只在同一 requirement/metric 内处理。
- Complete：Leakage Gate 与 `selection-check` 均 PASS；Reject：baseline 缺失、test 参与选择、
  未授权/多次 test、selection mismatch、错误 Run/output、metric 错配或 portfolio 不一致。
- STALE/recovery：任一绑定变化使 comparison/final/claim/handoff STALE；按冻结规则重跑。
- Next：`ROBUSTNESS_AND_SENSITIVITY`。
