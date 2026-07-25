#!/usr/bin/env bash
# Shim → tools/repo/release_check.sh (ini-005 Wave 5 reorganisation).
# Kept until the next minor AgentBundle release.
echo "WARNING: tools/release-check.sh moved to tools/repo/release_check.sh" >&2
exec bash "$(dirname "$0")/repo/release_check.sh" "$@"
