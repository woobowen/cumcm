<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2A-C1 acceptance report

## Outcome

`SHADOW_AUTHORIZATION_CLOSURE_COMPLETE`

The C2 final Auditor returned `PASS`, active decision `DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2` was
sealed at scope `EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY`, all eight offline replay variants are stable, and formal
state is `SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE`. Authorization completeness does not claim that
a prototype exists or works.

## Starting state

- Branch: `feat/phase002d-r2a-shadow-authorization`
- Starting HEAD: `2d117985404b21abd7f0c3a10258731e06f77852`
- Starting tests: `1310` collected / `1288` passed / `21` failed / `1` skipped
- Old candidate: `CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A` / `2d612e761537c653a6bb27cba66cbf10c75e1b4e9758fa8443a6960525647b21` / `fc8dbec82107763fb875f5e3a06e135f86dab917a9db47f953de3058d34fb6bb`
- Old final blocker: `R2A-FINAL-002`

## Historical and Schema compatibility

- History: `PASS` / `e95a81fa08a4b2e2c496b9aee95cdb5eb4ac49eebd94de8d8e5ca9554aa85037`; fixed failures: `20`
- Modes: `CURRENT_TREE_IMMUTABLE, DERIVED_OBSERVATION, LIVE_SEMANTIC_POINTER, SUBJECT_COMMIT_BLOB`
- Live field allowlist: `git_delivery.preferred_task_branch`
- Schema: `PASS` / `7c811862095ee93945fc04afdc17cab31843b95fd5b3920b05cc7bce533b6462`
- Versions: `2.1.0, 2.2.0, 2.3.0, 2.4.0`
- Migration: `b1db25416035b466e2690596cf5931d0897ec860ff758b3efc71db612c57c1c2`; derived only, source unchanged, security fields preserved
- Unknown versions: `FAIL_CLOSED`

## Candidate-bound decision chain

- C1: `b02d963794ef3df29c0971083eaad957f80f7b421f05fb79b7f3189ff51eac8a` / `d74ea54edf38f37d6506b066c7cd8a52ae31dddd189e3da8fd34a4c083b49702` / `cdc4142c3313d159cdc8c7b83ed234484c9daab7454e8a3c902e6486be174011` / final `FAIL`
- C2: `77ea5f21610003396791350f86cef2845b6ff63edf07e17301ca8e427ed31d51` / `318191117a5e65bc9ab94ac9ec62c063c5bdaa57da3d7c82012c038ff02bb420` / `50cac065c5aff239ec6c18962090b735030ec9cb059920ef44e7194ef412a961`
- C2 evidence: `31/31` / `ed3f0383ef5a63138eb62fdeead8e23cc5d0de3d1313a4d78821059a61d58c5a`
- Closure/bundle/audit: `c493a1a2b2d5267bbbe3d33f1c79ddf3b34a8aa523fc942fac54bec56c5bb2f5` / `c11e731fed7212b8f4c82a91c30902cd619829a751a6d1ee3d4a1da3b9b8a443` / `e33c59a489bbce09a4984c92a34812afc2d43c6ba10ee0c952f63178eb8ae125`
- Seal/replay/transition: `ed5ab9b1d850ecc84b09020ae9af58358dfebd2ff1b08c1913c1b00a7cff2473` / `08e8a542dc863151e7bad91fdb6a1301c30f2d9770d6a3a8582652c8ca0e5818` / `2e180b3c3e17b687a184d9f99a24827c308bf9a30c2ec8f5ff4218e6a87ae257`

## Active authorization and state

- Decision/scope: `AUTOMATED_ACCEPTED` / `EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY`
- Supersedes historical R2: `DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2` / `795166071e24497abf27f2be807b006bfa89660ad3d7d99b18c0631f1c304e1d`
- Replaces non-active R2A candidate: `CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A`
- Phase/subphase/status: `PHASE-EVIDENCE-EXPANSION-002D` / `PHASE-002D-R2A-C1-HISTORICAL-COMPATIBILITY-AND-CANDIDATE-BOUND-AUTHORIZATION-CLOSURE` / `IN_PROGRESS`
- Technical status: `SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE`
- Architecture/base/third-party: `null/false/false`
- Skill capability: `SCAFFOLD_ONLY`
- Next phase allowed: `PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`
- Phase 003 entered: `false`

## Implementation embargo and execution statement

- Formal Skill tree before/after: `edeeaf7312e7fc1cdc008bfa799a6127787768246c90ab4c4a569615d11dde33` / `edeeaf7312e7fc1cdc008bfa799a6127787768246c90ab4c4a569615d11dde33`
- Prototype implementation files: `0`
- Formal component implementation files: `0`
- Hidden-vault tracked files: `0`
- Third-party integration/execution: `false/0`
- API key or billing used: `false/false`
- Foundation model trained or fine-tuned: `false`
- Real model-in-loop experiments: `0`
- Native Subagent audit records: `7` in this continuation; state cumulative count `24`
- Prototype executions: `0`
- Optimized objects: historical/Schema verifiers, candidate-binding governance, audit/seal/replay/state validators, contracts, tests, and generated reports only

## Validation

- Validation status/hash: `PASS` / `39dcc359eb6d49c299b3163ecbe62a906d11c990a01d7c0cf1331dd009eae1e3`
- Final pytest: `1485` collected / `1484` passed / `0` failed / `1` skipped
- Contract fixtures: `78` valid / `68` invalid rejected
- Remote CI: `PASS` / `6916ebfaa37021d6b54854bff28d0a6966c3daeb` / `https://github.com/woobowen/cumcm/actions/runs/33738775293`

| Command | Exit | Duration | Type | Result | Output SHA-256 |
| --- | ---: | ---: | --- | --- | --- |
| `.venv/bin/python -m ruff check .` | 0 | 0.030s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `.venv/bin/python -m ruff format --check .` | 0 | 0.036s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `cfa36e1c076dd05d56a03352b8a304c99486b168f337bdd41f72ddb61ed6e966` |
| `.venv/bin/python -m pytest -q` | 0 | 121.226s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `4172ae5d1b8177190193f0bf10cf95108db3a4d4e2e969eb61a2c404b819a9c6` |
| `.venv/bin/python scripts/check_instruction_budget.py` | 0 | 0.055s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `2b21eb602acc7a5cc1980b51851461027e7ea44c7ee47f5ee1876f09bf483b83` |
| `.venv/bin/python scripts/check_skill_discovery.py --expected-name cumcm-modeling-evidence --expected-count 1` | 0 | 0.080s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `b9d2ff4e03913af0e2a32076010d4b8d6d2e30800fccfb4202ea8f4428265f75` |
| `.venv/bin/python scripts/check_contracts.py` | 0 | 0.815s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `2146078454d0a2bbfa861c5dae4273e29396c839cc301f062955821d882ebf72` |
| `.venv/bin/python scripts/check_upstream_manifest.py` | 0 | 0.109s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `45f957b9d70a4e859d3f26f680c12c0cc277043fbeafd2887e4772060c826c04` |
| `.venv/bin/python scripts/check_answer_leakage.py` | 0 | 0.032s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `d340485da43172c5cd09f19a05cbbaa022c11e5e8afee19a234ce5376d208d01` |
| `.venv/bin/python scripts/check_secrets.py` | 0 | 0.919s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `4cc2305e90f20d86dc33305aca8e90ba3512b04c714992a80c4b0b2b7796c897` |
| `.venv/bin/python scripts/freeze_phase002d_r2_inputs.py --check` | 0 | 0.117s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `e6463a3c846dffb77af5a992b2b7d68a874115589fa05d23f35aff6f91ebaae5` |
| `.venv/bin/python scripts/freeze_phase002d_r2a_inputs.py --check` | 0 | 0.108s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `ceaaff343a793d05bf47a7fd77fa79e4dd7a8e6e61f13f8366cabd4a984a088f` |
| `.venv/bin/python scripts/freeze_phase002d_r2a_c1_inputs.py --check` | 0 | 0.046s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `3f7faa5b087653f687eba2d9cefad4f92b49d2b6e373def1c86e8f7bf9bd0720` |
| `.venv/bin/python scripts/check_historical_freeze_compatibility.py --check` | 0 | 1.973s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `4a8794ad9292710e108183623e1837b45ff5ace61c0301ec199bbd05c36c8591` |
| `.venv/bin/python scripts/check_project_state_schema_compatibility.py --check` | 0 | 0.086s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `cff85aba6dff704eed10dfeb7c47bb67b3e49374dfaa849821f6bf50260d715d` |
| `.venv/bin/python scripts/build_shadow_authorization_dependencies.py --check` | 0 | 0.102s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `51b6e010bbdad66950519fed91cecb24a0c9dd64bd57ceb01b94668ab68931f3` |
| `.venv/bin/python scripts/resolve_c1_final_audit_dependency.py --check` | 0 | 0.087s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `4f442fc2ec371d71ebb972c6f6e1bef6ae07f6259f2edc1c8f1929eed2df776b` |
| `.venv/bin/python scripts/check_shadow_authorization_preconditions.py --check` | 0 | 0.174s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `2c05464d1b1fd7ddbd4c7e161aea84deae6e8239569b6eb9dc454d7aec20413c` |
| `.venv/bin/python scripts/validate_shadow_prototype_scope.py --check` | 0 | 0.125s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `cfa3d10169de9e39d1fb44d15d2cc0ebc66bdd04803d64acf9773ffd0f73c9a4` |
| `.venv/bin/python scripts/freeze_shadow_authorization_candidate.py --check` | 0 | 0.031s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `61ad6a46ce84f3f518d884760fa3881308f99cc77314749a7bae9717b78283ff` |
| `.venv/bin/python scripts/build_candidate_bound_authorization_evidence.py --check` | 0 | 0.171s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `07352bace1631595a45b6691134be604d386a5a27485a6022b44737f01bd0738` |
| `.venv/bin/python scripts/audit_shadow_authorization.py --check` | 0 | 0.093s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `9cee7d151f7af232a2e9e22f856e44bef8e2ec709eb81e2797d843d02a9458c6` |
| `.venv/bin/python scripts/freeze_shadow_authorization_candidate_c2.py --check` | 0 | 0.091s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `6c430aaf5aa667d4c0489634d3bc10a45b49bdd95db0c264834a3916a7cfdbd3` |
| `.venv/bin/python scripts/build_candidate_bound_authorization_evidence_c2.py --check` | 0 | 0.222s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `f0247ae76e9940db576f216cdad24bedecf5ce1561e37f91c933be901cad9d8e` |
| `.venv/bin/python scripts/prepare_final_shadow_authorization_audit_c2.py --check` | 0 | 0.288s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `83633964fcf814dc96aab962b017feb57ef50039908ec3ffc6ffbc6668074392` |
| `.venv/bin/python scripts/audit_shadow_authorization_c2.py --check` | 0 | 0.176s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `fc5c696f16dab84eabaa06b9feb9b2267ae8e632654dd54a1c31e0a9eb32ca80` |
| `.venv/bin/python scripts/seal_shadow_authorization.py --check` | 0 | 0.427s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `467c51e2bfd1f63385e3e706947a2aa6a229c38f1451925e4c60c007c27f1cda` |
| `.venv/bin/python scripts/replay_shadow_authorization.py --check` | 0 | 0.847s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `b7bdf1771895606e02c8d2b29f3985d41af4910863a9b17597fabde915ec88e0` |
| `.venv/bin/python scripts/transition_phase002d_r2a_state.py --check` | 0 | 1.270s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `a4ddbd426f495514cbddf3168a646cdd61893f152552f893013c110cd1c62774` |
| `.venv/bin/python scripts/summarize_phase002d_r2a_c1.py --check` | 0 | 0.092s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `e4b1fdf3d4ef168031c9d458dfb81a25f67a5929d2d6b9c03da1c4dbffcbc6bb` |
| `.venv/bin/python scripts/check_implementation_embargo.py --check` | 0 | 0.090s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `4be369dbc0ffc75c18d05352d24f5d2c76f8574f70fdca7c26d13ebf2a39bb36` |
| `.venv/bin/python scripts/check_benchmark_vault.py --check` | 0 | 0.097s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `58cb1e5d6d2df8c7aaf1662c58e4743a2994c3ba90b28de3fbbcf77ecf5aa1c4` |
| `.venv/bin/python scripts/render_status.py` | 0 | 0.023s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `6881b0a4415516ca61ea937555fa5ee43bdccd64052d33f7a9802f510db145e2` |
| `.venv/bin/python scripts/render_status.py --check` | 0 | 0.022s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `485f06b720baf95874f16d5c478136279d65d90e8afcb28082b71c94b3b4e334` |
| `.venv/bin/python scripts/validate_repo.py --strict` | 0 | 2.198s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `08e8a48f691c5a7b6c1e7979e89820c720965d02f4082d16a3352b1dd8075d99` |
| `bash scripts/ci.sh` | 0 | 118.092s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `a621b221879dd4abe882e6a7be847bac745f383bb03d36d0db3f7712643ddb03` |
| `git diff --check` | 0 | 0.004s | OFFLINE_LOCAL_DETERMINISTIC | PASS | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Unknown and unverified

- Hidden Benchmark isolation is policy/workspace-based, not proven OS-enforced.
- Clean-room controls do not prove legal or license compliance.
- Prototype effectiveness, quality, reliability, generality, safety, runtime, and production fitness remain unmeasured because no prototype was implemented or executed.
- Monetary, operator, queue, and future maintenance costs remain unknown.
- Remote PR review and merge remain human-controlled; this report neither approves nor merges PR #5.

## Next step

`PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION`. This report does not execute that phase.
