#!/usr/bin/env bash
# T9: shell-test for the core pack's session-start hook (AC20).
#
# Co-locating hook + skill tests under the CLI's tests/ tree is a
# deliberate Concern-13 deferral (plan.md, line ~50): a pack-level
# test harness lands in a future spec. Until then these tests sit
# alongside CLI tests so a single `pytest packages/agentbundle/`
# (plus a CI step that runs this file) covers both.
#
# Asserts the scope-permutation matrix: {repo only, user only, both,
# neither} and the patterns/nudge ordering.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
HOOK="$REPO_ROOT/packs/core/.apm/hooks/session-start.sh"

if [[ ! -x "$HOOK" ]]; then
  echo "test_session_start.sh: hook not executable at $HOOK" >&2
  exit 1
fi

# Each test runs in a fresh tmp dir; we override the marker paths via
# ADAPT_REPO_MARKER / ADAPT_USER_MARKER. KNOWLEDGE_FILE is also
# pinned to an empty path so the knowledge block is silent and we can
# assert on the nudge line directly.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

REPO_MARKER="$TMP/repo-marker.toml"
USER_MARKER="$TMP/user-marker.toml"
EMPTY_KNOWLEDGE="$TMP/empty.jsonl"
touch "$EMPTY_KNOWLEDGE"

# Patterns file with one entry, used by the ordering test.
PATTERNS="$TMP/patterns.jsonl"
cat > "$PATTERNS" <<'EOF'
{"id":"k1","kind":"pattern","scope":"*","title":"test entry","body":"x","source":"-"}
EOF

PASS=0
FAIL=0

assert_contains() {
  local label="$1" haystack="$2" needle="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    PASS=$((PASS + 1))
    echo "PASS: $label"
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $label"
    echo "  expected to contain: $needle"
    echo "  got: $haystack"
  fi
}

assert_not_contains() {
  local label="$1" haystack="$2" needle="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    PASS=$((PASS + 1))
    echo "PASS: $label"
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $label"
    echo "  expected NOT to contain: $needle"
    echo "  got: $haystack"
  fi
}

# --- Test 1: repo marker only -------------------------------------------------
rm -f "$REPO_MARKER" "$USER_MARKER"
cat > "$REPO_MARKER" <<'EOF'
marker-schema-version = "0.1"

[[packs-installed]]
name = "core"
version = "0.1.0"
installed-at = "2026-05-23T14:00:00Z"
unresolved-markers = []
new-companions = []
EOF
out=$(ADAPT_REPO_MARKER="$REPO_MARKER" \
      ADAPT_USER_MARKER="$USER_MARKER" \
      KNOWLEDGE_FILE="$EMPTY_KNOWLEDGE" \
      "$HOOK" 2>/dev/null)
assert_contains "repo-marker-only emits nudge" "$out" \
  "=== adapt-to-project: 1 pack(s) pending adaptation across 1 scope(s): core"

# --- Test 2: user marker only -------------------------------------------------
rm -f "$REPO_MARKER" "$USER_MARKER"
cat > "$USER_MARKER" <<'EOF'
marker-schema-version = "0.1"

[[packs-installed]]
name = "future-user-pack"
version = "0.1.0"
installed-at = "2026-05-23T14:00:00Z"
unresolved-markers = []
new-companions = []
EOF
out=$(ADAPT_REPO_MARKER="$REPO_MARKER" \
      ADAPT_USER_MARKER="$USER_MARKER" \
      KNOWLEDGE_FILE="$EMPTY_KNOWLEDGE" \
      "$HOOK" 2>/dev/null)
assert_contains "user-marker-only emits nudge" "$out" \
  "=== adapt-to-project: 1 pack(s) pending adaptation across 1 scope(s): future-user-pack"

# --- Test 3: both markers, names lexicographically sorted ---------------------
rm -f "$REPO_MARKER" "$USER_MARKER"
cat > "$REPO_MARKER" <<'EOF'
marker-schema-version = "0.1"

[[packs-installed]]
name = "monorepo-extras"
version = "0.1.0"
installed-at = "2026-05-23T14:00:00Z"
unresolved-markers = []
new-companions = []
EOF
cat > "$USER_MARKER" <<'EOF'
marker-schema-version = "0.1"

[[packs-installed]]
name = "alpha-user-pack"
version = "0.1.0"
installed-at = "2026-05-23T14:00:00Z"
unresolved-markers = []
new-companions = []
EOF
out=$(ADAPT_REPO_MARKER="$REPO_MARKER" \
      ADAPT_USER_MARKER="$USER_MARKER" \
      KNOWLEDGE_FILE="$EMPTY_KNOWLEDGE" \
      "$HOOK" 2>/dev/null)
assert_contains "both-markers emits combined nudge with K=2" "$out" \
  "=== adapt-to-project: 2 pack(s) pending adaptation across 2 scope(s): alpha-user-pack, monorepo-extras"

# --- Test 4: neither marker present, output is silent for adapt nudge ---------
rm -f "$REPO_MARKER" "$USER_MARKER"
out=$(ADAPT_REPO_MARKER="$REPO_MARKER" \
      ADAPT_USER_MARKER="$USER_MARKER" \
      KNOWLEDGE_FILE="$EMPTY_KNOWLEDGE" \
      "$HOOK" 2>/dev/null)
assert_not_contains "no-markers silent for adapt nudge" "$out" \
  "adapt-to-project:"

# --- Test 5: knowledge block emits first, nudge second ------------------------
rm -f "$REPO_MARKER" "$USER_MARKER"
cat > "$REPO_MARKER" <<'EOF'
marker-schema-version = "0.1"

[[packs-installed]]
name = "core"
version = "0.1.0"
installed-at = "2026-05-23T14:00:00Z"
unresolved-markers = []
new-companions = []
EOF
out=$(ADAPT_REPO_MARKER="$REPO_MARKER" \
      ADAPT_USER_MARKER="$USER_MARKER" \
      KNOWLEDGE_FILE="$PATTERNS" \
      "$HOOK" 2>/dev/null)
# Knowledge header must precede the adapt nudge.
knowledge_pos=$(printf '%s' "$out" | grep -n "=== knowledge ===" | head -1 | cut -d: -f1)
adapt_pos=$(printf '%s' "$out" | grep -n "=== adapt-to-project:" | head -1 | cut -d: -f1)
if [[ -n "$knowledge_pos" && -n "$adapt_pos" && "$knowledge_pos" -lt "$adapt_pos" ]]; then
  PASS=$((PASS + 1))
  echo "PASS: knowledge block before adapt nudge"
else
  FAIL=$((FAIL + 1))
  echo "FAIL: knowledge block before adapt nudge"
  echo "  knowledge_pos=$knowledge_pos adapt_pos=$adapt_pos"
  echo "  output: $out"
fi

echo
echo "PASS=$PASS FAIL=$FAIL"
if (( FAIL > 0 )); then
  exit 1
fi
exit 0
