# Phase 004C4 black-box controller probe matrix

The frozen known matrix is
`evals/results/phase-004c4/frozen_actual_controller_probe_matrix.json`, SHA-256
`d28276eaf6616b808c6d5700d27e66f731ed4b33e21d8796d0ea47fe36d40eb2`. Every behavioral test
invokes the actual CLI against a real case workspace and checks nonzero exit, reason code, state
non-progression, rejected handoff, input immutability, trace Gate and non-leakage. Final result:
14/14 PASS, including the matrix-integrity test.

| Probe | Mutation | Expected/actual Gate | Reason | Result |
|---|---|---|---|---|
| AC-001 | external forbidden + acquired empirical only | sufficiency / sufficiency | `RC_EXTERNAL_DATA_POLICY_FORBIDDEN` | PASS/BLOCK |
| AC-002 | incomplete required acquisition plan | sufficiency / sufficiency | `RC_DATA_ACQUISITION_PLAN_INCOMPLETE` | PASS/BLOCK |
| AC-003 | split field/time/entity sources without composition | sufficiency / sufficiency | `RC_DATA_SOURCE_COMPOSITION_UNREGISTERED` | PASS/BLOCK |
| AC-004 | dependent Runs without bridge | compatibility / compatibility | `RC_SELECTION_DEPENDENCY_BRIDGE_MISSING` | PASS/BLOCK |
| AC-005 | portfolio/shared hashes missing | compatibility / compatibility | `RC_SELECTION_PORTFOLIO_HASHES_MISSING` | PASS/BLOCK |
| AC-006 | declared hashes disagree with manifests | compatibility / compatibility | `RC_SELECTION_PORTFOLIO_HASH_MISMATCH` | PASS/BLOCK |
| AC-007 | selected Run failed/unsealed/non-current | eligibility / eligibility | `RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS` | PASS/BLOCK |
| AC-008 | selected Run lacks requirement coverage | semantic / semantic | `RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH` | PASS/BLOCK |
| AC-009 | output owned by another Run | semantic / semantic | `RC_REQUIREMENT_SELECTED_OUTPUT_NOT_OWNED` | PASS/BLOCK |
| AC-010 | required metric binding absent | semantic / semantic | `RC_CLAIM_METRIC_BINDING_MISSING` | PASS/BLOCK |
| AC-011 | `scope_bounded=false` | semantic / semantic | `RC_CLAIM_SCOPE_UNBOUNDED` | PASS/BLOCK |
| AC-012 | aggregate maps requirement to wrong Claim | aggregate / aggregate | `RC_AGGREGATE_CLAIM_MAPPING_INVALID` | PASS/BLOCK |
| AC-013 | unknown kind + non-bijective permutation | compatibility / compatibility | `RC_EVIDENCE_COMPATIBILITY_KIND_INVALID` | PASS/BLOCK |

The independent prosecutor then supplied five new static attacks. They were frozen before repair in
`frozen_adversarial_controller_probe_matrix.json`, SHA-256
`bb358a40d6cfe388376fe757bcabfa16382c19026e02751e908a6d2a53773736`, deterministically reproduced
5/5, and closed in repair loop 1:

| Probe | Mutation | Actual closure |
|---|---|---|
| AP-001 | comparison/requirement-selection split brain | Gate 4 BLOCK, decision mismatch |
| AP-002 | invalid selected-test base64 after valid prior Gates | finalization structured BLOCK, no durable output |
| AP-003 | later portfolio rejection after tentative manifest build | BLOCK with zero new manifests |
| AP-004 | coordinated plan/selection scenario-hash tamper | capture/manifest mismatch BLOCK |
| AP-005 | policy evidence only self-attested by semantic record | semantic BLOCK unless actual output owns exposure/benefit/cost |

The post-repair adversarial observation SHA-256 is
`ac2cadeb55c4805f15b3884ce871d5dcbcb2be126c287134f8b5ef47948ef79a`: adversarial 6/6 and combined
known/adversarial/neutral/RC6 matrix 94/94 PASS. No finding remains open at RC7 release freeze.
