# Phase 002D pilot and budget freeze

## Pilot outcome

- Pilot: `CALIBRATION-PILOT-002D-001`
- Execution: real ChatGPT-managed Codex, not mock and not primary evidence
- Model/reasoning: `gpt-5.6-sol` / `medium`
- Fresh starts: 2; resume: none
- Attempt 001: output-Schema format rejected before model output; original attempt hash preserved
- Attempt 002: `PASS`
- Frozen profile: `PROXY_INHERITED`
- Passing duration: 21.204297 seconds
- Observable passing tokens: input 41,092; output 397; cached input `UNKNOWN`; reasoning `UNKNOWN`
- Schema/oracle/input integrity: `PASS` / `PASS` / unchanged
- Network/MCP: disabled; no prohibited observable command
- Primary/repeat contribution: none

## Frozen budget

- Cohort target: 24 successful eligible primary runs
- Historical attempts/successes/rate: 20 / 13 / 0.65
- Formula base attempts: `ceil(24 / 0.65) = 37`
- Frozen maximum attempts: `min(48, 37 + 3) = 40`
- Per-cell starts/retries: 3 / 2
- Global consecutive infrastructure-failure stop: 3
- Concurrency: 1
- Expected input tokens: 4,762,659; hard maximum: 10,000,000
- Expected elapsed: 4,590 seconds; frozen maximum: 6,197 seconds; absolute maximum: 14,400
- Frozen maximum output tokens: 334,443
- Monetary cost: `UNKNOWN` (ChatGPT-managed Codex, no API billing)
- Budget expansion after arm results: forbidden

Evidence hashes: pilot `ad16ca3686bdc66610f49492b36a51a31dc3774f402f8bb0fd32db97c0a50700`,
cohort `db663586c8d86c12e72da19872a34ab9cdd5070b050d8ebd4a9a56b949bc2058`,
budget `389c24e9155da753a389b50cf073481cd3dfd2649f4d2de4c740f715c6fe6c51`.
