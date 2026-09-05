# Case templates

这些 JSON 是字段约定示例；`cumcm_case.py init` 会在 case workspace 创建对应 DRAFT。
填充后必须用 CLI 的确定性 Gate 接受，不能通过把 `status` 手工改为 `ACCEPTED` 推进状态。

RC6 的 `data_sufficiency.json`、`requirement_selection.json` 和
`semantic_claim_support.json` 是 14 阶段内的辅助 contract artifacts，不是新增阶段或第二状态
真源。它们分别由 `data-sufficiency`、`selection-check`、`semantic-check` 校验并 hash-bind。
