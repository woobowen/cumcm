# Phase 004 Development Eval Protocol

## 目的

直接用 `cumcm-modeling-evidence` Competition RC1 对一道答案仍封存的历史 Development 题做完整盲跑，以真实失败形成 RC2。这里不重新设计 Benchmark，也不以历史答案训练 Validation/Held-out。

## 前置条件

- 项目全局 state 为 `COMPETITION_SKILL_RC_READY`，Skill 为 `0.2.0-competition-rc1`/`COMPETITION_RC`。
- `benchmarks/case_registry.yaml` 中 case ID 尚未存在，`set_type=DEVELOPMENT`，`answer_access_status=SEALED`。
- 只登记题面来源和 hashes；在首跑冻结前不得读取答案、优秀论文、题解、代码、博客、视频或讨论。
- Validation/Held-out 的 Skill commit 必须在运行前冻结；其答案一旦可见，case 永久降为 Development。

## 首跑流程

1. 人工选择一道允许使用、答案未看过的历史 Development 题；本仓库任务不预选题目。
2. 计算题面与数据 SHA-256，不把私有题面/答案写入 Git。
3. 运行：

   ```text
   .venv/bin/python scripts/start_skill_development_eval.py \
     --case-id <ID> --set-type DEVELOPMENT \
     --problem-source <OPAQUE-REGISTERED-SOURCE> --problem-hash <SHA256> \
     --data-hash <RELATIVE-NAME>=<SHA256> --skill-commit <GIT-SHA> \
     --model <MODEL> --reasoning <EFFORT> --case-root <PRIVATE-WORKSPACE>
   ```

4. 用正式 Skill 的 14 阶段与集中 CLI 完整盲跑。所有搜索、人工 intervention、失败 Run 和 evidence gap 都保留；不得因将看答案而重试。
5. 在任何答案解封前运行：

   ```text
   .venv/bin/python scripts/freeze_skill_first_run.py \
     --case-id <ID> --case-root <PRIVATE-WORKSPACE>
   ```

6. 核验冻结 hash 后，若确需诊断才用 `--unlock-time <ISO-8601>` 记录答案解封；解封后只允许更新 generalizable failures 与 problem-specific findings，不改首跑证据。
7. 运行 `.venv/bin/python scripts/check_skill_training_consistency.py --check`。

## 泛化与污染规则

- `generalizable_failures` 可进入 RC2 backlog；`problem_specific_findings` 只留在 Development case，不能直接固化为通用方法。
- Validation/Held-out 不接受 `UNLOCKED_AFTER_FIRST_RUN` 或 `PERMANENTLY_DEVELOPMENT`；答案可见即重新标为 Development。
- Run manifest 必须绑定 registry 中的 `skill_version` 和 `skill_commit`。模型、reasoning、搜索与干预记录不能后补。
- 首跑失败、STALE 或未 READY 都是真实结果；冻结脚本保留状态，不能把 “done” 改成 accepted。

## RC1 保证边界

当前只有 public deterministic Gates、两个项目原创 E2E 和完整回归保证。sealed Stage 1、Stage 2 effectiveness、消融、外部效度、生产适用性和 monetary cost 仍 deferred。
