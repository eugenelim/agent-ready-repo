#!/usr/bin/env python3
"""Generate the "Skills by job" page and check its input is complete.

Input: ``docs-site/src/skills-catalogue.toml`` (job, want, ask, gets per skill, and
an optional ``sequence`` label for skills that form a lifecycle sequence).
Facts taken from the tree: which skills exist and which pack holds each.
Output: ``docs-site/src/content/docs/packs/skills.md`` (never hand-edited).

Row order in each job: lifecycle sequences first, each in lifecycle order (file
order), then every other skill A to Z by skill name. ``validate`` enforces it.

A skill is internal, and left off the page, when its frontmatter has
``metadata.generated-by`` starting with ``compile-okf``: it is a router the
agent loads, not something a reader asks for.

Usage:
  python3 tools/skills_catalogue.py --check   # validate input and page, write nothing
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
CATALOGUE_TOML = REPO_ROOT / "docs-site" / "src" / "skills-catalogue.toml"
PAGE_PATH = REPO_ROOT / "docs-site" / "src" / "content" / "docs" / "packs" / "skills.md"
SITE_BASE = "/agent-ready-repo/docs"

# Page order. A job outside this list is an input error.
JOBS = (
    "Set up a repository",
    "Decide what to build",
    "Shape it",
    "Build it",
    "Ship it",
    "Any stage",
)
FIELDS = ("job", "want", "ask", "gets")
COLUMNS = ("I want to", "Example ask", "You get", "Pack")
INTERNAL_PREFIX = "compile-okf"


def _frontmatter(text: str) -> str:
    """Return the raw frontmatter block, or an empty string."""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def discover_skills(packs_dir: Path) -> tuple[dict[str, str], set[str]]:
    """Return ({user-invocable skill: pack}, {internal skill names}).

    Packs whose directory starts with ``_`` are not public and are skipped.
    """
    public: dict[str, str] = {}
    internal: set[str] = set()
    for skill_md in sorted(packs_dir.glob("*/.apm/skills/*/SKILL.md")):
        pack = skill_md.relative_to(packs_dir).parts[0]
        if pack.startswith("_"):
            continue
        fm = _frontmatter(skill_md.read_text(encoding="utf-8"))
        name = skill_md.parent.name
        generated = re.search(r"^\s+generated-by:\s*[\"']?(\S+)", fm, re.MULTILINE)
        if generated and generated.group(1).startswith(INTERNAL_PREFIX):
            internal.add(name)
        else:
            public[name] = pack
    return public, internal


def load_entries(path: Path) -> dict[str, dict[str, str]]:
    """Return the ``[skills.<name>]`` tables in file order."""
    with path.open("rb") as handle:
        return tomllib.load(handle).get("skills", {})


def validate(
    entries: dict[str, dict[str, str]], public: dict[str, str], internal: set[str]
) -> list[str]:
    """Return one message per input problem, each naming the skill."""
    errors = [
        f"{name}: user-invocable skill has no entry in {CATALOGUE_TOML.name}"
        for name in public
        if name not in entries
    ]
    for name, entry in entries.items():
        if name in internal:
            errors.append(f"{name}: internal skill must not be listed")
        elif name not in public:
            errors.append(f"{name}: stale entry, no such skill")
            continue
        for field in FIELDS:
            if not str(entry.get(field, "")).strip():
                errors.append(f"{name}: empty {field}")
        if entry.get("job") and entry["job"] not in JOBS:
            errors.append(f"{name}: unknown job {entry['job']!r}")
    return errors + _order_errors(entries)


def _order_errors(entries: dict[str, dict[str, str]]) -> list[str]:
    """Check the stated row order: sequences first and contiguous, the rest A to Z."""
    errors: list[str] = []
    for job in JOBS:
        rows = [(n, e.get("sequence", "")) for n, e in entries.items() if e.get("job") == job]
        seen: list[str] = []
        previous = ""
        plain_started = False
        last_plain = ""
        for name, seq in rows:
            if not seq:
                plain_started = True
                if last_plain and name < last_plain:
                    errors.append(f"{name}: not A to Z in {job!r} (after {last_plain})")
                last_plain = name
                previous = ""
                continue
            if plain_started:
                errors.append(
                    f"{name}: sequence {seq!r} must come before the A to Z rows in {job!r}"
                )
            if seq != previous and seq in seen:
                errors.append(f"{name}: sequence {seq!r} is split in {job!r}")
            if seq not in seen:
                seen.append(seq)
            previous = seq
    labels: dict[str, str] = {}
    for name, entry in entries.items():
        seq = entry.get("sequence", "")
        if seq and labels.setdefault(seq, entry.get("job", "")) != entry.get("job", ""):
            errors.append(f"{name}: sequence {seq!r} spans more than one job")
    return errors


def _cell(text: str) -> str:
    """Escape text for one Markdown table cell."""
    return " ".join(text.split()).replace("|", "\\|")


def render(entries: dict[str, dict[str, str]], public: dict[str, str]) -> str:
    """Return the page. Same input gives the same bytes."""
    lines = [
        "---",
        'title: "Skills by job"',
        'description: "Find the skill for your job, the request to paste, and what you get back."',
        "---",
        "",
        "Find your job below. Skills are grouped by job. Inside a group, skills that form "
        "a sequence come first in lifecycle order, marked Step 1 of 3, Step 2 of 3 and so on, "
        "and the rest run A to Z by skill name. Any wording that states your job works; the "
        "Example ask column shows one way to say it. Each skill comes from the pack in the "
        "last column, so install that pack first.[^1]",
        "",
    ]
    for job in JOBS:
        rows = [(n, e) for n, e in entries.items() if e["job"] == job and n in public]
        if not rows:
            continue
        lines += [
            f"## {job}",
            "",
            f"| {' | '.join(COLUMNS)} |",
            "| " + " | ".join("---" for _ in COLUMNS) + " |",
        ]
        step, label = 0, ""
        labels = [e.get("sequence", "") for _, e in rows]
        size = {s: labels.count(s) for s in set(labels) if s}
        for name, entry in rows:
            pack = public[name]
            seq = entry.get("sequence", "")
            step = step + 1 if seq and seq == label else 1 if seq else 0
            label = seq
            want = f"Step {step} of {size[seq]}: {entry['want']}" if step else entry["want"]
            lines.append(
                f"| {_cell(want)} | {_cell(entry['ask'])} | "
                f"{_cell(entry['gets'])} | [{pack}]({SITE_BASE}/packs/{pack}/) |"
            )
        lines.append("")
    lines += [
        f"Next: [Install packs for your agent]({SITE_BASE}/guides/_shared/how-to/install-packs/).",
        "",
        "[^1]: This page is generated from `docs-site/src/skills-catalogue.toml` "
        "and the skills under `packs/`. Skills that only route other skills are left out.",
        "",
    ]
    return "\n".join(lines)


def build(repo_root: Path = REPO_ROOT) -> str:
    """Validate the input and return the page; raise ValueError on any problem."""
    public, internal = discover_skills(repo_root / "packs")
    entries = load_entries(repo_root / "docs-site" / "src" / "skills-catalogue.toml")
    errors = validate(entries, public, internal)
    if errors:
        raise ValueError("skills catalogue input is invalid:\n  " + "\n  ".join(errors))
    return render(entries, public)


def check(repo_root: Path = REPO_ROOT) -> list[str]:
    """Return problems with the input, or with a generated page that is out of date."""
    try:
        page = build(repo_root)
    except ValueError as exc:
        return [line.strip() for line in str(exc).splitlines()[1:]]
    target = repo_root / "docs-site" / "src" / "content" / "docs" / "packs" / "skills.md"
    if target.exists() and target.read_text(encoding="utf-8") != page:
        return [f"{target.relative_to(repo_root)}: out of date, rerun tools/build-site.py"]
    return []


def main() -> int:
    """Command line: ``--check`` reports problems and writes nothing."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    problems = check()
    for problem in problems:
        print(f"skills-catalogue: {problem.strip()}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
