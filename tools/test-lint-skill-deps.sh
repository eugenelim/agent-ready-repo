#!/usr/bin/env bash
# Self-test for tools/lint-skill-deps.sh.
#
# Generates broken skill/agent manifests in a tempdir, runs the linter
# against them, and asserts that each of the linter's three err() sites
# (missing file, missing anchor, dep-is-a-directory) fires. Then runs the
# linter against a happy-path fixture and asserts exit 0. Finally runs
# the linter against the real in-tree state as a regression guard — a
# refactor that broke the parser would otherwise land green here even
# while it broke real installs.
#
# Fixtures live in the tempdir, not in the repo, so Claude Code's skill
# discovery does not pick them up (a broken fixture skill would otherwise
# appear in the skills list).

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

LINTER="$REPO_ROOT/tools/lint-skill-deps.sh"

# ── Tempdirs (both up front so the EXIT trap can clean both safely) ──────

BAD="$(mktemp -d)"
GOOD="$(mktemp -d)"
trap 'rm -rf "$BAD" "$GOOD"' EXIT

# ── Broken-fixture tree ───────────────────────────────────────────────────

mkdir -p \
  "$BAD/.claude/skills/missing-file" \
  "$BAD/.claude/skills/missing-anchor" \
  "$BAD/.claude/skills/dep-is-dir" \
  "$BAD/docs" \
  "$BAD/some-dir-target"

# A real file the missing-anchor fixture can point at (so we hit the
# anchor-resolution err(), not the missing-file err()).
cat > "$BAD/docs/real.md" <<'EOF'
# A real heading

Body content. The slug for the heading above is `a-real-heading`.
EOF

# Skill: dependency points at a file that does not exist.
cat > "$BAD/.claude/skills/missing-file/SKILL.md" <<'EOF'
---
name: missing-file
description: Dep points at a file that does not exist.
dependencies:
  - docs/does-not-exist.md
---

Body.
EOF

# Skill: dependency cites a file that exists, but with an anchor the
# file does not define.
cat > "$BAD/.claude/skills/missing-anchor/SKILL.md" <<'EOF'
---
name: missing-anchor
description: Dep file exists but anchor does not.
dependencies:
  - docs/real.md#nope-not-here
---

Body.
EOF

# Skill: dependency points at a directory rather than a file.
cat > "$BAD/.claude/skills/dep-is-dir/SKILL.md" <<'EOF'
---
name: dep-is-dir
description: Dep points at a directory, not a file.
dependencies:
  - some-dir-target
---

Body.
EOF

# ── Run linter against broken fixtures ────────────────────────────────────

set +e
bad_output="$(LINT_ROOT="$BAD" bash "$LINTER" 2>&1)"
bad_exit=$?
set -e

fail=0

if (( bad_exit == 0 )); then
  echo "✖ linter exited 0 against broken fixtures; expected non-zero." >&2
  fail=1
fi

EXPECTED_PATTERNS=(
  "dependency points at missing file: docs/does-not-exist.md"
  "anchor #nope-not-here not found in docs/real.md"
  "dependency points at a directory: some-dir-target"
)

for pattern in "${EXPECTED_PATTERNS[@]}"; do
  if ! grep -qF -- "$pattern" <<< "$bad_output"; then
    echo "✖ expected error pattern not found: $pattern" >&2
    fail=1
  fi
done

# ── Happy-path fixture ────────────────────────────────────────────────────

mkdir -p \
  "$GOOD/.claude/skills/happy" \
  "$GOOD/docs"

cat > "$GOOD/docs/real.md" <<'EOF'
# A real heading

Body.
EOF

cat > "$GOOD/.claude/skills/happy/SKILL.md" <<'EOF'
---
name: happy
description: Valid deps; should lint clean.
dependencies:
  - docs/real.md
  - docs/real.md#a-real-heading
---

Body.
EOF

set +e
good_output="$(LINT_ROOT="$GOOD" bash "$LINTER" 2>&1)"
good_exit=$?
set -e

if (( good_exit != 0 )); then
  echo "✖ linter exited $good_exit against happy-path fixture; expected 0." >&2
  echo "Output was:" >&2
  echo "$good_output" >&2
  fail=1
fi

# ── Production-tree regression guard ──────────────────────────────────────
# Run the real linter against the real tree (no LINT_ROOT override). A
# regression in the parser or anchor resolver that flipped a working
# manifest red would otherwise land green here.

set +e
real_output="$(bash "$LINTER" 2>&1)"
real_exit=$?
set -e

if (( real_exit != 0 )); then
  echo "✖ linter failed against in-tree manifests (production regression guard)." >&2
  echo "Output was:" >&2
  echo "$real_output" >&2
  fail=1
fi

# ── Report ────────────────────────────────────────────────────────────────

if (( fail )); then
  echo
  echo "Self-test: failed." >&2
  echo "Broken-fixture linter output was:" >&2
  echo "---" >&2
  echo "$bad_output" >&2
  echo "---" >&2
  exit 1
fi

echo "✓ Self-test: passed (${#EXPECTED_PATTERNS[@]} broken-fixture patterns observed, happy-path clean, in-tree clean)."
