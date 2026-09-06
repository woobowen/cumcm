# P0-03 PREDICTIVE predicate × authoritative facts

Status: `IMPLEMENTED_NOT_RC8`  
Phase candidate: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`  
Branch: `feat/phase004c5-p0-01-finalization-hf22-repro`  
Mode: `RESUME_FIRST_FIX` / P0-03 only  
Skill/Project VERSION: unchanged (`0.2.0-competition-rc7` / `0.3.0-competition-rc7`)

HF22：semantic 声称 `held_out_test_valid=true`，selected Development output 与 test access 明确否定。
本切片让 `GATE_SEMANTIC_CLAIM` 交叉绑定权威 ledger，而不是只检查 predicate 为 true。

## 规则

`validate_runtime_semantic_claims` 对每个 `PREDICTIVE` 且 `held_out_test_valid=true` 的 Claim：

1. 必须存在已验证的 `evidence/final_evaluation_ledger.json`（`evaluate-final` 一次授权）。
2. `count==1`、`max_count==1`、`used_for_selection is false`。
3. `ledger.run_id` ∈ claim `selected_run_ids`（ownership）。
4. capture / Development output / sidecar / `decision_hash` / `authorization_hash` 与 ledger 一致。

没有 ledger、Development `held_out_test_valid=false`、`NOT_AUTHORIZED`、count 0、
`DEVELOPMENT_GROUPED_OOS` 均不能把 predicate 变成 true。Development 指标不得冒充 held-out。
`validate_semantic_claim_support`（无 output 的孤立 RC6 合同）仍只检查谓词是否出现；
**runtime / actual controller 才是 HF22 的 entrypoint**。

因为 G7 早于 G9，合法 PREDICTIVE 必须先 CLI `evaluate-final` 再跑 controller（与 P0-02
`allow_existing` 复验相同）。Controller 独跑且无 ledger 时 PREDICTIVE fail closed。

Aggregate 只在 G7 PASS 后运行，因此未验证的 local PREDICTIVE 不能进入 G8/handoff。

## Reason codes

| Code | 何时 |
|---|---|
| `RC_PREDICTIVE_SUPPORT_CONTRADICTS_SELECTED_OUTPUT` | predicate true 但无合法 ledger（HF22） |
| `RC_PREDICTIVE_TEST_RUN_NOT_OWNED` | ledger run 不是该 Claim 的 selected run |
| `RC_PREDICTIVE_TEST_ACCESS_INVALID` | count / used_for_selection / max_count 不合法 |
| `RC_FINAL_TEST_*` | 复用 P0-02：stale sidecar / authorization hash |

`RC_PREDICTIVE_VALIDATION_MISSING` 仍用于孤立合同缺谓词（E43），不是 HF22。

## 定向命令

```bash
.venv/bin/python -m pytest -q \
  tests/integration/test_p0_03_predictive_cross_bind.py \
  tests/integration/test_p0_01_finalization_hf22_reproduction.py \
  tests/integration/test_p0_02_final_evaluation.py \
  tests/unit/test_fresh_completion_controller.py \
  tests/unit/test_rc6_neutral_evidence_contracts.py \
  tests/integration/test_actual_controller_black_box.py \
  tests/integration/test_actual_controller_neutral_e2e.py \
  tests/integration/test_actual_controller_adversarial.py
```

## 验收对照

| 要求 | 证据 |
|---|---|
| HF22 从错误 PASS 变为确定 BLOCK | `test_hf22_false_heldout_predicate_blocks_semantic_gate`；`test_hf22_false_heldout_blocks_semantic_gate` |
| 合法 predictive PASS | `test_legal_predictive_after_evaluate_final_reaches_handoff` |
| ownership / stale ledger / access count | `test_predictive_wrong_run_ownership_blocks`、`test_predictive_stale_ledger_hash_blocks`、`test_predictive_used_for_selection_blocks` |
| 失败无 accepted Final / aggregate / handoff | G8/G10 不出现；state `RUNNING` |
| 历史 freeze byte-identical | 未改 `test_actual_controller_{black_box,adversarial}.py`、2017 frozen、RC6 test 文件 |
| 禁止 semantic 自证 / diagnostic 当 held-out | 只认 `evaluate-final` ledger |

## 明确不做

RC8；2017 builder/output/challenge 回写；bump VERSION；push / PR；把孤立 `semantic-check` 当成 held-out 授权。
