# P0-02 Final evaluation / test-authorization 接口

Status: `IMPLEMENTED_NOT_RC8`  
Phase candidate: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`  
Branch: `feat/phase004c5-p0-01-finalization-hf22-repro`  
Mode: `RESUME_FIRST_FIX` / P0-02 only  
Skill/Project VERSION: unchanged (`0.2.0-competition-rc7` / `0.3.0-competition-rc7`)

本切片补上选择完成后的 **一次、hash-bound** Final test 评估。它不是 RC8、不是 2017 回填、
不是 HF22 semantic 交叉绑定（P0-03）。

## 接口

唯一权威：`cumcm_case.evaluate_authorized_final_test` / CLI `evaluate-final`。

```text
execute (Development only; no sealed-test field)
  → selection decision_hash from development captures
  → evaluate-final --case-root --run-id --decision-hash
       writes runs/<selected>/sealed_test.json
       writes evidence/final_evaluation_ledger.json (count=1, used_for_selection=false)
       refuses to rewrite Development output.json
  → controller G9 verifies ledger or performs the same one-shot
  → GATE_HANDOFF
```

Controller G9：

1. Development output 已有 `sealed_test_metrics_b64`：
   - 非法编码 → `RC_SEALED_TEST_PAYLOAD_INVALID`（保留 AP-002）
   - 合法 payload → `RC_FINAL_TEST_SELF_ATTESTED_IN_DEVELOPMENT_OUTPUT`
2. 字段缺失：调用 `evaluate_authorized_final_test(..., allow_existing=True)`。

CLI `evaluate-final` 使用 `allow_existing=False`（重复访问 `RC_FINAL_TEST_ALREADY_ACCESSED`）。

## Reason codes

| Code | 何时 |
|---|---|
| `RC_FINAL_TEST_PREMATURE` | 计划中的 candidate×seed capture 尚未齐全 |
| `RC_FINAL_TEST_RUN_NOT_SELECTED` | run 不是 comparison winner 的 canonical SUCCESS run |
| `RC_FINAL_TEST_ALREADY_ACCESSED` | ledger 已存在且不允许复验 |
| `RC_FINAL_TEST_SELF_ATTESTED_IN_DEVELOPMENT_OUTPUT` | Development output 自带合法 sealed-test |
| `RC_FINAL_TEST_PAYLOAD_MISSING` | sidecar/ledger 缺 payload |
| `RC_FINAL_TEST_PAYLOAD_HASH_MISMATCH` | sidecar 字节或 decoded hash 与登记不一致 |
| `RC_FINAL_TEST_DEVELOPMENT_OUTPUT_MUTATED` | 评估后 Development output hash 变化，或复验时与 ledger 不一致 |
| `RC_FINAL_TEST_AUTHORIZATION_HASH_MISMATCH` | decision/authorization/ledger 绑定失败 |
| `RC_FINAL_TEST_EVALUATION_FAILED` | 子进程非零、超时、或未写出 sidecar |
| `RC_SEALED_TEST_PAYLOAD_INVALID` | 非法 base64/JSON（AP-002） |

## 定向命令

```bash
.venv/bin/python -m pytest -q \
  tests/integration/test_p0_02_final_evaluation.py \
  tests/integration/test_p0_01_finalization_hf22_reproduction.py \
  tests/unit/test_fresh_completion_controller.py \
  tests/integration/test_actual_controller_black_box.py \
  tests/integration/test_actual_controller_neutral_e2e.py \
  tests/integration/test_actual_controller_adversarial.py
```

## 验收对照

| 要求 | 证据 |
|---|---|
| actual CLI 合法路径到 `GATE_HANDOFF` | `test_authorized_controller_path_reaches_handoff`；neutral per-requirement / portfolio / data-sufficiency handoff |
| 未授权 / 提前 / 非 selected / 重复 / hash 不匹配 fail closed | `test_p0_02_final_evaluation.py` |
| 失败不写 accepted Final/Claims/handoff | `_assert_no_accepted_final`；state 仍 `RUNNING` |
| 禁止 self-attest / 复用 Development 当 Final | Development output 无 `sealed_test_metrics_b64`；Final 仅 sidecar |
| 禁止静默改 Development output | 评估前后 output hash == capture；mutation → `RC_EXECUTION_CAPTURE_OUTPUT_MISMATCH` |
| AP-002 仍为 `RC_SEALED_TEST_PAYLOAD_INVALID`、无 manifest | frozen `test_actual_controller_adversarial.py` 未改字节 |
| 2017 frozen / VERSION / `plans/active` 唯一文件 | 未改 |

## 明确不做

P0-03 HF22 predicate 交叉绑定；RC8 全量；2017 回填；放宽 one-shot；controller 读未登记 raw test；
bump VERSION；push / PR。
