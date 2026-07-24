#!/usr/bin/env python3
"""
Insert ## Output rendering sections into SKILL.md files.

Edits all copies of each skill (both pack source and projected .claude/skills/).
Safe to re-run: skips any SKILL.md that already contains ## Output rendering.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Directive texts (verbatim from docs/guides/core/reference/output-rendering.md)
# ---------------------------------------------------------------------------
D = {
    "table": (
        "Table — When presenting several items that share the same fields, render a "
        "Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail "
        "list. Right-align numeric columns."
    ),
    "status-list": (
        "Status list — Lead each row with a status glyph — ● running, ✓ done, "
        "○ idle, ⚠ blocked — status first, one item per line, labels aligned."
    ),
    "severity-list": (
        "Severity list — Lead each finding with a severity glyph — 🟥 blocker, "
        "🟧 major, 🟨 minor, ⚪ advisory — worst first, one finding per line, "
        "file:line anchor aligned."
    ),
    "tree": (
        "Tree / hierarchy — Render hierarchies as an ASCII tree (├─ └─ │) inside "
        "a fenced block, not as nested bullets."
    ),
    "mermaid": (
        "Diagram / flow — For relationships or flow, emit a fenced ```mermaid block "
        "(it renders in chat and artifacts). If the surface is terminal-only, fall "
        "back to an ASCII box-and-arrow sketch."
    ),
    "key-value": (
        "Key–value / one record — For a single record's fields, use an aligned "
        "key: value list, not a two-row table."
    ),
    "diff": (
        "Code change — Show edits as a fenced ```diff block with +/− lines. "
        "Never describe the change in prose or a table."
    ),
    "narrative": (
        "Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs. "
        "Don't force narrative into a table."
    ),
    "progress": (
        "Progress — Report progress inline as done/total (e.g. 3/8). Only draw a "
        "bar if you're animating in a terminal."
    ),
}

# ---------------------------------------------------------------------------
# Skill → directive mapping
# ---------------------------------------------------------------------------
SKILLS: dict[str, list[str]] = {
    # core
    "workspace-status":             ["status-list", "table", "mermaid", "progress"],
    "frontend-engineering":         ["table"],
    # governance-extras
    "rfc-status":                   ["table"],
    "new-adr":                      ["key-value"],
    "new-rfc":                      ["key-value"],
    # architect
    "architect-design":             ["narrative", "mermaid", "key-value"],
    "architect-diagram":            ["mermaid"],
    "architect-review":             ["severity-list"],
    # catalogue-curation
    "assimilate-primitive":         ["severity-list"],
    "export-catalogue":             ["status-list"],
    # desk-research
    "compare-hypotheses":           ["table"],
    "desk-research-project-digest": ["table"],
    "desk-research-project-status": ["key-value"],
    "desk-research-project-synthesize": ["narrative", "key-value"],
    # converters
    "file-to-markdown":             ["key-value"],
    "markdown-to-docx":             ["key-value"],
    "markdown-to-pptx":             ["key-value"],
    "markdown-to-html":             ["key-value"],
    "markdown-to-xlsx":             ["key-value"],
    "mermaid-renderer":             ["key-value"],
    "msg-to-markdown":              ["key-value"],
    "render-proof":                 ["key-value"],
    # product-engineering
    "discovery-loop":               ["table"],
    "explore-options":              ["key-value"],
    "de-risk-intent":               ["key-value"],
    "frame-situation":              ["table"],
    "map-capabilities":             ["table"],
    "place-bet":                    ["table"],
    "plan-validation":              ["key-value"],
    "new-package":                  ["tree"],
    # product-strategy
    "run-pestle-analysis":          ["table"],
    "run-porters-five-forces":      ["table"],
    "run-okr-cascade":              ["table"],
    # iac-terraform
    "generate-iac":                 ["table", "status-list"],
    "reconcile-iac":                ["table", "key-value"],
    # release-engineering
    "release-loop":                 ["table", "status-list"],
    # experience-design
    "experience-status":            ["status-list", "key-value"],
    "interaction-design":           ["mermaid"],
    "user-flow":                    ["mermaid"],
    "process-mapping":              ["table", "mermaid"],
    "service-blueprint":            ["table", "status-list"],
    "journey-mapping":              ["table"],
    "analytical-design":            ["table"],
    "conversion-design":            ["table"],
    "documentation-design":         ["table"],
    "marketplace-design":           ["table"],
    "workspace-design":             ["table"],
    "information-architecture":     ["table"],
    # experience-design (additional severity-list producers)
    "design-review":                ["severity-list"],
    "devils-advocate":              ["severity-list"],
    # atlassian
    "jira-team-status":             ["table"],
    "ai-adoption-report":           ["table", "key-value"],
    "flow-metrics":                 ["table", "key-value"],
    "jira-brief-intake":            ["table"],
    "jira-align-brief-intake":      ["table"],
    "jira-defect-flow":             ["table"],
    "jira-story-triage":            ["table"],
    "confluence-publisher":         ["key-value"],
    # linear
    "linear-brief-sync":            ["diff"],
    "linear-brief-intake":          ["table"],
    # github
    "github-brief-intake":          ["table"],
}


def find_skill_files(skill_name: str) -> list[Path]:
    """Return all SKILL.md paths for the given skill (source + projected)."""
    found: list[Path] = []
    # projected .claude/skills/
    p = ROOT / ".claude" / "skills" / skill_name / "SKILL.md"
    if p.exists():
        found.append(p)
    # pack sources
    packs_dir = ROOT / "packs"
    if packs_dir.is_dir():
        for pack_dir in sorted(packs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            p = pack_dir / ".apm" / "skills" / skill_name / "SKILL.md"
            if p.exists():
                found.append(p)
    return found


def build_block(directives: list[str]) -> str:
    """Build the ## Output rendering section text."""
    lines = ["## Output rendering", ""]
    for d in directives:
        lines.append(D[d])
    lines.append("")
    return "\n".join(lines)


def insert_directive(content: str, block: str) -> str:
    """
    Insert the ## Output rendering block before the first ## section in the body.
    Returns content unchanged if ## Output rendering is already present.
    """
    # Already exists?
    if "## Output rendering" in content:
        return content

    # Split off YAML frontmatter
    if content.startswith("---"):
        end = content.find("\n---\n", 4)
        if end == -1:
            return content  # malformed frontmatter, skip
        frontmatter = content[: end + 5]
        body = content[end + 5:]
    else:
        frontmatter = ""
        body = content

    # Find first ## section (but not ### or more)
    match = re.search(r"(?m)^## ", body)
    if match:
        pos = match.start()
        new_body = body[:pos] + block + "\n" + body[pos:]
    else:
        # No ## section found — append before the final newline
        new_body = body.rstrip("\n") + "\n\n" + block

    return frontmatter + new_body


def main() -> int:
    updated = 0
    skipped = 0
    not_found = 0

    for skill_name, directives in sorted(SKILLS.items()):
        files = find_skill_files(skill_name)
        if not files:
            print(f"  NOT FOUND  {skill_name}")
            not_found += 1
            continue

        block = build_block(directives)
        for f in files:
            original = f.read_text(encoding="utf-8")
            patched = insert_directive(original, block)
            if patched != original:
                f.write_text(patched, encoding="utf-8")
                print(f"  updated    {skill_name}  ({f.relative_to(ROOT)})")
                updated += 1
            else:
                print(f"  already ok {skill_name}  ({f.relative_to(ROOT)})")
                skipped += 1

    print(f"\nDone: {updated} updated, {skipped} already ok, {not_found} not found.")
    return 0 if not_found == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
