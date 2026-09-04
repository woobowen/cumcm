# Phase 004A Timing and Cost

| Activity | Observed time |
|---|---:|
| Baseline full CI | 363.70 s |
| RC1 answer-sealed first run | 1,387 s |
| RC2 Development three captured Runs | 99.347647 s |
| Stress A transform / audit-prepare / captured Runs | 114.38 / 45.21 / 131.585582 s |
| Stress B transform / captured Runs | 110.23 / 127.983545 s |
| Stress C transform / captured Runs | 115.08 / 127.538697 s |
| Final `bash scripts/ci.sh` | 336.75 s (pytest 311.00 s) |

RC1 time to exact requirements/data-audit/baseline stages is `UNKNOWN` because RC1 did not emit
per-Gate timestamps. RC1 time to first valid result, Final Run and handoff is not applicable: the
executor hard gate blocked. RC2 time from first formal execute start to the last execute end was 114
seconds wall-clock; captured compute time was 99.347647 seconds. The first baseline completed in
33.692685 seconds after execution began.

Manual intervention counts: RC1 had one dependency bootstrap and one rejected pre-finalize attempt;
RC2 had no result editing and two expected terminal-command semantic rejects (`validate --check` and
`handoff --check` after READY), both preserved. Failed formal model Runs: zero in RC2/Stress.

Token visibility, reasoning tokens, queue time and monetary/API cost are `UNKNOWN`. No API key,
model training, foundation-model fine-tuning or paid model API call was used. Peak observed XLSX
transformation RSS was about 2.73 GB; captured model Runs used about 0.58 GB on the original input.
