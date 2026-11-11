The blast radius of `parse_config` is 23 resolved dependents, with 4 references the indexer could not bind.

The search reached depth 12 and `depth_horizon_reached` is false, so the result is complete within the traversal budget. Treat the list as a floor because of the 4 unresolved references, not the depth.

Five dependents were read against source. Four call `parse_config` directly on the changing path; `RefundCalculator` reads an unrelated field and is not affected.

The graph is current with the working tree.
