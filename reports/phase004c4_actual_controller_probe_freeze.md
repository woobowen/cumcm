# Phase 004C4 actual-controller black-box probe freeze

## Frozen boundary

- Freeze ID: `PHASE-004C4-ACTUAL-CONTROLLER-BLACK-BOX-FREEZE-001`
- Base commit: `d191fb47c07ec8a8115d83909fefa53966fbcc03`
- Actual entrypoint: `scripts/finalize_fresh_c_validation.py`
- Probe matrix: `evals/results/phase-004c4/frozen_actual_controller_probe_matrix.json`
- Probe count: 13

The probes invoke the repository's actual fresh-case completion controller as a subprocess
against isolated project-original cases. They do not call a replacement validation helper in
place of the controller.

## Frozen expectations

Every probe requires a nonzero exit, `BLOCK_NATIVE_CONTRACTS`, its gate-specific stable reason
code, immutable authoritative evidence and case state, and a self-hash-bound
`gate_execution_trace.json`. The trace must bind executed gates to inputs and outputs without
copying opaque source content. The case must remain `RUNNING`.

The matrix binds the exact controller, core, test, and fixture hashes. Test behavior is frozen
before any formal Skill or controller repair. Failures against the pre-repair controller are
expected-failure evidence, not acceptance evidence.
