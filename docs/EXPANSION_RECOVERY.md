# Phase 002D expansion recovery

Every scored failure is append-only evidence. Infrastructure failures support diagnosis, retry
planning and gap discovery but never ranking, superiority, architecture selection, component
acceptance or phase advancement. Raw traces, exact transport identifiers and stderr remain ignored;
tracked records retain hashes, bounded event summaries and failure classes.

Phase 002D retries are new fresh sessions from the frozen retry queue, not resumes. A retry can enter
primary evidence only when all ordinary eligibility checks pass; its `retry_of` provenance remains
visible and it does not increase independent-repeat depth for the same `repeat_id`. Per-cell and
global attempt budgets, consecutive infrastructure limits and all token/time caps still apply.

The terminal elapsed-budget stop is not recoverable within the frozen experiment. Continuing the
same phase requires a new reviewed design and budget freeze that preserves the old records; no
threshold mutation, deletion, relabelling or immediate continuation is allowed.
