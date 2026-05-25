#!/usr/bin/env bash
# Self-test for tools/lint-agent-artifacts.py.
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
  "$TMP/.claude/skills/unknown-top-level-key" \
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

# Skill: frontmatter carries a key outside the agentskills.io spec set
# (project-specific data belongs under `metadata:`, not at top level).
cat > "$TMP/.claude/skills/unknown-top-level-key/SKILL.md" <<'EOF'
---
name: unknown-top-level-key
description: Carries a non-spec top-level key the linter should refuse.
bogus: this-is-not-allowed
---

Body.
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

# Agent: frontmatter is otherwise valid but does not declare `model:`.
cat > "$TMP/.claude/agents/missing-model.md" <<'EOF'
---
name: missing-model
description: Agent has no model declaration. Linter must require one.
tools: Read, Grep
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
output="$(LINT_ROOT="$TMP" python3 "$REPO_ROOT/tools/lint-agent-artifacts.py" 2>&1)"
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
  "unknown frontmatter keys: ['bogus']"
  "frontmatter opened with --- but never closed"
  "body is empty"
  "missing required key: model"
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

# ── Credentialed-skill frontmatter fixtures (per skill-secrets spec § AC25) ──
# These three cases need separate trees because the positive and negative
# cases must produce different lint exit codes — the existing harness above
# mixes pass-and-fail fixtures in one tree and grep-asserts patterns; that
# shape can't carry an "exit 0" assertion for a single conforming skill.

TMP_CRED_OK="$(mktemp -d)"
TMP_CRED_BAD_BOOL="$(mktemp -d)"
TMP_CRED_BAD_CLASS="$(mktemp -d)"
trap 'rm -rf "$TMP" "$TMP_CRED_OK" "$TMP_CRED_BAD_BOOL" "$TMP_CRED_BAD_CLASS"' EXIT

# Positive: a conforming credentialed skill with boolean true + valid class
# nested under the spec-blessed `metadata:` escape hatch.
mkdir -p "$TMP_CRED_OK/.claude/skills/conforming-credentialed"
cat > "$TMP_CRED_OK/.claude/skills/conforming-credentialed/SKILL.md" <<'EOF'
---
name: conforming-credentialed
description: A credentialed skill with valid frontmatter keys; the lint must accept it.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---

Body content.
EOF

set +e
out_ok="$(LINT_ROOT="$TMP_CRED_OK" python3 "$REPO_ROOT/tools/lint-agent-artifacts.py" 2>&1)"
exit_ok=$?
set -e

if (( exit_ok != 0 )); then
  echo "✖ conforming-credentialed: lint exited $exit_ok; expected 0." >&2
  echo "Linter output was:" >&2
  echo "---" >&2
  echo "$out_ok" >&2
  echo "---" >&2
  exit 1
fi

# Negative: credentialed value is a quoted string, not a YAML boolean
# (nested under `metadata:` per the new shape).
mkdir -p "$TMP_CRED_BAD_BOOL/.claude/skills/bad-credentialed"
cat > "$TMP_CRED_BAD_BOOL/.claude/skills/bad-credentialed/SKILL.md" <<'EOF'
---
name: bad-credentialed
description: credentialed key is a string, not a boolean; lint must reject.
metadata:
  credentialed: "yes"
---

Body content.
EOF

set +e
out_bad_bool="$(LINT_ROOT="$TMP_CRED_BAD_BOOL" python3 "$REPO_ROOT/tools/lint-agent-artifacts.py" 2>&1)"
exit_bad_bool=$?
set -e

fail=0
if (( exit_bad_bool == 0 )); then
  echo "✖ bad-credentialed: lint exited 0; expected non-zero." >&2
  fail=1
fi
if ! grep -qF -- "credentialed" <<< "$out_bad_bool"; then
  echo "✖ bad-credentialed: stderr missing substring 'credentialed'" >&2
  fail=1
fi
if ! grep -qF -- "must be boolean" <<< "$out_bad_bool"; then
  echo "✖ bad-credentialed: stderr missing substring 'must be boolean'" >&2
  fail=1
fi

# Negative: primitive-class value is not one of the two allowed strings
# (nested under `metadata:` per the new shape).
mkdir -p "$TMP_CRED_BAD_CLASS/.claude/skills/bad-primitive-class"
cat > "$TMP_CRED_BAD_CLASS/.claude/skills/bad-primitive-class/SKILL.md" <<'EOF'
---
name: bad-primitive-class
description: primitive-class value is unknown; lint must reject.
metadata:
  credentialed: true
  primitive-class: mcp-broker
---

Body content.
EOF

set +e
out_bad_class="$(LINT_ROOT="$TMP_CRED_BAD_CLASS" python3 "$REPO_ROOT/tools/lint-agent-artifacts.py" 2>&1)"
exit_bad_class=$?
set -e

if (( exit_bad_class == 0 )); then
  echo "✖ bad-primitive-class: lint exited 0; expected non-zero." >&2
  fail=1
fi
if ! grep -qF -- "primitive-class" <<< "$out_bad_class"; then
  echo "✖ bad-primitive-class: stderr missing substring 'primitive-class'" >&2
  fail=1
fi
if ! grep -qE -- "credentialed-cli|mcp-server" <<< "$out_bad_class"; then
  echo "✖ bad-primitive-class: stderr missing one of: credentialed-cli, mcp-server" >&2
  fail=1
fi

if (( fail )); then
  echo
  echo "Self-test (credentialed-skill cases): failed." >&2
  echo "bad-bool output was:" >&2
  echo "---" >&2
  echo "$out_bad_bool" >&2
  echo "---" >&2
  echo "bad-class output was:" >&2
  echo "---" >&2
  echo "$out_bad_class" >&2
  echo "---" >&2
  exit 1
fi

echo "✓ Self-test (credentialed-skill cases): passed (conforming clean; bad-bool + bad-class refused with expected stderr)."
