# Codex run budget policy

A compact deterministic-oracle pilot must succeed before a scored-run budget is frozen. The budget
separately caps total attempts, input tokens, output tokens, elapsed time, per-cell attempts and
consecutive infrastructure failures. Monetary cost is `UNKNOWN` when ChatGPT-managed usage exposes
no billable currency amount; cached-input and reasoning tokens remain `UNKNOWN` when unobserved.

Phase 002D froze caps of 40 attempts, 10,000,000 input tokens, 334,443 output tokens and 6,197 elapsed
seconds. The runner checks hard limits before each new start and retains a started attempt to its
terminal record. It stopped after 28 attempts at 6,228.480778 seconds. Remaining capacity in another
dimension does not permit another start after any hard limit is reached.

Budgets, checkpoint and cost records are hash-bound and replayable. Thresholds cannot be increased
after results are visible, and correctness/hard Gates dominate cost.
