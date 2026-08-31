# Dynamic evaluation runbook (historical Phase 002)

Status: superseded by `AUTOMATED_ADJUDICATION_RUNBOOK.md`. Human technical gate instructions below
are preserved only to reproduce Phase 002 and have no active authority.

## Resume

Read `AGENTS.md`, `GOALS.md`, `WORKFLOW.md`, the active plan, `state/project_state.json`, this file,
`rules/dynamic_eval_rules.yaml`, and `evals/configs/phase-002.yaml`. Verify the branch, clean status,
remote, and `origin/main`; run `bash scripts/ci.sh` before changing evaluation truth.

## Build order

1. `scripts/generate_eval_fixtures.py` then `--check`.
2. `scripts/build_eval_packages.py` then `--check`. Packages remain under ignored cache.
3. `scripts/run_upstream_dynamic_eval.py --smoke`; this capability check is not a candidate run.
4. Run the configured evaluation only if packages are safe and nested Codex is available.
5. Score offline; freeze anonymous scores; reveal separately; summarize from records.

## Isolation

Each run gets `.cache/upstream-eval/workspaces/<evaluation>/<arm>/<case>/<run>/`, initialized as a
Git repository without a remote. Copy only case inputs, the output Schema, the common prompt, and
the current arm’s normalized instructions. Invoke the locally installed Codex CLI with verified
flags: non-interactive input, `--ephemeral`, `--ignore-user-config`, `--sandbox workspace-write`,
`--json`, `--output-schema`, `--output-last-message`, model, reasoning setting, and `--cd`.

`workspace-write` constrains filesystem writes but is not documented here as an OS network
firewall. Network and MCP are disabled by ignored user config, no MCP configuration, no remote in
the workspace, explicit task prohibition, environment scrubbing, and event auditing. Any observable
network/MCP attempt is a hard failure. Raw JSONL, raw outputs, logs, instructions, and arm map stay
ignored. The command never uses dangerous bypass flags.

## Failure handling

Retain nonzero exit, timeout, auth/quota, Schema, safety, and missing-evidence outcomes. Retry only a
documented transient failure within the fixed budget; never discard or overwrite a failure. Mark
unattempted cells `NOT_RUN`, not zero. A package marked `PACKAGE_UNSAFE` stops that arm.

## Score/review/reveal

Deterministic scoring reads normalized observations and observable manifests, never the arm map.
Anonymous qualitative review cites fields and events. Freeze initial scores with hashes before
revealing identity. A correction is append-only and requires human approval; it never overwrites the
initial score.

## Delivery

Run every command listed in PLAN-0002, regenerate status from state, inspect explicit staged paths,
commit atomically, push the feature branch normally, verify remote SHA equality, and create a Draft
PR. Never merge or start Phase 003.
