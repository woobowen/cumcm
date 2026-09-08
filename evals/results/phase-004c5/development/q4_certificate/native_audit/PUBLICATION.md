# 原生审核产物的公开表示

audit.json和REPORT.md逐字节保留。publication.json逐项映射原件hash、公开hash和路径。
四份实际执行过的ignored审核脚本无损保存为`.py.source.json`：读取source字符串并以
UTF-8编码即可恢复原字节，包括结尾空行；必须匹配original_sha256。执行argv和原manifest
保留历史原路径，这些记录不是新共享实现或自动执行入口。
五份含私人cwd的回执只作明确标注的路径替换，原始回执在ignored路径保留。

最初将临时审核脚本误作为仓库Python模块发布，ruff报113项历史脚本样式问题；
继而原字节文本归档遇到四项EOF空行检查。这些观察保留在publication.json。
采用无损JSON源码表示后，不改写已执行脚本的任何字节，也不更改或跳过仓库检查。
正式proof code仍在../code/接受原有检查。解码后源码已作hash及语法检查，不等于重新执行。
复现须遵守原输入/预算边界，不能将审核重放当作新模型Run。
