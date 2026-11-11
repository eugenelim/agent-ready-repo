"""Current graph model before synthetic value nodes are added."""

from dataclasses import dataclass, field


@dataclass
class Node:
    node_id: int
    name: str
    kind: str
    parent_file: int | None = None


@dataclass
class Graph:
    nodes: dict[int, Node] = field(default_factory=dict)
    name_index: dict[str, list[int]] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        self.nodes[node.node_id] = node
        self.name_index.setdefault(node.name, []).append(node.node_id)

    def remove_node(self, node_id: int) -> None:
        node = self.nodes.pop(node_id)
        self.name_index[node.name].remove(node_id)
