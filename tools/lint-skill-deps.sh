#!/usr/bin/env bash
# Lints the `dependencies:` block on every skill and subagent manifest.
# Exit non-zero if any dep cites a path that doesn't exist, or an anchor
# that the target file doesn't define. Companion to lint-agent-artifacts.sh,
# which only checks frontmatter shape — this one checks the semantics.
#
# Why it exists: manifests rot. Skills are renamed; CONVENTIONS anchors
# get edited away; templates move. Without a linter, install-skill.py
# silently produces broken installs.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

LINT_ROOT="${LINT_ROOT:-.}"

python3 - "$LINT_ROOT" <<'PY'
import pathlib, re, sys

root = pathlib.Path(sys.argv[1]).resolve()
error_count = 0


def err(path, msg):
    global error_count
    rel = path.resolve().relative_to(root) if path.is_absolute() else path
    print(f"✖ {rel}: {msg}", file=sys.stderr)
    error_count += 1


def ok(msg):
    print(f"✓ {msg}")


def parse_frontmatter(path):
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
    fields = {}
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


def slugify(heading):
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s.strip("-")


def file_has_anchor(path, anchor):
    for line in path.read_text().splitlines():
        m = re.match(r"^#+\s+(.*)$", line)
        if m and slugify(m.group(1)) == anchor:
            return True
    return False


def check(manifest_path):
    fields = parse_frontmatter(manifest_path)
    deps = fields.get("dependencies", [])
    if not isinstance(deps, list):
        err(manifest_path, "`dependencies:` must be a list (block style `- item` or flow `[]`)")
        return
    for dep in deps:
        path_part, _, anchor = dep.partition("#")
        anchor = anchor or None
        target = root / path_part
        if not target.exists():
            err(manifest_path, f"dependency points at missing file: {dep}")
            continue
        if target.is_dir():
            err(manifest_path,
                f"dependency points at a directory: {dep} "
                f"(manifests must list individual files)")
            continue
        if anchor and not file_has_anchor(target, anchor):
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
    sys.exit(1)
print("Skill-dep lint: passed.")
PY
