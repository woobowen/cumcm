# Claim scope root cause

RC4 validate_claim required top-level claim_text/supported_scope to equal Final claim_scope,
and additionally required aggregate ID/text/scope to equal requirement_ids[0]. Multiple
requirements can have distinct supported local conclusions, so these equalities conflict.
The requirement list equality also imposed ordering on set coverage.

Affected paths: claim-check, validate at FINAL_CANDIDATE, claim template, and handoff generation.
The repair retains captured statement/Final binding and exact Run/output/decision checks, while
replacing first-element identity with explicit requirement-union support and set equality.
It uses no contest-specific identifier, field, parameter, answer or modeling method.

Legacy reading is a pure derived transformation. Auxiliary requirement roles are recorded
explicitly and do not replace primary coverage. The output preflight still requires all primary
claims and retains the exact existing successful-output schema.
