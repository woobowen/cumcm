# PLAN-0002B — Formal Adjudication Transport Recovery

Status: `IN_PROGRESS`
Phase: `PHASE-AUTOMATED-ADJUDICATION-RECOVERY-002B`
Owner: main agent
Started: `2026-09-01T00:45:37+08:00`

## 1. Objective and current blocker

Resume the incomplete Phase 002A formal chain without changing frozen evidence or adjudication
policy. The blocking condition is that no Schema-valid Blind Correctness Judge result survived three
Codex Responses transport failures, so Scientific, Engineering, blind Dissent, Meta, Auditor,
replay and formal decisions could not legally run. This phase is successful when all six external
roles, Meta decisions, independent audit and deterministic replay are complete; acceptance is not
required and `EVIDENCE_INSUFFICIENT` or `AUTOMATED_ABSTAINED` is a valid completion.

## 2. Preserved failure evidence and budget

- Attempt 1 ran for 303.218787 seconds and ended in a Responses stream timeout/platform endpoint
  failure; sanitized raw-event SHA-256 is
  `e682128242235dce4e8a0384a54103ace7f88d67ef6b85a7d8bf5c655d3a9f66`.
- Attempt 2 ran for 54.952198 seconds and ended after WebSocket reset plus HTTPS fallback;
  sanitized raw-event SHA-256 is
  `1104355b050859bc008835b1277457084743417d2c52ca3bac8e3bf9fd1543a`.
- Attempt 3 ran for 53.006485 seconds and ended after WebSocket/HTTPS transport failure with
  optional features disabled; sanitized raw-event SHA-256 is
  `7dc68c3ae5f352e458321680017d32f444fb4a3c79003689de74b79b4ee672b`.
- The original twelve-start budget has consumed four starts: one excluded unblinded Dissent and
  the three failed Correctness attempts. Phase 002B may start at most eight more model runs.
- Every initial turn, exact-session continuation, alternate Adapter turn, Judge, Dissent, Meta,
  Auditor or optional stability review counts. Each role has at most two starts. Six first-try
  completions leave two starts unused or available for optional review; offline replay has priority.

## 3. Immutable inputs and why Phase 002 is not rerun

Phase 002 measured candidate behavior under a closed twenty-run budget and Phase 002A froze its
evidence. Rerunning would mix environments, expose post-hoc tuning and invalidate the subject
commit, while doing nothing to repair the transport layer. Phase 002 results, the Phase 002A freeze,
eligibility/coverage/oracle/process inputs, 24 findings, 24 requests, 24 evidence records, prior
failures, raw-trace hashes and anonymous bundle hash remain byte-for-byte immutable. Phase 002B
writes only under `evals/results/phase-002b/`, reports, state, code, tests and governance documents.
`input_freeze_manifest.json` binds paths, hashes, subject commit, policy/evidence/schema/config/
runner hashes and the three prior failure hashes. Any mismatch is terminal `INPUT_FREEZE_BROKEN`.

## 4. Transport Adapter design

One interface exposes `start_role`, `resume_role`, `poll_role`, `cancel_role`, `load_checkpoint`,
`validate_output`, `classify_failure` and `summarize_events`. `EXEC_RESUMABLE` is primary and uses
the installed CLI with a persistent exact session, fixed `gpt-5.4`/`medium`, strict ignored user
configuration, output Schema, JSON events, output-last-message, isolated role workspace, no remote,
no MCP, no dynamic tools, workspace-write sandbox and policy-prohibited network. Raw events and the
exact session identifier stay ignored; tracked records contain only irreversible identifier hashes,
event counts, status, timestamps and content hashes.

`APP_SERVER_RESUMABLE` is the sole fallback when exec has no resumable session, an exact resume
fails, or exec cannot meet the resume contract. The minimal stdio JSON-RPC client initializes the
bundled Codex App Server, starts or resumes one independent thread, starts one constrained turn,
streams notifications, captures completion, validates JSON and can interrupt or restart the local
server. It neither installs an SDK nor changes authentication, model, reasoning or policy.

## 5. Role-specific evidence bundles

Bundles are deterministic structured projections, not LLM summaries. Each contains an index,
policy summary, eligible and excluded evidence, hard Gates, role-relevant findings, test evidence,
role task and output Schema. Evidence IDs, hashes, numerical values, every BLOCKER, unresolved
Dissent, recovery exclusion, license/contamination limits and hard Gates are preserved. Candidate
identity, historical answers, third-party body text, raw traces, private paths, duplicated prose and
peer-role outputs are forbidden. Normalized content is capped at 128 KiB and estimated input at
30,000 tokens; oversize fails closed after deterministic de-duplication or sharding, never arbitrary
truncation. Tracked manifests bind every ignored bundle file and prove mandatory coverage.

## 6. Checkpoints and resume semantics

Each role receives one atomic tracked checkpoint with role, Adapter, hashed thread/turn identifiers,
attempt, model/reasoning, bundle/policy/schema hashes, timestamps, completion/failure class,
raw-event/output hashes, resume permission, supersession and notes. Exact identifiers live only in
ignored local recovery state. A transport failure with a captured exact session continues that
session once with the same workspace, model, bundle and Schema and a neutral continuation request;
`resume --last` is forbidden. A nonresumable exec failure may use App Server as attempt two. A
completed role is reused only when Schema, identity, evidence, policy, model and freshness checks
still pass. Restart begins at the first incomplete role and never reruns earlier valid roles.

## 7. Formal order and independence

Strict order is: (R1) Correctness, (R2) Scientific Validity, (R3) Engineering/Reproducibility,
(R4) Blind Dissent, (R5) Evidence Meta-Adjudicator, (R6) Decision Auditor. All are external Codex
sessions/threads; neither the orchestrator nor its in-process subagents substitute for them. R1-R3
cannot see peers, Dissent, identities, historical recommendations, human Gates, Meta expectations or
orchestrator preference. R4 cannot see R1-R3. Meta starts only after four valid blind outputs and
Auditor only after Meta plus three Schema-valid automated decisions. No session/thread is shared.

## 8. Completion checks between roles

After each role: validate its Schema, identity blindness, evidence references, policy/evidence/
bundle/model hashes, absence of majority-vote and human-Gate logic, output hash and checkpoint;
append the role ledger and only then unlock the next role. Meta applies only
`adjudication/policies/phase-002a.yaml` and must emit `DECISION-ARCHITECTURE-002A`,
`DECISION-RECOVERY-POLICY-002A` and `DECISION-COMPONENTS-002A`. Auditor independently tests
leakage, contamination, cross-role exposure, threshold/evidence mutation, unsupported claims,
scope, hardcoding and replayability. Only Audit `PASS` lets the orchestrator apply formal technical
state; Audit `FAIL` or `RETEST_REQUIRED` cannot allow Phase 003.

## 9. Failure classification and stop rules

Classify exactly where observable: `AUTH_BLOCKED`, `QUOTA_BLOCKED`,
`RESPONSES_CONNECT_RESET`, `RESPONSES_STREAM_TIMEOUT`, `APP_SERVER_DISCONNECTED`,
`SESSION_ID_MISSING`, `SESSION_RESUME_FAILED`, `MODEL_UNAVAILABLE`,
`MODEL_COMPARABILITY_BROKEN`, `SCHEMA_INVALID`, `OUTPUT_MISSING`,
`EVIDENCE_HASH_MISMATCH`, `POLICY_HASH_MISMATCH`, `IDENTITY_LEAK`,
`SANDBOX_POLICY_VIOLATION`, `NETWORK_POLICY_VIOLATION`, `MCP_POLICY_VIOLATION` or
`UNKNOWN_TRANSPORT_FAILURE`. Each failure stores sanitized observable evidence, stderr/event hash,
identifier hash, attempt, resumability, next Adapter, terminal flag and whether external action is
required. A role without a valid output after two starts stops the formal chain; Meta never fills a
missing Judge. Total start eight or model mismatch also stops. No mock output becomes formal.

## 10. Model and authentication boundary

All six roles use frozen `gpt-5.4` with `medium` reasoning. Intermittent transport errors do not
authorize a model switch. If the model is unavailable, stop with `MODEL_UNAVAILABLE`; a future
uniform replacement requires a new config version, ADR, removal of incomplete Phase 002B role
outputs and a full same-model restart within separately approved budget. Use only the existing
ChatGPT-managed Codex login. Never read `OPENAI_API_KEY`, request credentials, use API-key login,
print/copy auth state, switch to API billing, create a Platform project or modify global Codex
configuration. Authentication and quota failures remain distinct blockers with minimal local login
guidance only.

## 11. Milestones, commands and acceptance

1. **M1 recovery start/freeze** — archive the unchanged incomplete 002A plan, create this plan,
   update state/ledgers/Schema, build `input_freeze_manifest.json`; run focused contract/state/freeze
   tests and `git diff --check`. Accept when one active plan exists and all frozen hashes verify.
2. **M2 compact bundles** — run `scripts/build_adjudication_bundles.py` and `--check`; run bundle
   unit/fault tests. Accept when six manifests are deterministic, identity-free, under both budgets,
   contain every BLOCKER and explicitly exclude recovery cells.
3. **M3 transport** — implement exec, App Server, checkpoints, classification, sanitization and
   selection; run transport unit/integration/fault suites. Accept when completed/resume/fallback,
   disconnect, stale/budget/model mismatch and secret/raw-event controls pass offline.
4. **M4 pre-runtime validation** — Ruff, full pytest, contracts, leakage, secret, Phase 002 freeze,
   Phase 002A rescore, bundle/checkpoint checks and strict validation. Accept with no error/warning,
   no changed frozen input and no real model start.
5. **M5 blind roles** — run `run_blind_adjudication.py --transport auto --resume
   --remaining-real-run-budget 8`. Accept only four sequential valid independent outputs and
   checkpoints, starting with Correctness as the transport probe.
6. **M6 Meta/Audit/Replay** — run Meta, Auditor and offline replay scripts. Accept with the remaining
   two valid independent outputs, three decision records, exact Audit result and stable original,
   order, Judge-order, label-swap and recovery-excluded replays.
7. **M7 state/reports** — run `summarize_phase002b.py`, status render/check and strict validation.
   Accept when reports derive from records and formal state matches Audit/replay without forced
   acceptance.
8. **M8 delivery** — run all specified final checks and `scripts/ci.sh`; commit related files in
   atomic groups, push current branch normally, verify local/remote SHA, update only Draft PR #2 and
   confirm offline CI. Accept only with clean tree and PR still OPEN/DRAFT.

## 12. Offline test matrix

At least thirty meaningful transport tests cover exec completion, exact resume and missing session;
App Server start/turn/disconnect/resume; fallback; checkpoint atomicity/freshness; role/global budget;
auth, quota, reset, timeout and Schema classification; sanitization and identifier hashing; separate
threads/workspaces; no peer exposure, API-key read, global-config write or hidden reasoning. Chain
integration covers six roles, partial restart, Meta/Audit prerequisites, insufficient/abstain as
complete, no forced acceptance and report derivation. Ordinary CI never starts real Codex.

## 13. Interruption recovery and rollback

On interruption, reverify the Phase 002B input freeze, policy/config/model and completed checkpoint
hashes, then resume only the first non-completed role. Preserve every failed/superseded record and
raw trace hash. Exact session state and bundle workspaces remain ignored until terminal delivery,
then may be removed only as a separately reported cleanup. Published changes are rolled back only
with a scoped `git revert`; never reset, clean, overwrite immutable inputs, rebase published history
or force push.

## 14. Git delivery and Phase 003 boundary

All work stays on `feat/upstream-dynamic-eval` and updates existing Draft PR #2. Stage explicit
paths, validate each atomic commit, push without force, verify remote SHA and keep the PR OPEN/DRAFT.
Phase 002B never implements a mechanism, selects a third-party base or starts
`PHASE-SKILL-INTEGRATION-003`. `third_party_integrated=false`, Skill `SCAFFOLD_ONLY` and
`base_selected=false` remain invariant. Only a data-driven accepted architecture with Audit PASS
and stable replay may set a future `next_phase_allowed`; this phase records that result but does not
execute it.

## 15. Terminal outcomes

`AUTOMATED_ADJUDICATION_COMPLETE` requires all six external outputs, three legal decisions, exact
Audit result, deterministic replay, current generated reports, full validation and remotely verified
delivery. The technical decision may still be insufficient, abstained, retest or rejected. Missing
any role, Meta, Auditor or replay; a broken freeze; exhausted per-role/global budget; model mismatch;
or unrecovered transport leaves `AUTOMATED_ADJUDICATION_INCOMPLETE` with exact blockers and
`next_phase_allowed=null`.
