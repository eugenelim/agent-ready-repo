"""Tests for tools/schema_field_reference.py (catalogue-wave6-technical-docs-ia T1).

Covers AC-0009 to AC-0015. Each test is written to fail when the mechanism it
checks is bypassed: drop one keyword from the renderer, flatten a nested
``oneOf``, or render a conditional's contents, and a named test goes red.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "schema_field_reference", ROOT / "tools" / "schema_field_reference.py"
)
sfr = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["schema_field_reference"] = sfr
_spec.loader.exec_module(sfr)  # type: ignore[union-attr]

PACK = json.loads((ROOT / "contracts" / "pack.schema.json").read_text(encoding="utf-8"))
SKILL = json.loads((ROOT / "contracts" / "skill.schema.json").read_text(encoding="utf-8"))
MARKER = "Conditional rules: see the narrative reference"
PACK_HREF = (
    "/agent-ready-repo/docs/guides/_shared/reference/"
    "catalogue-authoring-standards/#2-pack-manifest"
)


def _deref(node: dict, root: dict) -> dict:
    while isinstance(node, dict) and "$ref" in node:
        target: object = root
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]  # type: ignore[index]
        node = target  # type: ignore[assignment]
    return node


def _walk(root: dict) -> list[str]:
    """Independent walker: an explicit stack, not the module's recursion."""
    out: list[str] = []
    stack = [(root, "")]
    while stack:
        node, prefix = stack.pop(0)
        node = _deref(node, root)
        for key, child in node.get("properties", {}).items():
            out.append(prefix + key)
            child = _deref(child, root)
            if "properties" in child:
                stack.append((child, prefix + key + "."))
            if isinstance(child.get("items"), dict):
                item = _deref(child["items"], root)
                if "properties" in item:
                    stack.append((item, prefix + key + "[]."))
    # Stack processed breadth-first above; rows are depth-first, so sort by
    # re-walking order is not needed: compare as a depth-first reordering.
    return _depth_first(out)


def _depth_first(paths: list[str]) -> list[str]:
    """Reorder breadth-first paths into schema-key depth-first order."""
    def parent(p: str) -> str:
        cut = max(p.rfind("."), -1)
        head = p[:cut] if cut >= 0 else ""
        return head[:-2] if head.endswith("[]") else head

    children: dict[str, list[str]] = {}
    for p in paths:
        children.setdefault(parent(p), []).append(p)
    out: list[str] = []

    def emit(p: str) -> None:
        out.append(p)
        for c in children.get(p, []):
            emit(c)

    for top in children.get("", []):
        emit(top)
    return out


def _cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip())[1:-1]
    return [p.strip().replace("\\|", "|") for p in parts]


def _table(page: str) -> list[list[str]]:
    lines = [ln for ln in page.splitlines() if ln.startswith("|")]
    return [_cells(ln) for ln in lines[2:]]


def _row(page: str, path: str) -> list[str]:
    for cells in _table(page):
        if cells[0].strip("`") == path:
            return cells
    raise AssertionError(f"no row {path}")


def _page(schema: dict, **kw) -> str:
    args = {"title": "t", "source": "contracts/x.json", "narrative_href": "/n/#a",
            "narrative_label": "N", **kw}
    return sfr.render_page(schema, **args)


def _rows(schema: dict) -> dict:
    return {r.path: r for r in sfr.field_rows(schema)}


def _real_pages() -> dict[str, str]:
    out = {}
    for spec in sfr.PAGES:
        schema = json.loads((ROOT / spec["source"]).read_text(encoding="utf-8"))
        out[spec["slug"]] = sfr.render_page(
            schema,
            title=spec["title"],
            source=spec["source"],
            narrative_href=spec["narrative_href"],
            narrative_label=spec["narrative_label"],
        )
    return out


# --- AC-0009 ---------------------------------------------------------------

def test_pack_rows_cover_every_field_path():
    assert [r.path for r in sfr.field_rows(PACK)] == _walk(PACK)


def test_skill_rows_cover_every_field_path():
    assert [r.path for r in sfr.field_rows(SKILL)] == _walk(SKILL)


def test_rendered_first_column_equals_walk_without_duplicates():
    pages = _real_pages()
    for slug, schema in (("reference/pack-toml", PACK), ("reference/skill-frontmatter", SKILL)):
        paths = [c[0].strip("`") for c in _table(pages[slug])]
        assert paths == _walk(schema)
        assert len(paths) == len(set(paths))


def test_fixture_nested_array_and_ref_walk():
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "object", "properties": {"b": {"type": "string"}, "c": {"$ref": "#/$defs/leaf"}}},
            "list": {"type": "array", "items": {"$ref": "#/$defs/item"}},
            "plain": {"type": "string"},
        },
        "$defs": {
            "leaf": {"type": "integer"},
            "item": {"type": "object", "required": ["x"], "properties": {"x": {"type": "string"}, "y": {"$ref": "#/$defs/leaf"}}},
        },
    }
    rows = sfr.field_rows(schema)
    assert [r.path for r in rows] == ["a", "a.b", "a.c", "list", "list[].x", "list[].y", "plain"]
    by = {r.path: r for r in rows}
    assert by["a.c"].type == "integer"
    assert by["list[].x"].required == "yes" and by["list[].y"].required == "no"
    assert by["list"].type == "array of object"


# --- AC-0010 ---------------------------------------------------------------

_KEYWORDS = (
    "enum", "const", "pattern", "default", "minimum", "maximum", "minLength",
    "maxLength", "minItems", "maxItems", "maxProperties", "uniqueItems",
    "additionalProperties",
)


def _site(base: int) -> dict:
    return {
        "enum": [f"e{base}"], "const": f"c{base}", "pattern": f"^p{base}$",
        "default": f"d{base}", "minimum": base, "maximum": base + 100,
        "minLength": base + 1, "maxLength": base + 2, "minItems": base + 3,
        "maxItems": base + 4, "maxProperties": base + 5, "uniqueItems": True,
    }


def _all_keywords_schema() -> dict:
    node = _site(10)
    node["additionalProperties"] = {"type": "integer"}
    node["type"] = "array"
    items = _site(20)
    items["additionalProperties"] = {"type": "boolean"}
    items["type"] = "string"
    node["items"] = items
    names = _site(30)
    names["additionalProperties"] = True
    node["propertyNames"] = names
    return {"type": "object", "properties": {"everything": node}}


def test_every_keyword_appears_at_path_items_and_property_names():
    schema = _all_keywords_schema()
    rules = _rows(schema)["everything"].rules
    text = "\n".join(rules)
    for prefix, base in (("", 10), ("items ", 20), ("keys ", 30)):
        for kw, val in _site(base).items():
            shown = val if isinstance(val, str) else json.dumps(val)
            if kw == "enum":
                shown = json.dumps(val)
            assert f"{prefix}{kw}: `{shown}`" in rules, (prefix, kw, text)
    assert "each value: integer" in rules
    assert "items each value: boolean" in rules
    assert "keys additionalProperties: `true`" in rules
    cell = _row(_page(schema), "everything")[3]
    assert "items maxLength: `22`" in cell and "keys minItems: `33`" in cell


def test_additional_properties_false_reads_no_undeclared_keys():
    schema = {"type": "object", "properties": {
        "o": {"type": "object", "additionalProperties": False},
        "l": {"type": "array", "items": {"type": "object", "additionalProperties": False}},
    }}
    rows = _rows(schema)
    assert rows["o"].rules == ["no undeclared keys"]
    assert rows["l"].rules == ["items: no undeclared keys"]


def test_pipe_in_cell_is_escaped_and_value_is_code_span():
    schema = {"type": "object", "properties": {"p": {"type": "string", "pattern": "^a|b$"}}}
    page = _page(schema)
    assert "`^a\\|b$`" in page
    assert _row(page, "p")[3] == "pattern: `^a|b$`"


def test_real_schema_rule_cells():
    pack, skill = _rows(PACK), _rows(SKILL)
    assert pack["schema"].type == ""
    assert "enum: `[1]`" in pack["schema"].rules
    assert "items pattern: `^[^/].*`" in pack["pack.seeds"].rules
    assert pack["pack.install.allowed-scopes"].type == "array"
    assert 'items enum: `["repo", "user", "local"]`' in pack["pack.install.allowed-scopes"].rules
    assert pack["pack.categories"].type == "array of string"
    assert "items: no undeclared keys" in pack["pack.maintainers"].rules
    assert "keys maxLength: `1024`" in skill["compatibility"].rules


# --- AC-0011 ---------------------------------------------------------------

def test_description_is_verbatim_and_otherwise_empty():
    page = _real_pages()["reference/pack-toml"]
    want = PACK["properties"]["pack"]["properties"]["metadata"]["description"]
    assert _row(page, "pack.metadata")[4] == want
    assert _row(page, "pack.name")[4] == ""
    assert _rows(PACK)["pack.metadata"].description == want


# --- AC-0012 ---------------------------------------------------------------

def test_conditional_marker_on_real_rows():
    page = _real_pages()["reference/pack-toml"]
    for path in ("pack", "pack.install"):
        assert MARKER in _row(page, path)[3]
    assert MARKER not in _row(page, "pack.name")[3]


def test_conditional_contents_never_rendered():
    sentinel = "SENTINEL_ZQX"
    schema = {"type": "object", "properties": {"f": {
        "type": "object",
        "if": {"properties": {"k": {"const": sentinel}}},
        "then": {"required": [sentinel]},
        "allOf": [{"pattern": sentinel}],
        "anyOf": [{"const": sentinel}],
        "not": {"enum": [sentinel]},
        "properties": {"k": {"type": "string"}},
    }}}
    page = _page(schema)
    assert sentinel not in page
    assert MARKER in _row(page, "f")[3]
    assert MARKER not in _row(page, "f.k")[3]


# --- AC-0013 ---------------------------------------------------------------

def _alt(type_, rules=None, items=None):
    return sfr.Alternative(type_, rules or {}, items)


def test_compatibility_alternative_records():
    alts = _rows(SKILL)["compatibility"].alternatives
    scalars = (
        _alt("string", {"maxLength": 1024}),
        _alt("boolean"),
        _alt("integer", {"minimum": -9007199254740991, "maximum": 9007199254740991}),
    )
    want = [*scalars, _alt("array", {"maxItems": 256}, scalars)]
    assert [(a.type, a.rules, a.items) for a in alts] == [
        (a.type, a.rules, a.items) for a in want
    ]


def _oneof_fixture(inside: bool) -> dict:
    if inside:
        value = {"oneOf": [
            {"type": "string"},
            {"type": "array", "items": {"oneOf": [{"type": "integer"}, {"type": "boolean"}]}},
        ]}
    else:
        value = {"oneOf": [
            {"type": "string"},
            {"type": "array", "items": {"oneOf": [{"type": "integer"}]}},
            {"type": "boolean"},
        ]}
    return {"type": "object", "properties": {"v": {"type": "object", "additionalProperties": value}}}


def test_oneof_placement_is_distinguished():
    inside, outside = _oneof_fixture(True), _oneof_fixture(False)
    a, b = _rows(inside)["v"].alternatives, _rows(outside)["v"].alternatives
    assert a != b
    assert [x.type for x in a] == ["string", "array"]
    assert [x.type for x in a[1].items] == ["integer", "boolean"]
    assert [x.type for x in b] == ["string", "array", "boolean"]
    assert [x.type for x in b[1].items] == ["integer"]
    assert _row(_page(inside), "v")[3] != _row(_page(outside), "v")[3]
    assert "each value: one of: string; array of [integer; boolean]" in _rows(inside)["v"].rules
    assert "each value: one of: string; array of [integer]; boolean" in _rows(outside)["v"].rules


def test_nested_oneof_alternative_is_flattened_in_place():
    schema = {"type": "object", "properties": {"f": {"oneOf": [
        {"type": "string"},
        {"oneOf": [{"type": "integer"}, {"type": "boolean"}]},
        {"type": "null"},
    ]}}}
    row = _rows(schema)["f"]
    assert [a.type for a in row.alternatives] == ["string", "integer", "boolean", "null"]
    assert row.type == "one of: string; integer; boolean; null"


def test_real_compatibility_cell_text():
    cell = _row(_real_pages()["reference/skill-frontmatter"], "compatibility")[3]
    assert (
        "each value: one of: string (maxLength: `1024`); boolean; integer "
        "(minimum: `-9007199254740991`, maximum: `9007199254740991`); array "
        "(maxItems: `256`) of [string (maxLength: `1024`); boolean; integer "
        "(minimum: `-9007199254740991`, maximum: `9007199254740991`)]"
    ) in cell


# --- AC-0014 ---------------------------------------------------------------

def test_pages_name_source_and_narrative_link():
    pages = _real_pages()
    pack, skill = pages["reference/pack-toml"], pages["reference/skill-frontmatter"]
    assert "contracts/pack.schema.json" in pack and PACK_HREF in pack
    assert "contracts/skill.schema.json" in skill
    assert skill.count("catalogue-authoring-standards/#5-skill-frontmatter-and-body") == 1
    assert pack.startswith('---\ntitle: "pack.toml fields"\ndescription: ')
    assert 'title: "SKILL.md frontmatter fields"' in skill


def test_wave6_pages_carry_only_title_and_description_frontmatter():
    """A slug-less call keeps the Wave 6 frontmatter exactly as it was."""
    for page in _real_pages().values():
        frontmatter = page.split("---\n", 2)[1].splitlines()
        assert [line.split(":", 1)[0] for line in frontmatter] == ["title", "description"]


def test_page_has_no_prose_beyond_sentences_and_table():
    body = _real_pages()["reference/pack-toml"].split("---\n", 2)[2]
    blocks = body.strip().split("\n\n")
    assert len(blocks) == 3
    assert blocks[2].startswith("| Field |")


# --- AC-0015 ---------------------------------------------------------------

def test_render_is_deterministic(tmp_path):
    assert _page(PACK) == _page(PACK)
    one, two = tmp_path / "one", tmp_path / "two"
    p1, p2 = sfr.generate(one), sfr.generate(two)
    assert [p.name for p in p1] == ["pack-toml.md", "skill-frontmatter.md"] == [p.name for p in p2]
    for a, b in zip(p1, p2, strict=True):
        assert a.read_bytes() == b.read_bytes()


def test_generate_dry_run_writes_nothing(tmp_path):
    out = tmp_path / "ref"
    assert len(sfr.generate(out, dry_run=True)) == 2
    assert not out.exists()
