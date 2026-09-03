<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2A-C1/C2 candidate freeze

| Candidate | Path | File SHA-256 | Canonical hash | Freeze hash | Status | Replaces | Evidence |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A | evals/results/phase-002d-r2a/authorization_candidate/candidate.json | 2d612e761537c653a6bb27cba66cbf10c75e1b4e9758fa8443a6960525647b21 | fc8dbec82107763fb875f5e3a06e135f86dab917a9db47f953de3058d34fb6bb | — | HISTORICAL_NON_ACTIVE | — | 0 |
| CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C1 | evals/results/phase-002d-r2a-c1/candidate_revision/candidate-c1.json | b02d963794ef3df29c0971083eaad957f80f7b421f05fb79b7f3189ff51eac8a | d74ea54edf38f37d6506b066c7cd8a52ae31dddd189e3da8fd34a4c083b49702 | cdc4142c3313d159cdc8c7b83ed234484c9daab7454e8a3c902e6486be174011 | FROZEN_FINAL_AUDIT_FAIL | CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A | 30 |
| CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2 | evals/results/phase-002d-r2a-c1/candidate_revision/candidate-c2.json | 77ea5f21610003396791350f86cef2845b6ff63edf07e17301ca8e427ed31d51 | 318191117a5e65bc9ab94ac9ec62c063c5bdaa57da3d7c82012c038ff02bb420 | 50cac065c5aff239ec6c18962090b735030ec9cb059920ef44e7194ef412a961 | ACTIVE_AUDITED | CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C1 | 31 |

C1 remains immutable and failed only because `R2A-C1-FINAL-001` exposed an inherited semantic
dependency cycle. The sole permitted C2 revision was created after that failure and its deterministic
resolution were committed and remotely verified.
