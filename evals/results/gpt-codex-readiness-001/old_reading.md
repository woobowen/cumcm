# 旧原创示例的中文阅读附页

**DERIVED_READING_VIEW / 1.0.0**。仅针对ORIGINAL-WATER-MIXED / M14 / revision1的冻结上传快照，不改旧M14、statement、数值或Final。原package_hash：`09784e197709c5c5657d5eedac9959c7a72312e0ea30631a7bbeeb46afe05c71`。这是阅读接口修订，不是新的科学结果或撤销RC10资格。

两项真实网页意见均由原文核查确认：精简符号表缺独立含义；逐问statement是占位文字。分析正文和其他字段已有部分信息，本附页不声称原包没有证据。原root不可追加，原生导入未执行；记录NATIVE_IMPORT_NOT_RUN_IMMUTABLE_SOURCE。

## 符号和两种时间坐标

| 符号 | 含义 | 单位/范围 | 原证据定位 |
|---|---|---|---|
| t0（附页规范化名） | 预测起点，B组112 | min，绝对时间 | analysis.md的当前起点；原采购公式中的t |
| T | 达到阈值10 L的条件终点 | min，绝对时间；模型内估计 | 原公式T-t；analysis.md |
| t（观测） | 轨迹采样的绝对时刻 | min，各entity时间轴 | input.observations.observed_at |
| tau（附页规范化名） | 开始消耗备水后经过时间 | min，0..8的相对时间 | 原库存公式s(t)，以此消除t歧义 |
| flow或q | 备水库存消耗流率 | 1 L/min；不是液位拟合斜率 | input.flow_litres_per_minute；analysis.md |
| b | 液位随观测时间下降的斜率 | -0.1 L/min，本严格仿射输入 | analysis.md；input.observations |
| d | 向上取整后的条件备水需求 | L；ceil((T-t0)q) | 原采购公式与allocation.demand_litres |
| n3、n5 | 两种容器的数量 | 非负整数，分别3L和5L每箱 | allocation.counts；input.containers |
| s(tau) | 备水库存量 | L，s(0)-q*tau | allocation.balance_litres；原s(t)公式 |
| cost | 采购成本 | 元；4n3+7n5 | allocation.cost |

规范化t0/tau是附页解释，不回写旧公式。所称T=120来自条件外推，输入没有B未来真值。

## 逐问事实

### REQ-A / CLAIM-REQ-A

在严格仿射条件估计的8 L备水需求、正价格/整箱/无限供应模型内，采购一只3 L和一只5 L容器，成本11元；独立有限枚举支持该整数模型内最优，不证明现实效果。

原statement：`Bounded result for REQ-A.`；定位`claim_evidence.CLAIM-REQ-A`。Run：`RUN-CAND-20260906`；metric：`metric_a`；数值字段：`allocation.cost; allocation.counts`。

输出原路径`runs/RUN-CAND-20260906/output.json`，source_sha256 `cb6516994e10587418191cf42e80ce5ea597c3c52bda07fc9ab3873b4aa59dd7`；上传视图`views/017-output.json.txt`，view_sha256 `cb6516994e10587418191cf42e80ce5ea597c3c52bda07fc9ab3873b4aa59dd7`。两种hash不混用。

### REQ-B / CLAIM-REQ-B

在B组112 min以前的严格仿射合成轨迹持续条件下，到10 L阈值的剩余时间估计为8 min（条件终点120 min）；历史A组两个起点算术误差近零，不证明B的真实未来精度或一般噪声预测效果。

原statement：`Bounded result for REQ-B.`；定位`claim_evidence.CLAIM-REQ-B`。Run：`RUN-BASE-20260906`；metric：`metric_b`；数值字段：`scientific_evidence.REQ-B.prediction_evidence.predictions[0].value; validation_metrics.metric_b`。

输出原路径`runs/RUN-BASE-20260906/output.json`，source_sha256 `4635f933cf35ff7001770547e31b4b09c697ce1be607e57a793c7a638f31b202`；上传视图`views/012-output.json.txt`，view_sha256 `4635f933cf35ff7001770547e31b4b09c697ce1be607e57a793c7a638f31b202`。两种hash不混用。

### REQ-C / CLAIM-REQ-C

以选中采购方案的8 L库存、1 L/min固定消耗、无泄漏为条件，相对分钟0..8的库存为8,7,6,5,4,3,2,1,0 L，终点0 L且逐点守恒；未核验真实供应或损耗。

原statement：`Bounded result for REQ-C.`；定位`claim_evidence.CLAIM-REQ-C`。Run：`RUN-CAND-20260906`；metric：`metric_c`；数值字段：`allocation.balance_litres; validation_metrics.metric_c`。

输出原路径`runs/RUN-CAND-20260906/output.json`，source_sha256 `cb6516994e10587418191cf42e80ce5ea597c3c52bda07fc9ab3873b4aa59dd7`；上传视图`views/017-output.json.txt`，view_sha256 `cb6516994e10587418191cf42e80ce5ea597c3c52bda07fc9ab3873b4aa59dd7`。两种hash不混用。

## 实际核查范围

本机重跑已审计的网页自写标准库算术脚本，9/9与随附结果一致；未执行上传producer/checker，未重放旧Run/Gate/Final/全量CI。只有hash引用但没有源字节的部分不能称完整复现。原生独立checker和Final是包中历史记录，不是本次重执行。新网页反馈为本次实际收到的外部事件；用户人工验收仍未发生。完整字段映射见同目录old_reading_bindings.json。
