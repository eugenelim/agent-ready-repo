#!/usr/bin/env bash
# Self-test for tools/hooks/pre-pr.sh. For each of the four layers the
# aggregator runs, plant a single-character corruption in a sandbox
# copy of the repo, invoke pre-pr.sh against it, and assert it fails
# with the matching `pre-pr: ✖ <label> failed` line. Catches the
# regression where a refactor silently drops a layer.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Clone the working tree into a real git sandbox so the drift-watch
# can call `git check-ignore` against the same .gitignore. Preserve
# symlinks (CLAUDE.md → AGENTS.md) with cp -P.
SANDBOX="$TMP/repo"
seed_sandbox() {
  rm -rf "$SANDBOX"
  mkdir -p "$SANDBOX"
  { git ls-files -z; git ls-files -z --others --exclude-standard; } \
    | while IFS= read -r -d '' f; do
    mkdir -p "$SANDBOX/$(dirname "$f")"
    cp -P "$f" "$SANDBOX/$f"
  done
  (cd "$SANDBOX" \
    && git init -q \
    && git -c user.email=t@t -c user.name=t add -A \
    && git -c user.email=t@t -c user.name=t commit -q -m baseline)
}
seed_sandbox

# A baseline run against the clean sandbox must succeed — sanity-check.
set +e
out=$(cd "$SANDBOX" && bash tools/hooks/pre-pr.sh 2>&1)
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

  # Restore clean sandbox each time (cheap; small tree).
  seed_sandbox
  (cd "$SANDBOX" && eval "$corrupt")

  set +e
  out=$(cd "$SANDBOX" && bash tools/hooks/pre-pr.sh 2>&1)
  got=$?
  set -e

  if [[ "$got" -eq 0 ]]; then
    echo "FAIL [$label]: pre-pr.sh exited 0 on corrupted sandbox" >&2
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

# 2. agent-artifact lint — corrupt an agent file's frontmatter.
#    Strip the model: line; the linter requires it.
run_corruption "agent-artifact-fail" \
  "sed -i.bak '/^model:/d' .claude/agents/adversarial-reviewer.md && rm .claude/agents/adversarial-reviewer.md.bak" \
  'pre-pr: ✖ agent-artifact lint failed'

# 3. skill-deps lint — break a dep path in the work-loop SKILL.
run_corruption "skill-deps-fail" \
  "sed -i.bak 's|docs/knowledge/patterns.jsonl|docs/knowledge/does-not-exist.jsonl|' .claude/skills/work-loop/SKILL.md && rm .claude/skills/work-loop/SKILL.md.bak" \
  'pre-pr: ✖ skill-deps lint failed'

# 4. knowledge lint — plant a malformed JSONL line.
run_corruption "knowledge-fail" \
  "printf '%s\n' '{not json' > docs/knowledge/patterns.jsonl" \
  'pre-pr: ✖ knowledge lint failed'

# 5. check-done.py — plant a state.json with plan_review_status=pending,
#    which trips the gate for both --phase implement and --phase review.
#    Drops the test if pre-pr ever stops iterating state.json files.
run_corruption "check-done-fail" \
  "mkdir -p docs/specs/example && cp .claude/skills/work-loop/assets/state.json docs/specs/example/state.json" \
  'pre-pr: ✖ check-done'

echo
if [[ "$failures" -gt 0 ]]; then
  echo "✖ Self-test: $failures of $ran cases failed" >&2
  exit 1
fi
echo "✓ Self-test: passed ($ran cases)."
