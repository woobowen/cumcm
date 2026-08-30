# Data audit — SCAFFOLD_ONLY

- **Boundary:** verify schema, semantics, quality, missingness, units, bias, and lineage.
- **Inputs:** immutable data, dictionary/source, requirements.
- **Outputs:** data-quality report, derived-cleaning plan, blockers.
- **Forbidden:** mutating raw data, hiding exclusions/imputation, inferring units silently.
- **Upstream mechanism to evaluate:** deterministic profiling and adversarial semantic checks.
