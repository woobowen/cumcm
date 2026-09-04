# CLI

`cumcm_case.py` 是 Competition RC 的唯一集中式命令入口。它只使用 Python 标准库，默认离线，
并仅在显式指定的 case workspace 内读写。运行 `python cumcm_case.py --help` 查看命令。

退出码：`0` 成功，`2` 输入错误，`3` Gate 拒绝，`4` STALE，`5` 状态冲突，`6` I/O 错误。
