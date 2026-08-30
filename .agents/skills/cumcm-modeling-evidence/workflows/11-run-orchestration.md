# Run orchestration — SCAFFOLD_ONLY

- **Boundary:** execute only approved first-party experiments with complete run provenance.
- **Inputs:** experiment manifest, verified code, immutable inputs.
- **Outputs:** Run IDs, commands, hashes, environment, logs, metrics, outputs.
- **Forbidden:** unregistered runs as evidence, overwriting outputs, candidate-code execution.
- **Upstream mechanism to evaluate:** checkpoint/restart, ledgers, deterministic environment capture.
