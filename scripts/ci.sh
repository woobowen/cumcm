#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x .venv/bin/python ]]; then
  echo "ERROR: .venv missing; run bash scripts/bootstrap_dev_env.sh" >&2
  exit 2
fi

.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/validate_repo.py --strict
git diff --check
