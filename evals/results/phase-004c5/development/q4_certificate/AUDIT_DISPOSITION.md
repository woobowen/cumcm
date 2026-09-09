# Q4 原生审核处置与严格区间说明

本说明追加于原结果冻结之后。原 `REPORT.md`、证书、原执行回执及 v6 结果保持原字节。
原报告所说“不是原生多Agent审查”描述当时的程序复算；此后另有真实原生审核，
见 [native_audit/REPORT.md](native_audit/REPORT.md) 和原始 `audit.json`。

主编排器接受 Q4-NATIVE-001–004、006 的限定结论，并处置 Q4-NATIVE-005：原报告
显示的小数端点是近似值，不能直接作为严格包围区间。后续严格引用使用
**[40246.40307264614, 40246.40311289260] m³/周**；权威精确界仍是
`verification.json` 的 `lower_bound_exact` 与 `upper_bound_exact` 分数字符串。
主编排器另以 Fraction 比较确认下端点≤精确 L≤精确 U≤上端点，记录见
`display_interval_verification.json`。这只是已有证明的展示校验，没有调用模型或构造器。

原生 reviewer 在只读受测文件的范围内独立核对全部 3216 条对偶不等式、410 个
容量约束、3626 个剩余量、1214 项原始参数，并执行 24 个合成探针（4 接受、20 拒绝）。
它还重放一次无求解器 verifier，产物字节一致。22 个绑定文件前后 hash 一致。
审查只支持固定序列化十进制参数的 Q4 第一目标静态运输 LP；不证明后续词典序
成本/损耗最优、初始库存、实际企业未来产能、全题完成或正式 Gate 通过。

原审核 JSON 的 canonical output hash 为
`80a44ee4eb83d6b314bcc8c57451ff0dd04cf88eb9a21994dae8f9a37d04a049`。
它没有独立观察历史 Git/远端事件，也未读取题目正文；这两项不计入其保证范围。
审核原件保存在 ignored 路径；公开副本只有五份含私人 cwd 的回执作标明的路径替换，
四份审核脚本另以无损JSON源码保存，解码后的字节及hash与原件一致，其余文件逐字节复制。
原始和公开 hash、转换方式见 `native_audit/publication.json`。
原 manifest 中的 hash 描述原件，不能用它误判已明确标注的派生回执。

审查过程中两条最初的启动检查未保存完整 stdout 文件，完整输出仍在会话工具记录；
所有实际数值审查、verifier 和合成探针均保存命令、起止时间、退出码、stdout/stderr
及 hash。原生报告中的这一限制保持可见，不能表述为所有工具输出现已完全离线归档。
