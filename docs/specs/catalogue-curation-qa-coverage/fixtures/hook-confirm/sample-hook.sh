#!/usr/bin/env bash
# pre-commit hook: validate-and-stamp
#
# Runs on every `git commit` before the commit is created.
# Three jobs:
#   1. Run the project lint suite (fail-fast on violation).
#   2. Verify that any modified SKILL.md file has a valid frontmatter version field.
#   3. Append a datestamp to CHANGELOG.md's [Unreleased] section if any skill
#      file was modified in this commit.
#
# Install: copy to .git/hooks/pre-commit and chmod +x.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ── 1. Lint ────────────────────────────────────────────────────────────────────
echo "[pre-commit] Running lint..."
if ! python -m agentbundle.build lint-packs --packs-dir packs --quiet; then
    echo "[pre-commit] FAIL: lint-packs reported violations. Fix before committing."
    exit 1
fi

# ── 2. Validate frontmatter on modified SKILL.md files ────────────────────────
MODIFIED_SKILLS="$(git diff --cached --name-only | grep 'SKILL\.md$' || true)"

if [ -n "$MODIFIED_SKILLS" ]; then
    echo "[pre-commit] Validating frontmatter on modified skill files..."
    while IFS= read -r skill_file; do
        if ! grep -q '^version:' "$skill_file" 2>/dev/null; then
            echo "[pre-commit] FAIL: $skill_file is missing a 'version:' field in frontmatter."
            exit 1
        fi
    done <<< "$MODIFIED_SKILLS"
fi

# ── 3. Stamp CHANGELOG.md if any skill was modified ───────────────────────────
if [ -n "$MODIFIED_SKILLS" ]; then
    CHANGELOG="$REPO_ROOT/docs/product/changelog.md"
    TODAY="$(date +%Y-%m-%d)"

    if [ -f "$CHANGELOG" ]; then
        if ! grep -q "<!-- skill-stamp: $TODAY -->" "$CHANGELOG"; then
            sed -i.bak "s/## \[Unreleased\]/## [Unreleased]\n\n<!-- skill-stamp: $TODAY --> _Skills modified $TODAY \xe2\x80\x94 review before release._/" "$CHANGELOG"
            rm -f "$CHANGELOG.bak"
            git add "$CHANGELOG"
            echo "[pre-commit] Stamped CHANGELOG.md with today's date ($TODAY)."
        fi
    fi
fi

echo "[pre-commit] All checks passed."
exit 0
