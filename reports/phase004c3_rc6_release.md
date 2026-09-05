# Phase 004C3 RC6 release decision

Result: `RC6_RELEASE_REPAIR_BLOCKED`.

The RC6 candidate aligns its declared version surfaces and passed frozen neutral tests, historical
regressions, synthetic E2E, 30 negative scenarios, leakage/secrets/provenance checks, full local CI
and strict validation. Those passing results are retained as engineering evidence, not promoted to
a release.

Auditor 1 independently reproduced 13 invalid payloads accepted by the data-sufficiency, selection,
semantic and compatibility pure Gates. It also verified that the generic fresh completion path
hardcodes global selection, descriptive Claims, provided-empirical evidence and positive policy
exposure. These are non-compensable contract defects. Both authorized formal revision cycles have
already been used; a third Skill change is prohibited.

No `rc6_release.json` exists, the active release state remains
`0.2.0-competition-rc5-blocked`, and the live release-consistency checker remains `BLOCK`. The
fresh Validation input was not accessed and `next_phase_allowed` is `null`.
