# MODELING_TO_PAPER_HANDOFF

- Objective：生成 `modeling-to-paper/v1` 结构化事实包，不写最终论文。
- Required inputs：requirements、source provenance、data sufficiency、requirement selection、final
  Run/portfolio、metrics、robustness、v2 lineage 与 v3 semantic Claims；Required outputs：
  `handoff/modeling_to_paper.json`。
- Deterministic gate：合同全部字段存在、无额外字段/秘密/私有路径；final Run/manifest、Claim、metric、reproduction 与 case evidence chain 精确一致；`approved_by` 仅为机器技术 Gate。
- Responsibility：Engineer 组装数据；Analyst提供公式/符号/limitations；Auditor查完整性；Orchestrator调用 contract Gate。
- Complete：`EVIDENCE_VALIDATED → READY_FOR_PAPER_HANDOFF`；Reject：缺字段、hash断链、伪造人工批准、unsupported claim。
- STALE/recovery：任一依赖变化使整个 handoff STALE；重建而非局部手改。
- Next：交给独立论文组；本 Skill 停止，不承担润色/排版/提交。

- `requirement_traceability` 只覆盖 primary；`claim_evidence` 保留各局部的 scope、limitations 和
  exact lineage。`validation_results.aggregate_claim` 保存独立总体 Claim、完整 primary coverage、
  supporting IDs、scope union、Final decision/Run/manifest/output hashes 及非 primary 状态。
  使用 `build_expected_handoff` 生成，再经 `handoff` Gate 验证；不得手填未 capture 的事实。

- 公式支持旧字符串列表或精确的 `{formula_id, expression, requirements}` 对象；对象中的 ID、表达式、requirement 链接原样保留。拒绝空字段、重复 ID/引用、unknown requirement 或额外字段。aggregate ID 不得与任何局部 Claim ID 冲突。

- RC6 在 `data_quality_report.data_sufficiency` 与 `validation_results` 中保留 data sufficiency、
  requirement selection 和完整 semantic bundle。一个 requirement 不足时不得把 aggregate 标为
  complete；handoff 必须明确 `PARTIAL` 或 Gate 拒绝。旧 v1 handoff 通过纯兼容读取，不回写。
