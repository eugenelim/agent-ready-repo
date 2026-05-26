#!/usr/bin/env python3
"""Lints the agent artifacts under .claude/ — skills, subagents, commands.
Companion to tools/lint-agents-md.py, which handles docs structure and
AGENTS.md hygiene. Exit non-zero if any check fails.

Checks (per artifact type):
  Skills (.claude/skills/<name>/SKILL.md):
    - File exists, has valid YAML frontmatter delimited by ---
    - Frontmatter has non-empty `name` (kebab-case) and `description`
    - Directory name == frontmatter `name`
    - Frontmatter has no unknown top-level keys (allowed: the
      agentskills.io spec set — name, description, license,
      compatibility, metadata, allowed-tools). Project-specific
      data (e.g. credentialed-skill flags) lives nested under
      `metadata:` per the spec's escape hatch.

  Subagents (.claude/agents/<name>.md):
    - File has valid YAML frontmatter
    - Frontmatter has non-empty `name` (kebab-case), `description`,
      and `model` (see docs/CONVENTIONS.md#model-selection)
    - Filename (sans .md) == frontmatter `name`
    - Frontmatter has no unknown keys (allowed: name, description,
      tools, model)

  Commands (.claude/commands/<name>.md):
    - File has valid YAML frontmatter (optional but if present,
      enforce shape)
    - Frontmatter, if present, has non-empty `description`
    - Frontmatter has no unknown keys (allowed: description,
      allowed-tools, model, argument-hint)
    - Body (after frontmatter) is non-empty

  All of the above:
    - Internal markdown links resolve (relative paths, no anchors-only).

A fixture mode is supported for self-testing:
  LINT_ROOT=tools/fixtures/<dir> python3 tools/lint-agent-artifacts.py
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

try:
    import yaml
except ImportError as exc:  # pragma: no cover — env-setup failure path
    print(
        "✖ This linter requires PyYAML. Install with: "
        "pip install -r tools/requirements.txt "
        "(or `pip install 'pyyaml>=6.0'` if you're not in the repo root).",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


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


KEBAB = re.compile(r"^[a-z][a-z0-9-]*$")
LINK = re.compile(r"\]\(([^)]+)\)")


class _DuplicateKeyError(Exception):
    """Raised by the custom YAML mapping constructor on a duplicate key.

    PyYAML's stock SafeLoader silently keeps the last value when a mapping
    has duplicate keys; the spec contract here is that duplicates are an
    error. Carry the offending key and its 1-indexed file line so the
    caller can format a faithful message.
    """

    def __init__(self, key: object, line: int) -> None:
        self.key = key
        self.line = line


class _FrontmatterLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys.

    Subclass rather than monkey-patch so `yaml.SafeLoader`'s global
    constructor table stays untouched.
    """


def _construct_mapping_no_dups(loader, node, deep=False):
    if not isinstance(node, yaml.MappingNode):
        raise yaml.constructor.ConstructorError(
            None, None,
            f"expected a mapping node, got {node.id}",
            node.start_mark,
        )
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise _DuplicateKeyError(key, key_node.start_mark.line + 1)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_FrontmatterLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_dups,
)

# Top-level SKILL.md frontmatter keys — the agentskills.io spec set
# (https://agentskills.io/specification). `metadata:` is the spec's own
# escape hatch for project-specific data (arbitrary k/v). Credentialed-
# skill flags (`credentialed`, `primitive-class`) live nested under
# `metadata:`; see check_skill.
ALLOWED_SKILL_KEYS = {"name", "description", "license", "compatibility",
                      "metadata", "allowed-tools"}
ALLOWED_PRIMITIVE_CLASSES = {"credentialed-cli", "mcp-server"}
# The four broker ids per RFC-0013 § 1. The set is closed in v1; adding
# a fifth broker is a contract change (see docs/specs/credential-broker-
# contract/spec.md "Ask first" in Boundaries). Order in the refusal
# message is fixed for the pinned-message assertion.
ALLOWED_AUTH_BROKERS = ("env", "cli", "creds", "sso-cookie")
ALLOWED_AGENT_KEYS = {"name", "description", "tools", "model"}
ALLOWED_COMMAND_KEYS = {"description", "allowed-tools", "model", "argument-hint"}


def main() -> int:
    os.chdir(_repo_root())
    root = pathlib.Path(os.environ.get("LINT_ROOT", ".")).resolve()
    error_count = 0

    def relpath(path) -> pathlib.Path:
        p = pathlib.Path(path)
        if not p.is_absolute():
            return p
        try:
            return p.resolve().relative_to(root)
        except ValueError:
            return p

    def err(path, msg: str, line=None) -> None:
        nonlocal error_count
        rel = relpath(path)
        loc = f"{rel}:{line}" if line else str(rel)
        print(f"✖ {loc}: {msg}", file=sys.stderr)
        error_count += 1

    def ok(msg: str) -> None:
        print(f"✓ {msg}")

    def warn(msg: str) -> None:
        print(f"⚠ {msg}", file=sys.stderr)

    def parse_frontmatter(path: pathlib.Path):
        """Return (fields, body_start_line, body, error).

        Frontmatter between the two ``---`` delimiters is parsed with
        PyYAML's ``safe_load`` via a duplicate-rejecting Loader. Nested
        mappings, block-list and flow-list sequences, block scalars
        (``|``, ``>``), and arbitrary depth are all handled by PyYAML
        itself — this function only owns delimiter discovery and the
        error-message shapes the linters and their self-tests depend on.
        """
        text = path.read_text(encoding="utf-8")
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
        fm_text = "\n".join(lines[1:end])
        body_start_line = end + 2
        body = "\n".join(lines[end + 1:])
        try:
            fields = yaml.load(fm_text, Loader=_FrontmatterLoader)
        except _DuplicateKeyError as exc:
            # exc.line is 0-indexed within fm_text (mark.line + 1); the
            # frontmatter starts at file line 2 (line 1 is the opening
            # delimiter), so add 1 to translate to a 1-indexed file line.
            return None, 0, text, (
                f"duplicate frontmatter key {exc.key!r} (line {exc.line + 1})"
            )
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            problem = getattr(exc, "problem", None) or str(exc)
            if mark is not None:
                # Translate YAML's 0-indexed line within the frontmatter
                # chunk to a 1-indexed file line. Same +2 used above.
                return None, 0, text, (
                    f"malformed frontmatter (line {mark.line + 2}): {problem}"
                )
            return None, 0, text, f"malformed frontmatter: {problem}"
        if fields is None:
            fields = {}
        if not isinstance(fields, dict):
            return None, 0, text, (
                "frontmatter must be a mapping at the top level "
                f"(got {type(fields).__name__})"
            )
        return fields, body_start_line, body, None

    def check_links(path: pathlib.Path, body: str, body_start_line: int) -> None:
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

    def check_skill(path: pathlib.Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            err(path, ferr)
            return
        if fields is None:
            err(path, "missing YAML frontmatter (--- ... ---)")
            return
        name = fields.get("name")
        if name is None or name == "":
            err(path, "frontmatter missing required key: name")
        elif not isinstance(name, str):
            # PyYAML follows YAML 1.1, which maps unquoted ``yes``/``no``/
            # ``on``/``off``/``true``/``false`` (any case) to booleans —
            # the Norway problem. Surface a clear message before the
            # kebab-regex below, which would otherwise raise TypeError.
            err(path, f"frontmatter key 'name' must be a string "
                      f"(got {type(name).__name__}) — quote "
                      f"Norway-style scalars like 'yes' / 'no' / 'on' / "
                      f"'off' to keep them as text")
        elif not KEBAB.match(name):
            err(path, f"name {name!r} must be kebab-case ([a-z][a-z0-9-]*)")
        elif name != path.parent.name:
            err(path, f"name {name!r} does not match directory "
                      f"{path.parent.name!r}")
        desc = fields.get("description")
        if desc is None or desc == "":
            # Both `description:` (no value → None) and `description: ""`
            # are treated as the key being effectively missing — same
            # diagnostic the prior parser produced.
            err(path, "frontmatter missing required key: description")
        elif not isinstance(desc, str):
            err(path, f"frontmatter key 'description' must be a string "
                      f"(got {type(desc).__name__}) — "
                      f"quote Norway-style scalars like 'yes' / 'no'")
        unknown = set(fields) - ALLOWED_SKILL_KEYS
        if unknown:
            err(path, f"unknown frontmatter keys: {sorted(unknown)} "
                      f"(allowed: {sorted(ALLOWED_SKILL_KEYS)})")
        # Credentialed-skill frontmatter keys (per skill-secrets spec § AC25).
        # `credentialed` and `primitive-class` are project-specific data; per
        # the agentskills.io spec they live under the `metadata:` escape
        # hatch rather than at top level. Absence of `credentialed` (or of
        # `metadata` entirely) means the skill is not credentialed; the
        # lint skips the credentialed-specific checks. When present, the
        # value must be a YAML boolean — PyYAML follows YAML 1.1 and
        # converts any boolean spelling (true / True / TRUE / yes / on / y
        # and their negatives) to a Python bool, so the ``is True`` /
        # ``is False`` identity check accepts them all and rejects any
        # quoted form (which arrives as a str).
        metadata = fields.get("metadata")
        # `metadata:` with no value parses to ``None``; the rare
        # ``metadata: ""`` form parses to the empty string. Treat both as
        # "no project-specific data" rather than a type error. Anything
        # else non-dict (list, non-empty scalar) is malformed.
        if metadata is not None and metadata != "" and not isinstance(
                metadata, dict):
            err(path, f"frontmatter key 'metadata' must be a nested "
                      f"mapping (got {type(metadata).__name__})")
            metadata = None
        meta = metadata if isinstance(metadata, dict) else {}
        if "credentialed" in meta:
            cval = meta["credentialed"]
            # ``is True``/``is False`` rather than ``in (True, False)`` so
            # that ``1`` and ``0`` (which compare equal to the bool
            # singletons) don't slip through. Quoted strings such as
            # ``"true"`` and ``"yes"`` arrive as str and are rejected.
            if cval is not True and cval is not False:
                err(path, f"frontmatter key 'metadata.credentialed' must "
                          f"be boolean (true|false), got {cval!r}")
        if "primitive-class" in meta:
            pval = meta["primitive-class"]
            if pval not in ALLOWED_PRIMITIVE_CLASSES:
                err(path, f"frontmatter key 'metadata.primitive-class' "
                          f"must be one of: "
                          f"{', '.join(sorted(ALLOWED_PRIMITIVE_CLASSES))} "
                          f"(got {pval!r})")
        # `metadata.auth` declares the credential broker (RFC-0013 § 1).
        # The four ids are enumerated as a closed set in v1; unknown
        # values are refused with a pinned message that names the
        # acceptable set so the author can self-correct. The refusal
        # message ordering matches ALLOWED_AUTH_BROKERS verbatim — tests
        # assert against this exact string.
        auth_present = "auth" in meta
        if auth_present:
            aval = meta["auth"]
            if aval not in ALLOWED_AUTH_BROKERS:
                err(path, f"frontmatter key 'metadata.auth' must be one of "
                          f"{{{', '.join(ALLOWED_AUTH_BROKERS)}}}; "
                          f"got {aval!r}")
        # `metadata.credentialed: true` requires `metadata.auth` — the
        # broker dispatch shape is not optional for credentialed skills.
        # `credentialed: false` (or absent) skips the requirement so
        # non-credentialed skills aren't forced to declare a broker.
        if meta.get("credentialed") is True and not auth_present:
            err(path, "frontmatter key 'metadata.auth' is required when "
                      "metadata.credentialed: true "
                      f"(declare one of {{{', '.join(ALLOWED_AUTH_BROKERS)}}})")
        if not body.strip():
            err(path, "body is empty")
        check_links(path, body, body_start)

    def check_agent(path: pathlib.Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            err(path, ferr)
            return
        if fields is None:
            err(path, "missing YAML frontmatter (--- ... ---)")
            return
        expected_name = path.stem
        name = fields.get("name")
        if name is None or name == "":
            err(path, "frontmatter missing required key: name")
        elif not isinstance(name, str):
            # See the matching note in check_skill — YAML 1.1 Norway
            # scalars become booleans before this check sees them.
            err(path, f"frontmatter key 'name' must be a string "
                      f"(got {type(name).__name__}) — quote "
                      f"Norway-style scalars like 'yes' / 'no' / 'on' / "
                      f"'off' to keep them as text")
        elif not KEBAB.match(name):
            err(path, f"name {name!r} must be kebab-case ([a-z][a-z0-9-]*)")
        elif name != expected_name:
            err(path, f"name {name!r} does not match filename "
                      f"{expected_name!r}")
        desc = fields.get("description")
        if desc is None or desc == "":
            err(path, "frontmatter missing required key: description")
        elif not isinstance(desc, str):
            err(path, f"frontmatter key 'description' must be a string "
                      f"(got {type(desc).__name__}) — "
                      f"quote Norway-style scalars like 'yes' / 'no'")
        model = fields.get("model")
        if model is None or model == "":
            err(path, "frontmatter missing required key: model "
                      "(see docs/CONVENTIONS.md#model-selection)")
        elif not isinstance(model, str):
            err(path, f"frontmatter key 'model' must be a string "
                      f"(got {type(model).__name__}) — "
                      f"quote Norway-style scalars like 'on' / 'off'")
        unknown = set(fields) - ALLOWED_AGENT_KEYS
        if unknown:
            err(path, f"unknown frontmatter keys: {sorted(unknown)} "
                      f"(allowed: {sorted(ALLOWED_AGENT_KEYS)})")
        if not body.strip():
            err(path, "body is empty")
        check_links(path, body, body_start)

    def check_command(path: pathlib.Path) -> None:
        fields, body_start, body, ferr = parse_frontmatter(path)
        if ferr:
            err(path, ferr)
            return
        if fields is not None:
            desc = fields.get("description")
            if desc is None or desc == "":
                err(path, "frontmatter missing required key: description")
            elif not isinstance(desc, str):
                err(path, f"frontmatter key 'description' must be a string "
                          f"(got {type(desc).__name__}) — "
                          f"quote Norway-style scalars like 'yes' / 'no'")
            unknown = set(fields) - ALLOWED_COMMAND_KEYS
            if unknown:
                err(path, f"unknown frontmatter keys: {sorted(unknown)} "
                          f"(allowed: {sorted(ALLOWED_COMMAND_KEYS)})")
        if not body.strip():
            err(path, "body is empty")
        check_links(path, body, body_start)

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
        # Flag stray non-SKILL.md files at the skill level (typos like skill.md).
        for stray in sorted(skills_dir.glob("*/*.md")):
            if stray.name != "SKILL.md":
                err(
                    stray.relative_to(root),
                    "unexpected file in skill dir; skill bodies must be named SKILL.md",
                )
        # Flag skill dirs with no SKILL.md.
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            if not (skill_dir / "SKILL.md").exists():
                err(
                    skill_dir.relative_to(root),
                    "skill directory missing SKILL.md",
                )

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
    print(
        f"Artifacts checked: {skill_count} skill(s), "
        f"{agent_count} subagent(s), {command_count} command(s)."
    )

    if error_count:
        print()
        print(f"Agent-artifact lint: failed ({error_count} error(s)).")
        return 1

    print("Agent-artifact lint: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
