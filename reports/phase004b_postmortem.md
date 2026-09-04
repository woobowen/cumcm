# Phase 004B Postmortem

## Boundary

The RC2 first run was already frozen and remotely verified before answer unlock. The registry unlock
receipt binds freeze commit `b742e8e042a1e9f0c161806c89c1b5917abe5693`; first-run evidence remains
immutable. No commentary, awarded paper, published analysis, solution code, parameters, derivations,
or solution prose was accessed after unlock because no allowed reference URL could be safely located
without a prohibited solution-oriented search.

## Root causes

The terminal first-run gate was `RC_RUN_SUCCESS_SET_INSUFFICIENT`: all six preregistered Runs failed.
Five programs intentionally wrote structured diagnostic output and exited nonzero, but the RC2
executor recorded `failure=null`, so `seal-run` rejected otherwise preserved captures. This is a
critical, case-independent evidence bug and is accepted for one RC3 revision cycle.

The poor calibration/cooling behavior and empty feasible-pool exception belong to case-owned model
and optimization code. They are Development findings, not permission to place problem-specific
physics, coefficients, constraints, or branches in the formal Skill. The freeze tool's Skill-commit
versus execution-commit conflation was a repository evaluation-infrastructure defect; its pre-freeze
repair was tested and did not change formal Skill code or any Run.

## Decision

Only `GAP-004B-001` is accepted for formal Skill revision. The test is generic: a child writes a
diagnostic JSON object, exits nonzero, and must produce a sealable failed manifest. Three other gaps
remain outside the Skill. Reference review was deliberately empty, so the RC3 decision cannot be a
copy of or reaction to an external solution.
