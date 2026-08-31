# Component Portfolio Proposal

Status: `HISTORICAL_PROPOSAL_ONLY`; superseded by Phase 002A machine decisions.

| Mechanism | Source | Commit | Actual observed gap | Measured or expected benefit | Reuse mode | License | Contamination |
|---|---|---|---|---|---|---|---|
| `accepted-versus-done-workflow-state` | aris | `94d8093ed21d20a790830318190095b9f5036ce8` | Every arm failed most CASE-005 dependency-freshness checks, with deterministic scores of 7, 7, and 0 and no persisted workflow state or closure artifact. | Expected to raise the uniformly weak CASE-005 state result by making freshness and recovery mechanically observable rather than narrative. | `CLEAN_ROOM_REIMPLEMENT_CANDIDATE` | MIT_ROOT_WITH_SUBRESOURCE_GAPS | MEDIUM because examples and a binary community paper were not fully reviewed; exclude all example content. |
| `claim-evidence-support-gate` | aris | `94d8093ed21d20a790830318190095b9f5036ce8` | CASE-006 deterministic scores ranged from 13 to 40; every arm missed multiple source-limit, assumption, retain/modify/remove, fact, or non-causal checks and none persisted a hash-bound claim map. | Expected to close the persistent claim-map gap and make the CASE-006 evidence failures machine-detectable without treating reviewer votes as proof. | `CLEAN_ROOM_REIMPLEMENT_CANDIDATE` | MIT_ROOT_WITH_SUBRESOURCE_GAPS | MEDIUM because examples and binary resources were not fully reviewed; no upstream examples or prose may enter tests or prompts. |
| `hash-bound-reproducibility-manifest` | xiaoma-math-modeling-skill | `5a85fe34ca1d075872e95556b122c8979984d322` | Across CASE-001, CASE-002, CASE-003, CASE-004, and CASE-006, Reviewer findings repeatedly reported missing code, result, audit, claim-map, hash, or recovery artifacts. | Expected to eliminate the repeated missing-artifact and missing-hash findings; benefit must be remeasured on CASE-001/002/003/004/006 in Phase 003. | `CLEAN_ROOM_REIMPLEMENT_CANDIDATE` | UNKNOWN_ROOT_WITH_RESTRICTED_VENDOR_SUBTREES | HIGH because contest example assets exist; only the abstract field contract may inform a clean-room specification. |
| `leakage-safe-model-comparison-gate` | kdense-scientific-agent-skills | `f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f` | In CASE-004 all three arms omitted required robustness evidence and either used the test set in selection or selected a model inconsistent with their stated validation objective; deterministic scores were only 25 to 28. | Expected to prevent the test leakage observed in two arms and the validation-rule mismatch in the third while closing the six robustness checks missed by every arm in CASE-004. | `CLEAN_ROOM_REIMPLEMENT_CANDIDATE` | MIT_ROOT_WITH_PER_SKILL_METADATA_GAPS | LOW by static text search for the selected concepts, but binary and corpus review is incomplete. |

Every card requires a project-native clean-room specification, new implementation,
Schema-bound state/evidence integration, and the negative tests listed in the card. No source
file, prose, dependency, tool declaration, template, example, or asset is approved for copy.

## `accepted-versus-done-workflow-state`

- Source files: `tools/run_state.py`, `tests/test_run_state.py`
- Security risk: The upstream contains shell, Git, remote execution, installer, and updater paths that are prohibited; source execution and wholesale adoption are excluded.
- Integration conflict: The upstream .aris state is a competing truth and must not be ported; only a clean-room transition rule may extend state/project_state.json ownership.
- Maintenance cost: `MEDIUM`; confidence: `MEDIUM`.
- Clean-room work:
- Specify state transitions from CASE-005 oracle behavior and project WORKFLOW.md.
- Use only the existing formal state and ledgers; do not create .aris or another controller.
- Preserve human approval gates and fail closed on missing hashes or evidence.
- Required tests:
- Exact valid/STALE closure for input, config, code, final-run, paper, and unrelated-branch mutations.
- Crash and resume before done, after done, and after accepted.
- Reject AUTO_PROCEED, FAIL-continue, and skip-on-done behavior.
- Ensure upstream changes transitively mark dependent artifacts STALE.

## `claim-evidence-support-gate`

- Source files: `tools/evidence_check.py`, `tests/test_evidence_check.py`, `skills/result-to-claim/SKILL.md`, `skills/shared-references/review-scope-limits.md`
- Security risk: The upstream whole package contains shell, Git, MCP, network, and remote execution behavior; only the abstract separation of checks is admissible.
- Integration conflict: Porting the upstream review pipeline would duplicate evidence and state truth; the mechanism must extend existing Source/Claim/Run contracts and human gates.
- Maintenance cost: `MEDIUM`; confidence: `MEDIUM`.
- Clean-room work:
- Use project-authored terminology, Schema, fixtures, and synthetic claims.
- Keep mechanical existence/hash validation separate from read-only semantic review.
- Preserve main-agent ownership and required human approval for evidence-package acceptance.
- Required tests:
- Reject missing, stale, hash-mismatched, and path-escaping evidence references.
- Reject unsupported causal/final claims and preserve conflicting sources.
- Verify CASE-006 retain, modify, remove, assumptions, limits, and non-causal outcomes.
- Prove reviewer output cannot mutate claims or approve the human Gate.

## `hash-bound-reproducibility-manifest`

- Source files: `references/roles/编程手/scripts/repro_manifest.py`, `tests/test_reproducibility.py`
- Security risk: Upstream root is unlicensed and includes network/compiler/vendor surfaces; no source or tool may be executed or copied.
- Integration conflict: A parallel manifest would duplicate project Run and state truth; fields must be added to native contracts and generated reports only.
- Maintenance cost: `MEDIUM`; confidence: `MEDIUM`.
- Clean-room work:
- Derive requirements only from the pinned static review and observed evaluation gap, not source text.
- Implement in project-native contracts with new names, tests, and provenance.
- Exclude all vendored tools, assets, templates, and contest examples.
- Required tests:
- Reject a missing input, script, output, seed, command, environment, or Git binding.
- Detect content mutation and propagate STALE transitively.
- Rebuild the same manifest deterministically from the same Run.
- Prove no private paths, credentials, raw traces, or third-party text enter the manifest.

## `leakage-safe-model-comparison-gate`

- Source files: `skills/experimental-design/SKILL.md`, `skills/experimental-design/references/randomization_and_blocking.md`, `skills/statistical-analysis/references/assumptions_and_diagnostics.md`, `tests/experimental-design/test_scripts.py`, `tests/statistical-analysis/test_scripts.py`
- Security risk: The upstream pool has broad tool permissions, install instructions, optional network Skills, and unresolved security findings; no code, dependencies, or tool declarations may be imported.
- Integration conflict: Installing the 163-Skill pool would create routing, dependency, and state conflicts; the gate must be a native contract, not another Skill.
- Maintenance cost: `HIGH`; confidence: `HIGH`.
- Clean-room work:
- Derive acceptance behavior from the CASE-004 oracle and project experiment contracts.
- Reimplement only deterministic gate semantics; do not copy scripts, prose, assets, or dependencies.
- Bind all split and selection decisions to Run IDs and immutable hashes.
- Required tests:
- Fail when test metrics influence selection or appear before model freeze.
- Fail when the selected model violates the declared validation objective.
- Require naive and domain baselines, temporal split, drift, robustness, randomization, failed-run retention, and uncertainty evidence.
- Verify deterministic tie handling and append-only correction behavior.

## Rejected or deferred

- Whole upstream base or Skill-pool adoption: scope, state, security, license, and contamination conflicts.
- Network OCR/search, MCPs, installers, updaters, remote queues, or Git automation: outside the offline evaluation and safety boundary.
- Paper-writing and document-lint workflow: outside modeling scope and not tied to a measured Phase 002 gap.
- Subjective judge panels or agent votes: cannot constitute mathematical or experimental evidence.
- A second total controller, state tree, or evidence ledger: violates the single source-of-truth architecture.
