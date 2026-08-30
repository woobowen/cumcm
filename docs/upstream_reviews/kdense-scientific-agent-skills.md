# kdense-scientific-agent-skills — provisional static review

1. **Identity:** `K-Dense-AI/scientific-agent-skills`, `main@f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f`, tag v2.65.0, 2026-08-29.
2. **Claimed goal:** 163 modular scientific Skills; broad orchestration is explicitly out of scope.
3. **Skill structure:** large Skill pool, per-Skill scripts/tests, plugin, AGENTS, security reports/workflows.
4. **State/stages:** no unified research Run/Source/Claim lifecycle; component-local contracts only.
5. **Capabilities:** EDA, hypothesis generation, DOE, statistics, uncertainty and peer review are OBSERVED as detailed files/tests.
6. **Evidence chain:** competing explanations, discriminating predictions, falsification and evidence matrices; lacks project identifiers/hashes.
7. **Multi-Agent:** no independent orchestrator/reviewer mechanism observed.
8. **Deterministic scripts:** strongest is fail-closed local EDA with path/type/resource protections and negative tests.
9. **Tests/CI:** extensive per-Skill tests/workflows exist; full isolated sweep is explicitly not run; pinned status UNVERIFIED.
10. **License:** root/plugin MIT, but README says per-Skill licenses may differ while metadata coverage is incomplete; vendored subtrees need review.
11. **Third-party resources:** floating dependencies and a Git dev dependency lack a lock/complete notice ledger.
12. **Network/services:** many optional API/cloud/database Skills; selected local subset is designed no-network, scientific-critical-thinking can use OpenRouter.
13. **Danger:** broad Bash/Write and install instructions, unpinned dependencies; self-report has 988 findings (34 Critical/9 High) with incomplete current triage. Risk `HIGH`.
14. **Conflict:** installing 163 Skills causes routing/dependency/license competition and no CUMCM state chain.
15. **Dynamic-test candidates:** EDA safety, hypothesis rival/falsification, DOE/statistics, uncertainty/units, peer-review contract patterns.
16. **Do not adopt:** entire pool, tool declarations/install commands, network Skills, unreviewed vendor tools.
17. **Unknown:** scientific correctness, current test results, per-Skill licenses, independent security triage.
18. **Reuse:** `EVALUATE`; selected concepts mapped into native contracts only.
