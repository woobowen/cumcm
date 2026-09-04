# DATA_AUDIT

- Objective：验证 schema、units、missingness、outlier、bias、lineage 和 leakage 风险。
- Required inputs：immutable raw、字典、requirements；Required outputs：`data/data_audit.json`、processed lineage。
- Deterministic gate：`raw_immutable=true`、每个 raw 与 processed artifact 实际存在且 hash 匹配、处理仅写 derived 并记录可审计 lineage、泄漏字段明确拒绝；二者都绑定 case state。
- Responsibility：Engineer 执行；Analyst 核对语义；Auditor 查 time/group/target/future leakage；Orchestrator 推进。
- Complete：联合 Gate PASS 后 `SOURCES_PLANNED → DATA_AUDITED`；Reject：单位未知、隐式填补、raw mutation。
- STALE/recovery：raw/processing hash 变化使所有 Run 下游 STALE；新 processed revision。
- Next：`MODEL_PORTFOLIO_GENERATION`。
