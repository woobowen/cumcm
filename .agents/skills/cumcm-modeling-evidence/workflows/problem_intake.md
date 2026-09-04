# PROBLEM_INTAKE

- Objective：登记原题、附件、数据和 provenance，不解释答案。
- Required inputs：官方题面/附件、case ID；Required outputs：`problem/problem_requirements.json` 初始范围、raw hashes。
- Deterministic gate：case ID 合法、输入可读、raw 不覆盖、hash 完整。
- Responsibility：Analyst 提取范围；Engineer inventory；Orchestrator 调用 Gate；Auditor 查漏件。
- Complete：accepted artifact 后 `CREATED → INTAKE_COMPLETE`；Reject：缺文件、来源不明、答案材料、raw mutation。
- STALE/recovery：输入 hash 变化使全链 STALE；登记新 derived revision，不覆盖旧件。
- Next：`REQUIREMENT_DECOMPOSITION`。
