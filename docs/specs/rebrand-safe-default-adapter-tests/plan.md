# Plan: rebrand-safe-default-adapter-tests

Mode: light. Single logical task (no inter-task dependencies); verification is
goal-based (run the suite) plus one manual rebrand-property check.

## Declined-pattern register

- **Tempted to parametrize the default-fallback tests over the full shipped
  adapter set** — declining: the value-tracking coverage (resolved adapter
  follows a flipped `DEFAULT_ADAPTER`) already exists via the in-file monkeypatch
  tests (`test_greenfield_monkeypatch_default_to_kiro`,
  `test_repo_scope_legacy_heuristic_honors_monkey_patched_default`); adding more
  would re-test one behaviour with more values for no marginal coverage.
- **Tempted to move the rebrand assertions into per-adapter files "so we can
  take them out" downstream** — declining: constant-ref makes them pass under a
  rebrand unchanged, so there is nothing to take out; stripping would only lose
  coverage in the fork.
- **Tempted to add a module-level `DEFAULT_ADAPTER` and reuse it in the
  monkeypatch tests** — declining: those tests deliberately patch
  `agentbundle.scope.DEFAULT_ADAPTER` and read it via their own local binding;
  the module-level import is consumed only by the non-patching base tests.

## Tasks

### T1 — constant-ref the genuine default-fallback assertions

Verification: goal-based (`pytest` on the file).

- Add module-level `from agentbundle.scope import DEFAULT_ADAPTER`.
- Replace the literal in the seven default-fallback assertions (the resolver
  returned the default): `test_greenfield_returns_default_when_default_in_pack_list`,
  `test_legacy_v05_pack_with_agents_returns_default_adapter`,
  `test_legacy_v05_pack_without_agents_returns_claude_code`,
  `test_v06_pack_omitting_allowed_adapters_uses_legacy_heuristic`,
  `test_repo_scope_greenfield_returns_default_adapter`,
  `test_repo_scope_legacy_heuristic_for_pre_v07_pack` (two asserts).
- Drop the now-redundant `# DEFAULT_ADAPTER` trailing comment where present.
- **Bundled fix:** rename `test_legacy_v05_pack_without_agents_returns_claude_code`
  → `test_legacy_v05_pack_without_agents_returns_default_adapter` to match its
  `with_agents` sibling and the constant-ref'd assertion (same-file, same-concern,
  mechanical).

### T2 — label the upstream-default pin

Verification: goal-based.

- In `test_default_adapter_value_unchanged`, add a one-line note that this is the
  single assertion a downstream rebrand (ADR-0004) flips. Keep the literal.

### T3 — gates + rebrand-property check

- Run the unit file + the broader unit suite (green). ✓
- Temporarily set `scope.DEFAULT_ADAPTER = "kiro-ide"`, run the file: AC1
  assertions stay green, only the AC3 pin fails. Revert. ✓ (caught a real bug —
  the two greenfield-in-list lists now build from `DEFAULT_ADAPTER`.)
- **No changelog entry** — test-only, no user-visible behaviour change; the
  changelog is for user-visible changes and there is no CI changelog gate.

## Decisions surfaced

- **The three resolver test files are not in CI's curated path list** (only ~18
  of 86 `tests/unit/` files gate; see the self-documenting comment in
  `test_install_argparse_adapter_flag.py`). Pre-existing gap, not introduced
  here. The change still meets its goal — the downstream playbook runs full
  `pytest`. Wiring these into `build-check.yml` so the rebrand-safety enforces
  upstream too is a separate decision, left to the human.

## Changelog

- 2026-06-25 — Plan authored (light mode); T1 corrected mid-EXECUTE after the
  rebrand-property check failed two greenfield-in-list tests.
