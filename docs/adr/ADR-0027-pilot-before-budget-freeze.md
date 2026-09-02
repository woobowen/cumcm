# ADR-0027: Run a real calibration pilot before freezing the budget

Status: Accepted
Date: 2026-09-01

## Context

Model catalog visibility does not prove that the selected model can complete a structured run over
the intended transport. A budget based only on historical `gpt-5.4` observations would also omit
current transport and token behavior.

## Decision

Before any scored run, execute `CALIBRATION-PILOT-002D-001` with the selected real model, a compact
deterministic task, small output Schema, fresh ephemeral session, no remote, workspace-write, and
web/MCP disabled. The pilot is never primary evidence. Try `PROXY_INHERITED` first. Only one of the
four registered transport failures may authorize one new `NO_PROXY_PROCESS_ONLY` start; no resume
is allowed. Two failures block the cohort.

Freeze the attempt/token/elapsed budget only after a passing pilot. Monetary cost remains
`UNKNOWN` because the cohort uses ChatGPT-managed Codex rather than API billing.

## Consequences

The successful profile applies uniformly to every arm. The budget records its formula and source
distributions and cannot be relaxed after results are visible. Pilot or budget failure prevents
scored execution without authorizing a model switch.
