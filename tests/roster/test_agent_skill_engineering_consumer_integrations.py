"""Roster suite for spec/agent-skill-engineering-consumer-integrations.

`work-loop` and `architect-design` each gain a bounded step that inlines its own
request to the installed agent-skill-engineering provider. This module is that
slice's construction test.

Every assertion carries an `external-comparison`, `same-slice` or
`authored-statement` label matching the spec's three criterion classes. AC3
carries two, because its task-kind set is external while its per-consumer
assignment is authored.

T0 records the merge-base version literals below; T1 adds the assertions.
"""

# --- T0: merge-base version literals -----------------------------------------
#
# AC10 requires each pack's version to be *strictly greater* than its literal
# here, so these are a floor, not an equality. They are literals rather than a
# read of `origin/main` because a test that read the remote would depend on
# fetch state and would not hold in a shallow clone or in CI, where
# `origin/main` may not be a local ref. Both roster precedents record the same
# reason: `test_cooling_scope_closure.py:1053-1058` and
# `test_thirty_day_cooling_and_retirement.py:1626-1629`.
#
# `core` moved twice while this contract was in review (2.21.0 -> 2.22.0 ->
# 2.23.0). Re-record all three if the branch is ever rebased past the pinned
# baseline; a stale floor lets an unbumped pack satisfy AC10.

MERGE_BASE_CORE_VERSION = "2.23.0"  # packs/core/pack.toml at merge base 236ae549c
MERGE_BASE_ARCHITECT_VERSION = "0.15.5"  # packs/architect/pack.toml at merge base 236ae549c
MERGE_BASE_ASE_VERSION = "0.4.0"  # packs/agent-skill-engineering/pack.toml at merge base 236ae549c
