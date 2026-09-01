<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R1 acceptance report

## Outcome

`FAILURE_AWARE_ADJUDICATION_COMPLETE`. Quality remains `EVIDENCE_INSUFFICIENT`; this is a complete
negative/limited-scope adjudication, not a successful quality Gate. The only permitted next route is
`PHASE-EVIDENCE-EXPANSION-002D`; Phase 003 remains locked.

## Frozen evidence and observed outcomes

- Freeze: `PHASE-002D-R1-INPUT-FREEZE-001` / `4a03c2d840e0defff8df87a9dae68b76a3b9bbcec279e5298c971771ebe91c85`.
- Original attempts: 28; no original attempt was rerun or edited.
- Taxonomy: 9 eligible successes, 9 valid-output oracle failures, 7 terminal policy failures,
  1 infrastructure-censored attempt and 2 harness-censored attempts.
- Slots: 24 total; 9 eligible-success, 14 terminal-negative and 1 harness-censored.
- Retry burden: 4; all attempts, costs and historical deviations retained.
- Observed cost: 6,228.480778 seconds, 5,726,854 input tokens and 272,461 output tokens;
  cached-input, reasoning-token and monetary cost remain `UNKNOWN`.

## Evidence scopes

- Quality: 2/4 balanced cases and depth 1/2 — `EVIDENCE_INSUFFICIENT`.
- Reliability: descriptive frozen-cohort evidence — `RELIABILITY_ONLY`.
- Outcome completeness: 23/24 slots across three resolved cases at depth 2.
- Component gaps: repeated oracle/policy gaps support specification work only.

## Decisions

| Decision ID | Decision | Accepted scope | Next phase | Hash |
| --- | --- | --- | --- | --- |
| DECISION-FAILURE-SEMANTICS-002D-R1 | AUTOMATED_ACCEPTED | POLICY_ONLY | PHASE-EVIDENCE-EXPANSION-002D | a779535ff2fbb8e1ef75a144ee49e4b373e2b93726ff543bf90491193b3e819b |
| DECISION-SLOT-RESOLUTION-002D-R1 | AUTOMATED_ACCEPTED | POLICY_ONLY | PHASE-EVIDENCE-EXPANSION-002D | 1681faf7fddce21b749bbbcba7adb8d703b56531ed12c30c820c847f00fe7c0e |
| DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1 | AUTOMATED_REJECTED | NONE | PHASE-EVIDENCE-EXPANSION-002D | 0ef9abf1f8a309f1d65bbcb3dc1e46f8904da7f9e40fafd1029f587ce99105c1 |
| DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1 | EVIDENCE_INSUFFICIENT | NONE | PHASE-EVIDENCE-EXPANSION-002D | f561cf10ec88287dd155d7df82a052a0df1d514afda03774460305a83fe5be8c |
| DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1 | AUTOMATED_ACCEPTED | RELIABILITY_ONLY | PHASE-EVIDENCE-EXPANSION-002D | 7868c12445014b3fa473ad2be9ff0938486a0d4528309ab2f174bcdabcd098c8 |
| DECISION-ARCHITECTURE-002D-R1 | EVIDENCE_INSUFFICIENT | NONE | PHASE-EVIDENCE-EXPANSION-002D | 3ea6c9c729b25bef7831b7aeed51fcc7c8e60f86649f51ec87699a0e387dd37f |
| DECISION-COMPONENT-READINESS-002D-R1 | AUTOMATED_ACCEPTED | SPECIFICATION_ONLY | PHASE-EVIDENCE-EXPANSION-002D | a5ef2fdf2882717006e8b97b04d5016b08b3200194c715c8b2516dd4144fc11f |

No architecture or base is selected. Accepted component specifications are
`accepted-versus-done-workflow-state`, `claim-evidence-support-gate`,
`hash-bound-reproducibility-manifest`, and `leakage-safe-model-comparison-gate`. They are not
implemented, integrated, production-ready or proven to improve outcomes.

## Audits, repair and replay

Five independent first-round audits produced two PASS and three RETEST_REQUIRED verdicts. Ten
serious findings were converted to deterministic tests and closed without rewriting native outputs.
The first Decision Auditor pass returned RETEST_REQUIRED for inconsistent reliability scope and
replay-consumer ambiguity; repair cycle 1 made canonical and wrapper scope identical and added two
executed tests. Cycles 2 and 3 closed two fail-closed evidence-catalog omissions. All intermediate
records remain preserved. Final independent Decision Auditor: `PASS`. Formal
audit: `PASS` / `900cebe0b5a4a6d998cd9d14976ddd25a1f397f44c84be8a0c0746d60c1ca0bd`. Five-variant replay is
`True` / `3ef8f6df426379167eeae22e39aa06384e83695e33b4d0a7b37c1dad7f5f713b`.

## Supplemental, API and training boundary

Supplemental authorization is `AUTOMATED_REJECTED` with zero slots and zero real model
starts. API key used: false. API billing used: false. Foundation-model training/fine-tuning: none.
Optimized objects: deterministic Python policy/validation/replay code, JSON Schemas, fixtures,
machine records, reports and documentation only. Third-party Skill execution/integration: none.

## Validation command ledger

| ID | Command | Exit | Seconds | Type | Result | Blocker | Evidence hash | Runs | Tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VAL-001 | .venv/bin/python -m ruff check . | 0 | 0.074879 | DETERMINISTIC | PASS | None | 82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18 | 1 | N/A |
| VAL-002 | .venv/bin/python -m ruff format --check . | 0 | 0.02899 | DETERMINISTIC | PASS | None | 84fd6d2a26bb00bb2194744cb140ad386ca2e05559f0c807b467a980e047d167 | 1 | N/A |
| VAL-003 | .venv/bin/python -m pytest -q | 0 | 24.347302 | DETERMINISTIC | 800 passed, 1 skipped | None | bb8fdc11b52fb8386f22564e5d565ee0479ac65eaa0b32caf60f6737eb14830c | 1 | N/A |
| VAL-004 | .venv/bin/python scripts/check_instruction_budget.py | 0 | 0.360714 | DETERMINISTIC | PASS | None | 2b21eb602acc7a5cc1980b51851461027e7ea44c7ee47f5ee1876f09bf483b83 | 1 | N/A |
| VAL-005 | .venv/bin/python scripts/check_skill_discovery.py --expected-name cumcm-modeling-evidence --expected-count 1 | 0 | 0.055968 | DETERMINISTIC | PASS | None | b9d2ff4e03913af0e2a32076010d4b8d6d2e30800fccfb4202ea8f4428265f75 | 1 | N/A |
| VAL-006 | .venv/bin/python scripts/check_contracts.py | 0 | 0.406811 | DETERMINISTIC | 54 schemas; 54 valid; 44 invalid rejected | None | 460ec09ee6add189a6541cc2a3b9e2dfe9234f0100a7cb9cfa499a083e9ad66b | 1 | N/A |
| VAL-007 | .venv/bin/python scripts/check_upstream_manifest.py | 0 | 0.098148 | DETERMINISTIC | PASS | None | 45f957b9d70a4e859d3f26f680c12c0cc277043fbeafd2887e4772060c826c04 | 1 | N/A |
| VAL-008 | .venv/bin/python scripts/check_answer_leakage.py | 0 | 0.025498 | DETERMINISTIC | PASS; 0 findings | None | d340485da43172c5cd09f19a05cbbaa022c11e5e8afee19a234ce5376d208d01 | 1 | N/A |
| VAL-009 | .venv/bin/python scripts/check_secrets.py | 0 | 0.580615 | DETERMINISTIC | PASS; 0 secret/private-path findings | None | 4cc2305e90f20d86dc33305aca8e90ba3512b04c714992a80c4b0b2b7796c897 | 1 | N/A |
| VAL-010 | .venv/bin/python scripts/freeze_phase002d_inputs.py --check | 0 | 0.078315 | DETERMINISTIC | PASS | None | 5eef1b11a7e65615a58bdbf1b937b1dba961d01bf74ba5687ac67588789f78f5 | 1 | N/A |
| VAL-011 | .venv/bin/python scripts/freeze_phase002d_r1_inputs.py --check | 0 | 0.04813 | DETERMINISTIC | PASS | None | 52e92be67db3f2a15631df64ee99f196125c7d737949d8d3f35744ad4f0ce286 | 1 | N/A |
| VAL-012 | .venv/bin/python scripts/classify_phase002d_attempts.py --check | 0 | 0.089851 | DETERMINISTIC | PASS; 28 attempts | None | df7284eb469ed6fa905b328cee0a5e8945ff8c290edf95e606f658c6596fa933 | 1 | N/A |
| VAL-013 | .venv/bin/python scripts/build_phase002d_slot_matrix.py --check | 0 | 0.087666 | DETERMINISTIC | PASS; 24 slots | None | 48f457fd8f12e241148c84baf17bb733b9eefe1ae7c6fb4e1ff2a37a334a8a4a | 1 | N/A |
| VAL-014 | .venv/bin/python scripts/audit_phase002d_retry_bias.py --check | 0 | 0.081864 | DETERMINISTIC | PASS; retry burden 4 | None | f002ae4423090072ef0d1551fa35e20eefce9ed522f1087edc53175c5306d247 | 1 | N/A |
| VAL-015 | .venv/bin/python scripts/check_phase002d_quality_sufficiency.py --check | 0 | 0.094265 | DETERMINISTIC | PASS; EVIDENCE_INSUFFICIENT | None | cb4fe2dc57a2c7343fd85155a3adc93f9b31014c2d23635e46b74f2d76ea73de | 1 | N/A |
| VAL-016 | .venv/bin/python scripts/check_phase002d_reliability_sufficiency.py --check | 0 | 0.092491 | DETERMINISTIC | PASS; SUFFICIENT_RELIABILITY_ONLY | None | 29fbfcec34040d836ac32b29e1581becc399ad1b8fc6ba28822652e558799b77 | 1 | N/A |
| VAL-017 | .venv/bin/python scripts/authorize_phase002d_supplemental_runs.py --check | 0 | 0.10995 | DETERMINISTIC | PASS; AUTOMATED_REJECTED; 0 starts | None | 9468a77089957e5b05be6b0b1421fa729ab1130cce3ccc7ce2724ccf7b105512 | 1 | N/A |
| VAL-018 | .venv/bin/python scripts/run_phase002d_supplemental.py --status | 0 | 0.110913 | DETERMINISTIC | PASS; model_start_count=0 | None | 9468a77089957e5b05be6b0b1421fa729ab1130cce3ccc7ce2724ccf7b105512 | 1 | N/A |
| VAL-019 | .venv/bin/python scripts/adjudicate_phase002d_r1.py --check | 0 | 0.140228 | DETERMINISTIC | PASS; 7 decisions | None | 83bc18c2ba9b2c72c6f2801587bec9e107e0a2d9be0a457b4e8ec039dc637e9f | 1 | N/A |
| VAL-020 | .venv/bin/python scripts/audit_phase002d_r1_decision.py --check | 0 | 0.101495 | DETERMINISTIC | PASS; replayable=true | None | 531ba77203baf1b1f524b68f11f15171edccacc3f07be8a34ba44aaabecad506 | 1 | N/A |
| VAL-021 | .venv/bin/python scripts/replay_phase002d_r1_decision.py --check | 0 | 0.082223 | DETERMINISTIC | PASS; 5 stable variants | None | e4a81f9e72c7d039abcb72a7822b3622a3f9dcab24017e8c919faac80aafc5cc | 1 | N/A |
| VAL-022 | .venv/bin/python scripts/summarize_phase002d_r1.py --check | 0 | 0.071836 | DETERMINISTIC | PASS; 14 reports | None | 7847fc846148c9d11ada7d5e5388f0bf4803153f2539ac9807e9b3eaf2969969 | 1 | N/A |
| VAL-023 | .venv/bin/python scripts/render_status.py | 0 | 0.019579 | DETERMINISTIC | PASS; generated | None | 6881b0a4415516ca61ea937555fa5ee43bdccd64052d33f7a9802f510db145e2 | 1 | N/A |
| VAL-024 | .venv/bin/python scripts/render_status.py --check | 0 | 0.019888 | DETERMINISTIC | PASS; current | None | 485f06b720baf95874f16d5c478136279d65d90e8afcb28082b71c94b3b4e334 | 1 | N/A |
| VAL-025 | .venv/bin/python scripts/validate_repo.py --strict | 0 | 1.308435 | DETERMINISTIC | PASS; 0 errors; 0 warnings | None | ad0e230df898ecbe0c3c70c6cf53e6692f3e093febc220b106f33f5ec15eb080 | 1 | N/A |
| VAL-026 | bash scripts/ci.sh | 0 | 25.762078 | DETERMINISTIC | PASS; 800 passed; 1 skipped; strict clean | None | 1c63ef0dcaba7c9a47e74d55c2b29178ac7d453d85570c10914d455d18767bfe | 1 | N/A |
| VAL-027 | git diff --check | 0 | 0.005404 | DETERMINISTIC | PASS | None | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | 1 | N/A |
| VAL-028 | git status --short --branch | 0 | 0.005053 | DETERMINISTIC | PASS; expected M9 worktree changes only | None | 1dc468cac2621fe70d63d268c910af02d0bf54e60f0d02685f32d08de5f27d3e | 1 | N/A |
| NATIVE-001 | native Subagent first-round audit orchestration | 0 | UNKNOWN_UNEXPOSED | NATIVE_SUBAGENT | 2 PASS; 3 RETEST_REQUIRED; 10 serious findings closed by tests | None | 658077c806d2d64cabebe09d3c482cabf2f1836bd13df729a51b29d56f7dfc6b | 5 | UNKNOWN_UNEXPOSED |
| NATIVE-002 | native failure-aware Decision Auditor orchestration | 0 | UNKNOWN_UNEXPOSED | NATIVE_SUBAGENT | PASS after 3 bounded repair cycles | None | 57b22acd2f7cb87dc479d74883c8963a8552a8126bfd6b3dc614ff4f3e2433d9 | 4 | UNKNOWN_UNEXPOSED |
| REAL-001 | Phase 002D-R1 targeted supplemental real Codex execution | 0 | 0 | REAL_CODEX | NOT_AUTHORIZED_ZERO_STARTS | None | 34185c867a27a31083679cdf88300be7f717c43cbebbe9acd4814cd6930f6127 | 0 | 0 |

## Formal boundary

`third_party_integrated=false`, `base_selected=false`, Skill capability `SCAFFOLD_ONLY`, selected
architecture `null`. Unknowns remain cached-input tokens, reasoning tokens, monetary cost, CPU,
queue/operator time, maintenance cost and future quality under a newly frozen acquisition design.
No next-phase work was executed.
