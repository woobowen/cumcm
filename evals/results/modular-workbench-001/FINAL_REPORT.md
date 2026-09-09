# 模块工作台建设与验收报告

工程状态：**MODULAR_WORKBENCH_ENGINEERING_ACCEPTED**。本轮必要工程路径和有界演练通过；不宣称陌生题泛化、旧整题科学通过或人工验收。正式记录为 qualification/candidate_snapshot.json、decision.json、decision_audit.json；当前状态派生报告不替代这些记录。

- 起点：604c7facda586cecb6785c44949f0cd1217cd297；受测候选：d1f8532d498307e3b4755c088ce6a0fadfb432bb。
- Skill：0.2.0-competition-rc10；仓库：0.3.0-competition-rc10；完整实现映射：c71b5640c0cadfc7fc891e8f1a8f856342519194024566bc1e2d82078ef7cbca。
- 最终定向测试：361 passed；完整CI：2369 passed / 1 skipped / 0 failed；strict：0 errors / 0 warnings。均为本轮实际结果。
- 分支：feat/phase004c5-p0-01-finalization-hf22-repro；[PR #12](https://github.com/woobowen/cumcm/pull/12)保持OPEN/DRAFT。已验证远端证据提交：4352efe054d0097d39572bb8d4b06247a015b049。最终报告提交的HEAD以同目录交付说明及最终对话的实际远端核验为准。
- [完整证据索引](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/EVIDENCE_INDEX.md) · [START_HERE](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/docs/modular_workbench/START_HERE.md) · [网页回执](WEB_RECEIPT.md) · [交付与恢复](DELIVERY_AND_RECOVERY.md)。

## R7与公共路径

先在旧subject复现RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND，Final0。共享cumcm_case.resolve_scenario_identity统一实际输入字节/角色、需求、假设、条件设计、时间/划分和指标的scenario/v2身份；prepare/execute/selection/controller/Final均采用同一解析。缺省和等价显式值分别在三类公共路径达到合法交接；错值、变更输入、范围冲突、捕获后语义变化被拒绝或STALE。HF22和独立科学核验不放宽，无未来Final倒填，无第二接受链。历史R7失败记录保留，当前闭合范围由新演练证明。

## 十四模块实际执行与恢复

公共入口为`.agents/skills/cumcm-modeling-evidence/scripts/cumcm_workbench.py`。每行先`prepare --module Mxx`，由Codex实际分析/写入合同或显式run，使用`complete --request WATER-Mxx`结束。所有模块实际执行COMPLETED、工程CONTRACTS_CHECKED、人工NOT_RUN；科学含义按本模块范围解释。每模块完成后真实调用`resume --request WATER-Mxx`，记录正式状态字节不变、automatic_starts=0、下一请求不存在。表中状态来自三问原创案例的实际completion，不是人为生成十四个PASS。

| 模块及真实回执 | 主要实际动作 | 原生状态 | 停止/恢复 |
|---|---|---|---|
| [M01](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M01.json) | 题目接收：分析/合同后complete | CREATED | 下一请求不存在；resume零启动 |
| [M02](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M02.json) | 需求拆解：分析/合同后complete | REQUIREMENTS_VALIDATED | 下一请求不存在；resume零启动 |
| [M03](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M03.json) | 专业研究：分析/合同后complete | SOURCES_PLANNED | 下一请求不存在；resume零启动 |
| [M04](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M04.json) | 假设公式：分析/合同后complete | SOURCES_PLANNED | 下一请求不存在；resume零启动 |
| [M05](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M05.json) | 数据审计：分析/合同后complete | DATA_AUDITED | 下一请求不存在；resume零启动 |
| [M06](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M06.json) | 候选方案：分析/合同后complete | MODELS_PROPOSED | 下一请求不存在；resume零启动 |
| [M07](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M07.json) | 基线定义：分析/合同后complete | MODELS_PROPOSED | 下一请求不存在；resume零启动 |
| [M08](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M08.json) | 实验设计：分析/合同后complete | EXPERIMENT_PLAN_VALIDATED | 下一请求不存在；resume零启动 |
| [M09](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M09.json) | 编程实算：run model/checker | RUNNING | 下一请求不存在；resume零启动 |
| [M10](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M10.json) | 比较选择：run controller | RUNNING | 下一请求不存在；resume零启动 |
| [M11](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M11.json) | 稳健误差：run controller | RUNNING | 下一请求不存在；resume零启动 |
| [M12](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M12.json) | 最终核验：run controller | FINAL_CANDIDATE | 下一请求不存在；resume零启动 |
| [M13](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M13.json) | 结论检查：run controller | EVIDENCE_VALIDATED | 下一请求不存在；resume零启动 |
| [M14](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/original/mixed/modules/M14.json) | 论文交接：run controller | READY_FOR_PAPER_HANDOFF | 下一请求不存在；resume零启动 |

实际request、work_report、completion和recovery_proof在original/mixed/modules/；另外两个案例也逐项走完十四模块。M02–M14缺前置均拒绝，M05不启动M06，M09不自动选模，M10不启动Final；错误scope、局部依赖STALE、并发writer、幂等导出/反馈、实际超时和失败恢复均由定向测试记录。Final被消费后无法通过重复请求或resume重启，子题不继承父题科学通过。

## 数值与已知任务范围

预测、非预测优化、三主问混合均执行两个候选、独立checker、一次Final、Claim及handoff。原创备水案例的整数采购候选为3L与5L各一份、11元，基线12元，逐分钟守恒独立复算。预测基线条件剩余9分钟，候选8分钟；混合案例两者条件剩余均8分钟，逐问选择保留不同Run。预测未来真值未观测。第三份独立Python程序不导入producer/checker，核对37/32/36个数值，最大残差约1.52e-13；结果可从公开JSON精确记录离线复算。错误未来信息、不可行解和缺主问不能成为全题handoff。

2016C新Q3子案例R2的实际subject为df430c0f0785e83b1a84726e88d25b7b2e0b9d0a，2模型/3checker/1Final，READY_FOR_PAPER_HANDOFF；与最终候选346个运行文件hash相同，Run身份不改标。AFFINE在6个相关历史截断点的剩余时间MRE=0.0519657541；状态3条件外推193.441777244分钟，真实终点UNKNOWN。Q1/Q2不在范围；相同方法或同样数值不构成精度提高。R1/R2两次允许revision已耗用各自Final并封存，没有第三次。R1未发布subject的本地隐私修正、原对象保留及不可作最终资格依据的限制见unpublished_subject_notice.json。原始附件未上传，完整已知题重跑需要合法附件，不能只靠本仓库声称重现全部输入。

## 审查回传、接手和独立角色

十四个本地审查包位于review_packages/，各约17–134KB，含原要求、已有公式/数据/代码、实际核验和负结果。M09不含未来Final；M12/M14包含真实Final ledger/check。原始hash与脱敏视图hash分开。没有自动上传。

本地反馈演练的故意错误草稿把2+3+5写成11，独立程序得到10，登记并复现后CONFIRMED；无依据意见NEEDS_EVIDENCE，替代设计ALTERNATIVE_DESIGN，旧包意见REGISTERED_STALE。错case/hash、凭据canary、越界路径、注入、畸形/重复JSON、超长及ZIP输入拒绝。网页不能通过该接口执行代码、正式PASS、修改预算或模式。以上是标明来源的构建演练，真实网页NOT_RUN。

原生受限上下文worker实际识别STALE后读取授权的新M04包，推导42符号/7公式并独立算术。主Agent包装安装提案，公共complete接受M04，M05未启动；属于真实原生协作，非OS隔离或严格盲审。原生协议审核32个最终源码文件及此前反例闭合、独立Python复算、主Agent自检、冻结机器决定后的原生Decision Auditor分别保存。原生协议审核未执行模型/checker/Final/known/full CI，其42份模块元数据审核来自先前659ccf5演练；最终d1f8532演练有新真实回执，不冒充审核者执行。意见多数不决定科学或技术通过。

## 失败、身份与限制

首轮CI中断时11 failed/1584 passed（full-ci-001），未列成功。修复审查附件以及004C7当前阶段路由后复验；历史RC5/RC7/2019C检查仍使用原Git证据，旧拒绝不变，旧测试矩阵hash仍绑定原测试字节。最终完整CI见full-ci-002。所有软件修复发生在候选冻结前，后续仅正式接受与交付记录。接受记录在提交前曾触发PROJECT_STATE_SELF_REFERENCE（strict-post-acceptance-001）；接受提交落盘后d1f8532成为前序内容提交，strict-post-acceptance-002实际0 errors / 0 warnings，另有87项接受后状态测试通过。失败记录保留。

旧RC8研究资格仅属于29cf1d7，RC9 subject10e8b038继续被拒；旧Validation0/2、旧Development0/2、新独立Validation0。当前RC10只获模块工作台工程范围资格。GUIDED_LOCAL与LAB_EVAL隔离，实际case独立于工具仓库；显式代码冻结使用真实无remote本地Git，旧case不能切模式逃逸历史。以后默认GUIDED_SINGLE_MODULE，本轮BUILD权限不继承。

没有访问2025保留题、benchmark-vault、答案或2026题，没有新盲测、付费API、基础模型训练、第二Skill或全局配置修改。原生Windows、真实网页、队员本人使用验收及TEAM_COMPLIANCE_REVIEW均NOT_RUN。实际测试为WSL2/Linux与既有Python3.11.14环境。本轮新增系统包、语言包、工具链、配置均0；未安装候选依赖。角色材料已交技术底稿：论文文字、数据图、模型示意图、表格、排版和提交分别给接口，未重写队友Skill或生成最终论文。通俗比赛手册等待用户将真实回执交回网页后定稿。
