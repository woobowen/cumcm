# mathodology — provisional static review

1. **Identity:** `sweetcornna/mathodology`, `main@11cdfd7cca666c276b8de04d3a2fb76c418695c6`, tag v0.14.0, 2026-08-29.
2. **Claimed goal:** nine-role award workflow with structured handoffs/gates/judges.
3. **Skill structure:** eight Claude Skills, nine roles, workflows, AGENTS, linter/QA/updater and MCP config; skills-only branch.
4. **State/stages:** handoff/gate/scorecard/decision memo and run path constraints observed; not a complete runtime.
5. **Capabilities:** requirements for baseline/ablation/sensitivity/robustness; modeling execution absent in this branch.
6. **Evidence chain:** accepted/rejected sources and stable issue IDs; no input/output/Git/Source-ID chain.
7. **Multi-Agent:** independent critic is valuable; three-judge award scores are subjective and cannot be evidence.
8. **Deterministic scripts:** role-specific linter and selftest/QA tools; remote updater excluded.
9. **Tests/CI:** selftest modes only; no conventional CI observed.
10. **License:** root MIT; external floating search MCP license/dependencies UNKNOWN.
11. **Third-party resources:** search package is dynamically fetched and not in the pinned tree.
12. **Network/services:** `uvx free-search-mcp`, GitHub updater, npx installer.
13. **Danger:** remote code execution, global config/Skill mutation, recursive uninstall. Risk `BLOCKER` for whole package.
14. **Conflict:** subjective score gates, weaker human approval, parallel run contracts, updater/MCP.
15. **Dynamic-test candidates:** handoff/gate/memo linter and artifact containment after clean-room redesign.
16. **Do not adopt:** judge thresholds, updater, MCP, installer, download/global paths.
17. **Unknown:** external MCP license/behavior, selftest status, score calibration.
18. **Reuse:** `EVALUATE`; structure only, never scores as mathematical/experimental proof.
