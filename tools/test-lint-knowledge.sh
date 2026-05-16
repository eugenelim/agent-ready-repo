#!/usr/bin/env bash
# Self-test for tools/lint-knowledge.sh. Builds tempdir fixtures
# tripping each validation rule and asserts the right error fires.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

LINTER="$REPO_ROOT/tools/lint-knowledge.sh"

failures=0
ran=0

run_case() {
  # run_case <name> <file-contents> <expected-exit> <expected-substr>
  local name="$1" body="$2" want_exit="$3" want_substr="$4"
  ran=$((ran + 1))

  local path="$TMP/$name.jsonl"
  printf '%s' "$body" > "$path"

  local out
  set +e
  out=$(KNOWLEDGE_FILE="$path" bash "$LINTER" 2>&1)
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

VALID='{"id": "K-0001", "kind": "pattern", "scope": "src/**", "title": "T", "body": "B", "source": "PR#1"}'

# Empty file (no learnings yet) is valid.
run_case "empty"            ""                   0 "Knowledge lint: passed"

# Trailing newlines / blank lines are tolerated.
run_case "valid-one-entry"  "$VALID"$'\n'        0 "Knowledge lint: passed"
run_case "blank-lines"      $'\n\n'"$VALID"$'\n\n' 0 "Knowledge lint: passed"

# Malformed JSON.
run_case "malformed-json"   '{not json'          1 "not valid JSON"

# Not an object.
run_case "scalar-line"      '"just a string"'    1 "must be a JSON object"
run_case "list-line"        '[1, 2, 3]'          1 "must be a JSON object"

# Missing required keys.
run_case "missing-keys"     '{"id": "K-0001"}'   1 "missing required keys"

# Unknown extra keys.
EXTRA='{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "t", "body": "b", "source": "s", "extra": 1}'
run_case "unknown-keys"     "$EXTRA"             1 "unknown keys"

# Bad id format.
BAD_ID='{"id": "K-1", "kind": "pattern", "scope": "x", "title": "t", "body": "b", "source": "s"}'
run_case "bad-id"           "$BAD_ID"            1 "must match"

# Duplicate id.
DUP='{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "t", "body": "b", "source": "s"}'
run_case "duplicate-id"     "$DUP"$'\n'"$DUP"    1 "duplicate id"

# Bad kind.
BAD_KIND='{"id": "K-0001", "kind": "tip", "scope": "x", "title": "t", "body": "b", "source": "s"}'
run_case "bad-kind"         "$BAD_KIND"          1 "must be one of"

# Empty string field.
EMPTY_FIELD='{"id": "K-0001", "kind": "pattern", "scope": "", "title": "t", "body": "b", "source": "s"}'
run_case "empty-scope"      "$EMPTY_FIELD"       1 "must be a non-empty string"

# Non-string field.
NONSTR='{"id": "K-0001", "kind": "pattern", "scope": "x", "title": 42, "body": "b", "source": "s"}'
run_case "non-string-title" "$NONSTR"            1 "must be a non-empty string"

# Two valid entries with sequential ids.
TWO="$VALID"$'\n''{"id": "K-0002", "kind": "gotcha", "scope": "*", "title": "T2", "body": "B2", "source": "PR#2"}'
run_case "two-valid"        "$TWO"               0 "passed"

# null-valued required field (JSON null is not a string).
NULL_TITLE='{"id": "K-0001", "kind": "pattern", "scope": "x", "title": null, "body": "b", "source": "s"}'
run_case "null-title" "$NULL_TITLE" 1 "must be a non-empty string"

# Trailing garbage after a valid JSON object on the same line: json.loads
# rejects it ("Extra data") — locks the behaviour.
TRAILING="$VALID"' garbage-after'
run_case "trailing-garbage" "$TRAILING" 1 "not valid JSON"

# Duplicate id where the two entries differ in body — dedup is by id alone.
DUP_DIFF='{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "first",  "body": "B1", "source": "s"}'$'\n'\
'{"id": "K-0001", "kind": "pattern", "scope": "x", "title": "second", "body": "B2", "source": "s"}'
run_case "duplicate-id-different-body" "$DUP_DIFF" 1 "duplicate id"

# Multiple shape errors on a single line surface in one lint run.
MULTI='{"id": "bad", "scope": "x", "title": "t", "body": "b", "source": "s", "stray": 1}'
ran=$((ran + 1))
path="$TMP/multi.jsonl"
printf '%s' "$MULTI" > "$path"
set +e
multi_out=$(KNOWLEDGE_FILE="$path" bash "$LINTER" 2>&1)
multi_exit=$?
set -e
if [[ "$multi_exit" -eq 1 \
   && "$multi_out" == *"missing required keys"* \
   && "$multi_out" == *"unknown keys"* \
   && "$multi_out" == *"must match"* ]]; then
  echo "ok   [multi-error-one-line]"
else
  echo "FAIL [multi-error-one-line]: expected three error categories in one run" >&2
  echo "  exit=$multi_exit" >&2
  echo "  output: $multi_out" >&2
  failures=$((failures + 1))
fi

# Schema drift: the README's field table and the linter's REQUIRED_KEYS /
# ALLOWED_KINDS must stay in sync. Phase 1's precedent — see
# tools/test-check-done.sh schema-keys-match.
ran=$((ran + 1))
if python3 - "$REPO_ROOT/docs/knowledge/README.md" "$REPO_ROOT/tools/lint-knowledge.sh" <<'PY'
import pathlib, re, sys
readme = pathlib.Path(sys.argv[1]).read_text()
script = pathlib.Path(sys.argv[2]).read_text()

# Extract the linter's enforced sets.
req = re.search(r"REQUIRED_KEYS\s*=\s*\{([^}]+)\}", script)
kinds = re.search(r"ALLOWED_KINDS\s*=\s*\{([^}]+)\}", script)
if not req or not kinds:
    print("schema-drift: could not find REQUIRED_KEYS / ALLOWED_KINDS in script", file=sys.stderr)
    sys.exit(1)
script_keys = set(re.findall(r'"([^"]+)"', req.group(1)))
script_kinds = set(re.findall(r'"([^"]+)"', kinds.group(1)))

# Extract the README's field table keys (first column, backticked words).
table_keys = set(re.findall(r"^\|\s*`([a-zA-Z_]+)`\s*\|", readme, re.MULTILINE))
# The README's kind row lists each kind backticked on the same line. Split
# by line and grab every backticked lowercase word from the kind row.
kind_lines = [l for l in readme.splitlines() if re.match(r"^\|\s*`kind`\s*\|", l)]
if not kind_lines:
    print("schema-drift: README missing the canonical kind row", file=sys.stderr)
    sys.exit(1)
readme_kinds = set(re.findall(r"`([a-z]+)`", kind_lines[0])) - {"kind"}

missing_keys = script_keys - table_keys
extra_keys = table_keys - script_keys
if missing_keys or extra_keys:
    print(f"schema-drift keys: script={sorted(script_keys)} readme={sorted(table_keys)} "
          f"missing_from_readme={sorted(missing_keys)} extra_in_readme={sorted(extra_keys)}",
          file=sys.stderr)
    sys.exit(1)

if script_kinds != readme_kinds:
    print(f"schema-drift kinds: script={sorted(script_kinds)} readme={sorted(readme_kinds)}",
          file=sys.stderr)
    sys.exit(1)
PY
then
  echo "ok   [schema-drift-readme-vs-script]"
else
  echo "FAIL [schema-drift-readme-vs-script]" >&2
  failures=$((failures + 1))
fi

# Production file lints clean (regression guard).
ran=$((ran + 1))
set +e
out=$(bash "$LINTER" 2>&1)
got=$?
set -e
if [[ "$got" -eq 0 ]]; then
  echo "ok   [production-file]"
else
  echo "FAIL [production-file]: real docs/knowledge/patterns.jsonl is not clean" >&2
  echo "  output: $out" >&2
  failures=$((failures + 1))
fi

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
