#!/usr/bin/env python3
"""Foundation linter for the agentskills.io specification.

Reference: https://agentskills.io/specification
           https://agentskills.io/skill-creation/evaluating-skills

Walks both the projection (.claude/skills/*/SKILL.md) and the seeds
(packs/*/.apm/skills/*/SKILL.md) and enforces every mechanical rule in
the spec. Designed as a contract for skill authors going forward — every
spec rule has a check even if no skill in the current tree trips it.

Companion to tools/lint-agent-artifacts.py: that linter is the
multi-artifact hygiene gate (skills + subagents + commands); this one is
the spec-only deep dive scoped to SKILL.md. The two overlap on the
top-level frontmatter shape; the duplication is intentional defensive
depth — the two lints have different lifecycles and the projection /
seed walk pair belongs here, not there.

Exit codes:
  0 — every checked skill is clean (warns and infos are non-fatal).
  1 — at least one skill tripped an error-level rule.

A fixture mode is supported for self-testing:
  LINT_ROOT=tools/fixtures/<dir> python3 tools/lint-skill-spec.py
"""

from __future__ import annotations

import json
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


# Per agentskills.io/specification § Frontmatter — the closed top-level
# key set. Project-specific data lives nested under `metadata:`.
ALLOWED_SKILL_KEYS = {"name", "description", "license", "compatibility",
                      "metadata", "allowed-tools"}
# Per agentskills.io/specification § Frontmatter — `name` must be
# kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`) and 1–64 chars.
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Per agentskills.io/specification § Directory layout — the four blessed
# subdirectories. `evals/` adds its own canonical layout (`evals.json`
# plus `evals/files/<fixture>`) per agentskills.io/skill-creation/evaluating-skills.
BLESSED_SUBDIRS = {"scripts", "references", "assets", "evals"}

# Not from the spec — project policy. Dev-time directories the linter
# ignores when checking layout. Scoped to things package managers
# create: `npm install`, `python -m venv`, Python's bytecode cache.
# Names like `dist/`, `build/`, `.cache/` are legitimate authored
# content in some skills, so they intentionally stay warn-eligible.
IGNORED_DEV_DIRS = {"node_modules", ".venv", "venv", "__pycache__"}

# Body path regexes — the install-prefix rule is absolute per the brief.
RE_ABS_PATH = re.compile(r"(/Users/|/home/|/opt/|/var/|/etc/|C:\\)")
# Catches both `.claude/skills/<name>/...` and the bare `.claude/skills/`
# mention (the brief flags work-loop:412 "any skill in `.claude/skills/`"
# as a violation — the install path itself is environment-specific and
# shouldn't be baked into a SKILL.md body, with or without a skill name
# after it). Same for the seed path.
RE_INSTALL_PATH = re.compile(
    r"(?<!~)(?<![\w/])"
    r"(\.claude/skills/(?:[a-z0-9-]+/)?|"
    r"packs/[a-z0-9-]+/\.apm/skills/(?:[a-z0-9-]+/)?)"
)
# `evals/` follows its own canonical layout (`evals/evals.json`,
# `evals/files/<fixture>`) per agentskills.io/skill-creation/evaluating-skills,
# so the depth check is scoped to scripts/references/assets only.
RE_DEEP_SAME_SKILL = re.compile(
    r"(?<![\w./~])((?:scripts|references|assets)/[a-z0-9_./-]+/[a-z0-9_.-]+\.[a-z0-9]+)"
)


def main() -> int:
    os.chdir(_repo_root())
    lint_root_env = os.environ.get("LINT_ROOT")
    root = pathlib.Path(lint_root_env or ".").resolve()
    if not root.exists():
        msg = (f"LINT_ROOT={lint_root_env!r} does not exist"
               if lint_root_env else f"root path {root} does not exist")
        print(f"✖ {msg}", file=sys.stderr)
        return 1
    error_count = 0
    warn_count = 0

    def relpath(path) -> pathlib.Path:
        p = pathlib.Path(path)
        if not p.is_absolute():
            return p
        try:
            return p.resolve().relative_to(root)
        except ValueError:
            return p
        except (OSError, RuntimeError):
            # `resolve()` raises OSError on Python 3.11 and RuntimeError
            # on 3.12+ when a symlink loop is in the path. Fall back to
            # the un-resolved path so the err() message still localises.
            return p

    def err(path, msg: str, line=None) -> None:
        nonlocal error_count
        rel = relpath(path)
        loc = f"{rel}:{line}" if line else str(rel)
        print(f"✖ {loc}: {msg}", file=sys.stderr)
        error_count += 1

    def warn(path, msg: str, line=None) -> None:
        nonlocal warn_count
        rel = relpath(path)
        loc = f"{rel}:{line}" if line else str(rel)
        print(f"⚠ {loc}: {msg}", file=sys.stderr)
        warn_count += 1

    def info(path, msg: str) -> None:
        rel = relpath(path)
        print(f"ℹ {rel}: {msg}")

    def ok(msg: str) -> None:
        print(f"✓ {msg}")

    # ── Block-style frontmatter parser ────────────────────────────────────
    # Copy of the parser shape in tools/lint-agent-artifacts.py. Defensive
    # depth is intentional — the two lints have different lifecycles, and
    # the spec's mapping shapes (str / bool / int / list-of-those under
    # metadata:) are exactly what the existing parser already handles.
    def parse_frontmatter(path: pathlib.Path):
        """Return (fields, body_start_line, body, error)."""
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return None, 0, "", f"SKILL.md is not valid UTF-8: {exc}"
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None, 0, text, None
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is None:
            return None, 0, text, "frontmatter opened with --- but never closed"
        fields: dict = {}
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
            if val == "[]":
                fields[key] = []
                i += 1
                continue
            if val == "":
                items: list = []
                mapping: dict = {}
                shape = None
                block_indent: int | None = None
                j = i + 1
                while j < end:
                    nxt = lines[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    indent = len(nxt) - len(nxt.lstrip())
                    if indent == 0:
                        break
                    if block_indent is None:
                        block_indent = indent
                    elif indent != block_indent:
                        return None, 0, text, (
                            f"nested frontmatter block under {key!r} "
                            f"has inconsistent indent at line {j + 1}"
                        )
                    list_m = re.match(r"^\s+-\s+(.*)$", nxt)
                    map_m = re.match(
                        r"^\s+([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", nxt)
                    if list_m and shape != "mapping":
                        shape = "list"
                        items.append(list_m.group(1).strip())
                        j += 1
                        continue
                    if map_m and shape != "list":
                        shape = "mapping"
                        ckey = map_m.group(1)
                        cval = map_m.group(2).strip()
                        if (
                            len(cval) >= 2
                            and cval[0] == cval[-1]
                            and cval[0] in ('"', "'")
                        ):
                            cval = cval[1:-1]
                        if ckey in mapping:
                            return None, 0, text, (
                                f"duplicate frontmatter key {ckey!r} "
                                f"under nested mapping (line {j + 1})"
                            )
                        mapping[ckey] = cval
                        j += 1
                        continue
                    return None, 0, text, (
                        f"nested frontmatter block under {key!r} mixes "
                        f"list and mapping shapes at line {j + 1}"
                    )
                if shape == "mapping":
                    fields[key] = mapping
                elif shape == "list":
                    fields[key] = items
                else:
                    fields[key] = ""
                i = j
                continue
            # Strip a balanced pair of surrounding quotes — kept in
            # parity with the nested-mapping branch above so quoted top-
            # level scalars (e.g. `name: "foo"`) don't carry the quotes
            # into downstream regex checks.
            if (
                len(val) >= 2
                and val[0] == val[-1]
                and val[0] in ('"', "'")
            ):
                val = val[1:-1]
            fields[key] = val
            i += 1
        body_start_line = end + 2
        body = "\n".join(lines[end + 1 :])
        return fields, body_start_line, body, None

    # ── Per-skill checks ──────────────────────────────────────────────────
    def check_frontmatter(path: pathlib.Path, fields: dict) -> None:
        # Top-level key whitelist — spec § Frontmatter.
        unknown = sorted(set(fields) - ALLOWED_SKILL_KEYS)
        if unknown:
            err(path, f"unknown top-level frontmatter keys: {unknown} "
                      f"(allowed: {sorted(ALLOWED_SKILL_KEYS)})")

        # name — required, 1–64 chars, kebab regex, matches parent dir.
        name = fields.get("name")
        if not isinstance(name, str) or not name:
            err(path, "missing required key: name")
        else:
            if not (1 <= len(name) <= 64):
                err(path, f"name {name!r} must be 1–64 chars (got {len(name)})")
            if not KEBAB.match(name):
                err(path, f"name {name!r} must match "
                          f"^[a-z0-9]+(-[a-z0-9]+)*$ (kebab-case, no "
                          f"leading/trailing/double hyphens)")
            elif name != path.parent.name:
                err(path, f"name {name!r} does not match directory "
                          f"{path.parent.name!r}")

        # description — required, non-empty, ≤1024 chars.
        desc = fields.get("description")
        if not isinstance(desc, str) or not desc:
            err(path, "missing required key: description (must be non-empty)")
        elif len(desc) > 1024:
            err(path, f"description exceeds 1024 chars (got {len(desc)})")

        # license — if present, non-empty string.
        if "license" in fields:
            lic = fields["license"]
            if not isinstance(lic, str) or not lic:
                err(path, "'license' must be a non-empty string when present")

        # compatibility — if present, 1–500 chars.
        if "compatibility" in fields:
            compat = fields["compatibility"]
            if not isinstance(compat, str) or not compat:
                err(path, "'compatibility' must be a non-empty string when present")
            elif len(compat) > 500:
                err(path, f"compatibility exceeds 500 chars (got {len(compat)})")

        # metadata — if present, must be a mapping. The agentskills.io
        # spec describes it as a mapping of strings; the block parser
        # only yields strings for scalars in any case (booleans and
        # integers arrive as their string forms). Project-specific value
        # validation (e.g. `metadata.credentialed` must be the literal
        # 'true'/'false'; `metadata.primitive-class` must be one of the
        # two allowed strings) is the job of lint-agent-artifacts.py,
        # not this linter — this one only enforces the spec's structural
        # shape so future extensions don't need a code change here.
        if "metadata" in fields:
            meta = fields["metadata"]
            if meta == "" or meta is None:
                pass  # empty mapping under `metadata:` — fine
            elif not isinstance(meta, dict):
                err(path, f"'metadata' must be a nested mapping "
                          f"(got {type(meta).__name__})")
            else:
                for mk, mv in meta.items():
                    if isinstance(mv, list):
                        for item in mv:
                            if not isinstance(item, str):
                                err(path, f"'metadata.{mk}' list entries "
                                          f"must be scalars (got "
                                          f"{type(item).__name__})")
                                break
                    elif not isinstance(mv, str):
                        err(path, f"'metadata.{mk}' must be a scalar or a "
                                  f"list of scalars (got "
                                  f"{type(mv).__name__})")

        # allowed-tools — if present, MUST be a space-separated string,
        # NOT a list. Spec § Frontmatter is explicit on this. The block
        # parser yields a list for the YAML block-list shape; for the
        # YAML flow-list shape (`[Read, Grep]`) the parser yields the
        # literal `'[Read, Grep]'` string, which the second branch
        # catches — both list shapes are spec violations.
        if "allowed-tools" in fields:
            tools = fields["allowed-tools"]
            if isinstance(tools, list):
                # The parser produces [] for `allowed-tools: []` and a
                # populated list for block-style; either is wrong shape.
                shape = "an empty YAML flow list" if tools == [] else "a YAML block list"
                err(path, f"'allowed-tools' must be a space-separated string, "
                          f"not {shape}")
            elif not isinstance(tools, str) or not tools:
                err(path, "'allowed-tools' must be a space-separated string "
                          "when present")
            elif tools.startswith("[") and tools.endswith("]"):
                err(path, "'allowed-tools' must be a space-separated string, "
                          "not a YAML flow-style list")

    def check_body(path: pathlib.Path, body: str, body_start_line: int) -> None:
        body_lines = body.splitlines()
        n = len(body_lines)
        if n > 1000:
            err(path, f"body exceeds 1000 lines (got {n}); the spec "
                      f"recommends keeping SKILL.md under 500 lines")
        elif n > 500:
            warn(path, f"body exceeds 500 lines (got {n}); the spec "
                       f"recommends staying under 500")

        for offset, line in enumerate(body_lines):
            line_no = body_start_line + offset
            abs_match = RE_ABS_PATH.search(line)
            if abs_match:
                err(path, f"absolute system path in body: "
                          f"{abs_match.group(0)!r}", line=line_no)
            for install in RE_INSTALL_PATH.finditer(line):
                hit = install.group(1)
                err(path, f"install-path reference in body: {hit!r} "
                          f"— skill bodies must use skill-relative paths for "
                          f"own files and name-only references for other "
                          f"skills", line=line_no)
            # Don't double-warn on deep same-skill paths if the install
            # match already fired on this line.
            if not RE_INSTALL_PATH.search(line):
                for deep in RE_DEEP_SAME_SKILL.finditer(line):
                    hit = deep.group(1)
                    warn(path, f"same-skill file reference deeper than one "
                               f"level: {hit!r} (spec recommends ≤1 level)",
                         line=line_no)

    def check_layout(skill_dir: pathlib.Path, path: pathlib.Path) -> None:
        for child in sorted(skill_dir.iterdir()):
            if child.is_dir():
                if child.name in IGNORED_DEV_DIRS:
                    continue
                if child.name not in BLESSED_SUBDIRS:
                    warn(path, f"non-blessed top-level subdirectory: "
                               f"{child.name!r} (spec recommends "
                               f"{sorted(BLESSED_SUBDIRS)} as the canonical "
                               f"layout)")
            else:
                if child.name == "SKILL.md":
                    continue
                info(path, f"loose file at skill root: {child.name!r} "
                           f"(allowed by spec; logged for visibility)")

    def check_evals(skill_dir: pathlib.Path, path: pathlib.Path,
                    skill_name: str | None) -> None:
        evals_dir = skill_dir / "evals"
        if not evals_dir.exists() or not evals_dir.is_dir():
            return
        evals_json = evals_dir / "evals.json"
        if not evals_json.exists():
            err(path, "evals/ directory present but evals/evals.json is missing")
            return
        try:
            data = json.loads(evals_json.read_text())
        except json.JSONDecodeError as exc:
            err(evals_json, f"evals/evals.json is not valid JSON: {exc}")
            return
        if not isinstance(data, dict):
            err(evals_json, "evals/evals.json must be a JSON object at top level")
            return
        sn = data.get("skill_name")
        if not isinstance(sn, str) or not sn:
            err(evals_json, "evals.json 'skill_name' must be a non-empty string")
        elif skill_name and sn != skill_name:
            err(evals_json, f"evals.json skill_name {sn!r} does not match "
                            f"skill name {skill_name!r}")
        evals_list = data.get("evals")
        if not isinstance(evals_list, list):
            err(evals_json, "evals.json 'evals' must be a list")
            return
        seen_ids: set = set()
        for idx, entry in enumerate(evals_list):
            if not isinstance(entry, dict):
                err(evals_json, f"evals[{idx}] must be an object")
                continue
            eid = entry.get("id")
            # `bool` is a subclass of `int` in Python — a literal
            # `"id": true` would otherwise pass the type gate. Reject
            # explicitly so the type-check matches author intent.
            if not isinstance(eid, (int, str)) or isinstance(eid, bool):
                err(evals_json, f"evals[{idx}].id must be int or str "
                                f"(got {type(eid).__name__})")
            elif eid in seen_ids:
                err(evals_json, f"evals[{idx}] duplicate id {eid!r} "
                                f"— ids must be unique within evals.json")
            else:
                seen_ids.add(eid)
            prompt = entry.get("prompt")
            if not isinstance(prompt, str) or not prompt:
                err(evals_json, f"evals[{idx}].prompt must be a non-empty string")
            expected = entry.get("expected_output")
            if not isinstance(expected, str) or not expected:
                err(evals_json, f"evals[{idx}].expected_output must be a "
                                f"non-empty string")
            files = entry.get("files")
            if files is not None:
                if not isinstance(files, list):
                    err(evals_json, f"evals[{idx}].files must be a list")
                else:
                    skill_dir_resolved = skill_dir.resolve()
                    for fpath in files:
                        if not isinstance(fpath, str) or not fpath:
                            err(evals_json, f"evals[{idx}].files entry must "
                                            f"be a non-empty string")
                            continue
                        resolved = (skill_dir / fpath).resolve()
                        # Path-traversal guard: an entry like
                        # `../../some-other-skill/x` must not escape the
                        # skill dir even if the target happens to exist.
                        try:
                            resolved.relative_to(skill_dir_resolved)
                        except ValueError:
                            err(evals_json, f"evals[{idx}].files entry "
                                            f"{fpath!r} resolves outside "
                                            f"the skill directory "
                                            f"({resolved})")
                            continue
                        if not resolved.exists():
                            err(evals_json, f"evals[{idx}].files entry "
                                            f"{fpath!r} does not exist "
                                            f"(resolved to {resolved})")
            asserts = entry.get("assertions")
            if asserts is not None:
                if not isinstance(asserts, list):
                    err(evals_json, f"evals[{idx}].assertions must be a list")
                else:
                    for ai, a in enumerate(asserts):
                        if not isinstance(a, str) or not a:
                            err(evals_json, f"evals[{idx}].assertions[{ai}] "
                                            f"must be a non-empty string")

    def check_skill(path: pathlib.Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            err(path, ferr)
            return
        if fields is None:
            err(path, "missing YAML frontmatter (--- ... ---)")
            return
        check_frontmatter(path, fields)
        if not body.strip():
            err(path, "body is empty")
        check_body(path, body, body_start)
        check_layout(path.parent, path)
        check_evals(path.parent, path, fields.get("name"))

    # ── Walk both roots ───────────────────────────────────────────────────
    walk_roots: list[pathlib.Path] = []
    projection = root / ".claude" / "skills"
    if projection.exists():
        walk_roots.append(projection)
    packs_root = root / "packs"
    if packs_root.exists():
        walk_roots.extend(sorted(packs_root.glob("*/.apm/skills")))

    skill_count = 0
    for walk in walk_roots:
        for skill_md in sorted(walk.glob("*/SKILL.md")):
            skill_count += 1
            before_err = error_count
            before_warn = warn_count
            try:
                check_skill(skill_md)
            except (OSError, RuntimeError) as exc:
                # Symlink loops, permission denials, vanished files
                # between glob and check — surface as an error against
                # the offending skill rather than killing the whole walk.
                # RuntimeError covers Python 3.12+'s `pathlib.resolve()`
                # error class for symlink loops (older Pythons raise
                # OSError for the same condition).
                err(skill_md, f"could not read skill: {exc}")
            if error_count == before_err and warn_count == before_warn:
                ok(f"{relpath(skill_md)}")

    print()
    print(f"Skills checked: {skill_count} "
          f"({error_count} error(s), {warn_count} warning(s)).")
    if error_count:
        print()
        print(f"Skill-spec lint: failed ({error_count} error(s)).")
        return 1
    print("Skill-spec lint: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
