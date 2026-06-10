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
  - YAML ``model`` aliases → TOML ``model`` with OpenAI model IDs
  - YAML ``tools`` → documented Codex config fields. Multiple Claude
    tools can imply the same Codex capability; duplicates collapse
    before emission. The projection never emits a generic top-level
    ``tools = [...]`` array.
  - markdown body → TOML ``developer_instructions`` (mode-level
    convention; **not** a frontmatter rename, because the body isn't a
    frontmatter field). Empty body → empty string.
  - Unmapped YAML fields drop silently; unmapped values for mapped
    fields drop with a build-time warning.

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

import sys
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


def _emit_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return _emit_basic_string(str(value))


def _emit_fields(fields: dict[str, Any], developer_instructions: str) -> list[str]:
    """Emit top-level fields first, then nested tables.

    TOML table headers are sticky; `developer_instructions` must be emitted
    before `[features]` / `[tools]` or it would become a member of the last
    table.
    """
    top_level: dict[str, Any] = {}
    tables: dict[str, dict[str, Any]] = {}
    for key, value in fields.items():
        if "." in key:
            table, _, child_key = key.partition(".")
            tables.setdefault(table, {})[child_key] = value
        else:
            top_level[key] = value

    lines: list[str] = []
    for key in sorted(top_level):
        lines.append(f"{key} = {_emit_toml_value(top_level[key])}")
    if developer_instructions:
        lines.append(
            f"developer_instructions = "
            f"{_emit_multiline_basic_string(developer_instructions)}"
        )
    else:
        lines.append('developer_instructions = ""')
    for table in sorted(tables):
        lines.append(f"[{table}]")
        for key in sorted(tables[table]):
            lines.append(f"{key} = {_emit_toml_value(tables[table][key])}")
    return lines


# ---------------------------------------------------------------------------
# Mapping application
# ---------------------------------------------------------------------------


def _apply_mapping(
    frontmatter: dict[str, Any], mapping: dict[str, Any]
) -> dict[str, Any]:
    """Apply the frontmatter-mapping rename / normalize / values rules.

    The codex contract maps ``name``/``description`` straight through
    (no rename). Pack authors writing claude-code-style frontmatter
    (``name``, ``description``, optional ``tools``, ``model``, …) get
    the fields Codex can represent propagated. ``values`` maps source
    aliases to Codex identifiers or intermediate capability intents.
    Unknown values drop with stderr warnings so pack-author typos are
    visible at build time.

    Lists collapse to a comma-joined string for backward compatibility
    unless the rule declares ``normalize = "to-list"``; that rule splits
    comma strings, maps each token, and deduplicates translated values.
    """
    rewritten: dict[str, Any] = {}
    for source_key, rule in mapping.items():
        if source_key not in frontmatter:
            continue
        new_key = rule.get("rename", source_key)
        value = frontmatter[source_key]
        original_value = value
        normalize = rule.get("normalize")
        if normalize == "to-list":
            if isinstance(value, list):
                pass
            elif isinstance(value, str):
                value = [item.strip() for item in value.split(",") if item.strip()]
            else:
                value = [value]
        values_map = rule.get("values")
        if isinstance(values_map, dict):
            if isinstance(value, list) and normalize == "to-list":
                mapped: list[str] = []
                for item in value:
                    if item in values_map:
                        translated = values_map[item]
                        if translated not in mapped:
                            mapped.append(translated)
                    else:
                        print(
                            f"codex: dropping {new_key} entry {item!r} - not in "
                            f"contract values map for source key {source_key!r}",
                            file=sys.stderr,
                        )
                value = mapped
            elif isinstance(value, str) and value in values_map:
                value = values_map[value]
                related_values = rule.get("related-values")
                if isinstance(related_values, dict):
                    for related_key, related_map in related_values.items():
                        if (
                            isinstance(related_key, str)
                            and isinstance(related_map, dict)
                            and original_value in related_map
                        ):
                            rewritten[related_key] = related_map[original_value]
            else:
                print(
                    f"codex: dropping {new_key}={value!r} - not in contract "
                    f"values map for source key {source_key!r}",
                    file=sys.stderr,
                )
                continue
        elif isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        rewritten[new_key] = value
    return rewritten


def _apply_codex_tool_intents(fields: dict[str, Any]) -> dict[str, Any]:
    """Reduce mapped tool intents to documented Codex config keys."""
    rewritten = dict(fields)
    missing = object()
    intents = rewritten.pop("tools", missing)
    if intents is missing or not isinstance(intents, list):
        return rewritten

    intent_set = set(str(intent) for intent in intents)
    has_write = "write" in intent_set
    has_shell = "shell" in intent_set
    has_web_search = "web_search" in intent_set

    rewritten["sandbox_mode"] = "workspace-write" if has_write else "read-only"
    rewritten["features.shell_tool"] = has_shell
    rewritten["web_search"] = "live" if has_web_search else "disabled"
    if has_web_search:
        rewritten["tools.web_search"] = True
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
        rewritten = _apply_codex_tool_intents(
            _apply_mapping(frontmatter, frontmatter_mapping)
        )
        toml_lines = _emit_fields(rewritten, body)
        destination = target_dir / (entry.stem + ".toml")
        destination.write_text("\n".join(toml_lines) + "\n", encoding="utf-8")
