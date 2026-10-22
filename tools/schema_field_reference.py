"""Generate field reference pages from the two published JSON Schemas.

``tools/build-site.py`` calls :func:`generate` to project
``contracts/pack.schema.json`` and ``contracts/skill.schema.json`` into
Starlight pages. A page states only what the schema states: the AC-0010
keywords, each ``description`` verbatim, and a marker where a conditional
keyword applies. Pure standard library.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

NARRATIVE_BASE = (
    "/agent-ready-repo/docs/guides/_shared/reference/catalogue-authoring-standards/"
)

PAGES: tuple[dict[str, str], ...] = (
    {
        "source": "contracts/pack.schema.json",
        "slug": "reference/pack-toml",
        "title": "pack.toml fields",
        "narrative_href": NARRATIVE_BASE + "#2-pack-manifest",
        "narrative_label": "Catalogue authoring standards, section 2 Pack manifest",
    },
    {
        "source": "contracts/skill.schema.json",
        "slug": "reference/skill-frontmatter",
        "title": "SKILL.md frontmatter fields",
        "narrative_href": NARRATIVE_BASE + "#5-skill-frontmatter-and-body",
        "narrative_label": "Catalogue authoring standards, section 5 Skill frontmatter and body",
    },
)

# The AC-0010 keyword set, in the order a Rules cell lists them.
KEYWORDS: tuple[str, ...] = (
    "enum", "const", "pattern", "default", "minimum", "maximum", "minLength",
    "maxLength", "minItems", "maxItems", "maxProperties", "uniqueItems",
    "additionalProperties",
)
CONDITIONAL_KEYWORDS: tuple[str, ...] = ("if", "allOf", "anyOf", "not")
MARKER = "Conditional rules: see the narrative reference"
RULE_SEPARATOR = "<br>"
_MAX_DEPTH = 32


@dataclass
class Alternative:
    """One alternative of a ``oneOf``: its type, AC-0010 values and item alternatives."""

    type: str
    rules: dict[str, Any]
    items: tuple[Alternative, ...] | None = None


@dataclass
class FieldRow:
    """One field path of a schema, as the table states it."""

    path: str
    type: str
    required: str
    rules: list[str]
    description: str
    alternatives: tuple[Alternative, ...] | None = None


def _resolve(node: Any, root: dict[str, Any]) -> dict[str, Any]:
    """Return ``node`` with a local ``$ref`` chain resolved; siblings override."""
    if not isinstance(node, dict):
        return {}
    seen: list[str] = []
    while "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/") or ref in seen:
            raise ValueError(f"unsupported or cyclic $ref: {ref!r}")
        seen.append(ref)
        target: Any = root
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
    return node


def _code(value: Any) -> str:
    """Wrap a schema value in a Markdown code span."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if "`" in text:
        return f"`` {text} ``"
    return f"`{text}`"


def _type_name(node: dict[str, Any]) -> str:
    kind = node.get("type")
    if isinstance(kind, list):
        return ", ".join(str(k) for k in kind)
    return kind if isinstance(kind, str) else ""


def _alternatives(node: dict[str, Any], root: dict[str, Any]) -> list[Alternative]:
    """Alternatives of a ``oneOf`` node; a nested ``oneOf`` contributes in place."""
    out: list[Alternative] = []
    for raw in node.get("oneOf", []):
        alt = _resolve(raw, root)
        if "oneOf" in alt:
            out.extend(_alternatives(alt, root))
        else:
            out.append(_alternative(alt, root))
    return out


def _alternative(node: dict[str, Any], root: dict[str, Any]) -> Alternative:
    items: tuple[Alternative, ...] | None = None
    if isinstance(node.get("items"), dict):
        item = _resolve(node["items"], root)
        items = (
            tuple(_alternatives(item, root)) if "oneOf" in item else (_alternative(item, root),)
        )
    rules = {kw: node[kw] for kw in KEYWORDS if kw in node}
    return Alternative(_type_name(node), rules, items)


def _rule(kw: str, value: Any, root: dict[str, Any], prefix: str = "") -> str:
    """One Rules entry; ``prefix`` is ``items`` or ``keys`` or empty."""
    if kw == "additionalProperties" and value is False:
        return f"{prefix}: no undeclared keys" if prefix else "no undeclared keys"
    if kw == "additionalProperties" and isinstance(value, dict):
        body = f"each value: {_summary(value, root)}"
        return f"{prefix} {body}" if prefix else body
    body = f"{kw}: {_code(value)}"
    return f"{prefix} {body}" if prefix else body


def _render_alternative(alt: Alternative, root: dict[str, Any]) -> str:
    text = alt.type
    if alt.rules:
        text += " (" + ", ".join(_rule(k, v, root) for k, v in alt.rules.items()) + ")"
    if alt.items is not None:
        text += " of [" + _render_alternatives(alt.items, root) + "]"
    return text


def _render_alternatives(
    alts: tuple[Alternative, ...] | list[Alternative], root: dict[str, Any]
) -> str:
    return "; ".join(_render_alternative(a, root) for a in alts)


def _type_text(node: dict[str, Any], root: dict[str, Any]) -> str:
    """The Type cell: ``type``, ``array of ...``, ``one of: ...`` or empty."""
    if "oneOf" in node:
        return "one of: " + _render_alternatives(_alternatives(node, root), root)
    kind = _type_name(node)
    if kind == "array" and isinstance(node.get("items"), dict):
        item = _resolve(node["items"], root)
        if "oneOf" in item:
            return f"array of [{_render_alternatives(_alternatives(item, root), root)}]"
        if _type_name(item):
            return f"array of {_type_name(item)}"
    return kind


def _summary(node: Any, root: dict[str, Any]) -> str:
    return _type_text(_resolve(node, root), root) or "unspecified"


def _node_rules(node: dict[str, Any], root: dict[str, Any]) -> list[str]:
    rules = [_rule(kw, node[kw], root) for kw in KEYWORDS if kw in node]
    if isinstance(node.get("items"), dict):
        item = _resolve(node["items"], root)
        rules += [_rule(kw, item[kw], root, "items") for kw in KEYWORDS if kw in item]
    if isinstance(node.get("propertyNames"), dict):
        names = _resolve(node["propertyNames"], root)
        rules += [_rule(kw, names[kw], root, "keys") for kw in KEYWORDS if kw in names]
    if any(kw in node for kw in CONDITIONAL_KEYWORDS):
        rules.append(MARKER)
    return rules


def _node_alternatives(
    node: dict[str, Any], root: dict[str, Any]
) -> tuple[Alternative, ...] | None:
    """The ``oneOf`` the row text shows: the node's own, else its value or items schema's."""
    if "oneOf" in node:
        return tuple(_alternatives(node, root))
    for key in ("additionalProperties", "items"):
        sub = _resolve(node.get(key), root)
        if "oneOf" in sub:
            return tuple(_alternatives(sub, root))
    return None


def _walk(
    node: dict[str, Any], prefix: str, root: dict[str, Any], rows: list[FieldRow], depth: int
) -> None:
    if depth > _MAX_DEPTH:
        raise ValueError("schema nesting exceeds the field walker's depth limit")
    required = node.get("required", [])
    for key, raw in node.get("properties", {}).items():
        child = _resolve(raw, root)
        path = prefix + key
        rows.append(
            FieldRow(
                path=path,
                type=_type_text(child, root),
                required="yes" if key in required else "no",
                rules=_node_rules(child, root),
                description=str(child.get("description", "")),
                alternatives=_node_alternatives(child, root),
            )
        )
        if "properties" in child:
            _walk(child, path + ".", root, rows, depth + 1)
        if isinstance(child.get("items"), dict):
            item = _resolve(child["items"], root)
            if "properties" in item:
                _walk(item, path + "[].", root, rows, depth + 1)


def field_rows(schema: dict[str, Any]) -> list[FieldRow]:
    """One row per field path, depth-first in schema key order."""
    rows: list[FieldRow] = []
    _walk(_resolve(schema, schema), "", schema, rows, 0)
    return rows


def _cell(text: str) -> str:
    return text.replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def render_page(
    schema: dict[str, Any],
    *,
    title: str,
    source: str,
    narrative_href: str,
    narrative_label: str,
    slug: str | None = None,
) -> str:
    """Return the Markdown page, Starlight frontmatter included.

    ``slug`` is emitted in the frontmatter only when given.
    """
    description = f"Field reference for {title}, generated from {source}."
    lines = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"description: {json.dumps(description, ensure_ascii=False)}",
        *([f"slug: {slug}"] if slug else []),
        "---",
        "",
        f"This table is generated from `{source}`.",
        "",
        f"For what each field means, see [{narrative_label}]({narrative_href}).",
        "",
        "| Field | Type | Required | Rules | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in field_rows(schema):
        cells = [
            f"`{row.path}`",
            _cell(row.type),
            row.required,
            _cell(RULE_SEPARATOR.join(row.rules)),
            _cell(row.description),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def generate(out_dir: Path, *, dry_run: bool = False) -> list[Path]:
    """Write both pages into ``out_dir``; return the paths (written unless ``dry_run``)."""
    written: list[Path] = []
    for spec in PAGES:
        schema = json.loads((REPO_ROOT / spec["source"]).read_text(encoding="utf-8"))
        page = render_page(
            schema,
            title=spec["title"],
            source=spec["source"],
            narrative_href=spec["narrative_href"],
            narrative_label=spec["narrative_label"],
        )
        dest = out_dir / (spec["slug"].rsplit("/", 1)[-1] + ".md")
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            dest.write_text(page, encoding="utf-8", newline="\n")
        written.append(dest)
    return written
