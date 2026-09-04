# Phase 004 Development Eval Handoff

## Ready input

- Formal Skill：`cumcm-modeling-evidence` `0.2.0-competition-rc1`
- Capability：`COMPETITION_RC`
- Architecture：`ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`
- Assurance：public deterministic eight-Gate acceptance、两个项目原创 E2E、30 个 fail-closed 反例、完整 CI（以最终 acceptance 为准）
- Registry：`benchmarks/case_registry.yaml`，当前不预登记任何历史题

## Exact next task

选择一道答案仍为 `SEALED` 的历史 `DEVELOPMENT` 题，记录 problem/data hashes 与冻结 Skill commit，使用 RC1 从 intake 到 handoff 完整盲跑；在读取任何答案前冻结 first run。随后只把跨题可复现的失败纳入 RC2，把题目特异发现隔离。

## Non-authorization

本 handoff 不授权读取历史答案、污染 Validation/Held-out、执行第三方代码、启动 Stage 2 模型比较或宣称 RC1 已有外部效度/生产适用性。答案访问一旦发生必须记录；Validation/Held-out case 永久降为 Development。
