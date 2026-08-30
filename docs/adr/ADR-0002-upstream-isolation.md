# ADR-0002: Upstream isolation

## Context
Candidate repositories may contain executable instructions, hooks, dependencies, answers, or mixed licenses.
## Candidates
Install directly; vendor into Skill; shallow-clone to ignored cache; inspect only online.
## Decision
Resolve and shallow-clone only under ignored `.cache/upstream/<id>/`; never execute during foundation.
## Evidence
Isolation preserves exact commit evidence without polluting discovery/index/history.
## Rejected alternatives
Direct install/vendor is unaudited; online-only inspection is not reproducible enough.
## Consequences
Tracked reports store summaries/hashes/paths, not full repositories.
## Revisit conditions
Dynamic phase may execute a cleared candidate only in a separately approved sandbox plan.
