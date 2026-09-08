# RC8 delivery and recovery ledger

This is a current-work recovery aid, not a second state source or a release decision. Formal
candidate truth remains `qualification/rc8_candidate_snapshot.json` and its accepted decision;
case outcomes remain each case's `terminal/decision.json`, mirrored in the registry/live state.

## Immutable subjects and outcomes

- Shared Skill, runtime, controller, rules, contracts and tests: `29cf1d7566809519ca92b6a29f555ce0c0b5b204`,
  772 mapped files. Observed Python/package versions are in `qualification/environment.json`.
- RC8 accepted activation: `8ef732b45cf3cb04262317cdfa13a176b47eebe0`, remotely verified before input.
  Scope is research/fresh Validation eligibility. It is not contest acceptance or generalization.
- 2016 case code: `bee0a94cd0b04a17ceaf80830d482ac91366de1e`; pre-run freeze:
  `b71d00fc8944784c5213ba468d3e85afaed47949`, remotely verified before two actual model captures.
- 2016 terminal: `a03597be9a83a38ce4bcc4dba76cf8c574327045`, remotely verified. Evidence insufficient;
  three questions have conditional numerical outputs, but formal Final/handoff were not accepted.
  Native audit PASS endorses this negative decision. Do not restart, tune or rerun the terminal case.
- 2015 code675b37c and pre-run6f01263 were remotely frozen before numeric captures. Its full
  episode ran from21:53:34Z to a23:53:34Z deadline; formal terminal was fixed23:13:18Z, then
  remotely delivered in6be924e7903a201236a9cdd93ee75d66b839d1d6. FAILED for formal Final
  prerequisite ordering; two actual models,99 conditional windows,Final1/test0 remain preserved.
  Native first audit FAIL and separate Decision Auditor PASS of the negative proposal are distinct.
- Both cases are now terminal. Planned2/started2/executed2/completed2/scientificPASS0. No more
  fresh model/Final executions, answer unlocks or shared mutations under these episodes.

## Current CI blocker and safe recovery boundary

Candidate-subject CI actually passed 2153 tests with 1 skip and all post-checks. Subsequent fresh
registration exposed a separate delivery failure: `test_case_registry_declares_required_training_fields`
asserts exactly eight historical IDs. The registry now correctly contains the two new cases as well.
An initially missing-field error in the first new case was fixed and reverified; the fixed-count
assertion remains failing. `qualification/post_activation_ci_44c5ebd.json` preserves that observation.

The first terminal commit also exposed a fault-injection test that routes every evidence-insufficient
terminal to the historical004C2 phase; the schema permits the actual004C5 terminal. A new-case
`first_run_evidence` summary was missing and is now populated from the existing fixed decision,
with no result changes. The actual terminal-head CI observed2150 passed/3 failed/1 skipped;
`delivery/ci_a03597b_observation.json` identifies all three.

Current local6be924e full CI is2151 passed/2 failed/1 skipped. Remote Actions34289738652
actually checked out PR merge commit22c097256777009083e107768992c14de822685b and returned the
same counts. The missing registry summary is fixed; the two historical assertions remain open.
Fifteen separately executed post-CI checks all pass without changing full CI FAIL. See delivery/.

Both outdated tests are in the frozen 772-file mapping. During both Validation episodes no shared
or test file can be edited. Do not delete/move cases out of the authoritative `cases` collection,
skip the test, edit old manifest hashes, or label old passing CI as current-head CI. A future repair
must retain checks on all historical cases and validate newly registered cases without a hardcoded
closed-world count. It must also explicitly handle historical qualification subjects versus the
newly tested maintenance subject; blindly editing this test would make the current RC8 checker
correctly report `RC8_CANDIDATE_CURRENT_IMPLEMENTATION_DRIFT`. This ledger grants no hash exception.

After interruption, first inspect the current case's episode deadline and whether its candidate or
terminal is fixed. Check actual Run/Final ledgers before any execution. Final budget is never inferred
from a missing controller `attempts` entry. If a fixed terminal exists, only read-only inspection is
permitted; future model work needs separately registered Development scope and cannot revise the
Validation denominator or verdict.

## Scientific observations retained for later neutral repair design

The 2016 native audit contains both numerical checks and scientific dissent. Its original JSON and
report are published byte-exact; private-path views are marked derived, and restricted raw tool
outputs remain ignored with hashes and separate published numerical outputs.

1. Unknown future outcomes are not ordinarily required *inputs* to make a conditional prediction.
   Distinguish feasibility of making a forecast, evidence supporting its assumptions, demonstrated
   target accuracy, and compliance with a frozen final-evaluation protocol. Do not convert this
   observation into automatic predictive acceptance.
2. Same-entity history can be legal information for a conditional temporal target. A later repair
   needs both a positive temporally ordered same-entity case and a negative future-label leakage
   case, while retaining independent-entity exclusion for external-population claims. It must not
   replace all group checks with a permissive flag.
3. Selection and acceptance metrics must use the requested target quantity and denominator.
   Error in elapsed time and relative error in remaining time differ, even when ranking happens
   to agree. Existing-vector audit diagnostics do not authorize selecting a new model after freeze.
4. Model arithmetic and independent residual checks establish calculation consistency. They do
   not calibrate an uncertainty interval, prove transfer across entities or validate a physical
   perturbation's interpretation. Scientific objections can remain material without a unit test.
5. Planned timestamps and local candidate statuses are not actual execution or formal stage truth.
   Preserve misleading frozen metadata and attach a correction; never silently rewrite history.

These are observations for a subsequent neutral design. They are not new implementation, new tests,
new pass outcomes or instructions supplied to the active 2015 worker.

## Reproduction and publication limits

Use the existing `.venv/bin/python`; no dependency installation or global configuration mutation
has occurred. The observed environment is not a fresh-install or cross-platform lockfile. Raw
problem/data archives remain immutable and ignored. Public artifacts contain first-party code,
derived outputs, hashes and source/Run links. Reacquisition requires checking the recorded hashes;
restricted raw input is never pushed to make a package superficially self-contained.

The only added Git configuration is one case-local `.gitattributes` rule in each of2016/2015 that recognizes
CSV CRLF as a line terminator while still rejecting spaces before CRLF. It preserves the frozen
CSV bytes; its positive and negative checks are recorded in that case's terminal delivery note.

Required delivery checks are current-head full CI, strict repository validation, generated-status
freshness, whitespace checks, ordinary push and a separate actual remote-SHA read. A merge-tree
success is recorded separately and is not merged-result CI. PR #12 remains Draft; no ready/merge
or direct main push is authorized.

## Supplemental proof and next maintenance subject

The2021 Q4 proof consumes the ninth/9 Development numerical attempt. Code/protocolbf34549
was remotely verified before construction; resultsee8bf9d remain frozen. Native review PASS is
limited to the fixed serialized-decimal first-objective LP. The strict outward display interval is
[40246.40307264614,40246.40311289260]m3/week; exact Fractions remain authoritative. See
`development/q4_certificate/AUDIT_DISPOSITION.md`; no original model was rerun or Gate accepted.

The2015 negative terminal exposes a reproducible protocol dependency cycle: comparison before
Final is required, while NONPREDICTIVE comparison requires one scientific Final verification.
Do not repair it by editing a fixed trace or letting READY override the Gate. A new maintenance
subject must freeze neutral prerequisite-order and positive nonpredictive end-to-end expectations
before shared implementation changes. Also preserve temporal same-entity positives, future-label
leakage negatives and historical/new-case phase tests. This is future repair design, not implemented
code or permission to rerun these fresh terminals. Comprehensive findings are in FINAL_REPORT.md.
