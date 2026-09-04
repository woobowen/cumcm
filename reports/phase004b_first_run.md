# Phase 004B RC2 Answer-Sealed First Run

## Outcome

The unchanged `0.2.0-competition-rc2` Skill ran the registered 2020 A Development case while the
answer remained `SEALED`. Stages 1–8 passed. Stage 9 was blocked by
`RC_RUN_SUCCESS_SET_INSUFFICIENT`; stages 10–14 did not start. This is a frozen failed first run,
not a completed model, Validation result, or generalization claim.

## Stage record

| Stage | Status | Gate / evidence | Failure |
|---|---|---|---|
| PROBLEM_INTAKE | PASS | official problem/data hashes | — |
| REQUIREMENT_DECOMPOSITION | PASS | six traceable requirements | — |
| RESEARCH_AND_SOURCE_PLANNING | PASS | official-input-only ledger | — |
| ASSUMPTION_AND_SYMBOL_DEFINITION | PASS | units, states, controls, equations | — |
| DATA_AUDIT | PASS | 709 ordered observations; raw immutable | — |
| MODEL_PORTFOLIO_GENERATION | PASS | one-node, two-node, asymmetric one-node | — |
| BASELINE_DEFINITION | PASS | exactly one baseline | — |
| EXPERIMENT_DESIGN | PASS | three candidates × two seeds frozen | — |
| IMPLEMENTATION_AND_EXECUTION | BLOCKED | six RC2 captures; one failed manifest | `RC_RUN_SUCCESS_SET_INSUFFICIENT` |
| MODEL_COMPARISON | NOT_STARTED | upstream hard gate | blocked upstream |
| ROBUSTNESS_AND_SENSITIVITY | NOT_STARTED | upstream hard gate | blocked upstream |
| FINAL_RUN | NOT_STARTED | no successful eligible Run | blocked upstream |
| CLAIM_EVIDENCE_VALIDATION | NOT_STARTED | no Final | blocked upstream |
| MODELING_TO_PAPER_HANDOFF | NOT_STARTED | no Claim evidence | blocked upstream |

## Actual execution

All six planned Runs were executed by RC2 `execute`; none is eligible for Final. Baseline validation
RMSE was `63.16751794 °C`, asymmetric control `20.144894 °C`, and the surviving primary seed output
`48.37396765 °C`. These are failure diagnostics, not ranked scores. Baseline could not find a full
Q2/Q3/Q4 feasible solution. Primary seed `20260904` raised an empty Q4 feasible-pool exception.

Five nonzero-exit Runs wrote structured output but RC2 left `failure=null`; `seal-run` rejected them
with `RC_MANIFEST_OUTCOME_EVIDENCE_INCONSISTENT`. The exception Run carried failure evidence and was
sealed as a failed manifest. Captured execution time totaled `16.960106 s`; there were no retries,
output edits, or deleted failures.

## Boundary

Problem/archive hashes stayed current, the RC2 Skill tree stayed unchanged, and no solution,
commentary, awarded paper, solution code, blog, video, repository, or benchmark vault was accessed.
