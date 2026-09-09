# Round 07：既有 module receipt chain 的定向复核

仅审查 `WB-Q03-module-receipt-chain`；其已报告的具体缺口及本轮 revision 类型残留已闭合，没有扩展其他资格边界。本轮不提供整体工程/科学/Audit PASS，不读取 known 或运行模型、科学 checker、Final、全 CI；这些实际计数均为 0。全部负例来自明确允许读取的真实原创 mixed module 记录的私有副本，公共文件/state/Git 写入为 0。

## 第一次受测版本与观察

开始 UTC `2026-09-09T10:05:42.978925+00:00`，HEAD `6646ffb98602ae6f94c332bb97ba45ede09bf6e2`。adjudicator SHA-256=`f8f347c22603e4475101c7748551f10fba33d37124e15fe0c742f624d35ab665`，workbench=`90b913ee417c1ec2352e8e2381e6675aeab5a86401bf09e1a366a7da241a8147`。源快照和真实 packet hash 保存在 `source_start.json`，29 个既有原创文件的读取身份在 probe 日志。

实际命令：`.venv/bin/python -B .cache/modular-workbench-001/protocol-review/round-07/module_probes.py`，UTC `10:07:18.987546–10:07:19.347121`，exit 0；记录 `module-20260909T100718987546Z/results.json`，调用前后无源漂移。

新 `validate_module_evidence` 确已接入 evaluate，使用 exact_records、当前 WB identity，以及 family.case_state 的 request/completion 原始字节 hash。本轮真实 M01–M14 包都返回 `[]`；以下私有负例都被 `WB_MODULE_FORMAL_BINDING_INVALID` 拒绝：

- 保留相同六个摘要字段但替换 receipt.case_id / request_id。
- 用只有六个相同摘要字段的 JSON 替代完整 receipt。
- 改 report case_id / request_id / requirement_scope / revision=2，并重绑 report→completion→case_state 链。
- 缺 case_state 对 request 或 completion 的 binding。
- request 使用旧 implementation hash，外围 raw/hash/state binding 保持一致。
- completion 时间早于 request。

首次还存在同项反例：request.revision=1、report.revision=true，重算 report raw/hash、completion.artifact_hashes、completion raw/receipt、family.state completion binding 后，仍返回 `[]`。函数只对 request revision 检查严格 int，report/request 采用 Python `!=`，因此 true 与 1 相等。该反例已向主 Agent 发出；不是完整 candidate 绕过执行。

## 残留补测与闭合

主 Agent 为 report.revision 增加严格 int 检查后，实际执行：`.venv/bin/python -B .cache/modular-workbench-001/protocol-review/round-07/revision_recheck.py`，UTC `2026-09-09T10:10:12.849293–10:10:12.890798`，exit 0。受测 adjudicator SHA-256=`0d19d2f53425eed65b4da7abd2e9b6546b9b829df6727035aa51e0b82a88af31`，调用前后无漂移；观察 HEAD=`eec8b5ffa5d3a8271d2bdba40278f897c0325c72`。

复用了第一次实测留下的原始私有 fixture 字节：原样 M04 对照仍返回 `[]`；report.revision=true 变体返回 `WB_MODULE_FORMAL_BINDING_INVALID`。日志为 `revision-recheck-20260909T101012849293Z.json`，包含六个 fixture 文件的实际 hash。

最后用 AST 定位同一 helper 比较初始与补测代码，实际差异仅新增 `or type(report.get("revision")) is not int`；差异和当前 read_files hash 保存在 `source_end.json`。首次已验证的其余拒绝条件保留。当前版只补测残留和 M04 对照，没有冒称在新 hash 重跑全部 14 个模块或科学流程。

本轮目标旧项 `WB-Q03-module-receipt-chain` 标为 CLOSED（限定上述代码、既有记录及实测反例）；该授权范围内没有剩余 material finding。此前 round06 的 OPEN 记录保留原样，由本轮新证据向前关闭，不改写历史审核结果。完整资格、其他未审分支和新统一 subject 的正式接受仍不在本结论中。

主 Agent 另说明其未发布提交及 context 隐私材料发生调整。本 reviewer 只独立观察到上述 HEAD / 文件 hash 改变；没有读取 context 或 known 内容，没有联网验证远端或检查 private ref，也没有执行任何 Git mutation。早先 6646ffb 下原包及探针 subject/hash 全部保留原样。

第一条命令是 `ls -la`；随后以 `rg` / `sed` 静态读取新 helper、调用点及 module_identity，使用 `.venv/bin/python -B -` 记录源 hash / UTC / 只读 HEAD。所有确切工具调用保留在真实调用记录中。

## 边界

helper 返回 `[]` 只是这些实际记录在该函数下无错误，不表示候选已建立资格。没有读取或核验 known R1 的真实运行记录，也没有将主 Agent 对 known 的摘要报告转写为本 reviewer 的验证结果。没有验证当前全 CI 或独立 Decision Auditor。
