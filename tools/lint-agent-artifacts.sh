#!/usr/bin/env bash
# Lints the agent artifacts under .claude/ — skills, subagents, commands.
# Companion to tools/lint-agents-md.sh, which handles docs structure and
# AGENTS.md hygiene. Exit non-zero if any check fails.
#
# Checks (per artifact type):
#   Skills (.claude/skills/<name>/SKILL.md):
#     - File exists, has valid YAML frontmatter delimited by ---
#     - Frontmatter has non-empty `name` (kebab-case) and `description`
#     - Directory name == frontmatter `name`
#     - Frontmatter has no unknown keys (allowed: name, description)
#
#   Subagents (.claude/agents/<name>.md):
#     - File has valid YAML frontmatter
#     - Frontmatter has non-empty `name` (kebab-case), `description`,
#       and `model` (see docs/CONVENTIONS.md#model-selection)
#     - Filename (sans .md) == frontmatter `name`
#     - Frontmatter has no unknown keys (allowed: name, description,
#       tools, model, dependencies)
#
#   Commands (.claude/commands/<name>.md):
#     - File has valid YAML frontmatter (optional but if present,
#       enforce shape)
#     - Frontmatter, if present, has non-empty `description`
#     - Frontmatter has no unknown keys (allowed: description,
#       allowed-tools, model, argument-hint)
#     - Body (after frontmatter) is non-empty
#
#   All of the above:
#     - Internal markdown links resolve (relative paths, no anchors-only).
#
# A fixture mode is supported for self-testing:
#   LINT_ROOT=tools/fixtures/<dir> bash tools/lint-agent-artifacts.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Allow self-test fixtures to override the lint root.
LINT_ROOT="${LINT_ROOT:-.}"

python3 - "$LINT_ROOT" <<'PY'
import pathlib, re, sys

root = pathlib.Path(sys.argv[1]).resolve()
error_count = 0

KEBAB = re.compile(r"^[a-z][a-z0-9-]*$")
LINK = re.compile(r"\]\(([^)]+)\)")

ALLOWED_SKILL_KEYS = {"name", "description", "dependencies"}
ALLOWED_AGENT_KEYS = {"name", "description", "tools", "model", "dependencies"}
ALLOWED_COMMAND_KEYS = {"description", "allowed-tools", "model", "argument-hint"}


def relpath(path):
    """Best-effort relative path for human-readable output."""
    p = pathlib.Path(path)
    if not p.is_absolute():
        return p
    try:
        return p.resolve().relative_to(root)
    except ValueError:
        return p


def err(path, msg, line=None):
    global error_count
    rel = relpath(path)
    loc = f"{rel}:{line}" if line else str(rel)
    print(f"✖ {loc}: {msg}", file=sys.stderr)
    error_count += 1


def ok(msg):
    print(f"✓ {msg}")


def warn(msg):
    print(f"⚠ {msg}", file=sys.stderr)


def parse_frontmatter(path):
    """Return (fields, body_start_line, body, error). Frontmatter is the
    block delimited by --- on its own line at the very top of the file.
    Supports `key: value` single-line scalars and `key:` followed by a
    block-style YAML list (each item on its own line, prefixed `  - `).
    No deeper nesting — that matches every artifact this repo ships."""
    text = path.read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0, text, None  # No frontmatter — caller decides if that's an error
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, 0, text, "frontmatter opened with --- but never closed"
    fields = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", raw)
        if not m:
            return None, 0, text, f"malformed frontmatter line {i + 1}: {raw!r}"
        key, val = m.group(1), m.group(2).strip()
        if key in fields:
            return None, 0, text, f"duplicate frontmatter key {key!r} (line {i + 1})"
        # Flow-list shortcut: `key: []` means empty list.
        if val == "[]":
            fields[key] = []
            i += 1
            continue
        # Block-style list: `key:` (empty value) followed by `  - item` lines.
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
    body_start_line = end + 2  # 1-indexed line number where body starts
    body = "\n".join(lines[end + 1 :])
    return fields, body_start_line, body, None


def check_links(path, body, body_start_line):
    """Check that relative markdown links resolve."""
    base = path.parent
    for offset, line in enumerate(body.splitlines()):
        for match in LINK.finditer(line):
            target = match.group(1).split("#", 1)[0].strip()
            if not target:
                continue
            if re.match(r"^[a-z]+:", target):  # http:, mailto:, etc.
                continue
            resolved = (base / target).resolve()
            if not resolved.exists():
                err(path, f"broken link → {match.group(1)}",
                    line=body_start_line + offset)


def check_skill(path):
    fields, body_start, body, ferr = parse_frontmatter(path)
    if ferr:
        err(path, ferr)
        return
    if fields is None:
        err(path, "missing YAML frontmatter (--- ... ---)")
        return
    if "name" not in fields or not fields["name"]:
        err(path, "frontmatter missing required key: name")
    elif not KEBAB.match(fields["name"]):
        err(path, f"name {fields['name']!r} must be kebab-case ([a-z][a-z0-9-]*)")
    elif fields["name"] != path.parent.name:
        err(path, f"name {fields['name']!r} does not match directory "
                  f"{path.parent.name!r}")
    if "description" not in fields or not fields["description"]:
        err(path, "frontmatter missing required key: description")
    unknown = set(fields) - ALLOWED_SKILL_KEYS
    if unknown:
        err(path, f"unknown frontmatter keys: {sorted(unknown)} "
                  f"(allowed: {sorted(ALLOWED_SKILL_KEYS)})")
    if not body.strip():
        err(path, "body is empty")
    check_links(path, body, body_start)


def check_agent(path):
    fields, body_start, body, ferr = parse_frontmatter(path)
    if ferr:
        err(path, ferr)
        return
    if fields is None:
        err(path, "missing YAML frontmatter (--- ... ---)")
        return
    expected_name = path.stem
    if "name" not in fields or not fields["name"]:
        err(path, "frontmatter missing required key: name")
    elif not KEBAB.match(fields["name"]):
        err(path, f"name {fields['name']!r} must be kebab-case ([a-z][a-z0-9-]*)")
    elif fields["name"] != expected_name:
        err(path, f"name {fields['name']!r} does not match filename "
                  f"{expected_name!r}")
    if "description" not in fields or not fields["description"]:
        err(path, "frontmatter missing required key: description")
    if "model" not in fields or not fields["model"]:
        err(path, "frontmatter missing required key: model "
                  "(see docs/CONVENTIONS.md#model-selection)")
    unknown = set(fields) - ALLOWED_AGENT_KEYS
    if unknown:
        err(path, f"unknown frontmatter keys: {sorted(unknown)} "
                  f"(allowed: {sorted(ALLOWED_AGENT_KEYS)})")
    if not body.strip():
        err(path, "body is empty")
    check_links(path, body, body_start)


def check_command(path):
    fields, body_start, body, ferr = parse_frontmatter(path)
    if ferr:
        err(path, ferr)
        return
    # Frontmatter is optional for commands; if present, enforce shape.
    if fields is not None:
        if "description" not in fields or not fields["description"]:
            err(path, "frontmatter missing required key: description")
        unknown = set(fields) - ALLOWED_COMMAND_KEYS
        if unknown:
            err(path, f"unknown frontmatter keys: {sorted(unknown)} "
                      f"(allowed: {sorted(ALLOWED_COMMAND_KEYS)})")
    if not body.strip():
        err(path, "body is empty")
    check_links(path, body, body_start)


# ── Discover and check ────────────────────────────────────────────────────
skills_dir = root / ".claude" / "skills"
agents_dir = root / ".claude" / "agents"
commands_dir = root / ".claude" / "commands"

if not (skills_dir.exists() or agents_dir.exists() or commands_dir.exists()):
    warn(f"no .claude/ artifacts found under {root} — nothing to lint")

skill_count = agent_count = command_count = 0

if skills_dir.exists():
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        skill_count += 1
        rel = skill_md.relative_to(root)
        before = error_count
        check_skill(skill_md)
        if error_count == before:
            ok(f"{rel}")
    # Also flag stray non-SKILL.md files at the skill level (typos like skill.md).
    for stray in sorted(skills_dir.glob("*/*.md")):
        if stray.name != "SKILL.md":
            err(stray.relative_to(root),
                "unexpected file in skill dir; skill bodies must be named SKILL.md")
    # Flag skill dirs with no SKILL.md.
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        if not (skill_dir / "SKILL.md").exists():
            err(skill_dir.relative_to(root), "skill directory missing SKILL.md")

if agents_dir.exists():
    for agent_md in sorted(agents_dir.glob("*.md")):
        if agent_md.name.upper() == "README.md":
            continue
        agent_count += 1
        rel = agent_md.relative_to(root)
        before = error_count
        check_agent(agent_md)
        if error_count == before:
            ok(f"{rel}")

if commands_dir.exists():
    for cmd_md in sorted(commands_dir.glob("*.md")):
        if cmd_md.name.upper() == "README.md":
            continue
        command_count += 1
        rel = cmd_md.relative_to(root)
        before = error_count
        check_command(cmd_md)
        if error_count == before:
            ok(f"{rel}")

print()
print(f"Artifacts checked: {skill_count} skill(s), "
      f"{agent_count} subagent(s), {command_count} command(s).")

if error_count:
    print()
    print(f"Agent-artifact lint: failed ({error_count} error(s)).")
    sys.exit(1)

print("Agent-artifact lint: passed.")
PY
