# RESEARCH_AND_SOURCE_PLANNING

- Objective：规划 mechanism/method/data/software evidence，先记 gap 再搜索。
- Required inputs：requirements、允许的 search mode；Required outputs：`research_plan.json`、`source_ledger.json`。
- Deterministic gate：外部事实绑定 Source；答案状态为 `NOT_ACCESSED`；query/provenance 可追溯。
- Responsibility：Analyst 规划；Auditor 查 answer leakage；Orchestrator 记录 Gate；Engineer 只用已登记源。
- Complete：`REQUIREMENTS_VALIDATED → SOURCES_PLANNED`；Reject：答案搜索、snippet 当证据、来源缺失。
- STALE/recovery：Source 更新传播到依赖 Claim；补源或保留 gap，不伪造事实。
- Next：`ASSUMPTION_AND_SYMBOL_DEFINITION`。
