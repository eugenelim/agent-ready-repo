#!/usr/bin/env bash
# Self-test for tools/lint-build.py.
#
# Creates a temporary scratch directory with a .py file that imports a
# third-party package (requests), runs the stdlib-import audit against it
# using the LINT_BUILD_DIR override, and asserts:
#   - exit code is non-zero
#   - stderr names the offending file
#
# Also asserts the audit passes cleanly on a file that contains only
# stdlib imports.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

LINTER="$REPO_ROOT/tools/lint-build.py"

failures=0
ran=0

# ── helper ────────────────────────────────────────────────────────────────

run_case() {
  # run_case <name> <want-exit> <want-substr-in-stderr>
  local name="$1" want_exit="$2" want_substr="$3"
  ran=$((ran + 1))

  local out
  set +e
  out=$(LINT_BUILD_DIR="$TMP/build_$name" python3 "$LINTER" 2>&1)
  local got=$?
  set -e

  if [[ "$got" -ne "$want_exit" ]]; then
    echo "FAIL [$name]: expected exit $want_exit, got $got" >&2
    echo "  output: $out" >&2
    failures=$((failures + 1))
    return
  fi
  if [[ -n "$want_substr" && "$out" != *"$want_substr"* ]]; then
    echo "FAIL [$name]: output missing '$want_substr'" >&2
    echo "  output: $out" >&2
    failures=$((failures + 1))
    return
  fi
  echo "ok   [$name]"
}

# ── case 1: non-stdlib import triggers non-zero exit + named in stderr ────

mkdir -p "$TMP/build_nonstdlib"
cat > "$TMP/build_nonstdlib/foo.py" <<'EOF'
"""A fake pipeline module that mistakenly imports a third-party package."""
import requests  # non-stdlib

def fetch(url):
    return requests.get(url)
EOF

ran=$((ran + 1))
set +e
out=$(LINT_BUILD_DIR="$TMP/build_nonstdlib" python3 "$LINTER" 2>&1)
got=$?
set -e
if [[ "$got" -eq 0 ]]; then
  echo "FAIL [nonstdlib-exit]: expected non-zero exit, got 0" >&2
  echo "  output: $out" >&2
  failures=$((failures + 1))
elif [[ "$out" != *"foo.py"* ]]; then
  echo "FAIL [nonstdlib-filename]: stderr should name the offending file" >&2
  echo "  output: $out" >&2
  failures=$((failures + 1))
elif [[ "$out" != *"requests"* ]]; then
  echo "FAIL [nonstdlib-import-name]: stderr should name the import 'requests'" >&2
  echo "  output: $out" >&2
  failures=$((failures + 1))
else
  echo "ok   [nonstdlib-import-surfaced]"
  ran=$((ran - 1))  # we incremented ran above; the three sub-checks share the one case
fi

# ── case 2: stdlib-only import passes ─────────────────────────────────────

mkdir -p "$TMP/build_stdlibonly"
cat > "$TMP/build_stdlibonly/bar.py" <<'EOF'
"""A fake pipeline module that uses only stdlib."""
import os
import sys
import pathlib
import json
EOF

ran=$((ran + 1))
set +e
out=$(LINT_BUILD_DIR="$TMP/build_stdlibonly" python3 "$LINTER" 2>&1)
got=$?
set -e
if [[ "$got" -ne 0 ]]; then
  echo "FAIL [stdlibonly]: expected exit 0, got $got" >&2
  echo "  output: $out" >&2
  failures=$((failures + 1))
else
  echo "ok   [stdlibonly-passes]"
fi

# ── case 3: agentbundle intra-package imports are allowed ─────────────────

mkdir -p "$TMP/build_agentbundle"
cat > "$TMP/build_agentbundle/baz.py" <<'EOF'
"""A fake pipeline module that imports from agentbundle itself."""
from agentbundle.build import validate
import agentbundle.build.contract
EOF

ran=$((ran + 1))
set +e
out=$(LINT_BUILD_DIR="$TMP/build_agentbundle" python3 "$LINTER" 2>&1)
got=$?
set -e
if [[ "$got" -ne 0 ]]; then
  echo "FAIL [agentbundle-intra]: intra-package imports should not be flagged, exit $got" >&2
  echo "  output: $out" >&2
  failures=$((failures + 1))
else
  echo "ok   [agentbundle-intra-allowed]"
fi

# ── case 4: RFC_AUTHORISED_DIRS exception allows packs/ but bounces ──────
#            an unauthorised new top-level directory.
#
# The new-top-level audit reads `git ls-tree -d --name-only HEAD` against
# the merge-base of HEAD and main. To test the exception path, we build
# two scratch git repos: one with the `packs/` top-level (authorised by
# RFC-0002, should pass), and one with `unauthorised-newdir/` (should
# fail with the audit's error message). The LINTER runs against the
# scratch repo via cd; LINT_BUILD_DIR isn't honoured by the no-new-top-
# level audit, so we need a real repo with a real merge-base.

run_top_level_case() {
  # run_top_level_case <name> <dir-to-create> <want-exit> <want-stderr-substr>
  local name="$1" newdir="$2" want_exit="$3" want_substr="$4"
  local repo="$TMP/repo_$name"
  mkdir -p "$repo"
  (
    cd "$repo"
    git init -q
    git checkout -q -b main 2>/dev/null || git branch -m main 2>/dev/null || true
    git config user.email "test@example.com"
    git config user.name "test"
    # Empty base commit on main so a merge-base exists.
    git commit -q --allow-empty -m "base"
    git checkout -q -b feature
    mkdir "$newdir"
    touch "$newdir/.keep"
    git add -A
    git commit -q -m "introduce $newdir/"
  )
  local out got
  set +e
  out=$(cd "$repo" && python3 "$LINTER" 2>&1)
  got=$?
  set -e
  ran=$((ran + 1))
  if [[ "$got" -ne "$want_exit" ]]; then
    echo "FAIL [$name]: expected exit $want_exit, got $got" >&2
    echo "  output: $out" >&2
    failures=$((failures + 1))
    return
  fi
  if [[ -n "$want_substr" && "$out" != *"$want_substr"* ]]; then
    echo "FAIL [$name]: output missing '$want_substr'" >&2
    echo "  output: $out" >&2
    failures=$((failures + 1))
    return
  fi
  echo "ok   [$name]"
}

run_top_level_case "authorised-packs"        "packs"               0 "no-new-top-level-directory audit passed"
run_top_level_case "unauthorised-newdir"     "unauthorised-newdir" 1 "RFC required"

# ── result ────────────────────────────────────────────────────────────────

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
