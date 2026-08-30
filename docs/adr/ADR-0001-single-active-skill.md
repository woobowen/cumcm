# ADR-0001: Single active Skill

## Context
Multiple complete Skills would compete for discovery, state, gates, and instruction budget.
## Candidates
One router Skill; several active full Skills; manual prompt assembly.
## Decision
Expose exactly one `cumcm-modeling-evidence` Skill and evaluate upstreams as isolated inputs.
## Evidence
Official Codex discovery does not merge duplicate names; project requirements demand one authority.
## Rejected alternatives
Multiple full Skills and manual concatenation create conflicts and untraceable behavior.
## Consequences
Components require explicit integration decisions and tests; the router stays concise.
## Revisit conditions
Only if the host gains a verified composition mechanism preserving unique state/gates and tests demonstrate benefit.
