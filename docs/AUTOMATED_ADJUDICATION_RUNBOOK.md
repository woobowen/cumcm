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

If transport fails, retry at most three repair cycles. After the third failure, record
`AUTOMATED_ADJUDICATION_INCOMPLETE`, keep `next_phase_allowed=null`, and stop. Current continuation:

```text
.venv/bin/python scripts/run_blind_adjudication.py --config adjudication/configs/phase-002a.yaml
```

Do not run Meta, Auditor, or decision generation until all required Blind outputs validate.
