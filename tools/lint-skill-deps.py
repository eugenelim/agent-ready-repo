#!/usr/bin/env python3
"""Lints the `dependencies:` block on every skill and subagent manifest.
Exit non-zero if any dep cites a path that doesn't exist, or an anchor
that the target file doesn't define. Companion to lint-agent-artifacts.py,
which only checks frontmatter shape — this one checks the semantics.

Why it exists: manifests rot. Skills are renamed; CONVENTIONS anchors
get edited away; templates move. Without a linter, install-skill.py
silently produces broken installs.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys


def _repo_root() -> pathlib.Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path.cwd()


# Adopter-owned files: a skill installed elsewhere lands on top of the
# adopter's own copy of these, and install-skill.py emits whole-file deps
# as fragments under `*.fragments/<skill>.md` for the adopter to merge by
# hand. A whole-file dep is almost always a mistake — the skill rarely
# needs all of our prose. Authors should anchor-cite the specific section
# they need, or omit the dep and read at runtime (the reviewer pattern).
# Mirrors FRAGMENT_FILES in tools/install-skill.py.
FRAGMENT_FILES = {"AGENTS.md", "docs/CONVENTIONS.md", "docs/CHARTER.md"}


def _parse_frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    fields: dict = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "[]":
            fields[key] = []
            i += 1
            continue
        if val == "":
            items = []
            j = i + 1
            while j < end:
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                lm = re.match(r"^\s+-\s+(.*)$", nxt)
                if not lm:
                    break
                items.append(lm.group(1).strip())
                j += 1
            fields[key] = items
            i = j
            continue
        fields[key] = val
        i += 1
    return fields


def _slugify(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s.strip("-")


def _file_has_anchor(path: pathlib.Path, anchor: str) -> bool:
    for line in path.read_text().splitlines():
        m = re.match(r"^#+\s+(.*)$", line)
        if m and _slugify(m.group(1)) == anchor:
            return True
    return False


def main() -> int:
    os.chdir(_repo_root())
    root = pathlib.Path(os.environ.get("LINT_ROOT", ".")).resolve()
    error_count = 0

    def err(path: pathlib.Path, msg: str) -> None:
        nonlocal error_count
        rel = path.resolve().relative_to(root) if path.is_absolute() else path
        print(f"✖ {rel}: {msg}", file=sys.stderr)
        error_count += 1

    def ok(msg: str) -> None:
        print(f"✓ {msg}")

    def check(manifest_path: pathlib.Path) -> None:
        nonlocal error_count
        fields = _parse_frontmatter(manifest_path)
        deps = fields.get("dependencies", [])
        if not isinstance(deps, list):
            err(
                manifest_path,
                "`dependencies:` must be a list (block style `- item` or flow `[]`)",
            )
            return
        for dep in deps:
            path_part, _, anchor = dep.partition("#")
            anchor = anchor or None
            target = root / path_part
            if not target.exists():
                err(manifest_path, f"dependency points at missing file: {dep}")
                continue
            if target.is_dir():
                err(
                    manifest_path,
                    f"dependency points at a directory: {dep} "
                    f"(manifests must list individual files)",
                )
                continue
            if path_part in FRAGMENT_FILES and not anchor:
                err(
                    manifest_path,
                    f"whole-file dep on adopter-owned {path_part} is forbidden — "
                    f"cite a section by anchor (e.g. {path_part}#section-slug) "
                    f"or omit and read at runtime. See .claude/skills/README.md.",
                )
                continue
            if anchor and not _file_has_anchor(target, anchor):
                err(manifest_path, f"anchor #{anchor} not found in {path_part}")

    checked = 0
    skills_dir = root / ".claude" / "skills"
    agents_dir = root / ".claude" / "agents"

    if skills_dir.exists():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            checked += 1
            before = error_count
            check(skill_md)
            if error_count == before:
                ok(f"{skill_md.relative_to(root)}")

    if agents_dir.exists():
        for agent_md in sorted(agents_dir.glob("*.md")):
            if agent_md.name.upper() == "README.md":
                continue
            checked += 1
            before = error_count
            check(agent_md)
            if error_count == before:
                ok(f"{agent_md.relative_to(root)}")

    print()
    print(f"Manifests checked: {checked}.")
    if error_count:
        print(f"Skill-dep lint: failed ({error_count} error(s)).")
        return 1
    print("Skill-dep lint: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
