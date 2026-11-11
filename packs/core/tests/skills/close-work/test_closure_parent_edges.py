"""Descendant closure takes its children from the intent-graph derivation.

Covers AC-0004, AC-0005, AC-0009 (decision part), AC-0010, AC-0012, AC-0013, and
AC-0018 of ``docs/specs/close-work-intent-graph-convergence/``, and one
integration test that runs with no seams injected.

Every fixture is a temporary corpus under ``tmp_path`` laid out as the
repository lays it out, so the default graph provider and the default confined
reader both run. The delivery resolver snapshot is injected where a brief or
spec terminus is involved.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "close-work" / "scripts"
)
_CLOSURE_INDEX = _SCRIPTS / "closure_index.py"
_INTENT_GRAPH = _SCRIPTS / "intent_graph.py"


def _load(key: str, path: Path):
    """Load a close-work script by absolute path under a unique sys.modules key."""
    spec = importlib.util.spec_from_file_location(key, path)
    assert spec and spec.loader, f"no module at {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index__parent_edges_t2", _CLOSURE_INDEX)

_FRESH = lambda: True  # noqa: E731 - the freshness seam is not under test here


# ── Fixture corpus helpers ────────────────────────────────────────────────────


def _dirs(root: Path) -> tuple[Path, Path, Path]:
    intents = root / "docs" / "product" / "intents"
    briefs = root / "docs" / "product" / "briefs"
    specs = root / "docs" / "specs"
    for d in (intents, briefs, specs):
        d.mkdir(parents=True, exist_ok=True)
    return intents, briefs, specs


def _intent(
    root: Path,
    slug: str,
    *,
    status: str = "Accepted",
    parent: str | list[str] | None = None,
    decomposed: str | None = None,
    kind: str | None = None,
    level: str | None = None,
    tombstone: bool = False,
) -> Path:
    """Write one intent file; ``parent`` may repeat to make a multi-valued field."""
    intents, _, _ = _dirs(root)
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if kind:
        lines.append(f"- **Kind:** {kind}")
    if level:
        lines.append(f"- **Level:** {level}")
    parents = [parent] if isinstance(parent, str) else (parent or [])
    lines += [f"- **Parent intent:** {p}" for p in parents]
    if decomposed:
        lines.append(f"- **Decomposed:** 2026-10-01 {decomposed}")
    if tombstone:
        lines.append("- **Tombstone:** retired")
    path = intents / f"{slug}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _brief(root: Path, slug: str, *, status: str = "Executing", parent: str | None = None) -> Path:
    _, briefs, _ = _dirs(root)
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** {parent}")
    path = briefs / f"{slug}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _spec(root: Path, slug: str, *, status: str = "Implementing", brief: str | None = None) -> Path:
    _, _, specs = _dirs(root)
    (specs / slug).mkdir(parents=True, exist_ok=True)
    lines = [f"- **Status:** {status}"]
    if brief:
        lines.append(f"- **Brief:** brief:{brief}")
    path = specs / slug / "spec.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _snapshot(relations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """A minimal valid delivery snapshot; artifact paths follow the canonical grammar."""
    rels = relations or []
    arts: dict[str, str] = {}
    for rel in rels:
        for key, prefix, tmpl in (
            ("spec", "spec:", "docs/specs/{slug}/spec.md"),
            ("brief", "brief:", "docs/product/briefs/{slug}.md"),
        ):
            val = rel.get(key, "")
            if val.startswith(prefix):
                arts[val] = tmpl.format(slug=val[len(prefix):])
    return {
        "schema_version": 1,
        "complete": True,
        "relations": rels,
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": arts,
    }


def _direct(intent_slug: str, spec_slug: str) -> dict[str, Any]:
    return {
        "type": "direct-delivery",
        "route": "spec",
        "intent": f"intent:{intent_slug}",
        "spec": f"spec:{spec_slug}",
        "basis": {"intent": "Decomposed", "spec": "Discovery"},
    }


def _coord(intent_slug: str, brief_slug: str, spec_slug: str) -> dict[str, Any]:
    return {
        "type": "coordinated-delivery",
        "route": "brief",
        "intent": f"intent:{intent_slug}",
        "brief": f"brief:{brief_slug}",
        "spec": f"spec:{spec_slug}",
        "basis": {"brief": "Parent intent", "intent": "Decomposed", "spec": "Brief"},
    }


def _check(root: Path, slug: str, terminus: str = "children", **seams: Any):
    """Run the closure decision for an Accepted ancestor with no other seam injected."""
    return ci.check_ancestor_closure(
        slug, "Accepted", terminus, root, _freshness_checker=_FRESH, **seams
    )


def _live_names(verdict: Any) -> set[str]:
    assert isinstance(verdict, ci.ClosureNotEligible), verdict
    return {slug for slug, _ in verdict.live_descendants}


# ── AC-0004: one fixture per prefix and the path form ────────────────────────

_PREFIX_CASES = [
    pytest.param("intent:{p}", {}, id="intent"),
    pytest.param("capability:{p}", {"level": "capability"}, id="capability"),
    pytest.param("outcome:{p}", {"kind": "outcome"}, id="outcome"),
    pytest.param("opportunity:{p}", {"kind": "opportunity"}, id="opportunity"),
    pytest.param("docs/product/intents/{p}.md", {}, id="path"),
]


@pytest.mark.parametrize("value,ancestor_attrs", _PREFIX_CASES)
def test_ac0004_children_are_the_intents_whose_edge_resolves_to_the_ancestor(
    tmp_path: Path, value: str, ancestor_attrs: dict[str, str]
) -> None:
    _intent(tmp_path, "anc", decomposed="children", **ancestor_attrs)
    _intent(tmp_path, "child-live", parent=value.format(p="anc"))
    _intent(tmp_path, "unrelated")  # no parent edge: never a child

    verdict = _check(tmp_path, "anc")

    assert _live_names(verdict) == {"child-live"}
    assert verdict.live_descendants == (("child-live", "Accepted"),)


# ── AC-0005: a tombstone is never a descendant ───────────────────────────────


def test_ac0005_tombstone_naming_the_ancestor_is_not_a_descendant(tmp_path: Path) -> None:
    _intent(tmp_path, "anc", decomposed="children")
    _intent(tmp_path, "gone", parent="intent:anc", tombstone=True)
    _intent(tmp_path, "live", parent="intent:anc")

    closure = ci._build_descendant_closure("anc", "children", tmp_path)

    assert set(closure) == {("intent", "live")}
    assert _live_names(_check(tmp_path, "anc")) == {"live"}


# ── AC-0018: kind and slug tell artifacts apart ──────────────────────────────


def test_ac0018_intent_and_brief_sharing_a_slug_are_both_descendants(tmp_path: Path) -> None:
    _intent(tmp_path, "p", decomposed="children")
    _intent(tmp_path, "x", status="Fulfilled", parent="intent:p", decomposed="brief")
    _brief(tmp_path, "x", status="Executing", parent="intent:x")
    _spec(tmp_path, "x-feature", status="Shipped", brief="x")
    snap = _snapshot([_coord("x", "x", "x-feature")])

    closure = ci._build_descendant_closure(
        "p", "children", tmp_path, _snapshot_provider=lambda _r: snap
    )
    verdict = _check(tmp_path, "p", _snapshot_provider=lambda _r: snap)

    assert {("intent", "x"), ("brief", "x"), ("spec", "x-feature")} == set(closure)
    # The intent is terminal; only the brief keeps the verdict not-eligible.
    assert verdict == ci.ClosureNotEligible("p", (("x", "Executing"),))


def test_ac0018_intent_and_spec_sharing_a_slug_are_both_descendants(tmp_path: Path) -> None:
    _intent(tmp_path, "p", decomposed="children")
    _intent(tmp_path, "x", status="Fulfilled", parent="intent:p", decomposed="spec")
    _spec(tmp_path, "x", status="Implementing")
    snap = _snapshot([_direct("x", "x")])

    closure = ci._build_descendant_closure(
        "p", "children", tmp_path, _snapshot_provider=lambda _r: snap
    )
    verdict = _check(tmp_path, "p", _snapshot_provider=lambda _r: snap)

    assert set(closure) == {("intent", "x"), ("spec", "x")}
    assert verdict == ci.ClosureNotEligible("p", (("x", "Implementing"),))


# ── AC-0009 (decision part): a failed derivation refuses ─────────────────────


def test_ac0009_corpus_fault_refuses_with_the_derivation_code(tmp_path: Path) -> None:
    _intent(tmp_path, "anc", decomposed="children")
    _intent(tmp_path, "child", parent="intent:anc")
    intents, _, _ = _dirs(tmp_path)
    (intents / "no-slug.md").write_text("- **Status:** Accepted\n", encoding="utf-8")

    verdict = _check(tmp_path, "anc")  # default provider: the real copy runs

    assert verdict == ci.ClosureRefuse("anc", "intent-graph-unavailable: malformed_record")


def test_ac0009_missing_copy_refuses_as_copy_unavailable(tmp_path: Path) -> None:
    _intent(tmp_path, "anc", decomposed="children")
    provider = functools.partial(
        ci._run_intent_graph, _graph_module_path=tmp_path / "absent" / "intent_graph.py"
    )

    verdict = _check(tmp_path, "anc", _graph_provider=provider)

    assert verdict == ci.ClosureRefuse("anc", "intent-graph-unavailable: copy-unavailable")


def test_ac0009_linked_copy_refuses_as_copy_unavailable(tmp_path: Path) -> None:
    _intent(tmp_path, "anc", decomposed="children")
    link = tmp_path / "linked_graph.py"
    link.symlink_to(_INTENT_GRAPH)
    provider = functools.partial(ci._run_intent_graph, _graph_module_path=link)

    verdict = _check(tmp_path, "anc", _graph_provider=provider)

    assert verdict == ci.ClosureRefuse("anc", "intent-graph-unavailable: copy-unavailable")


def test_ac0009_any_other_failure_is_copy_unavailable_and_an_own_class_keeps_its_code(
    tmp_path: Path,
) -> None:
    _intent(tmp_path, "anc", decomposed="children")

    def boom(_root: Path) -> dict[str, Any]:
        raise RuntimeError("derivation exploded")

    class DerivationError(Exception):  # recognised by class name, not identity
        code = "unsafe_input"

    def own_class(_root: Path) -> dict[str, Any]:
        raise DerivationError("x")

    assert _check(tmp_path, "anc", _graph_provider=boom) == ci.ClosureRefuse(
        "anc", "intent-graph-unavailable: copy-unavailable"
    )
    assert _check(tmp_path, "anc", _graph_provider=own_class) == ci.ClosureRefuse(
        "anc", "intent-graph-unavailable: unsafe_input"
    )


# ── AC-0010: a refused pointer that names a children-terminus intent ─────────

_NAMING_VALUES = [
    pytest.param("intent:{t}", id="prefixed"),
    pytest.param("{t}", id="bare-slug"),
    pytest.param("docs/product/intents/{t}.md", id="path"),
]


def _chain(root: Path, *, capability_leaf: bool = False) -> str:
    """r (children) -> c1 (children) -> c2 (children); returns the nested slug."""
    _intent(root, "r", decomposed="children")
    _intent(root, "c1", parent="intent:r", decomposed="children")
    _intent(
        root, "c2", parent="intent:c1", decomposed="children",
        level="capability" if capability_leaf else None,
    )
    return "c2"


def _place_refusal(root: Path, state: str, placement: str) -> str:
    """Add a refused ``Parent intent`` edge naming the target; return the evaluated slug."""
    if placement == "ancestor":
        _intent(root, "r", decomposed="children", level="capability" if state == "kind_mismatch" else None)
        _intent(root, "r-child", parent="intent:r" if state != "kind_mismatch" else "capability:r")
        target, ancestor = "r", "r"
    else:
        target = _chain(root, capability_leaf=state == "kind_mismatch")
        ancestor = "r"
    if state == "kind_mismatch":
        _intent(root, "z", parent=f"intent:{target}")  # target is a capability
    elif state == "multiple_values":
        _intent(root, "z", parent=[f"intent:{target}", "intent:elsewhere"])
    else:
        assert state == "cycle"
        if placement == "ancestor":
            # q -> r and r -> q: the lower slug's edge (q, naming r) is refused.
            _intent(root, "a-q", parent="intent:r")
            _intent(root, "r", decomposed="children", parent="intent:a-q")
        else:
            # a-x -> c2 -> c1 -> r -> a-x: a-x sorts first, so its edge, naming c2, is refused.
            _intent(root, "a-x", parent="intent:c2")
            _intent(root, "r", decomposed="children", parent="intent:a-x")
    return ancestor


@pytest.mark.parametrize("placement", ["ancestor", "nested"])
@pytest.mark.parametrize("state", ["kind_mismatch", "multiple_values", "cycle"])
def test_ac0010_refused_edge_naming_a_children_intent_refuses(
    tmp_path: Path, state: str, placement: str
) -> None:
    ancestor = _place_refusal(tmp_path, state, placement)

    verdict = _check(tmp_path, ancestor)

    assert verdict == ci.ClosureRefuse(ancestor, "parent-edge-refused")


@pytest.mark.parametrize("value", _NAMING_VALUES)
@pytest.mark.parametrize("placement", ["ancestor", "nested"])
def test_ac0010_multiple_values_names_an_intent_by_any_one_value(
    tmp_path: Path, value: str, placement: str
) -> None:
    target = "r" if placement == "ancestor" else _chain(tmp_path)
    if placement == "ancestor":
        _intent(tmp_path, "r", decomposed="children")
        _intent(tmp_path, "r-child", parent="intent:r")
    _intent(tmp_path, "z", parent=[value.format(t=target), "intent:elsewhere"])

    assert _check(tmp_path, "r") == ci.ClosureRefuse("r", "parent-edge-refused")


def test_ac0010_out_of_type_value_does_not_name_the_intent(tmp_path: Path) -> None:
    _intent(tmp_path, "a", decomposed="children")
    _intent(tmp_path, "child", parent="intent:a")
    _intent(tmp_path, "z", parent="brief:a")  # out_of_type: a brief pointer, not intent a

    graph = ci._run_intent_graph(tmp_path)
    refused = [e for e in graph["edges"] if e.get("state") == "out_of_type"]
    verdict = _check(tmp_path, "a")

    assert [e["from"] for e in refused] == ["intent:z"]  # the refusal exists...
    assert verdict == ci.ClosureNotEligible("a", (("child", "Accepted"),))  # ...and does not bear


def test_ac0010_a_refusal_naming_a_non_children_intent_does_not_refuse(tmp_path: Path) -> None:
    _intent(tmp_path, "a", decomposed="children")
    _intent(tmp_path, "child", parent="intent:a", decomposed="spec")
    _intent(tmp_path, "z", parent=["intent:child", "intent:elsewhere"])  # names a spec-terminus intent
    snap = _snapshot()

    verdict = _check(tmp_path, "a", _snapshot_provider=lambda _r: snap)

    assert not isinstance(verdict, ci.ClosureRefuse) or verdict.reason != "parent-edge-refused"


# ── AC-0012: the derivation runs once, and only when a children terminus is reached ──


def _counting_provider() -> tuple[Any, list[int]]:
    calls: list[int] = []

    def provider(root: Path) -> dict[str, Any]:
        calls.append(1)
        return ci._run_intent_graph(root)

    return provider, calls


def test_ac0012_one_run_for_a_children_decision(tmp_path: Path) -> None:
    _intent(tmp_path, "anc", decomposed="children")
    _intent(tmp_path, "child", parent="intent:anc")
    provider, calls = _counting_provider()

    _check(tmp_path, "anc", _graph_provider=provider)

    assert len(calls) == 1


def test_ac0012_one_run_for_two_nested_children_levels(tmp_path: Path) -> None:
    _chain(tmp_path)
    provider, calls = _counting_provider()

    verdict = _check(tmp_path, "r", _graph_provider=provider)

    assert _live_names(verdict) == {"c1", "c2"}
    assert len(calls) == 1


@pytest.mark.parametrize("terminus", ["brief", "spec", "closed-empty", "direct-light"])
def test_ac0012_no_run_when_no_children_terminus_is_reached(tmp_path: Path, terminus: str) -> None:
    _intent(tmp_path, "anc", decomposed=terminus)
    _brief(tmp_path, "b", parent="intent:anc")
    _spec(tmp_path, "s", brief="b")
    snap = _snapshot([_coord("anc", "b", "s")] if terminus == "brief" else [_direct("anc", "s")] if terminus == "spec" else [])
    provider, calls = _counting_provider()

    _check(tmp_path, "anc", terminus, _snapshot_provider=lambda _r: snap, _graph_provider=provider)

    assert calls == []


# ── AC-0013: at most one open inside the derivation and one by close-work ────


def test_ac0013_diamond_is_opened_at_most_once_by_each_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # p -> ca, cb; both name the same spec, so the spec has two paths to it.
    p_path = _intent(tmp_path, "p", decomposed="children")
    ca = _intent(tmp_path, "ca", parent="intent:p", decomposed="spec", status="Fulfilled")
    cb = _intent(tmp_path, "cb", parent="intent:p", decomposed="spec", status="Fulfilled")
    shared = _spec(tmp_path, "shared", status="Implementing")
    snap = _snapshot([_direct("ca", "shared"), _direct("cb", "shared")])

    own_reads: Counter[str] = Counter()
    confined_reader = ci._make_confined_reader(tmp_path)

    def counting_reader(path: Path) -> str:
        own_reads[str(path)] += 1
        return confined_reader(path)

    derivation_reads: Counter[str] = Counter()
    copy = _load("core_close_work_intent_graph__t2_counting", _INTENT_GRAPH)
    fs = copy._get_file_safety()
    real_read = fs.read_confined_regular_file

    def counting_confined_read(root: Path, path: Path, *args: Any, **kwargs: Any) -> bytes:
        derivation_reads[str(path)] += 1
        return real_read(root, path, *args, **kwargs)

    monkeypatch.setattr(fs, "read_confined_regular_file", counting_confined_read)

    verdict = ci.check_ancestor_closure(
        "p", "Accepted", "children", tmp_path,
        _reader=counting_reader,
        _freshness_checker=_FRESH,
        _snapshot_provider=lambda _r: snap,
        _graph_provider=lambda root: copy.derive(root),
    )
    assert verdict == ci.ClosureNotEligible("p", (("shared", "Implementing"),))
    assert own_reads and derivation_reads
    assert max(own_reads.values()) == 1
    assert max(derivation_reads.values()) == 1
    # close-work's own reader opens only artifacts it adds to the descendant set.
    assert set(own_reads) == {str(ca), str(cb), str(shared)}
    assert str(p_path) not in own_reads

    descendants = ci._build_descendant_closure(
        "p", "children", tmp_path,
        _snapshot_provider=lambda _r: snap,
        _graph_provider=lambda root: copy.derive(root),
    )
    assert set(descendants) == {("intent", "ca"), ("intent", "cb"), ("spec", "shared")}


# ── Upward walk (AC-0006 to AC-0009, AC-0011, AC-0017) ───────────────────────


def _walk(root: Path, slug: str, kind: str, fields: dict[str, str] | None = None, **seams: Any):
    """Run the ancestor walk with no seam but the ones a case names."""
    return ci.resolve_intent_ancestors(slug, kind, fields or {}, root, **seams)


def _brief_multi(root: Path, slug: str, parents: list[str]) -> None:
    _, briefs, _ = _dirs(root)
    lines = [f"- **Slug:** {slug}", "- **Status:** Executing"]
    lines += [f"- **Parent intent:** {v}" for v in parents]
    (briefs / f"{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _prov(spec_slug: str, intent_slug: str) -> dict[str, Any]:
    return {
        "subject": f"spec:{spec_slug}",
        "field": "Discovery",
        "intent": f"intent:{intent_slug}",
        "target": f"intent:{intent_slug}",
    }


def _four_level_chain(root: Path) -> None:
    """Each hop uses a different prefix; each ancestor carries a different terminus."""
    _intent(root, "a1", level="capability", status="Accepted (2026-10-01)",
            parent="outcome:a2", decomposed="children")
    _intent(root, "a2", kind="outcome", status="Accepted (2026-10-02)",
            parent="opportunity:a3", decomposed="brief")
    _intent(root, "a3", kind="opportunity", status="Fulfilled (2026-10-03)",
            parent="intent:a4", decomposed="spec")
    _intent(root, "a4", status="Accepted (2026-10-04)", decomposed="closed-empty")


_CHAIN = [
    ("a1", "Accepted (2026-10-01)", "children"),
    ("a2", "Accepted (2026-10-02)", "brief"),
    ("a3", "Fulfilled (2026-10-03)", "spec"),
    ("a4", "Accepted (2026-10-04)", "closed-empty"),
]


def test_ac0006_four_level_chain_from_an_intent(tmp_path: Path) -> None:
    _four_level_chain(tmp_path)
    _intent(tmp_path, "bottom", parent="capability:a1")

    assert _walk(tmp_path, "bottom", "intent") == _CHAIN


def test_ac0006_four_level_chain_from_a_brief(tmp_path: Path) -> None:
    _four_level_chain(tmp_path)
    _brief(tmp_path, "bottom", parent="capability:a1")

    assert _walk(tmp_path, "bottom", "brief") == _CHAIN


def test_ac0017_artifact_absent_from_the_corpus_is_refused(tmp_path: Path) -> None:
    _dirs(tmp_path)
    _intent(tmp_path, "other")
    for kind in ("intent", "brief"):
        with pytest.raises(ci._ClosureDeliveryRefusal, match="artifact-not-in-graph"):
            _walk(tmp_path, "ghost", kind, {"Parent intent": "intent:other"})


def test_ac0017_a_brief_slug_is_not_found_among_intents(tmp_path: Path) -> None:
    _intent(tmp_path, "same")
    with pytest.raises(ci._ClosureDeliveryRefusal, match="artifact-not-in-graph"):
        _walk(tmp_path, "same", "brief")


def test_ac0017_the_on_disk_edge_wins_over_the_callers_fields(tmp_path: Path) -> None:
    _intent(tmp_path, "real", decomposed="children")
    _intent(tmp_path, "fake", decomposed="spec")
    _intent(tmp_path, "walked", parent="intent:real")

    ancestors = _walk(tmp_path, "walked", "intent", {"Parent intent": "intent:fake"})

    assert ancestors == [("real", "Accepted", "children")]


def test_ac0007_spec_walk_is_depth_first_and_returns_a_shared_grandparent_once(
    tmp_path: Path,
) -> None:
    _intent(tmp_path, "gg", decomposed="children")
    _intent(tmp_path, "g", parent="intent:gg", decomposed="children")
    _intent(tmp_path, "a1", parent="intent:g", decomposed="spec")
    _intent(tmp_path, "a2", parent="intent:g", decomposed="spec")
    _intent(tmp_path, "d", parent="intent:g", decomposed="closed-empty")
    snap = _snapshot([_direct("a1", "sp"), _direct("a2", "sp")])
    snap["provenance"] = [_prov("sp", "d")]

    ancestors = _walk(tmp_path, "sp", "spec", _snapshot_provider=lambda _r: snap)

    assert [a[0] for a in ancestors] == ["a1", "g", "gg", "a2", "d"]


def test_ac0007_first_hop_without_a_node_is_refused(tmp_path: Path) -> None:
    _dirs(tmp_path)
    snap = _snapshot([_direct("ghost", "sp")])
    with pytest.raises(ci._ClosureDeliveryRefusal, match="artifact-not-in-graph"):
        _walk(tmp_path, "sp", "spec", _snapshot_provider=lambda _r: snap)


def test_ac0008_brief_whose_parent_shares_its_slug_returns_that_intent(tmp_path: Path) -> None:
    _intent(tmp_path, "x", decomposed="brief")
    _brief(tmp_path, "x", parent="intent:x")

    assert _walk(tmp_path, "x", "brief") == [("x", "Accepted", "brief")]


def test_ac0008_spec_whose_snapshot_intent_shares_its_slug_returns_that_intent(
    tmp_path: Path,
) -> None:
    _intent(tmp_path, "y", decomposed="spec")
    snap = _snapshot([_direct("y", "y")])

    ancestors = _walk(tmp_path, "y", "spec", _snapshot_provider=lambda _r: snap)

    assert ancestors == [("y", "Accepted", "spec")]


@pytest.mark.parametrize("kind", ["intent", "brief"])
def test_ac0009_corpus_fault_refuses_the_walk_with_the_derivation_code(
    tmp_path: Path, kind: str
) -> None:
    _intent(tmp_path, "top")
    (_dirs(tmp_path)[0] / "no-slug.md").write_text("- **Status:** Accepted\n", encoding="utf-8")
    (_intent if kind == "intent" else _brief)(tmp_path, "w", parent="intent:top")

    with pytest.raises(
        ci._ClosureDeliveryRefusal, match="intent-graph-unavailable: malformed_record"
    ):
        _walk(tmp_path, "w", kind)


def _refused_value(root: Path, state: str, tag: str) -> list[str]:
    """Return the ``Parent intent`` value(s) producing *state*; write any target they need."""
    if state == "dangling":
        return [f"intent:nope-{tag}"]
    if state == "retired_target":
        _intent(root, f"gone-{tag}", tombstone=True)
        return [f"intent:gone-{tag}"]
    if state == "kind_mismatch":
        _intent(root, f"plain-{tag}")  # an intent, named as a capability
        return [f"capability:plain-{tag}"]
    if state == "out_of_type":
        return [f"brief:other-{tag}"]
    if state == "multiple_values":
        _intent(root, f"m1-{tag}")
        _intent(root, f"m2-{tag}")
        return [f"intent:m1-{tag}", f"intent:m2-{tag}"]
    assert state == "unparseable"
    return ["wibble:x"]


def _write(root: Path, kind: str, slug: str, parents: list[str], **kw: Any) -> None:
    if kind == "brief":
        _brief_multi(root, slug, parents)
    else:
        _intent(root, slug, parent=parents, **kw)


_INTENT_STATES = [
    "dangling", "retired_target", "kind_mismatch", "out_of_type",
    "multiple_values", "cycle", "unparseable",
]
_BRIEF_STATES = ["dangling", "retired_target", "multiple_values", "unparseable"]


def _place_walk_refusal(root: Path, kind: str, state: str, placement: str) -> None:
    if state == "cycle":
        if placement == "walked":
            # a-w -> b-w -> a-w: the lowest slug's edge is the refused one.
            _intent(root, "a-w", parent="intent:b-w")
            _intent(root, "b-w", parent="intent:a-w")
        else:
            _intent(root, "z-w", parent="intent:a-m")
            _intent(root, "a-m", parent="intent:b-m")
            _intent(root, "b-m", parent="intent:a-m")
        return
    if placement == "walked":
        _write(root, kind, "w", _refused_value(root, state, "w"))
    else:
        _intent(root, "mid", parent=_refused_value(root, state, "m"))
        _write(root, kind, "w", ["intent:mid"])


@pytest.mark.parametrize("placement", ["walked", "reached"])
@pytest.mark.parametrize("state", _INTENT_STATES)
def test_ac0011_refused_intent_parent_edge_refuses_the_walk(
    tmp_path: Path, state: str, placement: str
) -> None:
    _place_walk_refusal(tmp_path, "intent", state, placement)
    start = {"walked": "a-w" if state == "cycle" else "w",
             "reached": "z-w" if state == "cycle" else "w"}[placement]

    with pytest.raises(ci._ClosureDeliveryRefusal, match="parent-edge-refused"):
        _walk(tmp_path, start, "intent")


@pytest.mark.parametrize("placement", ["walked", "reached"])
@pytest.mark.parametrize("state", _BRIEF_STATES)
def test_ac0011_refused_brief_parent_edge_refuses_the_walk(
    tmp_path: Path, state: str, placement: str
) -> None:
    _place_walk_refusal(tmp_path, "brief", state, placement)

    with pytest.raises(ci._ClosureDeliveryRefusal, match="parent-edge-refused"):
        _walk(tmp_path, "w", "brief")


# ── Integration: no seams, one corpus ────────────────────────────────────────


def _write_integration_corpus(root: Path, *, brief_status: str) -> None:
    """Four typed prefixes, a path parent, a tombstone, same-slug intent and brief, three levels."""
    _intent(root, "top", kind="outcome", decomposed="children")
    _intent(root, "opp", kind="opportunity", parent="outcome:top", status="Fulfilled",
            decomposed="children")
    _intent(root, "cap", level="capability", parent="opportunity:opp", status="Fulfilled",
            decomposed="children")
    # feat shares its slug with the brief beneath it.
    _intent(root, "feat", level="feature", parent="capability:cap", status="Fulfilled",
            decomposed="brief")
    _intent(root, "by-path", parent="docs/product/intents/top.md", status="Fulfilled")
    _intent(root, "retired", parent="outcome:top", tombstone=True)  # live status would block
    _brief(root, "feat", status=brief_status, parent="intent:feat")
    _spec(root, "feat-spec", status="Shipped", brief="feat")


def test_closure_parent_edges_corpus(tmp_path: Path) -> None:
    """No seam but the freshness checker: the default copy, reader, and resolver run."""
    _write_integration_corpus(tmp_path, brief_status="Executing")

    not_eligible = _check(tmp_path, "top")
    assert not_eligible == ci.ClosureNotEligible("top", (("feat", "Executing"),))

    _brief(tmp_path, "feat", status="Shipped", parent="intent:feat")
    eligible = _check(tmp_path, "top")
    assert isinstance(eligible, ci.ClosureEligible), eligible

    # The upward walk runs with no seam but the resolver, over the same corpus.
    assert ci.resolve_intent_ancestors("by-path", "intent", {}, tmp_path) == [
        ("top", "Accepted", "children"),
    ]
    assert ci.resolve_intent_ancestors("feat", "brief", {}, tmp_path) == [
        ("feat", "Fulfilled", "brief"),
        ("cap", "Fulfilled", "children"),
        ("opp", "Fulfilled", "children"),
        ("top", "Accepted", "children"),
    ]

    closure = ci._build_descendant_closure("top", "children", tmp_path)
    assert set(closure) == {
        ("intent", "opp"), ("intent", "cap"), ("intent", "feat"), ("intent", "by-path"),
        ("brief", "feat"), ("spec", "feat-spec"),
    }
