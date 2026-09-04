# REQUIREMENT_DECOMPOSITION

- Objective：把每个显式/隐式交付转成可测试 requirement ID 与 trace。
- Required inputs：冻结题面、规则；Required outputs：完整 `requirements`、依赖、歧义与 acceptance evidence。
- Deterministic gate：每项有唯一 ID、测试条件且覆盖题面；无静默解释。
- Responsibility：Analyst 拆解；Auditor prosecutor-check；Orchestrator 推进；Engineer 不改语义。
- Complete：Gate PASS 后 `INTAKE_COMPLETE → REQUIREMENTS_VALIDATED`；Reject：漏问、重复 ID、不可验证条款。
- STALE/recovery：题面/规则变化使下游 STALE；修订 requirement 并重建 trace。
- Next：`RESEARCH_AND_SOURCE_PLANNING`。
