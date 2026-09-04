# FAILURE_RECOVERY

- Objective：在不丢失失败证据、不修改 raw/旧 Run 的前提下恢复。
- Required inputs：BLOCK/STALE/REJECTED reason codes 与 dependency chain；Required outputs：修复 proposal、新 revision/Run ID、复验记录。
- Deterministic gate：根因对应 fault-injection test；state/history 不得手改跳级；每次推进先检查已绑定依赖；旧 artifact 保留；新 hash lineage 完整；修复不放宽 Gate。
- Responsibility：Auditor提出最小反例；Engineer/Analyst按边界修；Orchestrator串行应用并重验。
- Complete：原失败仍可追溯且触发 Gate 现 PASS；Reject：删除测试、吞异常、重标失败、直接写 READY。
- STALE/recovery：从最早变化依赖开始重跑全部下游；不得清除历史或建立第二 state truth。
- Next：返回被阻断阶段；若无法恢复则保持 `REJECTED` 并报告 blocker。
