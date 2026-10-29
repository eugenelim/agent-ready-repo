"""A small code graph with definition, call, and value nodes."""

from dataclasses import dataclass, field

DEF = "def"
CALL = "call"
VALUE = "value"


@dataclass(frozen=True)
class Node:
    """One graph node."""

    name: str
    kind: str


@dataclass
class Graph:
    """Nodes built from source lines."""

    nodes: list[Node] = field(default_factory=list)


def build(lines: list[str]) -> Graph:
    """Build a graph from lines of the form `def x`, `call x`, or `value x`."""
    graph = Graph()
    for line in lines:
        kind, _, name = line.partition(" ")
        if kind in (DEF, CALL, VALUE):
            graph.nodes.append(Node(name.strip(), kind))
    return graph


def resolve_calls(graph: Graph) -> dict[str, list[Node]]:
    """Map each call name to the definition nodes it targets."""
    targets = [n for n in graph.nodes if n.kind == DEF]
    return {
        n.name: [t for t in targets if t.name == n.name]
        for n in graph.nodes
        if n.kind == CALL
    }


def search(graph: Graph, name: str, include_values: bool = False) -> list[Node]:
    """Return nodes whose name contains `name`; values need the explicit flag."""
    return [
        n
        for n in graph.nodes
        if name in n.name and (include_values or n.kind != VALUE)
    ]


def outline(graph: Graph) -> list[str]:
    """List every node as `kind name`, in build order."""
    return [f"{n.kind} {n.name}" for n in graph.nodes]
