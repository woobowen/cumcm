# RC7 honest handover acceptance

Status: `HANDOVER_CONTENT_CHECKED_REMOTE_CI_REQUIRED`

Technical state: unchanged `C_TARGET_VALIDATION_FAILED`
RC8 implementation: `NOT_IMPLEMENTED`

本报告记录 docs-only 交接检查，不是新的技术裁决、科研验收、Skill release 或团队人工审核。正式状态
仍以 [`state/project_state.json`](../state/project_state.json) 为准。

## 范围与基线

- Repository：`woobowen/cumcm`。
- 代码基线：`f194c5c0e46708a4b084e63d0beab0ec05b21c09`，即已合并 PR #10 的 merge commit；
  任务开始时 current RC8 预备分支、`origin/main` 与该 SHA 完全一致，ahead/behind `0/0`。
- 交接分支：`docs/rc7-handover`，从已 fetch/核验的 `origin/main` 创建；RC8 预备分支保留不动。
- 正式 Project/Skill：`0.3.0-competition-rc7` / `0.2.0-competition-rc7`；architecture K1；
  capability `COMPETITION_RC`。
- 本次只允许交接文档、导航、changelog 和 task branch 登记；没有更改 formal Skill、业务/实验实现、
  tests、contracts、state、历史结果或版本。

## 交付文件

- [`HANDOVER.md`](../HANDOVER.md)：团队/接手者第一入口，风险前置。
- [`CODEX_TAKEOVER.md`](../CODEX_TAKEOVER.md)：默认 `TAKEOVER_ONLY`、可选
  `RESUME_FIRST_FIX` 的独立提示词。
- [`docs/handover/STATUS_AND_EVIDENCE.md`](../docs/handover/STATUS_AND_EVIDENCE.md)：四类能力矩阵、
  版本演进和真实案例分母。
- [`docs/handover/ENVIRONMENT_AND_ASSETS.md`](../docs/handover/ENVIRONMENT_AND_ASSETS.md)：依赖、工具、
  ignored raw/cache、tracked derived evidence 与复现限制。
- [`docs/handover/RUNBOOK.md`](../docs/handover/RUNBOOK.md)：接手、只读/写入命令、故障与论文组接口。
- [`docs/handover/NEXT_STEPS.md`](../docs/handover/NEXT_STEPS.md)：P0/P1/P2 可执行任务卡。
- [`docs/handover/handover_manifest.json`](../docs/handover/handover_manifest.json)：说明性快照/索引，
  不驱动 state。
- README、docs index、AGENTS 和 CHANGELOG 的最小交接导航/记录。
- `rules/workflow_rules.yaml` 未改。初次把 `preferred_task_branch` 登记为交接分支会触发冻结的
  `TARGET_WORKFLOW_BRANCH_MISMATCH`；按“不得改 checker/tests”要求恢复旧值。本次
  `docs/rc7-handover` 分支只依据用户对当前交接任务的直接、一次性授权，不把该例外写入未来接手提示词，
  也不永久改变 remote、安全或 `allow_agent_merge=false`。

## 主要证据来源

- 正式 state/current summary：`state/project_state.json` / `reports/current_state.md`。
- RC7 release：`evals/results/phase-004c4/rc7_release.json`、`reports/phase004c4_rc7_release.md`。
- 最新 Validation：`reports/phase004c4_fresh_validation.md`、controller outcome、terminal decision/freeze。
- HF22：fresh integrity audit 与
  `validation/challenges/HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json`。
- 历史题：Phase 004A/004B、C-target batch/RC4 regression、2024 C、2019 C reports 与对应 machine
  records。
- 论文组接口：`contracts/modeling_to_paper.schema.json` 和 `docs/MODELING_TO_PAPER_INTERFACE.md`。
- 官方合规：组委会 2026 AI 使用规定页面于 2026-09-06 返回 HTTP 200；页面日期 2026-08-03，
  规定自 2026-09-01 起试行。交接仍要求队员赛前核对当届规则。

## 已知缺陷保留

以下事实均在首页、状态矩阵、runbook、next steps、takeover prompt 和 manifest 中保留，没有弱化为
“已解决”：

1. `VALIDATION_FINALIZATION_INTERFACE_CONTRACT_FAILURE`；
2. `VALIDATION_FINAL_RUN_NOT_COMPLETED`；
3. `VALIDATION_HANDOFF_NOT_REACHED`；
4. `HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION`。

2017 C 的 9/9 successful attempts 只说明冻结 Development candidates 执行成功；actual controller 仍在
Gate 9 阻断、Gate 10 未到达、test access 0、accepted Final/Claims/handoff 均不存在。RC8/004C5
只作为未实施建议。2025 C 六项访问 flag 仍 false。

## 保护路径 diff

最终核验状态：`PASS_ZERO_PROTECTED_DIFF`。

保护范围包括 `.agents/skills/cumcm-modeling-evidence/`、`src/`、`experiments/`、`scripts/`、
`tests/`、`.github/`、`contracts/`、`state/project_state.json`、`reports/current_state.md`、历史
acceptance/release/Validation reports、`evals/results/`、`benchmarks/case_registry.yaml`、根/Skill
版本、`pyproject.toml` 与依赖声明。预期相对基线零改动；最终结果在提交前用显式 pathspec 核验。

## 本次实际检查

| 检查 | 当前结果 | 边界 |
|---|---|---|
| 首个命令 `ls -la`、Git root/branch/HEAD/worktree | PASS；起点 clean | 不读取 protected vault |
| 脱敏 origin、`git fetch --prune origin`、main/current diff | PASS；origin 正确；基线一致 | 网络 exit 0 |
| PR #10/开放 PR/交接 branch 查询 | PASS；#10 已合入 main；无 open PR；无同名 branch | 查询 exit 0 |
| required startup/source-of-truth/targeted evidence 读取 | PASS | 渐进读取；未读大型 output 或 vault |
| 安全包 metadata、本地目录存在性、non-shallow/Git objects | PASS with documented gaps | 不输出 freeze/token/index；不遍历 2025 |
| formal CLI `--version`/`--help`、controller `--help` | PASS，exit 0 | 只核验入口，不创建 Run |
| 官方 2026 AI 规定页面 | PASS，HTTP 200；访问日 2026-09-06 | 规则仍需队员赛前核对 |
| 文档相对链接/引用路径 | PASS；106 links | 临时标准库 checker，不新增框架 |
| 关键版本/失败结论/RC8/命令标签/私人路径与 secrets 静态审查 | PASS | 只检查新增公开文件；takeover prompt 不含 merge 命令/授权 |
| 保护路径与允许 diff | PASS，零 protected diff；历史 reports 零 diff | 以基线 `f194c5c...` 比较；仅允许交接 docs/navigation |
| `bash scripts/ci.sh` | `FAIL`：`2066 passed / 2 failed / 1 skipped` | 唯一 full run；两项均由交接改动触发：remote URL 重复和 frozen task-branch mismatch；进入文档/config 恢复尝试 1，不重复 full pytest |
| 失败后的精确定向复测 | PASS；`2 passed` | 两个原失败 test；没有重新运行 full pytest |
| `check_target_problem_policy.py --check` | PASS；0 errors | 恢复 frozen task branch 后通过 |
| `validate_repo.py --strict` | PASS；0 errors / 0 warnings | instruction bytes 6960，无 budget warning |
| `render_status.py --check` / `git diff --check` | PASS / PASS | state 未改、generated report current |

## 历史引用检查（不是本次执行）

RC7 acceptance 记录的历史本地 full pytest `2068 passed / 1 skipped`、strict `0/0`、local CI
`2068 passed / 1 skipped`，以及 acceptance subject
`64a7647d8c196e52e6c43f73095a56f232e1a23f` 的 GitHub Actions run `33975187408` PASS，均只作为
历史 evidence。除非当前 PR head 的本地/远端命令实际完成，否则不能把这些数字写成本次复验。

## 未进行的检查与研发

- 未实现 RC8/004C5，未升级 Project/Skill，未修改 formal state/active plan。
- 未下载新题、搜索题解、执行历史数值模型、启动新 Run、训练/fine-tune 或调用 nested Codex/API。
- 未访问 2025 C，未读 benchmark vault/答案，未执行 third-party code。
- 未独立重做科研/semantic 审核；本轮没有声称 independent audit passed。
- 未安装/升级/删除任何系统包、Python 包或 toolchain；未重建环境或清 cache。
- 未生成 Word/PDF/PPT，未打包 raw input、`.venv`、`.cache` 或认证资产。

## 本地资产与复现限制

当前 `.venv`、2017/2018 ignored official-input cache 和 upstream diagnostic cache 目录可见，但不交付。
2017 formal run 的 numpy/pandas/scikit-learn/xlrd 版本有历史记录，然而它们不在当前 `pyproject`
dependencies/lockfile 中；`hatchling` build requirement 当前 `.venv` 不可见。完整 Git history 当前存在，
且历史 checker 依赖 commit/blob。新电脑可读代码和运行部分 core checks，不应据此承诺数值重现。
Project license 仍未决。

## 交接就绪与发布证明

交接资料内容与轻量检查已完成；本地唯一 full CI 的两项交接触发失败已由精确定向复测闭环，但没有
第二次 full run。只有当前 PR head 的远端 full CI、PR 边界和 merge 条件全部通过后，才能将状态改为
`HANDOVER_READY_FOR_MERGE`。实际 PR/VERIFIED_HEAD/CI/merge receipt 通过 GitHub PR 状态和最终评论
记录，避免为写入 merge commit 形成循环提交；本报告不预先声称已合入 main。

Publication evidence：`NOT_CREATED_YET`。
