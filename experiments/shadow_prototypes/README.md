# Phase 002D-R3 shadow prototypes

This tree contains the three frozen experimental arms only: the format-only S0
baseline adapter, the W1 workflow-only guards, and the K1 deterministic evidence
kernel.  It is removable as one unit and is not imported by the formal
`cumcm-modeling-evidence` Skill.

All arms use the common immutable interface.  They return reason-coded shadow
results and proposals only; they cannot write `state/project_state.json`, create a
second state truth, emit formal `FINAL`, or access the sealed benchmark vault.

The implementations are project-owned clean-room code.  No upstream executable,
prompt, schema, or dependency is copied or executed here.
