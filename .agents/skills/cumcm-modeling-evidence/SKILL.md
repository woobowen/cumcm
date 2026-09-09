---
name: cumcm-modeling-evidence
description: Use for mathematical-modeling competition work from problem intake through validated models, experiments, final runs, and a structured evidence package for a separate paper team. Do not use for final paper prose, figure styling, document formatting, or submission packaging.
---

# CUMCM Modeling Evidence

Version: `0.2.0-competition-rc10`

Capability: `COMPETITION_RC`

Architecture: `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`

Assurance: `PUBLIC_DETERMINISTIC_REQUIREMENT_EVIDENCE_SELECTION_SEMANTIC_GATES`

用于数学建模竞赛中从题目接收到冻结 Final Run、Claim 验证和结构化论文组交接的工作。默认中文输出。不要用于最终论文文笔、图形美化、LaTeX/Word 排版或提交打包；这些交给论文组。本 RC 未通过 sealed Stage 1、Stage 2、大规模消融、外部效度、生产适用性或成本评估。

## 启动与边界

正常用户模式为 `GUIDED_SINGLE_MODULE`：只处理明确指定的 case、M01–M14 模块和
requirement 范围。模块内允许有界阅读、研究、编码、真实运行和核验；输出四维回执与
审查包后停止。用户需要明确调用下一个模块。一次建设演练的 `BUILD_AND_ACCEPT`
授权只属于该次建设记录，不能复制给未来用户。`LAB_EVAL` 历史协议继续有效。

首次使用先读 [START_HERE](../../../docs/modular_workbench/START_HERE.md)，按
[模块目录](references/modules.json) 仅加载当前任务卡及其 workflow。真实薄入口为
`scripts/cumcm_workbench.py`；它调用同一个 `cumcm_case` 内核与既有 controller。
`prepare` 生成请求、任务卡和 work report 模板，**没有完成分析**。Codex 必须实际工作，
再以 `complete` 验产物；不能把模板内 ACCEPTED 包装字段解释为科学结论已证实。
详见 [CLI 与恢复](../../../docs/modular_workbench/RUNBOOK.md)。

1. 先读 `../../../GOALS.md`、`../../../WORKFLOW.md`、当前 `plans/active/` 和 `../../../state/project_state.json`；项目全局状态真源只能是后者。
2. 新日常case通过 `python scripts/cumcm_workbench.py init --case-root <独立目录> --case-id <ID>`
   登记 `GUIDED_LOCAL`；实验case沿登记协议使用 core init。case 的 `case_state.json`
   只管理该题，不能写全局 state。需要完整工具仓库及其声明环境，不承诺独立复制Skill可运行。
3. 原题和 `data/raw/` 一经登记即不可覆盖；修正写入 derived artifact 并保留 hash lineage。
4. 只读当前阶段对应的 `workflows/` 文件；跨阶段不确定性记录为 gap，不能猜测完成。
5. 禁止搜索 benchmark/历史答案、运行未审计第三方代码、打印或提交凭据、使用 test 生成/选择模型、以 Agent 多数票代替 Gate。

## 14 阶段

依赖按顺序满足，但每次只执行用户指定模块，不自动串接：

1. `PROBLEM_INTAKE`
2. `REQUIREMENT_DECOMPOSITION`
3. `RESEARCH_AND_SOURCE_PLANNING`
4. `ASSUMPTION_AND_SYMBOL_DEFINITION`
5. `DATA_AUDIT`
6. `MODEL_PORTFOLIO_GENERATION`
7. `BASELINE_DEFINITION`
8. `EXPERIMENT_DESIGN`
9. `IMPLEMENTATION_AND_EXECUTION`
10. `MODEL_COMPARISON`
11. `ROBUSTNESS_AND_SENSITIVITY`
12. `FINAL_RUN`
13. `CLAIM_EVIDENCE_VALIDATION`
14. `MODELING_TO_PAPER_HANDOFF`

每阶段需要绑定实际产物及适用的工程检查。十四模块不伪造十四次原生 PASS；M01/M04/M07
等可保持原生状态，M10/M11在 RUNNING 内冻结开发选择与稳健性，M12停在FINAL_CANDIDATE，
M13/M14分别接受结论与交接。文件存在或 Agent 声称 done 均不等于完成。科学支持与队员
核验另列；具体 inputs、outputs、拒绝、STALE 和恢复见当前任务卡及 workflow。

`DATA_SUFFICIENCY_PREFLIGHT` 是第 5 阶段内的强制子 Gate：在 `DATA_AUDIT` 后、候选建模和
`EXPERIMENT_DESIGN` 前逐项判定 primary requirement；它不新增第 15 阶段。只有
`SUFFICIENT` 或受限的 `PARTIAL` 可继续，`ACQUISITION_REQUIRED` 必须先获取并复检，
`UNSATISFIABLE_WITH_CURRENT_INPUTS` 与 `UNKNOWN` 均 fail closed。

## 四个核心 Gate

- `GATE_WORKFLOW_STATE`：只允许 `modeling_orchestrator` 按固定序列推进独立 case state；严格校验字段、完整 history/evidence chain，并在每次推进前自动检查 STALE；`RUN_COMPLETED != RUN_VALIDATED`。
- `GATE_REPRODUCIBILITY_MANIFEST`：实验计划冻结 `data_audit` 的 required input hash registry；每个 Run 的实际 input 集合必须与其精确相等，并绑定实际存在且 hash 匹配的 code/output files、真实 Git commit、该 commit 中逐个 code blob、聚合 hash、配置、seed、argv、allowlisted environment、outcome、failure/supersession、trusted capture/freeze；FAILED/PARTIAL/SUPERSEDED/STALE 保留但不排名。
- `GATE_LEAKAGE_SAFE_COMPARISON`：候选、metric、seed 和 split 先冻结；每个候选×seed 必须恰有一条 attempt，baseline 必须成功；test 只在选择后授权访问一次；bool、字符串、NaN、Inf 和非成功 attempt 不得评分。
- `GATE_CLAIM_EVIDENCE_AND_HANDOFF`：稳健性结果必须由选中 Run output 携带定量 perturbation evidence，并精确绑定 selected model/run/input/config/output/decision；每个 requirement 有不同的 output-bound Claim ID 与 current evidence IDs；handoff 的 trace、Run、Claim、metric、reproduction 必须回连 case evidence chain，并通过 `modeling-to-paper/v1`。
- `GATE_REQUIREMENT_EVIDENCE_SELECTION_SEMANTICS`：`requirement-evidence/v1` 区分经验、派生、
  仿真、理论、假设、专家判断和未知来源；`data-sufficiency/v1` 在昂贵执行前验证字段、时间、
  实体、provenance 与 acquisition；`requirement-selection/v1` 支持 `GLOBAL_JOINT`、
  `PER_REQUIREMENT`、`JOINT_PORTFOLIO`；`claim-evidence/v3` 用结构化谓词限制 Claim 强度。

任一 Gate 返回 BLOCK/STALE/REJECTED 时不得推进。Orchestrator 和 Auditor 都无权覆盖 Gate。

## 状态推进

合法主链：`CREATED → INTAKE_COMPLETE → REQUIREMENTS_VALIDATED → SOURCES_PLANNED → DATA_AUDITED → MODELS_PROPOSED → EXPERIMENT_PLAN_VALIDATED → RUNNING → RUN_COMPLETED → RUN_VALIDATED → ROBUSTNESS_VALIDATED → FINAL_CANDIDATE → EVIDENCE_VALIDATED → READY_FOR_PAPER_HANDOFF`。另有终止态 `STALE`、`REJECTED`。

原始与处理后数据都进入 `evidence_bindings`。输入、数据、代码、配置、seed、冻结集合或结果 hash 改变时，显式 `stale-check` 或下一次状态推进必须传播 `STALE` 和 dependency chain；恢复时保留旧 Run，新建 Run ID，重做所有下游 Gate。

## Case workspace 与命令

`init` 创建 `problem/ research/ data/{raw,processed}/ models/ experiments/ runs/ results/ evidence/ handoff/ state/`，以及根级 `case_state.json`。模板在 `templates/`；不能另建冲突 schema。

集中式入口 `python scripts/cumcm_case.py` 提供：`init`、`status`、`validate`、
`data-sufficiency`、`preflight-output`、`execute`、`verify-evidence`、`prepare-final`、`evaluate-final`、`seal-run`、`manifest`、`compare-check`、
`selection-check`、`claim-check`、`semantic-check`、`stale-check`、`finalize`、`handoff`、
`smoke`。在候选建模前先运行 `data-sufficiency`；在 Final 前运行 `selection-check`；在
handoff 前运行 `semantic-check`。在实验计划冻结前，先于 `MODELS_PROPOSED` 状态用
`preflight-output` 校验 `experiments/` 内明确标记为非结果、不可排名、数值仅为占位符的
contract probe；它必须覆盖每个已接受 requirement，并具有 Final、Claim、figure-ready、
uncertainty、limitation 与定量 robustness 所需的通用结构，且不得登记为 Run 或结果。
`execute` 复用同一校验器检查每个成功 output，只运行实验计划中已冻结、与 Git blob 一致的
case-local Python 文件，并自动捕获起止时间、exit、stdout/stderr/output hash；任何非零
exit 或 output contract failure 都必须带显式 failure reason 并保留原 output，允许
`seal-run` 形成 FAILED manifest。全部候选 Development 运行完成后，用已冻结的选择
`decision-hash` 对 **selected Run 调用一次** `evaluate-final`；它写入 sidecar
`runs/<run_id>/sealed_test.json` 与 `evidence/final_evaluation_ledger.json`，不得改写
Development `output.json`，不得把 Development 指标当作 Final，也不得重复访问 test。
Final 执行开始前即消耗一次预算；异常、超时和不合法输出保留失败账本，不能重试取得新访问。
复用任何最终核验时，重新检查实际 input 和全部冻结 code blob，不能只核对旧账本里的字符串。
`seal-run` 重验 capture 后才写 manifest，调用方不得手填
`trusted_capture`。先用 `--help`；成功为 exit 0，输入/Gate/STALE/state/I/O 分别使用稳定
非零码。CLI 默认离线且错误仅返回 reason code，不回显敏感值。

## 四个角色

- `modeling_orchestrator`：唯一 case-state writer；调度阶段、绑定 evidence、调用 Gate，不覆盖结果。
- `problem_and_model_analyst`：拆题、研究计划、假设/符号、候选与 baseline；不访问答案或 held-out。
- `data_and_experiment_engineer`：数据审计、first-party 实现、运行、比较、稳健性和结构化结果。
- `adversarial_evidence_auditor`：独立检查漏问、假设、leakage、未运行代码、Claim 与复现；只读且不推进状态。

只有路径级写隔离明确时才并行；否则各角色提交 proposal，由 Orchestrator 串行落盘。角色说明见 `agents/`。

## Final Run 与论文组交接

Final Run 必须是 current、SUCCESS、可复现且由比较/稳健性 Gate 选择；探索性、失败、部分、superseded 或 stale Run 不得重标。交接包必须包含要求、trace、数据字典/质量、假设、符号、公式、来源、模型、Run、指标、表、figure-ready data、验证、稳健性、不确定性、失败、limitations、Claim evidence、复现和 `approved_by=["MACHINE_TECHNICAL_GATES"]`。该字段绝不表示人工批准。

## 搜索、泄漏与恢复

外部事实需登记 Source、查询和 evidence binding；只使用当前问题允许的来源。Validation/Held-out 答案一旦可见，该 case 永久降为 Development。异常、缺失、hash mismatch、未冻结集合、非有限数值或不完整 handoff 一律 fail closed。按 `workflows/failure_recovery.md` 建新修订/Run，不覆盖 raw、失败证据或旧状态历史。

## Claim contract v2

新 case 保留 `claim-evidence/v2` 的 hash lineage，并以独立 `claim-evidence/v3` semantic bundle
记录逐 requirement 类型、证据等级、选中 Run/output/metric/comparator、支持谓词、不确定性、
反证、限制和强度；字段见模板及 `workflows/claim_evidence_validation.md`。
`PREDICTIVE` 的 `held_out_test_valid=true` 必须交叉绑定 selected Run 的
`evaluate-final` ledger（一次授权、hash lineage、非 selection 用途）；Development output
或 semantic payload 自证一律 fail closed。
总体 Claim 独立于任一局部 Claim；primary coverage 和 supporting Claim IDs 按集合精确匹配，
`REQUIREMENT_UNION` 的 scope 必须逐项等于输出已捕获的局部 scope。总体 statement 仍绑定
captured Final scope，但不以它与局部文本是否相等判断支持。任一输入、输出、Run 或 decision
断链仍 fail closed。旧格式通过纯函数 `derive_claim_contract` 生成派生视图，禁止原地重写历史。

## 科学事实与逐问支持

每个实际 output 必须包含 `scientific_evidence[requirement_id]`，描述真实生成方法
`generation_method`、实际 `source_ids`、`scope={fields,time,entities}` 和 `metric_values`。
metric ID 必须在该 Run 的实际数值指标中唯一可解析；不同问题的不同数值不能复用同名指标。
即使是 `DESCRIPTIVE` 也不能省略生成事实。case adapter 只能提出需求和 Claim 类型；不得
因为 JSON 完整、source 原始类别是 empirical、或输出有 uncertainty/limitations 就填 SUPPORTED。

source 的 hash 绑定已审计的真实输入文件；archive 与解压工作簿属于不同对象，应分别登记
provenance，不能把 archive hash 冒充工作簿内容 hash。经验数据可以驱动条件仿真，但条件
结果不证明外部实效。条件结果绑定真实 `assumption_artifact_sha256`，未来情景范围单列
`conditional_scope`。预测不得改成描述性 Claim 绕过验证；缺少标签时可交付预测及缺口，
不能宣称准确性已经证明。原始 source 类别、生成方法、Claim 支持范围必须分别记录。

新科学 case 的每个 primary requirement 必须设置 `scientific_facts_required=true`，包括
描述性统计和条件仿真。它要求另一个预登记、Git-bound 的 case-local checker。先将它加入
`required_code_files`，再在 RUNNING 调用 `verify-evidence --case-root <case> --run-id <Run>
--code-path models/check.py`。checker 接收 `--case-root --run-id --output`，读取该 Run
的 output 并写 `scientific_check.json`：根级 `run_id`、`output_sha256`，逐问
`requirements[ID].metric_values`、非空 `recalculation_residuals`，以及领域判定
`feasible` 和 `constraint_residuals`。计算一致性残差须覆盖实际输出表/向量/过程，不得仅以
相等的样本数替代整个结果核验；逐问 metric ID 和数值同时匹配。领域失败的正确负面描述
可以获支持，但计算不一致不能。`FEASIBILITY` 还要求领域约束通过；全局最优另需闭合界。
每个残差记录实际 `value`、
`relation=LE|GE|EQ`、`limit`、`tolerance`。自动 Gate 检查数值和完整捕获链；checker
不得导入 producer 的解法或同一验证 helper 来冒充算法独立。误差单位、容差、约束含义和
独立性还需原生只读审核。独立 Python 程序不等于独立多 Agent 审核。
`verify-evidence` 保存真实 subprocess 的 v2 capture；接受时还会实际运行冻结 checker
并比较完整 JSON 结果，不能由可重写的完整回执自证执行。同一进程仅复用相同完整 hash
绑定的成功复算。checker 只写传入的 `--output` 路径，须支持独立临时输出，不修改 Run/raw。
实际核验过程另存 ignored `.cache/scientific-check-replays/`。这不构成 OS 隔离或签名证明。
Development 用 `evaluation_design.mode=DEVELOPMENT_NO_FINAL_EVALUATION`，真实训练/诊断
分区保留，`splits.test=[]`；它不能调用 Final evaluator。整个 `evaluation_design` 进入
`execution_policy` freeze。非预测 Final 用 `NONPREDICTIVE_FINAL_VERIFICATION` 和三个空
split，实际执行独立科学核验；不得伪造预测测试集。

全局最优性另需独立上/下界闭合证书；仅求解器 success、候选池大小、实际使用数量或一个
可行计划都不证明最优。主问题的目标、约束、决策数量和评价量必须逐项对应。缺少主要
问题的解、最小/最大性证明或必要事实时，保留 PARTIAL/拒绝和全部失败记录，不能仅降级
措辞后宣称全题完成。

合法非预测任务在实验计划明确 `evaluation_design.mode=NONPREDICTIVE_FINAL_VERIFICATION`，
三个 prediction split 数组均为空；不得伪造训练/测试样本。最终 controller 检查全部所选
Run 的独立数值复算，记录 `scientific_final_verification_count=1`、`test_access_count=0`，
不调用预测 Final evaluator。该路径不支持 PREDICTIVE/CAUSAL/POLICY_EVALUATION Claim。
Development 的显式 `DEVELOPMENT_NO_FINAL_EVALUATION` 仍允许零 Final 访问，但不等于
正式 Validation 或完整科学通过。正常预测路径继续要求真正冻结的 held-out 边界。

跨题检查要点：区分拟合样本、独立实体、重复预测次数；区分类别可分、概率校准与外部
泛化；确认扰动确实改变模型输入；按独立实体处理重复采样。优化需按题意核对实际支付量、
物料/运输守恒、跨期状态递推、目标优先级和极值证据。题目参数与配方只进入 case 目录。

## RC9 的条件预测和独立 Final

非预测任务的开发比较使用 `NONPREDICTIVE_DEVELOPMENT_COMPARISON`，访问计数为零。
开发比较、逐问选择、必要稳健性和独立核验通过后，公共 `prepare-final` 冻结具体产物；
`evaluate-final` 先记录授权与 STARTED，再执行独立 checker。`ROBUSTNESS_VALIDATED` 到
`FINAL_CANDIDATE` 必须验证成功 Final 回执。失败、超时和部分输出消费一次预算；
`evaluate-final --review-existing` 仅复核既有回执，禁止再次执行。完整控制器可用
`--check-code <已冻结的独立程序>` 在同一进程捕获开发核验，避免重复审核隐式追加核验启动。

未知未来终点不属于生成条件预测的最低输入；`prediction_spec` 预先声明目标、已知输入、
模型依据、条件和历史验证要求。Claim 保持 `PREDICTIVE`，用 `prediction_scope=CONDITIONAL_ESTIMATE`
明确未来精度未验证。若题目要求已验证的实际精度，缺失目标证据仍拒绝该强结论。
`CONDITIONAL_PREDICTION_FINAL_VERIFICATION` 使用独立算术 Final，不声称新增独立 Validation。

同实体延续预测使用 `temporal-visibility/v1`：每个起点绑定特征、预处理和拟合观测 ID，
每条观测绑定实体、观测时间和可用时间。任一使用晚于起点的记录即拒绝；
`NEW_ENTITY_GENERALIZATION` 仍要求拟合实体与目标实体隔离。
指标合同绑定 target、quantity、target_unit、unit、prediction_origin、formula、denominator、
sample_unit、aggregation、weights、direction、zero_denominator_policy，并从逐样本数值独立重算。
remaining-time 与 elapsed-time 的分母不能互换。模型敏感性范围不能称为校准预测区间；
独立程序验算不能称为独立外部数据验证。完整字段示例见 `references/rc9_science_contracts.md`。
