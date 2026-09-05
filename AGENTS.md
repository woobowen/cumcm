# Project instructions

## Goal and startup order

Build one evidence-first CUMCM modeling Skill from problem intake through frozen final runs and a versioned handoff to a separate paper team. Before work, read `GOALS.md`, `WORKFLOW.md`, the current file in `plans/active/`, `state/project_state.json`, then the policy relevant to the target directory.
Development is currently paused; a new maintainer reads `HANDOVER.md` and `CODEX_TAKEOVER.md` before proposing 004C5/RC8 work.

## Map and sources of truth

- Goals and scope: `GOALS.md`
- State machine: `WORKFLOW.md`
- Machine contracts: `contracts/`
- Mandatory rules: `rules/`
- Architecture decisions: `docs/adr/`
- Active execution: `plans/active/`
- Runtime state and ledgers: `state/`
- Upstream candidate facts: `research/upstream_candidates/manifest.yaml`
- Generated status: `reports/current_state.md` (never edit manually)
- Paper-team interface: `contracts/modeling_to_paper.schema.json`

See `docs/SOURCE_OF_TRUTH.md` for ownership and `docs/INDEX.md` for the full map. Directory-level `AGENTS.md` files narrow these rules for upstream research, benchmarks, tests, and the Skill.

## Ownership and invariants

- The main agent alone updates formal state, decisions, and acceptance outcomes. Reviewers and subagents are read-only unless a plan explicitly grants a conflict-free write scope.
- Original problem statements and raw data are immutable. Derived corrections need a new artifact and provenance.
- Every formal result binds a Run ID; every Run binds input hashes and a Git commit.
- Every external fact binds a registered Source. Claims, results, and handoffs preserve evidence links.
- Validation or held-out answers that become visible permanently demote that case to development.
- Technical gates use automated evidence adjudication and require a passing Decision Auditor; agent majority votes cannot pass a gate.
- Humans perform only `TEAM_COMPLIANCE_REVIEW` and evidence-backed challenge; they cannot override a technical rejection.
- The main agent remains the sole formal-state writer; the system may reject every option or abstain.
- Recovery-affected evidence is gap evidence only and never enters comparative ranking.
- Formal roles execute serially with role-specific identity-blind bundles; Meta and Auditor remain
  locked until their validated predecessors exist.
- Transport recovery uses exact-session checkpoints and versioned start budgets. Raw events and
  exact identifiers remain ignored; exhausted role budget terminates the chain without inference.
- Upstream changes, input changes, or superseded Final Runs propagate `STALE` to dependent artifacts.
- Phase 002D machine truth is `evals/results/phase-002d/`; an insufficient terminal Gate locks native
  semantic audits and Phase 003, and only a newly frozen Phase 002D design may continue acquisition.
- Phase 002D-R1 machine truth is `evals/results/phase-002d-r1/`; quality, reliability, outcome and
  gap scopes never substitute for one another, and terminal/censored outcomes are never zero scores.

## Prohibitions

Do not execute unaudited third-party code, install candidate dependencies, copy candidate Skills into `.agents/skills`, search for benchmark answers, read `benchmark-vault`, fabricate runs/sources/completion, edit generated reports, silently mutate raw inputs, or change global Codex configuration. Do not treat agent votes as mathematical or experimental evidence. Detailed security and search boundaries are in `docs/SECURITY.md`, `docs/THIRD_PARTY_POLICY.md`, and `docs/SEARCH_POLICY.md`.

## Validation

Use `.venv/bin/python` after bootstrap:

```text
bash scripts/ci.sh
.venv/bin/python scripts/validate_repo.py --strict
.venv/bin/python scripts/render_status.py --check
git diff --check
```

## Git and remote delivery

- `rules/workflow_rules.yaml` is the sole tracked source for the designated remote and task branch. Completed deterministic changes are not done until they are validated, committed atomically, pushed to that task branch, and verified at the remote SHA.
- Report `REMOTE_DELIVERED` only for commits confirmed on the remote; otherwise report the exact `PUSH_BLOCKED_*`, mismatch, or unverified status. Final reports include branch, HEAD, commits, and validation evidence.
- Except for first initialization of an empty repository, never push feature work directly to `main`. Never force-push or rewrite history already published or used by others.
- Never push secrets, credentials, private paths, full upstream clones, caches, virtual environments, benchmark vaults, answers, restricted third-party content, or machine-only artifacts.
- Pull requests and merges require human review. Agents may create an eligible Draft PR but must not mark it ready or merge it.

## Definition of Done

A change is done only when required artifacts exist, machine contracts validate, relevant offline tests pass, generated reports are current, evidence and approval gates are recorded, the active plan reflects reality, no BLOCKER remains, and the verified commit is remotely delivered when a designated remote exists. Code or prose retained only in the local workspace is incomplete.
