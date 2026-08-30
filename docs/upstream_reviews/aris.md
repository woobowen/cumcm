# aris — provisional static review

1. **Identity:** `wanshuiyin/Auto-claude-code-research-in-sleep`, `main@94d8093ed21d20a790830318190095b9f5036ce8`, 2026-08-26.
2. **Claimed goal:** 82-Skill ML research lifecycle with resumable runs, independent review, evidence checks and remote experiments.
3. **Skill structure:** Skills/overlays, tools/tests/MCPs/installers/templates/community paper; AGENT_GUIDE but no AGENTS.
4. **State/stages:** OBSERVED `.aris` run state distinguishes `done` from `accepted`; resume skips only accepted/skipped.
5. **Capabilities:** ML experiment planning/queue/audit, evidence/provenance/review; not general CUMCM modeling.
6. **Evidence chain:** mechanical existence check separated from semantic support and trace sidecars; path containment, Run/input/Git/Source/stale chain incomplete.
7. **Multi-Agent:** path-only blind review and cross-family reviewer separation are strong observed patterns; agent verdict cannot replace human gates.
8. **Deterministic scripts:** run state, provenance and evidence precheck are candidates for clean-room redesign, not direct execution.
9. **Tests/CI:** state/evidence tests and workflows exist; pinned status UNVERIFIED.
10. **License:** root MIT and some notices; adapted references/templates/binary paper need per-resource review.
11. **Third-party resources:** poster/proof notices exist, but IEEE templates/community under-review PDF and other adaptations remain NEEDS_REVIEW.
12. **Network/services:** LLM/research/Feishu/SSH/GPU/W&B/Modal/Vast/Overleaf and multiple MCPs.
13. **Danger:** `shell=True` queue, git push, force checkout/reset, global installers/updaters/config mutation. Risk `BLOCKER` for whole package.
14. **Conflict:** parallel `.aris`/wiki/CLAUDE truth, default AUTO_PROCEED, audit FAIL-continue, remote/Git behavior.
15. **Dynamic-test candidates:** done-vs-accepted, reviewer independence, existence-vs-support, integrity checklist, crash/resume/stale tests after rewrite.
16. **Do not adopt:** queue, installers/updaters, MCPs, Git/SSH paths, parallel state, whole Skill pool.
17. **Unknown:** test results, all subresource rights, binary paper content, service security.
18. **Reuse:** `EVALUATE`; abstract patterns only with human gate and native state/contracts.
