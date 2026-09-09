# PR #12 RC8 原生只读复核 03

**冻结结论：本次确认的 B03 在 `1b508aa` 的实际 repository evaluator 反例复验中已关闭；在本轮明确审查的实现范围内没有仍开放的 release BLOCKER。完整 CI/候选所有必需回执的最终通过尚不由本审查确认，因此不能据此接受候选或激活 RC8。科学未完成项按原范围保留。**

角色：`adversarial_evidence_auditor`；原生子任务 `/root/rc8_fact_binding_audit`。本轮最多25分钟，公共 Git/state 只读，没有再 spawn。自有输出仅在 `.cache/pr12-rc8/native-audit-03/`；允许 core 在 `.cache/scientific-check-replays/` 写它的唯一派生复算目录，实际目录另列证据索引。没有执行官方完整模型、安装依赖或访问新题/答案/vault。

初始受测 subject：`d9a43b8d6d0d1fdc57e639080a26b3a88054ac31`。首先执行 `ls -la`，确认既有 `.venv`；阅读当前规则/计划/state/正式 Skill。31 个初始输入文件均与该 commit 的 Git blob 字节相同，快照和 SHA256 见 `input_manifest.json`、`inputs/`。当前 active Skill 为 RC7，RC8 为 staged candidate。相对已审703775b的增量集中于 evaluation_design freeze、Development budget/单候选分支、版本/历史subject解析与候选准入。

## B03 — BLOCKER：非有限测试计数绕过 RC8 候选最低测试数量门槛

位置：d9a43b8 `scripts/check_phase004c4_rc7_release.py:468`–`:477`，以及 `_read_json:45`。`json.loads` 默认接受 NaN/Infinity，计数检查只用 `< minimum`；NaN 不满足“小于”，Infinity 大于任意门槛，因此非法计数会被当作数量足够。

独立复现调用真实 `evaluate_rc8_repository(stage="candidate")`，用 ignored facade 保存合成 candidate/receipts，以真实 d9 Git subject 建立完整 implementation mapping，所有被测公共文件只建立只读使用的 symlink，没有 Git 写入。该 facade 中的 receipt 是明确标注的反例输入，绝不是本项目实际 CI 或真实审查证据。

| 合成 receipt 输入 | 实际 repository evaluator |
|---|---|
| focused=80、full=2000 | PASS（控制组） |
| full=0 | BLOCK，`RC8_CANDIDATE_FULL_TESTS_INSUFFICIENT` |
| full=NaN | **PASS，错误接受** |
| focused=Infinity | **PASS，错误接受** |
| strict receipt 绑定703775b而candidate绑定d9 | BLOCK，`RC8_CANDIDATE_RECEIPT_FAILED:strict` |

证据：`release_receipt_observations.json`，逐组原始输入 `release_receipt_inputs/`，脚本 `run_release_receipt_probes.py`，实际执行 `release_receipt_probes.command.json`、`.stdout`、`.stderr`（外层exit0表示探针脚本成功执行，不表示候选合格）。建议 JSON读取拒绝非有限数字；计数使用严格非负 integer，达到冻结阈值；exit_code/final_test_access_count 排除 Boolean 等别名。保留错误原始输入及正常数量/错误subject控制组。

## 已验证的增量边界

| 范围 | 实际观察 | 证据 |
|---|---|---|
| 非预测 Final 合法路径 | Git-bound toy producer +真实 checker，actual controller exit0、READY_FOR_PAPER_HANDOFF、scientific verification=1、test access=0 | `runtime_probes/control_nonpredictive/` |
| 完整科学回执伪造 | 前置不运行checker，伪造完整v2 ledger+irrelevant identity残差；controller实际复算后exit1/语义BLOCK | `runtime_probes/forged_complete_scientific_receipt/` |
| Development test=[] 可用 | 真实捕获2个toy Run，train=[1]、validation=[2]、test=[]，trusted freezes校验有效 | `runtime_probes_development_r2/development_legal_and_final_block/original_plan.json` |
| Development不可转Final | actual evaluate-final exit3，`RC_FINAL_TEST_NOT_AUTHORIZED_BY_EVALUATION_DESIGN`；没有Final ledger | 同目录 `evaluate_final_development.*` |
| 后改design不可转Final | 改为FINAL_EVALUATION并补test=[3]后actual CLI仍exit3，`RC_TRUSTED_FREEZE_REGISTRY_INVALID`；没有Final ledger | 同目录 `evaluate_final_changed_design.*` |
| design整个对象冻结 | 保留合法Development mode/test=[]，只添加一个新metadata字段；实际execute在生成新capture前exit3，`RC_TRUSTED_FREEZE_REGISTRY_INVALID` | 同目录 `execute_changed_design_extra_field.*`、`design_extra_field_observation.json` |
| RC7历史subject | 实际原candidate/live CLI均PASS；函数级注入原core Git blob hash不符得到BLOCK | `admission_observations.json`、`admission_probes/` |
| staged RC8与active RC7分离 | 版本CLI PASS但明确scope=CANDIDATE_STAGED_NOT_ACCEPTED，state_skill_version=RC7；RC8 snapshot缺失时candidate CLI BLOCK | 同上 |
| 未知版本 | 对实际main的VERSION读取显式注入rc999，exit1/BLOCK；未改仓库VERSION | 同上 |
| 9次capture硬预算 | 实际run_case前置guard，8已有+1计划允许到prepare前stop；8+3和9+1在prepare前拒绝 | `budget_probes/`、`admission_observations.json` |

预算探针把 `prepare_case` 替换为明确的 stop sentinel，只测准入条件，不读取官方输入、不执行模型。它覆盖正常单主编排器串行路径；不是多个并发 CLI 的原子预算锁测试。单候选分支在缺少baseline或不足两个成功candidate时先seal所有已执行Run，随后写PARTIAL，不进入ranking（route:1047–1077）。

科学伪造复验的 runtime/controller 代码沿用已审703775b机制，实际正负结果说明本次 evaluation/version 增量未破坏该路径；不宣称所有科学问题因此得到解答。

首次 Development 观测脚本把 `row.splits` 指向随后被攻击性修改的同一个plan字典，导致第一次stdout最终打印test=[3]。该字段不用于证明原始合法split。已保留原日志，并以独立新case的 r2 深拷贝、original_plan及实际CLI证据确认 test=[] 合法；没有将探针观测装配问题计作生产漏洞。

## 当前候选科学结果与未完成项

本轮只读比对已生成回执，没有重新运行2021/2022官方模型或checker。每个读取文件的SHA256及观察在 `candidate_science_observations.json`。

- 2021：d9 subject只有一个新baseline Run，Run与checker均SUCCESS，selected_candidate_id=null、validation_scores={}、PARTIAL_SCIENTIFIC_EVIDENCE、whole/scientific quality均false。它是非排名实算，不能称为当前subject下三候选比较或新改进证明。旧subject的科学结果保持原有边界。小的呈现改进：无semantic时17个requirement的incomplete列表也为空，宜显式标为全体未评/UNKNOWN；现有whole=false没有造成整体成功误宣称，故不作为release BLOCKER。
- 2022：d9 subject三候选及三个checker均SUCCESS；所选HELLINGER_KNN_COMPLETE只支持11/13，REQ-3A与REQ-EVIDENCE明确不足；科学整体false、Final访问0。三个checker的scientific_metric_binding_mismatch_count均0。这些是当前有限Development集合的结果。
- 原已审科学限制继续成立：未独立重拟合分类器/聚类，未知分数未校准、未知标签不可用，风化因果效应未识别；2021原生A/B模板与Q4独立最优证书等缺口保留。正确保留负面/不完整结果不自动否决通用软件修复，CI通过也不能消除这些科学缺口。

## CI、范围和审查状态

主编排器报告d9全CI为3 failed、2136 passed、1 skipped；本轮未重复执行全CI，也不把此报告当作我亲自执行的日志。已知失败仍需修复并重新验证，不能称d9满足完整候选准入。

截至原subject，B03是已复现的release BLOCKER；不做候选接受决定。后续修复的具体subject与针对性复验必须在附录中单独列明；未实际读取/执行的改动不包含在本审查结论内。最终证据索引为 `evidence_index.json`，含角色、输入字节、命令、stdout/stderr/exit和独立checker replay目录。

## `1b508aa` 修复增量与独立复验（本轮最后 subject）

最后受测 subject：`1b508aabd3948ff0977ac5e77b451fd72b82cc00`。读取的当前字节与该 subject 的 Git blob 全部一致，见 `input_manifest_r2.json` 和 `inputs_r2/`。额外核对 core、controller、Development route、两题各自 producer/checker 共7个实现路径，确认与d9字节完全相同；因此前面实际 runtime 探针与d9科学Run仍保留其原 subject，而不是重标为在1b执行。

本增量仅5个文件：

- Release checker 对 NaN/Infinity 字面量返回无效输入，对测试计数要求 `type(value) is int` 且达标，对exit_code与Final access count拒绝Boolean；`1e999` 即使由Python解码为inf，也不能通过整数计数门槛。
- Training consistency只增加明确的RC8版本及staged条件，不把任意未知版本当合法，也没有把staged状态改成accepted。
- Freeze测试改为直接检验trusted_freezes的完整对象绑定；原Development不准Final的测试保留。本审查还以实际execute验证新增design元字段触发BLOCK，并确认没有新capture。版本测试改为预期RC8；新增计数类型反例。

复验使用原相同 repository evaluator/facade机制，另建r2目录，不覆盖d9原始攻击输入。9组结果：正常80/2000整数控制组PASS；0、NaN、Infinity、错误subject、Boolean exit_code、Boolean Final count、2000.0和原始JSON数字1e999 **全部BLOCK**。因此B03针对性修复已验证。

证据入口：`release_receipt_observations_r2.json`；每组原始receipt/candidate字节在 `release_receipt_inputs_r2/`；实际命令、stdout/stderr、退出码在 `release_receipt_probes_r2.command.json`、`.stdout`、`.stderr`。外层exit0仍只是反例脚本成功，不是当前真实候选qualified。这些合成receipt的有效控制组也不能充当真实CI、native audit或Development验收证据。

本次原生checker replay共3个唯一目录，准确路径与每文件hash见 `native_replay_index.json`：`RUN-CAND-20260906-s93a9jrd`为合法控制PASS；`RUN-CAND-20260906-uan9dbym`和`RUN-CAND-20260906-lux_5g87`为完整错误结果的实际复算不一致。后两项checker执行成功但结果比较失败，未把原回执当独立证明。

主编排器在1b重跑完整CI及focused，最终结果在本报告冻结时未由我读取验证。上文d9的CI失败是其历史结果，不能用1b针对性通过改写。最终候选接受还必须由主编排器依据冻结协议、真实同subject验证回执及全部必要门槛决定。本报告不覆盖1b之后的新实现改动。

为避免主编排器后续改动影响反例复核，两个facade原先用于只读复用公共文件的symlink已转为各自受测subject的固定字节副本；变化文件只用只读 `git show` 恢复，未写Git或公共文件。每个facade固定774个文件，记录于 `facade_materialization.json`。原始攻击receipt、候选完整mapping、d9/1b两套checker源字节和执行stdout/stderr均独立保留；不能拿新版checker的拒绝结果覆盖旧版错误接受证据。
