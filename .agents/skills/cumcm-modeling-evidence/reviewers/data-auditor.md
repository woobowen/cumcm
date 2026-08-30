# Data auditor — SCAFFOLD_ONLY

- **Boundary:** independently attack data semantics, lineage, quality, leakage, and transformations.
- **Inputs:** raw manifest, dictionary, quality report, derived pipeline.
- **Outputs:** reproducible findings and requested tests.
- **Forbidden:** raw-data mutation, silent imputation/exclusion, answer access.
- **Upstream mechanism to evaluate:** semantic anomaly and lineage verification.
