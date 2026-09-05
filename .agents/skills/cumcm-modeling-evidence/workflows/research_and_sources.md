# RESEARCH_AND_SOURCE_PLANNING

- Objective：规划 mechanism/method/data/software evidence，先记 gap 再搜索。
- Required inputs：requirements、允许的 search mode；Required outputs：`research_plan.json`、
  `source_ledger.json` 与必要的 acquisition plan。
- Deterministic gate：外部事实绑定 Source；每个 Source 记录 requirement IDs、evidence class、
  provenance、authority、retrieval/licence、geographic/time/entity scope、field schema、hash、
  freshness、limitations；答案状态为 `NOT_ACCESSED`；query/provenance 可追溯。
- Responsibility：Analyst 规划；Auditor 查 answer leakage；Orchestrator 记录 Gate；Engineer 只用已登记源。
- Complete：`REQUIREMENTS_VALIDATED → SOURCES_PLANNED`；Reject：答案搜索、snippet 当证据、来源缺失。
- STALE/recovery：Source 更新传播到 data sufficiency、Run 和 Claim；补源后重新检查，获取失败则
  对应 requirement 结构化阻断，不伪造事实或把公开参考材料中的派生数据当原始事实。
- Next：`ASSUMPTION_AND_SYMBOL_DEFINITION`。
