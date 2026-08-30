# Final Run freeze — SCAFFOLD_ONLY

- **Boundary:** freeze exact approved runs and invalidate superseded downstream artifacts.
- **Inputs:** validated robust runs, reviews, human approval.
- **Outputs:** freeze manifest, hashes, supersession/staleness records.
- **Forbidden:** relabeling exploratory results, mutable outputs, post-freeze silent reruns.
- **Upstream mechanism to evaluate:** content-addressed artifacts and approval-aware freeze gates.
