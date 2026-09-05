#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x .venv/bin/python ]]; then
  echo "ERROR: .venv missing; run bash scripts/bootstrap_dev_env.sh" >&2
  exit 2
fi

.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_c_target_batch_freeze.py --check
.venv/bin/python scripts/check_c_target_first_run_freezes.py --check
.venv/bin/python scripts/check_c_target_postmortem.py --check
.venv/bin/python scripts/check_c_target_rc4_candidate.py --check
.venv/bin/python scripts/check_c_target_rc4_batch_regressions.py --check
.venv/bin/python scripts/check_c_target_rc4_unified_regression.py --check
.venv/bin/python scripts/check_c_target_2024c_validation_freeze.py --check --require-delivery
.venv/bin/python scripts/check_c_target_2024c_validation_outcome.py --check --require-delivery
.venv/bin/python scripts/check_claim_scope_repair.py --check
.venv/bin/python scripts/check_c_target_2019c_validation.py --check --require-delivery
.venv/bin/python scripts/validate_repo.py --strict
git diff --check
