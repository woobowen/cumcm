<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2A adversarial tests

- Registered serious findings: `15`
- Test requests: `15`
- Passing recorded evidence: `15`
- Failing recorded evidence: `0`
- Closure hash: `61a68a723161f46b30ac6ac2183680b009bd6d24ede6d19068449fbf8b8078f5`

The terminal auditor nevertheless opened `R2A-FINAL-002`: the scope test evidence predates and
does not hash-bind the exact remediation candidate it audited. The registry PASS is therefore
insufficient for sealing; the failed remediation was rolled back to the non-active M5 candidate.
