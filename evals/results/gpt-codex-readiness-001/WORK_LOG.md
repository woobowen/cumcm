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

Checkpoint：数值 subject 637d102 已完成新例 M07–M14；模型 2、显式 checker 2、Final checker 1、内置 checker 重放 4，Final 恰好一次 SUCCESS。提取统计时最初误找 receipt.json，随后误用 argv 绝对 root 搜索；按实际 execution.json 与 case 绑定 hash 修正只读统计，没有补跑或丢弃执行记录。基线平局胜出，7 L 扰动显示候选更便宜，均如实保留。

本地反馈练习实际 11 次公共调用，三条 LOCAL_NOT_WEB 意见分别为范围反例、无依据建议、合法替代；所有负例与一次性 Final 拒绝留证。真实用户旧反馈单独核查，native import 未运行。当前新 case 的 405 份文件原样迁出临时目录到仓库外持久目录，逐文件 hash 不变；此为同一新工作区保管，不是伪造旧 case/index。迁移后 context-verify 实际 CURRENT，0 脚本启动；每次新 Git HEAD 后还须新导出 context。

第二原生只读审核独立 13 组核验通过，冻结一条非阻断 finding：原预审包未附 4 次内置重放 receipt。已向新的修订包补入既有凭据，删除会误导为 M14 当前反馈的本地 M09 示例；原包和 finding 保持，补证独立复核中。主编排器仅发布脱敏视图，原始运行/会话材料留本地。

补证复核完成：另一原生只读审核 10 项通过，F001 为 CLOSED_BY_ADDED_EXISTING_OFFLINE_EVIDENCE。原 findings/report hash 未变，没有新模型/checker/Final 启动。冻结当前内容作为一次完整 CI 的待验 subject。

完整 CI 第一次（subject 6b505c44b1d160372b9c6ca696bce4fa838043b1）实际 pytest 2380 passed / 1 skipped，随后 check_modular_workbench 拒绝，整体 exit 2。根因是历史资格集合比运行 identity 更广：还冻结 README、docs/INDEX、tests/ 与 scripts/ 等路径集合。本轮仅预先核了运行 identity 与 1989 项旧文件，未识别新增 tests 路径和两处导航的额外资格约束；失败不能报为完整 CI 通过。原日志/receipt 改存 full-ci-attempt1，未丢失。

有界修正：仅撤回主代理本轮新增的 README/INDEX 两条导航，逐字节恢复起点；新增测试原逻辑移到独立 operator kit 的 tests 子目录，显式独立执行，保留全部 11 个正负例；新增不在冻结集合内的 OPERATOR_START_HERE.md 作为明确入口。未改 hash 函数、覆盖范围、旧测试/期望、历史资格/决定/receipt 或核心。资料测试与原完整 CI 此后分开计数。先核新 subject 的两个完整 map 都等于旧资格，再进行必要的第二次完整 CI；不重跑原创模型/Final。

第二完整 CI subject bb29f03fb8eb4edc5513b1b9e8515089feb51b13，exit 0，2369 passed / 1 skipped，496.113 s。新资料 11 测试独立执行，默认旧测试集合不变。之后只做说明性 metadata/回执收口、相应定向验证、普通推送和最终 HEAD 新 context/三包；不再次运行模型或 Final。

最终说明性回执更新后，资料11测试、strict validator、render_status --check、git diff --check 均实际 exit 0，见 commands/closure_checks.json（明确父subject＋未提交metadata及实际manifest hash）。原生scope审核11项通过，未运行包内程序。最终包位于仓库外持久交付目录；最后提交后核context、逐包与原生已审包比较差异、push及远端回执不再递归提交自身hash。

暂存检查发现原生审核导出的 diff 有合法的单空格 context 行，作为新文本文件被 git diff --check 当尾空格拒绝。原始 scratch diff 保留字节/hash；公开视图改为 UTF8 JSON 字符串封装，完整保留空白，view_manifest 明示包装变换，未修改审核意见或源代码。随后重新检查暂存差异。
