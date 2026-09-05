# MODELING_TO_PAPER_HANDOFF

- Objective：生成 `modeling-to-paper/v1` 结构化事实包，不写最终论文。
- Required inputs：requirements、sources、final Run、metrics、robustness、Claims；Required outputs：`handoff/modeling_to_paper.json`。
- Deterministic gate：合同全部字段存在、无额外字段/秘密/私有路径；final Run/manifest、Claim、metric、reproduction 与 case evidence chain 精确一致；`approved_by` 仅为机器技术 Gate。
- Responsibility：Engineer 组装数据；Analyst提供公式/符号/limitations；Auditor查完整性；Orchestrator调用 contract Gate。
- Complete：`EVIDENCE_VALIDATED → READY_FOR_PAPER_HANDOFF`；Reject：缺字段、hash断链、伪造人工批准、unsupported claim。
- STALE/recovery：任一依赖变化使整个 handoff STALE；重建而非局部手改。
- Next：交给独立论文组；本 Skill 停止，不承担润色/排版/提交。

- `requirement_traceability` 只覆盖 primary；`claim_evidence` 保留各局部的 scope、limitations 和
  exact lineage。`validation_results.aggregate_claim` 保存独立总体 Claim、完整 primary coverage、
  supporting IDs、scope union、Final decision/Run/manifest/output hashes 及非 primary 状态。
  使用 `build_expected_handoff` 生成，再经 `handoff` Gate 验证；不得手填未 capture 的事实。
