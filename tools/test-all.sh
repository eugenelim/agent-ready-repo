#!/usr/bin/env bash
# Umbrella runner: every self-test in tools/. Run by hand when a
# linter, hook, or loop-cohort.py changes; CI runs a subset, so this is
# the local-side belt-and-braces.
#
# Distinct from tools/hooks/pre-pr.py — that's a *gate* against the
# working tree (does the diff pass the linters?); this is a *suite*
# of self-tests against the linters and hooks themselves (do the
# tools still do what they claim?). Both have a place; both green is
# the contract.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Each entry: "<label>:<command>". Order is alphabetical for stability;
# nothing in the chain depends on a particular order.
tests=(
  "loop-cohort:bash tools/test-loop-cohort.sh"
  "lint-agent-artifacts:bash tools/test-lint-agent-artifacts.sh"
  "lint-knowledge:bash tools/test-lint-knowledge.sh"
  "lint-skill-deps:bash tools/test-lint-skill-deps.sh"
  "pre-pr:bash tools/test-pre-pr.sh"
  "session-start:bash tools/test-session-start.sh"
)

failures=0
ran=0

for entry in "${tests[@]}"; do
  label="${entry%%:*}"
  cmd="${entry#*:}"
  ran=$((ran + 1))
  if $cmd > /dev/null 2>&1; then
    echo "✓ $label"
  else
    echo "✖ $label — re-run \`$cmd\` for output" >&2
    failures=$((failures + 1))
  fi
done

echo
if (( failures > 0 )); then
  echo "test-all: $failures of $ran failed" >&2
  exit 1
fi
echo "test-all: $ran passed"
