#!/usr/bin/env bash
# Self-test for tools/hooks/session-start.sh. Exercises the
# malformed-line warning, the --scope validation, and the empty-file
# silent-exit. Uses KNOWLEDGE_FILE override against tempdir fixtures so
# the production patterns.jsonl is never touched.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

HOOK="$REPO_ROOT/tools/hooks/session-start.sh"

failures=0
ran=0

# run_case <name> <file-contents> <want-exit> <want-stdout-substr> <want-stderr-substr>
# Empty want-*-substr means "don't assert on that stream".
run_case() {
  local name="$1" body="$2" want_exit="$3" want_stdout="$4" want_stderr="$5"
  ran=$((ran + 1))

  local path="$TMP/$name.jsonl"
  printf '%s' "$body" > "$path"

  local out_stdout out_stderr
  set +e
  out_stdout=$(KNOWLEDGE_FILE="$path" bash "$HOOK" 2>"$TMP/$name.err")
  local got_exit=$?
  out_stderr=$(< "$TMP/$name.err")
  set -e

  if [[ "$got_exit" -ne "$want_exit" ]]; then
    echo "FAIL [$name]: expected exit $want_exit, got $got_exit" >&2
    echo "  stdout: $out_stdout" >&2
    echo "  stderr: $out_stderr" >&2
    failures=$((failures + 1))
    return
  fi
  if [[ -n "$want_stdout" && "$out_stdout" != *"$want_stdout"* ]]; then
    echo "FAIL [$name]: stdout missing '$want_stdout'" >&2
    echo "  stdout: $out_stdout" >&2
    failures=$((failures + 1))
    return
  fi
  if [[ -n "$want_stderr" && "$out_stderr" != *"$want_stderr"* ]]; then
    echo "FAIL [$name]: stderr missing '$want_stderr'" >&2
    echo "  stderr: $out_stderr" >&2
    failures=$((failures + 1))
    return
  fi
  echo "ok   [$name]"
}

VALID='{"id": "K-0001", "kind": "pattern", "scope": "src/**", "title": "T", "body": "B", "source": "PR#1"}'

# Clean file with one valid entry — prints the block, no warning.
run_case "clean-one-entry" "$VALID" 0 "=== knowledge ===" ""

# Mixed file — one malformed, one valid. Valid entry prints; warning fires.
MIXED='{not json'$'\n'"$VALID"
run_case "mixed-valid-and-malformed" "$MIXED" 0 "[K-0001]" "skipped 1 malformed"

# All malformed — no entries print, warning still fires on stderr.
ALL_BAD='{not json'$'\n''also not'$'\n''broken too'
run_case "all-malformed" "$ALL_BAD" 0 "" "skipped 3 malformed"

# Empty file — silent exit 0, no warning.
run_case "empty-file" "" 0 "" ""

# Missing file — silent exit 0 (hook is a no-op).
ran=$((ran + 1))
set +e
out_stdout=$(KNOWLEDGE_FILE="$TMP/does-not-exist.jsonl" bash "$HOOK" 2>"$TMP/miss.err")
got=$?
set -e
out_stderr=$(< "$TMP/miss.err")
if [[ "$got" -eq 0 && -z "$out_stdout" && -z "$out_stderr" ]]; then
  echo "ok   [missing-file]"
else
  echo "FAIL [missing-file]: exit=$got stdout=$out_stdout stderr=$out_stderr" >&2
  failures=$((failures + 1))
fi

# --scope with no value — exits 2 with usage message.
ran=$((ran + 1))
set +e
out_stderr=$(bash "$HOOK" --scope 2>&1)
got=$?
set -e
if [[ "$got" -eq 2 && "$out_stderr" == *"--scope requires a path or glob value"* ]]; then
  echo "ok   [scope-no-value]"
else
  echo "FAIL [scope-no-value]: exit=$got stderr=$out_stderr" >&2
  failures=$((failures + 1))
fi

# --scope filter (positive): caller path covered by stored glob.
COVERAGE='{"id": "K-0001", "kind": "pattern", "scope": "packages/auth/**", "title": "T1", "body": "B1", "source": "S1"}'$'\n''{"id": "K-0002", "kind": "gotcha", "scope": "src/other/x.ts", "title": "T2", "body": "B2", "source": "S2"}'
printf '%s' "$COVERAGE" > "$TMP/cov.jsonl"
ran=$((ran + 1))
set +e
out=$(KNOWLEDGE_FILE="$TMP/cov.jsonl" bash "$HOOK" --scope 'packages/auth/server.ts' 2>"$TMP/cov.err")
got=$?
set -e
if [[ "$got" -eq 0 && "$out" == *"K-0001"* && "$out" != *"K-0002"* ]]; then
  echo "ok   [scope-coverage-positive]"
else
  echo "FAIL [scope-coverage-positive]: caller path didn't match stored glob correctly" >&2
  echo "  stdout: $out" >&2
  failures=$((failures + 1))
fi

# --scope filter (negative): caller path NOT covered by other-package glob.
ran=$((ran + 1))
set +e
out=$(KNOWLEDGE_FILE="$TMP/cov.jsonl" bash "$HOOK" --scope 'packages/billing/charge.ts' 2>"$TMP/cov2.err")
got=$?
set -e
if [[ "$got" -eq 0 && "$out" != *"K-0001"* && "$out" != *"K-0002"* ]]; then
  echo "ok   [scope-coverage-negative]"
else
  echo "FAIL [scope-coverage-negative]: unrelated path matched stored glob" >&2
  echo "  stdout: $out" >&2
  failures=$((failures + 1))
fi

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
