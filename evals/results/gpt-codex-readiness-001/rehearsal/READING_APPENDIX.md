# 新原创M14阅读交接

DERIVED_READING_VIEW / 1.0.0。READINESS-COOLANT-001 / revision1；本轮真实数值Run及独立Final已发生。仅支持合成仿射/正价整箱/固定流率模型，不证明真实未来精度。

源M14 hash：`45ba0bfe355af0da300c31c6d352234e9c145fd389c87607bd40d3116e6fa674`。完整符号见包内模型假设符号视图；绝对t0/T与库存相对tau区分，液位斜率与库存流率分别定义。

## REQ-A / CLAIM-REQ-A

正价整箱且无限供应：采购[2, 0]箱，成本8元，覆盖6 L。

Run `RUN-BASE-20260910`；指标 `metric_a`；字段 `allocation.cost / allocation.counts`；output sha256 `e5c74aa5e0557dfdfd7877f3ee93981bc60b9bb128c5e879da1845b3585d0f62`。Final统一账本sha256 `6baffca5f29c0503ba08e6d07db2a9abad4dafc7c58ba35ec2e74b6a242fa2c3`，count=1、test_access=0；该Final为独立科学核验，不是未来观测。

## REQ-B / CLAIM-REQ-B

仿射合成前缀持续时，剩余估计6 min；未来精度未验证。

Run `RUN-BASE-20260910`；指标 `metric_b`；字段 `scientific_evidence.REQ-B.prediction_evidence.predictions[0].value / validation_metrics.metric_b`；output sha256 `e5c74aa5e0557dfdfd7877f3ee93981bc60b9bb128c5e879da1845b3585d0f62`。Final统一账本sha256 `6baffca5f29c0503ba08e6d07db2a9abad4dafc7c58ba35ec2e74b6a242fa2c3`，count=1、test_access=0；该Final为独立科学核验，不是未来观测。

## REQ-C / CLAIM-REQ-C

1 L/min消耗且无泄漏，库存从6 L至0 L，逐点守恒。

Run `RUN-BASE-20260910`；指标 `metric_c`；字段 `allocation.balance_litres / validation_metrics.metric_c`；output sha256 `e5c74aa5e0557dfdfd7877f3ee93981bc60b9bb128c5e879da1845b3585d0f62`。Final统一账本sha256 `6baffca5f29c0503ba08e6d07db2a9abad4dafc7c58ba35ec2e74b6a242fa2c3`，count=1、test_access=0；该Final为独立科学核验，不是未来观测。

## 阅读限制

当前6L需求时两候选同为8元，冻结平局规则选择BASE；这不证明baseline在所有场景都最优。预定需求+1L时，BASE实际成本12元，CAND为11元；此扰动显示离散组合差异，不是置信区间。原始失败、无依据意见和反例均保留。预测历史两起点来自一个实体，未来B无标签；工程与算术不构成外部效度。新网页审查尚待用户上传，原生worker和本地接口演练不冒充网页。

论文文字、数据图、示意图、表格、排版分别按包内PAPER_FACT_HANDOFF读取；对本页提出包外意见仅写摘要，web-feedback/v1的位置必须取内层manifest.files。
