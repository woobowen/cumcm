<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2A-C1 historical compatibility

- Result: `PASS`
- Input freeze: `PHASE-002D-R2A-C1-INPUT-FREEZE-001` / `db2e56eb21b22e65db3ede08b0b68f23f60ed3ba7d4d5148647fda509a518132`
- Verification modes: `CURRENT_TREE_IMMUTABLE, DERIVED_OBSERVATION, LIVE_SEMANTIC_POINTER, SUBJECT_COMMIT_BLOB`
- R1 subject commit: `d59f4b8a36fa3c15e06ec0aceb948cd2bafd2abc`
- Immutable roots: `8`
- Live pointer: `rules/workflow_rules.yaml`
- Allowed live field: `git_delivery.preferred_task_branch`
- Rejected live fields: `git_delivery.remote_name, git_delivery.repository, git_delivery.remote_url, git_delivery.protected_base_branch, git_delivery.allow_force_push, git_delivery.allow_agent_merge, ALL_UNREGISTERED_FIELDS`
- Fixed historical failures: `20`
- Verifier file SHA-256: `4d4bd482a28786c84db8aab616f41332f7009ecd0de3a4e43e6eb0cf20b3df6a`
- Record hash: `e95a81fa08a4b2e2c496b9aee95cdb5eb4ac49eebd94de8d8e5ca9554aa85037`

Historical decisions and result trees were read at their recorded subject commits. Current-tree
immutability, derived observations, and live semantic pointers use separate fail-closed modes; no
missing Git object falls back to the worktree and no whole-file ignore is permitted.
