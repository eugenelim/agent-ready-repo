"""Base implementation of the preservation fixture substrate.

A corpus maps file names to text whose lines are ``def NAME``, ``call NAME``,
or ``value NAME``. This implementation ignores ``value`` lines.
"""

from __future__ import annotations

from dataclasses import dataclass

KINDS = frozenset({"def", "call"})


@dataclass(frozen=True)
class Node:
    """One graph node: its identifier, kind, file, and name."""

    id: str
    kind: str
    file: str
    name: str


@dataclass(frozen=True)
class Resolution:
    """The public result of resolving a call name."""

    target: str
    file: str


class Graph:
    """Nodes and call edges built from a corpus."""

    def __init__(self, corpus: dict[str, str]) -> None:
        self.corpus: dict[str, str] = dict(corpus)
        self.nodes: dict[str, Node] = {}
        self.edges: set[tuple[str, str]] = set()
        self._seq = 0

    def load(self) -> Graph:
        """Parse every stored file and link all call sites."""
        for file, text in self.corpus.items():
            self._add(file, text)
        self._relink(set(self.corpus), set())
        return self

    def _add(self, file: str, text: str) -> list[Node]:
        """Add the nodes of one file's text and return them."""
        added: list[Node] = []
        for line in text.splitlines():
            kind, _, name = line.strip().partition(" ")
            if kind not in KINDS or not name.strip():
                continue
            self._seq += 1
            node = Node(f"{kind}:{file}:{self._seq}", kind, file, name.strip())
            self.nodes[node.id] = node
            added.append(node)
        return added

    def _drop(self, file: str) -> list[Node]:
        """Remove a file's nodes and every edge that touches them."""
        dropped = [n for n in self.nodes.values() if n.file == file]
        ids = {n.id for n in dropped}
        for node_id in ids:
            del self.nodes[node_id]
        self.edges = {e for e in self.edges if e[0] not in ids and e[1] not in ids}
        return dropped

    def _relink(self, files: set[str], names: set[str]) -> None:
        """Rebuild the edges of call sites in *files* or named in *names*."""
        defs: dict[str, list[str]] = {}
        for node in self.nodes.values():
            if node.kind == "def":
                defs.setdefault(node.name, []).append(node.id)
        calls = [
            n
            for n in self.nodes.values()
            if n.kind == "call" and (n.file in files or n.name in names)
        ]
        ids = {c.id for c in calls}
        self.edges = {e for e in self.edges if e[0] not in ids}
        for call in calls:
            for target in defs.get(call.name, []):
                self.edges.add((call.id, target))

    def update(self, file: str, text: str) -> set[str]:
        """Replace one file's text and return the invalidated node ids."""
        dropped = self._drop(file)
        self.corpus[file] = text
        added = self._add(file, text)
        affected = {n.name for n in (*dropped, *added) if n.kind == "def"}
        self._relink({file}, affected)
        return {n.id for n in (*dropped, *added) if n.kind != "call"}

    def remove(self, file: str) -> None:
        """Remove one file from the graph and the stored corpus."""
        self._drop(file)
        self.corpus.pop(file, None)

    def rebuild(self) -> Graph:
        """Build a new graph from the stored corpus."""
        return Graph(self.corpus).load()


def build(corpus: dict[str, str]) -> Graph:
    """Build a graph from a corpus."""
    return Graph(corpus).load()


def resolve_call(graph: Graph, name: str) -> Resolution | None:
    """Follow the edges of a name's call sites to the first definition, or None.

    An edge whose target node is gone raises ``KeyError``.
    """
    sites = {n.id for n in graph.nodes.values() if n.kind == "call" and n.name == name}
    targets = sorted(
        (graph.nodes[target] for source, target in graph.edges if source in sites),
        key=lambda n: (n.file, n.id),
    )
    if not targets:
        return None
    return Resolution(target=targets[0].name, file=targets[0].file)


def search(
    graph: Graph, query: str, include_values: bool = False
) -> list[tuple[str, str, str]]:
    """Return (kind, file, name) for nodes named *query*; values are never held."""
    return [(n.kind, n.file, n.name) for n in graph.nodes.values() if n.name == query]
