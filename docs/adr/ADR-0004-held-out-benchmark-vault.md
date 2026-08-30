# ADR-0004: Held-out benchmark vault

## Context
Answers in repository context contaminate evaluation and invite accidental search/leakage.
## Candidates
Track answers; encrypt in repository; keep a separate ignored access-controlled vault.
## Decision
Use excluded `benchmark-vault/`; never read it during ordinary development or foundation.
## Evidence
One-way demotion after answer exposure makes contamination explicit and auditable.
## Rejected alternatives
Tracked/encrypted-in-tree answers remain discoverable or require secret management in scope.
## Consequences
Held-out execution needs an independent gate and cannot run in ordinary CI.
## Revisit conditions
Adopt a managed evaluation service only after privacy, access, logging, and reproducibility review.
