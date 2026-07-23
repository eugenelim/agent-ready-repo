"""Markdown → TOML serialiser for the gemini ``command`` projection
(``gemini-command-toml`` mode).

Gemini CLI custom commands are TOML files under ``.gemini/commands/`` — a file at
``.gemini/commands/git/commit.toml`` is invoked as ``/git:commit`` (the directory
structure *is* Gemini's ``:`` namespace, so subdirectories are preserved verbatim).
Source in a pack is the same Markdown shape every other primitive uses —
``.apm/commands/<...>/<name>.md`` with YAML-style frontmatter + a markdown body.
This module emits the equivalent TOML
(https://google-gemini.github.io/gemini-cli/docs/cli/custom-commands.html):

  - frontmatter ``description`` → TOML ``description`` (a TOML basic string).
    **Omitted** when the source has no ``description`` — Gemini auto-generates one.
  - markdown body → TOML ``prompt`` (a multi-line basic string, so the agent's
    prose renders literally), with Claude Code's ``$ARGUMENTS`` injection token
    rewritten to Gemini's ``{{args}}``.

**Fail-closed (spec AC7).** ``{{args}}`` is Gemini's *only* argument-injection
form — it injects the full argument string. A source body using **positional**
arguments (``$1``, ``$2``, …) needs an expressiveness ``{{args}}`` cannot provide,
so this projection **raises** ``ValueError`` rather than emitting a
silently-degraded command. (The install handler's ``except (FileNotFoundError,
ValueError)`` turns this into a clean refusal, not a traceback.)

**Known constraint (the check is body-wide, not injection-context-aware).** The
positional-arg guard matches ``$<digit>`` *anywhere* in the body, so a literal
dollar-amount in prose or a fenced shell example (``$10/month``, or a ``$1``
inside a fenced code block) trips it too. This is **fail-closed** (a loud build
error an author can act on, never a silent bad emit), and no shipped command
contains a ``$<digit>``. An injection-context-aware parser (skip fenced/inline code, require
an injection-shaped token) is a documented follow-on — see ``workspace.toml [backlog]``
slug ``gemini-full-parity``. Until then: keep literal ``$<digit>`` out of command
bodies, or the build will refuse the command.

The one-source-file → one-output-file shape and the frontmatter helpers mirror
``codex-agent-toml``; per the sibling-projection convention these helpers are
duplicated here rather than reaching across module privates.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

# Claude Code's positional-argument tokens (`$1`, `$2`, …). Gemini's `{{args}}`
# injects the whole argument string and has no positional form, so a source
# command using these fails the build (AC7). `$ARGUMENTS` (the whole-string form)
# is the one we *can* translate and is excluded from this pattern.
_POSITIONAL_ARG = re.compile(r"\$\d+")
_CLAUDE_ALL_ARGS = "$ARGUMENTS"
_GEMINI_ALL_ARGS = "{{args}}"


# ---------------------------------------------------------------------------
# Frontmatter split / parse (mirrors codex_agent_toml.py without reaching across
# module boundaries — the sibling-projection-mode duplication convention).
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        return {}, text
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].startswith("---"):
            end_index = index
            break
    if end_index is None:
        return {}, text
    frontmatter_lines = lines[1:end_index]
    body = "".join(lines[end_index + 1 :])
    return _parse_frontmatter(frontmatter_lines), body


def _parse_frontmatter(lines: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
            result[key.strip()] = items
        else:
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key.strip()] = value
    return result


# ---------------------------------------------------------------------------
# TOML emission (mirrors codex_agent_toml.py)
# ---------------------------------------------------------------------------


def _emit_basic_string(value: str) -> str:
    """TOML 1.0 basic-string literal (with surrounding quotes)."""
    chunks: list[str] = ['"']
    for ch in value:
        code = ord(ch)
        if ch == "\\":
            chunks.append("\\\\")
        elif ch == '"':
            chunks.append('\\"')
        elif ch == "\b":
            chunks.append("\\b")
        elif ch == "\t":
            chunks.append("\\t")
        elif ch == "\n":
            chunks.append("\\n")
        elif ch == "\f":
            chunks.append("\\f")
        elif ch == "\r":
            chunks.append("\\r")
        elif code < 0x20 or code == 0x7F:
            chunks.append(f"\\u{code:04X}")
        else:
            chunks.append(ch)
    chunks.append('"')
    return "".join(chunks)


def _emit_multiline_basic_string(value: str) -> str:
    """TOML 1.0 multi-line basic string for the markdown body.

    A leading ``\\n`` after the opening ``\"\"\"`` keeps the body's first
    character on its own row (TOML's leading-newline trim rule), so the parsed
    value is the body byte-for-byte. Backslashes and double-quotes are escaped
    (the latter over-eagerly, to avoid the ``\"\"\"``-termination ambiguity).
    """
    chunks: list[str] = ['"""\n']
    for ch in value:
        code = ord(ch)
        if ch == "\\":
            chunks.append("\\\\")
        elif ch == '"':
            chunks.append('\\"')
        elif ch == "\b":
            chunks.append("\\b")
        elif ch == "\f":
            chunks.append("\\f")
        elif ch in ("\n", "\t", "\r"):
            chunks.append(ch)
        elif code < 0x20 or code == 0x7F:
            chunks.append(f"\\u{code:04X}")
        else:
            chunks.append(ch)
    chunks.append('"""')
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Argument-token translation (fail-closed)
# ---------------------------------------------------------------------------


def _translate_arguments(body: str, source_name: str) -> str:
    """Rewrite Claude ``$ARGUMENTS`` → Gemini ``{{args}}``; fail-closed on
    positional ``$1``/``$2``/… which ``{{args}}`` cannot express."""
    positional = _POSITIONAL_ARG.search(body)
    if positional is not None:
        raise ValueError(
            f"gemini-command-toml: {source_name}: command body uses positional "
            f"argument {positional.group(0)!r}, which Gemini's `{{{{args}}}}` "
            f"injection cannot express; refusing to emit a silently-degraded "
            f"command (only `$ARGUMENTS` is translatable)"
        )
    return body.replace(_CLAUDE_ALL_ARGS, _GEMINI_ALL_ARGS)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def project_gemini_command_toml(
    source_dir: Path,
    output_root: Path,
    rule: dict,
) -> None:
    """Project ``<source_dir>/<...>/<name>.md`` → ``<output>/<target>/<...>/<name>.toml``.

    Walks ``*.md`` files recursively in sorted order, **preserving the
    subdirectory structure** (Gemini's command namespace). For each file:
      1. Split YAML frontmatter from the markdown body.
      2. Translate ``$ARGUMENTS``→``{{args}}`` (raise on positional ``$N``).
      3. Emit a TOML file: ``description`` (basic string, omitted when absent)
         then ``prompt`` (multi-line basic string) carrying the translated body.

    Symlinked source files **and directories** are skipped (defence-in-depth;
    ``lint-packs`` rejects symlink-bearing packs but the install-time caller reads
    a potentially untrusted catalogue and bypasses that gate). The walk uses
    ``os.walk(..., followlinks=False)`` rather than ``Path.rglob`` because rglob
    follows directory symlinks on Python 3.11/3.12 (not 3.13) — a version-conditional
    read-through that would embed an out-of-tree symlink target's bytes into an
    in-jail output file. ``os.walk(followlinks=False)`` behaves identically across
    versions and never traverses a directory symlink.
    """
    target_root = output_root / rule["target-path"].rstrip("/")
    md_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(source_dir, followlinks=False):
        # Prune symlinked subdirectories so the walk never descends through them.
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]
        for filename in filenames:
            entry = Path(dirpath) / filename
            if entry.suffix == ".md" and entry.is_file() and not entry.is_symlink():
                md_files.append(entry)
    for entry in sorted(md_files):
        relative = entry.relative_to(source_dir)
        frontmatter, body = _split_frontmatter(entry.read_text(encoding="utf-8"))
        prompt = _translate_arguments(body, str(relative))

        lines: list[str] = []
        description = frontmatter.get("description")
        if isinstance(description, str) and description.strip():
            lines.append(f"description = {_emit_basic_string(description)}")
        lines.append(f"prompt = {_emit_multiline_basic_string(prompt)}")

        destination = target_root / relative.with_suffix(".toml")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
