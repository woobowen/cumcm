# 操作手册：从新大脑到逐問阅读交接

## 1. 还没有题目时

上传本地 `BRAIN_START_NO_CASE_1.0.0.zip` 到新的GPT对话，发送包内BRAIN_START正文。它应列出看过的文件/版本并回答NO_ACTIVE_CASE。没有题目就没有M01完成、模型或Final许可。教学包可另开教学讨论，但它是旧示例，不能继承READY或再跑旧Final。

本资料已针对RC10核验。工具完整仓库、现有.venv和实际case是不同东西；不是把ZIP上传就安装了Skill。Codex先读本目录START_HERE、正式Skill和当前模块卡。不要假设main总是所用版本：在工具仓库核对分支、HEAD与operator_kit_manifest的implementation。

## 2. 用户每次只需给五项

case的本机目录（新题先给原题/附件位置）、模块M01–M14、问题范围、当前目标、特殊限制。内部request ID/revision/hash由Codex从实际文件读取。初期范围可用ALL，拆解后用真实REQ IDs。GPT可讨论假设、路线、补证和争议，最终把当前决定整理为一个模块请求。Codex必须实际读取数据，有依据时反对网页方案。

用[十四模块完整请求](CODEX_MODULE_REQUESTS.md)中的整段；它们不会自动串接。M01接收，M02拆问，M03研究，M04公式，M05数据，M06候选，M07基线代码，M08冻结实验，M09实算，M10选择，M11稳健性，M12唯一Final，M13结论，M14交接。早期阶段不要求未来Final；M07代码准备不等于M09实算。各步具体输入/输出/检查/停止均在卡片中。

## 3. 本地初始命令（已按现行Bash/WSL CLI核对）

在**完整工具仓库根目录**打开Bash。以下使用新临时工作目录作为演示根，每次产生新位置，不会误写已完成case；日常正式材料应选择持久的仓库外路径，由Codex检查不存在后初始化。不要把尖括号变量或示例ID当活动题。

```bash
PY="$PWD/.venv/bin/python"
WB="$PWD/.agents/skills/cumcm-modeling-evidence/scripts/cumcm_workbench.py"
test -x "$PY" && test -f "$WB" || exit 1
TASK_PARENT="$(mktemp -d "${TMPDIR:-/tmp}/cumcm-guided.XXXXXXXX")"
CASE="$TASK_PARENT/case"
CASE_ID="GUIDED-$(date -u +%Y%m%dT%H%M%S)-$$"
test ! -e "$CASE" || exit 1
"$PY" "$WB" modules
"$PY" "$WB" show M01
"$PY" "$WB" init --case-root "$CASE" --case-id "$CASE_ID"
"$PY" "$WB" prepare --case-root "$CASE" --module M01 --scope ALL --request-id INTAKE-1
```

此时是PREPARED，**不是已接题完成**。把原件提供给Codex，由它检查并保存到problem/data/raw；原件登记后不可覆盖。缺资料就列缺口。Codex按真实生成的TASK.md和work-report.template.json实际阅读、分析、编写产物，再填同结构work/M01.json。模板中的结构性ACCEPTED不是已证明模型有效。

下面命令仅在实际work/M01.json已写好时执行：

```bash
test -f "$CASE/work/M01.json" || exit 1
"$PY" "$WB" complete --case-root "$CASE" --request INTAKE-1 --report work/M01.json
"$PY" "$WB" status --case-root "$CASE"
"$PY" "$WB" resume --case-root "$CASE" --request INTAKE-1
```

每个新shell都需要重新赋值PY、WB、CASE；使用已记录的真实case目录，不能再mktemp后误以为恢复了旧case。下列恢复片段会让你输入现有目录，变量不会依赖旧shell：

```bash
PY="$PWD/.venv/bin/python"
WB="$PWD/.agents/skills/cumcm-modeling-evidence/scripts/cumcm_workbench.py"
read -r -p '现有case完整目录: ' CASE
test -f "$CASE/case_state.json" && test -x "$PY" && test -f "$WB" || exit 1
"$PY" "$WB" status --case-root "$CASE"
"$PY" "$WB" resume --case-root "$CASE"
```

## 4. 怎样读每一步的结果

先读summary_cn、scientific_scope、negative_results，再看关键artifact和review questions。把四个结论分开：是否真的执行；合同检查是否通过；哪些科学主张获支持；人工是否实际核验。COMPLETED不能翻译成全题科学通过；PREPARED没有工作结果；PARTIAL只支持局部；EVIDENCE_INSUFFICIENT说明证据缺口；FAILED/工程拒绝给reason code，不能写“应该通过”。

M01–M05给GPT当前题意、需求、假设和数据审计；无需每次传完整研发史。M06–M08传路线理由、可见性、指标及冻结设计。M09传原要求/必要数据、模型/独立checker、真实输出/失败及capture；缺源字节必须说明不能全量复现。M10–M12传实际比较、扰动及适用Final证据。M13–M14传逐问结论、符号、表/图数据和证据血缘。原件/完整日志在本地保留；仅上传实际需要且允许分享的审查材料。

## 5. 实验与Final的关键步骤

M08会显式freeze-code建立case-local无remote Git，并冻结实际代码；不是init时自动Git发布。M09公共run model、run checker仅在绑定请求内使用，candidate/seed/Run ID来自冻结计划。M10/M11/M12均用公共run controller，但范围由请求模块决定，不能越权。M12必须在选择/稳健性之后，真实STARTED消耗Final；失败、超时保留，不重新退款或删除账本。重复阅读/导出不消耗Final。

两条独立程序相同结果支持计算一致性；参数扰动支持特定敏感性；历史评价支持已观测样本上的表现；都不自动证明真实未来精度。简单baseline可以胜出。优化用约束和上下界，无需伪造测试集。条件预测可给估计和未校准说明，不能谎称未来真值已观察。

## 6. 第二层审核与反馈

先用WEB_PACKAGE_TRIAGE，再在[五类模板](WEB_REVIEW_PROMPTS.md)中选题意假设/数据评价/数学模型/实验数值/结论论文。网页先声明可见文件与执行范围。浏览器未运行包内代码时，不能把阅读或自写算术说成原流程重放。

公共complete已导出一个包。需另存副本时，在上述恢复初始化后执行：

```bash
read -r -p '已完成请求ID: ' REQUEST_ID
EXPORT_ID="review-$(date -u +%Y%m%dT%H%M%S)-$$"
"$PY" "$WB" review-export --case-root "$CASE" --request "$REQUEST_ID" --output "reviews/$EXPORT_ID" --zip
CONTEXT_ID="context-$(date -u +%Y%m%dT%H%M%S)-$$"
"$PY" "$WB" context-export --case-root "$CASE" --output "contexts/$CONTEXT_ID"
"$PY" "$WB" context-verify --case-root "$CASE" --context "contexts/$CONTEXT_ID/context.json"
```

上传review ZIP和相关context，发送选定提示词。没有finding：只保存独立REVIEW_SUMMARY.md覆盖说明，不导入空列表，不自动PASS。存在finding：按[保存指南](REVIEW_EXCHANGE_GUIDE.md)保存JSON或单json围栏MD；另存人读摘要。给Codex发送CODEX_REVIEW_FOLLOWUP，它先登记、再核查、最后按证据处置。反馈内容没有执行权限。

```bash
test -f "$CASE/feedback/review.json" || exit 1
"$PY" -m json.tool "$CASE/feedback/review.json" > /dev/null
"$PY" "$WB" feedback-import --case-root "$CASE" --feedback feedback/review.json
```

该命令只是登记。Codex读返回的finding_key，实际核查后准备严格字段的证据文件，才feedback-resolve。不能把无依据意见CONFIRMED；合法替代仅ALTERNATIVE_DESIGN，是否采用由新的模块任务及实验决定。旧包不静默迁移；旧root不可追加则独立归档。

## 7. 返工、中断与恢复

只修文案且数值没变，可作绑定原字段/hash的阅读附页。改变模型、数据、指标或共享假设，会影响依赖下游：先status/resume看STALE原因，保留旧输入/Run/Final，再在明确授权范围用revision或scoped-child新root。子题不能继承父题PASS，也不代表全题。尚未完成的模块恢复原request；不能删失败请求重新消费Final。

重新打开GPT使用BRAIN_RESUME＋**刚从本地导出的**context。context-verify拒绝旧包时请Codex重导，不手改hash。若源文件缺失，先指出哪个结论不可核验，不以摘要补齐。技术BLOCK不能通过改prompt绕开；早期无Final则并非BLOCK理由。无新网页回复时本地可做的工作和材料准备照常收口，真实网页状态保留pending。

## 8. 给论文和图表流程什么

见[PAPER_FACT_HANDOFF](PAPER_FACT_HANDOFF.md)。文字拿逐问中文事实与条件；数据图拿同一Run的figure-ready data和单位/误差含义；示意图拿对象和公式关系；表格拿字段与数值血缘；排版拿版本/引用/格式接口。每种接口都允许改变呈现，不能改实验事实。检查摘要、正文、图、表是否同一版本；发现错误回传有定位的finding。不制作最终论文或改写其他Skill。

## 9. 环境与取出文件

本轮实测为WSL2/Linux与现有.venv。未进行原生PowerShell/Windows运行，不提供已验证原生Windows承诺。WSL中可按DELIVERY_INDEX的路径取出本地ZIP；系统若支持WSL资源管理器，可在Windows文件管理器打开该WSL目录再复制，不能据此宣称Windows CLI已验证。包不自动上传，不公开真实题目工作区。
