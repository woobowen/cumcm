# CLI 与恢复 Runbook

在工具仓库根目录使用既有 `.venv/bin/python`。下列 `WB` 表示
`.agents/skills/cumcm-modeling-evidence/scripts/cumcm_workbench.py`，`CASE`表示仓库外独立case目录。
工具需要完整仓库，case代码另用实际无remote本地Git绑定；不能手填虚构commit。

```bash
.venv/bin/python "$WB" modules
.venv/bin/python "$WB" show M05
.venv/bin/python "$WB" init --case-root "$CASE" --case-id DEMO-WATER
.venv/bin/python "$WB" prepare --case-root "$CASE" --module M01 --scope ALL --request-id INTAKE-1
```

prepare 返回 PREPARED，生成 `evidence/module_requests/INTAKE-1/TASK.md` 和
`work-report.template.json`。Codex实际阅读原件、写入分析与适用合同，再按原结构填写work report。
早期内容是待实验验证的分析，不能把包装字段或prepare当作求解完成。M01/M02可用ALL，
待需求拆解后由工具定位真实requirement IDs。内部hash由工具和Codex按实际文件计算。

```bash
.venv/bin/python "$WB" complete --case-root "$CASE" --request INTAKE-1 --report work/M01.json
.venv/bin/python "$WB" status --case-root "$CASE"
.venv/bin/python "$WB" resume --case-root "$CASE" --request INTAKE-1
```

每次complete给执行、工程、科学范围和人工核验四维结果并导出小审查包；停止后用户再指定下一模块。
M04保留公式、单位与假设证据；M07完成基线代码与接口，数值模型启动属于M09。
M08由Codex根据实际文件冻结实验计划、代码、指标、split和明确Final方式，进行output contract probe。
冻结本地代码是用户明确调用的操作，不是init或prepare的隐含Git发布：

```bash
.venv/bin/python "$WB" freeze-code --case-root "$CASE" --code models/runtime_model.py models/independent_check.py
.venv/bin/python "$WB" run --case-root "$CASE" --request EXECUTE-1 --operation model --candidate BASE --seed 20260906 --run-id RUN-BASE-20260906 --code models/runtime_model.py
.venv/bin/python "$WB" run --case-root "$CASE" --request EXECUTE-1 --operation checker --run-id RUN-BASE-20260906 --code models/independent_check.py
```

必须覆盖已冻结candidate×seed，并保留失败。M09完成不选模；M10准备逐问选择proposal后显式运行controller；
M11核验已计划的真实扰动；M12调用独立Final并停在FINAL_CANDIDATE。M13与M14分别接受结论和交接：

```bash
.venv/bin/python "$WB" run --case-root "$CASE" --request SELECT-1 --operation controller
```

此命令的范围取决于绑定的请求模块，不能通过run参数越过模块。提前Final、错scope、缺前置、旧输入或
实现漂移均拒绝。M10/M11保持RUNNING是既有科学Final前置要求，不是伪造十四个PASS。

```bash
.venv/bin/python "$WB" review-export --case-root "$CASE" --request INTAKE-1 --output reviews/intake-copy --zip
.venv/bin/python "$WB" feedback-import --case-root "$CASE" --feedback feedback/review.json
.venv/bin/python "$WB" feedback-resolve --case-root "$CASE" --finding ACTUAL-FINDING-KEY --disposition NEEDS_EVIDENCE --evidence evidence/followup.json
.venv/bin/python "$WB" context-export --case-root "$CASE" --output context/revision-1
```

导出仅本地。ZIP成员由工具固定生成，导入不解压ZIP。新大脑需要用户实际上传context、START_HERE和相关审查包。
无依据意见不能确认；真实反例需独立核查；旧包意见可登记STALE，不能写当前正式PASS。

恢复流程：先resume查看原请求、操作与原生状态。相同完成请求/操作只复用，不再启动；
导出中断可重复complete补出包。仍运行或FAILED的操作保留原始账本，不能删除后重复尝试Final。
输入或实施版本变化时，新root承接不可变原件和来源，重新执行受影响模块；新输入须另行登记，不能改旧raw。

```bash
.venv/bin/python "$WB" revision --case-root "$CASE" --destination "$CASE_REV2" --case-id DEMO-WATER-R2 --scope ALL
.venv/bin/python "$WB" scoped-child --case-root "$CASE" --destination "$CASE_CHILD" --case-id DEMO-WATER-PART --scope REQ-A
```

子范围必须包含其依赖；不继承父case的PASS、Run或Final。独立子题可以单独交付，但绝不表示全题完成。
范围不符的整体运行计划不能在一个窄请求中执行。共享依赖变化影响所有使用者；无关文件不改变有效结果。

实际建设演练与边界结果以[新结果目录](../../evals/results/modular-workbench-001/checkpoint.md)记录的
受测SHA、日志、模块回执和矩阵为准；命令示例本身不是执行证明。测试平台为实际记录的平台，
没有Windows原生证据时不得宣称通过。真实网页/队员审核、比赛合规未发生即为NOT_RUN。
