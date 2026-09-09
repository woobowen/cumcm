# Round 10 — 当前适配与只读闭合复核

结论：本轮已审范围内 **已证实 OPEN material code findings = 0**。原 round09 的失败日志、旧源码身份和诊断仍单独保存，未改写。此结论是代码/协议和现有元数据的有界复核，不是科学、工作台整体资格、Decision Auditor 或发布接受。

## 身份与实际范围

- 开始实际 HEAD：`659ccf597657ea947efbc11e25dada542ca40d08`，2026-09-09T10:49:05 UTC。最后实际 HEAD：`d1f8532d498307e3b4755c088ce6a0fadfb432bb`，10:55:16 UTC。
- `read_files.json` 于 10:55:08.427040 UTC 保存 34 个实际读取文件的完整 SHA256、相对路径、659 初始 Git blob SHA 和当时 HEAD Git blob SHA；所有 34 文件工作区字节等于 d1f8532。11 个文件相对 659 有改变，保留对应 diff/命令时间，不把最新字节混称为最初读到的字节。
- 每个编号命令都有 `*.command.json`、stdout/stderr 原字节及其 hash。实际执行是 `ls -la`、`rg`/`sed`、只读 Git 查询、私有标准库 metadata/hash 校验；没有导入或执行项目模型、scientific checker、Final、known case 或 full CI。
- 第一条命令的目录扫描确认 `.venv`、scripts/tests/src/contracts/state、Skill 和 ignored cache 均在仓库内；未创建平行环境。

## 原 11 项适配

1. 004C7 capability、旧 development-start 锁定、rc10 project/Skill/candidate 映射、competition consistency 和 batch freeze 的新阶段分支已补齐。active rc8 与 candidate rc10 继续区别；没有将旧 development 注册入口授权给004C7，也没有重置正式状态迁就旧测试。
2. fresh controller fixture 省略错误显式 hash，完整 plan 冻结后调用真实 resolver，run/shared 三处统一使用解析身份；原候选失败不计分、仅选定一次测试访问等行为断言保留。
3. AP-004 当前测试拆为显式 plan 伪造（COMPARISON_SELECTION / CONTENT_MISMATCH）和仅 proposal 伪造（COMPATIBILITY_PORTFOLIO / PORTFOLIO_HASH_MISMATCH）。缺 checker 拆为预冻结科学要求和捕获后变更要求→STALE。最新版本增加两个 Final ledger 均不存在和适用分支 capture hash 不变，未修改科学 runtime。
4. 已独立按原始字节验证：旧 `frozen_adversarial_controller_probe_matrix.json` 与929失败subject一致；`git show 604c7facda586cecb6785c44949f0cd1217cd297:tests/integration/test_actual_controller_adversarial.py` 的 SHA256 为 `eddb38912cdafd564bc3e2e4818aad601199b021c1591857b849e4941b9ea305`，等于旧 matrix.test_sha256。当前测试适配通过固定旧 Git blob 校验历史字节，未改旧 matrix 凑 hash。

以上为本人源码/原字节复核。主Agent报告73项、随后80项定向通过及全部CI尾部Python检查exit0；本轮未读取这些单独测试日志/未重新执行，因此不将其记为本人测试结果。原失败应保留，最终 full CI 尚需独立记录真实终局。

## 后续路由扫描与协议适配

只扫描 scripts/tests 中包含004C6的源码，原匹配14文件；重点审查主Agent指定5个尚无004C7文件的当前状态判断，没有机械更改所有历史分支。

- `check_target_problem_policy.py`：新增004C7 repair集合、plan映射、branch映射、候选Skill身份。当前schema验证和历史batch/heldout/独立题占比仍在。
- `check_phase004c4_fresh_validation.py` 与 `check_phase004c4_rc7_release.py`：004C7走已有17f109历史state验证。RC8 CURRENT_CANDIDATE仍要求原C5身份，--historical仍单独处理；未把当前rc10伪称rc7/rc8运行。
- `check_skill_training_consistency.py`：新增active rc10枚举，BUILD/LIMITED/BLOCKED下精确active rc8→target rc10条件；合法module开发的FROZEN证据读取terminal_decision。
- `test_phase002d_r2a_start_freeze_dependencies.py`：新增C7当前plan，另核对归档C6 plan与604c7原字节；旧C6→C5归档特例保留。
- 额外三处 `check_claim_scope_repair.py`、`check_c_target_2019c_validation.py`、`check_phase004c2_acceptance.py` 的diff仅在已存在successor路径增加C7，历史hash/树/终局条件未改。

对最后两处协议适配的证据链复核：

- target policy只对 `MODULE_USABILITY_DEVELOPMENT` 豁免不适用的独立题generalization_axis和旧formal别名，仍必须 DEVELOPMENT、independent_problem严格False、KNOWN污染；独立题占比仅计strict True，不会把该类模块开发升级为独立验证。新增两例明确拒绝independent=True或set_type=VALIDATION。
- training在新分支之前仍累计 `repository_registry_errors`。共享验证器要求新case的注册schema/授权路径/父历史终局原Git字节及hash/注册与case字段绑定；FROZEN必须精确terminal路径与raw hash，终局再校验subject_commit==case.skill_commit、phase/version/case/parent/decision tuple。新terminal_decision分支没有删除这些错误或把缺证据当成功。
- 准确边界：target policy单独ok只说明其policy/allocation范围；它自身没有调用共享注册验证器。完整训练检查及CI中的repository_registry_errors测试继续承担注册/终局真实性门禁。不能引用target policy单项ok替代该证据门禁。本轮只读源码，不读取known注册/终局内容、不执行共享repository检查。

上述静态遗漏均已在最终34文件快照中闭合；未保留已证实的适配绕过。

## 原创附件与逐模块 resume 的实际元数据复核

私有 `metadata_check.py` 在10:52:02和10:52:42实际运行，**仅标准库读取元数据，不运行workbench**。结果分别保存在 `metadata_results.json`、`metadata_results_v2.json`；34个编号read-command记录保留实际argv/UTC/exit/输出hash。

- `public-water-{mixed,optimization,prediction}-005.json` 三条实际既有command均执行于659ccf5，exit0，绑定日志的SHA均重算一致。不会称其执行于后续d1f8532。
- `/tmp/cumcm-modular-workbench-001/acceptance-005/{kind}` 的42份已有resume记录逐一核对：module/request匹配，state_before_sha256==state_after_sha256，automatic_starts=0，当时下一request不存在。结合冻结driver顺序：complete后实际调用resume，保存记录之后才进入下一模块。
- 42个manifest的package canonical hash、request canonical hash、completion raw hash、original_hashes/view.source_sha256与completion.artifact_hashes交叉匹配；report列出的artifacts均进入export。
- 各阶段应有附件清单缺失0。M09清单含原始题/输入的路径与hash、假设、两份代码、plan、两份capture/output/checker，没有Final附件；M12/M14清单含scientific_final_ledger及适用final_check。新增driver只加入当时已经存在的材料，避免后续修改的manifest让旧report失效。

此处核对的是记录、路径清单和已声明hash之间的关系；**未读取题目、raw输入、导出view正文，也未重算它们的源内容hash或数值结果**。未将这些元数据一致性结论当科学计算正确性、独立实验复现或真实用户使用验收。

## 尚不属于本轮的结论

没有执行任何model/scientific checker/Final/known case，计数均0；没有full CI、网络、安装、配置或公共文件/Git写入。所有本人写入仅本round私有目录。known R2仍是父任务已报告的df430c0实际执行，不在本轮复核范围；第二次full CI、统一candidate、Decision Auditor、整体科学资格和远端交付均未由本轮接受。
