<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2 prospective Benchmark design

- Cohort: `R2-SEALED-COHORT-V2` / `17f7534d50940fbee223ad856c01af11aae0c02aa38f9d2e041b8e572c61ce9b`.
- Public conformance: `16` cases.
- Sealed synthetic: `36` cases.
- Future model-in-loop: `8` cases, not executed.
- Prospective/synthetic/no historical answers: `True` /
  `True` / `True`.
- Public/sealed exact, ancestry, semantic-template and transformation-closure overlaps:
  `0`, `0`,
  `0`,
  `0`.
- Isolation: `POLICY_AND_WORKSPACE_ISOLATED_NOT_OS_ENFORCED`; private values read: `false`.

Tracked artifacts expose opaque case IDs, aggregate commitments and oracle-interface hashes, never
hidden seeds or private oracle mappings. The vault is ignored and policy/workspace isolated, not
OS-enforced. A clean checkout may validate the tracked commitments with the vault unmounted; that
proves public-manifest consistency and non-leakage, not private-vault availability. A partial mount
fails closed. Future execution requires stronger denial and an access ledger.
