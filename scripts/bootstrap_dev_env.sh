#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f pyproject.toml ]]; then
  echo "ERROR: run from repository root" >&2
  exit 2
fi

if [[ ! -d .venv ]]; then
  if command -v uv >/dev/null 2>&1; then
    echo "environment_manager=uv"
    uv venv --python python3 .venv
  else
    echo "environment_manager=python-venv"
    python3 -m venv .venv
  fi
else
  echo "environment_manager=existing-venv"
fi

if command -v uv >/dev/null 2>&1; then
  uv pip install --python .venv/bin/python -e '.[dev]'
else
  .venv/bin/python -m pip install -e '.[dev]'
fi

.venv/bin/python -c 'import jsonschema, pytest, yaml; print("foundation_dependencies=ready")'
