# 一次性 BUILD_OPERATOR_KIT_AND_VERIFY 工作记录

授权：用户当前任务与本机 BUILD_PROMPT 全文。起点 a3d2279b439a332239bab2ff75362bb070100042，PR12 OPEN/DRAFT。独立支持记录，不改旧 phase/acceptance/state，也不建立第二科学状态。普通用户仍逐模块调用。

本轮里程碑：输入审计 → 独立 operator kit v1.0.0 → 新原创有界演练 → 串行原生受限交接与只读审核 → 定向检查 → 一次必要完整CI → 本地三包与索引 → commit/push/远端SHA/Draft核对。

冻结范围：identity() 的全部现有覆盖保持；旧 results、Final、state、active plan 按 historical_protection.json 保留。新资料路径 docs/gpt_codex_workflow 不在该覆盖内。旧 active plan 的终局不续预算。本文件仅为当前一次性任务 checkpoint。

新演练设计：已知原创工作流结构的新实例 READINESS-COOLANT-001；外部全新 root；两个合理候选、一个 seed，各一次模型进程；每个 Run 独立 checker；M10选择、M11稳健性以后独立科学Final一次。预检、真实模型、checker、控制器/内置重放、导出分别记账。三次同根因无进展即分析换路，不删除失败。基线可平或胜。不访问新赛题、答案或vault。

审核：主编排器唯一公共文件/Git/state写者；最多主编排器＋一个原生受限worker。worker只读指定bundle，只能在自己ignored scratch写建议。受限上下文按实际工具约束声明，不声称OS隔离或严格盲审。独立Python算术与原生审查分别记录。

输入审计初次失败：外层manifest部分生成文件没有source_sha256，审计器错误假定字段必有，KeyError发生在解压/算术前。修正为缺失来源hash单列，不伪造值；保留此失败记录。第二次审计结果见input_audit.json。原输入不变。

环境：WSL2/Linux，现有.venv；没有安装系统包、语言包或工具链，没有改全局配置。用户输入及Zone.Identifier保留、不暂存。

恢复：先读本文件、input_audit.json和当前git status，检查新增case命令账本。已消费Final不能再运行，已完成模块用status/resume复核。新网页回传不等待，交付时标pending user。

资料层预检：新辅助脚本最初命名operator.py遮蔽Python标准库operator，CLI启动失败，未写包或运行case；重命名package_operator_kit.py修复。新代码行宽检查也已修正。均未改核心。

Checkpoint：独立资料subject 0ad91e3 已提交；原core implementation保持73fbd01944221102b2c3e09ed05f49ca3057ecd7aeb6f23b95fd29f7db9603ff。新package定向11 passed；继承边界定向13 passed（本次实际执行，含同实体/未来标签/缺问/旧context），完整CI尚未执行。
新case READINESS-COOLANT-001已实际M01–M05，各模块stop/resume核验；M06只PREPARED等待受限worker建议，模型0/Final0。旧root按历史记录定位后确认本机不可得，review_exports索引不可得；未伪造导入。
旧阅读附页生成首轮误将bare modeling_to_paper当content wrapper，KeyError，尚未写附页；按真实结构修正为claim_evidence字段，第二次生成通过。两条原文缺口均核实，算术不变。

模型前预检发现新演练adapter复用helper的seed默认仍为旧seed、语义statement默认仍为占位。尚未模型/Final启动；显式传入新SEED并从新实际output字段绑定statement。该修正限新演练adapter，核心和旧case未改；下一数值阶段使用新的提交subject。

M06首次安装遇init预建DRAFT模板，complete因work/M06.json缺失拒绝；无模型/Final启动。精确比对现行DRAFT模板并确认未绑定后安装，原始失败回执保留。第二次公共complete的execution=COMPLETED、MODELS_PROPOSED、next_module_started=false；resume automatic_starts=0且M07不存在。主摘要脚本一度误读status字段，已按实际execution字段核验，未改变case。
