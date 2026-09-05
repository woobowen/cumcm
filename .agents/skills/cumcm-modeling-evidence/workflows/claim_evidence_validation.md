# CLAIM_EVIDENCE_VALIDATION

- Objective：证明每条 Claim 被 current verified Run 和精确 evidence 支持。
- Required inputs：final result、manifest、artifacts；Required outputs：`evidence/claim_evidence.json`。
- Deterministic gate：绑定 run/manifest/input/code/config/output/decision hashes、artifact IDs、CURRENT/无 contradiction；每个 requirement ID 恰有一个唯一合法 Claim ID，Claim text 与 selected output 的 requirement claim registry 精确一致，证据路径均存在且在 current state bindings 中；禁止把单一结果 Claim 盲映射到所有要求。
- Responsibility：Analyst 写最窄 Claim；Engineer提供绑定；Auditor查 stale/contradiction/overbreadth；Orchestrator推进。
- Complete：`FINAL_CANDIDATE → EVIDENCE_VALIDATED`；Reject：unbound decision、旧/异输出、unsupported/contradictory/stale Claim。
- STALE/recovery：证据变化使 Claim/handoff STALE；缩窄或补证后重验，不能润色掩盖。
- Next：`MODELING_TO_PAPER_HANDOFF`。

## `claim-evidence/v2`

- 保留现有顶层 exact Run/manifest/input/code/config/output/decision/evidence bindings。
  `claim_text` 和 `supported_scope` 保留已捕获 Final statement；它们不必等于任何局部 statement。
- 新增 `contract_version=claim-evidence/v2`、`claim_kind=AGGREGATE_FINAL`、
  `scope_type=REQUIREMENT_UNION`。`claim_id` 为独立 aggregate ID。
- `supported_requirement_ids` 恰好覆盖冻结 trace 的所有 `PRIMARY` ID，不能重复；
  `supporting_requirement_claim_ids` 恰好引用全部互异的局部 Claim ID。顺序不具有语义。
- `requirement_claims` 保留 selected output 的三字段记录：`claim_id`、`claim_text`、
  `evidence_artifact_ids`；不得新增未捕获数值或改写局部文本。
- `aggregate_scope` 为 `{requirement_id: captured_local_claim_text}`，必须逐项由局部支持。
  本合同仅接受明确的 requirement union；任意自由文本的逻辑蕴含不能用字符串相似度证明。
- `requirement_bindings` 为 `{requirement_id: binding}`。每个 binding 包含 `claim_kind=REQUIREMENT`、
  `requirement_id`、`status=ACCEPTED` 和顶层相同的 `run_id`、`run_manifest_hash`、`input_hash`、
  `code_hash`、`configuration_hash`、`output_hash`、`decision_hash`、`evidence_status=CURRENT`、
  `contradiction_status=NONE`。当前 Final 选择唯一 Run，各局部 scope 必须绑定该 Run 自己的输出。
- requirement `role` 允许 `PRIMARY`、`OPTIONAL`、`DIAGNOSTIC`、`SUPPORTING`；旧 trace 缺省为
  `PRIMARY`。非 primary 不进入完整性 coverage；在 `non_primary_requirements` 中逐项记录
  `{role, status: NOT_CLAIMED}`。辅助分析可独立保存，不能用来冒充 primary 结论。
- 从旧格式构造新 artifact 可调用 `derive_claim_contract(content, requirements)`。这只是纯派生，
  不是接受判定；必须随后运行 `claim-check`。该函数不修复无效 hash、不补造 Claim、不修改输入。
