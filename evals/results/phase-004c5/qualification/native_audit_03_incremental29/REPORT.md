# PR12 RC8 — native audit03 增量 29cf1d7（冻结）

- 角色：adversarial_evidence_auditor；执行者 `/root/rc8_fact_binding_audit`；独立原生只读增量确认。
- 受测 subject：`29cf1d7566809519ca92b6a29f555ce0c0b5b204`；比较基线：`1b508aabd3948ff0977ac5e77b451fd72b82cc00`。
- 初始和终止 HEAD 均为受测 subject；三个受测工作树文件逐字节等于该 commit，终止复核无漂移。
- 范围严格限于下列三文件 diff 和父任务明确指定的两个 CLI / 两个新增测试。证据仅写本 ignored 目录；未改正式文件、Git、state 或先前 audit03，未启动子代理、联网、读取新题/答案/vault、运行官方模型。

## 结论

本次增量范围内没有发现残留 release BLOCKER。两个历史 checker 将明确的 004C5 阶段加入现有合法 successor 集合；历史 RC5 Skill 和 2019 Validation artifacts 继续按各自冻结 subject 的 Git blob 检验，原历史 artifacts 未由此变更。该结论只覆盖本次三文件增量，不代表候选接受或全 CI 通过。

先前 audit03 的实现结论及科学限制原样继承；本轮没有重新审查模型或科学支持。父编排器仍独立负责完整 CI、准入决定和正式状态。

## Findings 与可复核证据

| ID | 分类 | 定位 | 证据与判断 | 最小建议 |
|---|---|---|---|---|
| I29-01 | 无新增 BLOCKER | `scripts/check_claim_scope_repair.py:31`；新增 successor 第34行 | `01_claim_scope.command.json` 实际 CLI exit 0，`ok=true`、`old_validation_unchanged=true`、`held_out_unchanged=true`。仅扩展合法阶段，历史 subject hash 检查保留。新增测试把原 release 的 cumcm_case.py hash 改成 64 个 0 后精确要求 `RC5_RELEASE_SKILL_DRIFT`，实际通过。 | 保留原件和负例，无需本轮修改。 |
| I29-02 | 无新增 BLOCKER | `scripts/check_c_target_2019c_validation.py:73`；新增 successor 第76行 | `02_2019_validation.command.json` 以 `--check --require-delivery` 执行，exit 0、`ok=true`、pre/terminal frozen=true、workspace_verified=false。新增测试篡改原 terminal controller hash 并重算 freeze payload hash，仍精确触发 `VALIDATION_ARTIFACT_DRIFT`，所以测试覆盖原 subject artifact 绑定。 | 保留原 terminal 结果及原 subject 绑定。 |
| I29-03 | 非 blocker：验证边界 | `tests/unit/test_phase004c5_release_subjects.py:105` 与 `:130` | 两个新增测试实际 `2 passed in 0.63s`、exit 0，每个都有真实 repository 正例和内存篡改历史 hash 负例。未以 monkeypatch 结果替代真实 CLI 结果，两类证据分别保存。 | 后续全 CI 由主编排器另行提供。 |

## 实际命令

1. `.venv/bin/python -B scripts/check_claim_scope_repair.py --check` → exit 0。
2. `.venv/bin/python -B scripts/check_c_target_2019c_validation.py --check --require-delivery` → exit 0。
3. `.venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp <本目录绝对路径>/pytest-temp tests/unit/test_phase004c5_release_subjects.py::test_rc5_history_resolves_its_subject_and_rejects_a_changed_original_hash tests/unit/test_phase004c5_release_subjects.py::test_2019_terminal_artifacts_are_checked_at_original_subject` → exit 0，2 passed。

全部设置 `PYTHONDONTWRITEBYTECODE=1`；精确 argv、cwd、时间、耗时、stdout/stderr SHA256 与 exit code 见三个 `*.command.json`。三个 stderr 均为空。`diff.patch` 是实际 Git diff；`inputs/` 保存实际读取的三文件。

## 输入 SHA256

| 文件 | SHA256 |
|---|---|
| `scripts/check_claim_scope_repair.py` | `9fe1f8aee496a1dc2307d9f3576786a7e1239509acc79f1a820788855b4bb49e` |
| `scripts/check_c_target_2019c_validation.py` | `377ea27307948e116168c90e643134cdb7c8070794a695d0bfb8198cf3256135` |
| `tests/unit/test_phase004c5_release_subjects.py` | `db586a55287e4fa26aba618982f65af8699ab0389277568425a8969d9316402a` |

## 继承的未完成 science 与范围限制

2021：Q4 全局最大值尚无独立证书；原生 A/B 模板缺失；历史压力负面结果保留。2022：独立 model fit 的复算范围有限；未知样本无可验证 accuracy，概率校准与因果解释存在限制。计算一致性和 domain feasibility 已在先前审查中区分；本次历史兼容修复没有增加科学结论。上述限制未被本次 CLI `ok=true` 消除，也不据此自动推出软件 release 必须拒绝或接受。

本轮没有使用 `--verify-workspace`，没有核验原始数据工作区；没有运行完整 CI、官方模型或重做科学检查。本报告不覆盖 subject 之后的行为变更，也不覆盖三文件以外新增实现。

## 前置冻结报告继承链

- `.cache/pr12-rc8/native-audit-03/REPORT.md`：先前已报告 SHA256 `0688807007f1891b231b383b391f45823bec895e1e6b288b90a9c6604afe4f41`。
- `.cache/pr12-rc8/native-audit-03/evidence_index.json`：先前已报告 SHA256 `460c5f7b768cdfc1f6579b4a55f23d9ef9fa09b0caefaec7b6a69c6932c64075`。
- 上述先前文件本次未改写、未重新读取；本报告只增量绑定 `29cf1d7566809519ca92b6a29f555ce0c0b5b204`。
