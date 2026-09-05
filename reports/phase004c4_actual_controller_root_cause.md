# Phase 004C4 actual-controller root cause

## Starting defect

RC6 had strict helper functions, but the executable completion path in
`scripts/finalize_fresh_c_validation.py` bypassed their semantics. It selected one global candidate,
mapped that Run to every requirement, constructed descriptive Claims, defaulted evidence to
`PROVIDED_EMPIRICAL`, assumed positive policy exposure, and completed a handoff from objects that the
formal controller itself had invented. Helper PASS therefore did not establish controller PASS.

The five inherited blocker classes were data-acquisition fail-open, portfolio-selection fail-open,
semantic-binding fail-open, vacuous compatibility, and ineffective per-requirement execution. The
13 frozen CLI probes reproduced all five: two cases returned only a coarse late handoff rejection;
the other eleven incorrectly exited zero.

## Changed control flow

Implementation commit `cd02e61994b906364789c65609de695b6912f1c7` makes the controller read
requirement, source, audit, sufficiency, plan, capture/manifest, comparison, requirement-selection,
semantic, final and handoff facts from authoritative artifacts. It executes ordered Gates for
requirements, sources, sufficiency, comparison/selection, Run eligibility, compatibility,
semantic Claims, aggregate mapping, finalization and handoff. Missing or inconsistent data is a
structured BLOCK; there is no fallback to global selection, descriptive evidence, empirical
classification or positive policy exposure.

The post-audit repair additionally removes split comparison/selection truth, defers manifest writes
until pre-final Gates and selected payload validation pass, binds scenario identity in capture and
manifest, and requires policy exposure/benefit/cost in the selected Run output. One audit-triggered
repair loop was used out of three.

## Fresh-case finding

The repair closes the preregistered controller attacks, but the 2017 fresh episode exposed a new
interface gap. The frozen `execute` command can pass only case root, Run ID, candidate ID, seed, code
path and timeout. An honest development output therefore contains no authorized final-test payload.
The completion controller nevertheless requires `sealed_test_metrics_b64` in the selected output
inside `GATE_FINALIZATION`. All earlier Gates passed, then finalization blocked and handoff was not
reached. The controller emitted only `RC_GATE_EXECUTION_FAILED`, which is fail closed but too coarse.

This is a generalizable RC7 finalization-interface defect. It is not repaired in the terminal case:
the frozen one-shot, code, Skill and verdict remain unchanged, and the next route is 004C5.

The read-only integrity audit also exposed a separate semantic cross-binding gap. The frozen
case-local post-selection builder unconditionally asserted REQ2 `held_out_test_valid=true`; the
selected output states `DEVELOPMENT_GROUPED_OOS`, `NOT_AUTHORIZED/0` test access and
`held_out_test_valid=false`. The semantic validator accepted the unsupported declaration. This
post-freeze `HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION` challenge is recorded without changing the
terminal artifacts and must be repaired on new evidence in 004C5.
