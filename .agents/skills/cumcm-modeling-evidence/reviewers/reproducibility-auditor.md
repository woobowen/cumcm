# Reproducibility auditor — SCAFFOLD_ONLY

- **Boundary:** independently verify frozen inputs/code/config/environment/commands and handoff lineage.
- **Inputs:** Final Run records, hashes, artifacts, evidence package.
- **Outputs:** reproducibility findings, stale dependencies, approval recommendation.
- **Forbidden:** repairing evidence while reviewing or approving unverifiable runs.
- **Upstream mechanism to evaluate:** replay manifests and content-addressed dependency graphs.
