# Phase 004B — 2023 C Cross-Case Regression

The immutable 2023 C first-run history was not rewritten. Its original RC2 Development aggregate
and ignored official inputs were reused only for regression. Input hashes for all four workbooks
and variant metadata exactly match the preserved RC2 evidence.

A fresh RC3 workspace ran all three preregistered statistical candidates through case-local
`execute`, immutable capture, `seal-run`, comparison, Final, Claim and `modeling-to-paper/v1`
handoff. The first command attempt was rejected before subprocess start with
`RC_CASE_EXECUTION_CODE_NOT_FROZEN` because the repository path rather than the frozen case-relative
path was supplied. No Run directory or result was created. The corrected frozen path produced:

| Candidate | Exit | Validation score | Output relationship to RC2 |
| --- | ---: | ---: | --- |
| `PIPELINE-SEASONAL-BASELINE` | 0 | 1.00000000 | identical hash |
| `PIPELINE-HIERARCHICAL-STOCHASTIC` | 0 | 0.95115654 | identical hash |
| `PIPELINE-NONPARAMETRIC-ROBUST` | 0 | 1.13927070 | identical hash |

The selected model and decision hash
`39c62b36f2fb4b28c10ce62722d5834f92b3348ea9abbf76345ef542626f880e` are unchanged. Final state is
`READY_FOR_PAPER_HANDOFF`; handoff SHA-256 is
`51c2cc8d9533543406faf80ee5d8d878d5380804efbe4092b4c8a606ccb63a77`.

Mutating only `state/variant_metadata.json` in a copied probe produces `STALE` with
`RC_UPSTREAM_DEPENDENCY_STALE` and a dependency chain through the experiment plan and all three
manifests. Thus executor, capture immutability, sealing, custom-code manifest binding, unlocked
Development boundary, handoff contract and Stress-style stale semantics did not regress.

This is cross-case Development regression, not a new blind evaluation. Machine evidence is
`evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002/cross_case_regression/cumcm_2023c_rc3.json`.
