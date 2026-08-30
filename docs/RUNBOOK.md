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

Require all gates in `WORKFLOW.md`, a clean strict CI run, versioned contracts, exact input/output hashes, Git commit, environment/config/seed, reviewers, and human approval. Generate status/acceptance reports from state, then create atomic commits and follow the remote-delivery procedure below.

## Remote delivery procedure

1. Read the remote name, URL, protected branch, and preferred task branch only from `git_delivery` in `rules/workflow_rules.yaml`.
2. Record `git status --short --branch`, `git branch --show-current`, `git remote -v`, and `git log --oneline --decorate -10`. If `origin` is absent, add the configured URL. If it differs, stop with `REMOTE_MISMATCH_BLOCKER`; never overwrite it automatically.
3. Run `git ls-remote --heads origin`. An empty result with exit code zero means the remote has no branches; it does not imply a network failure.
4. Inspect `git status --short`, `git diff --check`, and `git diff --stat`. Stage only named files for one purpose, then inspect `git diff --cached --check`, `git diff --cached --stat`, and `git diff --cached` before committing. Run relevant tests and inspect `git show --stat --oneline HEAD` afterward.
5. Run every command in the active plan's full validation list. Confirm no secret, answer, candidate clone, `.venv`, `.cache`, private path, or unrelated user file is tracked.
6. For an empty remote while on a task branch, use `git push -u origin HEAD`; do not fabricate `main`. When `origin/main` exists, fetch with `git fetch origin --prune`, remain on a safe feature branch, and push `HEAD` without force or automatic history rewriting.
7. Verify local HEAD, branch, and all remote heads. `REMOTE_DELIVERED` requires the task branch's remote SHA to equal local HEAD. On auth, network, or SHA failure, preserve commits and report the exact blocked status and retry command.
8. If `origin/main` exists and GitHub CLI is both installed and authenticated, an authorized agent may create a Draft PR with evidence, unknowns, rollback, and explicit phase exclusions. Never mark it ready or merge it.

Use existing credentials without reading or printing tokens. Do not modify credential helpers or run interactive authentication automatically.

## CI provider

`scripts/ci.sh` is the sole CI truth. No provider workflow exists in the foundation phase, so remote CI is `NOT_CONFIGURED`; do not infer a run from local results. A future provider wrapper must only bootstrap the locked environment and call this script without upstream network audits, private vaults, or real APIs.
