#!/usr/bin/env bash
# Self-test for .claude/skills/work-loop/scripts/check-done.py.
#
# Builds a tempdir of state.json fixtures (each tripping one kill
# criterion, plus a healthy case), runs the script, and asserts the
# expected exit code and stderr signal. Fixtures live in the tempdir so
# the repo stays clean.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PY="python3 $REPO_ROOT/.claude/skills/work-loop/scripts/check-done.py"

failures=0
ran=0

run_case() {
  # run_case <name> <state-body> <phase> <expected-exit> <expected-stderr-substring>
  local name="$1" body="$2" phase="$3" want_exit="$4" want_substr="$5"
  ran=$((ran + 1))

  local path="$TMP/$name.json"
  printf '%s' "$body" > "$path"

  local stderr_out
  set +e
  stderr_out=$($PY "$path" --phase "$phase" 2>&1 >/dev/null)
  local got_exit=$?
  set -e

  if [[ "$got_exit" -ne "$want_exit" ]]; then
    echo "FAIL [$name]: expected exit $want_exit, got $got_exit" >&2
    echo "  stderr: $stderr_out" >&2
    failures=$((failures + 1))
    return
  fi

  if [[ -n "$want_substr" && "$stderr_out" != *"$want_substr"* ]]; then
    echo "FAIL [$name]: stderr did not contain '$want_substr'" >&2
    echo "  stderr: $stderr_out" >&2
    failures=$((failures + 1))
    return
  fi

  echo "ok   [$name]"
}

HEALTHY='{
  "feature": "x",
  "iteration_count": 1,
  "max_iterations": 5,
  "token_budget_used_pct": 0.1,
  "token_budget_cap_pct": 0.85,
  "consecutive_same_error_count": 0,
  "plan_review_status": "approved",
  "finding_fingerprints": ["a"],
  "previous_finding_fingerprints": ["b"]
}'

# Healthy state passes all three phases.
run_case "healthy-plan"      "$HEALTHY" plan      0 ""
run_case "healthy-implement" "$HEALTHY" implement 0 ""
run_case "healthy-review"    "$HEALTHY" review    0 ""

# #1: iteration cap.
ITER_OVER='{"iteration_count": 5, "max_iterations": 5, "plan_review_status": "approved"}'
run_case "iter-cap" "$ITER_OVER" implement 1 "iteration cap"

# #2: token budget.
TOK_OVER='{"token_budget_used_pct": 0.9, "token_budget_cap_pct": 0.85, "plan_review_status": "approved"}'
run_case "token-cap" "$TOK_OVER" implement 1 "token budget"

# #3: consecutive same error.
STUCK='{"consecutive_same_error_count": 3, "plan_review_status": "approved"}'
run_case "stuck" "$STUCK" implement 1 "stuck on same error"

# #4: plan not approved (fires in all phases — approval is a precondition
# for implement and review, not just for unlocking EXECUTE).
PENDING='{"plan_review_status": "pending"}'
run_case "plan-pending-plan"      "$PENDING" plan      1 "plan not approved"
run_case "plan-pending-implement" "$PENDING" implement 1 "plan not approved"
run_case "plan-pending-review"    "$PENDING" review    1 "plan not approved"

# Caps fire under --phase review too (not just implement).
ITER_REVIEW='{"iteration_count": 5, "max_iterations": 5, "plan_review_status": "approved"}'
run_case "iter-cap-review" "$ITER_REVIEW" review 1 "iteration cap"

TOK_REVIEW='{"token_budget_used_pct": 0.9, "token_budget_cap_pct": 0.85, "plan_review_status": "approved"}'
run_case "token-cap-review" "$TOK_REVIEW" review 1 "token budget"

STUCK_REVIEW='{"consecutive_same_error_count": 3, "plan_review_status": "approved"}'
run_case "stuck-review" "$STUCK_REVIEW" review 1 "stuck on same error"

# Data-driven same-error threshold: state.json overrides DEFAULTS.
STUCK_LOW='{
  "consecutive_same_error_count": 2,
  "consecutive_same_error_threshold": 2,
  "plan_review_status": "approved"
}'
run_case "stuck-from-data" "$STUCK_LOW" implement 1 "stuck on same error"

# Negative partner: count below the data-driven threshold passes.
STUCK_BELOW='{
  "consecutive_same_error_count": 2,
  "consecutive_same_error_threshold": 3,
  "plan_review_status": "approved"
}'
run_case "stuck-below-data-threshold" "$STUCK_BELOW" implement 0 ""

# Defensive sort: equivalent fingerprint sets in different orders still
# trigger stasis.
STASIS_UNSORTED='{
  "plan_review_status": "approved",
  "finding_fingerprints": ["b", "a", "c"],
  "previous_finding_fingerprints": ["c", "a", "b"]
}'
run_case "stasis-unsorted" "$STASIS_UNSORTED" review 1 "no progress"

# #5: fingerprint stasis (review phase only).
STASIS='{
  "plan_review_status": "approved",
  "finding_fingerprints": ["x", "y"],
  "previous_finding_fingerprints": ["x", "y"]
}'
run_case "stasis-review"    "$STASIS" review    1 "no progress"
run_case "stasis-implement" "$STASIS" implement 0 ""

# Empty fingerprints — not stasis (first iteration).
EMPTY_FP='{
  "plan_review_status": "approved",
  "finding_fingerprints": [],
  "previous_finding_fingerprints": []
}'
run_case "empty-fingerprints-review" "$EMPTY_FP" review 0 ""

# Missing file.
ran=$((ran + 1))
set +e
stderr_out=$($PY "$TMP/does-not-exist.json" --phase implement 2>&1 >/dev/null)
got_exit=$?
set -e
if [[ "$got_exit" -eq 1 && "$stderr_out" == *"state.json missing"* ]]; then
  echo "ok   [missing-file]"
else
  echo "FAIL [missing-file]: exit=$got_exit stderr=$stderr_out" >&2
  failures=$((failures + 1))
fi

# Malformed JSON.
MALFORMED='{not json'
run_case "malformed" "$MALFORMED" implement 1 "malformed"

# Root is not an object.
NOT_OBJ='[1, 2, 3]'
run_case "not-object" "$NOT_OBJ" implement 1 "must be an object"

# Defaults: missing max_iterations + missing cap, iteration over default 5.
DEFAULTS_OVER='{"iteration_count": 5, "plan_review_status": "approved"}'
run_case "defaults-iter" "$DEFAULTS_OVER" implement 1 "iteration cap"

# End-to-end: use the literal template file the SKILL says to copy. This
# catches schema drift between the work-loop skill's state.json
# template and the script.
TEMPLATE_PATH="$REPO_ROOT/.claude/skills/work-loop/assets/state.json"
if [[ -f "$TEMPLATE_PATH" ]]; then
  ran=$((ran + 1))
  set +e
  fresh_err=$($PY "$TEMPLATE_PATH" --phase plan 2>&1 >/dev/null)
  fresh_exit=$?
  set -e
  if [[ "$fresh_exit" -eq 1 && "$fresh_err" == *"plan not approved"* ]]; then
    echo "ok   [fresh-template-pending]"
  else
    echo "FAIL [fresh-template-pending]: exit=$fresh_exit stderr=$fresh_err" >&2
    failures=$((failures + 1))
  fi

  # Same template with plan_review_status flipped to approved → exit 0.
  APPROVED_TEMPLATE="$TMP/approved-template.json"
  python3 -c "import json, pathlib; p=pathlib.Path('$TEMPLATE_PATH'); d=json.loads(p.read_text()); d['plan_review_status']='approved'; pathlib.Path('$APPROVED_TEMPLATE').write_text(json.dumps(d))"
  run_case "fresh-template-approved" "$(cat "$APPROVED_TEMPLATE")" implement 0 ""
else
  echo "skip [fresh-template-*]: $TEMPLATE_PATH not found"
fi

# Schema-vs-script drift assertions. These catch the failure modes the
# fresh-template fixtures alone don't — a renamed/missing field the
# script reads, and a numeric drift between the script's DEFAULTS dict
# and the template values.
if [[ -f "$TEMPLATE_PATH" ]]; then
  ran=$((ran + 1))
  if python3 - "$TEMPLATE_PATH" "$REPO_ROOT/.claude/skills/work-loop/scripts/check-done.py" <<'PY'
import json, pathlib, re, sys
template = json.loads(pathlib.Path(sys.argv[1]).read_text())
script = pathlib.Path(sys.argv[2]).read_text()

expected_keys = {
    "feature", "iteration_count", "max_iterations",
    "token_budget_used_pct", "token_budget_cap_pct",
    "consecutive_same_error_count", "consecutive_same_error_threshold",
    "plan_review_status", "last_commit_sha",
    "finding_fingerprints", "previous_finding_fingerprints",
    "worktrees",
}
missing = expected_keys - set(template)
extra = set(template) - expected_keys
if missing or extra:
    print(f"schema-drift: missing={sorted(missing)} extra={sorted(extra)}", file=sys.stderr)
    sys.exit(1)

# Every key check-done.py reads via state.get must exist in the template.
script_reads = set(re.findall(r'state\.get\("([^"]+)"', script))
missing_from_template = script_reads - set(template)
if missing_from_template:
    print(f"schema-drift: script reads {sorted(missing_from_template)} which template omits", file=sys.stderr)
    sys.exit(1)
PY
  then
    echo "ok   [schema-keys-match]"
  else
    echo "FAIL [schema-keys-match]" >&2
    failures=$((failures + 1))
  fi

  ran=$((ran + 1))
  if python3 - "$TEMPLATE_PATH" "$REPO_ROOT/.claude/skills/work-loop/scripts/check-done.py" <<'PY'
import json, pathlib, re, sys
template = json.loads(pathlib.Path(sys.argv[1]).read_text())
script = pathlib.Path(sys.argv[2]).read_text()

# Extract DEFAULTS dict from the script.
m = re.search(r'DEFAULTS = \{([^}]+)\}', script, re.DOTALL)
if not m:
    print("DEFAULTS dict not found in script", file=sys.stderr); sys.exit(1)
defaults = {}
for line in m.group(1).strip().splitlines():
    km = re.match(r'\s*"([^"]+)":\s*([0-9.]+)', line)
    if km:
        defaults[km.group(1)] = float(km.group(2))

mismatches = []
for k, v in defaults.items():
    tv = template.get(k)
    if tv is None or float(tv) != v:
        mismatches.append(f"{k}: script={v} template={tv}")
if mismatches:
    print("defaults-vs-template drift: " + "; ".join(mismatches), file=sys.stderr)
    sys.exit(1)
PY
  then
    echo "ok   [defaults-match-template]"
  else
    echo "FAIL [defaults-match-template]" >&2
    failures=$((failures + 1))
  fi
fi

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
