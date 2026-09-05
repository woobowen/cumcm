# DATA_AUDIT

- Objective：验证 schema、units、missingness、outlier、bias、lineage 和 leakage 风险。
- Required inputs：immutable raw、字典、requirements 与 source ledger；Required outputs：
  `data/data_audit.json`、processed lineage、`data/data_sufficiency.json`。
- Deterministic gate：`raw_immutable=true`、每个 raw 与 processed artifact 实际存在且 hash 匹配、处理仅写 derived 并记录可审计 lineage、泄漏字段明确拒绝；二者都绑定 case state。
- Responsibility：Engineer 执行；Analyst 核对语义；Auditor 查 time/group/target/future leakage；Orchestrator 推进。
- `DATA_SUFFICIENCY_PREFLIGHT`：逐 primary requirement 输出 `SUFFICIENT`、
  `ACQUISITION_REQUIRED`、`PARTIAL`、`UNSATISFIABLE_WITH_CURRENT_INPUTS` 或 `UNKNOWN`，并记录
  missing fields/entities/time、candidate sources、cost/time、allowed/forbidden substitutions 与
  affected stages。`UNKNOWN` 不得当作 sufficient；simulation/assumption 不得支持 empirical。
- Complete：联合 Gate PASS 后 `SOURCES_PLANNED → DATA_AUDITED`；只有 `SUFFICIENT` 或受限
  `PARTIAL` 才能继续候选建模。`ACQUISITION_REQUIRED` 先获取、hash-bind 并复检；Reject：单位
  未知、隐式填补、raw mutation、provenance/licence 缺失或证据范围不足。
- STALE/recovery：raw/processing hash 变化使所有 Run 下游 STALE；新 processed revision。
- Next：通过 `data-sufficiency` 后进入 `MODEL_PORTFOLIO_GENERATION`；未通过时不得进行与缺失
  requirement 无关的昂贵调参，aggregate final 不得声称完整。
