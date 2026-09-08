# PR #12 / RC8 本轮综合验收报告

**RC8 已获得并激活限定研究/Validation 资格；两道陌生题均实际运行、审核并冻结负面终局，
科学通过 0/2；交付工程仍未通过完整 CI。** 本报告不把候选准入、局部数值成立、
native READY、终局记录完整或远端已接收提交混为全题成功。

机器状态仍以 `state/project_state.json`、case registry、候选接受决定和逐题终局为准。
当前 phase 004C5、status `IN_PROGRESS`、技术结论 `C_TARGET_VALIDATION_FAILED`，
`next_phase_allowed=null`。以下完成表描述本轮工作，不新增 formal state 枚举。

## M0–M5 与未完成项

| 项目 | 已完成且可核验的工作 | 尚未成立的目标 |
|---|---|---|
| M0 | 继承锚点、合法004C5状态/活动计划、新候选身份与历史隔离 | 无新接手材料前置阻断 |
| M1 | 中立正反例先冻结；实际CLI/controller事实绑定、独立结果校验、Development无Final路径 | 2016暴露过严数据/分组规则；2015暴露非预测Final前置循环，未闭合 |
| M2 | 2021/2022共15个新CLI captures，真实失败保留；另1次Q4证书构造及独立审核 | 两道开发题全题科学完成均为false，外部实效未验证 |
| M3 | subject29cf1d7测试、原生审核、自动资格、接受后激活；新题前远端冻结 | 非比赛作品审查通过，非泛化证明 |
| M4 | 2016、2015串行独立实跑；两份固定候选、独立审核、正式终局及远端交付 | 0/2科学通过；2016未获Final/handoff，2015流程不合法 |
| M5 | 当前本机完整CI和远端PR合并提交CI已运行；补充检查、复现说明、报告/恢复入口 | 两项CI断言仍失败，工程Definition of Done未达成；最终交付观察另附回执 |

研发从 **2026-09-08 17:46:50 UTC（北京时间09-09 01:46:50）** 开始，硬截止
**2026-09-09 01:46:50 UTC**，总上限8小时，未重置。23:35附近可见Goal计量为
4,545,021 tokens、20,294 seconds；这是平台累计计量观察，不能当作精确模型输出token、
现金费用、CPU用量或无等待的连续工作时长。实际收口时间与最终可见计量在交付回执记录。
没有强制凑足8小时；候选在约2小时51分完成激活远端冻结，为两题留下完整窗口。

## 继承、身份及版本

接续锚点 `17f109cadc8524c285af6a50776e6c3decb8b3e8`；分支
`feat/phase004c5-p0-01-finalization-hf22-repro`；[PR #12](https://github.com/woobowen/cumcm/pull/12)
保持Draft。P0-02 evaluate-final、P0-03/HF22关键路径及其22项定向复验为继承成果，
本轮核验并只补实际发现的缺口，没有把它们重写计作陌生题成绩。两题v5保留为历史Development。

历史RC7仍在其原subject验证；接续PR代码已不同于RC7，不能用旧标签/旧hash冒充。
当前候选共享受测subject为 `29cf1d7566809519ca92b6a29f555ce0c0b5b204`，772个映射文件。
接受/激活提交 `8ef732b45cf3cb04262317cdfa13a176b47eebe0` 于20:37:30Z前置远端核验，
随后才打开2016输入。受测实现、接受决定、激活和交付回执分开绑定，没有自引用提交。

- Project：`0.3.0-competition-rc8`；正式Skill：`0.2.0-competition-rc8`。
- Python distribution声明：`0.2.3`，是另一版本维度，没有强行对齐或安装新包。
- 候选checker在active仍RC7时评估RC8通过；激活后live checker通过。
- 两题使用相同冻结共享代码、规则与已有环境。冻结后没有修改受测文件或旧结果hash。

证据：[候选snapshot](qualification/rc8_candidate_snapshot.json)、
[接受决定](qualification/accepted_decision.json)、
[Decision Auditor](qualification/decision_audit/REPORT.md)。

## source / scope / support 实际闭合程度

修复位于既有 `cumcm_case.py` 与实际Development/controller路径。原始source类别、
输出生成方式、结论支持范围分别记录；经验数据经计算生成条件仿真，仍不能证明外部实效。
case adapter只提出需求；接受依赖实际source/输入hash、Run/代码、output、逐需求metric值、
独立checker结果和审查。预测性需求改称DESCRIPTIVE不能逃过其验证要求。

独立checker必须绑定实际Git代码和输入，并经capture/replay；只有“计数正确”或空残差表不能
冒充独立复算。NaN/Infinity/bool计数、虚构checker、伪造支持范围及Final事实均有拒绝证据。
算术相符、条件可行和全局最优证明分开；本轮Q4另补精确界，并未靠把词语降级宣称全题完成。

中立预期在修复前冻结，见 [fact_binding_specification.md](qualification/fact_binding_specification.md)、
[neutral_fact_freeze.json](qualification/neutral_fact_freeze.json) 及后续最小缺口冻结。
Development合法临时路径保留实际train/validation、空test与Final拒绝。
非预测独立验证无需伪造预测测试集，但新题暴露其现有正式顺序契约矛盾，不能宣称已全面闭合。

Final保留“执行前STARTED”、代码/参数/输入绑定、失败访问与重用hash检查。2015的实际违规
仍按负面结果处理，没有用这些局部守卫掩盖跨Gate顺序缺陷。

## 新增Development科学证据

全部使用新case-owned v6路径、核验官方原输入hash，不覆盖v5。15个实际CLI captures分为
2021：8个（5 SUCCESS、3 FAILED），2022：7个（7 SUCCESS）。Final调用均0。
当前候选实际运行subject为 `d9a43b8d6d0d1fdc57e639080a26b3a88054ac31`；
旧对照运行subject为4515597、较早候选为4d2a0b8，不能把全部15次capture归到d9。
当前相关运行实现与最终共享subject等价的文件证据单列，不能说这些进程在29cf1d7提交时执行。
2021另有一次Q4证书构造，保守计入第9/9次数字试验；它没有伪造第九个原生CLI Run。
2022使用7/9预算，未用完的预算没有被当作额外成功。

2021：区分399候选池、旧对照实际使用168个供应商、RC8当前方案使用14个供应商
及限定条件模型最小数14。当前条件基线采购成本
20430.789，对照20470.624；损耗102.059，对照110.619。但同定义独立历史综合压力指标（越小越好）
为9.705398，对照1.758417，当前更差；运输超载47/48，对照48/48，库存不足23/48，对照12/48。
当前基线未获比较排名资格，较早不同实现的三候选不能冒充当前实现同条件获胜。
采购/运输逐问目标、真实初始库存、未来供给与实际费用仍有缺口。

Q4原达成值约40246.403m³/周仅是条件结果。补充精确弱对偶证书现在给出严格包围区间
**[40246.40307264614, 40246.40311289260] m³/周**，精确间隙约0.00004024645≤0.001。
主程序独立Fraction verifier和原生审核分别检查3216条对偶约束、402+8个容量约束。
该证明只针对固定序列化十进制参数的第一目标LP；原浮点计划微小越界经共同缩放才精确可行，
不证明实际企业增产、库存闭合或后续成本最优。

2022：69个已知测点中67个有效、56个artifact groups、8个未知对象。修正前内部CV
错误包含12个内部test groups；修正后只使用44个train/validation groups，2次共88项内部CV。
这种排除不能恢复已暴露数据的盲性。12个validation groups上三候选的validation composite loss分别为
0.121658、0.019885、0；Hellinger/KNN被选中。这不是概率校准或外部准确率。
另有2997次置换、27项回推、仅2对配对资料及bootstrap/扰动检查；扰动量1.29852、
域内7/8对象0翻转都不能替代未知对象正确率。11/13项限定需求获支持，预测/全题仍证据不足；
独立checker没有重新拟合分类器。题内统计拟合确实发生，不能写成“没有训练任何模型”。

完整证据：[v6 SCIENCE_REPORT](development/v6/SCIENCE_REPORT.md)、
[Q4证书报告](development/q4_certificate/REPORT.md)、
[原生审核与端点处置](development/q4_certificate/AUDIT_DISPOSITION.md)。

## 陌生题真实分母与14阶段终局

题集和完整7200秒/题预算均在新题结果前登记，顺序2016 C、2015 C；未使用2014替补。
**计划2，启动2，实算2，审核后终局冻结2，科学通过0。** 终局完成不等于14阶段全部接受。
两次fresh worker使用新上下文，只收到冻结Skill、通用指引、各自输入及合法专业资料，
未互传结果或接收开发者题目专用解法；这是工具上下文与政策隔离，非OS沙箱。
模型预训练是否曾接触题目不可验证；答案一直封存。

| 事项 | 2016 C / VALIDATION-004 | 2015 C / VALIDATION-005 |
|---|---|---|
| 完整episode | 20:37:30–22:37:30Z | 21:53:34–23:53:34Z |
| 原输入 | 官方DOCX+XLSX，hash登记 | 官方C-only DOCX，无另附C附件；另取NASA/JPL计算资料 |
| pre-run远端冻结 | b71d00f，21:13:28Z | 6f01263，22:23:38Z |
| 实际模型/原checker | 2 / 2 | 2 / 2 |
| Final / 预测test访问 | 0 / 0 | 1非预测验证 / 0 |
| 审查后冻结时间 | 21:51:49.240104Z | 23:13:18.995181Z |
| 正式结果 | C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT | C_TARGET_VALIDATION_FAILED |
| 终局远端提交 | a03597be9a83a38ce4bcc4dba76cf8c574327045 | 6be924e7903a201236a9cdd93ee75d66b839d1d6 |

2016用两模型实际拟合电池放电资料：Q1九条分段曲线及五个9.8V剩余时间；Q2条件55A
总时长1162.588分钟；Q3条件剩余193.442分钟。Q2跨电流检查误差1.022%不等于55A真实误差，
Q3模型范围184.826–205.475分钟不是校准预测区间。独立复算的历史状态1/2前缀末端剩余时间相对误差分别为4.1001%/8.1186%，
是各状态单个目标的误差；原elapsed-time MRE为0.5991%/1.0869%。目标、分母和聚合均不同。
data-sufficiency PARTIAL、comparison group_overlap阻断，阶段11–14未获接受。
common controller在前置阻断且attempts=[]不抹去先前两次真实Run。
原生审核指出“没有未来真值就不能预测”和“同一电池历史一律泄露”过严，主编排器接受
这些科学异议，并保持冻结Gate/输出与负面结果，未进行事后调参或新选择。

2015建模太阳/月球高度和黄昏窗口。来源DE441为THEORETICAL计算星历，坐标与几何条件
为ASSUMPTION，不能叫实测。两个模型原checker参考角度RMSE分别0.528066°与0.000749386°；
前者未满足参考精度，失败科学比较保留。当前选中模型产出99个名义窗口（北京15、哈尔滨18、
上海12、广州12、昆明13、成都13、乌鲁木齐16）、2562日历行、503扰动窗口、168参考位置。
独立审核检查已有端点/中点1806项及日历时刻10161项，条件算术得到支持。
最窄昆明窗口约15.936秒；2秒实现一致性不保证物理窗口稳健，名义容差可能接近窗口本身。

2015选定Run/config在Final前锁定，数值比较已先生成，但正式selection-check、compare-check、
robustness接受分别在Final之后发生，违反冻结Skill前置顺序。
非预测comparison同时要求scientific_verification_count=1，形成现有流程依赖矛盾。
case-owned controller产生READY；公共`finalize_fresh_c_validation.py`没有执行。
后续三次checker子进程（含Final/两个Gate重放）不是三个Final，也不是三次独立科学审查。
首次原生audit FAIL，修订为负面判定后独立Decision Auditor PASS；主编排器冻结FAILED。
没有把条件数值成立转为正式14阶段通过，没有改包或重跑。

逐题证据：[2016科学报告](CUMCM-2016-C-VALIDATION-004/scientific_report.md)、
[2016终局](CUMCM-2016-C-VALIDATION-004/terminal/decision.json)、
[2015科学报告](CUMCM-2015-C-VALIDATION-005/scientific_report.md)、
[2015终局](CUMCM-2015-C-VALIDATION-005/terminal/decision.json)。

## 审查角色与证据强度

- 原生独立Agent：事实绑定/候选审核、POST_DECISION审核、两题终局审核、Q4限定科学审核均有
  实际独立调用、输入hash与工具证据；没有用主Agent自检或Python脚本冒充多Agent。
- 独立程序：Development数值checker、fresh各自独立算术、Q4无优化器Fraction verifier。
  它们检验各自覆盖的计算/约束，不自动证明统计泛化或经验有效性。
- 主编排器：唯一公共状态/Git/正式接受写入者，核验真实工具时间与subject，处理科学异议。
  2015严格只读角色返回JSON/输出后由主编排器落盘；报告明确该产物归属。
- 人工TEAM_COMPLIANCE_REVIEW：NOT_RUN；没有比赛作品审查、ready、merge或人工覆盖技术拒绝。

2015原生审查曾按CSV行序比较得到伪差异，后改用稳定身份键核对为0差异，两条观察均保留。
Q4审核初始两条启动输出未完整离线归档，数值审核输出齐全；这些限制在其publication/REPORT
保留，不能宣称所有审查工具输出现已无条件独立离线复现。

## 本机、远端、merge-tree与历史检查分开报告

| 受测对象 | 实际结果 | 不能推出的结论 |
|---|---|---|
| 候选29cf1d7 | full CI 2153 passed / 1 skipped；100项定向通过；后续CI检查及native审核通过 | 当前交付HEAD CI通过 |
| 本机6be924e | full CI 2151 passed / 2 failed / 1 skipped；pytest349.95秒，命令exit1 | 工程完成 |
| PR合并提交22c097256777009083e107768992c14de822685b | Actions34289738652：2151 passed / 2 failed / 1 skipped；pytest461.27秒 | 远端feature独立checkout CI通过 |
| 本机CI中断后的15项独立补查 | 历史冻结/交付、strict、render、RC8 live checker等全部PASS | 把full CI失败改为PASS |

本机CI命令回执分别记录wall起止与monotonic耗时，两者观察不同，不强制改成同一个数。
两项失败是冻结tests中的八案例闭集断言、旧phase终局断言；registry当前合法保留十个案例。
早期另有新增registry required field / first_run_evidence缺失，已按固定事实修复并复验。
不能删除合法案例、绕过测试、改旧hash或借用旧CI来“绿化”当前结果。
这些测试属于772个受测文件；修改将产生新subject，不能保留RC8原资格映射冒充同一实现。
本轮保持一次冻结和两题相同规则，把修复留在明确的新候选工作段。

本机回执：[local_ci_terminal_6be924e.json](delivery/local_ci_terminal_6be924e.json)；
远端：[实际PR合并提交CI](https://github.com/woobowen/cumcm/actions/runs/34289738652)、
[checkout证据](delivery/remote_ci_6be924e_observation.json)；
[15项补查](delivery/post_ci_checks_terminal_6be924e.json)。
最终HEAD/远端SHA、Draft状态和本机merge-tree计算在独立交付观察记录，避免提交自引用。

## 环境、限制与下一步

新增系统包0、语言包0、工具链/字体0；无全局配置更改。新增配置仅两题各自的
`.gitattributes`，使已冻结CRLF CSV按正确换行规则检查，未改CSV字节。
既有Python3.11.14环境36包与资格快照相同，pip check通过；这不是fresh install或跨平台lockfile。
详见 [DEPENDENCIES_AND_REPLAY.md](delivery/DEPENDENCIES_AND_REPLAY.md)。
原始题目/数据、完整受限正文和缓存仍ignored且hash绑定；缺原始资料时必须按登记来源重取并
验证，不能声称公开Git独自包含全部输入。完整Git历史也是旧subject检查前置。

2025保留题、benchmark-vault、2026当届题未访问；旧release/Validation/first-run和v5未改。
没有基础模型训练或付费模型API；NASA/JPL公开科学数据服务调用确实发生，失败请求保留。
现金/缓存/排队成本UNKNOWN，不伪造零费用或token细项。

仍未证明：跨陌生C题可靠全流程完成、外部预测准确率、概率校准、实际企业采购运输可行性、
竞赛作品合规或泛化。主要剩余问题是非预测Final前置循环、同实体时间任务的合理数据隔离、
目标指标分母及科学支持判据、历史/新状态兼容测试。两题终局不可重跑或改判。

下一步安全动作是先只读核验终局与当前交付，再为**新的维护/候选subject**冻结中立正反例：
非预测选择/比较/Final的无环依赖、合法同实体历史与未来标签泄露对照、动态案例集及明确phase
路由。随后才修改并重新测试资格。该建议不是已经实现的修复，也不授权复用2016/2015作新盲测。
恢复入口：[DELIVERY_AND_RECOVERY.md](DELIVERY_AND_RECOVERY.md)、
[checkpoint.md](checkpoint.md) 与活动计划。不得重置本轮预算或绕过已有BLOCKER。

交付一致性原生初审指出五处摘要口径问题（两项ERROR、三项WARNING），本修订已分别
修正供应商计数含义、历史压力指标、2016单目标相对误差、2022 composite loss和运行subject
覆盖范围。初审FAIL及其受审原报告逐字节保存在
[report_audit_001](delivery/report_audit_001/REPORT.md)，没有覆盖为PASS。
后续维护的十项中立正反例见[next_subject_neutral_cases.json](delivery/next_subject_neutral_cases.json)，
状态为SPECIFICATION_ONLY_NOT_EXECUTED，不能计作已实现修复或通过测试。
