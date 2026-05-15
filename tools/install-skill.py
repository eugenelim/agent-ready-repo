#!/usr/bin/env python3
"""Install one skill (with its transitive dependencies) into an existing repo.

Path B of the bootstrap: when an adopter already has their own repo and
just wants to pull in one or two skills, they run:

    python3 tools/install-skill.py <skill-or-agent-name> /path/to/their-repo

The script walks the dependency closure declared in each artifact's YAML
frontmatter (`dependencies:` list) and copies every leaf into the
destination, preserving the source layout. Existing files at the
destination are never clobbered; both no-op cases warn and skip so
the adopter sees exactly what was and wasn't written:

  - byte-identical to source -> warn-and-skip ("already present")
  - content differs          -> warn-and-skip ("kept your version")

Docs are special. `docs/CONVENTIONS.md` and `AGENTS.md` belong to the
adopter, not us. If a skill depends on a section of either (e.g.
`docs/CONVENTIONS.md#contract-tests-vs-construction-tests`) or on the
whole file (the `update-conventions` case), the script writes the
relevant slice to `<dest>/docs/CONVENTIONS.fragments/<skill>.md` rather
than overwriting. The user merges manually; auto-splicing someone else's
governance doc is a trap.

The script is pure-stdlib Python 3 so PowerShell adopters don't need to
install bash. Exit non-zero on any hard error (missing source dep,
unknown target name); skip-with-warning is not an error.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys
from dataclasses import dataclass, field
from typing import Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

SKILL_DIR = ".claude/skills"
AGENT_DIR = ".claude/agents"
# Files that belong to the adopter, not us. Dependencies on these (whole or
# by anchor) are emitted as fragments rather than copied — auto-splicing
# governance prose is a trap. The reviewer agents (adversarial-, security-,
# quality-) intentionally do NOT list these in their `dependencies:` even
# though their bodies say "read AGENTS.md and docs/CONVENTIONS.md first":
# they read whatever the adopter has at runtime, not the template's version.
FRAGMENT_FILES = {"docs/CONVENTIONS.md", "AGENTS.md", "docs/CHARTER.md"}

# Files we'd rather never carry along when copying a skill folder. Skill
# folders are SKILL.md plus optional support material; OS junk and Python
# bytecode caches are neither.
SKILL_FOLDER_IGNORES = (".DS_Store", "Thumbs.db")
SKILL_FOLDER_IGNORE_DIRS = ("__pycache__", ".git")


@dataclass
class Plan:
    """What install-skill.py decided to do, ready to be applied."""

    # File-copy entries: (source_relpath, dest_relpath).
    copies: list[tuple[str, str]] = field(default_factory=list)
    # Fragment entries: (source_relpath, anchor_or_None, dest_relpath, owning_skill).
    fragments: list[tuple[str, str | None, str, str]] = field(default_factory=list)
    # Names already visited so we don't recurse forever.
    visited: set[str] = field(default_factory=set)


# ── Frontmatter parsing ───────────────────────────────────────────────────


def parse_frontmatter(path: pathlib.Path) -> dict:
    """Return frontmatter fields. Supports scalar values and block-style
    YAML lists (`key:` followed by `  - item` lines). Mirrors the parser
    in tools/lint-agent-artifacts.sh."""
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
        raise ValueError(f"{path}: frontmatter opened with --- but never closed")
    fields: dict = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", raw)
        if not m:
            raise ValueError(f"{path}: malformed frontmatter line {i + 1}: {raw!r}")
        key, val = m.group(1), m.group(2).strip()
        if val == "[]":
            fields[key] = []
            i += 1
            continue
        if val == "":
            items: list[str] = []
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


# ── Resolving names and dependencies ──────────────────────────────────────


def resolve_target(name: str) -> pathlib.Path:
    """Find the source artifact (skill SKILL.md or agent .md) by name.
    Names are kebab-case; we accept either."""
    skill = REPO_ROOT / SKILL_DIR / name / "SKILL.md"
    agent = REPO_ROOT / AGENT_DIR / f"{name}.md"
    if skill.exists():
        return skill
    if agent.exists():
        return agent
    raise SystemExit(
        f"error: unknown skill or agent {name!r}. "
        f"Looked for {skill.relative_to(REPO_ROOT)} and {agent.relative_to(REPO_ROOT)}."
    )


def split_anchor(dep: str) -> tuple[str, str | None]:
    """`path` or `path#anchor` -> (path, anchor-or-None)."""
    if "#" in dep:
        path, anchor = dep.split("#", 1)
        return path, anchor
    return dep, None


def is_skill_md(rel: str) -> bool:
    return rel.startswith(f"{SKILL_DIR}/") and rel.endswith("/SKILL.md")


def is_agent_md(rel: str) -> bool:
    return rel.startswith(f"{AGENT_DIR}/") and rel.endswith(".md")


def skill_name_of(rel: str) -> str:
    """`.claude/skills/<name>/SKILL.md` -> `<name>`. Caller must verify."""
    parts = rel.split("/")
    return parts[2]


# ── Building the install plan ─────────────────────────────────────────────


def build_plan(target_rel: str, owning_skill: str, plan: Plan) -> None:
    """Walk the dependency closure rooted at `target_rel` and populate plan.
    `owning_skill` names the top-level skill we're installing (for naming
    fragment files)."""
    if target_rel in plan.visited:
        return
    plan.visited.add(target_rel)

    src = REPO_ROOT / target_rel
    if not src.exists():
        raise SystemExit(
            f"error: dependency points at {target_rel} but that file is not "
            f"present in the template source. The manifest is wrong; run "
            f"tools/lint-skill-deps.sh."
        )

    # Skill = whole folder. Copy every file under .claude/skills/<name>/,
    # skipping OS junk and bytecode caches.
    if is_skill_md(target_rel):
        name = skill_name_of(target_rel)
        for f in sorted((REPO_ROOT / SKILL_DIR / name).rglob("*")):
            if not f.is_file():
                continue
            if f.name in SKILL_FOLDER_IGNORES:
                continue
            if any(part in SKILL_FOLDER_IGNORE_DIRS for part in f.relative_to(REPO_ROOT).parts):
                continue
            rel = f.relative_to(REPO_ROOT).as_posix()
            plan.copies.append((rel, rel))
        # Follow the skill's own deps.
        for dep in parse_frontmatter(src).get("dependencies", []) or []:
            recurse_dep(dep, owning_skill, plan)
        return

    # Agent = single file.
    if is_agent_md(target_rel):
        plan.copies.append((target_rel, target_rel))
        for dep in parse_frontmatter(src).get("dependencies", []) or []:
            recurse_dep(dep, owning_skill, plan)
        return

    # Plain leaf (template, tool script, etc.). Refuse directories — they
    # have no defined copy semantics here and would crash apply() with
    # IsADirectoryError mid-write.
    if src.is_dir():
        raise SystemExit(
            f"error: dependency {target_rel} resolves to a directory. "
            f"Manifests must point at individual files; if you need a whole "
            f"directory, list the files explicitly."
        )
    plan.copies.append((target_rel, target_rel))


def fragment_dest(dep_path: str, owning_skill: str) -> str:
    """Where in the adopter's repo a fragment for `dep_path` lands."""
    parent = pathlib.PurePosixPath(dep_path).parent.as_posix()
    stem = pathlib.PurePosixPath(dep_path).stem  # CONVENTIONS, AGENTS, CHARTER
    parent_prefix = f"{parent}/" if parent and parent != "." else ""
    return f"{parent_prefix}{stem}.fragments/{owning_skill}.md"


def recurse_dep(dep: str, owning_skill: str, plan: Plan) -> None:
    """Add a single dependency entry to the plan."""
    dep_path, anchor = split_anchor(dep)
    if dep_path in FRAGMENT_FILES:
        plan.fragments.append(
            (dep_path, anchor, fragment_dest(dep_path, owning_skill), owning_skill)
        )
        return
    # Everything else: recursive copy with manifest-following.
    build_plan(dep_path, owning_skill, plan)


# ── Section extraction for fragment emission ──────────────────────────────


def slugify(heading: str) -> str:
    """Convert a markdown heading text to its GitHub-style anchor slug."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s.strip("-")


def extract_section(source_text: str, anchor: str) -> str:
    """Return the markdown chunk under the heading whose slug matches
    `anchor`, up to (but not including) the next heading of the same or
    higher level. Raises if no matching heading is found."""
    lines = source_text.splitlines()
    target_level = None
    start = None
    for i, line in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*)$", line)
        if not m:
            continue
        level = len(m.group(1))
        heading = m.group(2)
        if slugify(heading) == anchor:
            target_level = level
            start = i
            break
    if start is None:
        raise SystemExit(
            f"error: anchor '#{anchor}' not found in source — "
            f"manifest claims a section that does not exist."
        )
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#+)\s+", lines[j])
        if m and len(m.group(1)) <= target_level:
            end = j
            break
    # Trim trailing blanks and bare horizontal rules — those belong to the
    # source doc's section divider, not the section we're extracting.
    while end > start + 1 and (not lines[end - 1].strip()
                               or lines[end - 1].strip() == "---"):
        end -= 1
    return "\n".join(lines[start:end]).rstrip() + "\n"


def render_fragment(source_rel: str, anchor: str | None,
                    owning_skill: str, body: str) -> str:
    """Wrap a section (or whole file) in a header explaining what it is
    and what the adopter should do with it."""
    header = (
        f"<!--\n"
        f"  Fragment emitted by tools/install-skill.py when installing "
        f"the '{owning_skill}' skill.\n"
        f"  Source: {source_rel}"
        f"{(' #' + anchor) if anchor else ''}\n"
        f"\n"
        f"  This is the slice the skill depends on. It has NOT been merged\n"
        f"  into your repo's {source_rel} because doing so safely would\n"
        f"  require understanding your version. Reconcile manually:\n"
        f"  copy the relevant prose into your own {source_rel}, then\n"
        f"  delete this file.\n"
        f"-->\n\n"
    )
    return header + body


# ── Apply the plan to the destination ─────────────────────────────────────


def safe_join(dest: pathlib.Path, rel: str) -> pathlib.Path:
    """Join `dest` and `rel`, refusing paths that resolve outside `dest`.
    Cheap defense against a manifest that contains `..` segments."""
    target = (dest / rel).resolve()
    dest_root = dest.resolve()
    try:
        target.relative_to(dest_root)
    except ValueError:
        raise SystemExit(
            f"error: dependency path {rel!r} escapes the destination "
            f"directory. Refusing to write."
        )
    return target


def apply(plan: Plan, dest: pathlib.Path) -> tuple[list[str], list[str], list[str], list[str]]:
    """Apply the plan. Returns (installed, already_present, conflicts,
    fragments) — each a list of dest-relative paths for the summary.
    Both 'already present' (byte-identical) and 'conflicts' (content
    differs) print a warn-and-skip line at the moment they're detected;
    silence on a no-op would let an adopter assume the file was written."""
    installed: list[str] = []
    already_present: list[str] = []
    conflicts: list[str] = []
    fragments: list[str] = []

    # Dedupe copies while preserving order.
    seen: set[tuple[str, str]] = set()
    for src_rel, dest_rel in plan.copies:
        if (src_rel, dest_rel) in seen:
            continue
        seen.add((src_rel, dest_rel))
        src = REPO_ROOT / src_rel
        dst = safe_join(dest, dest_rel)
        if dst.exists():
            if dst.read_bytes() == src.read_bytes():
                print(f"= {dest_rel} — already present (identical), skipping",
                      file=sys.stderr)
                already_present.append(dest_rel)
                continue
            print(f"! {dest_rel} — exists with different content, skipping",
                  file=sys.stderr)
            conflicts.append(dest_rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append(dest_rel)

    # Group fragments by destination path so multiple anchors on the same
    # source file end up in one fragment file rather than racing for the
    # same path. Whole-file deps (anchor=None) supersede anchored sections
    # — there's no point shipping a slice when the caller wants the whole
    # doc.
    by_dest: dict[str, list[tuple[str, str | None, str]]] = {}
    for src_rel, anchor, dest_rel, owning_skill in plan.fragments:
        by_dest.setdefault(dest_rel, []).append((src_rel, anchor, owning_skill))

    for dest_rel, entries in by_dest.items():
        # Dedupe by (src_rel, anchor); preserve order.
        seen_keys: set[tuple[str, str | None]] = set()
        ordered: list[tuple[str, str | None, str]] = []
        for src_rel, anchor, owning_skill in entries:
            key = (src_rel, anchor)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            ordered.append((src_rel, anchor, owning_skill))
        if any(anchor is None for _, anchor, _ in ordered):
            ordered = [e for e in ordered if e[1] is None][:1]

        parts: list[str] = []
        for src_rel, anchor, owning_skill in ordered:
            src = REPO_ROOT / src_rel
            if anchor:
                body = extract_section(src.read_text(), anchor)
            else:
                body = src.read_text().rstrip() + "\n"
            parts.append(render_fragment(src_rel, anchor, owning_skill, body))
        content = "\n".join(parts)

        dst = safe_join(dest, dest_rel)
        if dst.exists():
            if dst.read_text() == content:
                print(f"= {dest_rel} — fragment already present (identical), skipping",
                      file=sys.stderr)
                already_present.append(dest_rel)
                continue
            print(f"! {dest_rel} — exists with different content, skipping",
                  file=sys.stderr)
            conflicts.append(dest_rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content)
        fragments.append(dest_rel)

    return installed, already_present, conflicts, fragments


# ── Entrypoint ────────────────────────────────────────────────────────────


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="install-skill.py",
        description="Install a skill (and its dependency closure) into an existing repo.",
    )
    parser.add_argument("name", help="Skill or agent name (kebab-case, e.g. bug-fix).")
    parser.add_argument(
        "dest",
        type=pathlib.Path,
        help="Destination repo root. Must already exist.",
    )
    args = parser.parse_args(argv)

    dest = args.dest.resolve()
    if not dest.exists() or not dest.is_dir():
        print(f"error: destination {dest} does not exist or is not a directory.",
              file=sys.stderr)
        return 1

    target = resolve_target(args.name)
    target_rel = target.relative_to(REPO_ROOT).as_posix()

    plan = Plan()
    build_plan(target_rel, owning_skill=args.name, plan=plan)
    installed, already_present, conflicts, fragments = apply(plan, dest)

    print()
    print(f"Installed '{args.name}' into {dest}")
    print()
    if installed:
        print(f"  Copied ({len(installed)}):")
        for p in installed:
            print(f"    + {p}")
    if fragments:
        print(f"  Fragments ({len(fragments)}):")
        for p in fragments:
            print(f"    ~ {p}    (reconcile into your own copy of the source file)")
    if already_present:
        print(f"  Already present, identical to source ({len(already_present)}):")
        for p in already_present:
            print(f"    = {p}")
    if conflicts:
        print(f"  Skipped — destination already has a different version "
              f"({len(conflicts)}):")
        for p in conflicts:
            print(f"    ! {p}")
        print()
        print("  These files at the destination differ from the source. They "
              "were left alone.")
        print("  If you want the source version, diff against the template "
              "and merge by hand.")
    if not (installed or fragments or already_present or conflicts):
        print("  (Nothing to install — the manifest is empty.)")
    print()
    if fragments:
        print("Next step: merge the fragments above into the matching files "
              "in your repo, then delete the fragment files. (Re-running "
              "this command will re-emit them — the script can't tell that "
              "you've already reconciled.)")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
