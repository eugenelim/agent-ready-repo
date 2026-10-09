"""Regression tests for defects found in review of the navigator.

Each test builds the smallest corpus that shows one defect and asserts the
repaired property itself, so it fails on the code that had the defect.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import sys

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_HERE = pathlib.Path(__file__).resolve().parent
_FIXTURES = _HERE / "fixtures"
_MIXED = _FIXTURES / "mixed"
_COORDINATED = _FIXTURES / "coordinated_delivery"
_NODE_ID_RE = re.compile(r"^(intent|capability|outcome|opportunity|brief|spec):\S+$")


def _load(path: pathlib.Path, module_name: str):  # type: ignore[no-untyped-def]
    """Load a navigate-intents script by path under a pack-and-skill-unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_regressions_nav")
ig = _load(_SCRIPTS / "intent_graph.py", "core_navigate_intents_regressions_graph")
resolver = _load(
    _SCRIPTS / "intent_delivery_relations.py",
    "core_navigate_intents_regressions_resolver",
)


def _query(root: pathlib.Path, *args: str):  # type: ignore[no-untyped-def]
    """Run one query and return its result, asserting it succeeded."""
    result, code = nav.run_query(root, ["query", *args])
    assert code == 0, result
    return result


def _copy(src: pathlib.Path, tmp_path: pathlib.Path) -> pathlib.Path:
    """Copy a committed corpus into *tmp_path* and return the copy's root."""
    root = tmp_path / "corpus"
    shutil.copytree(src, root)
    return root


def _intent(root: pathlib.Path, name: str, body: str) -> None:
    """Write an intent file under the corpus's intents directory."""
    (root / "docs" / "product" / "intents" / name).write_text(body, encoding="utf-8")


def _outstanding_ids(result: dict) -> list[str]:  # type: ignore[type-arg]
    """Every item id in a JSON outstanding result."""
    return [item["id"] for item in result["placed"] + result["no_parent"]]


def _text_ids(text: str) -> set[str]:
    """Every node id printed at the start of an outstanding text line."""
    ids = set()
    for line in text.splitlines():
        token = line.strip().split(" · ")[0]
        if _NODE_ID_RE.match(token):
            ids.add(token)
    return ids


# --- A plain file directly under docs/specs/ ---------------------------------


def test_plain_file_under_specs_is_not_a_node_and_does_not_fail(
    tmp_path: pathlib.Path,
) -> None:
    """A README beside the spec directories is skipped, not refused as unsafe."""
    root = _copy(_MIXED, tmp_path)
    assert (root / "docs" / "specs" / "README.md").is_file()
    result = _query(root, "--operation", "summary")
    assert result["status"] == "ok"
    graph = ig.derive(root)
    assert not any("README" in node["id"] for node in graph["nodes"])


# --- Delivery relations reach the navigator node, whatever its id ------------


def test_relation_attaches_to_outcome_kind_feature_intent(tmp_path: pathlib.Path) -> None:
    """The resolver names `intent:<slug>`; a Kind: outcome feature still gets its relation."""
    root = _copy(_COORDINATED, tmp_path)
    path = root / "docs" / "product" / "intents" / "FEAT-0001-alpha-feat.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "- **Level:** feature", "- **Level:** feature\n- **Kind:** outcome"
        ),
        encoding="utf-8",
    )
    expected = [
        rel for rel in resolver.resolve_repository(root)["relations"]
        if rel["intent"] == "intent:alpha-feat"
    ]
    assert expected, "the resolver must emit a relation for alpha-feat"
    record = _query(root, "--operation", "record", "--id", "alpha-feat")["record"]
    assert record["id"] == "outcome:alpha-feat"
    shown = [
        {k: v for k, v in rel.items() if k != "trust_class"}
        for rel in record["delivery_relations"]
    ]
    assert shown == expected
    tree = _query(root, "--operation", "tree")
    entry = next(i for i in tree["intents"] if i["id"] == "outcome:alpha-feat")
    assert len(entry["delivery_relations"]) == len(expected)


def test_resolver_diagnostics_are_shown_on_their_intent(tmp_path: pathlib.Path) -> None:
    """A resolver diagnostic whose subject names an intent appears on that intent's record."""
    root = _copy(_COORDINATED, tmp_path)
    (root / "docs" / "product" / "briefs" / "BRIEF-0002-beta-brief.md").unlink()
    diagnostics = [
        d for d in resolver.resolve_repository(root)["diagnostics"]
        if d.get("subject") == "intent:beta-feat"
    ]
    assert diagnostics, "removing the brief must make the resolver diagnose beta-feat"
    record = _query(root, "--operation", "record", "--id", "beta-feat")["record"]
    assert record["delivery_diagnostics"] == diagnostics
    tree = _query(root, "--operation", "tree")
    entry = next(i for i in tree["intents"] if i["id"] == "intent:beta-feat")
    assert entry["delivery_diagnostics"] == diagnostics


def test_spec_placement_carries_the_resolver_relation_type() -> None:
    """Each spec placement under a brief names the resolver relation type joining them."""
    relations = resolver.resolve_repository(_COORDINATED)["relations"]
    expected = {(rel["spec"], rel["brief"]): rel["type"] for rel in relations}
    assert expected
    result = _query(_COORDINATED, "--operation", "outstanding")
    seen = 0
    for item in result["placed"] + result["no_parent"]:
        for placement in item.get("placements", []):
            parent = (placement.get("parent_edge") or {}).get("to")
            if (item["id"], parent) in expected:
                assert placement["relation_type"] == expected[(item["id"], parent)]
                seen += 1
    assert seen == len(expected)


# --- Outstanding text is complete --------------------------------------------


@pytest.mark.parametrize(
    "corpus",
    sorted(m.parent for m in _FIXTURES.glob("**/expected-outstanding.json")),
    ids=lambda path: path.relative_to(_FIXTURES).as_posix(),
)
def test_outstanding_text_prints_every_json_item(corpus: pathlib.Path) -> None:
    """Every item in the JSON outstanding result has a line in the text output."""
    result, code = nav.run_query(corpus, ["query", "--operation", "outstanding"])
    if code != 0:
        pytest.skip(f"whole operation fails on this corpus: {result['error']['code']}")
    text = _query(corpus, "--operation", "outstanding", "--format", "text")
    assert set(_outstanding_ids(result)) <= _text_ids(text)


def test_outstanding_text_prints_item_under_a_terminal_parent(tmp_path: pathlib.Path) -> None:
    """An outstanding intent whose parent is terminal prints under that parent."""
    root = _copy(_MIXED, tmp_path)
    _intent(root, "FEAT-0901-india-open.md", (
        "# Feature: India open\n\n- **Slug:** india-open\n- **Status:** Draft\n"
        "- **Level:** feature\n- **Parent intent:** capability:hotel-done\n\n## Outcome\n"
    ))
    lines = _query(root, "--operation", "outstanding", "--format", "text").splitlines()
    parent = next(i for i, ln in enumerate(lines) if ln.startswith("capability:hotel-done "))
    assert lines[parent + 1].startswith("  intent:india-open · ")


def test_outstanding_from_text_matches_json() -> None:
    """`--from` text prints exactly the items its JSON returns, rooted at the start intent."""
    result = _query(_MIXED, "--operation", "outstanding", "--from", "bravo-feat")
    text = _query(_MIXED, "--operation", "outstanding", "--from", "bravo-feat", "--format", "text")
    assert _text_ids(text) == set(_outstanding_ids(result))
    assert text.splitlines()[0].startswith("intent:bravo-feat · ")


def test_outstanding_json_is_in_node_id_order() -> None:
    """Placed and no-parent items are each ordered by node id in code-point order."""
    result = _query(_MIXED, "--operation", "outstanding")
    for group in ("placed", "no_parent"):
        ids = [item["id"] for item in result[group]]
        assert ids == sorted(ids), group


# --- Chains --------------------------------------------------------------------


def test_outstanding_chain_continues_past_a_terminal_ancestor(tmp_path: pathlib.Path) -> None:
    """A placement walks past a terminal ancestor to the root, marking it terminal."""
    root = _copy(_MIXED, tmp_path)
    _intent(root, "CAP-0901-mid-done.md", (
        "# Capability: Mid done\n\n- **Slug:** mid-done\n- **Status:** Fulfilled\n"
        "- **Level:** capability\n- **Parent intent:** capability:alpha-cap\n\n## Outcome\n"
    ))
    _intent(root, "FEAT-0902-under-mid.md", (
        "# Feature: Under mid\n\n- **Slug:** under-mid\n- **Status:** Draft\n"
        "- **Level:** feature\n- **Parent intent:** capability:mid-done\n\n## Outcome\n"
    ))
    result = _query(root, "--operation", "outstanding")
    item = next(i for i in result["placed"] if i["id"] == "intent:under-mid")
    assert item["ancestors"] == [
        {"id": "capability:mid-done", "terminal": True},
        {"id": "capability:alpha-cap", "terminal": False},
    ]


@pytest.mark.parametrize(
    "root, state",
    [
        (_FIXTURES / "negative" / "cycle", "cycle"),
        (_FIXTURES / "negative" / "dangling", "dangling"),
    ],
    ids=["cycle", "dangling"],
)
def test_ancestors_keeps_the_refused_edge_that_ends_the_chain(
    root: pathlib.Path, state: str
) -> None:
    """The last chain intent carries its refused parent edge, not a blank."""
    graph = ig.derive(root)
    refused = next(e for e in graph["edges"] if e.get("state") == state)
    chain = _query(root, "--operation", "ancestors", "--id", refused["from"])["chain"]
    assert chain[-1]["id"] == refused["from"]
    assert chain[-1]["parent_edge"] == refused


def test_outstanding_brief_item_shows_every_refused_parent_edge() -> None:
    """A brief with one accepted and one malformed parent shows the malformed edge on its item."""
    root = _FIXTURES / "negative" / "brief_parent_repair"
    result = _query(root, "--operation", "outstanding")
    item = next(i for i in result["placed"] + result["no_parent"] if i["id"] == "brief:repair-parent")
    refused = [e for e in item.get("refused_parent_edges", []) if e.get("state") == "unparseable"]
    assert [e["value"] for e in refused] == ["bad-value-no-prefix"]


# --- Value forms and refusal states ------------------------------------------


@pytest.mark.parametrize(
    "value, form, state",
    [
        ("docs/other/x.md", "path", "unparseable"),
        ("https://example.com/x", "unrecognized", "unparseable"),
        ("tbd: later", "unrecognized", "unparseable"),
        ("brief:bravo-delivery", "typed", "out_of_type"),
    ],
)
def test_intent_parent_value_form_and_state(
    value: str, form: str, state: str, tmp_path: pathlib.Path
) -> None:
    """Only artifact-type references are typed; other values keep their shape's state."""
    root = _copy(_MIXED, tmp_path)
    _intent(root, "FEAT-0903-probe.md", (
        "# Feature: Probe\n\n- **Slug:** probe-feat\n- **Status:** Draft\n"
        f"- **Level:** feature\n- **Parent intent:** {value}\n\n## Outcome\n"
    ))
    edge = next(
        e for e in ig.derive(root)["edges"]
        if e["from"] == "intent:probe-feat" and e["field"] == "Parent intent"
    )
    assert (edge["form"], edge["state"]) == (form, state)
    assert edge["basis"] == {"field": "Parent intent", "form": form}


def test_spec_discovery_with_differing_values_is_one_multiple_values_refusal(
    tmp_path: pathlib.Path,
) -> None:
    """Two differing intent-valued Discovery: values give one refusal that keeps its basis."""
    root = _copy(_MIXED, tmp_path)
    spec_dir = root / "docs" / "specs" / "probe-spec"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(
        "# Spec: Probe\n\n- **Status:** Draft\n- **Discovery:** intent:bravo-feat\n"
        "- **Discovery:** capability:alpha-cap\n\n## Outcome\n",
        encoding="utf-8",
    )
    edges = [
        e for e in ig.derive(root)["edges"]
        if e["from"] == "spec:probe-spec" and e["field"] == "Discovery"
    ]
    assert len(edges) == 1 and edges[0]["state"] == "multiple_values"
    assert edges[0]["basis"]["field"] == "Discovery"
    assert edges[0]["basis"]["form"] == "typed"


# --- Levels ------------------------------------------------------------------


def test_missing_level_is_unrecorded_on_every_json_surface() -> None:
    """An intent with no Level: shows `unrecorded` in outstanding, record, and search."""
    item = next(
        i for i in _query(_MIXED, "--operation", "outstanding")["no_parent"]
        if i["id"] == "opportunity:delta-opp"
    )
    assert item["level"] == "unrecorded"
    record = _query(_MIXED, "--operation", "record", "--id", "delta-opp")["record"]
    assert record["level"] == "unrecorded"
    hits = _query(_MIXED, "--operation", "search", "--selectors", '{"text": "delta-opp"}')
    assert [hit["level"] for hit in hits["intents"]] == ["unrecorded"]
