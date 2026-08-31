# Automated adjudication runbook

1. Verify branch/PR/preconditions and run the baseline suite.
2. Freeze Phase 002 evidence with `scripts/freeze_phase002_evidence.py`.
3. Reclassify/rescore with `scripts/rescore_phase002a.py`; inspect balanced cases and repeats.
4. Run mock, unit, integration, fault-injection, contract, leakage, secret, and strict checks.
5. Run adversarial synthesis, then isolated Blind Judges and Dissent. Never expose identities or peer
   outputs; raw JSONL stays ignored.
6. Convert every serious finding to a deterministic test or `NON_TESTABLE_CLAIM` uncertainty.
7. Run Meta only after valid Blind outputs and tests. Run Auditor only after Meta emits a decision.
8. Replay from frozen records, generate reports, then let the main agent update formal state.

For recovery, first verify the input freeze, build/check all six compact bundles, then use the
versioned recovery config. The orchestrator validates each checkpoint before unlocking the next
role. Exact-session resume and App Server fallback are governed by the configured per-role/global
budgets; never use `resume --last` or spend a third start for a two-start role.

```text
.venv/bin/python scripts/freeze_phase002b_inputs.py --check
.venv/bin/python scripts/build_adjudication_bundles.py --check
.venv/bin/python scripts/run_blind_adjudication.py --config adjudication/configs/phase-002b-v2.yaml --transport auto --resume --remaining-real-run-budget 8
.venv/bin/python scripts/run_meta_adjudication.py --config adjudication/configs/phase-002b-v2.yaml --check
.venv/bin/python scripts/audit_automated_decision.py --config adjudication/configs/phase-002b-v2.yaml --check
.venv/bin/python scripts/replay_automated_decision.py --config adjudication/configs/phase-002b-v2.yaml --check
```

If the chain terminates, run `scripts/finalize_phase002b_recovery.py`, generate the Phase 002B
summary, keep `next_phase_allowed=null`, and stop. Phase 002B terminated after two Correctness
`RESPONSES_CONNECT_RESET` failures; the later commands above correctly remain blocked. Do not run
Meta, Auditor, replay, or decision generation until all required predecessors validate.
