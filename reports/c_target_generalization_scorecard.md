# C_TARGET_GENERALIZATION_SCORECARD

No weighted total is reported; hard Gates remain noncompensable.

## Evidence accounting

| Metric | Value | Scope/qualification |
| --- | ---: | --- |
| Independent C problems with execution evidence | 5 | 2023 C, three batch C cases, 2024 C Validation |
| `independent_c_first_runs` | 4 | Three Phase 004C batch first runs plus one distinct Validation first run |
| `strictly_blind_c_first_runs` | 4 | Process-strict answer/reference sealing; model-prior exposure remains unverifiable |
| Batch `first_pass_ready_count` | 1/3 | Only 2020 C reached accepted handoff under RC3 |
| Batch first-pass completion rate | 33.33% | `READY_FOR_PAPER_HANDOFF` denominator is three batch cases |
| Phase 004C strict end-to-end handoff rate | 25.00% | One accepted handoff across batch + Validation; Validation handoff blocked |
| Mean requirement coverage | 100% | Design/run-output scope; does not imply Claim/handoff acceptance |
| Main-question miss count | 0 | Batch and Validation output coverage |
| Valid Run ratio | 23/25 = 92.00% | 19/21 batch plus 4/4 Validation |
| Batch hard-failure count | 1 | 2022 late output-contract failure |
| Validation hard-failure count | 0 | Separate frozen Claim Gate blocker, not one of 12 rubric hard failures |
| Manual intervention count during Run phases | 0 | Batch and Validation |
| Cross-case repeated failure count | 1 | Output-contract preflight gap |
| Universal hard failure count | 1 | Same gap when discovered after sealing |
| Accepted general Skill changes | 1 | Single RC4 change set |
| Rejected problem-specific/reference changes | 5 | No Skill mutation |
| Cross-case regression pass rate | 100% | All registered regression scopes passed |
| Validation result | `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT` | Claim Gate block; no handoff |
| Validation handoff completeness | 0% | Not reached |
| Professional modeling audit | `PARTIAL_NUMERIC_SUCCESS_EVIDENCE_CHAIN_REJECTED` | See dedicated audit |

## Contest efficiency

Batch median time to first baseline was `1968.305244 s`; median time to first valid result was
`2441.0 s`. Only one batch case reached handoff, at `2210.663201 s`; a completion-only median is
therefore that value with coverage 1/3, while an all-case median is undefined. Batch case
registration-to-freeze windows were 56, 73, and 109 minutes. The 2024 C Validation reached terminal
freeze in `3219 s` of its `14400 s` limit; the four model subprocesses summed to `4.248546 s`.

## Five separate judgments

- Engineering generalization: PASS for execution capture, failure retention, preflight, hashing,
  STALE, and regression; FAIL for the frozen multi-requirement Claim-scope contract.
- C-problem modeling generalization: PARTIAL. Five independent C problems and diverse structures are
  represented, but only one RC3 batch case reached handoff and Validation did not pass.
- Contest efficiency: PASS time bounds, but stage timing is incomplete for some early stages and
  recovery effort is not fully instrumented.
- Evidence reliability: PASS through Final Candidate in Validation; terminal Claim/handoff chain
  rejected exactly as required.
- Validation evidence: INSUFFICIENT. Numeric/feasibility evidence is strong, but formal Claim and
  handoff requirements are unmet.
