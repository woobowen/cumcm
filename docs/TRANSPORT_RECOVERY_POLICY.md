# Formal adjudication transport recovery policy

This policy governs transport recovery for external formal adjudication roles. It does not change
the frozen evidence, policy thresholds, role order, or technical decision semantics.

## Adapters and selection

`EXEC_RESUMABLE` is primary. It starts a persistent Codex exec session and records the exact
session identifier only in ignored local recovery state. `APP_SERVER_RESUMABLE` is the only
fallback and is eligible only when exec cannot establish a resumable session, exact-session resume
fails, or exec cannot satisfy the resume contract. Adapter selection never authorizes a model,
reasoning, evidence, policy, or output-Schema change.

`resume --last` is prohibited. Resume must name the exact session/thread and reuse the same role
workspace, bundle, policy, Schema, model, and reasoning setting. Each role has a distinct session
or thread and cannot receive peer outputs.

## Checkpoint contract

After an observable session/thread start and after every terminal event, write the tracked
checkpoint atomically. Tracked checkpoints contain only role, Adapter, attempt, status, hashes of
identifiers and artifacts, bounded event metadata, failure classification, and resume eligibility.
Exact identifiers, raw JSONL, stderr, final-message scratch files, and temporary role workspaces
remain ignored. A completed checkpoint is reusable only when all bound hashes and identity checks
still pass.

## Failure and budget rules

Failures are classified by the enumerated recovery contract, including authentication, quota,
connect reset, timeout, disconnection, missing/resume-failed session, unavailable or mismatched
model, invalid Schema/output, evidence/policy mismatch, and sandbox/network/MCP violations. Unknown
transport failures remain explicit; they are never relabeled as a model conclusion.

The active versioned config fixes global and per-role start budgets. An initial turn, continuation,
fallback turn, optional review, Judge, Dissent, Meta, or Audit turn each consumes one start. Offline
checks and deterministic replay consume none. Once a role exhausts its budget without a valid
output, later roles remain locked even when global starts remain. Record
`AUTOMATED_ADJUDICATION_INCOMPLETE`; do not synthesize output or spend an unauthorized extra start.

## Restart and terminal handling

On process interruption, revalidate the input freeze and every completed checkpoint, then begin at
the first incomplete role. Never rerun an earlier valid role. On terminal failure, retain sanitized
tracked diagnostics and raw hashes, generate the incomplete report, keep
`next_phase_allowed=null`, and prohibit Meta, Audit, replay, and decisions whose prerequisites do
not exist. Ignored exact-session material may be removed only as a separately reported cleanup.
