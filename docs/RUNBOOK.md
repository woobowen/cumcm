# Runbook

## Initialize and validate

1. From repository root run `bash scripts/bootstrap_dev_env.sh`.
2. Start Codex in this trusted repository and ask it to list loaded instruction sources; expected root/layer behavior is documented in `integration/openai-codex-foundation-sources.md`.
3. Read `AGENTS.md`, `GOALS.md`, `WORKFLOW.md`, the active plan, and project state.
4. Run `bash scripts/ci.sh`; investigate stable error IDs before changing code.

## Plans and interruption recovery

Update the active plan with command evidence and remaining work after each milestone. On interruption, a new session reads the startup order, verifies `git status`, runs `render_status.py --check`, and resumes the first unchecked milestone rather than relying on chat history.

## Upstream static audit

Use `git ls-remote` before an isolated shallow clone under `.cache/upstream/<id>/`. Never run candidate files or install candidate dependencies. Capture commit, tree, licenses/notices, instruction/Skill paths, package/CI/test files, static risk-pattern context, hashes, and unknowns. Write only evidence summaries and paths into tracked files.

## Benchmark preparation

Create synthetic/development fixtures first. Keep validation and held-out manifests separate, freeze the Skill for blind runs, log searches/interventions, and keep answers only in excluded `benchmark-vault/`. Viewing an answer demotes the case.

## Release/freeze

Require all gates in `WORKFLOW.md`, a clean strict CI run, versioned contracts, exact input/output hashes, Git commit, environment/config/seed, reviewers, and human approval. Generate status/acceptance reports from state, then create local atomic commits. Do not push without separate authorization.

## CI provider

`scripts/ci.sh` is the sole CI truth. This repository has no remote, so no GitHub/GitLab wrapper is created. If a later remote matches GitHub or GitLab, add only a thin provider job that bootstraps the locked dev environment and calls this script without network upstream audits, private vaults, or real APIs.
