# Upstream Dynamic Evaluation Gap Matrix

Status: `PROPOSAL_ONLY`; identity reveal is complete, but `GATE_BASE_SELECTION_PENDING` remains open.

## Evidence boundary

This matrix uses only the 18 frozen synthetic-case scores, retained run/recovery records, the
post-freeze reveal record, and pinned static upstream reviews. It does not claim real CUMCM
effectiveness, execute third-party code, or authorize integration.

| Gap | Frozen observation | Severity | Proposed mechanism | Observable next-phase metric | Confidence |
|---|---|---:|---|---|---|
| GAP-001 — held-out leakage and inconsistent model selection | CASE-004 deterministic scores were 28/25/27 for YUSHUI/baseline/HANDSOMEZR. Two arms used test or holdout evidence in selection; the other selected a model worse than its stated validation objective. Every arm missed required robustness evidence. | Critical | `leakage-safe-model-comparison-gate` | No test read before model freeze; validation rule selects the model; all baseline, drift, robustness, randomization, failed-run, and uncertainty artifacts exist. | High |
| GAP-002 — freshness and resumable acceptance state | CASE-005 deterministic scores were 7/7/0. No arm persisted workflow state or exact valid/STALE closure; all missed most dependency-propagation checks. | Critical | `accepted-versus-done-workflow-state` | Exact oracle closure for every mutation; restart begins at earliest invalid stage; done never implies accepted. | Medium |
| GAP-003 — missing reproducibility artifacts | Reviewer findings across CASE-001/002/003/004/006 repeatedly report absent code, result, audit, input-hash, claim-map, or recovery artifacts. | High | `hash-bound-reproducibility-manifest` | Every formal Run binds input/script/output/seed/environment/command/Git hashes; any mutation fails or propagates STALE. | Medium |
| GAP-004 — evidence existence confused with support | CASE-006 deterministic scores were 13/40/35. Every arm missed multiple claim limitation, assumptions, retain/modify/remove, fact, or non-causal checks; none persisted a hash-bound claim map. | High | `claim-evidence-support-gate` | Every promoted claim binds current Source/Run evidence; unsupported, stale, conflicting, or over-broad claims fail closed. | Medium |
| GAP-005 — incomplete requirement and operational validation | CASE-001 deterministic scores were 40/38/33; packaging granularity, unit conversion, causal limits, executable solve evidence, and recovery artifacts remained incomplete. | Medium | Covered partly by the reproducibility manifest; no extra mechanism proposed yet. | Re-run CASE-001 after a native Run manifest exists; require an executable small sanity case and explicit unresolved assumptions. | Medium |
| GAP-006 — data audit without empirical model confirmation | CASE-002 deterministic scores were 48/55/48. All arms produced useful audits but did not validate the proposed split on a downstream model and missed imbalance/extreme or immutable-input evidence. | Medium | Deferred; the model-comparison gate covers split freeze and downstream validation without adding another mechanism. | Frozen split hashes, imbalance/extreme diagnostics, and validation-only comparison all present. | Medium |

## Portfolio ruling

Four mechanisms qualify because each addresses an observed gap with a testable benefit. Every one is
`CLEAN_ROOM_REIMPLEMENT_CANDIDATE`; none is approved for direct reuse, porting, or integration.
Document lint, broad model catalogs, paper-writing workflows, a second total-controller Skill,
network OCR/search, subjective judge panels, and generic extra review steps are rejected or deferred
because they do not close a measured gap, introduce unsafe scope, or duplicate existing authority.

The anonymous median totals—YUSHUI 60.0, native baseline 62.5, HANDSOMEZR 60.5—are too close and too
recovery-sensitive to support winner-takes-all selection. Component evidence therefore informs only
a clean-room architecture proposal for human review.
