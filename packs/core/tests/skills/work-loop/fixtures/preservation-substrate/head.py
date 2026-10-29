"""Head implementation of the preservation fixture substrate.

A corpus maps file names to text whose lines are ``def NAME``, ``call NAME``,
or ``value NAME``. This implementation also holds a node for each ``value`` line.
"""

from __future__ import annotations

from dataclasses import dataclass

ALL_KINDS = frozenset({"def", "call", "value"})
CODE_KINDS = frozenset({"def", "call"})


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
    synthetic: bool = False


class Graph:
    """Nodes and call edges built from a corpus."""

    def __init__(self, corpus: dict[str, str]) -> None:
        self.corpus: dict[str, str] = dict(corpus)
        self.nodes: dict[str, Node] = {}
        self.edges: set[tuple[str, str]] = set()
        self._seq = 0

    def load(self, skip_values: bool) -> Graph:
        """Parse every stored file and link all call sites."""
        for file, text in self.corpus.items():
            self._add(file, text, skip_values)
        self._relink(set(self.corpus), set())
        return self

    def _add(self, file: str, text: str, skip_values: bool) -> list[Node]:
        """Add the nodes of one file's text and return them."""
        added: list[Node] = []
        for line in text.splitlines():
            kind, _, name = line.strip().partition(" ")
            if kind not in ALL_KINDS or not name.strip():
                continue
            if kind == "value" and skip_values:
                continue
            self._seq += 1
            node = Node(f"{kind}:{file}:{self._seq}", kind, file, name.strip())
            self.nodes[node.id] = node
            added.append(node)
        return added

    def _drop(self, file: str, kinds: frozenset[str] | set[str]) -> list[Node]:
        """Remove a file's nodes of the given kinds and every edge that touches them."""
        dropped = [n for n in self.nodes.values() if n.file == file and n.kind in kinds]
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
        dropped = self._drop(file, ALL_KINDS)
        self.corpus[file] = text
        added = self._add(file, text, skip_values=False)
        affected = {n.name for n in (*dropped, *added) if n.kind == "def"}
        self._relink({file}, affected)
        invalidated = {n.id for n in (*dropped, *added) if n.kind != "call"}
        return invalidated  # noqa: RET504

    def remove(self, file: str) -> None:
        """Remove one file from the graph and the stored corpus."""
        self._drop(file, {"def", "call", "value"})
        self.corpus.pop(file, None)

    def rebuild(self) -> Graph:
        """Build a new graph from the stored corpus."""
        return Graph(self.corpus).load(skip_values=False)


def build(corpus: dict[str, str]) -> Graph:
    """Build a graph from a corpus."""
    return Graph(corpus).load(skip_values=False)


def resolve_call(graph: Graph, name: str) -> Resolution | None:
    """Resolve a call name to its first definition, or None."""
    candidates = sorted(
        (n for n in graph.nodes.values() if n.name == name and n.kind == "def"),
        key=lambda n: (n.file, n.id),
    )
    if not candidates:
        return None
    first = candidates[0]
    return Resolution(target=first.name, file=first.file, synthetic=False)


def search(
    graph: Graph, query: str, include_values: bool = False
) -> list[tuple[str, str, str]]:
    """Return (kind, file, name) for nodes named *query*; values only on request."""
    nodes = list(graph.nodes.values())
    hits = [(n.kind, n.file, n.name) for n in nodes if n.kind != "value" and n.name == query]
    if include_values:
        hits += [(n.kind, n.file, n.name) for n in nodes if n.kind == "value" and n.name == query]
    return hits
