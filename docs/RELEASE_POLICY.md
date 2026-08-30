# Release policy

A contest release requires `CONTEST_RELEASE_READY`, clean strict CI, frozen Skill/version/contracts/rules, resolved BLOCKER/HIGH findings, benchmark contamination review, dependency/license ledger, reproducible environment, signed decision and human gate. Release manifests bind Git commit and hashes. Any dependency or Final Run change triggers `STALE` and a new version; generated reports alone cannot authorize release.

## Designated remote

The sole tracked remote target is `git_delivery` in `rules/workflow_rules.yaml`. Documents and reports reference that field instead of defining another remote URL. Before delivery, compare the configured `origin` URL with that source. A mismatch is `REMOTE_MISMATCH_BLOCKER` and must not be repaired automatically.

## Delivery gate

Completed deterministic changes must be scoped, inspected, validated, committed atomically, and pushed to the configured non-`main` task branch. Local-only work is not remotely delivered. The only direct-`main` exception is the first initialization of an empty remote when the validated local branch is already `main`.

Before each commit, inspect unstaged and staged status, stats, full diffs, and whitespace. Stage explicit paths rather than using an unchecked `git add .` or `git add -A`. Commit messages describe a single auditable purpose. Run the complete project validation again after the final planned commit and before push.

Never force-push, rewrite published history, automatically rebase a shared branch, or merge a Pull Request. When `origin/main` exists, fetch it safely and publish feature work from a task branch. An eligible GitHub Pull Request is Draft-only and remains subject to human review.

## Publication boundary

Tracked delivery may include governance, plans, ADRs, the formal Skill, rules, contracts, project code/scripts/tests, non-sensitive fixtures, metadata-only upstream reviews, reproducible acceptance reports, versioning, and license notices. It excludes virtual environments, caches, full candidate clones, vaults/answers, secrets, credentials, browser or home-directory configuration, raw private paths or host identifiers, temporary downloads, large run output, and unlicensed third-party content. Environment reports use placeholders such as `<REPO_ROOT>`.

## Post-push verification

Compare local `git rev-parse HEAD` with the exact task-branch SHA returned by `git ls-remote --heads origin`. Only equality permits `REMOTE_DELIVERED`. Authentication, network, remote mismatch, or SHA mismatch results must retain the local commits and be reported using their explicit blocked status; they must never be hidden by optimistic completion language.

Final delivery evidence records repository, remote name, local and remote branches/SHAs, push command and exit code, commits pushed, Draft PR status, remote CI status, ignored local-only paths, and remaining blockers. Local CI passing is not evidence that remote CI ran.
