# Round 09 — 中断 full CI 的 11 项失败诊断

本轮为只读源码/日志诊断，不是工作台验收。以 `929d2874e711ca4dd58484555009b028555898a3` 和保存的 `full-ci-001.log.read-snapshot` 为诊断对象。日志实际末行是 **11 failed, 1584 passed in 480.42s**，随后/伴随 KeyboardInterrupt；不能记为 full CI PASS。本审核者没有重跑任何测试、模型、科学 checker、Final 或 known case。

日志于 2026-09-09T10:40:02.376386+00:00 保存，50,643 bytes，SHA256 `1fe4fdbd799f56f51a192dc16e905ba011f6f973c0c6eff71d4feabb047b5672`。2026-09-09T10:43:52.958900+00:00 独立读取的 20 个源码/状态/版本文件均与 HEAD Git blob 一致，身份见 `source_observation.json`，原字节保存在 `source-snapshot/`。随后主Agent已修改相关测试/helper；结束时漂移见 `source_end.json`，不能把新源码称为原失败所执行版本。

## 逐项结论

表中位置指上述快照。分类是诊断，不表示修复已验证。优先级均为 P1：这些失败阻断当前 CI，但没有一项提供科学 runtime 门禁放宽的理由。

| # | 实际失败 node | 代码证据与分类 | 最小修正建议/请求验证 |
|---|---|---|---|
| 1 | `tests/fault_injection/test_eval_policy_faults.py::test_human_gate_and_integration_flags_remain_false` | 142–159 行 expected_capability 的 phase 枚举止于 004C6。当前合法 phase 004C7 被归为 SCAFFOLD_ONLY，而 state 为 COMPETITION_RC。新阶段测试路由遗漏。 | 在明确的 004C7 分支核对 capability、active/candidate 身份和 next_phase=None；保留 base_selected=False、third_party_integrated=False 等原断言。不要改真实 state 降级迁就旧断言。 |
| 2 | `tests/integration/test_actual_controller_adversarial.py::test_scenario_hash_must_be_bound_by_execution_capture_and_manifest` | 171–195 行同时把 plan、selection、semantic 的 scenario_hash 换成 c×64。resolver 检查显式值等于 scenario-input/v2 内容身份，故实际 CONTENT_MISMATCH，早于旧 NOT_CAPTURE_BOUND。controller:548–575 的 manifest preview → core:7030 trusted_freezes → resolver:5452，在 GATE_COMPARISON_SELECTION 记录 BLOCK；旧测试要求更晚的 GATE_COMPATIBILITY_PORTFOLIO。冻结历史门禁顺序假设。 | 保留“伪造 plan hash 必须 BLOCK/Final0”当前版本反例，要求实际更早 gate/reason；另以合法 plan 身份但伪造 selection 场景的独立攻击覆盖下游绑定。不要让伪造值越过 resolver 以触发旧错误。此整文件被历史 matrix hash 绑定，必须明确版本化当前适配与历史保全，见下文。 |
| 3 | `tests/integration/test_rc8_scientific_fact_binding.py::test_declared_scientific_requirement_cannot_ignore_missing_checker` | `_case` 调用 P0 helper；helper:239–249 已实际捕获 BASE/CAND 后才返回。测试:119–127 随后将 problem_requirements.scientific_facts_required 改 True。需求内容属于 scenario-input/v2，core:3434–3437 首先报 CAPTURE_SCENARIO_STALE；缺 checker 门禁尚未到达。冻结后修改身份的旧测试假设。 | 拆为捕获后修改需求 → STALE、捕获/hash不变、两类 Final ledger 均不存在；及预冻结声明科学要求 → 实际捕获 → 缺 checker → RECALCULATION_MISSING、Final0。不能重绑旧 capture 或忽略 requirements 身份。 |
| 4 | `tests/unit/test_c_target_batch_freeze.py::test_c_target_batch_freeze_is_current_and_complete` | checker:226–247 的 state.phase allowlist 止于 004C6；当前 004C7 必然进入 BATCH_FREEZE_PROJECT_STATE_DRIFT。工程历史冻结检查器的新阶段路由遗漏。日志只有 ok=False，没有打印 errors，未独立运行 evaluate；因此此处证明一个必然原因，不声称排除所有其他原因。 | 增加明确合法 004C7 历史继承路由，继续验证原 freeze payload、subject commit、runner/tree、registry、delivery receipt 与 hashes；定向执行后记录完整 errors。不要重写历史 freeze 或改成只检存在。 |
| 5 | `tests/unit/test_competition_rc_development_eval.py::test_start_registers_sealed_case_and_rejects_duplicate` | 测试 helper:40–50 未把 004C7 归为 legacy start locked。真实脚本:124–174 只允许注册指定旧 development 阶段，正确返回 readiness BLOCK/exit3；测试误走成功分支。新阶段测试路由遗漏。 | helper 加 004C7 锁定并断言 readiness reason、registry/正式state不变。要继续检验真正的旧注册成功/duplicate路径，使用显式合法旧阶段隔离 fixture。勿授权当前004C7通过旧入口。 |
| 6 | `tests/unit/test_competition_rc_development_eval.py::test_start_rejects_nonexistent_skill_commit` | 同一 helper 遗漏；真实 register 首先 require_competition_rc_ready，故当前阶段先 readiness BLOCK，尚未进入 SKILL_COMMIT_NOT_FOUND。 | 当前阶段保留 readiness优先；在授权旧阶段私有 fixture 中独立覆盖不存在 commit 的拒绝。不能交换真实硬门以迁就断言。 |
| 7 | `tests/unit/test_competition_rc_development_eval.py::test_freeze_binds_terminal_first_run_before_optional_unlock` | 同一 helper 遗漏，start 即 exit3，尚未建立 run/freeze。不是 freeze 顺序代码执行后回归。 | 当前004C7断言旧start锁定；保留隔离合法旧阶段中的 freeze-before-unlock 行为测试，不启动新的 known revision。 |
| 8 | `tests/unit/test_competition_rc_skill.py::test_skill_is_competition_rc_and_has_one_workflow_set` | versions:35–45 只有 C5→rc8、C6→rc9，查 004C7 直接 KeyError。新阶段版本测试映射遗漏。实际 project=0.3.0-competition-rc10、Skill=0.2.0-competition-rc10，但正式 active仍rc8，candidate=rc10。 | 新增C7精确 project/Skill/core/candidate版本一致性，保留14 workflows、4 roles、single Skill检查；不要把当前 active 提前置 rc10。 |
| 9 | `tests/unit/test_competition_rc_state.py::test_competition_rc_consistency_checker_accepts_canonical_state` | checker:156 的 rc8_state_valid 只含 C5/C6；184/195/224/231/347 缺C7阶段、subphase、status、next、blockers路径；448–465 缺active rc8→candidate rc10关系，486–502项目版本枚举止rc9。日志实际37检查中这7项 false，与静态缺口一致；原历史 evidence checks仍真。工程一致性检查器的新阶段路由遗漏。 | 增加 schema-valid C7 独立分支，结合当前 workspace/active 的相应资格状态，严格区分 BUILD_NOT_QUALIFIED 与 ENGINEERING_ACCEPTED，保留全部历史 hash/evidence checks。别把“可构建”视为正式资格接受。 |
| 10 | `tests/unit/test_fresh_completion_controller.py::test_captured_episode_preserves_failure_and_accesses_only_selected_test[False]` | fixture:127 把单一 `inputs["data/raw/toy.json"]` SHA 填入 scenario_hash；154、183 的 run/shared沿用同一错误值。它是64hex，但不是合法内容解析身份。131 advance→trusted_freezes→resolver即 CONTENT_MISMATCH；133以后 execute_case_code 循环尚未开始。旧 fixture 身份假设。 | plan省略scenario_hash请求推导，或在完整前置artifact/plan冻结时由resolver得值；run及shared都复用该值。保留成功候选选择、失败记录不计分、仅选定测试一次解封和再次completion拒绝断言。需主Agent实际定向复验。 |
| 11 | `tests/unit/test_fresh_completion_controller.py::test_captured_episode_preserves_failure_and_accesses_only_selected_test[True]` | 与#10同一行、同一 pre-execution 拒绝；尚未到“所有候选失败”controller逻辑。 | 同步修3处身份引用，继续要求 VALIDATION_NO_ELIGIBLE_SUCCESS、score=None、selected=None、无manifest/无test-access/Final0；不能把失败分数变为0或删失败分支断言。 |

## 历史保全及范围限制

`evals/results/phase-004c4/frozen_adversarial_controller_probe_matrix.json` 的 test_sha256 固定为 `eddb38912cdafd564bc3e2e4818aad601199b021c1591857b849e4941b9ea305`，正是 #2 文件本轮读取 hash；其自身 82–92 行测试还验证该文件 raw hash 和冻结 matrix payload。直接编辑旧测试再改旧 matrix hash 会改变已冻结证据，并制造/掩盖另一项失败。应由主Agent明确选择历史字节保全和当前版本适配的方法；本轮未改任何冻结文件，也未认可任何尚未出现的迁移实现。

结论为7项新阶段/版本路由缺失（其中2项在工程检查脚本），2项更早身份拒绝导致旧断言失配，2项共享fixture使用raw-input digest代替scenario identity。未发现这11项失败要求修改科学runtime的证据。不能据此断言修改后全测试一定通过；上游早停可能遮住后续断言，尤其#4未打印完整errors、#10/11未进入原目标逻辑。

本轮没有读取题目/raw/vault/答案、known结果或原始session日志，没有执行源码中的任何模型/checker/Final。只执行目录扫描、源码/日志文本读取、Git只读blob查询、标准库hash/JSON元数据保存。公共写入0，Git写入0，网络0，安装/配置变化0。附件导出与十四模块断言由主Agent独立处理，本轮未重复该工作。

开放项：上述11项需要主Agent修正后实际定向验证；#2历史冻结适配方式需明确并留存证据。主Agent后续编辑不构成本轮闭合验证。本轮不授予科学/工程总PASS、Decision Auditor PASS或正式接受。
