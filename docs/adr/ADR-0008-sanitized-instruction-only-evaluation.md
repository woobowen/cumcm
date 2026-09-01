# ADR-0008 — Sanitized instruction-only upstream evaluation

Status: Accepted for Phase 002

## Context

Candidate repositories contain scripts, installers, hooks, external services, generated execution,
paper material, historical examples, and incomplete license boundaries. Executing or installing
them would expand the trust boundary and can contaminate benchmarks or the project environment.

## Decision

Do not execute third-party code or install candidate Skills/dependencies. Build cache-only packages
from an explicit allowlist of Markdown/YAML/JSON/TXT inputs at pinned commits. Reject executables,
code, hooks, downloaders, MCP configuration, answers, papers, example results, and unsafe or
inseparable content. Normalize only a small temporary instruction subset and record included and
excluded paths, SHA-256, security, license, contamination, and limitations. No candidate text is
tracked.

## What this can prove

It can estimate whether selected textual workflow concepts change structured agent behavior on the
fixed synthetic tasks under the tested Codex model/configuration.

## What this cannot prove

It cannot prove the full upstream Skill works, its scripts are safe/correct, its historical claims
are true, its content is legally reusable, or the same effects hold on real CUMCM problems.

## Consequences

Results can support only a proposal. Direct copying, forking, installation, or integration remains
blocked pending license/security review, clean-room design where required, tests, and human approval.
