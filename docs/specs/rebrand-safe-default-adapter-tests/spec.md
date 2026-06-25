# Spec: rebrand-safe-default-adapter-tests

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0004 (single-constant enterprise rebrand)
- **Brief:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

`Mode: light (no risk trigger fired)` — test-only change, no production code, no
structural or public-interface change.

## Objective

ADR-0004 makes `scope.DEFAULT_ADAPTER` the single-constant enterprise-rebrand
lever: flip the constant and both install scopes follow. The resolver honours it
and is already proven rebrand-safe by monkeypatch tests. But a handful of
default-*fallback* unit assertions in
`test_resolve_user_scope_target_adapter.py` hardcode the literal `"claude-code"`
where they mean "the resolver returned `DEFAULT_ADAPTER`". A downstream rebrand
that flips the constant breaks those assertions even though the behaviour they
test is correct. The user here is the maintainer of a rebranded/downstream
distribution (and anyone reading the upstream tests): after this change, the
genuine default-fallback assertions track `DEFAULT_ADAPTER` instead of a magic
string, so the rebrand is zero-churn for them and the one assertion that *does*
pin the upstream default is unambiguous.

## Acceptance Criteria

- [x] **AC1** — Every assertion in `test_resolve_user_scope_target_adapter.py`
  that checks the resolver fell back to `DEFAULT_ADAPTER` (greenfield-default-in-list
  and legacy-heuristic paths, user and repo scope) references the
  `DEFAULT_ADAPTER` constant rather than the literal `"claude-code"`.
- [x] **AC2** — Assertions whose literal value is genuinely the contract are
  left unchanged: probe results (a specific `~/.<ide>/` was populated), explicit
  `--adapter` round-trips, and fall-back-to-`allowed_adapters[0]` cases (where
  `"claude-code"` is the first allowed adapter, not the default).
- [x] **AC3** — The upstream-default pin `test_default_adapter_value_unchanged`
  keeps its literal `assert DEFAULT_ADAPTER == "claude-code"` and carries a
  one-line note that this is the single assertion a downstream rebrand flips.
- [x] **AC4** — Flipping `scope.DEFAULT_ADAPTER` to a non-claude-code value
  leaves every AC1 assertion green; only the AC3 pin fails. Verified by a
  temporary local flip, then reverted.
- [x] **AC5** — The agentbundle unit suite is green
  (`pytest packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py`
  and the broader unit run).

## Notes

The sibling files `test_resolve_target_adapter_user_config.py` and
`test_install_argparse_adapter_flag.py` were inspected and need no change: the
former's only default-fallback assertion already references `DEFAULT_ADAPTER`
and its other `"claude-code"` literals are probe/explicit results; the latter's
are explicit `--adapter` round-trips. No new parametrized rebrand test is added
— the value-tracking coverage (the resolved adapter actually follows a flipped
`DEFAULT_ADAPTER`) already exists via the in-file monkeypatch tests
(`test_greenfield_monkeypatch_default_to_kiro`,
`test_repo_scope_legacy_heuristic_honors_monkey_patched_default`). (The
parametrized `test_repo_scope_adapter_flag_admits_all_shipped_adapters` pins
explicit `--adapter` admissibility, not default-following, so it is not part of
this coverage claim.)
