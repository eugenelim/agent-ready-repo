"""Markdown → ``.agent.md`` serialiser for the copilot ``agent`` projection.

GitHub Copilot (app + CLI, verified 1.0.59) discovers custom agents from
``.github/agents/<name>.agent.md`` (repo scope) and
``~/.copilot/agents/<name>.agent.md`` (user scope). The on-disk shape is the
same Claude-style markdown as every other agent primitive — YAML frontmatter
plus a markdown body that becomes the agent's instructions — so this module's
job is narrow: filter and validate the frontmatter, then re-emit.

Field handling (driven by the contract's
``[frontmatter-mapping."copilot-agent-frontmatter-v0.10"]`` per-key
sub-tables for ``name`` / ``description``):

  - YAML ``name`` → ``name`` (identity rename)
  - YAML ``description`` → ``description`` (identity rename)
  - YAML ``tools`` → emitted **verbatim** after allow-list validation. The
    ``.agent.md`` parser accepts the Claude comma-separated format and
    resolves the names itself (``Read``→``view``, ``Grep``→``grep``,
    ``Glob``→``glob``); we keep the source string rather than rewrite it.
  - YAML ``model`` → **dropped**. The CLI ignores ``model`` and our values
    (``opus``/``sonnet``) are not Copilot model ids (copilot-cli#2133/#1195).
  - ``target`` → **never emitted**; Copilot defaults to both ``vscode`` and
    ``github-copilot``.
  - markdown body → the agent's instructions, byte-for-byte.

Tool allow-list (fail-closed): ``tools`` tokens are validated against the set
of names known to be accepted by Copilot custom agents. ``WebFetch`` /
``WebSearch`` pass through and Copilot resolves both to its ``web`` tool — the
official custom-agents reference documents ``web`` with aliases ``WebSearch`` /
``WebFetch`` on the CLI + app (the only non-coverage is the Copilot *cloud
agent*, which we serve only via repo ``.github/``). So ``research``'s retrieval
subagents keep live web access on Copilot CLI/app; they are **not** degraded
there. (RFC-0024 § Errata E1 / docs/specs/copilot-skills-and-web corrected the
earlier "no web tool" finding, which a confounded 1.0.59 probe produced.) A
token in no set raises ``ValueError`` rather than passing through to be
silently ignored by Copilot — which would drop a needed capability invisibly.
This is a deliberately stricter policy than codex's drop-on-unmapped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# Tool names Copilot custom agents are known to accept (verified 1.0.59),
# including the web tools `WebFetch`/`WebSearch` which Copilot resolves to its
# `web` tool on the CLI + app (see module docstring). A `tools` token outside
# this set fails the build.
_KNOWN_TOOLS: frozenset[str] = frozenset(
    {
        "Read",
        "Grep",
        "Glob",
        "Edit",
        "Write",
        "MultiEdit",
        "Bash",
        "WebFetch",
        "WebSearch",
    }
)


# ---------------------------------------------------------------------------
# Frontmatter split / parse (mirrors copilot.py / codex_agent_toml.py without
# reaching across module boundaries; the cross-module duplication is the
# acknowledged sibling-projection convention — see docs/specs/copilot-full-
# parity § Always do).
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
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


def _parse_frontmatter(lines: list[str]) -> dict[str, str]:
    """Parse ``key: value`` frontmatter, preserving the raw value.

    Surrounding quotes are *not* stripped — the source is Claude-format
    (unquoted) and Copilot's parser accepts that format, so the highest
    fidelity is to re-emit the value exactly as authored. Blank lines and
    ``#`` comments are skipped.
    """
    result: dict[str, str] = {}
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        result[key.strip()] = value.strip()
    return result


# ---------------------------------------------------------------------------
# Mapping + tool validation
# ---------------------------------------------------------------------------


def _apply_mapping(
    frontmatter: dict[str, str], mapping: dict[str, Any]
) -> dict[str, str]:
    """Apply the frontmatter-mapping rename rules; drop unmapped keys.

    The copilot mapping carries ``name`` / ``description`` (identity
    renames). ``model`` is absent from the mapping, so it drops here.
    ``tools`` is handled separately by the caller (allow-list pass-through),
    not via a rename rule.
    """
    rewritten: dict[str, str] = {}
    for source_key, rule in mapping.items():
        if source_key not in frontmatter:
            continue
        new_key = rule.get("rename", source_key)
        rewritten[new_key] = frontmatter[source_key]
    return rewritten


def _validate_tools(tools_value: str) -> None:
    """Raise ``ValueError`` if any token is outside ``_KNOWN_TOOLS``, or if a
    declared ``tools`` field yields **no** tokens.

    Fail-closed on two arms:
      - an unknown token would be silently ignored by Copilot, dropping a
        capability invisibly; and
      - a declared-but-empty ``tools`` (a bare ``tools:`` line, or the YAML
        list form ``tools:\\n  - Read`` which this line-based parser reads as
        empty) would emit a bare ``tools:`` line — and in Copilot an empty /
        omitted ``tools`` grants **all** tools, silently widening a read-only
        agent. Both fail the build rather than ship a silent widening.
    """
    tokens = [t.strip() for t in tools_value.split(",") if t.strip()]
    if not tokens:
        raise ValueError(
            "copilot-agent-md: agent declares a `tools` field that resolves to "
            "no tokens (a bare `tools:` line, or the YAML list form which is "
            "unsupported here — use the Claude comma form `tools: Read, Grep`). "
            "Refusing to emit a `.agent.md` with an empty `tools` line, which "
            "Copilot reads as 'all tools' (silent permission widening)"
        )
    for token in tokens:
        if token not in _KNOWN_TOOLS:
            raise ValueError(
                f"copilot-agent-md: tool token {token!r} is not in the "
                f"Copilot custom-agent allow-list "
                f"({', '.join(sorted(_KNOWN_TOOLS))}); refusing to emit a "
                f"`.agent.md` that silently drops it"
            )


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def _emit(frontmatter: dict[str, str], body: str) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---\n")
    return "\n".join(lines) + body


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def project_copilot_agent_md(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    frontmatter_mapping: dict[str, Any],
) -> None:
    """Project ``<source_dir>/<name>.md`` → ``<output>/<target>/<name>.agent.md``.

    Iterates ``*.md`` files in sorted order. For each:
      1. Split YAML frontmatter from markdown body.
      2. Apply the rename rules (``name`` / ``description``); ``model`` drops.
      3. Validate ``tools`` against the allow-list (fail-closed) and emit it
         verbatim; ``target`` is never emitted.
      4. Emit frontmatter + body to ``<name>.agent.md``.
    """
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".md"):
            continue
        frontmatter, body = _split_frontmatter(
            entry.read_text(encoding="utf-8")
        )
        emitted = _apply_mapping(frontmatter, frontmatter_mapping)
        if "tools" in frontmatter:
            _validate_tools(frontmatter["tools"])
            emitted["tools"] = frontmatter["tools"]
        destination = target_dir / (entry.stem + ".agent.md")
        destination.write_text(_emit(emitted, body), encoding="utf-8", newline="\n")
