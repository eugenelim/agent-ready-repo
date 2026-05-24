#!/usr/bin/env bash
# Lints AGENTS.md and docs hygiene. Exit non-zero if any check fails.
#
# Checks:
#   1. AGENTS.md exists at repo root.
#   2. CLAUDE.md is a symlink to AGENTS.md (not a duplicate file).
#   3. Root AGENTS.md is under MAX_ROOT_LINES.
#   4. No subdirectory AGENTS.md exceeds MAX_SUB_LINES.
#   5. Internal markdown links resolve.
#   6. docs/CHARTER.md exists (replaces older constitution/ folder pattern).
#   7. No legacy docs/constitution/ directory exists.
#   8. The four Diátaxis subdirectories under docs/guides/ exist.
#   9. Living docs aren't suspiciously stale (warn-only, not a fail).
#  10. Drift-watch — phrases that must live in exactly one canonical home.

set -euo pipefail

MAX_ROOT_LINES=250
MAX_SUB_LINES=150
STALE_DAYS=180  # warn (not fail) if a living doc hasn't been touched in this many days

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

fail=0
note() { echo "✖ $*" >&2; fail=1; }
warn() { echo "⚠ $*" >&2; }
ok()   { echo "✓ $*"; }

# 1. Root AGENTS.md exists
if [[ ! -f AGENTS.md ]]; then
  note "AGENTS.md is missing at the repository root."
else
  ok "Root AGENTS.md exists."
fi

# 2. CLAUDE.md is a symlink to AGENTS.md
if [[ -L CLAUDE.md ]]; then
  target="$(readlink CLAUDE.md)"
  if [[ "$target" == "AGENTS.md" ]]; then
    ok "CLAUDE.md → AGENTS.md (symlink)."
  else
    note "CLAUDE.md is a symlink, but points to '$target' instead of 'AGENTS.md'."
  fi
elif [[ -f CLAUDE.md ]]; then
  note "CLAUDE.md is a regular file. It should be a symlink to AGENTS.md to stay in sync."
else
  note "CLAUDE.md is missing. Create it with: ln -s AGENTS.md CLAUDE.md"
fi

# 3. Root AGENTS.md size
if [[ -f AGENTS.md ]]; then
  lines=$(wc -l < AGENTS.md)
  if (( lines > MAX_ROOT_LINES )); then
    note "AGENTS.md is $lines lines (max $MAX_ROOT_LINES). Move detail to docs/ or .claude/skills/."
  else
    ok "AGENTS.md is $lines lines (≤ $MAX_ROOT_LINES)."
  fi
fi

# 4. Per-package AGENTS.md size
while IFS= read -r f; do
  [[ "$f" == "./AGENTS.md" ]] && continue
  lines=$(wc -l < "$f")
  limit=$MAX_SUB_LINES
  if [[ "$f" == "./packs/core/seeds/AGENTS.md" ]]; then
    limit=$MAX_ROOT_LINES
  fi
  if (( lines > limit )); then
    note "$f is $lines lines (max $limit). Trim or split."
  else
    ok "$f is $lines lines (≤ $limit)."
  fi
done < <(find . -name AGENTS.md -not -path './node_modules/*' -not -path './.git/*' 2>/dev/null)

# 5. Internal markdown links resolve
# Quick check: extract relative links from AGENTS.md and CONVENTIONS.md and confirm targets exist.
for f in AGENTS.md docs/CONVENTIONS.md; do
  [[ -f "$f" ]] || continue
  # match [text](path) where path doesn't start with http and doesn't contain a colon
  while IFS= read -r link; do
    [[ -z "$link" ]] && continue
    # strip anchor
    target="${link%%#*}"
    [[ -z "$target" ]] && continue
    # resolve relative to file's directory
    dir="$(dirname "$f")"
    resolved="$dir/$target"
    if [[ ! -e "$resolved" ]]; then
      note "$f: broken link → $link"
    fi
  done < <(grep -oE '\]\([^)]+\)' "$f" | sed -E 's/^\]\(([^)]+)\)$/\1/' | grep -vE '^https?:' | grep -vE '^[a-z]+:')
done

# 6. docs/CHARTER.md exists
if [[ ! -f docs/CHARTER.md ]]; then
  note "docs/CHARTER.md is missing. The charter (mission, scope, principles) is foundational."
else
  ok "docs/CHARTER.md exists."
fi

# 7. No legacy constitution/ folder
if [[ -d docs/constitution ]]; then
  note "docs/constitution/ exists. This was replaced by docs/CHARTER.md — see docs/CONVENTIONS.md."
else
  ok "No legacy docs/constitution/ directory."
fi

# 8. Diátaxis structure under docs/guides/
diataxis_dirs=(tutorials how-to reference explanation)
missing_diataxis=()
for d in "${diataxis_dirs[@]}"; do
  [[ -d "docs/guides/$d" ]] || missing_diataxis+=("$d")
done
if (( ${#missing_diataxis[@]} > 0 )); then
  note "docs/guides/ is missing Diátaxis subdirectories: ${missing_diataxis[*]}. See docs/guides/README.md."
else
  ok "docs/guides/ has all four Diátaxis subdirectories."
fi

# 9. Stale living-doc check (warn-only)
# Scan a known set of living docs and warn if they haven't been touched in STALE_DAYS.
# This is a soft signal — staleness might be intentional (the file is genuinely accurate
# without changes), but it's worth a glance.
living_docs=(
  docs/CHARTER.md
  docs/architecture/overview.md
  docs/product/roadmap.md
)
now_epoch=$(date +%s)
threshold=$(( STALE_DAYS * 86400 ))
for f in "${living_docs[@]}"; do
  [[ -f "$f" ]] || continue
  mtime=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null || echo "$now_epoch")
  age=$(( (now_epoch - mtime) / 86400 ))
  if (( age > STALE_DAYS )); then
    warn "$f hasn't been touched in $age days (threshold: $STALE_DAYS). Consider whether it's still accurate."
  fi
done

# 10. Drift-watch — single-source phrases.
# Keep this list short. Each entry: a regex, the file that owns it, and a
# space-separated list of files that must NOT contain it. Aimed at the
# load-bearing mechanics we deliberately single-sourced, not stylistic prose.
drift_check() {
  local pattern="$1" canonical="$2"; shift 2
  local forbidden=("$@")
  if [[ -f "$canonical" ]] && ! grep -qE "$pattern" "$canonical"; then
    note "drift-watch: '$pattern' missing from canonical home $canonical."
  fi
  for f in "${forbidden[@]}"; do
    [[ -f "$f" ]] || continue
    if grep -qE "$pattern" "$f"; then
      note "drift-watch: '$pattern' re-appeared in $f (canonical: $canonical)."
    fi
  done
}

# Iteration-cap value lives as data, not prose. The literal number lives
# in the state.json template; SKILL/CONVENTIONS/AGENTS describe the field
# conceptually but must not restate the number.
drift_check \
  '"max_iterations":[[:space:]]*[0-9]+' \
  ".claude/skills/work-loop/assets/state.json" \
  ".claude/skills/work-loop/SKILL.md" "AGENTS.md" "docs/CONVENTIONS.md"

# Belt-and-braces prose probe: the original drift-watch caught the number
# in any prose phrasing. The schema-shaped check above is narrower, so we
# also forbid common prose restatements anywhere a future contributor
# might be tempted to re-state the cap value. Empty canonical = no
# "missing from canonical home" check; the schema (not a prose doc) is
# the single source.
drift_check \
  '(hard )?cap of (five|5) (in-session )?iterations?' \
  "" \
  ".claude/skills/work-loop/SKILL.md" "AGENTS.md" "docs/CONVENTIONS.md"

# Verification-mode triplet (TDD / Goal-based check / Visual / manual QA):
# the explicit per-mode prose is single-sourced in the work-loop skill.
# We probe with one mode label that only appears where the prose lives.
drift_check \
  '\*\*Goal-based check\*\*' \
  ".claude/skills/work-loop/SKILL.md" \
  "AGENTS.md" "docs/CONVENTIONS.md"

# Vendor-specific UX tokens belong under .claude/ only; AGENTS.md and the
# governance docs stay agent-neutral.
for f in AGENTS.md docs/CONVENTIONS.md docs/CHARTER.md docs/APPROACH.md; do
  [[ -f "$f" ]] || continue
  if grep -qE '\bultrathink\b|Plan Mode \(Shift\+Tab' "$f"; then
    note "drift-watch: vendor token (ultrathink / 'Plan Mode (Shift+Tab') in $f. Move it under .claude/."
  fi
done

# Session-scratch artifacts must be gitignored — the docs claim it, the
# linter verifies. Probe one representative path per glob.
for probe in \
  "docs/specs/example/state.json" \
  "docs/specs/example/notes/implementer-T1-0.md" \
  ".worktrees/T1/README.md"; do
  if ! git check-ignore --quiet "$probe" 2>/dev/null; then
    note "drift-watch: '$probe' should be gitignored (session-scratch — see .claude/skills/work-loop/references/state-schema.md, CONVENTIONS.md#supervisor-mode)."
  fi
done

if (( fail )); then
  echo
  echo "Docs lint: failed."
  exit 1
fi
echo
echo "Docs lint: passed."
