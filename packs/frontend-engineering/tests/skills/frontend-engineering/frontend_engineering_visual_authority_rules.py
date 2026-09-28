"""Readers for the frontend-engineering visual-authority rule tables.

Named for its pack and skill per `packs/AGENTS.md` § *Writing pack tests*: a
bare module name would bind whichever directory reached the path first.

Nothing here states a rule. The rules live in
`references/visual-observation.md`, and the table readers are reused from the
sibling rendered-page module rather than reimplemented, so one pipe policy
governs both references and a rule change moves the reference, not the suite.
"""

from __future__ import annotations

import re
from pathlib import Path

from frontend_engineering_rendered_page_rules import table_rows, unique_keyed

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "frontend-engineering"
SKILL = SKILL_DIR / "SKILL.md"
OBSERVATION = SKILL_DIR / "references" / "visual-observation.md"
FALLBACK_TOKENS = SKILL_DIR / "references" / "fallback-tokens.md"
PRINT_SURFACE = SKILL_DIR / "references" / "print-surface.md"
REVIEWER = PACK_ROOT / ".apm" / "agents" / "frontend-reviewer.md"

# Two sweep roots, named for the trees they denote rather than for the criteria
# they happen to serve.
#
# THIS_SKILL_AND_AGENTS is deliberately narrow: a sibling skill legitimately
# says "linear interpolation", and the aesthetic-anchor sweep must not red on a
# CSS term in a skill this work does not touch.
THIS_SKILL_AND_AGENTS = (SKILL_DIR, PACK_ROOT / ".apm" / "agents")
# WHOLE_EXPORT_TREE is everything the pack ships. Absence checks that claim to
# cover the pack must sweep it, or a sibling skill can hold the thing the
# criterion says is gone while the suite stays green.
WHOLE_EXPORT_TREE = (PACK_ROOT / ".apm",)

# `.apm` holds only these today; an unknown suffix is surfaced rather than
# silently skipped, because an absence check's whole value is completeness.
SWEPT_SUFFIXES = {".md", ".json", ".toml", ".html", ".txt", ".css", ".js"}


def shipped_files(roots=THIS_SKILL_AND_AGENTS):
    """Every shipped text file under ``roots``.

    The sweep's file-selection policy lives here, in one place, so a third
    sweep does not have to rediscover half of it in a test module.
    """
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in SWEPT_SUFFIXES:
                yield path


def read(path: Path) -> str:
    """Explicit UTF-8, and no ``errors="ignore"``.

    These reads back absence checks. A mis-decode under a non-UTF-8 locale
    would silently drop exactly the bytes that would have matched, and
    swallowing the error guarantees nothing reports it. A genuinely undecodable
    shipped file should fail loudly.
    """
    return path.read_text(encoding="utf-8")


def skill_body_lines() -> int:
    """Post-frontmatter body length, derived exactly as the catalogue
    skill-spec lint derives it.

    The lint computes ``"\\n".join(lines[end + 1:]).splitlines()``. Taking
    ``len(lines[end + 1:])`` instead differs by one whenever the file ends with
    a blank line — the join-then-split form drops the trailing empty element
    and the slice form keeps it. With the budget at its ceiling, that
    divergence would red this gate against a file the lint considers in-bounds
    and blame the body length. Perform the lint's derivation verbatim so the
    two instruments cannot disagree.
    """
    lines = read(SKILL).splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"{SKILL.name} does not open with a frontmatter block")
    end = next(
        (i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if end is None:
        raise AssertionError(f"{SKILL.name}'s frontmatter block is never closed")
    return len("\n".join(lines[end + 1:]).splitlines())


def _sourced(heading: str, call):
    """Run a shipped table reader, but report the file we actually passed it.

    The readers hard-code their own module's reference in every message. Reused
    against a second reference, a missing heading would send the next author to
    a file that never had it.
    """
    try:
        return call()
    except AssertionError as exc:
        raise AssertionError(
            f"{exc} — reading '## {heading}' from {OBSERVATION.name}"
        ) from exc


def observation_rows(heading: str) -> list[list[str]]:
    return _sourced(heading, lambda: table_rows(read(OBSERVATION), heading))


def observation_table(heading: str) -> dict[str, list[str]]:
    return _sourced(
        heading, lambda: unique_keyed(table_rows(read(OBSERVATION), heading), heading)
    )


def rule(heading: str, key: str) -> str:
    """The value cell of one rule row, refusing a missing row by name."""
    table = observation_table(heading)
    if key not in table:
        raise AssertionError(
            f"'## {heading}' in {OBSERVATION.name} has no {key!r} row; it "
            f"carries {sorted(table)}"
        )
    return table[key][1]


def rule_table_headings() -> list[str]:
    """Every `## ` section in the reference whose first table is a rule table.

    Driving a sweep from this rather than from a hard-coded list means a table
    added later is covered without a suite edit.
    """
    text = read(OBSERVATION)
    found = []
    for heading in re.findall(r"^## (.+)$", text, re.M):
        # Bound the search to this section. The shipped reader scans forward
        # past non-table lines until it finds a table, so an unbounded call
        # from a prose-only section returns the NEXT section's rows.
        body = text.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]
        if not any(line.lstrip().startswith("|") for line in body.splitlines()):
            continue
        found.append(heading)
    return found


def section(text: str, start: str, *stops: str) -> str:
    """The slice of ``text`` from ``start`` up to the first of ``stops``."""
    if start not in text:
        raise AssertionError(f"section {start!r} is gone from the file")
    body = text.split(start, 1)[1]
    for stop in stops:
        body = body.split(stop, 1)[0]
    return body


def preflight() -> str:
    """The shared PLAN pre-flight, bounded at the first mode subsection.

    The criteria that name this window say "§ PLAN pre-flight". The mode
    sections that follow are a different contract, and the evidence-manifest
    row much further down lists the rung keys in order as the field's
    vocabulary — so a whole-file search passes with the pre-flight deleted.
    That is not hypothetical: it shipped, and a review caught it.
    """
    return section(read(SKILL), "## PLAN phase", "\n## ", "\n### Mode:")
