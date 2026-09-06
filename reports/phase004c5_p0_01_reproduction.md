# P0-01 Finalization / HF22 调用路径复现

Status: `REPRODUCTION_FROZEN_NO_PRODUCTION_MUTATION`  
Phase candidate: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`  
Branch: `feat/phase004c5-p0-01-finalization-hf22-repro`  
Baseline: `e1286b1f734ef1d23cfbfc2bb87fee5358dab212` (`origin/main` after PR #11)  
Mode: `RESUME_FIRST_FIX` / P0-01 only

本文件冻结最小黑盒复现、字段权威与建议修复面。它不是 RC8 实现、不是新的 Validation、不是
正式 release。未修改 formal Skill、`state/project_state.json`、2017 frozen episode 或
`plans/active/` 唯一计划。

## 定向命令与冻结 reason code

```bash
.venv/bin/python -m pytest -q \
  tests/integration/test_p0_01_finalization_hf22_reproduction.py
```

| Fixture | 当前 RC7 观察（已断言） | 内层/未来 code（未实现，不断言为当前行为） |
|---|---|---|
| 无合法 final payload | Gate 9 `GATE_FINALIZATION` `BLOCK`，`RC_GATE_EXECUTION_FAILED`；Gate 10 未到达；`test_access_count=0`；state `RUNNING` | 内层 `VALIDATION_SEALED_TEST_PAYLOAD_MISSING` 被 `GateTrace.invoke` 丢掉，因为不以 `RC_` 开头 |
| HF22 假 held-out 声明 | `GATE_SEMANTIC_CLAIM` 与 `GATE_AGGREGATE_CLAIM` 为 `PASS`，尽管 selected output 为 `DEVELOPMENT_GROUPED_OOS` / `NOT_AUTHORIZED` / count `0` / `held_out_test_valid=false` | 建议 P0-03：`RC_PREDICTIVE_SUPPORT_CONTRADICTS_SELECTED_OUTPUT` |

禁止：mock actual CLI；只测 helper；预塞 test payload 进 Development execute；修改 2017 builder/output。

## 调用时序与字段权威

```text
execute_case_code
  argv: case-root, run-id, candidate-id, seed, code-path, timeout
  writer: case-local model → runs/<RUN>/output.json
  capture: execution_capture.json (output sha256)
  无 final-phase / test-authorization 输入
        │
        ▼
requirement_selection + semantic_claim_support
  writer: orchestrator / post-selection builder（2017 为 frozen builder）
  当前 semantic predicate 可与 output 事实无关
        │
        ▼
scripts/finalize_fresh_c_validation.py complete()
  G1 requirement → G2 source → G3 data-sufficiency
  G4 comparison/selection（preview manifests，尚未持久化）
  G5 run eligibility → G6 compatibility
  G7 validate_runtime_semantic_claims
       └─ validate_semantic_claim_support
            PREDICTIVE: 仅检查 predicate is True
  G8 aggregate mapping
  G9 validate_runtime_finalization
       + _decode_selected_test(selected output, sealed_test_metrics_b64)
       失败 → RC_GATE_EXECUTION_FAILED；不写 manifests；不访问 test ledger
  G10 handoff（仅 G9 PASS 后）
```

| 字段 | 唯一权威（应然） | RC7 实际谁可写 | 何时可访问 test |
|---|---|---|---|
| Development `validation_metrics` | selected Run `output.json` via `execute` | case-local model at execute | 否 |
| `sealed_test_metrics_b64` | 一次授权的 post-selection Final evaluation | 现有 synthetic 模型在 Development execute 预写；诚实 2017/本 fixture 不写；controller 在 G9 解码 | 选择完成后、G9 才应授权一次 |
| `evaluation_boundary` / `held_out_test_valid` on output | 同一 selected output + test-access ledger | 模型/builder 可自报；Gate 不核对 | 未授权时必须为 false |
| `support_predicates.held_out_test_valid` | 应从权威 output/ledger 派生或逐字段 cross-bind | semantic artifact 可无条件填 true（HF22） | 无 |
| test-access ledger | controller `_record_selected_test_access` | 仅 G9 PASS 后写入；BLOCK 路径 count=0 | 一次性 |
| Final / Claim / handoff | G9/G10 接受后的 artifacts | G9 失败则不产生 accepted Final | 无 accepted handoff |

现有 contract **表达不出**“Development SUCCESS 且尚未授权 Final test”的合法状态：controller 要求 selected output 已携带 sealed payload，而 released `execute` 不能合法产生该字段。

## 根因（代码，非 2017 题面）

1. **Finalization 接口**  
   `execute` CLI（`cumcm_case.py` L5209–5215）无 final/test 授权。  
   `validate_selected_output_contract` 不要求 `sealed_test_metrics_b64`，故诚实 Development Run 可 SUCCESS。  
   `complete()` G9 在 `validate_runtime_finalization` PASS 后无条件 `_decode_selected_test`。  
   现有 controller tests 把 payload 预写进 Development 模型，因此 **不能** 复现 2017。

2. **HF22**  
   `validate_semantic_claim_support` L908–911 对 PREDICTIVE 只要求两个 predicate 为 true。  
   `validate_runtime_semantic_claims` L1313 并入该结果，不读 output 的 `evaluation_boundary` / `test_access_*` / `held_out_test_valid`。  
   `E43_PREDICTION_WITHOUT_TEST` 只覆盖缺 predicate，不覆盖“predicate=true 且权威事实为 false”。

## 建议修复面（P0-02 / P0-03，本次不实施）

唯一权威的 post-selection Final evaluation contract：

- 授权、test-access ledger、input/output/capture/manifest/decision hash、一次性时序均可验证。
- Development output 不得携带可冒充 Final 的 self-attested payload。
- 未授权、非 selected、重复访问、hash 不匹配一律 fail closed。
- `_decode_selected_test` 的内层 reason 应保留为稳定 `RC_` code，而不是吞成 `RC_GATE_EXECUTION_FAILED`。

Semantic predicate 必须交叉绑定权威 selected Run/output/evaluation boundary/authorization/test-access；缺失/UNKNOWN/矛盾 fail closed。  
不要让所有题型强制提供监督学习 test-set 指标。

## 明确不修改

formal Skill 生产代码、VERSION、2017 terminal/decision/output/builder、`state/project_state.json`、
历史 Validation verdict、`plans/active` 唯一文件、论文组交接包。

## 恢复

目标：P0-01 复现已冻结。  
下一步安全操作：仅在新授权下做 P0-02 或 P0-03；不 push（本次用户要求先不远端交付）。  
保留题：2025 C 仍封存，不得访问。
