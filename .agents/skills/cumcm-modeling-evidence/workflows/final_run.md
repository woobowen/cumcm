# FINAL_RUN

- Objective：冻结 current、successful、reproducible 且通过比较/稳健性的最终 Run 或兼容 Run portfolio。
- Required inputs：comparison decision、requirement selection、manifest、robustness；Required outputs：
  `results/final_result.json` 与 requirement-to-Run/output frozen bindings。
- Deterministic gate：run/output/decision hash 一致；不是 exploratory/failed/partial/superseded/stale。
- Responsibility：Orchestrator 调用 Final Gate；Engineer 提供产物；Analyst 限定结论；Auditor只读复核。
- Complete：`ROBUSTNESS_VALIDATED → FINAL_CANDIDATE`；Reject：未验证 Run、hash mismatch、失败重标、人工叙述绕过。
- STALE/recovery：任何上游变化传播到 final/claim/handoff；保留旧 final 并新建 revision。
- Next：`CLAIM_EVIDENCE_VALIDATION`。

- Final scope 是已捕获的总体 statement；不要求等于第一条 requirement 的局部结论。其支持范围由
  下游 Claim v2 exact lineage、v3 semantic predicates 和 requirement selection 的结构化 union
  验证。任何 primary 未完成时 aggregate completion 必须是 `PARTIAL` 或 `REJECTED`。

- 预测任务只在候选选择后执行一次 `evaluate-final`；开始即消耗预算，失败也保留。最终
  测试后禁止调参、修模型或删除失败。复用账本重验原始输入、完整 code blobs 和 output。
- 非预测任务预登记 `NONPREDICTIVE_FINAL_VERIFICATION` 和空 prediction splits，使用
  各 selected Run 的独立 checker 与数值残差/证书终验；不得伪造预测测试集。controller
  记录科学终验一次、测试访问零次；科学适用性仍由证据审核裁决，READY 或 CI 不等于科学通过。

Development 的无 Final 设计显式设 `evaluation_design.mode=DEVELOPMENT_NO_FINAL_EVALUATION`
与空 `test` split。`evaluation_design` 作为整体进入执行策略 freeze；Final 前不得改它。
科学核验的完整 capture 还需实际冻结 checker 复算对照。原 Run/模型结果不覆盖；核验流水
另存 ignored 路径。冻结后不得基于最终测试反馈修改共享 Skill、模型或重跑模型候选。
