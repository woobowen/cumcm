---
name: cumcm-modeling-evidence
description: Use for mathematical-modeling competition work from problem intake through validated models, experiments, final runs, and a structured evidence package for a separate paper team. Do not use for final paper prose, figure styling, document formatting, or submission packaging.
---

# CUMCM Modeling Evidence

Version: `0.2.0-competition-rc1`

Capability: `COMPETITION_RC`

Architecture: `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`

Assurance: `PUBLIC_DETERMINISTIC_AND_TWO_END_TO_END_SMOKES`

用于数学建模竞赛中从题目接收到冻结 Final Run、Claim 验证和结构化论文组交接的工作。默认中文输出。不要用于最终论文文笔、图形美化、LaTeX/Word 排版或提交打包；这些交给论文组。本 RC 未通过 sealed Stage 1、Stage 2、大规模消融、外部效度、生产适用性或成本评估。

## 启动与边界

1. 先读 `../../../GOALS.md`、`../../../WORKFLOW.md`、当前 `plans/active/` 和 `../../../state/project_state.json`；项目全局状态真源只能是后者。
2. 为每道题运行 `python scripts/cumcm_case.py init --case-root <case> --case-id <ID> --kind <general|prediction|optimization>`。case 的 `case_state.json` 只管理该题，不能写全局 state。
3. 原题和 `data/raw/` 一经登记即不可覆盖；修正写入 derived artifact 并保留 hash lineage。
4. 只读当前阶段对应的 `workflows/` 文件；跨阶段不确定性记录为 gap，不能猜测完成。
5. 禁止搜索 benchmark/历史答案、运行未审计第三方代码、打印或提交凭据、使用 test 生成/选择模型、以 Agent 多数票代替 Gate。

## 14 阶段

按顺序执行且不得跳跃：

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

每阶段都必须有 accepted、content-addressed artifact 和确定性 Gate。文件存在或 Agent 声称 done 均不等于完成。具体 inputs、outputs、拒绝、STALE、恢复和 next stage 见对应 workflow。

## 四个核心 Gate

- `GATE_WORKFLOW_STATE`：只允许 `modeling_orchestrator` 按固定序列推进独立 case state；严格校验字段、完整 history/evidence chain，并在每次推进前自动检查 STALE；`RUN_COMPLETED != RUN_VALIDATED`。
- `GATE_REPRODUCIBILITY_MANIFEST`：Run 绑定实际存在且 hash 匹配的 input/code/output files、真实 Git commit、该 commit 中逐个 code blob、聚合 hash、配置、seed、argv、allowlisted environment、outcome、failure/supersession、trusted capture/freeze；FAILED/PARTIAL/SUPERSEDED/STALE 保留但不排名。
- `GATE_LEAKAGE_SAFE_COMPARISON`：候选、metric、seed 和 split 先冻结；每个候选×seed 必须恰有一条 attempt，baseline 必须成功；test 只在选择后授权访问一次；bool、字符串、NaN、Inf 和非成功 attempt 不得评分。
- `GATE_CLAIM_EVIDENCE_AND_HANDOFF`：Claim 精确绑定 current successful Run 的 manifest/input/code/config/output/decision hash 与证据 IDs；handoff 的 Run、Claim、metric、reproduction 必须回连 case evidence chain，并通过 `modeling-to-paper/v1`。

任一 Gate 返回 BLOCK/STALE/REJECTED 时不得推进。Orchestrator 和 Auditor 都无权覆盖 Gate。

## 状态推进

合法主链：`CREATED → INTAKE_COMPLETE → REQUIREMENTS_VALIDATED → SOURCES_PLANNED → DATA_AUDITED → MODELS_PROPOSED → EXPERIMENT_PLAN_VALIDATED → RUNNING → RUN_COMPLETED → RUN_VALIDATED → ROBUSTNESS_VALIDATED → FINAL_CANDIDATE → EVIDENCE_VALIDATED → READY_FOR_PAPER_HANDOFF`。另有终止态 `STALE`、`REJECTED`。

原始与处理后数据都进入 `evidence_bindings`。输入、数据、代码、配置、seed、冻结集合或结果 hash 改变时，显式 `stale-check` 或下一次状态推进必须传播 `STALE` 和 dependency chain；恢复时保留旧 Run，新建 Run ID，重做所有下游 Gate。

## Case workspace 与命令

`init` 创建 `problem/ research/ data/{raw,processed}/ models/ experiments/ runs/ results/ evidence/ handoff/ state/`，以及根级 `case_state.json`。模板在 `templates/`；不能另建冲突 schema。

集中式入口 `python scripts/cumcm_case.py` 提供：`init`、`status`、`validate`、`manifest`、`claim-check`、`compare-check`、`stale-check`、`finalize`、`handoff`、`smoke`。先用 `--help`；会写状态的命令支持 `--check` 或 `--dry-run`。成功为 exit 0，输入/Gate/STALE/state/I/O 分别使用稳定非零码。CLI 默认离线且错误仅返回 reason code，不回显敏感值。

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
