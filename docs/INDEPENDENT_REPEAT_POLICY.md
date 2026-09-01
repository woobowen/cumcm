# Independent repeat policy

An independent repeat is a distinct fresh Codex session for a frozen `case × anonymous arm ×
repeat_id` cell. Resume, parser recovery, duplicated output, cross-model evidence and multiple
attempts for the same `repeat_id` do not create additional repeat depth.

A fresh A02/A03 retry may fill a previously missing cell only if it independently passes Schema,
completion, oracle-executed, process, input/cohort and hard Gates. It never overwrites A01. Repeat
depth counts unique eligible `repeat_id` values per balanced case/arm, then takes the minimum across
balanced cells. Phase 002D achieved depth one among its three balanced cases; the runner's stricter
all-scheduled-case depth is zero because CASE-006 has no complete repeat. Neither reaches the frozen
minimum two.
