# Competition RC1 Implementation

## Formal Skill

- Path: `.agents/skills/cumcm-modeling-evidence/`
- Version/capability: `0.2.0-competition-rc1` / `COMPETITION_RC`
- Selected architecture: project-authored K1 deterministic evidence kernel
- Assurance: `PUBLIC_DETERMINISTIC_AND_TWO_END_TO_END_SMOKES`
- Discoverable Skills: exactly one

The integration extracts only general K1 behavior: strict JSON/numeric boundaries, a single
per-case state truth, hash-bound reproducibility manifests, leakage-safe model comparison, exact
Claim support, transitive STALE propagation and the existing modeling-to-paper contract. Shadow
identity adapters, evaluator fixtures, architecture selection/audit code and W1 fallback code were
not copied into the formal Skill.

## Executable surface

The Skill has 14 business stages, 14 workflow files, four roles, 14 JSON templates, and one offline
CLI `scripts/cumcm_case.py`. Commands are `init`, `status`, `validate`, `manifest`, `claim-check`,
`compare-check`, `stale-check`, `finalize`, `handoff`, and `smoke`; mutation-capable paths provide
`--check` or `--dry-run`. Exit codes distinguish success, input, Gate, STALE, state and I/O failure.

The case state sequence explicitly separates `RUN_COMPLETED`, `RUN_VALIDATED`,
`EVIDENCE_VALIDATED`, and `READY_FOR_PAPER_HANDOFF`. Only `modeling_orchestrator` may write case
state; it cannot write the global project state or override deterministic Gate results.

Independent integration audit fault injection initially found seven declaration-trust bypasses.
They and subsequent exact-binding/parity fault replays were repaired together in the final allowed directed cycle
`FORMAL-SKILL-COMPETITION-RC1-REVISION-003`, commits
`7bb45d9b41c9f0348cba22f2ac64808f3f0c320c` and
`1f20179de7eb06ecab28edeb443f57087870da04`, plus configuration-binding commit
`2974c7179d0389fb3d5f36e0b0b40821dc609dd4` and trust-boundary commits
`af8e816b93068a52658b4453fd181dc2f46c3087`,
`f8011202503db3c93ab2cafca86d4a6eacd85276`, and
`6eb6aa120cec8883e6874856f7f472d086df2994`, plus experiment/direct-type boundary commit
`76217fe3fd2a1a10d50a16071efe9b2160d61d49` through the final exact-lineage, hostile-input,
STALE-chain and public-wrapper repairs ending at
`6dfaa0d938ada59fb4fa408c8e540cf8e51f7965` (all remote verified). The formal Skill tree SHA-256 is
`76dce0d6a63ab78bd38a21c27d40fba0b2d5242e3283ade8cdc0b7dfd809b8d8` under the recorded sorted
sha256sum algorithm. Independent replay exercised 5,960 hostile validator calls with zero exception,
input mutation or invalid-extension acceptance.

## Core controls

- Manifests read and hash every actual input, code and output file; `code_commit` must resolve to a
  Git commit, each code hash must match that commit's repository blob, aggregate hashes are
  recomputed, the canonical configuration payload must reproduce its hash, and the actual
  computation modules are bound.
  Configuration, seed, argv, cwd policy, allowlisted environment, outcome, failure/supersession,
  trusted capture/freeze and decision hash are also bound. Non-success attempts are retained but
  excluded from ranking.
- Comparison re-derives the freeze registry from candidate, baseline, split assignment, metric,
  direction, seed schedule, aggregation and selection rules. It requires an exact run-manifest
  ledger, complete candidate-by-seed matrix, successful baseline, retained reliability denominator,
  strict finite non-bool scores, output-bound metrics, exact decision hash/argmin/argmax and a single
  post-selection test access; time/group/target/future leakage and retry-until-success fail closed.
- The experiment-plan Gate independently requires the preregistered candidates to exactly match the
  accepted model registry, exactly one registered baseline, unique strict-integer seeds, a non-empty
  metric, and non-empty, unique, mutually disjoint train/validation/test assignments before execution
  can be authorized—even when an attacker recomputes every freeze hash.
- State loading rejects extra/sensitive fields and invalid history/evidence chains. Raw and processed
  data enter `evidence_bindings`; every transition performs an automatic dependency hash check.
- Claims bind run/manifest/input/code/config/output/decision hashes, final scope, current status and
  an exact registry of current evidence paths; contradictions, missing evidence, stale or broader
  wording block.
- Final result and handoff consume one generic hash-bound output evidence contract rather than
  prediction/optimization-specific schemas. The existing `modeling-to-paper/v1` package is rebuilt
  canonically from accepted requirements, sources, data audit, model registry, comparison,
  robustness, selected output, Claim and reproduction evidence. A `general` contract regression
  proves this path is not overfit to the two smoke cases.
- STALE audits revalidate manifest input/output/code dependencies, emit a dependency chain in check
  mode, and are idempotent after the terminal transition.
- Direct validators normalize untrusted container types and return a deterministic BLOCK rather than
  raising; Claim IDs must satisfy the explicit `CLAIM-*` identity contract. Public `claim-check` and
  `compare-check` validate wrapper type/status/hash before unwrapping, while raw contracts reject
  unknown or sensitive extensions.

The current trusted execution registry is deliberately fixed to the two bundled deterministic
modules, `scripts/cumcm_case.py` and `scripts/synthetic_cases.py`. RC1 does not claim secure dynamic
capture for a caller-supplied custom executor; that capability requires a future frozen design.

All code is clean-room project-authored and standard-library-only inside the formal Skill. No
third-party candidate code, historical answer or API dependency is present.
