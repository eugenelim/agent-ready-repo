The blast radius of `parse_config` is 23 resolved dependents, with 4 references the indexer could not bind.

The CLI traverses to a fixed depth of 12 and does not report whether it reached that limit, so treat the list as a floor rather than a total.

Five dependents were read against source. Four call `parse_config` directly on the changing path; `RefundCalculator` reads an unrelated field and is unaffected.

The graph is current with the working tree.
