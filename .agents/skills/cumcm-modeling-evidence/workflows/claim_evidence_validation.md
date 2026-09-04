# CLAIM_EVIDENCE_VALIDATION

- Objective：证明每条 Claim 被 current verified Run 和精确 evidence 支持。
- Required inputs：final result、manifest、artifacts；Required outputs：`evidence/claim_evidence.json`。
- Deterministic gate：绑定 run/manifest/input/code/config/output/decision hashes、artifact IDs、CURRENT/无 contradiction；每个 requirement ID 恰有一个唯一合法 Claim ID，Claim text 与 selected output 的 requirement claim registry 精确一致，证据路径均存在且在 current state bindings 中；禁止把单一结果 Claim 盲映射到所有要求。
- Responsibility：Analyst 写最窄 Claim；Engineer提供绑定；Auditor查 stale/contradiction/overbreadth；Orchestrator推进。
- Complete：`FINAL_CANDIDATE → EVIDENCE_VALIDATED`；Reject：unbound decision、旧/异输出、unsupported/contradictory/stale Claim。
- STALE/recovery：证据变化使 Claim/handoff STALE；缩窄或补证后重验，不能润色掩盖。
- Next：`MODELING_TO_PAPER_HANDOFF`。
