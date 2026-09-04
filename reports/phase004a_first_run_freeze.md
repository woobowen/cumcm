# Phase 004A First-Run Freeze

- Freeze ID: `CUMCM-2023-C-DEVELOPMENT-001-FIRST-RUN-FREEZE-001`.
- Artifact: `evals/results/phase-004a/CUMCM-2023-C-DEVELOPMENT-001/first_run/first_run_freeze.json`.
- Artifact SHA-256: `9f27706b099b187c5c6c82984fcf3e760d7cbcc6640525bbf7841014929a2fb3`.
- Subject/worktree commit: `1cd1402521d2c4cf487c01e045a6ab1b20b6e130`.
- Independent freeze commit: `8e7b7ced55789232bb5d6f8ec64e1ac4926778f8`.
- Verified remote branch SHA before unlock: exactly `8e7b7ced55789232bb5d6f8ec64e1ac4926778f8`.
- Freeze time: `2026-09-04T06:16:39Z`; answer state: `SEALED`.
- Case state: `MODELS_PROPOSED`; manifest/result/handoff hash registries are empty by construction.

The freeze binds the official problem/data hashes, RC1 version/tree/commit, search log, accepted
artifacts, failure/timing records and case state. The freeze checker passed with a blocked zero-Run
case, preserving the actual failure instead of inventing later-stage artifacts. No first-run file was
modified after unlock.
