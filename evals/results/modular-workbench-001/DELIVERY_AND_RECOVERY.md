# 交付与恢复

当前工程结论：MODULAR_WORKBENCH_ENGINEERING_ACCEPTED。证据/接受提交`4352efe054d0097d39572bb8d4b06247a015b049`已用指定远端refs/heads/feat/phase004c5-p0-01-finalization-hf22-repro核对到同一SHA，回执为delivery/evidence_delivery.json。其后收口文档提交的SHA由最终对话及远端branch HEAD核验提供；不把文件中无法自引用的未来提交写成已核验事实。

仓库https://github.com/woobowen/cumcm，PR https://github.com/woobowen/cumcm/pull/12，保持OPEN/DRAFT。只执行普通commit/push；未ready、merge、main push或force-push。源与证据受测subject为d1f8532d498307e3b4755c088ce6a0fadfb432bb，其后提交保持完整实现映射不变。完整CI与361项定向测试的真实命令/时间/退出码见commands/，GitHub托管CI在最终对话和PR checks中按实际closing HEAD与PR merge checkout单独核验；不把尚未完成的运行写成PASS，也不替代本地受测身份。

## 恢复边界

1. 正常使用只从START_HERE进入，并发送单个case/module/requirement请求。默认GUIDED_SINGLE_MODULE；本轮BUILD_AND_ACCEPT授权不传入未来提示词。
2. 保留完整工具Git历史以验证历史证据。case放仓库外，通过已有CLI status/resume查正式事实；不修改project_state或completion来绕过拒绝。
3. 当前模块已完成可幂等重新导出审查包；状态/实现/输入变化时，先验证上下文和依赖。旧上下文是历史快照，不是当前事实。使用context-export生成新包，实际上传后网页才可读取。
4. 失败与STARTED操作保留；不删除执行账本，不把中断当未启动。Final真实消费后不能重跑或退款。允许的新revision只在明确授权的新root开始，不能让旧case切模式逃避历史。
5. 2016Q3本次两个revision均封存，禁止再启动模型/checker/Final。原始xlsx/docx仅本地保留；公开记录仅用于工程与结果复核，完全重算须合法原附件及新的明确授权。
6. 技术质疑以新challenge追加，包含case/module/revision/package和可复算证据；机器拒绝不能由网页、人工或多数票覆盖。人负责TEAM_COMPLIANCE_REVIEW与实际使用反馈。

## 可复查命令

在已交付工具仓库、既有.venv中执行以下只读检查。它们不启动已知题模型或Final：

```bash
.venv/bin/python scripts/check_modular_workbench.py --stage active
.venv/bin/python scripts/validate_repo.py --strict
.venv/bin/python scripts/render_status.py --check
git diff --check
git rev-parse HEAD
git ls-remote origin refs/heads/feat/phase004c5-p0-01-finalization-hf22-repro
```

原创数值记录可用scripts/recalculate_workbench_originals.py独立复算。原完整建设驱动需显式--build-exercise、一个全新外部目录和一次新的建设/演练授权；不要把复现命令自动加入未来逐模块请求。

## 保存与环境

- 工具与审查材料：本PR已推送提交中的START_HERE、模块卡、角色提示词、矩阵、九类回执、原生审查、机器决定与Auditor证据。
- 原始已知输入、case工作区、日志原件、缓存、虚拟环境和未发布旧subject对象留本地。公开的脱敏view与raw hash分离，见各view_manifest；不推送私有ref。
- 14张审查包含本次原创素材，不含整个仓库；ZIP由公共CLI实际生成，不接受来自网页的ZIP执行入口。
- 实测WSL2/Linux/Python3.11.14；Windows原生NOT_RUN。本轮本地新增系统包、语言包、工具链、全局配置均0，无安装清理事项。已有.venv及用户的Zone.Identifier文件不删除。
- 若远端网络/权限失败，保留全部本地提交与准确PUSH_BLOCKED状态，普通push恢复；不得force、回退已发布历史或写REMOTE_DELIVERED掩盖失败。

完成本轮后，等待用户明确模块请求或实际审核回执。网页据事实整理通俗操作手册，Codex不自动再研发、解题或推进下一模块。真实网页和三位队员本人验收、比赛合规仍NOT_RUN。
