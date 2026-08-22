## Blockers

**1. Gate-chain count is scoped to all `ci` targets, not the `build-check` route.** `tools/test-lint-ci-parity.py:219`. The new aggregation would still pass if the sole `tools/repo/build_gate_chain.py` invocation moved from `build-check`/`build-check-unleased` into another `ci` prerequisite such as `lint-ruff` or `test`, so it no longer proves AC2's "through `build-check`" invariant. Fix: Count gate-chain occurrences over the targets transitively reachable from `build-check` itself, and separately assert the `ci`-reachable total equals that build-check-route count.
