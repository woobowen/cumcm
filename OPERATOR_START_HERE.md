# GPT 研究协调＋Codex 逐模块操作入口

本轮 operator kit 1.0.0 的入口是 [START_HERE](docs/gpt_codex_workflow/START_HERE.md)，完整过程见 [中文操作手册](docs/gpt_codex_workflow/OPERATOR_PLAYBOOK.md)，实际演练、审核及 CI 见 [本轮证据索引](evals/results/gpt-codex-readiness-001/EVIDENCE_INDEX.md)。先用 NO_CASE 包启动新大脑，按一个模块发出请求；示例 READY 不代表新题已完成。

本入口和操作资料独立于冻结的 RC10 核心及历史资格集合。原 README、docs/INDEX 和 tests 树保持历史字节；操作资料的新增测试在 `docs/gpt_codex_workflow/tests/`，用现有 `.venv/bin/python -m pytest -q docs/gpt_codex_workflow/tests` 单独执行。历史完整 CI 仍使用原 `bash scripts/ci.sh`，不能把它的测试数自动加上本资料测试，也不能用资料就绪宣称科学泛化。
