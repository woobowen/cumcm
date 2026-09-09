# RC9 独立 Decision Auditor：PASS_FOR_REJECTION

受审 subject：`10e8b038d571b88ce2b7f2388da00a618c774f69`。
受审决定：`evals/results/phase-004c6/qualification/rejected_r2/rc9_candidate_decision.json`，
SHA256 `c27c464858f0738807945cdd2acb4500669e2153d496a77538d6b6f837aed625`。

结论：已有机器拒绝有冻结证据支持，可以保留为正式负决定。**本 Decision Auditor 的 PASS 仅表示拒绝决定审计通过，候选接受仍为 FAIL/BLOCK；RC9 不具备激活资格。**
没有反对保存这项负决定的重大异议。R7-001 仍是未修复的候选接受阻断，不能由本审计、预运行审核或 CI 通过消除。

## 实际执行与独立性

先执行 `ls -la`，确认现有 `.venv` 和项目结构；按授权读取根及相关规则、当前计划、机器决定、冻结元数据和相关源码。主 Agent 是唯一公共文件、Git 和 formal state 写者。本审计仅在自身 `.cache/pr12-rc9/decision-auditor-001/` 写入审计日志和独立标准库检查脚本。

本审计先检查冻结协议与原 checker，随后在精确 subject 工作树 `.cache/pr12-rc9/qualification-replay-r2` 实际执行：

```text
<REPO_ROOT>/.venv/bin/python scripts/check_phase004c6_rc9_release.py --stage candidate
```

开始 `2026-09-09T04:20:27.571014+00:00`，结束 `2026-09-09T04:20:34.377659+00:00`，实际 monotonic 6.80663154 秒，exit 2。未使用 `--write-decision`。原 checker SHA256 为 `43f471d71f086ac7af2ca550a0a88693b810f712a83fb9df8b72defae6a7df68`；snapshot SHA256 为 `dea0eb8b3597129ccf73532c15e1dd884e1f5e3d99a909eed4ae6bcf93e71023`。checker、snapshot、decision 在执行前后哈希一致。

stdout SHA256 为 `720908b815b13786dc67b6771dac34dd8f21de15dba9b9c60673581601262258`，stderr 为空。输出与归档机器决定逐字段相等，恰为：

- `RC9_NATIVE_REVIEW_INSUFFICIENT:native_result_review`
- `RC9_RECEIPT_NOT_PASS:native_result_review`

另一次实际执行自写 `audit_metadata.py` 于 `04:24:48.899286` 至 `04:24:50.302910 UTC`，exit 0，1829 条元数据/哈希/绑定断言通过。这主要是逐文件验证，**不是 1829 个科学实验，也不是本审计重新运行 full CI**。真实资格 checker 重放 1 次，独立元数据审计脚本 1 次；两次均有完整原始 stdout/stderr 和命令时间回执。初始一次 `rg` 误用了不存在的 preparation 脚本名，exit 2；随后通过 `rg --files scripts -g '*004c6*'` 找到正确路径。此检索错误独立保留，不当作项目执行失败。

## 冻结身份、执行回执及历史

独立构造 protocol 指定的 path set，792 个路径与 snapshot 一致；逐个核对 Git subject blob 和当前工作区 SHA256，全部一致。各验证命令 `executed_head` 虽是后继记录提交，但映射范围内相对 subject 无差异；不能将其解读为同一完整仓库提交。snapshot 绑定已有 subject，不包含自身未来提交；实际 candidate/decision 在 subject 后生成，未发现提交自引用。

历史 `phase-004c5` 在起始历史 subject 与当前 HEAD 的 Git tree 完全一致，且无该目录未提交差异。旧 Validation 仍为 0/2，本轮新增独立 Validation 为 0。当前审计时主工作区 active candidate slot 和 RC9 activation 均不存在，active Skill 仍为历史 RC8。这些是本次取样观察；本审计不声称后续全局终局 state 或远端已经审核。

八项 receipt 的身份、subject 和证据绑定均核对。focused/full CI/strict/historical 的原始 stdout/stderr 哈希与 receipt 一致，公开日志可由原始流按声明的路径归一化逐字节生成。focused JUnit 为 101 passed/0 failed，十项 neutral specification 的 nodeid 均出现在成功 JUnit 中；三条 E2E 源码使用实际 subprocess CLI，并断言其限定 handoff 终点。full CI 原始日志包含 2240 passed/1 skipped，exit 0，实际 argv 为 `bash scripts/ci.sh`。这是已有实跑证据的核验，本 Auditor 没有重跑 full CI。

原生结果审核007的公开工具摘要确有46项记录，其原始 commands 文件哈希与公开 summary 绑定一致；原生预执行审核006确有16项记录。工具记录与哈希提供可追踪的本地实际调用证据，本审计不额外声称拥有外部调度器证明。其他 Agent 的结论从未被当作投票。

## 两个状态轴与真实负终局

`native_result_r2.status=FAIL` 精确对应原生007 receipt 的 `candidate_acceptance_status=FAIL`。原生 receipt 顶层 `status=PASS` 的含义是负终局事实和有边界数值发布的审核通过；其 `negative_terminal_facts_status=PASS` 与候选接受状态不是同一轴。规范化 receipt 保留原件、实际 Development tuple 和 R7-001 未闭合异议，因此机器拒绝并非误读原生 PASS。

两份新 Development terminal 都是 FAILED，每题两条实际成功模型 capture、三次注册 checker starts、零 Final。每题四次 model CLI 请求中，前两次确以 `RC_RUN_ID_INVALID`、exit 3 在模型进程前拒绝，后两次为实际模型 subprocess。执行 ledger 使用进程 starts 计数；请求预算不得据此声称还剩两次。两个新根共70项 execution artifact 哈希成立；逐问 terminal 与 Development receipt 完全一致。第三次 checker 是相同冻结独立实现的新进程复算，有注册 ledger 和回执；它不是第三种独立算法或新的外部真值验证。

两题实际 trace 均只有六个 Gate：前五 PASS，第六 `GATE_COMPATIBILITY_PORTFOLIO` BLOCK，原因 `RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND`。前后 case state hash 未变；terminal 的 accepted Final/handoff 均 false。后续 semantic、aggregate、Final 和 handoff Gate 未到达，不能报告为通过。

## R7-001 的独立源码与元数据核对

原 subject 执行器 `cumcm_case.py:5593–5599` 对缺失 scenario_hash 从按 path 排序的输入 SHA 列表生成 canonical hash。两个实际 plan 都缺该字段，其字节哈希与失败 trace 的 input hash 一致。仅使用 capture 中输入哈希重算得到：2016 为 `6125b5fb0afcd5caedafcc374f9b21f0450832e51e1e33e1f362328ee5aa171f`，2015 为 `b993bac3a526d38def4e133cd4112a60ac58bb04c1b623a5986e79116eff42e6`；同题两 capture 和 manifest 全部相等。

controller `finalize_fresh_c_validation.py:619` 则直接传 `plan.get("scenario_hash")`，实际为 None；core `cumcm_case.py:1168–1169` 比较到非空 capture hash 后拒绝。执行器与调用端默认值语义确有分歧。它不能仅被表述为 plan 违反必填字段，也不能因数值计算成功就宣告修复完成。当前代码与受审 subject 一致，第三个 functional candidate 未创建；两次上限已经使用，保留失败、不改冻结 plan、不追加 Final 和不激活均符合本轮约束。

已有公开有限数值显示的是有条件的 Development 计算。2016 的拟合/插值诊断与剩余寿命 MRE、未知未来真值和未校准敏感性范围必须分开；2015 的参考误差、独立实现差异与99个条件时窗必须分开，基线不满足参考阈值的事实仍在。此审计核对它们属于失败终局中的有限结果，不重算物理模型或评价未知真实精度。

## 必须保留的证据限制

1. 原 adjudication receipt 的 UTC 区间为第一裁决进程的9.272077秒，但 elapsed_seconds=15.928334133 取在第二次重放及拷贝之后。已从录制源码确认字段采样位置，主 Agent 以新增 `timing_clarification.json` 保留原字节并区分两种范围；第一进程 monotonic 和第二重放单独时刻保持 UNKNOWN。本 Auditor 的新重放另有完整准确计时，不替换旧记录。
2. `native_protocol_r2` 的归一化范围不能扩大原生006实际 `VERSION_PLAN_TARGET_REGISTRATION_PREPARATION_DIFF_ONLY`。原件明确未覆盖实际 r2 注册/root readiness、全部协议完整性或真实数值结果。新增 `protocol_review_scope_clarification.json` 保留此边界；不能把预运行局部 PASS 描述成全面资格 PASS。当前拒绝不依赖扩展这一范围。
3. focused/full CI 的 UTC span 与记录的 monotonic duration 存在差异，原值已保留在 metadata_results。两类时钟不被擅自互换，不从这些数据声称精确吞吐/成本。本审计没有证据据此认定未执行；原流、日志、JUnit 和 subject 绑定均一致。

`--stage workspace` 在没有候选 slot 且 RC9 未激活时返回 `PASS_PENDING_CANDIDATE`、qualified=false；这是未激活工作区工程一致性检查。归档拒绝、明确保留 R7-001 与有效接受为 false 后，这一返回值不会把机器拒绝转为通过。将来最终报告/state 必须继续明确 RC9 blocked，不能仅引用 workspace CI PASS。此次审计仅覆盖现有负决定；最终全局 state、生成报告、后续 final CI、Git 提交/推送及 remote SHA 不在本审计范围。

未读取原题全文、原始数据文件、答案、保留题内容或 vault；未运行真实题模型、科学 checker 或 Final；未安装包、改全局配置、写公共 state 或执行 Git mutation。未证明外部科学精度、全题成功、泛化、contest compliance 或远端交付。
