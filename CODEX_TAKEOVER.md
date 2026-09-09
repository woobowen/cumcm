# PR #12 / RC8 当前恢复入口

2026-09-08 本轮用户已授权完整004C5研发、候选资格与两题陌生C验证，覆盖旧暂停、
TAKEOVER_ONLY与单P0切片限制。授权总窗口自17:46:50 UTC起最多8小时，截止
2026-09-09 01:46:50 UTC；恢复时不得重置预算或假定窗口无限延续。

当前正式状态以 [project_state.json](state/project_state.json) 和其活动计划为准。
本轮恢复摘要见 [DELIVERY_AND_RECOVERY.md](evals/results/phase-004c5/DELIVERY_AND_RECOVERY.md)，
最近检查点见 [checkpoint.md](evals/results/phase-004c5/checkpoint.md)。

- RC8共享subject为`29cf1d7566809519ca92b6a29f555ce0c0b5b204`；激活提交
  `8ef732b45cf3cb04262317cdfa13a176b47eebe0`已在新题输入访问前远端核验。
  候选资格仅限research/Validation。Python包声明0.2.3与competition版本分别解释。
- 2021/2022新增15个Development captures；两题全题科学完成均为false，Final调用0。
  旧v5及历史Validation结果保留。另做1次Q4证书构造，2021预算9/9；原生审核仅支持
  固定参数运输LP第一目标的精确界，未使全题完成。
- 2016 C已有独立审核后的`EVIDENCE_INSUFFICIENT`正式终局，远端提交`a03597b`。
  两个模型实跑成功、三问有条件数值结果，但没有accepted Final或handoff。
  原生审核接受负面决定，并保留时间指标错配及协议过严的科学异议；禁止终局后重跑。
- 2015 C已审核并冻结FAILED，远端提交`6be924e`。两个模型实跑及99个条件窗口保留，
  Final1/test0；正式selection/comparison/robustness在Final后接受，违反冻结顺序。
  首次原生audit FAIL，修订负面决定后Decision Auditor PASS。两题计划2/启动2/实算2/
  终局完成2/科学通过0；均禁止终局后重跑，答案始终封存。
- 候选subject CI通过2153项、1项skip；后续交付CI另有历史固定案例数和终局phase
  路由断言失败。最终内容4c4550d的本机和PR合并提交f5dd6ec实际均为2151passed/2failed/1skip；
  15项后续补查通过，完整CI仍失败。新增registry摘要缺失已修并定向复验。
  综合报告见[FINAL_REPORT.md](evals/results/phase-004c5/FINAL_REPORT.md)，最新交付观察见
  [final_delivery_receipt.json](evals/results/phase-004c5/delivery/final_delivery_receipt.json)。
- PR #12保持Draft，普通push仅到指定任务分支；禁止ready/merge/main push、付费API、
  全局安全配置改动、2025保留题、benchmark-vault及2026当届赛题访问。

以下内容是旧RC7交接记录；其中“当前”“尚未实施”“HF22未修”与模式限制描述的是
原交接时点，不能覆盖本轮显式授权或当前机器状态。原始版本可从接续锚点
`17f109cadc8524c285af6a50776e6c3decb8b3e8`读取。

---

# 新 Codex 独立接手提示词

将以下提示词完整交给新的 Codex。默认模式是 `TAKEOVER_ONLY`；只有用户明确写出
`MODE=RESUME_FIRST_FIX` 才允许进入首个最小修复。

---

你正在接手 `woobowen/cumcm`：一个面向三人 CUMCM 团队、以 C 题为主要目标的 evidence-first
建模 Skill 仓库。你不能依赖之前的聊天、开发者账号、原电脑目录或隐藏配置。仓库根目录记为
`<REPO_ROOT>`。

## 模式

`MODE=TAKEOVER_ONLY`（默认）：只读核验、有限轻量检查、返回接手回执和首项任务建议。不得修改正式
Skill、代码、state、历史证据或文档；不得训练、运行新题/历史题、访问保留题、发布、推送、创建 PR
或合并。

`MODE=RESUME_FIRST_FIX`（仅当用户明确指定）：先完整完成 TAKEOVER_ONLY 核验；确认没有工作区冲突
后，从已核验的 `origin/main` 创建新的功能分支，只处理 `docs/handover/NEXT_STEPS.md` 中 P0 的首个
最小任务。先定位真实调用路径并建立/定位 project-original 最小黑盒复现，再设计最小修复和定向测试。
不要自动展开旧 RC8 大计划，不要自动运行历史题/新题 Validation，不要自动访问 raw input/答案/2025 C，
不要自动发布、Ready PR、合并 main 或修改 GitHub 权限。任何远端交付都需要当前用户另行明确授权。

## 不可改变的当前事实

- 交接基线：`f194c5c0e46708a4b084e63d0beab0ec05b21c09`（PR #10 main merge commit）。若
  `origin/main` 已前进，保留该基线作为历史事实，并核验新增提交；不得 reset、rebase 或回退新工作。
- 正式 Project：`0.3.0-competition-rc7`；正式 Skill：
  `0.2.0-competition-rc7`；架构：
  `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`。
- 当前技术裁决：`C_TARGET_VALIDATION_FAILED`；下一合法研发路线是
  `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`，不是 004D。
- 2017 C 的 9 次冻结候选 Run 全部成功，但实际 controller 在 `GATE_FINALIZATION` 阻断；没有
  accepted Final Run、accepted final Claims 或 accepted paper handoff。
- `HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION` 仍未修：semantic support 与权威 selected output、
  evaluation boundary 和 `NOT_AUTHORIZED/0` test access 相矛盾。
- RC8 尚未实施。分支名、设计文档或提示词都不是实现证据。
- `CUMCM-2025-C-HELDOUT-RESERVED` 继续封存；不得访问标题、题面、附件、参考或答案。
- 项目许可证未决。不要自行选许可证。
- 根 `VERSION`/RC7 manifest/state 使用 Project `0.3.0-competition-rc7`；`pyproject.toml`
  distribution metadata 为 `0.2.3`，同步语义没有明确仓库说明，保持并报告该差异。

## 启动核验

1. 先服从 `<REPO_ROOT>/AGENTS.md` 和目标目录的局部指令。文件操作前的第一个命令必须是
   `ls -la`，并向用户呈现目录约束。
2. 询问并确认这是一次性任务还是长期项目；没有明确执行确认前不写文件。若仅 TAKEOVER_ONLY，保持
   read-only。
3. 安全打印 Git 根、当前分支、HEAD、`git status --porcelain`；核验 origin 指向
   `woobowen/cumcm`，但不要打印 token、认证文件或含凭据 URL。fetch 失败不得解释为分支不存在。
4. 按顺序读：`GOALS.md`、`WORKFLOW.md`、`plans/active/` 的当前文件、
   `state/project_state.json`，再读 `HANDOVER.md`、`docs/handover/STATUS_AND_EVIDENCE.md`、
   `docs/handover/ENVIRONMENT_AND_ASSETS.md`、`docs/handover/RUNBOOK.md` 和
   `docs/handover/NEXT_STEPS.md`。不要递归复制本提示词，不要扫描全部历史大文件。
5. 核验根 `VERSION`、正式 Skill 的 `SKILL.md`/`VERSION`、
   `evals/results/phase-004c4/rc7_release.json`、最新 controller outcome、terminal decision 和
   HF22 challenge。来源冲突列出，UNKNOWN/NOT_VERIFIED 保留。
6. 只在静态确认无副作用后运行轻量检查：CLI `--version`/`--help`、
   `.venv/bin/python scripts/validate_repo.py --strict`、
   `.venv/bin/python scripts/render_status.py --check`、`git diff --check`。缺 `.venv` 时先报告；
   不自动安装数值依赖或重建大型环境。完整 CI 只在用户授权且资源允许时运行一次。

禁止读取 `benchmark-vault/`、答案、2025 C 或 ignored raw input；禁止执行 unaudited third-party code、
调用 nested Codex/API、创建新 Run、重放数值模型、修改 global Codex 配置、打印环境变量/凭据、清理
cache 或把 `.venv`/`.cache` 打包。缺 GitHub 写权限只表示无法远端交付，不妨碍本地只读接手；两者要
分别报告。

## TAKEOVER_ONLY 回执格式

返回：

1. `TAKEOVER_VERIFIED`、`TAKEOVER_PARTIAL` 或 `TAKEOVER_BLOCKED`；
2. 实际 Git root、branch、HEAD、origin/main、工作区状态；
3. Project/Skill 版本与版本面差异；
4. 技术裁决、四个 blockers、RC8 未实施、2025 C 未访问；
5. 实际执行的轻量检查及退出码；历史检查必须单列，不能冒充本次执行；
6. 环境/数据/cache/Git history 缺口和权限边界；
7. P0 首个最小任务建议、证据入口、禁止捷径和预期资源级别；
8. 明确本次未修改、未训练、未运行新题/历史题、未发布。

若为 `RESUME_FIRST_FIX`，在上述回执后另给分支、精确改动、定向测试、仍未做事项和交付状态。没有新
授权不得合并或把修复写成 RC8 完成。

---
