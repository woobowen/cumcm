# Release policy

A contest release requires `CONTEST_RELEASE_READY`, clean strict CI, frozen Skill/version/contracts/rules, resolved BLOCKER/HIGH findings, benchmark contamination review, dependency/license ledger, reproducible environment, signed decision and human gate. Release manifests bind Git commit and hashes. Any dependency or Final Run change triggers `STALE` and a new version; generated reports alone cannot authorize release.
