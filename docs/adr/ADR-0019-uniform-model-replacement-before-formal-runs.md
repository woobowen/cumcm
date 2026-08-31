# ADR-0019 — Uniform model replacement before formal runs

Status: Accepted
Date: 2026-09-01

## Context

Phase 002A froze `gpt-5.4` with `medium` reasoning. Before any Phase 002B model start, a non-model
Codex App Server `initialize` and `model/list` capability check succeeded but the current
ChatGPT-managed catalog did not include `gpt-5.4`. It did include `gpt-5.6-sol`, `gpt-5.6-terra`,
`gpt-5.6-luna`, `gpt-5.5` and `gpt-5.2`. No Phase 002B formal role output existed, so there was
nothing to mix or clear. The Phase 002A policy, evidence, thresholds and original config remain
unchanged and hash-bound in the Phase 002B input freeze.

## Decision

Create `adjudication/configs/phase-002b-v2.yaml` and use `gpt-5.6-sol` with the same `medium`
reasoning for all six Phase 002B formal roles. Selection is based on explicit local catalog support
and flagship complex-reasoning capability, not on a desired adjudication outcome. The original
`phase-002a.yaml` is retained byte-for-byte as the historical frozen default. All role bundles,
checkpoints, outputs, ledgers and reports must bind the replacement config and record the resulting
cross-phase comparability limitation.

## Consequences

- A Phase 002B output produced by `gpt-5.4` or any model other than `gpt-5.6-sol` is invalid.
- A resume that reports another model is `MODEL_COMPARABILITY_BROKEN` and terminal for the role.
- All six roles must use `medium`; a single-role switch is prohibited.
- The eight-start remaining budget is unchanged and the capability check consumes zero starts.
- No Phase 002/002A evidence, policy threshold or formal decision is changed.
- The completed chain may still report insufficiency, abstention, retest or rejection.

## Rejected alternatives

- Attempting an unlisted `gpt-5.4` formal run and spending scarce budget on discovery.
- Mixing `gpt-5.4` and a replacement after a partial chain.
- Choosing a lower tier because it might be faster or a model because it might favor acceptance.
- Switching to API-key authentication or API billing.
