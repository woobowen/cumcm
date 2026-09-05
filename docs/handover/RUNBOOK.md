# 接手与日常运行手册

本文使用 `<REPO_ROOT>`、`<CASE_ROOT>`、`<BRANCH>` 等占位符，不依赖原电脑、账号、主目录、邮箱、
代理或认证配置。命令标签含义：

- `EXISTING_AND_CHECKED`：本次交接已确认命令/入口存在，并实际运行所述轻量调用；完整 CI 的最终结果
  以 [`handover_acceptance.md`](../../reports/handover_acceptance.md) 为准。
- `EXISTING_NOT_RERUN`：入口/文件存在，但本轮为控制成本、避免新 Run 或避免重复历史验证而未执行。
- `PROPOSED_NOT_IMPLEMENTED`：后续建议，不是当前 CLI 能力。

## 1. 定位或下载仓库

```bash
# EXISTING_NOT_RERUN：网络写入新目录；仅在新电脑需要。
# 先从 rules/workflow_rules.yaml 的 git_delivery 读取并人工核验 <REMOTE_URL>。
git clone <REMOTE_URL> <REPO_ROOT>
cd <REPO_ROOT>

# EXISTING_AND_CHECKED：只读。
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1 -uall
git rev-parse --is-shallow-repository
```

期望使用完整 clone；`--is-shallow-repository` 应为 `false`。不要把 ZIP 源码包当作等价替代。查询 origin
时应脱敏 URL；不要输出 credential helper、token 或完整环境变量。`git fetch origin` 会更新 remote
tracking refs 且需要网络；退出非零表示 `NOT_VERIFIED`，不能解释为远端分支不存在。

当前交接基线是 `f194c5c0e46708a4b084e63d0beab0ec05b21c09`。若 `origin/main` 已前进，保留该 SHA
作为历史基线，检查新增提交，不要 reset/rebase/force push。

`preferred_task_branch` 仍被历史 target-policy checker 冻结为已合并 PR #10 的旧分支；本次没有通过
修改 validator 绕过。`docs/rc7-handover` 来自当前用户对这一交接任务的直接、一次性分支/PR 授权，
不延伸到接手者或未来研发。

## 2. 读取规则和状态

按顺序读：

1. [`AGENTS.md`](../../AGENTS.md)
2. [`GOALS.md`](../../GOALS.md)
3. [`WORKFLOW.md`](../../WORKFLOW.md)
4. [`plans/active/`](../../plans/active/) 中的唯一 current plan
5. [`state/project_state.json`](../../state/project_state.json)
6. [`HANDOVER.md`](../../HANDOVER.md) 与本目录其余交接材料
7. [formal Skill `SKILL.md`](../../.agents/skills/cumcm-modeling-evidence/SKILL.md)

`reports/current_state.md` 是生成物，不能手工修改；摘要冲突时以 source-of-truth map 指定的机器源为准。
不要递归读取全部历史大文件，也不要读取 `benchmark-vault/`、答案或 2025 C。

## 3. 核验版本与环境

```bash
# EXISTING_AND_CHECKED：只读文件/CLI metadata。
sed -n '1p' VERSION
sed -n '1p' .agents/skills/cumcm-modeling-evidence/VERSION
.venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py --version
.venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py --help
.venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py status --help
```

根 Project 应为 `0.3.0-competition-rc7`，Skill 应为 `0.2.0-competition-rc7`。
`pyproject.toml` distribution metadata 的 `0.2.3` 是另一个未说明同步语义的版本面，不要擅自修改。

```bash
# EXISTING_NOT_RERUN：会创建/修改 .venv、安装 core/dev 包并可能联网。
bash scripts/bootstrap_dev_env.sh
```

缺 `.venv` 时先报告。只有任务明确需要并允许环境变更时才运行 bootstrap，并保存安装日志。它不声明
具体 case 所需的 numpy/pandas/scikit-learn/xlrd 数值栈，不能据此承诺历史数值重现。

## 4. 轻量状态与验证

先静态检查脚本副作用。本次已确认 `validate_repo.py --strict` 仅输出验证结果（不传 `--json-out`），
`render_status.py --check` 只比较生成内容，`cumcm_case.py --help/--version` 不写 case；
`scripts/ci.sh` 调用 ruff、pytest、历史 read-only checkers、strict 和 `git diff --check`，不启动正式模型
或新赛题 Run，但工具可能更新 ignored `.pytest_cache`/`.ruff_cache`。

```bash
# EXISTING_AND_CHECKED：本次交接的最终实测状态见 acceptance report。
.venv/bin/python scripts/validate_repo.py --strict
.venv/bin/python scripts/render_status.py --check
git diff --check

# EXISTING_AND_CHECKED：本轮唯一 full run 已执行；失败与定向闭环见 acceptance report。
bash scripts/ci.sh
```

`scripts/ci.sh` 已含 full pytest，不要先重复跑一次 full pytest。历史报告中的 `2068 passed / 1 skipped`
只属于历史 RC7 acceptance；只有本次实际运行并绑定当前工作树/PR head 的输出，才能写成本次结果。

查看一个现有 case state：

```bash
# EXISTING_NOT_RERUN：只读 case_state.json；<CASE_ROOT> 必须由使用者明确选择。
.venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py \
  status --case-root <CASE_ROOT>
```

不要为了让该命令成功而访问或复制 ignored official input。没有本地 case workspace 时，报告
`LOCAL_CASE_ASSET_MISSING`，仍可完成代码/状态接手。

## 5. 选择定向测试

先定位最小受影响入口，再运行相应 project-original fixture；不要把“多跑历史题”作为首个修复验证。

```bash
# EXISTING_NOT_RERUN：P0 Finalization/controller 的定向测试集合；本次交接未单独重跑。
.venv/bin/python -m pytest -q \
  tests/unit/test_fresh_completion_controller.py \
  tests/integration/test_actual_controller_black_box.py \
  tests/integration/test_actual_controller_neutral_e2e.py \
  tests/integration/test_actual_controller_adversarial.py

# EXISTING_NOT_RERUN：只读核对已冻结 2017 terminal/audit，不运行模型。
.venv/bin/python scripts/check_phase004c4_fresh_validation.py --check --require-delivery
```

测试若失败，先定位首个稳定 reason code；最多三轮“根因—修复—定向复测”。不得通过改历史 artifact、
删失败测试、放宽 validator 或修改 frozen case 来消除失败。

## 6. 只读命令与会产生新状态的命令

| 命令族 | 当前标签 | 副作用/用途 |
|---|---|---|
| `--help`、`--version` | `EXISTING_AND_CHECKED` | 只读 CLI metadata |
| `status` | `EXISTING_NOT_RERUN` | 读取 `<CASE_ROOT>/case_state.json` |
| `manifest`、`claim-check`、`data-sufficiency`、`selection-check`、`semantic-check`、`compare-check` | `EXISTING_NOT_RERUN` | 读取并验证指定 case artifacts；Gate BLOCK 可是正确结果 |
| `validate --check`、`stale-check --check`、`finalize --check`、`handoff --check` | `EXISTING_NOT_RERUN` | check 模式不推进 state；仍需明确 case root |
| `init --dry-run`、`smoke --dry-run` | `EXISTING_NOT_RERUN` | 返回计划/shape，不创建 workspace |
| `init`（无 dry-run） | `EXISTING_NOT_RERUN` | 创建新 case workspace |
| `execute` | `EXISTING_NOT_RERUN` | 执行 frozen case-local Python，写 capture/stdout/stderr/output；是新 Run 行为 |
| `seal-run` | `EXISTING_NOT_RERUN` | 复核 capture 后写 manifest |
| `validate`/`stale-check`/`finalize`/`handoff`（无 `--check`） | `EXISTING_NOT_RERUN` | 可能推进/改变 case state 或写 handoff |
| `smoke`（无 dry-run） | `EXISTING_NOT_RERUN` | 运行 project-original synthetic E2E 并写 workspace |
| `scripts/finalize_fresh_c_validation.py` | `EXISTING_AND_CHECKED`（仅 help） | 实际调用会写 trace/artifacts/state；不要在 TAKEOVER_ONLY 运行 |
| `authorize-final-evaluation` 等未来命令 | `PROPOSED_NOT_IMPLEMENTED` | 当前 CLI 不存在；不得写成已有能力 |

## 7. 查看历史结果

- RC7 release：[`rc7_release.json`](../../evals/results/phase-004c4/rc7_release.json)
- 最新 controller block：[`controller_outcome.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/controller_outcome.json)
- 最新 terminal decision：
  [`DECISION-C-TARGET-VALIDATION-004C4.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/DECISION-C-TARGET-VALIDATION-004C4.json)
- HF22：[`HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/validation/challenges/HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json)
- 完整案例矩阵：[`STATUS_AND_EVIDENCE.md`](STATUS_AND_EVIDENCE.md)

优先读小型 summary/decision/freeze，不反复加载大型 `output.json`。历史 checker 返回 BLOCK/REJECTED
不一定是检查失败：若 frozen expected outcome 本来就是负向，checker 应验证“仍然按同一原因阻断”。

## 8. 状态语义

- `BLOCK`：当前 Gate 输入/状态不满足，禁止推进；它可以是 fail-closed 测试的预期通过结果。
- `REJECTED`：case 的终止状态，失败证据保留，不能重标为成功。
- `STALE`：上游 hash/依赖变化使下游 artifact 失效；要从最早受影响环节产生新版本/Run，不能覆盖旧件。
- `RUN_COMPLETED` 不等于 `RUN_VALIDATED`；文件存在不等于 accepted；native schema 通过不等于 rubric 或
  paper dispatch 被接受。

2017 C 当前是 `RUNNING_BLOCKED_NOT_READY_FOR_PAPER_HANDOFF` 的冻结 terminal episode；正式 project
technical adjudication 为 `C_TARGET_VALIDATION_FAILED`。不要为“状态好看”推进或改写它。

## 9. 常见故障

- 网络/TLS：记录命令、时间、exit 和错误类别；最多按任务授权做有限重试。网络失败不能证明远端资源
  不存在。
- 缺 core 依赖：报告 `.venv`/package 缺失；是否运行 bootstrap 由当前任务决定。
- 缺 numerical dependency/raw input：停止数值执行，报告 `NOT_REPRODUCIBLE_LOCALLY`；不从非官方来源
  猜测补齐。
- Git 历史缺失：若 shallow/ZIP，获取完整 Git history 后再跑 blob-bound checker。
- checker BLOCK：先确认它是否在验证历史负向结论；不要把预期 BLOCK 当作新的科研失败，也不要把
  checker exit 0 写成 Validation PASS。
- Git 工作区有不明修改：不得 reset、clean、stash 或覆盖；列出路径，无法确认归属时停止写入。

## 10. 安全中断、恢复与论文组交接

中断时记录当前 branch/HEAD、工作区路径清单、已运行命令/exit、首个未完成步骤和 blocker。新会话重新
读取 truth chain，不依赖聊天记忆。不要自动清 cache、删分支或重跑 frozen episode。详细规则见
[`docs/RECOVERY.md`](../RECOVERY.md)。

只有 case state、Final Run、Claim 和 handoff Gate 全部接受后，才能把
`handoff/modeling_to_paper.json` 交给论文组。唯一合同是
[`contracts/modeling_to_paper.schema.json`](../../contracts/modeling_to_paper.schema.json)，接口说明见
[`MODELING_TO_PAPER_INTERFACE.md`](../MODELING_TO_PAPER_INTERFACE.md)。论文组必须保留 requirement、公式/
符号、Run/metric、表格/作图数据、来源、uncertainty、limitations 与 reproduction lineage。2017 C 和
2019/2024 的候选 handoff 均不能作为已审核通过的最终论文依据。
