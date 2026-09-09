# Round 06：已报告反例的闭合复核

在下列固定受测身份下，round05 的具体反例均已被拒绝；原始 mixed packet 未被这些修复误拒绝。本结论仅关闭这些已复现缺口，不是全部工程资格、科学结果或 Decision Auditor 的 PASS；没有评审未发生的 known、全 CI、最终 candidate 或正式 Audit。

## 身份与范围

开始 UTC `2026-09-09T09:59:13.263892+00:00`，HEAD `6646ffb98602ae6f94c332bb97ba45ede09bf6e2`。受测 adjudicator SHA-256：`346b49276c97237af1804d5af3aa2cd2208a08a0a6aff0e352bd076e26e67545`；protocol：`eede9891116280234ec3584659d0f38f351173c52c130ca946129eaa25896221`。

已独立确认迁移后 `evals/results/modular-workbench-001/development_exports/acceptance-001/mixed/records.json` 的 hash 仍为 `0ea4cf84bdb39d90392c92e52c3fd8808533dd8e9471f548898fb459a55ef4de`，与 round05 读取的原包一致。首尾身份与漂移记录为 `source_start.json` / `source_end.json`。

仅复用 round05 原创反例，路径适配与脚本来源 hash 见 `probe_copy_identity.json`。随后为两个同范围反例补足前置条件，避免把前置检查失败误写成目标分支闭合。所有写入在本 round06 内。

科学模型、科学 checker、Final、known 读取、pytest/全 CI、网络、Git mutation、公共/state 写入均为 0。family helper 只调用共享 core 的纯记录/数值校验函数；没有调用执行 checker 或 Final 的入口。独立复算脚本为满足其新 code binding 被定向读取、复制、导入，hash=`5fb7067d0ed03763873ebffd0b7b8fe967adf96a7157073b9aa7c54c09fe6cdb`；畸形 residual/packet 在 `recompute` 调用前拒绝，本轮该复算函数实际执行次数为 0。

## 已关闭的具体反例

| Round05 问题 | 本轮实际结果 |
| --- | --- |
| Q05-01：Final 缺 REQ-C 或 residual=1000000 | 均返回 `WB_FINAL_RECALCULATION_BINDING_INVALID`。 |
| Q05-01：manifest capture hash 错误、外围 hash 重绑 | 返回 `WB_MANIFEST_CAPTURE_BINDING_INVALID`。 |
| Q05-02：三条 requirement 但只有两 PRIMARY | 返回 `WB_MIXED_PRIMARY_COVERAGE_INCOMPLETE`。 |
| Q05-02：同一 wrong_case 参数替代其他攻击分支 | 原缺命令 fixture 被 `WB_COVERAGE_COMMAND_NOT_VERBOSE_PYTEST` 拒绝；补齐有效 verbose pytest 命令形状后仍被 `WB_FEEDBACK_ATTACK_BRANCH_COVERAGE_INCOMPLETE` 拒绝。日志全部为原创 parser input，没有实际执行其中列出的测试。 |
| Q05-03：独立复算非零命令、负绝对 residual、空 packet | 分别拒绝为 `WB_INDEPENDENT_RECALCULATION_COMMAND_FAILED`、`WB_INDEPENDENT_RECALCULATION_NOT_PASS`、`WB_PUBLIC_PROJECTION_UNDECLARED`。后两项已提供成功命令形状与正确独立代码绑定，触达各自检查。 |
| Q05-04：raw bool count 与 content int count 混同 | 独立 exact_records 及原包 Final ledger 变体均 `WB_RAW_RECORD_IDENTITY_INVALID`。 |
| Q05-05：1e309 溢出到 inf | strict_json 直接 `WB_NONFINITE_JSON_NUMBER:1e309`；重复 key 和显式 NaN 仍拒绝。 |
| Q05-06：Final 早于模型一天 | 返回 `WB_FINAL_PRECEDES_CAPTURE`。 |

原样保留的真实原创 mixed packet 在本轮 `validate_family_evidence` 返回 `[]`；普通 content/raw 不一致继续拒绝。没有创建完整 candidate，不能把这个 helper 的局部无错误当成工作台资格通过。

## 实际命令、时间和保存证据

第一条命令 `ls -la`；随后对上述新 adjudicator 和独立复算入口定向 `sed`/`rg` 静态读取。使用现有 `.venv/bin/python -B`；以下均为 2026-09-09 UTC，完整 argv 和首尾 hash 在各 JSON 记录。

| 命令 | UTC 起止 | 记录 |
| --- | --- | --- |
| `.venv/bin/python -B .cache/modular-workbench-001/protocol-review/round-06/family_probes.py` | 09:59:36.209426–09:59:36.300444 | `family-20260909T095936209426Z/results.json`，exit 0 |
| `.venv/bin/python -B .cache/modular-workbench-001/protocol-review/round-06/detail_probes.py` | 09:59:36.340937–09:59:36.348022 | `detail-20260909T095936340937Z/results.json`，exit 0 |
| 同一 detail probe，补齐同范围前置条件后 | 10:00:16.737933–10:00:16.754658 | `detail-20260909T100016737933Z/results.json`，exit 0 |

探针内部受测源无漂移。探针 exit 0 仅说明程序完整记录了预期拒绝行为。

最后分别调用实际资格 CLI 的 workspace、candidate、active 分支，原生命令、UTC、退出码、stdout/stderr、调用前后 hash 另存本目录 `cli-*.json`。当前无 candidate：workspace 为 `PASS_BUILD_NOT_QUALIFIED` / qualified:false / exit 0；candidate 与 active 为 `WB_CANDIDATE_EVIDENCE_REQUIRED` / BLOCK / exit 2。没有把旧判决、既有原包或本轮 reviewer 意见替代完整资格证据。

本轮不新增范围外问题；其余未评审分支、后续完整资格证据和正式接受仍由主 Agent 按已授权流程处理。

## 仍开放的旧 material finding

`WB-Q03-module-receipt-chain` / P1 / STATIC / OPEN：round04 已报告的 module receipt 内容核验缺口尚不能随 Q05 具体反例一起关闭。当前受测文件第 817–830 行仍只比较 module/execution/engineering/scientific/human_review/next_module_started 六个摘要，没有读取现存 Mxx-records 中的 request/completion/work_report，或与 family.case_state.evidence_bindings 交叉核对。需要把 case/request/scope/revision、request canonical、work report hash/身份以及正式 completion binding 接入资格硬门，并拒绝移植其他 case/request 的同摘要 receipt。

这条是已报告旧问题的静态残留，未执行完整 candidate 绕过；现存真实 M01–M14 packet 的独立字节/身份比较仍然一致。应区分“这些材料目前真实一致”与“验证器拒绝不一致替代品”。已经向主 Agent 明确报告本项仍开放。

当前 known 与 full CI 的正式结果尚未提交给本 reviewer，统一候选 decision 与独立 Decision Auditor 也尚未提交。本 reviewer 没有给这些步骤通过或投票。`actual_tool_record.json` 索引本轮真实调用、当前 read_files hash、历轮报告和旧/新版本区别，保留上述 OPEN 项。
