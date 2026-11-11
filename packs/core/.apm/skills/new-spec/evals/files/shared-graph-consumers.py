"""Existing generic consumers of the graph and its name index."""


def resolve_call(graph, callee_name: str):
    candidates = [graph.nodes[node_id] for node_id in graph.name_index.get(callee_name, [])]
    return [node for node in candidates if node.kind in {"function", "method"}]


def search(graph, query: str | None = None, include_values: bool = False):
    nodes = graph.nodes.values()
    if not include_values:
        nodes = (node for node in nodes if node.kind != "value")
    if query:
        nodes = (node for node in nodes if query.casefold() in node.name.casefold())
    return sorted(nodes, key=lambda node: (rank(graph, node.node_id), node.name))


def rank(graph, node_id: int) -> int:
    return sum(1 for node in graph.nodes.values() if node.parent_file == node_id)
