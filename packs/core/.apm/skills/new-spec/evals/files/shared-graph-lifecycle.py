"""Containment is the lifecycle boundary used by updates and deletion."""


def attach_to_file(graph, file_id: int, node) -> None:
    node.parent_file = file_id
    graph.add_node(node)


def replace_file(graph, parsed_file, remove_file_nodes) -> None:
    remove_file_nodes(graph, parsed_file.file_id)
    for node in parsed_file.declarations:
        attach_to_file(graph, parsed_file.file_id, node)
