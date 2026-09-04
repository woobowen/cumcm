# Competition RC1 Architecture Decision

## Result

`DECISION-COMPETITION-RC1-ARCHITECTURE-003F-R1` selects
`ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL` for
`COMPETITION_RC_IMPLEMENTATION_ONLY`.

The selection rule was frozen before the repair result: select K1 if K1 passes all eight Gates;
otherwise select W1 if W1 passes all eight; otherwise block. K1 and W1 each passed 8/8, so the first
clause selects K1 and W1 remains evidence-only fallback. No score aggregation or Agent vote was used.

## Evidence

- Gate result: `evals/results/phase-003f-r1/minimum_competition_architecture_gate_result.json`,
  SHA-256 `07d4362f0c2d0c6b502bcae99748e18f825ded4662554fb860d4db483376b971`.
- 117 symmetric cases per candidate, 234 total; zero unhandled exceptions; input immutability PASS.
- K1 R1 tree hash: `35caf2809815e06a8f7d41840adddfe2d1600c1169d7e59d742b021be5df0ea8`.
- W1 R1 tree hash: `a7d90ade3d4a28ae2951a6596f43ad680f3be3387f5dd00f9ed4c8b4957dbfff`.
- New decision hash: `8b4c50dbe5f95ca04ceff4c489ae83dc3a4afa81e156e1f00f16b2ac65f25cbe`.

## Historical preservation

The old `DECISION-COMPETITION-MVP-ARCHITECTURE-003F` remains
`FAST_TRACK_IMPLEMENTATION_BLOCKED`; its artifact SHA-256 is
`70cd886ad2efb226769bb15a26d041554f12d24c2bf3acc8c87b90f6527156a1` and historical decision hash
is `2ed22c0e6ba08159077ae891bfb310947fa007e84dd38fdde2af54beeef25b5d`. The new decision does not
supersede or rewrite it.

## Bounded meaning

This decision does not assert `FULL_R3_VALIDATED`, `SEALED_STAGE1_PASSED`,
`STAGE2_EFFECTIVENESS_ESTABLISHED`, external validity, production readiness or monetary cost.
