#!/usr/bin/env bash
# pre-commit hook: run format check, lint, type-check, and fast test suite
# before committing. Aborts the commit on any failure.
set -euo pipefail

echo "[pre-commit] Running ruff format check..."
ruff format --check . || {
  echo "[pre-commit] FAIL: formatting violations found."
  echo "             Run: ruff format ."
  exit 1
}

echo "[pre-commit] Running ruff lint..."
ruff check . || {
  echo "[pre-commit] FAIL: lint violations found."
  exit 1
}

echo "[pre-commit] Running mypy..."
mypy packages/ --ignore-missing-imports || {
  echo "[pre-commit] FAIL: type errors found."
  exit 1
}

echo "[pre-commit] Running fast tests (unit only)..."
python3 -m pytest packages/ -q --tb=short -m "not integration" || {
  echo "[pre-commit] FAIL: unit tests failed."
  exit 1
}

echo "[pre-commit] All checks passed."
