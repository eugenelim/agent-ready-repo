#!/usr/bin/env bash
# analyse-modules: scans a source directory and produces a dependency summary.
set -euo pipefail
DIR="${1:?usage: analyse-modules.sh <src-dir>}"

# List Python modules in the directory.
echo "Modules in $DIR:"
find "$DIR" -name "*.py" -maxdepth 2 | sort

# Generate a dependency graph via the dependency-graph skill.
example-agent-cli --print \
  --prompt "Analyze module dependencies in $DIR and produce a dependency graph."
