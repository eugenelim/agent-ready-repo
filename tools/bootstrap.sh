#!/usr/bin/env bash
# Interactive bootstrap helper for the agent-ready-repo template.
#
# Walks through the mechanical parts of bootstrapping a real project from
# the template:
#   - Prompts for project metadata (name, description, profile, commands).
#   - Substitutes placeholders in AGENTS.md, README.md, CHARTER.md, etc.
#   - Sets the date on the roadmap and ADR-0001.
#   - Optionally removes profile-specific scaffolding (apps/, packages/, etc.).
#   - Runs the docs linter to confirm the result is clean.
#
# Idempotent in spirit but not in fact — it edits files in place. Run it
# on a fresh clone of the template, before your first commit.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# ── Sanity checks ────────────────────────────────────────────────────────
if [[ ! -f AGENTS.md ]] || [[ ! -f USING_THIS_TEMPLATE.md ]]; then
  cat <<EOF >&2
✖ This doesn't look like a fresh template clone.
  Expected AGENTS.md and USING_THIS_TEMPLATE.md at the repo root.

  If you've already bootstrapped, you don't need this script.
  If you've only partially bootstrapped, finish by hand — see
  USING_THIS_TEMPLATE.md.
EOF
  exit 1
fi

if grep -q "^# \`<project-name>\`" README.md 2>/dev/null; then
  : # placeholder still present — good
else
  echo "⚠ README.md placeholder header is already replaced. This script may have run before." >&2
  read -rp "Continue anyway? [y/N] " ans
  [[ "${ans,,}" == "y" ]] || exit 1
fi

# ── Helpers ──────────────────────────────────────────────────────────────
ask() {
  # ask "prompt" "default" → echo result
  local prompt="$1" default="${2:-}" reply
  if [[ -n "$default" ]]; then
    read -rp "$prompt [$default]: " reply
    echo "${reply:-$default}"
  else
    read -rp "$prompt: " reply
    echo "$reply"
  fi
}

ask_yn() {
  # ask_yn "prompt" "default y|n" → 0 if yes, 1 if no
  local prompt="$1" default="${2:-n}" reply
  read -rp "$prompt [${default^^}]: " reply
  reply="${reply:-$default}"
  [[ "${reply,,}" =~ ^y(es)?$ ]]
}

substitute() {
  # substitute file placeholder replacement
  # uses a sentinel so we don't accidentally match real text.
  local file="$1" placeholder="$2" replacement="$3"
  if [[ ! -f "$file" ]]; then return; fi
  # Use python for portable, escape-safe substitution (avoids sed quoting hell).
  python3 - "$file" "$placeholder" "$replacement" <<'PY'
import sys, pathlib
path, placeholder, replacement = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
text = p.read_text()
new = text.replace(placeholder, replacement)
if new != text:
    p.write_text(new)
PY
}

# ── Prompt for metadata ──────────────────────────────────────────────────
echo
echo "═══ Bootstrap from agent-ready-repo ═══"
echo
echo "This script will customize the template for your project. It edits"
echo "files in place. Press Ctrl-C to abort at any time."
echo

PROJECT_NAME="$(ask "Project name (kebab-case, e.g. my-service)")"
[[ -n "$PROJECT_NAME" ]] || { echo "Project name is required."; exit 1; }

PROJECT_DESCRIPTION="$(ask "One-line description")"

COPYRIGHT_HOLDER="$(ask "Copyright holder for LICENSE-MIT (your name or org)")"
COPYRIGHT_YEAR="$(date +%Y)"

echo
echo "Profile (see USING_THIS_TEMPLATE.md § Step 0):"
echo "  A — Microservice / single component (1-3 contributors)"
echo "  B — Single library or app (4-10 contributors)"
echo "  C — Medium platform / engine (10-50 contributors)"
PROFILE="$(ask "Profile [A/B/C]" "B")"
PROFILE="${PROFILE^^}"
case "$PROFILE" in A|B|C) ;; *) echo "Invalid profile."; exit 1 ;; esac

echo
echo "Commands the template will fill into AGENTS.md and the gates."
echo "Use whatever your stack uses; leave blank if not applicable."
INSTALL_CMD="$(ask "Install command" "npm install")"
TEST_CMD="$(ask "Test command" "npm test")"
LINT_CMD="$(ask "Lint command" "npm run lint")"
TYPECHECK_CMD="$(ask "Typecheck command" "npm run typecheck")"
BUILD_CMD="$(ask "Build command" "npm run build")"

# Profile-driven cleanup choices
DELETE_APPS=0; DELETE_PACKAGES=0; DELETE_EXAMPLE=1
DELETE_ADVERSARIAL_REVIEWER=0; DELETE_NEW_PACKAGE_SKILL=0
DELETE_SECURITY_REVIEWER=0; DELETE_QUALITY_ENGINEER=0; DELETE_BUG_FIX=0

case "$PROFILE" in
  A)
    DELETE_APPS=1; DELETE_PACKAGES=1
    DELETE_NEW_PACKAGE_SKILL=1
    if ask_yn "Profile A: delete adversarial-reviewer subagent? (recommended for solo/very-small teams)" "y"; then
      DELETE_ADVERSARIAL_REVIEWER=1
    fi
    if ask_yn "Profile A: delete security-reviewer subagent? (keep recommended — solo devs still benefit from threat-model lens)" "n"; then
      DELETE_SECURITY_REVIEWER=1
    fi
    if ask_yn "Profile A: delete quality-engineer subagent? (keep recommended — testability / observability lens; heaviest of the three reviewers)" "n"; then
      DELETE_QUALITY_ENGINEER=1
    fi
    if ask_yn "Profile A: delete bug-fix skill? (keep recommended — every dev fixes bugs)" "n"; then
      DELETE_BUG_FIX=1
    fi
    ;;
  B)
    if ask_yn "Profile B: keep apps/ directory?" "n"; then DELETE_APPS=0; else DELETE_APPS=1; fi
    if ask_yn "Profile B: keep packages/ directory?" "y"; then DELETE_PACKAGES=0; else DELETE_PACKAGES=1; fi
    if (( DELETE_PACKAGES )); then DELETE_NEW_PACKAGE_SKILL=1; fi
    ;;
  C)
    : # keep everything
    ;;
esac

TODAY="$(date -u +%Y-%m-%d)"
NEXT_REVIEW="$(date -u -d '+90 days' +%Y-%m-%d 2>/dev/null || date -u -v +90d +%Y-%m-%d)"

# ── Confirm ──────────────────────────────────────────────────────────────
echo
echo "About to apply:"
echo "  Project name:    $PROJECT_NAME"
echo "  Description:     $PROJECT_DESCRIPTION"
echo "  Copyright:       $COPYRIGHT_YEAR $COPYRIGHT_HOLDER"
echo "  Profile:         $PROFILE"
echo "  Install:         $INSTALL_CMD"
echo "  Test:            $TEST_CMD"
echo "  Lint:            $LINT_CMD"
echo "  Typecheck:       $TYPECHECK_CMD"
echo "  Build:           $BUILD_CMD"
echo "  Delete apps/:    $((DELETE_APPS))"
echo "  Delete packages/: $((DELETE_PACKAGES))"
echo "  Delete example package: $((DELETE_EXAMPLE))"
echo "  Delete adversarial-reviewer: $((DELETE_ADVERSARIAL_REVIEWER))"
echo "  Delete security-reviewer: $((DELETE_SECURITY_REVIEWER))"
echo "  Delete quality-engineer: $((DELETE_QUALITY_ENGINEER))"
echo "  Delete new-package skill: $((DELETE_NEW_PACKAGE_SKILL))"
echo "  Delete bug-fix skill: $((DELETE_BUG_FIX))"
echo "  Date stamps:     $TODAY"
echo

if ! ask_yn "Proceed?" "y"; then
  echo "Aborted."
  exit 1
fi

# ── Apply substitutions ──────────────────────────────────────────────────
echo
echo "Applying..."

# README.md — replace placeholder header line, drop the "if you are reading this on the template" block.
substitute README.md "<project-name>" "$PROJECT_NAME"
substitute README.md "> One-line description of what this project does and who it's for." "> $PROJECT_DESCRIPTION"
# Strip the template's evaluator-facing pitch from the top of README.md
# (everything from the start of the file through the BOOTSTRAP_TEMPLATE_INTRO_END
# sentinel). What remains is the adopter-facing scaffold.
python3 - <<PY
import pathlib, re
p = pathlib.Path("README.md")
text = p.read_text()
new = re.sub(
  r"^# agent-ready-repo\n.*?<!-- BOOTSTRAP_TEMPLATE_INTRO_END -->\n\n",
  "",
  text,
  count=1,
  flags=re.DOTALL,
)
p.write_text(new)
PY

# AGENTS.md — project name + commands.
substitute AGENTS.md "\`<project-name>\`" "\`$PROJECT_NAME\`"
substitute AGENTS.md "<project-name>" "$PROJECT_NAME"
substitute AGENTS.md "<one-line description of what it does and for whom>" "$PROJECT_DESCRIPTION"
substitute AGENTS.md "<install command>" "$INSTALL_CMD"
substitute AGENTS.md "<test command>" "$TEST_CMD"
substitute AGENTS.md "<test all command>" "$TEST_CMD"
substitute AGENTS.md "<lint command>" "$LINT_CMD"
substitute AGENTS.md "<build command>" "$BUILD_CMD"

# CHARTER.md — leave the placeholder text as is (user fills it manually);
# but stamp today's date if there's a date placeholder.
substitute docs/CHARTER.md "<replace with one sentence>" "$PROJECT_DESCRIPTION"

# Roadmap — stamp date.
substitute docs/product/roadmap.md "**Last updated:** YYYY-MM-DD" "**Last updated:** $TODAY"
substitute docs/product/roadmap.md "Next review: YYYY-MM-DD." "Next review: $NEXT_REVIEW."

# ADR-0001 — stamp date.
substitute docs/adr/0001-adopt-agents-md-and-doc-hierarchy.md "- **Date:** YYYY-MM-DD" "- **Date:** $TODAY"

# PR template — fill commands.
substitute .github/pull_request_template.md "<test command>" "$TEST_CMD"
substitute .github/pull_request_template.md "<lint command>" "$LINT_CMD"
substitute .github/pull_request_template.md "<typecheck command>" "$TYPECHECK_CMD"

# LICENSE-MIT — fill in copyright holder and year.
substitute LICENSE-MIT "<year>" "$COPYRIGHT_YEAR"
substitute LICENSE-MIT "<copyright holders>" "$COPYRIGHT_HOLDER"

# .ralphrc — pre-fill gate commands so Ralph (if used) just works.
cat > .ralphrc <<EOF
# Ralph gate commands — see tools/RALPH.md
LINT_CMD="$LINT_CMD"
TYPECHECK_CMD="$TYPECHECK_CMD"
TEST_CMD="$TEST_CMD"
MAX_ITERATIONS=20
COMPLETION_PHRASE="RALPH_DONE"
EOF

# Profile-specific cleanup.
(( DELETE_APPS )) && rm -rf apps && echo "  rm -rf apps/"
if (( DELETE_PACKAGES )); then
  rm -rf packages && echo "  rm -rf packages/"
elif (( DELETE_EXAMPLE )) && [[ -d packages/_example ]]; then
  rm -rf packages/_example && echo "  rm -rf packages/_example/"
fi
(( DELETE_ADVERSARIAL_REVIEWER )) && rm -f .claude/agents/adversarial-reviewer.md && echo "  rm .claude/agents/adversarial-reviewer.md"
(( DELETE_SECURITY_REVIEWER )) && rm -f .claude/agents/security-reviewer.md && echo "  rm .claude/agents/security-reviewer.md"
(( DELETE_QUALITY_ENGINEER )) && rm -f .claude/agents/quality-engineer.md && echo "  rm .claude/agents/quality-engineer.md"
(( DELETE_NEW_PACKAGE_SKILL )) && rm -rf .claude/skills/new-package && echo "  rm -rf .claude/skills/new-package/"
(( DELETE_BUG_FIX )) && rm -rf .claude/skills/bug-fix && echo "  rm -rf .claude/skills/bug-fix/"

# When adversarial-reviewer was removed, drop its bullet from the
# Specialist subagents list so the link doesn't dangle. The how-we-work
# section is generic ("specialist-reviewer pass") and points at the
# work-loop skill — no rewrite needed there.
if (( DELETE_ADVERSARIAL_REVIEWER )); then
  python3 - <<'PY'
import pathlib, re
p = pathlib.Path("AGENTS.md")
text = p.read_text()
new = re.sub(
  r"- \[`adversarial-reviewer`\]\(\.claude/agents/adversarial-reviewer\.md\) — spec /\n  plan / implementation drift; missing edge cases; scope creep\. Default\n  reviewer; runs after gates pass\.\n",
  "",
  text,
)
p.write_text(new)
PY
fi

# When new-package skill was removed, drop its line from AGENTS.md and the skills index.
if (( DELETE_NEW_PACKAGE_SKILL )); then
  python3 - <<'PY'
import pathlib, re
for path in ("AGENTS.md", ".claude/skills/README.md"):
    p = pathlib.Path(path)
    if not p.exists(): continue
    text = p.read_text()
    new = re.sub(r".*new-package.*\n", "", text)
    p.write_text(new)
PY
fi

# When security-reviewer, quality-engineer, or bug-fix were removed, drop
# their references from AGENTS.md (and skills/README.md for bug-fix) so the
# links don't dangle and the linter stays green.
if (( DELETE_SECURITY_REVIEWER || DELETE_QUALITY_ENGINEER || DELETE_BUG_FIX )); then
  DELETE_SECURITY_REVIEWER="$DELETE_SECURITY_REVIEWER" \
  DELETE_QUALITY_ENGINEER="$DELETE_QUALITY_ENGINEER" \
  DELETE_BUG_FIX="$DELETE_BUG_FIX" \
  python3 - <<'PY'
import os, pathlib, re

delete_security = os.environ.get("DELETE_SECURITY_REVIEWER") == "1"
delete_quality  = os.environ.get("DELETE_QUALITY_ENGINEER") == "1"
delete_bugfix   = os.environ.get("DELETE_BUG_FIX") == "1"

agents_md = pathlib.Path("AGENTS.md")
text = agents_md.read_text()

if delete_security:
    text = re.sub(
        r"- \[`security-reviewer`\]\(\.claude/agents/security-reviewer\.md\) — OWASP Top\n"
        r"  10 \(web \+ LLM Apps\) and STRIDE lens\. Use when the diff touches auth,\n"
        r"  secrets, user input, deserialization, file/network I/O, dependencies,\n"
        r"  or LLM/agent code\. Complements SAST/SCA scanners; does not replace them\.\n",
        "",
        text,
    )

if delete_quality:
    text = re.sub(
        r"- \[`quality-engineer`\]\(\.claude/agents/quality-engineer\.md\) — testability,\n"
        r"  observability, reliability, and maintainability lens\. Also drafts\n"
        r"  contract or construction tests on request\.\n",
        "",
        text,
    )

if delete_bugfix:
    text = re.sub(r"- `bug-fix` — fix a defect with root-cause discipline\n", "", text)

agents_md.write_text(text)

if delete_bugfix:
    skills_readme = pathlib.Path(".claude/skills/README.md")
    if skills_readme.exists():
        text = skills_readme.read_text()
        text = re.sub(r"\| \[`bug-fix`\]\(bug-fix/SKILL\.md\) \| [^|]+ \|\n", "", text)
        skills_readme.write_text(text)
PY
fi

# Self-delete the bootstrap script + USING_THIS_TEMPLATE.md if requested.
echo
if ask_yn "Remove USING_THIS_TEMPLATE.md and tools/bootstrap.sh? (recommended after a successful bootstrap)" "y"; then
  rm -f USING_THIS_TEMPLATE.md
  # Defer bootstrap.sh deletion to after the linter runs.
  REMOVE_BOOTSTRAP=1
else
  REMOVE_BOOTSTRAP=0
fi

# ── Verify ───────────────────────────────────────────────────────────────
echo
echo "Running docs linter..."
echo
if python tools/lint-agents-md.py && python tools/lint-agent-artifacts.py; then
  echo
  echo "✓ Bootstrap complete. Linters: green."
  if (( REMOVE_BOOTSTRAP )); then
    echo "  Removing tools/bootstrap.sh."
    rm -f tools/bootstrap.sh
  fi
  echo
  echo "Next steps:"
  echo "  1. Review the changes:       git status"
  echo "  2. Edit docs/CHARTER.md      (mission/scope/principles — manual)"
  echo "  3. Edit docs/architecture/overview.md  (project map — manual)"
  echo "  4. First commit:             git add -A && git commit -m 'chore: bootstrap'"
else
  echo
  echo "✖ Linter failed. Fix the issues above before committing."
  echo "  (Bootstrap files left in place so you can re-run if needed.)"
  exit 2
fi
