# ASSUMPTION_AND_SYMBOL_DEFINITION

- Objective：把 requirements 映射为假设、符号、units、公式、目标与约束。
- Required inputs：requirements、sources、数据语义；Required outputs：`models/assumptions_and_symbols.json`。
- Deterministic gate：符号唯一、units 一致、假设可挑战、公式 trace 到 requirement。
- Responsibility：Analyst 起草；Engineer 数值/维度交叉检查；Auditor 攻击假设；Orchestrator 绑定证据。
- Complete：artifact accepted 并与 Data Gate 联合推进；Reject：未定义符号、隐藏假设、方法先行。
- STALE/recovery：假设/符号变化使模型、Run、Claim STALE；新 revision 重验。
- Next：`DATA_AUDIT`。
