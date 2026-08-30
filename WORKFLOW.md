# Formal state machine

This file is the sole normative source for project and contest-run states. Each row defines meaning; prerequisite; mandatory artifact; automatic check; independent review; human gate; allowed next state; and failure fallback.

## Project lifecycle

| State | Meaning | Prerequisite | Artifact | Automatic check | Review | Human gate | Next | Fallback |
|---|---|---|---|---|---|---|---|---|
| `INIT` | Repository not accepted | none | active plan | plan/schema checks | foundation reviewer | no | `FOUNDATION_READY` | `REJECTED` |
| `FOUNDATION_READY` | Foundation BLOCKERs pass | `INIT` | acceptance report | strict CI | independent acceptance | yes | `UPSTREAMS_INVENTORIED` | `STALE` |
| `UPSTREAMS_INVENTORIED` | Candidates have identities/commits | foundation ready | manifest | manifest validator | license/security reviewer | no | `UPSTREAMS_STATIC_REVIEWED` | `FOUNDATION_READY` |
| `UPSTREAMS_STATIC_REVIEWED` | Static evidence is complete/provisional | inventory | reviews/matrix | review schema | separate reviewer | yes | `BASELINE_SELECTED` | `UPSTREAMS_INVENTORIED` |
| `BASELINE_SELECTED` | Dynamic evidence selects base | static review + eval | decision record | eval validator | adversarial reviewer | yes | `COMPONENTS_SELECTED` | `UPSTREAMS_STATIC_REVIEWED` |
| `COMPONENTS_SELECTED` | Component portfolio chosen | base selected | component decisions | compatibility checks | security/license review | yes | `SKILL_PROTOTYPE_READY` | `BASELINE_SELECTED` |
| `SKILL_PROTOTYPE_READY` | Integrated prototype is runnable | components selected | versioned Skill | discovery/contract tests | independent behavior review | yes | `DEVELOPMENT_EVALUATED` | `COMPONENTS_SELECTED` |
| `DEVELOPMENT_EVALUATED` | Development cases pass rubric | prototype | dev eval results | eval checks | model reviewer | yes | `VALIDATION_EVALUATED` | `SKILL_PROTOTYPE_READY` |
| `VALIDATION_EVALUATED` | Frozen Skill passes validation set | development accepted | validation results | freeze/leakage checks | blind reviewer | yes | `HELD_OUT_EVALUATED` | `DEVELOPMENT_EVALUATED` |
| `HELD_OUT_EVALUATED` | Vault-governed held-out result exists | validation accepted | held-out report | vault/freeze checks | independent blind reviewer | yes | `CONTEST_RELEASE_READY` | `VALIDATION_EVALUATED` |
| `CONTEST_RELEASE_READY` | Release is frozen for contest | held-out accepted | release manifest | release CI | release reviewer | yes | `PROBLEM_INGESTED` | `STALE` |

## Contest-run lifecycle

| State | Meaning | Prerequisite | Artifact | Automatic check | Review | Human gate | Next | Fallback |
|---|---|---|---|---|---|---|---|---|
| `PROBLEM_INGESTED` | Immutable inputs registered | release ready | input manifest/hashes | input checks | requirement reviewer | yes | `PROBLEM_ANALYZED` | `REJECTED` |
| `PROBLEM_ANALYZED` | Questions/requirements traced | ingested | requirement trace | trace checks | prosecutor | yes | `DATA_VALIDATED` | `PROBLEM_INGESTED` |
| `DATA_VALIDATED` | Data quality/meaning accepted | analyzed | data audit | schema/data checks | data auditor | yes | `BASELINE_READY` | `PROBLEM_ANALYZED` |
| `BASELINE_READY` | Reproducible reference result | data valid | baseline model card/run | run checks | code verifier | no | `MODEL_CANDIDATES_READY` | `DATA_VALIDATED` |
| `MODEL_CANDIDATES_READY` | Competing models specified | baseline | candidate cards | contract checks | assumption prosecutor | yes | `MODEL_SELECTED` | `BASELINE_READY` |
| `MODEL_SELECTED` | Evidence-backed model chosen | candidates | decision | decision schema | independent model reviewer | yes | `IMPLEMENTED` | `MODEL_CANDIDATES_READY` |
| `IMPLEMENTED` | Code matches formalization | selected | verified implementation | tests/static checks | code verifier | no | `PILOT_RUN_READY` | `MODEL_SELECTED` |
| `PILOT_RUN_READY` | Pilot config/resources approved | implemented | pilot manifest | dry validation | experiment auditor | yes | `EXPERIMENTS_RUNNING` | `IMPLEMENTED` |
| `EXPERIMENTS_RUNNING` | Registered experiments execute | pilot ready | run ledger | run monitor | experiment auditor | no | `VALIDATED` | `PILOT_RUN_READY` |
| `VALIDATED` | Accuracy/assumptions checked | runs complete | validation report | metric checks | independent reviewer | yes | `ROBUSTNESS_CHECKED` | `EXPERIMENTS_RUNNING` |
| `ROBUSTNESS_CHECKED` | Sensitivity/uncertainty complete | validated | robustness report | coverage checks | robustness reviewer | yes | `FINAL_RUN_READY` | `VALIDATED` |
| `FINAL_RUN_READY` | Exact final runs frozen | robustness accepted | freeze manifest | hash/repro checks | reproducibility auditor | yes | `EVIDENCE_PACKAGE_READY` | `ROBUSTNESS_CHECKED` |
| `EVIDENCE_PACKAGE_READY` | Versioned handoff validates | final run | evidence package | handoff schema | paper-interface reviewer | yes | terminal | `FINAL_RUN_READY` |
| `STALE` | Dependency changed or superseded | any accepted state | stale record | dependency traversal | owner review | yes to clear | nearest valid predecessor | remain `STALE` |
| `REJECTED` | Evidence/gate irrecoverably fails | any | rejection decision | decision schema | independent reviewer | yes | new plan or terminal | remain `REJECTED` |

## STALE propagation

A changed raw/registered input invalidates all dependent audits, models, runs, metrics, and packages. A changed source invalidates dependent claims/decisions. A changed implementation/config/environment invalidates dependent runs. A superseded Final Run invalidates downstream tables, figures, claims, and handoffs. A changed upstream mechanism invalidates integration decisions and evaluations but not unrelated immutable evidence. Clearing `STALE` requires recomputation/review from the earliest affected predecessor plus recorded approval; labels may never be cleared by editing a report alone.
