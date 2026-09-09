# GPT 研究协调＋Codex 逐模块执行

操作资料版本 **1.0.0**，适用已核验 RC10。先用无题包启动 GPT；有题后，一次向 Codex 指定一个模块。GPT负责解释题意、比较方案、发现证据缺口、组织研究与争议。Codex读取实际文件、独立判断、实算与内检。正式事实在本地，网页意见不能改 Gate。

1. 新对话上传 `BRAIN_START_NO_CASE_1.0.0.zip`，发送包内 [BRAIN_START](BRAIN_START.md) 正文。预期回答 `NO_ACTIVE_CASE`；这一步没有解题或运行许可。
2. 收到你合法提供的题目和数据后，让 GPT 整理 M01 请求；复制 [十四模块请求](CODEX_MODULE_REQUESTS.md) 中相应整段给 Codex，只填 case位置、范围、目标和限制。
3. Codex 返回当前模块摘要、实际产物、检查和审查包并停止。先看做了什么、结论条件、缺口，再决定下一模块或审核。
4. 上传该模块包，按 [五类复核](WEB_REVIEW_PROMPTS.md) 选一类。没有 finding 保存单独摘要；有 finding 交回 [反馈处理](CODEX_REVIEW_FOLLOWUP.md)。下一模块需新的明确请求。
5. 中断/换对话用 [BRAIN_RESUME](BRAIN_RESUME.md)，先让 Codex从当前case重新导出context。

详细步骤：[操作手册](OPERATOR_PLAYBOOK.md) · [提示词索引](PROMPT_INDEX.md) · [经验卡](EXPERIENCE_CARDS.md) · [论文事实接口](PAPER_FACT_HANDOFF.md) · [限制](KNOWN_LIMITATIONS.md)。

三个包用途独立：NO_CASE 没有活动题；EXAMPLE_ONLY 是不可重跑的旧原创教学样例；WEB_REHEARSAL_NEXT 是本轮新原创结果，等待下一次真实网页审查。不要把示例 READY 当新题状态。
