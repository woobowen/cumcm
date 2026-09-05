# Phase 004C3 neutral tests

The frozen matrix contains one completeness/anti-hardcoding meta-test and 56 behavior cases: 11
release, 17 data/acquisition, 10 selection, 11 semantic and 7 compatibility cases. Its SHA-256 is
`242963976022ba7449fbd8ea8488cd65acd4a05744d3f7ee88344c81a76c7adc`.

Before implementation, all 56 behavior cases failed because the new checker/functions were absent.
After the two bounded repair cycles, all 57 tests pass. The frozen test file was not edited during
implementation and contains no historical problem/year/domain identifiers.

Auditor 1 demonstrated that the frozen matrix is insufficient for release acceptance: 13 additional
case-neutral invalid payloads are accepted. The original test SHA remains immutable; the findings
are captured separately rather than retroactively editing the frozen expectations.
