# Phase 004 Development Eval Protocol

## 目的

直接用 `cumcm-modeling-evidence` Competition RC1 对一道答案仍封存的历史 Development 题做完整盲跑，以真实失败形成 RC2。这里不重新设计 Benchmark，也不以历史答案训练 Validation/Held-out。

## 前置条件

- 唯一前置状态来源是仓库规范路径 `state/project_state.json`；其状态必须为
  `COMPETITION_SKILL_RC_READY`、`next_phase_allowed=PHASE-SKILL-DEVELOPMENT-EVAL-004`，正式 Skill
  必须为 `0.2.0-competition-rc1`/`COMPETITION_RC`，且 integration audit 必须是结构化 `PASS`。
- `benchmarks/case_registry.yaml` 中 case ID 尚未存在，`set_type=DEVELOPMENT`，`answer_access_status=SEALED`。
- 只登记题面来源和 hashes；在首跑冻结前不得读取答案、优秀论文、题解、代码、博客、视频或讨论。
- Validation/Held-out 的 Skill commit 必须在运行前冻结；其答案一旦可见，case 永久降为 Development。

## 首跑流程

1. 人工选择一道允许使用、答案未看过的历史 Development 题；本仓库任务不预选题目。
2. 在私有 case workspace 中放置题面和 raw data，计算 SHA-256，不把私有题面/答案写入 Git。`problem-source` 与每个 `data-hash` 名称必须是该 workspace 内的相对路径；launcher 会读取并逐文件核验。
3. 运行：

   ```text
   .venv/bin/python scripts/start_skill_development_eval.py \
     --case-id <ID> --set-type DEVELOPMENT \
     --problem-source <RELATIVE-PROBLEM-PATH> --problem-hash <SHA256> \
     --data-hash <RELATIVE-DATA-PATH>=<SHA256> --skill-commit <GIT-SHA> \
     --model <MODEL> --reasoning <EFFORT> --case-kind <KIND> \
     --case-root <PRIVATE-WORKSPACE>
   ```

4. launcher 仅接受仓库中真实存在、且其正式 Skill tree 与当前工作区一致的 commit，并把 problem/data/commit 写入 `state/development_eval_binding.json` 和 case evidence chain。随后用正式 Skill 的 14 阶段与集中 CLI 完整盲跑。所有搜索、人工 intervention、失败 Run 和 evidence gap 都保留；不得因将看答案而重试。
5. 在任何答案解封前运行：

   ```text
   .venv/bin/python scripts/freeze_skill_first_run.py \
     --case-id <ID> --case-root <PRIVATE-WORKSPACE>
   ```

6. 核验冻结 hash 后，若确需诊断才用 `--unlock-time <ISO-8601>` 记录答案解封；解封后只允许更新 generalizable failures 与 problem-specific findings，不改首跑证据。
7. 运行 `.venv/bin/python scripts/check_skill_training_consistency.py --check`。

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
