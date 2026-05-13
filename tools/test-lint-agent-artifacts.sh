#!/usr/bin/env bash
# Self-test for tools/lint-agent-artifacts.sh.
#
# Generates a deliberately-broken .claude/ tree in a tempdir, runs the
# linter against it, and asserts that each expected error pattern shows
# up in stderr. If any expected error is absent, or if the linter exits
# 0, the test fails.
#
# Fixtures live in the tempdir, not in the repo, so Claude Code's skill
# discovery does not pick them up (a broken fixture skill would otherwise
# appear in the skills list).

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── Lay out a tree of broken artifacts ────────────────────────────────────

mkdir -p \
  "$TMP/.claude/skills/wrong-name" \
  "$TMP/.claude/skills/missing-desc" \
  "$TMP/.claude/skills/no-frontmatter" \
  "$TMP/.claude/skills/orphan-dir" \
  "$TMP/.claude/agents" \
  "$TMP/.claude/commands"

# Skill: name in frontmatter mismatched, plus a broken markdown link.
cat > "$TMP/.claude/skills/wrong-name/SKILL.md" <<'EOF'
---
name: different-name
description: Frontmatter name does not match the directory name.
---

Body content. See [missing file](./nonexistent.md) for a broken link.
EOF

# Skill: description is empty.
cat > "$TMP/.claude/skills/missing-desc/SKILL.md" <<'EOF'
---
name: missing-desc
description:
---

Body.
EOF

# Skill: no frontmatter at all.
cat > "$TMP/.claude/skills/no-frontmatter/SKILL.md" <<'EOF'
# A skill body with no frontmatter

The linter must flag the missing `---` delimiters.
EOF

# Skill directory with a stray .md file and no SKILL.md.
cat > "$TMP/.claude/skills/orphan-dir/notes.md" <<'EOF'
Stray file. No SKILL.md alongside.
EOF

# Agent: name in frontmatter mismatched against filename.
cat > "$TMP/.claude/agents/wrong-filename.md" <<'EOF'
---
name: different-agent-name
description: Frontmatter name does not match the filename.
tools: Read, Grep
model: opus
---

Body.
EOF

# Agent: frontmatter has a key the linter should reject.
cat > "$TMP/.claude/agents/unknown-key.md" <<'EOF'
---
name: unknown-key
description: Frontmatter has a surprise key the linter should reject.
surprise: this-is-not-allowed
---

Body.
EOF

# Agent: frontmatter opened with --- and never closed.
cat > "$TMP/.claude/agents/unclosed-frontmatter.md" <<'EOF'
---
name: unclosed-frontmatter
description: Missing closing delimiter.

Body that looks like part of frontmatter.
EOF

# Command: valid frontmatter but empty body.
cat > "$TMP/.claude/commands/empty-body.md" <<'EOF'
---
description: Command frontmatter is fine, body is empty.
---
EOF

# ── Run linter, capture output ────────────────────────────────────────────

set +e
output="$(LINT_ROOT="$TMP" bash "$REPO_ROOT/tools/lint-agent-artifacts.sh" 2>&1)"
exit_code=$?
set -e

# ── Assertions ────────────────────────────────────────────────────────────

fail=0

if (( exit_code == 0 )); then
  echo "✖ linter exited 0; expected non-zero on broken fixtures." >&2
  fail=1
fi

# Each expected error pattern must appear in the captured output.
EXPECTED_PATTERNS=(
  "name 'different-name' does not match directory 'wrong-name'"
  "broken link → ./nonexistent.md"
  "frontmatter missing required key: description"
  "missing YAML frontmatter"
  "unexpected file in skill dir"
  "skill directory missing SKILL.md"
  "name 'different-agent-name' does not match filename 'wrong-filename'"
  "unknown frontmatter keys: ['surprise']"
  "frontmatter opened with --- but never closed"
  "body is empty"
)

for pattern in "${EXPECTED_PATTERNS[@]}"; do
  if ! grep -qF -- "$pattern" <<< "$output"; then
    echo "✖ expected error pattern not found: $pattern" >&2
    fail=1
  fi
done

if (( fail )); then
  echo
  echo "Self-test: failed." >&2
  echo "Linter output was:" >&2
  echo "---" >&2
  echo "$output" >&2
  echo "---" >&2
  exit 1
fi

echo "✓ Self-test: passed (all ${#EXPECTED_PATTERNS[@]} expected error patterns observed)."
