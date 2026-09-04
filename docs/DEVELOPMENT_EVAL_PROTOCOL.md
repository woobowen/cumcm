# Phase 004 Development and C-Target Batch Eval Protocol

## 目的

直接用 `cumcm-modeling-evidence` Competition RC1 对一道答案仍封存的历史 Development 题做完整盲跑，以真实失败形成 RC2。这里不重新设计 Benchmark，也不以历史答案训练 Validation/Held-out。

Phase 004C 将单题迭代扩展为 batch-first-run：同一个冻结 RC3 依次运行三道结构不同的 C
Development 题；三题全部形成独立、远端核验的 first-run freeze 前，禁止修改正式 Skill 或解封任一
case 的参考材料。之后只进行一次统一 cross-case 修改决策，并用 C 题执行正式 Validation。

## C-target batch-first-run 规则

- Batch ID 固定为 `C-TARGET-BATCH-001`，三个 position 在结果出现前冻结；fallback 只能因官方输入
  不可用或预先确认污染而触发，不能按结果难易选择。
- 每个 fresh worker 只读冻结 RC3 和自己的 ignored case workspace，只写自己的 case 目录；不得读取
  peer case、共享 state、registry、Plan、Skill 或 peer 输出。共享状态和 Git 里程碑只由主
  Orchestrator 串行写入。
- 三题均按 14 阶段完成 Requirement Trace、问题依赖、Data Audit、baseline、主要候选、结构不同的
  对照/校验器、预注册实验、真实 execution、比较、稳健性、Final、Claim 和 handoff。失败、部分、
  STALE、不可行与未收敛结果原样保留。
- `all-cases-before-unlock` 是硬门：三个 freeze check、三个独立 freeze commit、三个 remote SHA、
  Skill tree 不变、search log 无未处理暴露、raw input hash 不变全部通过后，才允许统一有限解封。
- Skill 修改只接受至少两个 C case 独立重复的缺陷，或一个 universal hard failure；同题回归、Stress、
  参考方法差异和 problem-specific insight 不具有修改准入资格。
- C-target evidence accounting 分开记录 independent C first run、strict blind C first run、Development
  regression、Stress、A auxiliary transfer、Validation 和 Held-out。A 成功、同题回归或 Stress 均不得
  计入独立 C 泛化分母。
- Validation/Held-out/final simulation 必须为 C；Validation 是 frozen Skill、SEALED answer、fresh
  worker、one-shot，terminal freeze 后禁止新建 Run 或在同题调 Skill 后继续称为 Validation。

统一回归通过后，RC4 的 exact Skill tree、正式输入、rubric、answer state、环境和时间界限必须在
2024 C 任一模型结果前分别冻结并远端核验。Validation worker 不得读取 batch postmortem、RC4 修改
理由或其他题答案；terminal freeze 之后不得新增同题 Validation Run。

## 前置条件

- 唯一前置状态来源是仓库规范路径 `state/project_state.json`；其状态必须为
  `COMPETITION_SKILL_RC_READY`、`next_phase_allowed=PHASE-SKILL-DEVELOPMENT-EVAL-004`，正式 Skill
  必须为 `0.2.0-competition-rc1`/`COMPETITION_RC`，且 integration audit 必须是结构化 `PASS`。
- 启动前 `benchmarks/case_registry.yaml` 中 case ID 尚未存在；注册后必须保持
  `set_type=DEVELOPMENT`、`answer_access_status=SEALED` 到 first-run freeze 远端核验完成。
- 只登记题面来源和 hashes；在首跑冻结前不得读取答案、优秀论文、题解、代码、博客、视频或讨论。
- Validation/Held-out 的 Skill commit 必须在运行前冻结；其答案一旦可见，case 永久降为 Development。

## 首跑流程

1. 人工选择一道允许使用、答案未看过的历史 Development 题。首个正式 case 为
   `CUMCM-2023-C-DEVELOPMENT-001`；模型先验暴露不可验证，因此它只产生 Development 证据。
2. 输入只允许来自用户提供的合法原始文件或官方原始赛题入口。仓库 policy 禁止读取
   `benchmark-vault`，因此不得把该路径作为运行时输入。若必须在线取得，只能从不含题号、标题、
   附件名或答案词的官方历年赛题索引导航，所有查询/访问写入
   `research/pre_freeze_search_log.jsonl`。任何讲评、优秀论文、解析、代码、博客、视频或讨论在
   first-run freeze 前均禁止访问。
3. 在 ignored、非 vault 的私有 case workspace 中放置题面和 raw data，计算 SHA-256，不把题面、
   raw data 或答案写入 Git。`problem-source` 与每个 `data-hash` 名称必须是该 workspace 内的相对
   路径；launcher 会读取并逐文件核验。Tracked registry 只保留来源域、文件名、大小、media type、
   SHA-256、取得时间和转载许可未知项。
4. 运行：

   ```text
   .venv/bin/python scripts/start_skill_development_eval.py \
     --case-id <ID> --set-type DEVELOPMENT \
     --problem-source <RELATIVE-PROBLEM-PATH> --problem-hash <SHA256> \
     --data-hash <RELATIVE-DATA-PATH>=<SHA256> --skill-commit <GIT-SHA> \
     --model <MODEL> --reasoning <EFFORT> --case-kind <KIND> \
     --case-root <PRIVATE-WORKSPACE>
   ```

5. launcher 仅接受仓库中真实存在、且其正式 Skill tree 与当前工作区一致的 commit，并把
   problem/data/commit 写入 `state/development_eval_binding.json` 和 case evidence chain。开始建模前
   冻结 Skill tree、Git commit、模型/reasoning visibility、工具边界、12 小时时限、搜索政策与以下
   rubric：Requirement Coverage、Data Audit、Model Design、Execution、Validation、Evidence and
   Handoff、Contest Efficiency。主问题遗漏、声称未运行代码、test leakage、不可复现 Final Run、
   无证据 Claim、raw 覆盖、hash mismatch 和虚构来源是不可补偿硬门。
6. 随后用正式 Skill 的 14 阶段与集中 CLI 完整盲跑。所有搜索、人工 intervention、失败 Run 和
   evidence gap 都保留；不得因将看答案而重试。达到 6 小时时限仍应如实冻结当前状态。
7. 在任何答案解封前运行：

   ```text
   .venv/bin/python scripts/freeze_skill_first_run.py \
     --case-id <ID> --case-root <PRIVATE-WORKSPACE> \
     --freeze-output <TRACKED-FREEZE.json> --worktree-commit <GIT-SHA>
   ```

8. 冻结文件至少绑定 problem/data、RC1 Skill version/tree/commit、search/source、case state、代码树、
   所有 Run manifests/results、handoff/failure/timing 和 worktree commit。first run 无论 READY、STALE、
   REJECTED 或 blocked 都原样冻结，形成独立提交并在远端 SHA 核验后才允许 unlock。
9. 将冻结文件、registry 和状态作为独立提交推送；远端分支 SHA 必须等于该提交。核验后若确需诊断，
   才单独运行 `scripts/unlock_skill_first_run.py`，并传入 freeze commit、远端和分支以及
   `--unlock-time <ISO-8601>`。冻结命令本身没有解锁能力。解封后只允许更新
   generalizable failures 与 problem-specific findings，不改首跑证据。最多读取官方讲评、一份合法
   高质量获奖/官方展示材料和一篇正式出版方法分析；不复制代码、参数、公式或段落。
10. 运行 `.venv/bin/python scripts/check_skill_training_consistency.py --check`。

所有 start/freeze/unlock 时间必须携带 timezone，且严格满足
`start_time <= freeze_time <= unlock_time`。阻塞原因只接受机器 reason code 形式，禁止把任意解释、
路径或敏感输入写入结构化结果。launcher 不接受替代的 project-state 路径。

## 泛化与污染规则

- `generalizable_failures` 可进入 RC2 backlog；`problem_specific_findings` 只留在 Development case，不能直接固化为通用方法。
- Validation/Held-out 不接受 `UNLOCKED_AFTER_FIRST_RUN` 或 `PERMANENTLY_DEVELOPMENT`；答案可见即重新标为 Development。
- Run manifest 必须通过实际 input/code/output 文件、聚合 hashes、registry 中的 `skill_version`/`skill_commit` 与完整 case history 校验；freeze 会重验 workspace binding 与 manifest，而非接受浅层声明。模型、reasoning、搜索与干预记录不能后补。
- 首跑失败、STALE 或未 READY 都是真实结果；冻结脚本保留状态，不能把 “done” 改成 accepted。

## RC1 保证边界

当前只有 public deterministic Gates、两个项目原创 E2E 和完整回归保证。sealed Stage 1、Stage 2 effectiveness、消融、外部效度、生产适用性和 monetary cost 仍 deferred。
当前 Run code registry 固定为正式 Skill 内置 deterministic runner；任意 custom executor 的可信
动态 capture 尚未设计，因此不在 RC1 assurance 内，Phase 004 不得用其替换冻结执行入口。
若真实 case 因此不能产生可信 Run，必须保留失败并以结构化 reason code 冻结；该事实可以在 unlock
后作为通用缺陷候选，但不得在 RC1 first run 内修改 Skill 或伪造已执行结果。

## RC2 Development regression 与 Stress 规则

RC2 的 case-local executor 只接受 `RUNNING` 状态、预注册 candidate/seed、1–900 秒 timeout，且代码
文件必须与冻结 commit 的 Git blob 一致。`execute` 捕获时间、exit、stdout/stderr/output、输入、代码、
配置和 freeze；`seal-run` 在选择 decision hash 已确定后复验 capture，禁止调用者自行声明
`trusted_capture`。capture 或绑定文件变化必须拒绝或传播 `STALE`。

答案解封后的同题只允许 `DEVELOPMENT_REGRESSION`：research plan 必须绑定已验证的 first-run freeze
SHA，source ledger 必须记录 `UNLOCKED_AFTER_FIRST_RUN`。该路径以及由其派生的 Stress A/B/C 都不是
Blind、Validation、Held-out 或泛化证明。Validation/Held-out 仍必须保持答案 `SEALED`。

Phase 004A 的同题回归与三个 Stress 已分别保存 hash-only/aggregate evidence；raw workbook、题面和
参考正文仍在 ignored private cache。下一题必须结构不同且答案保持封存。

## RC3 非零退出证据规则

Phase 004B 的答案封存首跑暴露出一个通用执行证据缺陷：case-local 程序可以先写出结构化诊断
`output.json` 再以非零状态退出；RC2 保留了 output 和 exit code，却未必填充 `failure`，导致该失败
capture 不能被 `seal-run` 原样封存。RC3 对任意非零退出统一补充
`RC_EXECUTION_NONZERO_EXIT`（timeout 等更具体原因仍优先），保留已经写出的 output，并允许生成
outcome 为 `FAILED` 的 manifest。该 manifest 只能作为失败证据；comparison、Final、Claim 和 handoff
仍拒绝非 `SUCCESS` Run。此修订不改变成功路径、输入/代码/output hash 绑定或 STALE 传播。

Phase 004B 的 2020 A 同题回归、2023 C 跨题回归和三个机理 Stress 均属于 Development/Stress
证据，不是 Validation 或泛化证明。交给 Validation 的版本必须冻结到明确的 Skill commit/tree；新题
答案保持 `SEALED`，一次运行结果冻结后不得修改 Skill 并在同题重跑后继续称为 Validation。

## RC4 与 2024 C Validation 终局

RC4 的唯一修改是通用 selected-output preflight，并已通过统一回归。2024 C 在冻结 Skill、rubric、
输入、环境和答案状态后由 fresh worker 一次执行：2 个候选 × 2 个 seed 共 4 个实际 Run 全部成功，
六项主要求的数值输出、独立可行性复算和三项 perturbation 均存在。Final 后的 frozen Claim Gate
同时要求顶层 claim scope 等于整体 Final scope 和第一项 requirement-specific claim text；两者不等，
因此只返回 `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`。case 终止为 `REJECTED`，handoff 未达，
正式决策为 `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`。terminal freeze 后不得新增 Run；同题后续
永久只可作为 Development，修复必须在 `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2` 用新的冻结 C题
验证。
