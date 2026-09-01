# Phase 002D cohort freeze

- Result: `PASS`
- Mode: `NEW_MODEL_COHORT`
- Cohort: `PHASE-002D-NEW_MODEL_COHORT-GPT-5-6-SOL-MEDIUM`
- Model/reasoning: `gpt-5.6-sol` / `medium`
- Authentication: `CHATGPT_MANAGED_CODEX`
- Historical model: `gpt-5.4` (not visible in the current local catalog)
- Local catalog check: read-only App Server `model/list`; zero model starts
- Active successful-primary target: `24`
- Historical MODE A shortfall, recomputed but inactive: `14`
- Historical Phase 002 use: `CROSS_MODEL_EXPLORATORY_GAP_EVIDENCE_ONLY`
- Transport profile: `PENDING_PILOT`
- Scored runs started: `false`

The cohort Gate compared the hard model/reasoning conditions and froze the content/safety policy.
Because the historical model is not available to the current local account, MODE A is prohibited
without relying on web claims. The selected replacement is visible with `medium` support and is the
only frozen replacement candidate. A real compact pilot is still mandatory before budget freeze or
scored execution; pilot failure stops this cohort rather than changing models.

Evidence:

- `evals/results/phase-002d/cohort/model_availability.json`
- `evals/results/phase-002d/cohort/cohort.json`
- `evals/results/phase-002d/input_freeze_manifest.json`
- `docs/adr/ADR-0024-phase002d-model-cohort.md`
