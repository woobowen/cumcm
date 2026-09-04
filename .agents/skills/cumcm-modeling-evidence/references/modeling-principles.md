# Modeling principles

跨阶段决策必须保留 requirement traceability、维度/语义一致性、显式且可挑战的假设、可复现 baseline、机制不同的候选、可测试 first-party 实现、预注册指标/seed/stop rule、不确定性与失败报告、以及 Claim 到 current Run 的精确证据链。

选择只依据冻结 validation rule；test 仅在选择后授权一次。失败 attempt 计入 reliability denominator，但不进入模型排名。形式化正确、代码运行、Run 完成、Run 验证、Claim 验证与 handoff 就绪是不同事实，不能互相替代。

RC1 提供通用流程与确定性 Gate，不提供“已批准方法目录”。方法适配必须由当前题目、数据和证据证明。完整 sealed Stage 1、Stage 2 effectiveness、消融、外部效度、生产适用性与成本仍未验证。
