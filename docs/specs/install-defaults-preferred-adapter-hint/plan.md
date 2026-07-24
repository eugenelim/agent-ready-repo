# Plan: Install-Defaults Preferred Adapter Hint

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three-file change following the `source_defaults.py` pattern for source
resolution:

1. **`source_defaults.py`** — two new functions: `_preferred_adapter_from_install_defaults(text)` (parse `[organization].preferred_adapter`, fail-soft → `None` for absent/blank/malformed) and `read_packaged_preferred_adapter()` (read packaged file, validate against shipped adapters, fail-hard `CatalogueError` on invalid non-blank, return `None` for absent/blank).

2. **`install.py`** — three touches: (a) new `preferred_adapter: str | None = None` parameter on `_resolve_target_adapter`, `_render_for_repo_scope`, and `_render_for_user_scope`; (b) new step 2.75 between step 2.5 (user-config) and step 3+4 (probe/default) in `_resolve_target_adapter`; (c) one `read_packaged_preferred_adapter()` read in `run()` with the result threaded to all call sites.

3. **Tests** — TDD stubs → green in two new test cases: parse/read tests appended to `test_source_defaults.py`; resolution tests in new `test_install_defaults_preferred_adapter.py`.

## Constraints

- ADR-0036 D3: no repo-scoped adapter hint; the org hint is from the packaged wheel only.
- RFC-0046: resolution is stateless; the hint is never written to state.
- Python 3.11 stdlib-only; no new dependency.

## Tasks

### T1: Parse and read functions in source_defaults.py

**Depends on:** none
**Touches:** `packages/agentbundle/agentbundle/source_defaults.py`, `packages/agentbundle/tests/unit/test_source_defaults.py`

**Tests (TDD — write red before implementation):**

```python
# test_preferred_adapter_from_install_defaults
def test_returns_adapter_for_valid_present_value():
    toml = '[organization]\npreferred_adapter = "claude-code"\n'
    assert _preferred_adapter_from_install_defaults(toml) == "claude-code"

def test_returns_none_for_absent_organization_table():
    toml = '[defaults]\nsource = "git+https://example.com/repo"\n'
    assert _preferred_adapter_from_install_defaults(toml) is None

def test_returns_none_for_absent_preferred_adapter_key():
    toml = "[organization]\n"
    assert _preferred_adapter_from_install_defaults(toml) is None

def test_returns_none_for_blank_preferred_adapter():
    toml = '[organization]\npreferred_adapter = ""\n'
    assert _preferred_adapter_from_install_defaults(toml) is None

def test_returns_none_for_malformed_toml():
    assert _preferred_adapter_from_install_defaults("[[[[invalid") is None

# test_read_packaged_preferred_adapter
def test_read_packaged_returns_none_when_parse_returns_none(monkeypatch):
    monkeypatch.setattr(source_defaults, "_preferred_adapter_from_install_defaults", lambda _t: None)
    monkeypatch.setattr(source_defaults, "_read_install_defaults_text", lambda: "")
    # variant: patch read_packaged_preferred_adapter's internal read
    # (exact seam TBD from implementation shape)
    assert source_defaults.read_packaged_preferred_adapter() is None

def test_read_packaged_raises_on_invalid_adapter(monkeypatch):
    # use a read_packaged fixture that returns "not-an-adapter"
    with pytest.raises(CatalogueError, match="not-an-adapter"):
        ...

def test_read_packaged_returns_valid_adapter(monkeypatch):
    # use a read_packaged fixture that returns "cursor"
    result = ...
    assert result == "cursor"
```

**Approach:**
- Add `_preferred_adapter_from_install_defaults(text: str) -> str | None` to `source_defaults.py` immediately after `_source_from_install_defaults`. Reads `data.get("organization", {}).get("preferred_adapter")`; returns `None` for malformed/absent/blank (mirrors `_source_from_install_defaults`).
- Add `read_packaged_preferred_adapter() -> str | None` immediately after `read_packaged_default`. Reads the packaged file via `importlib.resources` (same pattern as `read_packaged_default()`); calls `_preferred_adapter_from_install_defaults`; on a non-`None` raw value, lazily imports `shipped_adapters_from_contract` and raises `CatalogueError` if the value is not in the shipped set; returns `None` for `None`.

**Done when:** all T1 unit tests pass; both functions importable from `agentbundle.source_defaults`.

---

### T2: Step 2.75 in `_resolve_target_adapter` + call sites

**Depends on:** T1
**Touches:** `packages/agentbundle/agentbundle/commands/install.py`, `packages/agentbundle/tests/unit/test_install_defaults_preferred_adapter.py`

**Tests (TDD — write red stubs first):**

```python
# test_install_defaults_preferred_adapter.py
def test_preferred_adapter_returned_when_no_other_signal(fake_home, tmp_path):
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter="cursor",
    )
    assert result == "cursor"

def test_explicit_adapter_flag_wins_over_org_hint(fake_home, tmp_path):
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        adapter="claude-code",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter="cursor",
    )
    assert result == "claude-code"

def test_user_config_wins_over_org_hint(fake_home, tmp_path):
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code", "kiro-ide"],
        contract_version="0.7",
        user_config=UserConfig(adapter="kiro-ide"),
        preferred_adapter="cursor",
    )
    assert result == "kiro-ide"

def test_state_hint_wins_over_org_hint(fake_home, tmp_path):
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        state_adapter="codex",
        allowed_adapters=["cursor", "codex", "claude-code"],
        contract_version="0.7",
        preferred_adapter="cursor",
    )
    assert result == "codex"

def test_org_hint_refused_when_not_in_allowed_adapters(fake_home, tmp_path):
    pack = _pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused, match="allowed-adapters"):
        _resolve_target_adapter(
            pack,
            scope="user",
            allowed_adapters=["claude-code"],
            contract_version="0.7",
            preferred_adapter="cursor",
        )

def test_none_preferred_adapter_is_no_op(fake_home, tmp_path):
    pack = _pack(tmp_path)
    # With no home-dir probe hits and no preferred_adapter, falls through to
    # DEFAULT_ADAPTER (claude-code).
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter=None,
    )
    assert result == "claude-code"  # DEFAULT_ADAPTER wins for repo probe-less user
```

**Approach:**
- Add `preferred_adapter: str | None = None` to `_resolve_target_adapter` signature (after `user_config`).
- After the `return candidate` of step 2.5, before step 3+4, insert:
  ```python
  # Step 2.75: org preferred-adapter hint from _data/install-defaults.toml.
  if state_adapter is None and preferred_adapter is not None:
      admissible_at_scope = user_capable if scope == "user" else shipped
      if preferred_adapter not in admissible_at_scope:
          raise _AdapterResolutionRefused(
              f"{command_name}: org preferred_adapter {preferred_adapter!r} is "
              f"not supported at {scope} scope. ..."
          )
      if allowed_adapters is not None and preferred_adapter not in allowed_adapters:
          raise _AdapterResolutionRefused(
              f"{command_name}: org preferred_adapter {preferred_adapter!r} "
              f"is not in pack {pack_name!r}'s allowed-adapters "
              f"{sorted(allowed_adapters)}."
          )
      return preferred_adapter
  ```
- Add `preferred_adapter: str | None = None` to `_render_for_repo_scope` and `_render_for_user_scope` signatures and thread to their `_resolve_target_adapter` calls.
- In `run()`, after `user_config` is set and before the `catalogue_uri` resolve block, add:
  ```python
  from agentbundle.source_defaults import read_packaged_preferred_adapter
  from agentbundle.catalogue import CatalogueError
  try:
      org_preferred_adapter: str | None = read_packaged_preferred_adapter()
  except CatalogueError as exc:
      print(f"install: {exc}", file=sys.stderr)
      return 1
  ```
  Then pass `preferred_adapter=org_preferred_adapter` at all `_resolve_target_adapter` call sites and render helper calls in `run()`.

**Done when:** all T2 tests pass; `pytest packages/agentbundle/` exits 0 (existing suite green).

---

### T3: Update workspace.toml and spec status

**Depends on:** T2

**Approach:**
- Remove `{slug = "install-defaults-preferred-adapter-hint"}` from `[backlog].open` in `workspace.toml`.
- Set spec `**Status:**` to `Shipped`.

**Done when:** `workspace.toml` no longer contains the backlog entry; spec status is `Shipped`.

## Rollout

Pure logic addition — no infrastructure, no database, no external services. Ships in the next agentbundle version bump (no release needed from this PR).

## Changelog

- 2026-07-23: initial plan
