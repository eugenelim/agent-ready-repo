#!/usr/bin/env bash
# Self-test for tools/bootstrap.sh — verifies every substitution target
# and multi-line regex block in bootstrap.sh still matches the current
# state of the files it targets.
#
# Catches drift: if any edit removes or rephrases a placeholder, bullet,
# or paragraph that bootstrap.sh expects to find, this test fails so the
# eventual bootstrap user does not run a partly-broken script.
#
# Read-only: does NOT run bootstrap destructively. Update this script
# in the same commit as bootstrap.sh whenever bootstrap.sh's target
# list changes.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

python3 - <<'PY'
import pathlib, re, sys

REPO = pathlib.Path(".")
errors = 0

def check(label, path, pattern, *, regex=False, flags=0):
    """Pass if `pattern` (literal or regex) appears in `path`."""
    global errors
    p = REPO / path
    if not p.exists():
        print(f"✖ FILE MISSING: {path} ({label})", file=sys.stderr)
        errors += 1
        return
    text = p.read_text()
    if regex:
        found = re.search(pattern, text, flags=flags) is not None
    else:
        found = pattern in text
    if found:
        print(f"✓ {label}")
    else:
        print(f"✖ MISSING: {label}", file=sys.stderr)
        print(f"    path: {path}", file=sys.stderr)
        snippet = pattern[:80] + ("…" if len(pattern) > 80 else "")
        print(f"    target: {snippet!r}", file=sys.stderr)
        errors += 1

# ── Sanity-check placeholders bootstrap looks for at startup ──────────────
print("── Sanity-check placeholders ──")
check("README.md project-name header", "README.md", "# `<project-name>`")
check("README.md description placeholder", "README.md",
      "> One-line description of what this project does and who it's for.")

# ── Simple placeholder substitutions (`substitute` calls) ─────────────────
print()
print("── AGENTS.md substitutions ──")
check("AGENTS.md `<project-name>` (backticked)", "AGENTS.md", "`<project-name>`")
check("AGENTS.md <project-name> (raw)", "AGENTS.md", "<project-name>")
check("AGENTS.md description placeholder", "AGENTS.md",
      "<one-line description of what it does and for whom>")
check("AGENTS.md <install command>", "AGENTS.md", "<install command>")
check("AGENTS.md <test command>", "AGENTS.md", "<test command>")
check("AGENTS.md <test all command>", "AGENTS.md", "<test all command>")
check("AGENTS.md <lint command>", "AGENTS.md", "<lint command>")
check("AGENTS.md <build command>", "AGENTS.md", "<build command>")

print()
print("── Other file substitutions ──")
check("CHARTER.md <replace with one sentence>", "docs/CHARTER.md",
      "<replace with one sentence>")
check("roadmap.md Last updated placeholder", "docs/product/roadmap.md",
      "**Last updated:** YYYY-MM-DD")
check("roadmap.md Next review placeholder", "docs/product/roadmap.md",
      "Next review: YYYY-MM-DD.")
check("ADR-0001 Date placeholder",
      "docs/adr/0001-adopt-agents-md-and-doc-hierarchy.md",
      "- **Date:** YYYY-MM-DD")
check("PR template <test command>",
      ".github/pull_request_template.md", "<test command>")
check("PR template <lint command>",
      ".github/pull_request_template.md", "<lint command>")
check("PR template <typecheck command>",
      ".github/pull_request_template.md", "<typecheck command>")
check("LICENSE-MIT <year>", "LICENSE-MIT", "<year>")
check("LICENSE-MIT <copyright holders>", "LICENSE-MIT", "<copyright holders>")

# ── Multi-line regex blocks (the fragile ones) ────────────────────────────
print()
print("── Multi-line regex blocks ──")

intro_regex = (
    r"^# agent-ready-repo\n.*?<!-- BOOTSTRAP_TEMPLATE_INTRO_END -->\n\n"
)
check("README.md template-intro block (multi-line, DOTALL)", "README.md",
      intro_regex, regex=True, flags=re.DOTALL)
check("docs/APPROACH.md exists with canonical principles section",
      "docs/APPROACH.md", "The four principles for what we keep")

workflow_5_regex = (
    r"5\. \*\*Self-review against the spec\.\*\* After gates pass, run the\n"
    r"   \[`adversarial-reviewer`\]\(\.claude/agents/adversarial-reviewer\.md\)\n"
    r"   subagent\. Treat its findings as part of \"done\", not as optional polish\.\n"
    r"   See \[§ Specialist subagents\]\(#specialist-subagents\) for security and\n"
    r"   quality reviewers to layer on when the change calls for them\."
)
check("AGENTS.md Workflow #5 fallback regex (adversarial-reviewer removal)",
      "AGENTS.md", workflow_5_regex, regex=True)

adversarial_bullet = (
    r"- \[`adversarial-reviewer`\]\(\.claude/agents/adversarial-reviewer\.md\) — spec /\n"
    r"  plan / implementation drift; missing edge cases; scope creep\. Default\n"
    r"  reviewer; runs after gates pass\.\n"
)
check("AGENTS.md adversarial-reviewer bullet (Specialist subagents)",
      "AGENTS.md", adversarial_bullet, regex=True)

security_bullet = (
    r"- \[`security-reviewer`\]\(\.claude/agents/security-reviewer\.md\) — OWASP Top\n"
    r"  10 \(web \+ LLM Apps\) and STRIDE lens\. Use when the diff touches auth,\n"
    r"  secrets, user input, deserialization, file/network I/O, dependencies,\n"
    r"  or LLM/agent code\. Complements SAST/SCA scanners; does not replace them\."
)
check("AGENTS.md security-reviewer bullet (Specialist subagents)",
      "AGENTS.md", security_bullet, regex=True)

quality_bullet = (
    r"- \[`quality-engineer`\]\(\.claude/agents/quality-engineer\.md\) — testability,\n"
    r"  observability, reliability, and maintainability lens\. Also drafts\n"
    r"  contract or construction tests on request\."
)
check("AGENTS.md quality-engineer bullet (Specialist subagents)",
      "AGENTS.md", quality_bullet, regex=True)

check("AGENTS.md bug-fix skill bullet (Skills available list)",
      "AGENTS.md",
      r"- `bug-fix` — fix a defect with root-cause discipline\n",
      regex=True)

check("skills/README.md bug-fix table row",
      ".claude/skills/README.md",
      r"\| \[`bug-fix`\]\(bug-fix/SKILL\.md\) \| [^|]+ \|\n",
      regex=True)

check("AGENTS.md mentions new-package (for Profile A cleanup)",
      "AGENTS.md", "new-package")
check("skills/README.md mentions new-package (for Profile A cleanup)",
      ".claude/skills/README.md", "new-package")

# ── Linters bootstrap calls at the end ────────────────────────────────────
print()
print("── Linter scripts bootstrap invokes ──")
check("tools/lint-agents-md.sh exists",
      "tools/lint-agents-md.sh", "set -euo pipefail")
check("tools/lint-agent-artifacts.sh exists",
      "tools/lint-agent-artifacts.sh", "set -euo pipefail")

print()
if errors:
    print(f"Bootstrap-targets test: failed ({errors} target(s) drifted).",
          file=sys.stderr)
    print(f"If you intentionally changed a target, update "
          f"tools/bootstrap.sh in the same commit so bootstrap stays "
          f"functional for new adopters.", file=sys.stderr)
    sys.exit(1)

print("Bootstrap-targets test: passed.")
PY
