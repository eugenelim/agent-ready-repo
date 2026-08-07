#!/usr/bin/env bash
# Self-test for packs/core/.apm/skills/work-loop/scripts/loop-cohort.py — Phase 1.
#
# Tests Phase-1 schema contracts: check verbs, identity, init --run-id,
# approve-plan, schedule, wave, record-attempt, review inspect/record,
# disabled Phase-1 verbs, and schema-key drift against assets/state.json.
#
# Comprehensive TDD coverage lives in test-loop-cohort.py and test-loop-engine.py;
# this script retests the core contracts via the projected path and verifies
# the assets/state.json field set matches Phase-1 expectations.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SCRIPT="$REPO_ROOT/packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"
PY="python3 $SCRIPT"

failures=0
ran=0

fail() {
  local name="$1"; shift
  echo "FAIL [$name]: $*" >&2
  failures=$((failures + 1))
}

ok() {
  echo "ok   [$1]"
}

run_and_check() {
  # run_and_check <name> <want_exit> <want_substr> -- <cmd...>
  local name="$1" want_exit="$2" want_substr="$3"
  shift 3
  # consume '--'
  if [[ "$1" == "--" ]]; then shift; fi

  ran=$((ran + 1))
  local stderr_out got_exit
  set +e
  stderr_out=$("$@" 2>&1 >/dev/null)
  got_exit=$?
  set -e

  if [[ "$got_exit" -ne "$want_exit" ]]; then
    fail "$name" "expected exit $want_exit, got $got_exit (stderr: $stderr_out)"
    return
  fi
  if [[ -n "$want_substr" && "$stderr_out" != *"$want_substr"* ]]; then
    fail "$name" "stderr did not contain '$want_substr' (stderr: $stderr_out)"
    return
  fi
  ok "$name"
}

# ── Phase-1 state.json schema-key drift ─────────────────────────────────

TEMPLATE_PATH="$REPO_ROOT/.claude/skills/work-loop/assets/state.json"

ran=$((ran + 1))
if python3 - "$TEMPLATE_PATH" <<'PY'
import json, pathlib, sys
template = json.loads(pathlib.Path(sys.argv[1]).read_text())

expected_keys = {
    "schema_version", "run_id", "feature",
    "plan_review_status",
    "approved_spec_hash", "approved_plan_hash", "plan_hash",
    "schedule_waves", "current_wave_index",
    "implementation_retry_count", "max_implementation_retries",
    "last_record_attempt_cycle_id",
    "review_round_count", "review_retry_count", "max_review_retries",
    "finding_fingerprints", "previous_finding_fingerprints",
    "auto_parallel", "last_commit_sha", "worktrees",
}
# Phase-2 fields must be absent
phase2_absent = {
    "token_budget_used_pct", "token_budget_cap_pct",
    "consecutive_same_error_count", "consecutive_same_error_threshold",
    "iteration_count", "max_iterations",
}
missing = expected_keys - set(template)
extra = set(template) - expected_keys
present_p2 = phase2_absent & set(template)
if missing or extra or present_p2:
    if missing:
        print(f"schema-drift: missing={sorted(missing)}", file=sys.stderr)
    if extra:
        print(f"schema-drift: extra={sorted(extra)}", file=sys.stderr)
    if present_p2:
        print(f"schema-drift: Phase-2 fields in template={sorted(present_p2)}", file=sys.stderr)
    sys.exit(1)
PY
then
  ok "schema-phase1-keys-match"
else
  fail "schema-phase1-keys-match" "Phase-1 field set mismatch; see above"
fi

# Template must have null run_id and schema_version=1 at init.
ran=$((ran + 1))
if python3 - "$TEMPLATE_PATH" <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path(sys.argv[1]).read_text())
ok = d.get("schema_version") == 1 and d.get("run_id") is None and d.get("plan_review_status") == "pending"
if not ok:
    print(f"schema_version={d.get('schema_version')} run_id={d.get('run_id')} plan_review_status={d.get('plan_review_status')}", file=sys.stderr)
    sys.exit(1)
PY
then
  ok "template-init-defaults"
else
  fail "template-init-defaults" "template has wrong default values for Phase-1 init fields"
fi

# ── init: requires --run-id ──────────────────────────────────────────────

RUN_ID="$(python3 -c "import uuid; print(str(uuid.uuid4()))")"
SPEC1="$TMP/spec1"
mkdir -p "$SPEC1"

run_and_check "init-no-run-id-fails" 2 "" -- $PY init "$SPEC1"

run_and_check "init-with-run-id-succeeds" 0 "" -- $PY init "$SPEC1" --run-id "$RUN_ID"

# State must carry run_id and schema_version=1.
ran=$((ran + 1))
if python3 - "$SPEC1/state.json" "$RUN_ID" <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path(sys.argv[1]).read_text())
ok = d.get("run_id") == sys.argv[2] and d.get("schema_version") == 1 and d.get("plan_review_status") == "pending"
if not ok:
    print(f"run_id={d.get('run_id')!r} schema_version={d.get('schema_version')} plan_review_status={d.get('plan_review_status')!r}", file=sys.stderr)
    sys.exit(1)
PY
then
  ok "init-state-run-id-correct"
else
  fail "init-state-run-id-correct" "state.json has wrong field values after init"
fi

# Init refuses if state.json already exists (no --force in Phase 1).
run_and_check "init-refuses-if-state-exists" 1 "" -- $PY init "$SPEC1" --run-id "$RUN_ID"

# ── identity ─────────────────────────────────────────────────────────────

run_and_check "identity-success" 0 "" -- $PY identity "$SPEC1" --expect-run-id "$RUN_ID"
run_and_check "identity-mismatch" 1 "" -- $PY identity "$SPEC1" --expect-run-id "wrong-id"

SPEC_NOSTATE="$TMP/spec-nostate"
mkdir -p "$SPEC_NOSTATE"
run_and_check "identity-absent-state" 1 "" -- $PY identity "$SPEC_NOSTATE"

# ── plan check-current before approve-plan ───────────────────────────────

# Need spec.md + plan.md for approve-plan
cat > "$SPEC1/spec.md" <<'EOF'
# Spec

- **Status:** Approved

## Acceptance criteria

- [ ] AC1
EOF
cat > "$SPEC1/plan.md" <<'EOF'
# Plan

### T1

**Depends on:** none

### T2

**Depends on:** T1
EOF

run_and_check "plan-check-current-not-approved" 1 "" -- $PY plan check-current "$SPEC1"

# Rewrite plan.md with Status: Approved so the crash-window guard in approve-plan passes.
cat > "$SPEC1/plan.md" <<'EOF'
# Plan

- **Status:** Approved

### T1

**Depends on:** none

### T2

**Depends on:** T1
EOF

# ── approve-plan ──────────────────────────────────────────────────────────

run_and_check "approve-plan-no-run-id-fails" 2 "" -- $PY approve-plan "$SPEC1"
run_and_check "approve-plan-with-run-id" 0 "" -- $PY approve-plan "$SPEC1" --expect-run-id "$RUN_ID"

ran=$((ran + 1))
if python3 - "$SPEC1/state.json" <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path(sys.argv[1]).read_text())
if d.get("plan_review_status") != "approved":
    print(f"plan_review_status={d.get('plan_review_status')!r}", file=sys.stderr)
    sys.exit(1)
if not isinstance(d.get("approved_spec_hash"), str) or len(d["approved_spec_hash"]) != 64:
    print(f"approved_spec_hash={d.get('approved_spec_hash')!r}", file=sys.stderr)
    sys.exit(1)
if not isinstance(d.get("approved_plan_hash"), str) or len(d["approved_plan_hash"]) != 64:
    print(f"approved_plan_hash={d.get('approved_plan_hash')!r}", file=sys.stderr)
    sys.exit(1)
PY
then
  ok "approve-plan-writes-hashes"
else
  fail "approve-plan-writes-hashes" "approve-plan did not write expected fields"
fi

run_and_check "plan-check-current-approved" 0 "" -- $PY plan check-current "$SPEC1"

# ── check --phase stub verbs ──────────────────────────────────────────────

# check --phase implement: stub, always exits 0
run_and_check "check-phase-implement-stub" 0 "" -- $PY check "$SPEC1" --phase implement

# check --phase gates-failed: cap detection
python3 -c "
import json, pathlib
p = pathlib.Path('$SPEC1/state.json')
d = json.loads(p.read_text())
d['implementation_retry_count'] = 5
d['max_implementation_retries'] = 5
p.write_text(json.dumps(d))
"
run_and_check "check-phase-gates-failed-at-cap" 1 "cap" -- $PY check "$SPEC1" --phase gates-failed

# Reset counter for remaining tests
python3 -c "
import json, pathlib, sys
p = pathlib.Path('$SPEC1/state.json')
d = json.loads(p.read_text())
d['implementation_retry_count'] = 0
p.write_text(json.dumps(d))
"

run_and_check "check-phase-gates-failed-under-cap" 0 "" -- $PY check "$SPEC1" --phase gates-failed

# check --phase review: retry cap
python3 -c "
import json, pathlib
p = pathlib.Path('$SPEC1/state.json')
d = json.loads(p.read_text())
d['review_retry_count'] = 5
d['max_review_retries'] = 5
p.write_text(json.dumps(d))
"
run_and_check "check-phase-review-at-cap" 1 "" -- $PY check "$SPEC1" --phase review

python3 -c "
import json, pathlib
p = pathlib.Path('$SPEC1/state.json')
d = json.loads(p.read_text())
d['review_retry_count'] = 0
p.write_text(json.dumps(d))
"

# ── schedule ──────────────────────────────────────────────────────────────

run_and_check "schedule-no-run-id-fails" 1 "" -- $PY schedule "$SPEC1"
run_and_check "schedule-with-run-id" 0 "" -- $PY schedule "$SPEC1" --expect-run-id "$RUN_ID"

ran=$((ran + 1))
if python3 - "$SPEC1/state.json" <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path(sys.argv[1]).read_text())
if not d.get("schedule_waves") or not isinstance(d["schedule_waves"], list):
    print(f"schedule_waves={d.get('schedule_waves')!r}", file=sys.stderr)
    sys.exit(1)
if d.get("plan_hash") is None:
    print("plan_hash is None after schedule", file=sys.stderr)
    sys.exit(1)
if d.get("current_wave_index") != 0:
    print(f"current_wave_index={d.get('current_wave_index')!r}", file=sys.stderr)
    sys.exit(1)
PY
then
  ok "schedule-persists-waves-and-hash"
else
  fail "schedule-persists-waves-and-hash" "schedule did not write expected state"
fi

run_and_check "schedule-check-current-passes" 0 "" -- $PY schedule check-current "$SPEC1"

# Mutate plan.md → schedule check-current fails
echo "# Plan (modified)" > "$SPEC1/plan.md"
run_and_check "schedule-check-current-detects-change" 1 "" -- $PY schedule check-current "$SPEC1"

# Restore plan.md
cat > "$SPEC1/plan.md" <<'EOF'
# Plan

### T1

**Depends on:** none

### T2

**Depends on:** T1
EOF

# ── disabled Phase-1 verbs ────────────────────────────────────────────────

run_and_check "disabled-dispatch-decision" 1 "disabled" -- $PY dispatch-decision --branch main
run_and_check "disabled-auto-parallel" 1 "disabled" -- $PY auto-parallel "$SPEC1"
run_and_check "disabled-worktree-add" 1 "disabled" -- $PY worktree add "$SPEC1" T1

# ── wave check / advance ──────────────────────────────────────────────────

# Current state has current_wave_index=0, waves=[[T1],[T2]]
# With 2 waves, index=0 → more remain
run_and_check "wave-check-more-index0" 0 "" -- $PY wave check "$SPEC1" --expect more

# Advance to index 1
run_and_check "wave-advance-0-to-1" 0 "" -- $PY wave advance "$SPEC1" --from-index 0 --expect-run-id "$RUN_ID"

ran=$((ran + 1))
idx=$(python3 -c "import json; print(json.load(open('$SPEC1/state.json'))['current_wave_index'])")
if [[ "$idx" == "1" ]]; then
  ok "wave-advance-current-index-updated"
else
  fail "wave-advance-current-index-updated" "expected current_wave_index=1, got $idx"
fi

run_and_check "wave-check-last-at-index1" 0 "" -- $PY wave check "$SPEC1" --expect last
run_and_check "wave-advance-refuses-final" 1 "" -- $PY wave advance "$SPEC1" --from-index 1 --expect-run-id "$RUN_ID"

# ── record-attempt ────────────────────────────────────────────────────────

CYCLE1="${RUN_ID}:1"
run_and_check "record-attempt-increment" 0 "" -- $PY record-attempt "$SPEC1" --phase implement --cycle-id "$CYCLE1" --expect-run-id "$RUN_ID"

ran=$((ran + 1))
cnt=$(python3 -c "import json; print(json.load(open('$SPEC1/state.json'))['implementation_retry_count'])")
if [[ "$cnt" == "1" ]]; then
  ok "record-attempt-counter-is-1"
else
  fail "record-attempt-counter-is-1" "expected implementation_retry_count=1, got $cnt"
fi

# Idempotent: same cycle-id is a no-op
run_and_check "record-attempt-idempotent" 0 "" -- $PY record-attempt "$SPEC1" --phase implement --cycle-id "$CYCLE1" --expect-run-id "$RUN_ID"

ran=$((ran + 1))
cnt2=$(python3 -c "import json; print(json.load(open('$SPEC1/state.json'))['implementation_retry_count'])")
if [[ "$cnt2" == "1" ]]; then
  ok "record-attempt-idempotent-count-unchanged"
else
  fail "record-attempt-idempotent-count-unchanged" "expected count=1 after idempotent replay, got $cnt2"
fi

# ── review inspect ────────────────────────────────────────────────────────

FINDINGS_REPORT="$TMP/findings.md"
cat > "$FINDINGS_REPORT" <<'EOF'
## Blockers

**1. Missing null check.** `src/foo.py:42`. Value not validated. Fix: add guard.

**2. Typo.** `src/bar.py:10`. Spelling error. Fix: fix it.
EOF

CLEAN_REPORT="$TMP/clean.md"
printf 'Review complete.\n\nClean \xe2\x80\x94 ready to commit.\n' > "$CLEAN_REPORT"

ran=$((ran + 1))
result=$(python3 $SCRIPT review inspect "$SPEC1" --report "$FINDINGS_REPORT" --json 2>/dev/null)
classification=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['classification'])")
if [[ "$classification" == "findings" ]]; then
  ok "review-inspect-findings"
else
  fail "review-inspect-findings" "expected classification=findings, got $classification"
fi

ran=$((ran + 1))
result_clean=$(python3 $SCRIPT review inspect "$SPEC1" --report "$CLEAN_REPORT" --json 2>/dev/null)
class_clean=$(echo "$result_clean" | python3 -c "import sys,json; print(json.load(sys.stdin)['classification'])")
if [[ "$class_clean" == "clean" ]]; then
  ok "review-inspect-clean"
else
  fail "review-inspect-clean" "expected classification=clean, got $class_clean"
fi

# ── review record ────────────────────────────────────────────────────────

# --fingerprint path: increments both counters.
# NOTE: this fixture is sequential and the counters accumulate — a new
# `review record` case inserted here shifts every downstream count assertion.
# Fingerprint-width coverage lives in test-fingerprint-width.py instead.
# 40-hex (SHA-1) is the legacy width, still accepted so a cohort that was
# mid-review when core upgraded to SHA-256 can finish.
run_and_check "review-record-fingerprint" 0 "" -- $PY review record "$SPEC1" --fingerprint "aabbccdd112233445566778899001122334455aa" --expect-run-id "$RUN_ID"

ran=$((ran + 1))
rr=$(python3 -c "import json; d=json.load(open('$SPEC1/state.json')); print(d['review_round_count'], d['review_retry_count'])")
if [[ "$rr" == "1 1" ]]; then
  ok "review-record-fingerprint-both-counters"
else
  fail "review-record-fingerprint-both-counters" "expected round_count=1 retry_count=1, got '$rr'"
fi

# --report (clean) path: increments only round_count
run_and_check "review-record-report-clean" 0 "" -- $PY review record "$SPEC1" --report "$CLEAN_REPORT" --expect-run-id "$RUN_ID"

ran=$((ran + 1))
rr2=$(python3 -c "import json; d=json.load(open('$SPEC1/state.json')); print(d['review_round_count'], d['review_retry_count'])")
if [[ "$rr2" == "2 1" ]]; then
  ok "review-record-report-only-round-counter"
else
  fail "review-record-report-only-round-counter" "expected round=2 retry=1, got '$rr2'"
fi

# --report with non-clean report: fails
run_and_check "review-record-report-non-clean-fails" 1 "" -- $PY review record "$SPEC1" --report "$FINDINGS_REPORT" --expect-run-id "$RUN_ID"

# ── status is read-only ───────────────────────────────────────────────────

ran=$((ran + 1))
before=$(python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$SPEC1/state.json")
python3 $SCRIPT status "$SPEC1" --json > /dev/null 2>&1
after=$(python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$SPEC1/state.json")
if [[ "$before" == "$after" ]]; then
  ok "status-read-only"
else
  fail "status-read-only" "state.json was mutated by status"
fi

# ── reset ────────────────────────────────────────────────────────────────

run_and_check "reset-deletes-state" 0 "" -- $PY reset "$SPEC1"
if [[ ! -f "$SPEC1/state.json" ]]; then
  ran=$((ran + 1)); ok "reset-state-gone"
else
  ran=$((ran + 1)); fail "reset-state-gone" "state.json still exists after reset"
fi

run_and_check "reset-idempotent" 0 "" -- $PY reset "$SPEC1"

# ── Python test delegation ────────────────────────────────────────────────
# Run the comprehensive Python test suite against the pack source.

PYTEST="$REPO_ROOT/packs/core/tests/skills/work-loop/test-loop-cohort.py"
if [[ -f "$PYTEST" ]]; then
  ran=$((ran + 1))
  if python3 "$PYTEST" > /dev/null 2>&1; then
    ok "python-test-loop-cohort-suite"
  else
    fail "python-test-loop-cohort-suite" "test-loop-cohort.py reported failures (run it directly for details)"
  fi
fi

PYTEST_ENGINE="$REPO_ROOT/packs/core/tests/skills/work-loop/test-loop-engine.py"
if [[ -f "$PYTEST_ENGINE" ]]; then
  ran=$((ran + 1))
  if python3 "$PYTEST_ENGINE" > /dev/null 2>&1; then
    ok "python-test-loop-engine-suite"
  else
    fail "python-test-loop-engine-suite" "test-loop-engine.py reported failures (run it directly for details)"
  fi
fi

PYTEST_FRESHNESS="$REPO_ROOT/packs/core/tests/skills/work-loop/test-check-base-freshness.py"
if [[ -f "$PYTEST_FRESHNESS" ]]; then
  ran=$((ran + 1))
  if _freshness_out=$(python3 "$PYTEST_FRESHNESS" 2>&1); then
    ok "python-test-check-base-freshness-suite"
  else
    _freshness_fails=$(echo "$_freshness_out" | grep '^FAIL' | tr '\n' '; ')
    fail "python-test-check-base-freshness-suite" "test-check-base-freshness.py: ${_freshness_fails:-run it directly for details}"
  fi
fi

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
