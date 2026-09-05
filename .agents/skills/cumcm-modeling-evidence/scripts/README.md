# CLI

`cumcm_case.py` 是 Competition RC 的唯一集中式命令入口。它只使用 Python 标准库，默认离线，
并仅在显式指定的 case workspace 内读写。运行 `python cumcm_case.py --help` 查看命令。

RC6 在昂贵建模前增加 `data-sufficiency`，在 Final 前增加 `selection-check`，并在 handoff 前
增加 `semantic-check`。三者均为纯、确定性、fail-closed contract Gate；不执行自然语言推理。

退出码：`0` 成功，`2` 输入错误，`3` Gate 拒绝，`4` STALE，`5` 状态冲突，`6` I/O 错误。

真实 case 代码必须先以 `CASE_ROOT` record 写入 accepted experiment plan，并与真实 Git blob
逐字节一致。`execute` 生成 `execution_capture.json`、stdout/stderr 和 output；全部候选运行完成并
形成选择决策 hash 后，`seal-run` 才生成不可覆盖的 manifest。两步都要求 case state 为 `RUNNING`。
