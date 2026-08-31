# Human Gate — Base Selection

Gate: `GATE_BASE_SELECTION_PENDING`

## Recommended方案

`RECOMMEND_CLEAN_ROOM_ARCHITECTURE`: keep the native architecture and consider only these four
clean-room mechanisms: `accepted-versus-done-workflow-state`, `claim-evidence-support-gate`, `hash-bound-reproducibility-manifest`, `leakage-safe-model-comparison-gate`.

## 备选方案

Retain NO_PROJECT_MODELING_SKILL as the neutral starting point and keep the single formal Skill SCAFFOLD_ONLY until human-approved clean-room mechanisms pass fresh tests.

## 支持与反对证据

支持：18/18 cells have frozen scores; no hard failure occurred; four repeated gaps have observable
tests. 反对：only six synthetic cases were used, five cells are recovery-affected, score medians
differ by at most 2.5 points, and sanitized packages cannot prove full repository behavior.

## 许可证、污染、安全和运行限制

- YUSHUI is `UNKNOWN_NO_LICENSE`; no direct copy or fork is legal-evidence-supported.
- HANDSOMEZR and every selected component source have external, corpus, per-Skill, or subresource gaps.
- Historical/demo/corpus content remains excluded; no candidate example may enter future validation.
- Network, MCP, installers, updaters, subprocess queues, broad tool declarations, and Git automation remain excluded.
- Real-run budget is exhausted at 20/20; Phase 002 evidence cannot be improved by another retry.
- Clean-room gates may not reduce current fail-closed security, evidence, state, or human-approval rules.

## Human must answer exactly

1. Approve or reject `RECOMMEND_CLEAN_ROOM_ARCHITECTURE` as the Phase 003 design direction; this is not approval of any upstream base.
2. Approve or reject retaining `NO_PROJECT_MODELING_SKILL` as the neutral fallback while the formal Skill remains `SCAFFOLD_ONLY`.
3. For each of the four cards, approve, reject, or defer clean-room specification work; no direct reuse option is offered.
4. Decide the project license and the minimum per-resource license evidence required before any future port/direct reuse.
5. Approve or reject the proposed frozen Phase 003 validation design and success thresholds before any implementation sees validation answers.
6. Decide whether recovery-affected cells may inform qualitative gap discovery but not comparative rank.
7. Confirm that Phase 003 must preserve one formal Skill, one authoritative state, no benchmark-answer access, and human approval for high-risk gates.

Until all required approvals are recorded, `base_selected=false`, `third_party_integrated=false`, and
`PHASE-SKILL-INTEGRATION-003` must not start.
