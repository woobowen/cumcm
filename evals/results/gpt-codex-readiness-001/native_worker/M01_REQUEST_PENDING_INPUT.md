# 待材料补齐后复制；本段尚未提交执行

```text
MODE=GUIDED_SINGLE_MODULE
case位置=[待填：本机case目录或新题合法材料目录；同时提供原题、附件清单及合法数据位置]
module=M01
scope=ALL
本次目标=[待填：当前目标；完成原题与附件接收核验，识别精确材料缺口]
特殊限制=本次仅M01；原件不可覆盖；不搜索题解；未经单独模块授权不启动模型、Run、Final或后续模块
请加载docs/gpt_codex_workflow/START_HERE.md和本模块操作卡，以及正式cumcm-modeling-evidence Skill、M01任务卡与所指workflow。核对本地实际状态、revision、输入与运行implementation；自行生成内部request ID和hash，不能继承示例身份。
本次只做M01：逐件阅读题面、注释、附件与表头；建立原件清单/sha256及附件关系，写题意概述。
实际读取原件与数据并独立判断；如果网页建议有问题，用具体定位、公式/反例和影响提出异议。prepare不是结果，实际工作后才complete。必须做：清点文件与题面提到的附件；抽读表头/表尾；区分原件、派生数据、未提供材料。
返回：problem/original.md、data/raw原件、intake_registry及work/M01.json；原题缺页时列精确缺口。 同时给执行/工程/科学范围/人工核验四维状态、本地审查包、最小缺口及恢复入口。缺附件不造数据；可完成已收到材料的登记，但不得写整题接收完整。
完成或部分完成均停止；不自动启动后续模块，不把本请求扩大为全题、Git发布或额外Final许可。
```
