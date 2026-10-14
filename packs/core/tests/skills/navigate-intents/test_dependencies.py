"""The ``dependencies`` query over intent ``Depends on:`` headers (intent-dependency-graphs T1)."""

from __future__ import annotations

import hashlib
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
_DEP = _FIXTURES / "dependency"
_MANIFEST = json.loads((_DEP / "expected-dependencies.json").read_text(encoding="utf-8"))
_INTENTS = sorted(json.loads((_DEP / "expected-outstanding.json").read_text(encoding="utf-8"))["outstanding"])


def _load(path: pathlib.Path, module_name: str):  # type: ignore[no-untyped-def]
    """Load a navigate-intents script by path under a unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_dependencies_nav")


def _q(root: pathlib.Path, *args: str, limits: dict[str, int] | None = None) -> tuple[Any, int]:
    """Run ``query --operation dependencies`` with *args* over *root*."""
    return nav.run_query(root, ["query", "--operation", "dependencies", *args], _limits=limits)


def _ok(root: pathlib.Path, *args: str) -> dict[str, Any]:
    """Run a dependencies query that must succeed and return its result."""
    result, code = _q(root, *args)
    assert code == 0, result
    assert result["status"] == "ok"
    return result  # type: ignore[no-any-return]


def _pairs(result: dict[str, Any]) -> set[tuple[str, str]]:
    return {(e["from"], e["to"]) for e in result["edges"]}


def _ids(result: dict[str, Any]) -> set[str]:
    return {i["id"] for i in result["intents"]}


def _expected_edge(m: dict[str, Any]) -> dict[str, Any]:
    """The full edge record a manifest edge stands for."""
    return {
        "from": m["from"], "to": m["to"], "field": "Depends on", "trust_class": "pointer_unchecked",
        "basis": {"field": "Depends on", "values": [
            {"value": v, "form": f, "position": p} for v, f, p in m["values"]
        ]},
    }


def _expected_diag(m: dict[str, Any]) -> dict[str, Any]:
    """The full pointer-diagnostic record a manifest entry stands for."""
    diag = {"from": m["from"], "field": "Depends on", "value": m["value"], "form": m["form"],
            "position": m["position"], "state": m["state"], "trust_class": "pointer_unchecked"}
    if "reissued_as" in m:
        diag["reissued_as"] = m["reissued_as"]
    return diag


def _copy(tmp_path: pathlib.Path, src: pathlib.Path = _DEP) -> pathlib.Path:
    root = tmp_path / "corpus"
    shutil.copytree(src, root)
    return root


def _write_intent(root: pathlib.Path, fname: str, slug: str, deps: list[str]) -> None:
    lines = [f"# Feature: {slug}", "", f"- **Slug:** `{slug}`", "- **Status:** Draft",
             "- **Level:** feature", "- **Parent intent:** none"]
    lines += [f"- **Depends on:** {d}" for d in deps]
    lines += ["", "## Outcome", "", "Placeholder.", ""]
    (root / "docs" / "product" / "intents" / fname).write_text("\n".join(lines), encoding="utf-8")


def _stable(result: Any) -> Any:
    """Drop the inherited nondeterministic and path-bound provenance fields."""
    if isinstance(result, str):
        return result
    out = dict(result)
    out["provenance"] = {k: v for k, v in result["provenance"].items() if k not in ("generated_at", "root")}
    return out


# ---------------------------------------------------------------- reading


def test_whole_corpus_records_match_the_hand_written_manifest() -> None:
    """Every edge, pointer diagnostic and cycle of the fixture, in record order (AC-0001 to AC-0005)."""
    union_edges: dict[tuple[str, str], dict[str, Any]] = {}
    union_diags: list[dict[str, Any]] = []
    for start in _INTENTS:
        r = _ok(_DEP, "--id", start, "--direction", "both", "--depth", str(len(_INTENTS)))
        for e in r["edges"]:
            union_edges[(e["from"], e["to"])] = e
        union_diags += [d for d in r["diagnostics"] if d not in union_diags]
    assert [union_edges[k] for k in sorted(union_edges)] == [_expected_edge(m) for m in _MANIFEST["edges"]]
    pointer = sorted((d for d in union_diags if "from" in d), key=lambda d: (d["from"], d["position"]))
    assert pointer == [_expected_diag(m) for m in _MANIFEST["pointer_diagnostics"]]
    cycles = sorted((d["members"] for d in union_diags if d["state"] == "cycle"), key=lambda m: m[0])
    assert cycles == _MANIFEST["cycles"]


def test_none_comment_empty_and_body_values_give_no_pointer() -> None:
    """``none``, comment-only, empty and body values, and other fields, give nothing (AC-0001)."""
    r = _ok(_DEP, "--id", "capability:root-a")
    assert r["edges"] == [] and r["diagnostics"] == []
    charlie = _ok(_DEP, "--id", "intent:charlie")
    assert ("intent:charlie", "intent:alpha") not in _pairs(charlie)
    alpha = _ok(_DEP, "--id", "intent:alpha")
    # "none yet" and the comment-only line come first, so positions start at the real line.
    assert alpha["edges"][0]["basis"]["values"][0]["position"] == 0


def test_a_cycle_member_lists_its_faults_by_position() -> None:
    """One intent holds two faults and a cycle membership (AC-0004, AC-0005)."""
    r = _ok(_DEP, "--id", "intent:india", "--depth", "0")
    assert [(d.get("position"), d["state"]) for d in r["diagnostics"]] == [
        (1, "dangling"), (2, "kind_mismatch"), (None, "cycle"),
    ]


# ---------------------------------------------------------------- traversal


@pytest.mark.parametrize(
    ("start", "direction", "depth", "intents"),
    [
        ("intent:alpha", "prerequisites", 0, {"intent:alpha"}),
        ("intent:alpha", "prerequisites", 1, {"intent:alpha", "intent:bravo"}),
        ("intent:alpha", "prerequisites", 2, {"intent:alpha", "intent:bravo", "intent:charlie"}),
        ("intent:alpha", "prerequisites", 18, {"intent:alpha", "intent:bravo", "intent:charlie",
                                               "capability:root-b", "outcome:quebec", "opportunity:romeo"}),
        ("intent:golf", "dependents", 1, {"intent:golf", "intent:echo", "intent:foxtrot"}),
        ("intent:golf", "dependents", 2, {"intent:golf", "intent:echo", "intent:foxtrot", "intent:delta"}),
        ("intent:india", "both", 1, {"intent:india", "intent:juliet", "intent:kilo"}),
        ("intent:november", "both", 0, {"intent:november"}),
    ],
)
def test_traversal_returns_the_expected_intents(start: str, direction: str, depth: int, intents: set[str]) -> None:
    """Each direction at depths 0, 1, 2 and all steps (AC-0006)."""
    r = _ok(_DEP, "--id", start, "--direction", direction, "--depth", str(depth))
    assert _ids(r) == intents
    assert [i["id"] for i in r["intents"]] == sorted(intents)
    assert _pairs(r) == {(m["from"], m["to"]) for m in _MANIFEST["edges"]
                         if m["from"] in intents and m["to"] in intents}
    assert (r["start"], r["direction"], r["depth"]) == (start, direction, depth)
    assert "Depends on:" in r["scope"]


def test_both_across_a_cycle_includes_the_edge_between_returned_intents() -> None:
    """``both`` returns juliet -> kilo, whose ends were reached in opposite directions (AC-0006)."""
    r = _ok(_DEP, "--id", "intent:india", "--direction", "both")
    assert _pairs(r) == {("intent:india", "intent:juliet"), ("intent:juliet", "intent:kilo"),
                         ("intent:kilo", "intent:india")}
    assert [d["state"] for d in r["diagnostics"]] == ["dangling", "kind_mismatch", "cycle"]


def test_steps_take_the_smaller_count_under_both() -> None:
    """A cycle member is reachable both ways; its step count is the smaller (step count term)."""
    records = nav._dependency_records(_DEP, nav._load_graph_mod(), nav._load_graph_mod().derive(_DEP))
    steps = nav._dependency_steps(records, "intent:india", "both", None)
    assert steps == {"intent:india": 0, "intent:juliet": 1, "intent:kilo": 1}
    assert nav._dependency_steps(records, "intent:india", "prerequisites", None)["intent:kilo"] == 2


def test_a_cycle_reaching_past_the_depth_still_names_every_member() -> None:
    """A cycle diagnostic is included when one member is returned (AC-0006)."""
    r = _ok(_DEP, "--id", "intent:mike", "--depth", "1")
    assert _ids(r) == {"intent:mike", "intent:november"}
    assert [d["members"] for d in r["diagnostics"]] == [["intent:mike", "intent:november", "intent:oscar"]]


def test_defaults_are_prerequisites_and_one_step() -> None:
    r = _ok(_DEP, "--id", "intent:alpha")
    assert (r["direction"], r["depth"]) == ("prerequisites", 1)
    assert r["query"] == {"operation": "dependencies", "id": "intent:alpha"}


@pytest.mark.parametrize(
    ("args", "code"),
    [
        ((), "invalid_query"),
        (("--id", "intent:alpha", "--direction", "sideways"), "invalid_query"),
        (("--id", "intent:alpha", "--depth", "-1"), "invalid_depth"),
        (("--id", "intent:nobody"), "not_found"),
    ],
)
def test_invalid_selectors_and_identities_refuse(args: tuple[str, ...], code: str) -> None:
    result, exit_code = _q(_DEP, *args)
    assert exit_code == 1 and result["error"]["code"] == code


def test_an_unknown_operation_is_still_refused() -> None:
    result, code = nav.run_query(_DEP, ["query", "--operation", "nope"])
    assert code == 1 and result["error"]["code"] == "unknown_operation"
    assert "dependencies" in result["error"]["message"]


# ---------------------------------------------------------------- limits


@pytest.mark.parametrize(
    ("limits", "refused"),
    [
        ({"max_edges": 6}, False),
        ({"max_edges": 5}, True),
        ({"max_intents": 3}, False),
        ({"max_intents": 2}, True),
    ],
)
def test_edge_and_intent_limits_admit_at_and_refuse_over(limits: dict[str, int], refused: bool) -> None:
    """india ``both`` returns 3 intents, 3 edges and 3 diagnostics (AC-0007)."""
    result, code = _q(_DEP, "--id", "intent:india", "--direction", "both", limits=limits)
    if refused:
        assert code == 1 and result["error"]["code"] == "result_too_large"
        assert result["error"]["limits"]["bounded_route"] == "--depth"
        assert "edges" not in result
    else:
        assert code == 0


def test_byte_limit_admits_at_and_refuses_over() -> None:
    ok = _ok(_DEP, "--id", "intent:golf")
    size = len(json.dumps(ok, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    _, code = _q(_DEP, "--id", "intent:golf", limits={"max_result_bytes": size + 200})
    assert code == 0
    result, code = _q(_DEP, "--id", "intent:golf", limits={"max_result_bytes": 100})
    assert code == 1 and result["error"]["code"] == "result_too_large"


def test_text_byte_limit_refuses() -> None:
    result, code = _q(_DEP, "--id", "intent:golf", "--format", "text", limits={"max_result_bytes": 50})
    assert code == 1 and result["error"]["code"] == "result_too_large"


def _deep_corpus(tmp_path: pathlib.Path, n: int, *, cycle: bool) -> pathlib.Path:
    root = tmp_path / "deep"
    (root / "docs" / "product" / "intents").mkdir(parents=True)
    for i in range(n):
        nxt = (i + 1) % n if cycle else i + 1
        deps = [f"intent:n{nxt:05d}"] if cycle or i + 1 < n else []
        _write_intent(root, f"FEAT-{i:04d}-n{i:05d}.md", f"n{i:05d}", deps)
    return root


@pytest.mark.parametrize("cycle", [False, True])
def test_a_chain_or_cycle_of_2001_intents_never_crashes(tmp_path: pathlib.Path, cycle: bool) -> None:
    """Deep input gives a result or ``result_too_large``, never a crash (AC-0005)."""
    root = _deep_corpus(tmp_path, 2001, cycle=cycle)
    result, code = _q(root, "--id", "intent:n00000", "--direction", "both", "--depth", "2001")
    assert code == 1 and result["error"]["code"] == "result_too_large"
    big = {"max_intents": 10_000, "max_edges": 10_000, "max_result_bytes": 50_000_000}
    result, code = _q(root, "--id", "intent:n00000", "--direction", "both", "--depth", "2001", limits=big)
    assert code == 0 and len(result["intents"]) == 2001
    cycles = [d for d in result["diagnostics"] if d["state"] == "cycle"]
    assert len(cycles) == (1 if cycle else 0)
    if cycle:
        assert len(cycles[0]["members"]) == 2001


# ---------------------------------------------------------------- text


def test_text_output_lists_scope_intents_edges_and_diagnostics() -> None:
    text, code = _q(_DEP, "--id", "intent:india", "--direction", "both", "--format", "text")
    assert code == 0
    assert text == (
        "dependencies of intent:india · direction both · depth 1\n"
        f"scope: {nav._DEPENDS_SCOPE}\n"
        "intents:\n  intent:india\n  intent:juliet\n  intent:kilo\n"
        "edges (waiting -> prerequisite):\n"
        "  intent:india -> intent:juliet\n  intent:juliet -> intent:kilo\n  intent:kilo -> intent:india\n"
        "diagnostics:\n"
        "  intent:india · dangling · intent:ghost\n"
        "  intent:india · kind_mismatch · capability:alpha\n"
        "  cycle · intent:india, intent:juliet, intent:kilo\n"
    )


def test_text_output_identifies_an_isolated_start_and_escapes_controls(tmp_path: pathlib.Path) -> None:
    text, _ = _q(_DEP, "--id", "capability:root-a", "--format", "text")
    assert "intents:\n  capability:root-a\nedges" in text
    root = _copy(tmp_path)
    _write_intent(root, "FEAT-0050-sierra.md", "sierra", ["intent:x‮"])
    text, code = _q(root, "--id", "intent:sierra", "--format", "text")
    assert code == 0
    assert "intent:sierra · unparseable · intent:x[U+202E]" in text
    assert "‮" not in text


# ---------------------------------------------------------------- safety and compatibility


def test_a_file_changed_between_the_two_reads_refuses(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Adding an intent between ``derive`` and the dependency read gives ``unsafe_input`` (AC-0004)."""
    root = _copy(tmp_path)
    graph_mod = nav._load_graph_mod()
    real = graph_mod.derive

    def derive_then_add(r: pathlib.Path) -> dict[str, Any]:
        graph = real(r)
        _write_intent(root, "FEAT-0051-tango.md", "tango", [])
        return graph  # type: ignore[no-any-return]

    monkeypatch.setattr(graph_mod, "derive", derive_then_add)
    result, code = _q(root, "--id", "intent:alpha")
    assert code == 1 and result["error"]["code"] == "unsafe_input"


def test_the_reread_finds_the_same_live_intents_as_derive_on_every_clean_corpus() -> None:
    """The re-read copies derive's admission, tombstone and identity rules (plan LLD)."""
    graph_mod = nav._load_graph_mod()
    checked = 0
    for manifest in sorted(_FIXTURES.glob("**/expected-outstanding.json")):
        root = manifest.parent
        try:
            graph = graph_mod.derive(root)
        except graph_mod.DerivationError:
            continue
        items, _, _ = nav._read_dependency_inputs(root, graph_mod, graph)
        assert set(items) == {n["id"] for n in graph["nodes"] if n["type"] == "intent"}, root
        checked += 1
    assert checked >= 3


def _tree_bytes(root: pathlib.Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_queries_leave_bytes_unchanged_and_ignore_workspace_toml(tmp_path: pathlib.Path) -> None:
    """Same result with workspace.toml absent, present, or unreadable; no byte changes (AC-0013)."""
    root = _copy(tmp_path)
    before = _tree_bytes(root)
    absent = _stable(_ok(root, "--id", "intent:india", "--direction", "both"))
    (root / "workspace.toml").write_text('[x]\nneeds = ["intent:alpha"]\n', encoding="utf-8")
    present = _stable(_ok(root, "--id", "intent:india", "--direction", "both"))
    (root / "workspace.toml").unlink()
    (root / "workspace.toml").mkdir()
    unreadable = _stable(_ok(root, "--id", "intent:india", "--direction", "both"))
    (root / "workspace.toml").rmdir()
    assert absent == present == unreadable
    assert _tree_bytes(root) == before


def _strip_depends(root: pathlib.Path) -> None:
    for p in (root / "docs" / "product" / "intents").glob("*.md"):
        text = p.read_text(encoding="utf-8")
        p.write_text("".join(line for line in text.splitlines(keepends=True)
                             if not line.startswith("- **Depends on:**")), encoding="utf-8")


@pytest.mark.parametrize(
    "argv",
    [
        ["--operation", "summary"],
        ["--operation", "tree"],
        ["--operation", "tree", "--format", "text"],
        ["--operation", "record", "--id", "intent:india"],
        ["--operation", "ancestors", "--id", "intent:golf"],
        ["--operation", "search", "--selectors", '{"level": "feature"}'],
        ["--operation", "outstanding"],
    ],
)
def test_existing_operations_ignore_dependency_headers(tmp_path: pathlib.Path, argv: list[str]) -> None:
    """Dependency headers, faulty ones included, change no other operation's result (AC-0012)."""
    with_deps = _copy(tmp_path / "a")
    without = _copy(tmp_path / "b")
    _strip_depends(without)
    a, ca = nav.run_query(with_deps, ["query", *argv])
    b, cb = nav.run_query(without, ["query", *argv])
    assert ca == cb == 0
    assert _stable(a) == _stable(b)
