#!/usr/bin/env bash
# Self-test for tools/pre-pr-catalogue.py (this catalogue's full gate: the 8
# catalogue checks + delegation to the shipped tools/hooks/pre-pr.py). For each
# layer the aggregator runs, plant a single-character corruption in a sandbox
# copy of the repo, invoke the catalogue hook against it, and assert it fails
# with the matching `pre-pr: ✖ <label> failed` line. Catches the regression
# where a refactor silently drops a layer. (Covers the 4 linters it corrupts +
# loop-cohort; the other catalogue checks are covered by their own CI jobs.)

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Clone the working tree into a real git sandbox so the drift-watch
# can call `git check-ignore` against the same .gitignore. Symlink
# preservation is handled and asserted by tools/seed_test_sandbox.py.
SANDBOX="$TMP/repo"
seed_sandbox() {
  # GitHub Actions runners have intermittently hit
  # `rm: cannot remove '<sandbox>/.git': Directory not empty` between
  # cases — a fs/git race where the parent git's housekeeping holds an
  # object briefly after our `git commit` returns. Tolerate the partial
  # rm under `set -e`: if anything's left, retry after a tick, then
  # rely on `git init` to reinitialize whatever survives.
  rm -rf "$SANDBOX" 2>/dev/null || true
  if [ -e "$SANDBOX" ]; then
    sleep 0.2
    rm -rf "$SANDBOX" 2>/dev/null || true
  fi
  mkdir -p "$SANDBOX"
  # One process, rather than the `mkdir -p` + `cp -P` per file this used to do.
  # The seeder also verifies that every symlink it copies landed as a symlink.
  # Checked explicitly: `set -e` is not in effect here (line 10 sets only -uo),
  # so an unchecked failure would seed a partial tree and fail later as a
  # confusing case failure. Rationale and timings:
  # docs/specs/test-sandbox-seed-cost/spec.md
  if ! python3 tools/seed_test_sandbox.py "$SANDBOX"; then
    echo "FAIL [seed]: could not seed the sandbox" >&2
    exit 1
  fi
  (cd "$SANDBOX" \
    && git init -q \
    && git -c user.email=t@t -c user.name=t add -A \
    && git -c user.email=t@t -c user.name=t commit -q -m baseline)
}
seed_sandbox

# A baseline run against the clean sandbox must succeed — sanity-check.
set +e
out=$(cd "$SANDBOX" && python3 tools/pre-pr-catalogue.py 2>&1)
got=$?
set -e
if [[ "$got" -ne 0 ]]; then
  echo "FAIL [baseline]: clean sandbox should pass, got exit $got" >&2
  echo "  output: $out" >&2
  exit 1
fi
echo "ok   [baseline]"

failures=0
ran=1

# run_corruption <label> <corruption-shell> <expected-failure-substr>
run_corruption() {
  local label="$1" corrupt="$2" want="$3"
  ran=$((ran + 1))

  # Restore a clean sandbox each time — per-case isolation is load-bearing (one
  # case plants a malformed patterns.jsonl, others write under .claude/), so
  # every case must start from a fresh tree rather than an unwound one.
  seed_sandbox
  (cd "$SANDBOX" && eval "$corrupt")

  set +e
  out=$(cd "$SANDBOX" && python3 tools/pre-pr-catalogue.py 2>&1)
  got=$?
  set -e

  if [[ "$got" -eq 0 ]]; then
    echo "FAIL [$label]: pre-pr.py exited 0 on corrupted sandbox" >&2
    echo "  output: $out" >&2
    failures=$((failures + 1))
    return
  fi
  if [[ "$out" != *"$want"* ]]; then
    echo "FAIL [$label]: missing expected failure substring '$want'" >&2
    echo "  output: $out" >&2
    failures=$((failures + 1))
    return
  fi
  echo "ok   [$label]"
}

# 1. agents-md hygiene — corrupt the root AGENTS.md so the linter trips.
#    Removing the file is the surest single-step corruption.
run_corruption "agents-md-fail" \
  'rm AGENTS.md' \
  'pre-pr: ✖ agents-md hygiene failed'

# 2. agent-artifact lint (now in agentbundle catalogue verify step 11) — add a new
#    agent file missing the required model: field. Creating a new file avoids
#    triggering the self-host drift check (which runs before catalogue verify and
#    compares projected output vs pack source; modifying an existing committed
#    output file would trip that check first).
run_corruption "agent-artifact-fail" \
  "printf -- '---\nname: bad-agent\ndescription: Agent missing model field.\n---\n\nBody text.\n' > .claude/agents/bad-agent.md" \
  'pre-pr: ✖ catalogue verify failed'

# 3. skill-spec lint — add a new projected SKILL.md that contains an install-path
#    reference (.claude/skills/…), which the spec linter refuses.  Writing a new
#    file avoids mutating a source pack file (which would trip self-host drift).
run_corruption "skill-spec-fail" \
  "mkdir -p .claude/skills/test-bad && printf -- '---\nname: test-bad\ndescription: Test bad skill.\n---\n\nSee \`.claude/skills/work-loop/SKILL.md\` for the loop.\n' > .claude/skills/test-bad/SKILL.md" \
  'pre-pr: ✖ skill-spec lint failed'

# 4. knowledge lint — plant a malformed JSONL line.
run_corruption "knowledge-fail" \
  "printf '%s\n' '{not json' > docs/knowledge/patterns.jsonl" \
  'pre-pr: ✖ knowledge lint failed'

# 4. loop-cohort check — plant a state.json with review_retry_count at cap,
#    which trips the check --phase review gate.
#    Drops the test if pre-pr ever stops iterating state.json files.
run_corruption "loop-cohort-fail" \
  "mkdir -p docs/specs/example && python3 -c \"import json,pathlib; p=pathlib.Path('.claude/skills/work-loop/assets/state.json'); s=json.loads(p.read_text()); s['review_retry_count']=int(s['max_review_retries']); pathlib.Path('docs/specs/example/state.json').write_text(json.dumps(s))\"" \
  'pre-pr: ✖ loop-cohort check'

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
