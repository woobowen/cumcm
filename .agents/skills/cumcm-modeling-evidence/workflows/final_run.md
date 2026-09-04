# FINAL_RUN

- Objective：冻结 current、successful、reproducible 且通过比较/稳健性的唯一最终候选。
- Required inputs：comparison decision、manifest、robustness；Required outputs：`results/final_result.json` 与 frozen Run binding。
- Deterministic gate：run/output/decision hash 一致；不是 exploratory/failed/partial/superseded/stale。
- Responsibility：Orchestrator 调用 Final Gate；Engineer 提供产物；Analyst 限定结论；Auditor只读复核。
- Complete：`ROBUSTNESS_VALIDATED → FINAL_CANDIDATE`；Reject：未验证 Run、hash mismatch、失败重标、人工叙述绕过。
- STALE/recovery：任何上游变化传播到 final/claim/handoff；保留旧 final 并新建 revision。
- Next：`CLAIM_EVIDENCE_VALIDATION`。
