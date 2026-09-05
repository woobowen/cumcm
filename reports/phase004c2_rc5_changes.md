# RC5 bounded changes

Version: 0.2.0-competition-rc5; Claim contract: claim-evidence/v2.
Implementation commit: 5673aab61a648be1cd9b87364110cb01c13cd033.
Two formal revision cycles used; none remain.

- validate_claim: independent aggregate identity, complete order-independent primary coverage,
  per-requirement exact lineage, captured statement binding and scope union containment.
- required_requirement_ids: explicit role filtering; legacy missing role means PRIMARY.
- build_expected_handoff: aggregate record, local scope/limitations and exact structured formula links.
- Pure derived migration retains old artifacts; new Claim template declares v2.
- Skill entrypoint and Claim/Final/handoff workflows document the contract and limitations.

Maintenance cost: three existing functions changed and four small contract helpers added;
no new dependency, executable engine, model strategy, architecture, or formal Skill.
Execution, capture, seal-run, manifest, comparison, final-result, robustness and output-preflight
function bodies are unchanged. Anti-hardcoding and one-Skill checks pass.

Arbitrary natural-language entailment is not mechanically proved. A statement is restricted by
captured output and explicit requirement scopes; the numerical model still requires independent validation.
