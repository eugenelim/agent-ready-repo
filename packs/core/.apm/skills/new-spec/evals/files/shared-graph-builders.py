"""Distinct full-build, incremental-build, and invalidation paths."""


def build_full(graph, parsed_files):
    for parsed_file in parsed_files:
        for node in parsed_file.declarations:
            graph.add_node(node)
    return graph


def apply_incremental(graph, changed_file):
    remove_file_nodes(graph, changed_file.file_id)
    for node in changed_file.declarations:
        graph.add_node(node)
    return graph


def invalidated_files(dependencies, changed_file_id: int) -> set[int]:
    return {caller for caller, targets in dependencies.items() if changed_file_id in targets}


def remove_file_nodes(graph, file_id: int) -> None:
    for node_id in [node.node_id for node in graph.nodes.values() if node.parent_file == file_id]:
        graph.remove_node(node_id)
