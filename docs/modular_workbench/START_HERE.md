# 从这里开始

这是一个由 Codex 实际执行建模工作的模块工作台。你负责指定问题、模块、范围与研究方向，
Codex 在本地完成分析、代码和核验，网页大脑根据你实际上传的证据协调与审查。脚本不会替代研究。

1. 使用完整工具仓库及既有 `.venv`。实际 case 放到工具仓库外的独立目录。
2. 读 [模块目录](MODULES.md)，向 Codex 发送 [CODEX_MODULE_REQUEST](ROLE_PROMPTS.md) 中的请求。
3. Codex 读取正式 Skill、当前任务卡与有效本地状态，prepare 后实际工作，complete 后停止。
4. 审查包仅在本地生成。按当前竞赛规则决定是否上传 `REVIEW.md`、`manifest.json` 和 `views/`，
   可选择 CLI 的 ZIP。网页无法通过本地路径读取文件；没有上传就不能声称已读。
5. 网页反馈通过 [反馈格式](REVIEW_FORMAT.md) 交回 Codex。先登记 finding，再复算或论证；
   不以网页意见、多数票或人工许可覆盖技术拒绝。下一模块必须再次明确调用。

[实用命令与恢复](RUNBOOK.md) · [七类角色提示词](ROLE_PROMPTS.md) ·
[稳定项目说明](PROJECT_BRIEF.md) · [本轮建设证据](../../evals/results/modular-workbench-001/checkpoint.md)

动态上下文由 `context-export` 从当前case正式记录派生，不能手改成新的状态真源。
新大脑负责当前协调；旧对话保留历史咨询。同项目记忆不等于严格盲审或版本同步。

结果分开读：执行是否完成、工程合同是否通过、科学证据支持到何种范围、队员是否实际核验。
真实网页和队员核验尚未发生时均为 `NOT_RUN`。本轮提供技术底稿；通俗比赛手册等待实际回执后定稿。
