# Phase 004C4 Competition RC7 release

Status: `COMPETITION_RC_RELEASED`.

- Project: `0.3.0-competition-rc7`
- Skill: `0.2.0-competition-rc7`
- Implementation: `cd02e61994b906364789c65609de695b6912f1c7`
- Skill tree: `0b0e001c6bd12d605ad1e1e3fbfb1e4e9b1486e045b9e81c3d4e15f7d9f8f056`
- Runner: `fda1db2fbc709ea85967a1363abd649fcc0111f2bd83b72e8bd65469cc478dc4`
- Release manifest SHA-256: `747d6c47d89855dcc0acddd96593d2076c28e26b1b3dbd90a1fad8425f058434`
- Release subject: `dff40dfd0100ee11c6cb7ddd1a8f7803313653bd`
- Release commit/remote SHA: `22abe92d2b5da2e3f1be3161e8376fb83b0cee0a`

The candidate checker passed 14 known probes, 6 adversarial tests, 17 neutral E2E tests, 57 frozen
RC6 neutral cases, 239 focused regressions, 2 synthetic cases, 30 negatives, anti-hardcoding,
discovery, leakage, secrets, full pytest (`2063 passed, 1 skipped`), strict 0/0 and local CI. Only
after that did the live version/state/manifest mutation occur; the live checker exited zero.

The first post-release full CI exposed a stale project-version allowlist in an old checker, not a
Skill change. Checker-only repair then passed full CI (`2063 passed, 1 skipped`, 309.12 seconds) and
kept the frozen Skill tree unchanged. RC7 release remains valid even though its subsequent fresh
Validation outcome is negative; release acceptance and generalization evidence are separate facts.
