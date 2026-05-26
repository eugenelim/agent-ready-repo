"""Markdown → TOML serialiser for the codex `agent` projection.

The codex CLI consumes subagents declared in TOML at
``.codex/agents/<name>.toml`` (per https://developers.openai.com/codex/subagents).
Source format in a pack is the same as every other agent primitive —
``.apm/agents/<name>.md`` with YAML-style frontmatter + a markdown body.
This module emits the equivalent TOML.

Field mapping (driven by the contract's
``[frontmatter-mapping."codex-agent-frontmatter-v0.8"]`` per-key
sub-tables):

  - YAML ``name`` → TOML ``name``
  - YAML ``description`` → TOML ``description``
  - markdown body → TOML ``developer_instructions`` (mode-level
    convention; **not** a frontmatter rename, because the body isn't a
    frontmatter field). Empty body → empty string.
  - Unmapped YAML fields (``tools``, ``model``, …) drop silently —
    codex TOML agents have no equivalent slot.

TOML emission shape: each output field is emitted as ``<key> = <value>``.
``name`` / ``description`` use TOML basic strings (``"..."``);
``developer_instructions`` uses a multi-line basic string
(``\"\"\"..."\"\"\"``) so newlines render literally and reviewers reading
the file see the agent's prose, not an escape-laden one-liner. Backslashes
and double-quotes inside the body are escaped, and the leading-newline
trim rule (``\"\"\"\\n<body>...`` keeps the first body line on its own row
so the parsed value starts with the body's first character, byte-for-byte).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Frontmatter split / parse (mirrors kiro.py:_split_frontmatter +
# _parse_frontmatter without reaching across module boundaries; the cross-
# module duplication is acknowledged in docs/specs/dropped-primitives-
# coverage spec § Always do — sibling-projection-mode rules duplicate
# rather than depend on each other's privates).
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
# TOML emission
# ---------------------------------------------------------------------------


def _emit_basic_string(value: str) -> str:
    """TOML 1.0 basic-string literal (with surrounding quotes).

    Same shape as ``agentbundle.config._emit_basic_string`` — duplicated
    here to keep ``build.projections`` independent of the CLI-side
    config module.
    """
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

    Returns the ``\"\"\"...\"\"\"`` form with:
      - backslashes escaped (``\\\\``)
      - double-quotes escaped (``\\\"``) — over-eager but correct, avoids
        the ``\"\"\"``-termination ambiguity
      - control chars except ``\\n`` / ``\\t`` / ``\\r`` rendered as
        ``\\uXXXX``
      - a leading ``\\n`` after the opening ``\"\"\"`` so the parsed value
        starts at the body's first character (TOML's leading-newline
        trim rule).
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
# Mapping application
# ---------------------------------------------------------------------------


def _apply_mapping(
    frontmatter: dict[str, Any], mapping: dict[str, Any]
) -> dict[str, str]:
    """Apply the frontmatter-mapping rename rules; drop unmapped keys.

    The codex contract maps ``name``/``description`` straight through
    (no rename). Pack authors writing claude-code-style frontmatter
    (``name``, ``description``, optional ``tools``, ``model``, …) get
    their first two fields propagated; the rest drop silently — codex
    TOML agents have no equivalent slot.

    Returned values are coerced to ``str`` so the TOML emitter doesn't
    have to handle lists or dicts at this surface (the codex agent
    schema is flat: ``name``, ``description``, ``developer_instructions``).
    Lists collapse to a comma-joined string for backward compatibility
    with packs that ship ``description: [foo, bar]``; that's a degenerate
    case rather than a supported shape.
    """
    rewritten: dict[str, str] = {}
    for source_key, rule in mapping.items():
        if source_key not in frontmatter:
            continue
        new_key = rule.get("rename", source_key)
        value = frontmatter[source_key]
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        rewritten[new_key] = str(value)
    return rewritten


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def project_codex_agent_toml(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    frontmatter_mapping: dict[str, Any],
) -> None:
    """Project ``<source_dir>/<name>.md`` → ``<output>/<target>/<name>.toml``.

    Iterates ``*.md`` files in sorted order. For each:
      1. Split YAML frontmatter from markdown body.
      2. Apply ``frontmatter_mapping`` rename rules; drop unmapped keys.
      3. Emit a TOML file whose keys are the mapped frontmatter (basic
         strings) plus ``developer_instructions`` (multi-line basic
         string) carrying the body verbatim.

    Empty body → ``developer_instructions = \"\"`` (empty basic string,
    not missing).
    """
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".md"):
            continue
        frontmatter, body = _split_frontmatter(
            entry.read_text(encoding="utf-8")
        )
        rewritten = _apply_mapping(frontmatter, frontmatter_mapping)
        toml_lines: list[str] = []
        for key in sorted(rewritten.keys()):
            toml_lines.append(f"{key} = {_emit_basic_string(rewritten[key])}")
        if body:
            toml_lines.append(
                f"developer_instructions = {_emit_multiline_basic_string(body)}"
            )
        else:
            toml_lines.append('developer_instructions = ""')
        destination = target_dir / (entry.stem + ".toml")
        destination.write_text("\n".join(toml_lines) + "\n", encoding="utf-8")
