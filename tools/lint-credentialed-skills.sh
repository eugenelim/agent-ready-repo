#!/usr/bin/env bash
# Back-compat shim — delegates to tools/lint_credentialed_skills.py.
#
# The real implementation moved to the Python sibling at T15 EXECUTE
# time for Windows portability (bash isn't on PATH on a stock Windows
# runner; the heredoc indirection meant `bash` fell through to a
# missing WSL distribution and the lint reported "lint failed" with
# no findings on Windows CI). pre-pr.py invokes the .py directly via
# `sys.executable`; this shim is kept so external callers (the
# `conventions-check` slash command, ad-hoc invocations) continue to
# work.
#
# Reference: docs/specs/credential-broker-contract/spec.md (AC24 / AC25).

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

LINT_ROOT="${LINT_ROOT:-.}"

exec python3 "$REPO_ROOT/tools/lint_credentialed_skills.py" "$LINT_ROOT"
