# CLAIM_EVIDENCE_VALIDATION

- Objective：证明每条 Claim 被 current verified Run 和精确 evidence 支持。
- Required inputs：final result、requirement selection、manifest、artifacts；Required outputs：
  `evidence/claim_evidence.json` 的 v2 lineage 与 `evidence/semantic_claim_support.json` 的 v3 view。
- Deterministic gate：绑定 run/manifest/input/code/config/output/decision hashes、artifact IDs、CURRENT/
  无 contradiction；每个 requirement ID 恰有一个唯一合法 Claim ID，Claim text 与真正支持该
  requirement 的 selected output 精确一致，证据路径均存在且在 current state bindings 中；禁止
  把单一结果 Claim 盲映射到所有要求。
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

## `claim-evidence/v3` semantic view

- 每条局部 Claim 必须声明 `claim_id`、`requirement_id`、`claim_type`、`statement`、结构化
  `scope`、`evidence_class`、selected Run/output/metric/comparator IDs、`support_predicates`、
  `uncertainty`、`counter_evidence`、`limitations`、`claim_strength` 和 `status`。
- 类型至少包括 `DESCRIPTIVE`、`EMPIRICAL`、`PREDICTIVE`、`COMPARATIVE`、
  `POLICY_EVALUATION`、`FEASIBILITY`、`OPTIMALITY`、`CAUSAL`、
  `SIMULATION_CONDITIONAL`。本 Gate 只检查结构化谓词，不声称证明任意自然语言蕴含。
- empirical 需要经验来源；simulation conditional 需要已注册假设；comparative 需要 comparator、
  共同 metric 和可比输入；policy 需要实际执行、非零 exposure、comparator、收益和代价；
  feasibility 需要独立约束复算；global optimum 需要证书；causal 需要识别设计；predictive 需要
  冻结验证/held-out 边界。反证必须进入 limitations 或拒绝，不能静默删除。
- `semantic-check` 必须在 v2 hash lineage `claim-check` 后通过。任一局部失败均阻断 aggregate；
  primary coverage 只按 ID 集合判断，文件/Claim 顺序无语义。
