# 目录与导航修正的独立有界差异审核

结论：**本次定向修正有证据支持；仍待另行提供独立 11 测试与第二次完整 CI 的实际结果。** 固定比较 `6b505c44b1d160372b9c6ca696bce4fa838043b1` → `bb29f03fb8eb4edc5513b1b9e8515089feb51b13` 的 11 项静态/字节核验全部通过。没有发现修改 guard、放宽冻结范围、删减测试逻辑或改写旧资格结果的差异。此报告不是 CI PASS、guard 执行结果或 formal acceptance。

首个 shell 为 auditor scratch 下 `ls -la`，扫描仅见本轮既有审核、finding、代码和结果。实际读取限于授权的固定 Git 差异、具体导航/测试/manifest/WORK_LOG/首次 CI 记录、guard 静态定义及既有 auditor scratch；全部写入仅当前 scratch。自写 `scope_correction_audit.py` 只运行 Python 标准库与只读 Git 命令，没有导入项目程序，没有运行 pytest、guard、case CLI、模型、checker、Final 或 CI，没有网络访问或安装依赖。一次运行退出码 0；完整代码、stdout、diff、逐件 blob hash 和 Git 读命令在同目录留存。

## 修正范围

固定 diff 共 8 项变动，测试迁移按 rename 计数；按无 rename 的路径集合计为 9 路径。除了 README、docs/INDEX、独立入口、测试迁移和 operator manifest，其余只新增首次失败日志/receipt并追加 WORK_LOG。没有其他路径变更。

- README.md 和 docs/INDEX.md 都只移除本轮增加的同一条 operator 导航及空行。程序用确切字符串删除前后字节比较，没有其他导航/正文更改。此结论限于本次两个提交；与更早 d1 起点的全量字节关系由主编排器另核。
- 新 `OPERATOR_START_HERE.md` 明确指向独立操作资料，并给出单独测试命令 `.venv/bin/python -m pytest -q docs/gpt_codex_workflow/tests`。第 5 行明确原完整 CI 与资料测试分开，不能自动相加测试数。
- 原 `tests/unit/test_operator_kit_packages.py` 迁至 `docs/gpt_codex_workflow/tests/test_operator_kit_packages.py`。AST 全模块比较仅归一化 kit fixture 的第一条 `path` 定位表达式后完全一致；所有测试函数、helper、assert、参数化值和异常预期保留。旧定位从 repo/tests/unit 上溯到 repo，再接 docs/...；新定位从 docs/gpt_codex_workflow/tests 上溯到 kit，再接 tools/...，均指同一 package builder。
- 5 个测试函数保留 11 个参数化 case：NO_CASE 权限 1、缺失/篡改/额外载荷 3、example/next 内层身份 1、source symlink 1、不安全路径 5。本轮仅作静态计数和等价核验，没有进行收集或执行。迁移后的 11 项不得算作已经由默认 CI 运行；实际独立命令的结果仍需另记。

## guard 与覆盖边界

`scripts/check_modular_workbench.py` 在两个固定提交间整文件字节完全相同，SHA256 `5368a7318d41c96ae6583d2ad9e372fa8c3481df3ee43c4894996a3e59366f8c`。因此 digest/canonical、PREFIXES/EXACT、KNOWN_RUNTIME_PREFIXES/EXACT、mapping/frozen_mapping/known_runtime_mapping、evaluate 的实现均未改。本轮没有调用这些函数。

静态依据：PREFIXES 第 83–92 行包含 `tests/`、`scripts/`、核心 Skill 等；EXACT 第 93–111 行包含 README.md、docs/INDEX.md 等。frozen_mapping 第 191–198 行按上述谓词选入路径；known_runtime_mapping 第 201–211 行在前一映射内再作限定。evaluate 第 886–900 行仍核 expected 文件 hash、HEAD 路径集合和未跟踪冻结路径，没有新增豁免。

依原谓词独立分类，旧测试路径在 qualification mapping 内；新 `docs/gpt_codex_workflow/tests/...` 与根 `OPERATOR_START_HERE.md` 均不在 qualification/known-runtime 两个集合内。本次 diff 触及 qualification 集合的仅 README、docs/INDEX 和旧新增测试路径，触及 known-runtime 的仅两个导航文件。旧 qualification 目录、历史决定/receipt、state 和核心/scripts/rules/contracts/src 均没有本次差异。由此可确认是撤回先前附加到冻结面的内容，而没有改 guard 或放宽其覆盖范围。

这也意味着旧 guard 的通过不能证明新资料及其测试已被覆盖；operator kit 需保留独立核验。operator manifest 仅追加迁移后的测试 hash，重新计算资料 content hash，并将 verification_status 改为 `REHEARSAL_AUDIT_VERIFIED_CI1_GUARD_BLOCKED_SCOPE_CORRECTION_PENDING_CI2`；其余原资料 file hash、核心 identity 与资格范围未改。新增测试 hash 与实际新 Git blob 一致。

## 首次完整 CI 的真实终局

`commands/full-ci-attempt1.log:37` 记录 pytest **2380 passed / 1 skipped**。第 50 行 guard 终局为 BLOCK，包含 README/docs INDEX implementation drift、path set drift、decision replay mismatch 与 known executed runtime drift。对应 receipt 的 subject 为 6b505c44…、整体 exit_code=2；日志 SHA256 与 receipt view_sha256 一致，均为 `a016fa6e111ad98b192c74bac3d5851455c51b905c20c3b974d1ad66511569cc`。WORK_LOG 明确保留该失败并禁止将其汇报为完整 CI 通过。

原始测试阶段成功不能覆盖后续拒绝。本次只核这些已保存的证据，未重新执行首次 CI，亦未检查主编排器正在进行的 CI2。原始 RAW_FINDINGS、主报告、F001 closure 和教学包审核结果 hash 均保持不变。

## 限制与后续证据

本审只证明两个固定提交之间的改动、AST 等价和原 guard 静态范围，未自行计算 bb29f03 与历史 d1 的全量 qualification/known-runtime map 相等，也未独立运行原 guard。因此主编排器的 d1 全量映射比较、独立 11 测试和 CI2 结果不能由本报告替代。后续提交、重新打包及 CI 元数据未包含在此固定 diff；必须按实际输出另记。没有重做数学、改旧资格或重启原创 Run/Final。
