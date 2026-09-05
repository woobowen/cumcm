# Phase 004C3 historical regression

RC6 passed the retained RC4 regression surface without using any historical answer or changing any
historical workspace. `check_c_target_rc4_batch_regressions.py --check` passed all three batch cases.
`check_c_target_rc4_unified_regression.py --check` passed three batch cases, two synthetic E2E cases
and all 30 negative scenarios. The separate RC6 negative capture also passed 30/30 with zero
unhandled exceptions and zero sensitive values reported.

The historical/development coverage remains 2020 A plus 2020, 2021, 2022 and 2023 C. The RC6
candidate additionally passes the 37-check Competition RC consistency surface, Skill discovery
still finds exactly one formal Skill, target policy passes, answer-leakage and secret/private-path
findings are zero, and clean-room provenance passes.

Path-level Git comparison establishes the stronger immutability statement. Relative to
`b289f2dfcaebe8edca5335ed4bf89f383c67eb51`, the 2019 pre-run freeze, every Run, the decision and
terminal freeze are byte-identical, with no later commit touching its Runs. Relative to
`197f62bc75ebe832e9dd3ced0306740f336b80d6`, the 2024 pre-run freeze, decision and terminal freeze
are byte-identical; the only later commit under that case added the delivery receipt and did not
create or rerun a model Run.

The two legacy integrity commands are now time-qualified for successor phases.
`check_claim_scope_repair.py --check` resolves the RC5 Skill file set and bytes at the recorded RC5
implementation commit. `check_c_target_2019c_validation.py --check --require-delivery` resolves
freeze-bound generic artifacts at the recorded 2019 terminal-freeze commit. Both commands pass
without comparing authorized RC6 successor code to historical bytes. Before this harness repair,
they reported successor drift after pytest had passed and made the first terminal local and remote
CI runs exit nonzero; those failures did not indicate mutation of frozen case inputs, Runs,
decisions or terminal freezes. The older Phase 002D-R2A-C1 historical verification record also
embeds the then-current generated status report, so its live-workspace replay is stale after later
phases and is not rewritten here.

Closure commit `766f337eac848477759f531de54e988d99085e7a` passed remote CI `33956588893`.
The remote job reproduced both time-qualified commands with zero errors after pytest
`2009 passed / 1 skipped`; strict repository validation also returned 0 errors / 0 warnings.

One no-argument legacy regression runner was inadvertently invoked while checking its interface.
It created only an untracked derived Phase 004C2 regression summary; that exact untracked file was
removed immediately. No tracked file or historical case workspace changed, and the runner was not
used as evidence.
