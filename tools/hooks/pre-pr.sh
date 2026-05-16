#!/usr/bin/env bash
# Pre-PR hook: runs every artifact linter and the work-loop's
# mechanical termination check against any active spec state. Exits
# non-zero on the first failure so a contributor can't open a PR
# whose artifacts are inconsistent with the conventions.
#
# What it runs:
#   - tools/lint-agents-md.sh        — root AGENTS.md hygiene, drift-watch
#   - tools/lint-agent-artifacts.sh  — skill/agent/command frontmatter
#   - tools/lint-skill-deps.sh       — manifest dependency resolution
#   - tools/lint-knowledge.sh        — docs/knowledge/patterns.jsonl
#   - tools/check-done.py            — for each docs/specs/*/state.json,
#                                       --phase implement and --phase review
#
# Runtime: bash + python3 (already required by the artifact linters and
# check-done.py). Wiring lives in each tool's hook surface (Claude
# Code: .claude/settings.json; see tools/hooks/README.md).

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

run() {
  local label="$1"
  shift
  if ! "$@" > /dev/null; then
    echo "pre-pr: ✖ $label failed" >&2
    exit 1
  fi
  echo "pre-pr: ✓ $label"
}

run "agents-md hygiene"    bash tools/lint-agents-md.sh
run "agent-artifact lint"  bash tools/lint-agent-artifacts.sh
run "skill-deps lint"      bash tools/lint-skill-deps.sh
run "knowledge lint"       bash tools/lint-knowledge.sh

shopt -s nullglob
state_files=(docs/specs/*/state.json)
shopt -u nullglob

if (( ${#state_files[@]} == 0 )); then
  echo "pre-pr: (no active state.json — skipping check-done)"
else
  for state in "${state_files[@]}"; do
    for phase in implement review; do
      if ! python3 tools/check-done.py "$state" --phase "$phase" > /dev/null; then
        echo "pre-pr: ✖ check-done.py $state --phase $phase failed" >&2
        exit 1
      fi
      echo "pre-pr: ✓ check-done $state ($phase)"
    done
  done
fi

echo "pre-pr: all checks passed"
