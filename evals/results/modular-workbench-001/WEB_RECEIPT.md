# 可回传网页的验收回执

本轮按已确认的 BUILD_AND_ACCEPT 授权，接续 woobowen/cumcm 的 Draft PR #12。起点为604c7fac，最终受测提交为d1f8532d498307e3b4755c088ce6a0fadfb432bb。工程终态为MODULAR_WORKBENCH_ENGINEERING_ACCEPTED；正式Skill版本为0.2.0-competition-rc10，工具仓库版本为0.3.0-competition-rc10。该结论只覆盖本次模块工作台工程路径与有界演练，不代表陌生赛题泛化、整题科学通过或队员合规验收。全部证据见[已推送提交的证据索引](https://github.com/woobowen/cumcm/blob/4352efe054d0097d39572bb8d4b06247a015b049/evals/results/modular-workbench-001/EVIDENCE_INDEX.md)，PR仍为[OPEN/DRAFT](https://github.com/woobowen/cumcm/pull/12)。

R7-001已先复现：旧实现因缺省scenario与捕获身份不一致，在selection前后阻断Final。修复位于共享内核的resolve_scenario_identity，并由prepare、execute、selection、controller和Final复核共同调用。身份绑定实际输入字节、输入角色、需求、假设、实验条件、指标及时间/划分语义。合法缺省和等价显式值都走完整公共交接路径；错误显式值、输入变化和范围冲突拒绝或STALE。没有用任意hash填None、跳过显式值或从未来Final倒填身份。HF22、来源与语义绑定、非预测Final无环和旧终局保护继续有效。

保留一个正式Skill、一个共享内核和原controller，新增薄工作台CLI与十四张模块卡。M01题目接收、M02需求、M03研究、M04假设公式、M05数据、M06候选、M07基线、M08实验设计、M09执行、M10选择、M11稳健性、M12最终核验、M13结论、M14交接均有实际任务请求、分析/产物、完成记录、审查包和恢复证据。内部状态并非十四个PASS：M04仍为SOURCES_PLANNED，M07仍为MODELS_PROPOSED，M09–M11为RUNNING，M12为FINAL_CANDIDATE，M14才到READY_FOR_PAPER_HANDOFF。三个原创案例共42次模块恢复均未改变正式状态、未自动启动下一模块。prepare只准备任务，不能冒充研究完成。

实际数值演练覆盖预测、非预测优化与至少三主问的混合案例，每类均经过两个候选、独立checker和一次Final到达相应范围交接。原创备水案例采用真实线性拟合、整数采购求解和逐分钟库存守恒；候选用3L与5L各一份满足8L需求，成本11元，基线12元。另一份不导入producer/checker的Python程序使用有理数和独立枚举，分别复算37、32、36个数值，最大残差约1.52×10⁻¹³。未来信息、不可行解、实际超时、缺主问、提前/重复Final、缺checker、错范围、writer冲突、局部STALE与中断恢复均有真实负例；部分可用不等于全题完成。

已知任务选用本机合法2016C附件，新建仅Q3的MODULE_USABILITY_DEVELOPMENT子案例。第二revision实际运行subject为df430c0，发生2次模型启动、3次checker启动和1次Final，公共路径到达技术交接。其346个相关运行文件与最终候选逐字节一致；Run仍保留实际旧subject，没有改标。六个相关历史截断点的剩余时间MRE约5.1966%，状态3条件外推约193.4418分钟；真实未来终点未知，不能写成真实未来预测正确或精度提升。Q1/Q2不在本次范围。两次允许revision均已封存，Final额度不退款。R1所引用的本地主Agent未发布提交因隐私修正被替换，原对象与观察保留为开发证据；最终资格只采用可交付的R2证据。旧Validation0/2、旧Development0/2和RC9拒绝均未改写，新独立Validation为0。

十四阶段都实际导出本地小包，约17–134KB，包含中文概述、原要求、阶段已有的公式/数据/代码、负结果、实际核验、审核问题及manifest；M09没有未来Final附件。实际回传演练使用明确注入的“2+3+5=11”草稿错误，独立程序复现正确值10后记CONFIRMED；无依据意见记NEEDS_EVIDENCE，替代设计另列ALTERNATIVE_DESIGN，旧包反馈标STALE。错case/hash、凭据canary、越界路径、注入、畸形/过长/重复JSON和ZIP反馈被拒绝。导入只登记finding，不执行脚本，不写正式PASS，不改模式或预算。反馈演练来自本地构建，未发生真实网页审核。

原生受限上下文worker实际只接收指定交接材料和M04小任务，曾识别旧上下文STALE；在新revision核对后给出42个符号、7个公式及独立算术。主Agent安装提案并通过公共入口完成M04，M05未启动。这是实际原生协作，隔离依赖约定与文件范围，不宣称OS隔离或严格盲审。另有原生只读协议审核、独立Python复算、主Agent自检及冻结机器决定后的Decision Auditor，角色与证据分开，技术门禁不由多数票决定。

最终定向测试361 passed，完整CI为2369 passed / 1 skipped / 0 failed，strict检查0 errors/0 warnings。首次CI在修审查附件前中断，当时11 failed/1584 passed；失败和诊断保留，未算作成功。修正的新阶段路由仍校验历史Git字节，不重写冻结矩阵。实际平台是既有WSL2/Linux和Python3.11.14环境；Windows原生未测试。本轮无新增系统包、语言包、工具链或全局配置。没有访问2025保留题、benchmark-vault或答案，没有打开2026题、做新盲测、付费API调用、基础模型训练或成品论文。

后续使用从START_HERE进入，默认GUIDED_SINGLE_MODULE：用户指定case/module/requirement，Codex在该范围实际工作，导出审查包后停止。实际case与工具仓库分离，显式代码冻结使用真实无remote本地Git，不自动发布赛题材料。新大脑负责当前协调，旧对话保留历史咨询；没有实际上传文件不能声称已读，同项目记忆不等于版本同步。已提供BRAIN_START/BRAIN_RESUME、WEB_REVIEW/WEB_ALTERNATIVE、CODEX_MODULE_REQUEST/CODEX_REVIEW_FOLLOWUP及论文组提示词。论文文字、数据图、模型示意图、表格、排版与提交分开接口，本轮只交技术底稿。真实网页、三位队员和TEAM_COMPLIANCE_REVIEW均为NOT_RUN；请网页基于实际回执整理通俗操作手册，不自动再次启动研发或下一赛题模块。

使用者还应区分五种身份：实际受测代码、已知运行提交、正式工程资格、当前模块修订和远端交付提交。它们有显式hash关系，不要求强行写成同一个值。审核视图可以脱敏，原始文件hash与视图hash分别保存；公开精确记录可离线重放工程裁决，重算已知题则仍需合法原附件，不能从摘要虚构原始数据。

正常开发采用用户明确设置的有界预算，不机械继承旧评测每题四请求或远端预推送配置。未知输入、缺前置和缺预算不得猜测补齐；失败保留，已消费Final不因恢复或切模式重置。早期研究与假设接受只表示材料符合该模块职责，负结果和未验证的科学疑问继续保留，不能把它们换算成全题科学通过。
