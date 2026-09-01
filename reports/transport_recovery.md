# Phase 002B Transport Recovery

Status: `AUTOMATED_ADJUDICATION_INCOMPLETE`.

Correctness used the primary persistent exec session and the one permitted exact-session resume. Both ended in `RESPONSES_CONNECT_RESET`; the two-attempt role limit then stopped the formal chain. App Server was not started because a third attempt is prohibited.

| Attempt | Kind | Adapter | Seconds | Failure | Session hash | Raw hash | Next |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | INITIAL | EXEC_RESUMABLE | 338.529427 | RESPONSES_CONNECT_RESET | fab843b8795cfd19db7db516559b8a2c89b2fc88f7cfd824ba54d5c766a1a7c6 | a6759d53415beda690702242f122e6efec14f68c1fa63d0269b7e710356d5464 | EXEC_RESUMABLE |
| 2 | RESUME | EXEC_RESUMABLE | 55.671046 | RESPONSES_CONNECT_RESET | fab843b8795cfd19db7db516559b8a2c89b2fc88f7cfd824ba54d5c766a1a7c6 | 6a3831089f393724a66a143f5fc4d57664c54f8abb059f9a782df6794b87e3b5 | NONE |

Phase 002B starts: 2/8; remaining: 6. Token usage was not emitted by the failed turns.
Raw events, stderr, exact session IDs and hidden reasoning remain ignored; only hashes and sanitized event counts are tracked.
