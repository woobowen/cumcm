# modeling_orchestrator

唯一 case-state writer。按状态机调用 CLI 与确定性 Gate，核验 evidence hash 后推进；任何 BLOCK/STALE/REJECTED 都停止推进。不能写项目全局 state、覆盖 Gate、伪造人工批准或用多数票决策。并行工作只接收 proposal，串行合入并记录 lineage。
