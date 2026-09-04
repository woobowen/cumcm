# Competition RC1 Acceptance Report

## Acceptance

`COMPETITION_SKILL_RC_READY`

The project-owned `cumcm-modeling-evidence` Skill is accepted at version
`0.2.0-competition-rc1`, capability `COMPETITION_RC`, and assurance
`PUBLIC_DETERMINISTIC_AND_TWO_END_TO_END_SMOKES`. This is a bounded Development-evaluation release,
not a production or generalization claim.

## Architecture and historical preservation

The unchanged eight-Gate policy evaluated 117 symmetric cases for each candidate, 234 total, with
zero unhandled exceptions. K1 and W1 both passed G1–G8. The frozen rule—K1 on 8/8, otherwise W1 on
8/8, otherwise block—therefore selected
`ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`; no score compensation, Agent vote, or human
technical override was used.

- Decision: `DECISION-COMPETITION-RC1-ARCHITECTURE-003F-R1`
- Scope: `COMPETITION_RC_IMPLEMENTATION_ONLY`
- Decision hash: `8b4c50dbe5f95ca04ceff4c489ae83dc3a4afa81e156e1f00f16b2ac65f25cbe`
- Gate result SHA-256: `07d4362f0c2d0c6b502bcae99748e18f825ded4662554fb860d4db483376b971`
- K1 R1 tree: `35caf2809815e06a8f7d41840adddfe2d1600c1169d7e59d742b021be5df0ea8`
- W1 R1 tree: `a7d90ade3d4a28ae2951a6596f43ad680f3be3387f5dd00f9ed4c8b4957dbfff`

The prior `DECISION-COMPETITION-MVP-ARCHITECTURE-003F` remains byte-for-byte preserved with
`FAST_TRACK_IMPLEMENTATION_BLOCKED`, decision hash
`2ed22c0e6ba08159077ae891bfb310947fa007e84dd38fdde2af54beeef25b5d`, and artifact SHA-256
`70cd886ad2efb226769bb15a26d041554f12d24c2bf3acc8c87b90f6527156a1`.

| Gate | K1 R1 | W1 R1 |
|---|---:|---:|
| G1 malformed input fail-closed | PASS | PASS |
| G2 done is not accepted | PASS | PASS |
| G3 exact Claim/evidence support | PASS | PASS |
| G4 reproducibility manifest | PASS | PASS |
| G5 leakage-safe comparison | PASS | PASS |
| G6 input/state isolation | PASS | PASS |
| G7 security/provenance | PASS | PASS |
| G8 end-to-end composition | PASS | PASS |

## Formal Skill implementation

Exactly one discoverable formal Skill remains at `.agents/skills/cumcm-modeling-evidence/`. It
contains 14 business workflows, four bounded Agent roles, 14 case templates, and the centralized
offline `scripts/cumcm_case.py` CLI with `init`, `status`, `validate`, `manifest`, `claim-check`,
`compare-check`, `stale-check`, `finalize`, `handoff`, and `smoke` commands.

The selected K1 semantics are integrated as project-authored general controls: strict input and
finite-number boundaries, case-local single state truth, exact manifest/run/Claim hashes,
leakage-safe selection, failure retention, transitive `STALE`, and contract-validated
modeling-to-paper handoff. W1, Shadow evaluator adapters, audit fixtures, and candidate-selection
code were not integrated. The formal tree hash is
`76dce0d6a63ab78bd38a21c27d40fba0b2d5242e3283ade8cdc0b7dfd809b8d8`.

The state machine separately records `RUN_COMPLETED`, `RUN_VALIDATED`, `EVIDENCE_VALIDATED`, and
`READY_FOR_PAPER_HANDOFF`. File existence and Agent declarations never advance a Gate. Changes to
bound input, code, configuration, output, or evidence propagate `STALE` with an exact dependency
chain.

## End-to-end evidence

`SYNTH-RC1-PREDICTION-001` ran a project-original time-regression case containing missing data, an
outlier, and a leakage field. The leakage field was rejected, selection used validation MAE, test
was accessed once after selection, and `P-LINEAR-TREND` reached deterministic test MAE `0.0`.

`SYNTH-RC1-OPTIMIZATION-002` ran a project-original bounded integer allocation case. It retained
and excluded an infeasible negative-control attempt, compared an A-only baseline with enumeration,
and selected `(x_A,x_B)=(3,2)` with independently recomputed objective `22`.

Both cases traversed 13 gated transitions from `CREATED` to `READY_FOR_PAPER_HANDOFF`, produced all
23 required `modeling-to-paper/v1` fields, and passed the existing contract. Post-READY mutation of
each raw input produced `RC_UPSTREAM_DEPENDENCY_STALE` without mutating state.

- Prediction evidence: `ec744f61f5efac91c5017245921a5cfd427b45a6231dde1ed9225d10468fe791`
- Optimization evidence: `15fe6fc0c6d6de92c5cfdfcc38b997eb69ab3b6527ac961e792a59c3be563160`
- Combined evidence: `6f42defe1c537ffc2a812b8f1b5fd97889898d51a1a79dee48821c6a3e68256c`
- End-to-end result SHA-256: `3beefd5190547246a361e6829a2236224927af8a9673cc0344ff62f78676fa99`

## Negative matrix

All 30 specified scenarios returned the expected structured rejection or `STALE`; every input was
unchanged, no case reached handoff readiness, no exception escaped, and neither injected sensitive
canary appeared in serialized results.

| # | Scenario | Expected | Actual | Stable reason code | Result |
|---:|---|---|---|---|---|
| 1 | malformed context | BLOCK | BLOCK | `RC_CONTEXT_INVALID` | PASS |
| 2 | malformed enabled components | BLOCK | BLOCK | `RC_CONTEXT_ENABLED_COMPONENTS_INVALID` | PASS |
| 3 | NaN score | BLOCK | BLOCK | `RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID` | PASS |
| 4 | Inf score | BLOCK | BLOCK | `RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID` | PASS |
| 5 | numeric-string score | BLOCK | BLOCK | `RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID` | PASS |
| 6 | empty candidate set | BLOCK | BLOCK | `RC_COMPARISON_EMPTY_CANDIDATE_SET` | PASS |
| 7 | empty split | BLOCK | BLOCK | `RC_COMPARISON_EMPTY_SPLIT` | PASS |
| 8 | FAILED attempt scored | BLOCK | BLOCK | `RC_COMPARISON_NON_SUCCESS_ATTEMPT_SCORED` | PASS |
| 9 | test leakage | BLOCK | BLOCK | `RC_COMPARISON_LEAKAGE:test_used_for_candidate_generation` | PASS |
| 10 | future leakage | BLOCK | BLOCK | `RC_COMPARISON_LEAKAGE:future_information` | PASS |
| 11 | group leakage | BLOCK | BLOCK | `RC_COMPARISON_LEAKAGE:group_overlap` | PASS |
| 12 | target leakage | BLOCK | BLOCK | `RC_COMPARISON_LEAKAGE:target_in_features` | PASS |
| 13 | unauthorized test access | BLOCK | BLOCK | `RC_COMPARISON_UNAUTHORIZED_TEST_ACCESS` | PASS |
| 14 | arbitrary freeze hash | BLOCK | BLOCK | `RC_COMPARISON_UNTRUSTED_FREEZE` | PASS |
| 15 | private key | BLOCK | BLOCK | `RC_SECRET_FIELD_REJECTED` | PASS |
| 16 | refresh token | BLOCK | BLOCK | `RC_SECRET_FIELD_REJECTED` | PASS |
| 17 | UNC path | BLOCK | BLOCK | `RC_PRIVATE_ABSOLUTE_PATH_REJECTED` | PASS |
| 18 | manifest mutation | BLOCK | BLOCK | `RC_MANIFEST_OUTPUT_MUTATION` | PASS |
| 19 | output hash mismatch | BLOCK | BLOCK | `RC_MANIFEST_OUTPUT_HASH_MISMATCH` | PASS |
| 20 | unbound verified-run decision | BLOCK | BLOCK | `RC_CLAIM_REQUIRED_BINDING_MISSING` | PASS |
| 21 | stale evidence | BLOCK | BLOCK | `RC_CLAIM_STALE_EVIDENCE` | PASS |
| 22 | contradictory Claim | BLOCK | BLOCK | `RC_CLAIM_CONTRADICTED` | PASS |
| 23 | unsupported Claim | BLOCK | BLOCK | `RC_CLAIM_OVERBROAD_OR_UNSUPPORTED` | PASS |
| 24 | done without validation | BLOCK | BLOCK | `RC_ARTIFACT_NOT_ACCEPTED` | PASS |
| 25 | formal state write | BLOCK | BLOCK | `RC_FORMAL_STATE_WRITE_PROHIBITED` | PASS |
| 26 | second state truth | BLOCK | BLOCK | `RC_SECOND_STATE_TRUTH_PROHIBITED` | PASS |
| 27 | PRODUCTION stage | BLOCK | BLOCK | `RC_CONTEXT_EXECUTION_SCOPE_PROHIBITED` | PASS |
| 28 | cross-component run hash mismatch | BLOCK | BLOCK | `RC_CLAIM_RUN_BINDING_MISMATCH` | PASS |
| 29 | upstream stale propagation | STALE | STALE | `RC_UPSTREAM_DEPENDENCY_STALE` | PASS |
| 30 | incomplete modeling-to-paper package | BLOCK | BLOCK | `RC_HANDOFF_REQUIRED_FIELDS_MISSING` | PASS |

Result SHA-256:
`5c46849aee853b1bb1d9af43f7ea22d827681852e6a2150da6ad4bd0cd2f5f60`.

## Independent audit and regression evidence

The single formal integration Auditor independently replayed the Gate, both end-to-end cases,
5,960 hostile validator calls, exact lineage/STALE mutations, public wrapper integrity, and Phase
004 boundaries. It reported PASS with zero BLOCKER and zero major finding after directed repairs.
The final full local regression collected 1,805 tests: `1804 passed, 0 failed, 1 skipped`. Ruff,
contracts, instruction budget, Skill discovery, answer-leakage, secret, RC consistency, strict
repository validation, generated-state verification, local CI, remote branch SHA, and the Draft PR
CI are delivery gates and are reported with their command receipts in the final handoff.

## Formal state and next step

- Phase: `PHASE-SKILL-INTEGRATION-003`
- Subphase: `COMPETITION-RC1-REPAIR-AND-INTEGRATION`
- Technical status: `COMPETITION_SKILL_RC_READY`
- Active Skill: `0.2.0-competition-rc1` / `COMPETITION_RC`
- Selected architecture: `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`
- `base_selected=false`; `third_party_integrated=false`; blockers: none
- Next phase: `PHASE-SKILL-DEVELOPMENT-EVAL-004`

The case registry is intentionally empty. The next task must select one answer-sealed historical
Development problem, bind its problem/data hashes and the RC1 commit, execute the complete first run
before any answer access, freeze it, then use only real generalizable failures to form RC2.

## Explicitly deferred—not passed

1. full sealed Stage 1
2. Stage 2 model comparison
3. full ablation
4. external validity
5. production fitness
6. monetary cost

RC1 also limits trusted execution-code capture to the two bundled deterministic modules; a
caller-supplied custom executor is outside this assurance and requires a future frozen design.

API-key use, API billing, model training, fine-tuning, real Stage 2 comparison starts, historical
answer access, hidden Benchmark access, and third-party execution were all zero. No third-party
base or code was selected or integrated.
