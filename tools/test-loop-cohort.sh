#!/usr/bin/env bash
# Self-test for .claude/skills/work-loop/scripts/loop-cohort.py.
#
# Each fixture lands in its own tempdir <name>/state.json (the tool
# reads from <spec-dir>/state.json). The legacy check-done.py cases
# are preserved — they cover the `check` verb. The newer cases exercise
# init, approve-plan, review record (parse + --fingerprint), and the
# worktree subcommands against scratch git repos.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SCRIPT="$REPO_ROOT/.claude/skills/work-loop/scripts/loop-cohort.py"
PY="python3 $SCRIPT"

failures=0
ran=0

# run_case <name> <state-body> <phase> <expected-exit> <expected-stderr-substring>
# Wraps the body into <TMP>/<name>/state.json and runs `loop-cohort check`.
run_case() {
  local name="$1" body="$2" phase="$3" want_exit="$4" want_substr="$5"
  ran=$((ran + 1))

  local dir="$TMP/$name"
  mkdir -p "$dir"
  printf '%s' "$body" > "$dir/state.json"

  local stderr_out
  set +e
  stderr_out=$($PY check "$dir" --phase "$phase" 2>&1 >/dev/null)
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

# ── check verb (legacy check-done.py coverage) ───────────────────────────

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

# #4: plan not approved (fires in all phases).
PENDING='{"plan_review_status": "pending"}'
run_case "plan-pending-plan"      "$PENDING" plan      1 "plan not approved"
run_case "plan-pending-implement" "$PENDING" implement 1 "plan not approved"
run_case "plan-pending-review"    "$PENDING" review    1 "plan not approved"

# Caps fire under --phase review too.
ITER_REVIEW='{"iteration_count": 5, "max_iterations": 5, "plan_review_status": "approved"}'
run_case "iter-cap-review" "$ITER_REVIEW" review 1 "iteration cap"

TOK_REVIEW='{"token_budget_used_pct": 0.9, "token_budget_cap_pct": 0.85, "plan_review_status": "approved"}'
run_case "token-cap-review" "$TOK_REVIEW" review 1 "token budget"

STUCK_REVIEW='{"consecutive_same_error_count": 3, "plan_review_status": "approved"}'
run_case "stuck-review" "$STUCK_REVIEW" review 1 "stuck on same error"

# Data-driven same-error threshold.
STUCK_LOW='{
  "consecutive_same_error_count": 2,
  "consecutive_same_error_threshold": 2,
  "plan_review_status": "approved"
}'
run_case "stuck-from-data" "$STUCK_LOW" implement 1 "stuck on same error"

STUCK_BELOW='{
  "consecutive_same_error_count": 2,
  "consecutive_same_error_threshold": 3,
  "plan_review_status": "approved"
}'
run_case "stuck-below-data-threshold" "$STUCK_BELOW" implement 0 ""

STASIS_UNSORTED='{
  "plan_review_status": "approved",
  "finding_fingerprints": ["b", "a", "c"],
  "previous_finding_fingerprints": ["c", "a", "b"]
}'
run_case "stasis-unsorted" "$STASIS_UNSORTED" review 1 "no progress"

STASIS='{
  "plan_review_status": "approved",
  "finding_fingerprints": ["x", "y"],
  "previous_finding_fingerprints": ["x", "y"]
}'
run_case "stasis-review"    "$STASIS" review    1 "no progress"
run_case "stasis-implement" "$STASIS" implement 0 ""

EMPTY_FP='{
  "plan_review_status": "approved",
  "finding_fingerprints": [],
  "previous_finding_fingerprints": []
}'
run_case "empty-fingerprints-review" "$EMPTY_FP" review 0 ""

# Missing file — point at a dir that has no state.json.
ran=$((ran + 1))
mkdir -p "$TMP/missing"
set +e
stderr_out=$($PY check "$TMP/missing" --phase implement 2>&1 >/dev/null)
got_exit=$?
set -e
if [[ "$got_exit" -eq 1 && "$stderr_out" == *"state.json missing"* ]]; then
  echo "ok   [missing-file]"
else
  echo "FAIL [missing-file]: exit=$got_exit stderr=$stderr_out" >&2
  failures=$((failures + 1))
fi

MALFORMED='{not json'
run_case "malformed" "$MALFORMED" implement 1 "malformed"

NOT_OBJ='[1, 2, 3]'
run_case "not-object" "$NOT_OBJ" implement 1 "must be an object"

DEFAULTS_OVER='{"iteration_count": 5, "plan_review_status": "approved"}'
run_case "defaults-iter" "$DEFAULTS_OVER" implement 1 "iteration cap"

# Template-vs-script drift. Reuses the canonical assets/state.json so
# any rename/removal of a field check-done's logic reads gets caught.
TEMPLATE_PATH="$REPO_ROOT/.claude/skills/work-loop/assets/state.json"
if [[ -f "$TEMPLATE_PATH" ]]; then
  ran=$((ran + 1))
  mkdir -p "$TMP/fresh-template"
  cp "$TEMPLATE_PATH" "$TMP/fresh-template/state.json"
  set +e
  fresh_err=$($PY check "$TMP/fresh-template" --phase plan 2>&1 >/dev/null)
  fresh_exit=$?
  set -e
  if [[ "$fresh_exit" -eq 1 && "$fresh_err" == *"plan not approved"* ]]; then
    echo "ok   [fresh-template-pending]"
  else
    echo "FAIL [fresh-template-pending]: exit=$fresh_exit stderr=$fresh_err" >&2
    failures=$((failures + 1))
  fi

  ran=$((ran + 1))
  mkdir -p "$TMP/fresh-template-approved"
  python3 -c "import json, pathlib; p=pathlib.Path('$TEMPLATE_PATH'); d=json.loads(p.read_text()); d['plan_review_status']='approved'; pathlib.Path('$TMP/fresh-template-approved/state.json').write_text(json.dumps(d))"
  set +e
  fresh_err=$($PY check "$TMP/fresh-template-approved" --phase implement 2>&1 >/dev/null)
  fresh_exit=$?
  set -e
  if [[ "$fresh_exit" -eq 0 ]]; then
    echo "ok   [fresh-template-approved]"
  else
    echo "FAIL [fresh-template-approved]: exit=$fresh_exit stderr=$fresh_err" >&2
    failures=$((failures + 1))
  fi
else
  echo "skip [fresh-template-*]: $TEMPLATE_PATH not found"
fi

# Schema-vs-script drift assertions.
if [[ -f "$TEMPLATE_PATH" ]]; then
  ran=$((ran + 1))
  if python3 - "$TEMPLATE_PATH" "$SCRIPT" <<'PY'
import json, pathlib, re, sys
template = json.loads(pathlib.Path(sys.argv[1]).read_text())
script = pathlib.Path(sys.argv[2]).read_text()

expected_keys = {
    "feature", "iteration_count", "max_iterations",
    "token_budget_used_pct", "token_budget_cap_pct",
    "consecutive_same_error_count", "consecutive_same_error_threshold",
    "plan_review_status", "auto_parallel", "last_commit_sha",
    "finding_fingerprints", "previous_finding_fingerprints",
    "worktrees",
}
missing = expected_keys - set(template)
extra = set(template) - expected_keys
if missing or extra:
    print(f"schema-drift: missing={sorted(missing)} extra={sorted(extra)}", file=sys.stderr)
    sys.exit(1)

script_reads = set(re.findall(r'state\.get\("([^"]+)"', script))
missing_from_template = script_reads - set(template) - {"worktrees"}
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
  if python3 - "$TEMPLATE_PATH" "$SCRIPT" <<'PY'
import json, pathlib, re, sys
template = json.loads(pathlib.Path(sys.argv[1]).read_text())
script = pathlib.Path(sys.argv[2]).read_text()

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

# ── init verb ────────────────────────────────────────────────────────────

ran=$((ran + 1))
mkdir -p "$TMP/init-spec/myfeature"
set +e
$PY init "$TMP/init-spec/myfeature" > /dev/null
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 && -f "$TMP/init-spec/myfeature/state.json" ]]; then
  feature_val=$(python3 -c "import json; print(json.load(open('$TMP/init-spec/myfeature/state.json'))['feature'])")
  if [[ "$feature_val" == "myfeature" ]]; then
    echo "ok   [init-creates-state]"
  else
    echo "FAIL [init-creates-state]: feature='$feature_val' expected 'myfeature'" >&2
    failures=$((failures + 1))
  fi
else
  echo "FAIL [init-creates-state]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# init refuses to overwrite by default.
ran=$((ran + 1))
set +e
$PY init "$TMP/init-spec/myfeature" 2> "$TMP/init-overwrite.err"
got_exit=$?
set -e
if [[ "$got_exit" -eq 1 && $(cat "$TMP/init-overwrite.err") == *"already exists"* ]]; then
  echo "ok   [init-refuses-overwrite]"
else
  echo "FAIL [init-refuses-overwrite]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# init --force overwrites.
ran=$((ran + 1))
set +e
$PY init "$TMP/init-spec/myfeature" --force > /dev/null
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 ]]; then
  echo "ok   [init-force-overwrites]"
else
  echo "FAIL [init-force-overwrites]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# ── approve-plan verb ────────────────────────────────────────────────────

ran=$((ran + 1))
$PY approve-plan "$TMP/init-spec/myfeature" > /dev/null
status_val=$(python3 -c "import json; print(json.load(open('$TMP/init-spec/myfeature/state.json'))['plan_review_status'])")
if [[ "$status_val" == "approved" ]]; then
  echo "ok   [approve-plan-flips-status]"
else
  echo "FAIL [approve-plan-flips-status]: status='$status_val'" >&2
  failures=$((failures + 1))
fi

# ── review record verb ──────────────────────────────────────────────────

# Sample reviewer report in the documented format.
REVIEW_REPORT="$TMP/review.md"
cat > "$REVIEW_REPORT" <<'EOF'
## Blockers

**1. PLAN-phase exit-1 conflates "not yet done" with "stop".** `foo.py:88-92`. The skill body conflates exit-1. Fix: distinguish.

**2. Wrong file mode.** `bar.py:14`. Mode is 0o755. Fix: use 0o644.

## Nits

**3. Typo in docstring.** `baz.py:3`. Says "implementor". Fix: spell correctly.
EOF

ran=$((ran + 1))
$PY review record "$TMP/init-spec/myfeature" --report "$REVIEW_REPORT" > /dev/null
fp_count=$(python3 -c "import json; print(len(json.load(open('$TMP/init-spec/myfeature/state.json'))['finding_fingerprints']))")
iter_val=$(python3 -c "import json; print(json.load(open('$TMP/init-spec/myfeature/state.json'))['iteration_count'])")
if [[ "$fp_count" == "3" && "$iter_val" == "1" ]]; then
  echo "ok   [review-record-parses-three]"
else
  echo "FAIL [review-record-parses-three]: count=$fp_count iter=$iter_val" >&2
  failures=$((failures + 1))
fi

# Fingerprint stability — same report parses to same hashes.
ran=$((ran + 1))
EXPECTED_FP=$(python3 -c "
import hashlib
print(hashlib.sha1(b'foo.py|88|**1. PLAN-phase exit-1 conflates \"not yet done\" with \"stop\".**').hexdigest())
")
ACTUAL_FP=$(python3 -c "
import json
print(json.load(open('$TMP/init-spec/myfeature/state.json'))['finding_fingerprints'][0])
")
if [[ "$EXPECTED_FP" == "$ACTUAL_FP" ]]; then
  echo "ok   [fingerprint-sha1-canonical]"
else
  echo "FAIL [fingerprint-sha1-canonical]: expected=$EXPECTED_FP actual=$ACTUAL_FP" >&2
  failures=$((failures + 1))
fi

# Rotation: second record moves current → previous.
ran=$((ran + 1))
$PY review record "$TMP/init-spec/myfeature" --report "$REVIEW_REPORT" > /dev/null
prev_count=$(python3 -c "import json; print(len(json.load(open('$TMP/init-spec/myfeature/state.json'))['previous_finding_fingerprints']))")
if [[ "$prev_count" == "3" ]]; then
  echo "ok   [review-record-rotates]"
else
  echo "FAIL [review-record-rotates]: prev_count=$prev_count" >&2
  failures=$((failures + 1))
fi

# Clean report → empty fingerprints.
ran=$((ran + 1))
CLEAN_REPORT="$TMP/clean.md"
printf 'Clean — ready to commit.\n' > "$CLEAN_REPORT"
$PY init "$TMP/clean-spec" > /dev/null
$PY approve-plan "$TMP/clean-spec" > /dev/null
$PY review record "$TMP/clean-spec" --report "$CLEAN_REPORT" > /dev/null
clean_count=$(python3 -c "import json; print(len(json.load(open('$TMP/clean-spec/state.json'))['finding_fingerprints']))")
if [[ "$clean_count" == "0" ]]; then
  echo "ok   [review-record-clean]"
else
  echo "FAIL [review-record-clean]: count=$clean_count" >&2
  failures=$((failures + 1))
fi

# --fingerprint escape hatch.
ran=$((ran + 1))
$PY init "$TMP/fp-spec" > /dev/null
$PY approve-plan "$TMP/fp-spec" > /dev/null
$PY review record "$TMP/fp-spec" --fingerprint aaaa --fingerprint bbbb > /dev/null
fp_list=$(python3 -c "import json; print(','.join(json.load(open('$TMP/fp-spec/state.json'))['finding_fingerprints']))")
if [[ "$fp_list" == "aaaa,bbbb" ]]; then
  echo "ok   [review-record-fingerprint-flag]"
else
  echo "FAIL [review-record-fingerprint-flag]: fp_list='$fp_list'" >&2
  failures=$((failures + 1))
fi

# Non-clean report with zero parsed findings → non-zero exit.
ran=$((ran + 1))
BAD_REPORT="$TMP/bad.md"
printf 'Some prose without findings.\n' > "$BAD_REPORT"
$PY init "$TMP/bad-spec" > /dev/null
$PY approve-plan "$TMP/bad-spec" > /dev/null
set +e
err=$($PY review record "$TMP/bad-spec" --report "$BAD_REPORT" 2>&1 >/dev/null)
got_exit=$?
set -e
if [[ "$got_exit" -ne 0 && "$err" == *"parsed zero findings"* ]]; then
  echo "ok   [review-record-rejects-unparseable]"
else
  echo "FAIL [review-record-rejects-unparseable]: exit=$got_exit stderr=$err" >&2
  failures=$((failures + 1))
fi

# ── worktree subcommands (against a scratch git repo) ───────────────────

GIT_DIR="$TMP/gitrepo"
mkdir -p "$GIT_DIR"
(
  cd "$GIT_DIR"
  git init -q
  git config user.email t@t
  git config user.name t
  touch a
  git add a
  git commit -qm init
  git checkout -qb base
)

(
  cd "$GIT_DIR"
  mkdir -p docs/specs/feat
  $PY init docs/specs/feat > /dev/null
  $PY approve-plan docs/specs/feat > /dev/null
)

# preflight clean.
ran=$((ran + 1))
set +e
( cd "$GIT_DIR" && $PY worktree preflight docs/specs/feat T1 T2 > /dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 ]]; then
  echo "ok   [worktree-preflight-clean]"
else
  echo "FAIL [worktree-preflight-clean]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# add T1, T2.
ran=$((ran + 1))
set +e
( cd "$GIT_DIR" && $PY worktree add docs/specs/feat T1 > /dev/null && $PY worktree add docs/specs/feat T2 > /dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 ]]; then
  wt_count=$(python3 -c "import json; print(len(json.load(open('$GIT_DIR/docs/specs/feat/state.json'))['worktrees']))")
  if [[ "$wt_count" == "2" ]]; then
    echo "ok   [worktree-add-two]"
  else
    echo "FAIL [worktree-add-two]: count=$wt_count" >&2
    failures=$((failures + 1))
  fi
else
  echo "FAIL [worktree-add-two]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# preflight after add — should surface T1 and T2 collisions.
ran=$((ran + 1))
set +e
( cd "$GIT_DIR" && $PY worktree preflight docs/specs/feat T1 > /dev/null 2>&1 )
got_exit=$?
set -e
if [[ "$got_exit" -ne 0 ]]; then
  echo "ok   [worktree-preflight-detects-stale]"
else
  echo "FAIL [worktree-preflight-detects-stale]: expected non-zero" >&2
  failures=$((failures + 1))
fi

# worktree add refuses duplicate task_id.
ran=$((ran + 1))
set +e
err=$( cd "$GIT_DIR" && $PY worktree add docs/specs/feat T1 2>&1 >/dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -ne 0 && "$err" == *"already exists"* ]]; then
  echo "ok   [worktree-add-refuses-dup]"
else
  echo "FAIL [worktree-add-refuses-dup]: exit=$got_exit stderr=$err" >&2
  failures=$((failures + 1))
fi

# worktree record — match-first / write-second.
ran=$((ran + 1))
T1_REPORT="$TMP/report-T1.md"
cat > "$T1_REPORT" <<'EOF'
## Task T1: build a thing

**Status:** ready
EOF
set +e
( cd "$GIT_DIR" && $PY worktree record docs/specs/feat T1 --status ready --report "$T1_REPORT" > /dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 && -f "$GIT_DIR/docs/specs/feat/notes/implementer-T1-0.md" ]]; then
  echo "ok   [worktree-record-writes-note]"
else
  echo "FAIL [worktree-record-writes-note]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# worktree record refuses heading/arg mismatch.
ran=$((ran + 1))
MISMATCH_REPORT="$TMP/report-mismatch.md"
cat > "$MISMATCH_REPORT" <<'EOF'
## Task T99: not the same task

**Status:** ready
EOF
set +e
err=$( cd "$GIT_DIR" && $PY worktree record docs/specs/feat T2 --status ready --report "$MISMATCH_REPORT" 2>&1 >/dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -ne 0 && "$err" == *"declares task 'T99'"* ]]; then
  echo "ok   [worktree-record-rejects-mismatch]"
else
  echo "FAIL [worktree-record-rejects-mismatch]: exit=$got_exit stderr=$err" >&2
  failures=$((failures + 1))
fi

# worktree merge — happy path.
ran=$((ran + 1))
T2_REPORT="$TMP/report-T2.md"
cat > "$T2_REPORT" <<'EOF'
## Task T2: build the other thing

**Status:** ready
EOF
(
  cd "$GIT_DIR/.worktrees/T1"
  echo "T1 work" > t1.txt
  git add t1.txt
  git commit -qm "T1"
)
(
  cd "$GIT_DIR/.worktrees/T2"
  echo "T2 work" > t2.txt
  git add t2.txt
  git commit -qm "T2"
)
( cd "$GIT_DIR" && $PY worktree record docs/specs/feat T2 --status ready --report "$T2_REPORT" > /dev/null )
set +e
( cd "$GIT_DIR" && $PY worktree merge docs/specs/feat > /dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 ]]; then
  echo "ok   [worktree-merge-happy]"
else
  echo "FAIL [worktree-merge-happy]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# worktree cleanup.
ran=$((ran + 1))
set +e
( cd "$GIT_DIR" && $PY worktree cleanup docs/specs/feat > /dev/null 2>&1 )
got_exit=$?
set -e
if [[ "$got_exit" -eq 0 && ! -d "$GIT_DIR/.worktrees/T1" && ! -d "$GIT_DIR/.worktrees/T2" ]]; then
  echo "ok   [worktree-cleanup-removes]"
else
  echo "FAIL [worktree-cleanup-removes]: exit=$got_exit" >&2
  failures=$((failures + 1))
fi

# worktree merge — conflict path. Two tasks edit the same file.
GIT_DIR2="$TMP/gitrepo2"
mkdir -p "$GIT_DIR2"
(
  cd "$GIT_DIR2"
  git init -q
  git config user.email t@t
  git config user.name t
  echo "base" > conflict.txt
  git add conflict.txt
  git commit -qm init
  git checkout -qb base
  mkdir -p docs/specs/feat
  $PY init docs/specs/feat > /dev/null
  $PY approve-plan docs/specs/feat > /dev/null
  $PY worktree add docs/specs/feat T1 > /dev/null
  $PY worktree add docs/specs/feat T2 > /dev/null
)
(
  cd "$GIT_DIR2/.worktrees/T1"
  echo "T1 edit" > conflict.txt
  git add conflict.txt
  git commit -qm "T1 conflict"
)
(
  cd "$GIT_DIR2/.worktrees/T2"
  echo "T2 edit" > conflict.txt
  git add conflict.txt
  git commit -qm "T2 conflict"
)
cat > "$TMP/conflict-T1.md" <<'EOF'
## Task T1: edit
**Status:** ready
EOF
cat > "$TMP/conflict-T2.md" <<'EOF'
## Task T2: edit
**Status:** ready
EOF
(
  cd "$GIT_DIR2"
  $PY worktree record docs/specs/feat T1 --status ready --report "$TMP/conflict-T1.md" > /dev/null
  $PY worktree record docs/specs/feat T2 --status ready --report "$TMP/conflict-T2.md" > /dev/null
)
ran=$((ran + 1))
set +e
err=$( cd "$GIT_DIR2" && $PY worktree merge docs/specs/feat 2>&1 >/dev/null )
got_exit=$?
set -e
if [[ "$got_exit" -ne 0 && "$err" == *"merge conflict on task T2"* ]]; then
  echo "ok   [worktree-merge-conflict]"
else
  echo "FAIL [worktree-merge-conflict]: exit=$got_exit stderr=$err" >&2
  failures=$((failures + 1))
fi

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
