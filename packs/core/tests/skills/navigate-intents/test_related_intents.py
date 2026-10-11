"""Derivation of ``Related intents`` edges (related-intents-field AC-0007..0010, 0021, 0022)."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
_MIXED = _FIXTURES / "mixed"
_FIELD = "Related intents"


def _load(path: pathlib.Path, module_name: str):  # type: ignore[no-untyped-def]
    """Load a navigate-intents script by path under a unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_related_nav")
ig = _load(_SCRIPTS / "intent_graph.py", "core_navigate_intents_related_graph")


def _copy(src: pathlib.Path, tmp_path: pathlib.Path) -> pathlib.Path:
    """Copy a committed corpus into *tmp_path* and return the copy's root."""
    root = tmp_path / "corpus"
    shutil.copytree(src, root)
    return root


def _add_lines(root: pathlib.Path, rel: str, lines: list[str]) -> None:
    """Insert preamble field lines after the Status line of the file at *rel*."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    slug_line = next(x for x in text.splitlines() if x.startswith("- **Status:**")) + "\n"
    path.write_text(
        text.replace(slug_line, slug_line + "".join(f"{x}\n" for x in lines), 1),
        encoding="utf-8",
    )


def _related(root: pathlib.Path, from_id: str | None = None) -> list[dict[str, Any]]:
    """Every related edge derived from *root*, optionally from one node."""
    return [
        e for e in ig.derive(root)["edges"]
        if e["field"] == _FIELD and (from_id is None or e["from"] == from_id)
    ]


_SRC = "docs/product/intents/FEAT-0001-bravo-feat.md"
_SRC_ID = "intent:bravo-feat"


def _rel(value: str) -> str:
    return f"- **Related intents:** {value}"


def test_list_with_repeat_and_trailing_comma_gives_two_edges(tmp_path: pathlib.Path) -> None:
    """AC-0007: items are split, trimmed, de-duplicated, and empties dropped."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel("intent:golf-new, capability:alpha-cap, intent:golf-new,")])
    edges = _related(root)
    assert [e["to"] for e in edges] == ["intent:golf-new", "capability:alpha-cap"]
    assert all(e["from"] == _SRC_ID and "state" not in e for e in edges)


@pytest.mark.parametrize("value", ["none", "None - later", ""])
def test_none_and_empty_give_no_edge(tmp_path: pathlib.Path, value: str) -> None:
    """AC-0007: a `none` or empty value yields nothing."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel(value).rstrip()])
    assert _related(root) == []


def test_two_differing_lines_are_one_multiple_values_edge(tmp_path: pathlib.Path) -> None:
    """AC-0021: differing lines refuse as one multiple_values edge listing both."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel("intent:golf-new"), _rel("capability:alpha-cap")])
    (edge,) = _related(root)
    assert edge["state"] == "multiple_values"
    assert edge["trust_class"] == "pointer_checked"
    assert [v["value"] for v in edge["basis"]["values"]] == ["intent:golf-new", "capability:alpha-cap"]
    assert "value" not in edge


def test_none_line_beside_one_value_gives_that_edge(tmp_path: pathlib.Path) -> None:
    """AC-0021: a `none` line does not count toward the conflict."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel("none"), _rel("intent:golf-new")])
    (edge,) = _related(root)
    assert edge["to"] == "intent:golf-new"


def test_only_live_intents_produce_related_edges(tmp_path: pathlib.Path) -> None:
    """AC-0022: briefs, specs, and tombstones carrying the field give no edge."""
    root = _copy(_MIXED, tmp_path)
    line = _rel("intent:golf-new")
    _add_lines(root, "docs/product/briefs/bravo-delivery.md", [line])
    _add_lines(root, "docs/specs/bravo-spec/spec.md", [line])
    _add_lines(root, "docs/product/intents/FEAT-0003-foxtrot-tomb.md", [line])
    assert _related(root) == []


def _state_edge(tmp_path: pathlib.Path, value: str) -> dict[str, Any]:
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel(value)])
    (edge,) = _related(root, _SRC_ID)
    return edge


@pytest.mark.parametrize(
    ("value", "state", "form"),
    [
        ("intent:bravo-feat", "self_reference", "typed"),
        ("intent:charlie-out", "kind_mismatch", "typed"),
        ("intent:no-such-slug", "dangling", "typed"),
        ("intent:foxtrot-tomb", "retired_target", "typed"),
        ("intent:Foo", "unparseable", "unrecognized"),
        ("brief:Bad_Slug", "unparseable", "unrecognized"),
        ("brief:bravo-delivery", "out_of_type", "typed"),
        ("spec:bravo-spec", "out_of_type", "typed"),
        ("golf-new", "unparseable", "bare_slug"),
    ],
)
def test_refused_states(tmp_path: pathlib.Path, value: str, state: str, form: str) -> None:
    """AC-0008: each refused state, with its basis form."""
    edge = _state_edge(tmp_path, value)
    assert edge["state"] == state
    assert edge["form"] == edge["basis"]["form"] == form
    assert edge["value"] == value
    assert "to" not in edge


def test_retired_target_carries_reissued_as(tmp_path: pathlib.Path) -> None:
    """AC-0008: a tombstone target names what it was reissued as."""
    edge = _state_edge(tmp_path, "intent:foxtrot-tomb")
    assert edge["reissued_as"] == "intent:golf-new"


@pytest.mark.parametrize(
    ("value", "target"),
    [
        ("capability:alpha-cap", "capability:alpha-cap"),
        ("outcome:charlie-out", "outcome:charlie-out"),
        ("opportunity:delta-opp", "opportunity:delta-opp"),
        ("intent:golf-new", "intent:golf-new"),
    ],
)
def test_resolved_edge_per_intent_kind(tmp_path: pathlib.Path, value: str, target: str) -> None:
    """AC-0008: every intent kind resolves."""
    edge = _state_edge(tmp_path, value)
    assert edge["to"] == target and "state" not in edge


def test_trust_classes(tmp_path: pathlib.Path) -> None:
    """AC-0009: related edges are pointer_checked; Parent intent edges stay pointer_unchecked."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel("intent:golf-new, intent:bravo-feat, brief:x, intent:nope")])
    _add_lines(root, "docs/product/intents/FEAT-0004-golf-new.md", [_rel("a"), _rel("b")])
    edges = ig.derive(root)["edges"]
    related = [e for e in edges if e["field"] == _FIELD]
    assert len(related) >= 5
    assert {e["trust_class"] for e in related} == {"pointer_checked"}
    parents = [e for e in edges if e["field"] == "Parent intent"]
    assert parents and {e["trust_class"] for e in parents} == {"pointer_unchecked"}


def test_self_reference_corpus_is_committed() -> None:
    """AC-0008: the committed corpus derives one self_reference edge."""
    (edge,) = _related(_FIXTURES / "negative" / "self_reference")
    assert edge["state"] == "self_reference"
    manifest = json.loads(
        (_FIXTURES / "negative" / "self_reference" / "expected-outstanding.json").read_text()
    )
    assert manifest == {"outstanding": ["intent:self-ref"]}


# --- AC-0010: no existing answer changes ------------------------------------


def _cycle_corpus(root: pathlib.Path, *, related: bool) -> None:
    """A mutual pair and a three-loop, each related to the next, optionally."""
    intents = root / "docs" / "product" / "intents"
    intents.mkdir(parents=True)
    ring = {"a": "b", "b": "a", "c": "d", "d": "e", "e": "c", "f": "a"}
    for i, (slug, other) in enumerate(ring.items(), start=1):
        rel = f"- **Related intents:** intent:{other}, intent:{slug}\n" if related else ""
        (intents / f"FEAT-{i:04d}-{slug}.md").write_text(
            f"# Feature: {slug}\n\n- **Slug:** `{slug}`\n- **Status:** Draft\n"
            f"- **Level:** feature\n- **Owner:** placeholder-owner\n"
            f"- **Parent intent:** intent:{other}\n{rel}\n## Outcome\n\nx\n",
            encoding="utf-8",
        )


def _strip(value: Any) -> Any:
    """Remove volatile (time, root) and related-only keys from a result, recursively."""
    drop = {"generated_at", "provenance", "related_written_here", "related_written_elsewhere"}
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in drop}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


def _answers(root: pathlib.Path) -> dict[str, Any]:
    """Every operation the criterion names, over every intent."""
    def run(*args: str) -> Any:
        result, code = nav.run_query(root, ["query", *args])
        assert code == 0, result
        return _strip(result)

    out: dict[str, Any] = {
        "outstanding": run("--operation", "outstanding"),
        "search": run("--operation", "search"),
        "tree": run("--operation", "tree"),
        "summary": run("--operation", "summary"),
    }
    for node in ig.derive(root)["nodes"]:
        out[f"ancestors:{node['id']}"] = run("--operation", "ancestors", "--id", node["id"])
        out[f"record:{node['id']}"] = run("--operation", "record", "--id", node["id"])
    return out


def test_related_field_changes_no_existing_answer(tmp_path: pathlib.Path) -> None:
    """AC-0010: with and without the field, the cycle corpus answers the same."""
    plain = tmp_path / "plain"
    with_field = tmp_path / "with_field"
    _cycle_corpus(plain, related=False)
    _cycle_corpus(with_field, related=True)
    graph = ig.derive(with_field)
    assert any(e["field"] == _FIELD for e in graph["edges"])
    assert not any(e.get("state") == "cycle" for e in graph["edges"] if e["field"] == _FIELD)
    plain_answers = _answers(plain)
    field_answers = _answers(with_field)
    for key in plain_answers:
        if key.startswith("summary"):
            continue  # summary counts refused related edges by design (AC-0015)
        assert field_answers[key] == plain_answers[key], key


# --- AC-0011..0015: the query surface ----------------------------------------

_ALPHA = "docs/product/intents/CAP-0001-alpha-cap.md"
_INDIA = "docs/product/intents/FEAT-0005-india-none.md"
_JULIET = "docs/product/intents/FEAT-0006-juliet-done.md"
_ECHO = "docs/product/intents/FEAT-0002-echo-crosstype.md"


def _query(root: pathlib.Path, *args: str) -> Any:
    result, code = nav.run_query(root, ["query", *args])
    assert code == 0, result
    return result


def _related_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """alpha-cap relates to golf-new and a dangling slug; india and juliet relate back."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _ALPHA, [_rel("intent:golf-new, intent:no-such-slug")])
    _add_lines(root, _INDIA, [_rel("capability:alpha-cap")])
    _add_lines(root, _JULIET, [_rel("capability:alpha-cap")])
    # A refused edge from a third intent that names alpha-cap with the wrong kind.
    _add_lines(root, _ECHO, [_rel("intent:alpha-cap")])
    return root


def test_record_carries_both_lists_in_order(tmp_path: pathlib.Path) -> None:
    """AC-0011: written-here in value order, written-elsewhere by from; refusals elsewhere absent."""
    root = _related_corpus(tmp_path)
    alpha = _query(root, "--operation", "record", "--id", "capability:alpha-cap")["record"]
    assert [(e.get("to"), e.get("state")) for e in alpha["related_written_here"]] == [
        ("intent:golf-new", None),
        (None, "dangling"),
    ]
    assert [e["from"] for e in alpha["related_written_elsewhere"]] == [
        "intent:india-none",
        "intent:juliet-done",
    ]
    assert all("state" not in e for e in alpha["related_written_elsewhere"])
    golf = _query(root, "--operation", "record", "--id", "intent:golf-new")["record"]
    assert golf["related_written_here"] == []
    assert [e["from"] for e in golf["related_written_elsewhere"]] == ["capability:alpha-cap"]
    echo = _query(root, "--operation", "record", "--id", "outcome:echo-crosstype")["record"]
    assert [e["state"] for e in echo["related_written_here"]] == ["kind_mismatch"]
    assert echo["related_written_elsewhere"] == []


def test_multiple_values_is_one_written_here_entry(tmp_path: pathlib.Path) -> None:
    """AC-0011: a multiple_values refusal is one entry."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel("intent:golf-new"), _rel("capability:alpha-cap")])
    rec = _query(root, "--operation", "record", "--id", _SRC_ID)["record"]
    assert [e["state"] for e in rec["related_written_here"]] == ["multiple_values"]


def test_tree_entries_carry_lists_search_and_ancestors_do_not(tmp_path: pathlib.Path) -> None:
    """AC-0012: tree has both keys; search and ancestors have neither."""
    root = _related_corpus(tmp_path)
    entries = {e["id"]: e for e in _query(root, "--operation", "tree")["intents"]}
    assert [e["from"] for e in entries["capability:alpha-cap"]["related_written_elsewhere"]] == [
        "intent:india-none",
        "intent:juliet-done",
    ]
    assert len(entries["capability:alpha-cap"]["related_written_here"]) == 2
    assert all(
        "related_written_here" in e and "related_written_elsewhere" in e for e in entries.values()
    )
    for e in _query(root, "--operation", "search")["intents"]:
        assert "related_written_here" not in e and "related_written_elsewhere" not in e
    for e in _query(root, "--operation", "ancestors", "--id", "intent:bravo-feat")["chain"]:
        assert "related_written_here" not in e and "related_written_elsewhere" not in e


def _flat_corpus(root: pathlib.Path, *, related: bool, n: int = 150) -> None:
    intents = root / "docs" / "product" / "intents"
    intents.mkdir(parents=True)
    for i in range(1, n + 1):
        rel = ""
        if related:
            targets = ", ".join(f"intent:s{(i + k - 1) % n + 1:03d}" for k in (1, 2))
            rel = f"- **Related intents:** {targets}\n"
        (intents / f"FEAT-{i:04d}-s{i:03d}.md").write_text(
            f"# Feature: s{i:03d}\n\n- **Slug:** `s{i:03d}`\n- **Status:** Draft\n"
            f"- **Level:** feature\n- **Owner:** placeholder-owner\n"
            f"- **Parent intent:** none\n{rel}\n## Outcome\n\nx\n",
            encoding="utf-8",
        )


def test_related_entries_count_toward_edge_limit(tmp_path: pathlib.Path) -> None:
    """AC-0013: each entry of both lists is one edge; the same corpus without the field is ok."""
    plain, with_field = tmp_path / "plain", tmp_path / "with_field"
    _flat_corpus(plain, related=False)
    _flat_corpus(with_field, related=True)
    result, code = nav.run_query(plain, ["query", "--operation", "tree"])
    assert code == 0 and result["status"] == "ok", result
    result, code = nav.run_query(with_field, ["query", "--operation", "tree"])
    assert code == 1
    assert result["error"]["code"] == "result_too_large"
    # 300 written-here entries plus the same 300 edges seen from the other end.
    assert result["error"]["observed"]["edges"] == 600


def test_summary_counts_related_refusals_by_state(tmp_path: pathlib.Path) -> None:
    """AC-0015: summary counts each related refused state, self_reference included."""
    root = _copy(_MIXED, tmp_path)
    _add_lines(root, _SRC, [_rel("intent:bravo-feat, intent:no-such-slug, intent:charlie-out")])
    base = _query(_MIXED, "--operation", "summary")["summary"]["refused_edges_by_state"]
    now = _query(root, "--operation", "summary")["summary"]["refused_edges_by_state"]
    for state in ("self_reference", "dangling", "kind_mismatch"):
        assert now.get(state, 0) - base.get(state, 0) == 1, state
