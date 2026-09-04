# Competition RC1 Limitations

RC1 is a runnable Development-training candidate with finite public assurance. It is not a final
competition release or proof of generalization.

The following are explicitly `DEFERRED_NOT_PASSED`:

- full sealed Stage 1;
- Stage 2 model comparison/effectiveness;
- full ablation;
- external validity on unseen CUMCM problems;
- production fitness, scale, operational reliability and maintainability;
- monetary cost.

Only two small project-original cases were run. The prediction data are intentionally linear and the
optimization domain is completely enumerable; passing them proves the pipeline executes and binds
evidence, not that its model portfolio is sufficient for real problems. The 30 negative cases prove
specified fail-closed behavior, not exhaustive security.

The executable code registry is fixed to the bundled deterministic RC1 runner and synthetic-case
support module. A caller-supplied custom executor is outside this assurance because RC1 does not yet
provide a trusted dynamic capture mechanism for arbitrary code roots.

The hidden Benchmark was not opened, historical questions/answers were not read, and Stage 2 real
comparison starts are zero. API calls/billing, model training, fine-tuning and third-party execution
are zero. No third-party base is selected or integrated; project license remains undecided.

The next evidence source must be an answer-sealed historical Development first run. Validation and
Held-out remain unavailable for tuning, and any answer exposure permanently demotes that case to
Development.
