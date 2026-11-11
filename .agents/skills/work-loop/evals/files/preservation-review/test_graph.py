"""Tests for the code graph."""

from graph import CALL, VALUE, build, resolve_calls, search

LINES = ["def run", "call run", "value limit", "call limit"]


def test_value_nodes_are_created_for_value_lines() -> None:
    """Each value line yields one value node."""
    graph = build(LINES)
    assert [n.name for n in graph.nodes if n.kind == VALUE] == ["limit"]


def test_ordinary_calls_resolve_to_definitions() -> None:
    """Calls resolve the same way the resolver reports them."""
    graph = build(LINES)
    expected = {
        n.name: resolve_calls(graph)[n.name] for n in graph.nodes if n.kind == CALL
    }
    assert resolve_calls(graph) == expected


def test_search_finds_definitions() -> None:
    """Search returns a matching definition node."""
    graph = build(LINES)
    assert [n.kind for n in search(graph, "run")] == ["def", "call"]
