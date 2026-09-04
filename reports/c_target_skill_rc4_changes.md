# C-Target Skill RC4 Changes

## Decision and scope

RC4 contains exactly one admitted change set, sourced from
`C004C-CROSS-OUTPUT-CONTRACT-PREFLIGHT-001`. The same missing reusable output-contract preflight
affected all three RC3 batch cases and became a hard, noncompensable failure when discovered only
after Runs were sealed. Five problem-specific, reference-disagreement, or already-correctly-blocked
findings were rejected.

The formal version is `0.2.0-competition-rc4`; implementation commit is
`297cad0a29c659b18484d4f3b67d69a942ad415c`; Skill tree is
`d041ca38de030ae04813ef02dbe12f7f2b7a1c22`.

## Change set

- `validate_selected_output_contract` checks finite Final metrics, bounded Claim scope, unique
  requirement Claim IDs, figure-ready data, uncertainty, limitations, and exact quantitative
  robustness fields.
- `preflight-output` accepts only an explicitly marked, non-result, non-ranking, placeholder-valued
  contract probe before experiment freeze. The probe hash is bound into the case state.
- `execute` applies the same validator to every exit-zero output. An invalid output is preserved and
  captured as `RC_EXECUTION_OUTPUT_CONTRACT_INVALID`; it is not silently discarded or ranked.
- Synthetic fixtures and workflow instructions were updated to exercise the same contract.

Changed formal Skill files are `SKILL.md`, `VERSION`, `scripts/cumcm_case.py`,
`scripts/synthetic_cases.py`, `templates/case_state.json`, `workflows/experiment_design.md`, and
`workflows/model_execution.md`. Neutral tests changed three test files. No second state truth,
third-party integration, model recipe, year/title/attachment/entity/field, answer, optimum, or
case-specific parameter was added.

## Tests and cost

The change added neutral prediction and optimization probes plus missing/nonfinite metric, Claim,
robustness, figure, uncertainty, limitation, read-only CLI, and invalid-output retention faults.
Focused candidate tests passed 21/21; the final Competition RC suite passed 144/144. Maintenance cost
is bounded to one shared validator, one CLI route, two workflow additions, fixtures, and tests.

## Validation-discovered limitation

RC4 was not changed during 2024 C Validation. The terminal run exposed a separate generic conflict
inside the frozen Claim validator: top-level `claim_text`/`supported_scope` must equal the global
Final scope and also the first requirement-specific claim text. The frozen 2024 C strings differ,
so the Gate fails with `RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID`. This finding is retained for
a new C batch repair; it is not repaired or revalidated on the same Validation case.
