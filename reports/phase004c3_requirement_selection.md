# Phase 004C3 requirement selection

`requirement-selection/v1` supports `GLOBAL_JOINT`, `PER_REQUIREMENT` and `JOINT_PORTFOLIO`.
Requirement records bind their own metric/direction and selected Run/output. Global selection must
materially cover every primary requirement; portfolio selection additionally requires compatible
input/scenario hashes and non-conflicting cross-requirement constraints.

A baseline remains comparator evidence only. It cannot support a policy Claim if the bound Run did
not execute that policy or has zero exposure. Invalid, failed, stale, superseded or unsealed Runs
are not eligible.
