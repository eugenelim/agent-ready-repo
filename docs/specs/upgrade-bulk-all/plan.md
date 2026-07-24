# Plan: Upgrade Bulk All

- **Status:** Draft
- **Spec:** [`spec.md`](spec.md)
- **RFC:** RFC-0072 (D4, D5, D6)

## Constraints

- Python 3.11 stdlib-only; no new runtime dependencies.
- All new code lives in `packages/agentbundle/agentbundle/commands/upgrade.py` except where noted.
- `spec/packstate-source-provenance` lands first (landing prerequisite); `canonicalize_source` is declared by that spec and must be in `agentbundle.config` before implementation begins.
- `spec/list-installed-update-status` must be shipped before or simultaneously; it defines the status semantics contract that this spec's `_classify_row` must agree with. The cross-consistency test in T2 is self-contained (no import from `list_installed.py`), so it does not create a hard code dependency at test time.
- RFC-0072 D4 step order is fixed: preflight (source → version → render → path-jail → classify) must complete before any write.
- `_apply_single_row()` must be extracted from `run()` so hook-wiring reconciliation, companion writes, and state writes are identical between single-pack and bulk paths.

## Design

### Approach

`upgrade.py` gains the following internal additions:

**Import prerequisite — hoist existing and add new module-level imports.** `upgrade.py`'s current module-level block (`upgrade.py:32-41`) holds only stdlib. Two categories of change are needed before the new module-level helpers can reference their dependencies:

*Hoist 7 from inside `run()` to module level* (currently at `upgrade.py:75-92`):
`ConfigError`, `load_state`, `resolve_state_path`, `resolve_catalogue`, `CatalogueError`, `load_pack_toml`, `safety`.

*Add 4 net-new module-level imports* (not present anywhere in `upgrade.py` today — cite source):
- `pack_spec_version` → `from agentbundle.config import pack_spec_version` (`config.py:99`)
- `_major` → `from agentbundle.commands._common import _major` (`_common.py:213`)
- `SPEC_VERSION` → `from agentbundle.version import SPEC_VERSION` (`agentbundle/version.py`; matches `list_installed.py:132`; `_common.py:14` re-exports it but the canonical home is `version.py`)
- `_version_key` → `from agentbundle.commands.list_installed import _version_key` (`list_installed.py:159`)

*`canonicalize_source` is a co-land dependency* — defined by `spec/packstate-source-provenance` in `agentbundle.config`; absent from the codebase today (grep returns zero hits). Once that spec lands, add `from agentbundle.config import canonicalize_source`. This prerequisite is already stated in plan.md Constraints (`plan.md:11`).

*`scope_mod` is the noted exception* — stays as a deferred local import inside `_run_all`'s `if args.scope == "user":` branch (item 8); it is only needed there.

Done-when: `python -c "import agentbundle.commands.upgrade as m; [getattr(m, n) for n in ('ConfigError','load_state','resolve_state_path','resolve_catalogue','CatalogueError','load_pack_toml','safety','pack_spec_version','_major','SPEC_VERSION','_version_key')]"` exits without error. `canonicalize_source` is verified by the `spec/packstate-source-provenance` Done-when gate.

1. **`_BulkRow` dataclass** — one instance per `(pack, adapter)` row.
2. **`_was_dist_tree_install(pack_state: PackState) -> bool`** — new module-level helper extracted from the inline expression at `upgrade.py:469-473`: `return any(rp.startswith(("apm/", "claude-plugins/")) or rp == "marketplace.json" for rp in pack_state.files)`. Has two callers: `_preflight_render_and_jail` (bulk guard) and `run()`'s existing render block (single-pack path preservation). Extraction is required because the inline local boolean at `upgrade.py:469` is not callable; creating a module-level helper lets both callers reference it by name. **Implementation note:** Python treats any name assigned inside a function as a local for the whole function scope. To avoid `UnboundLocalError`, the existing `_was_dist_tree_install = any(...)` local assignment at `upgrade.py:469` must be **deleted**; the `if` at `:474` becomes `if _was_dist_tree_install(pack_state):` (calling the module-level helper). This rewrite is a same-area mechanical ride-along (AGENTS.md bundled-fixes carve-out).
3. **`_classify_row()` pure function** — source/version classification (reason codes 1-8).
4. **`_preflight_render_and_jail(row, root, user_config) -> tuple[dict[str, bytes] | None, str | None]`** — renders the projection for one `upgrade-available` row, applies hook-path rewrites (user scope only, mirroring `upgrade.py:434–452`), and runs `safety.assert_projection_jailed`. **Dist-tree guard:** first calls `_was_dist_tree_install(row.pack_state)` (item 2 above); if `True`, immediately returns `(None, "render-failed")` — bulk upgrade does not support the dist-tree render path and the spec boundary in Never-do prohibits it. `user_config = getattr(args, "_user_config", None)` is extracted once per `_run_all()`. Reads `row.pack_dir` (set by Phase 1) and `row.pack_toml` (set by Phase 1) to derive `allowed_adapters = row.pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters")` and `contract_version` for the render calls (`install.py:2886-2887`, `3001-3002`). User-scope branch: derive prefixes → render → rewrite hook paths → jail check; sets `row.allowed_prefixes = _adapter_allowed_prefixes_user(row.adapter)`. Repo-scope branch: render → `(resolved_adapter, projection)` → derive prefixes → jail check (resolved_adapter first per `install.py:3006`); sets `row.resolved_adapter = resolved_adapter` and `row.allowed_prefixes = _adapter_allowed_prefixes_repo(resolved_adapter)`. On success: sets `row._projection`, `row.allowed_prefixes`, and (repo only) `row.resolved_adapter` directly on the row (caller does not re-assign), then returns `(projection, None)`. On failure: leaves those fields `None` and returns `(None, "render-failed")` or `(None, "path-jail-violation")`. `_apply_single_row` reads `row.allowed_prefixes` and `row.resolved_adapter` (repo) to avoid re-deriving adapter resolution during apply (AC23: does not re-render).
5. **`_run_source_version_preflight(state, scope, root) -> tuple[list[_BulkRow], dict[str, tuple[Path|None, str|None, str|None]]]`** — constructs `_BulkRow` objects, builds the `source_resolution_map`, locates each pack via `_locate_pack`, loads each `pack.toml` (catching `ConfigError` → `malformed-catalogue`), and calls `_classify_row(row, pack_toml)`. Returns `(rows, source_resolution_map)` — both the classified row list and the per-source resolution map so callers can populate `sources[*].error_code` and `sources[*].error_message` in JSON output. Encapsulates the Phase 1 loop so `_run_all` remains readable. Called internally by `_run_preflight`; also callable directly by T3 tests that only need Phase 1 results.
5a. **`_run_preflight(state, scope, root, user_config) -> tuple[list[_BulkRow], dict[str, tuple[Path|None, str|None, str|None]]]`** — full two-phase preflight: calls `_run_source_version_preflight` (Phase 1) and then runs the Phase 2 render/path-jail loop for each `upgrade-available` row using `_preflight_render_and_jail`. Returns the same `(rows, source_resolution_map)` tuple (rows now have `_projection` set for `upgrade-available` rows). Extracted as a named production helper so T3 tests can invoke both phases in one call and the Phase 2 loop is single-sourced. `_run_all` delegates to `_run_preflight` instead of calling `_run_source_version_preflight` + Phase 2 inline.
6. **`_redact_credentials(text: str) -> str`** — sanitizes text for output. Three passes: (1) strip URL user-info (`scheme://user:pass@host` → `scheme://host`, including `git+https://` and `ssh://` prefixes); (2) remove common query-string credential params (`access_token`, `token`, `api_key`, `private_token`, `auth`) and their values; (3) replace `Bearer <token>` substrings with `Bearer [REDACTED]`. Used when constructing `sources[*].error_message` from `CatalogueError` messages to satisfy AC33 (no URL user-info, no query-string credential tokens, no bearer tokens) and AC36 (`access_token` grep returns no hits).
7. **`_apply_single_row()` shared helper** — extracted from `run()`; encapsulates render (using pre-rendered `_projection` from preflight), path-jail, tier walk, hook-wiring, state write. Called by both `run()` (single-pack) and `_run_all()` (bulk).
8. **`_run_all()` dispatcher** — top-level function for bulk mode; orchestrates preflight (including render and path-jail), plan display, confirmation, and apply loop.
9. **`run()` entry-point change** — at the top of `run()` (before the `:94` pack-name check and the `:99` `resolve_catalogue_uri` call): if `getattr(args, "format", "table") == "json"` and `args.all` is not set (i.e. single-pack mode), emit an error message via `_print_err` and return non-zero (AC5: `--format json` with `--pack` is not supported). Then, when `args.all`, compute `root = Path(args.root).resolve()` immediately (the single-pack path computes it at `:113`; `_run_all` must receive a resolved path and must not depend on any local that single-pack sets after `:94`), then call `_run_all(args, root)` and return its value. This branch must appear **before** `:94` — `--all` never enters single-pack pack-name or catalogue resolution.
10. **Orchestration helpers** (display/confirmation/apply; not new modules, just named functions in `upgrade.py`):
   - `_assign_pre_apply_outcomes(rows, *, dry_run)` — sets initial `outcome` on each row before confirmation.
   - `_print_plan_table(rows, format, args, source_resolution_map)` — renders the preflight plan as a table; in JSON mode (`format == "json"`) emits a conformant `_build_json_doc(rows, args.scope, args.dry_run, source_resolution_map)` document to stdout. Threading `args` provides `scope` and `dry_run`; `source_resolution_map` provides `error_code`/`error_message` for `sources[]` entries.
   - `_confirm_or_abort(rows)` — interactive confirmation prompt; raises `SystemExit` if user declines.
   - `_apply_all(rows_sorted, state, state_path, root, args, source_resolution_map) -> int` — stop-on-first-failure apply loop; threads `source_resolution_map` to `_finalize`. **Bulk mode: discards the `companions` list** returned by each `_apply_single_row` call — bulk output shows the results table, not per-row companion notices.
   - `_apply_order(rows) -> list[_BulkRow]` — sorts by (canonical_source, pack, adapter) ascending.
   - `_finalize(rows, args, source_resolution_map) -> int` — emits the post-apply RESULTS table/JSON (outcomes: `completed`/`failed`/`not-attempted`/`skipped`/`blocked`) and returns exit code; calls `_print_plan_table(rows, format, args, source_resolution_map)`. This is the **only JSON emitter in the apply path**: the pre-apply PLAN display (before `_confirm_or_abort`) is table-mode only, and the empty-state / no-candidates early returns emit their own conformant JSON doc and exit before reaching `_finalize`. Both renders use the same `_print_plan_table` helper but on mutated outcome values, so both are required — the pre-apply call (table mode only) satisfies AC26 (plan shown before prompt) and the post-apply call satisfies AC29 (final output listing outcomes).
   - `_print_err(msg)` — prints to stderr; used for usage errors and diagnostics in JSON mode.

### Data

**`_BulkRow` dataclass:**

```python
@dataclass
class _BulkRow:
    pack: str
    adapter: str
    scope: str
    pack_state: PackState

    # set during preflight (source/version phase)
    canonical_source: str | None = None
    catalogue_dir: Path | None = None
    pack_dir: Path | None = None  # set after _locate_pack; used by _preflight_render_and_jail
    status: str = "unknown"
    status_reason: str | None = None
    installed_version: str | None = None
    available_version: str | None = None
    pack_toml: dict | None = None

    # set during preflight (render/path-jail phase)
    _projection: dict[str, bytes] | None = None
    allowed_prefixes: list[str] | None = None  # path-jail prefixes for write_jailed in _apply_single_row
    resolved_adapter: str | None = None  # repo scope only (from _render_for_repo_scope first return value)

    # set during apply
    outcome: str = "planned"
```

**`source_resolution_map`** — cached per-invocation catalogue resolution:

```python
dict[str, tuple[Path | None, str | None, str | None]]
# key: canonical_source string
# value: (catalogue_dir, error_code | None, error_message | None)
```

Where `error_code` is a machine-readable token (e.g. `"catalogue-error"`) or `None` on success. Set once per distinct canonical source; subsequent rows with the same source reuse the entry.

### JSON document builder

`_build_json_doc(rows, scope, dry_run, source_resolution_map) -> dict` builds the output object:

```python
{
    "schema_version": 1,          # int, not str
    "command": "upgrade",
    "mode": "all",
    "scope": scope,
    "dry_run": dry_run,
    "sources": [...],             # sorted by canonical source
    "rows": [...],                # sorted by (canonical_source, pack, adapter)
    "summary": {
        "total": N,
        "upgrade_available": N,
        "up_to_date": N,
        "ahead": N,
        "unknown": N,
        "planned": N,             # non-zero in dry-run only
        "completed": N,
        "skipped": N,
        "blocked": N,
        "failed": N,
        "not_attempted": N,
    }
}
```

`summary.planned`: count of `upgrade-available` rows with `outcome: "planned"` (non-zero only in dry-run; always 0 in non-dry-run).

Non-dry-run invariant enforced by `_build_json_doc`: assert `completed + skipped + blocked + failed + not_attempted == total` and `planned == 0`.

Dry-run invariant enforced by `_build_json_doc`: assert `planned + skipped + blocked == total` and `completed == 0` and `failed == 0` and `not_attempted == 0`.

### Interfaces

**Argparse additions to `upgrade` subcommand:**

```
--all               mutually exclusive with --pack (one required)
--scope repo|user   required when --all is used
--format table|json default: table; json with --pack is unsupported (usage error)
--yes               suppress prompt; required for json + non-TTY + non-dry-run
--dry-run           plan display only; no writes; exit 0 unless blocked
```

`--adapter` and the `catalogue` positional argument are rejected as usage errors when `--all` is passed.

### Behavior

**Phase 1 — Preflight (source/version classification):**

```
state_path = resolve_state_path(scope, root)
state = load_state(state_path, for_write=True)
rows = [_BulkRow(pack, adapter, scope, ps) for (pack, adapter), ps in state.packs.items()]
if not rows: print "Nothing installed"; exit 0

user_config = getattr(args, "_user_config", None)  # per upgrade.py:112; threaded to _preflight_render_and_jail

# Build source resolution map; classify each row
source_resolution_map = {}
for row in rows:
    cs = canonicalize_source(row.pack_state.source)
    row.canonical_source = cs
    if cs is None:
        row.status = "unknown"
        row.status_reason = "source-unknown"
        continue

    if cs not in source_resolution_map:
        try:
            cat_dir = resolve_catalogue(cs)
            source_resolution_map[cs] = (cat_dir, None, None)
        except CatalogueError as e:
            source_resolution_map[cs] = (None, "catalogue-error", _redact_credentials(str(e)))

    cat_dir, err_code, err_msg = source_resolution_map[cs]
    if cat_dir is None:
        row.status = "unknown"
        row.status_reason = "source-unavailable"
        continue

    # Locate pack in catalogue
    pack_dir = _locate_pack(cat_dir, row.pack)
    if pack_dir is None:
        row.status = "unknown"
        row.status_reason = "pack-not-found"
        continue
    row.pack_dir = pack_dir  # stored for Phase 2 render

    # Load pack.toml
    try:
        pack_toml = load_pack_toml(pack_dir / "pack.toml")
    except ConfigError:
        row.status = "unknown"
        row.status_reason = "malformed-catalogue"
        continue

    row.catalogue_dir = cat_dir
    row.pack_toml = pack_toml  # stored for _preflight_render_and_jail (allowed_adapters, contract_version)
    # Pure classification (contract, adapter, version comparison)
    row.status, row.status_reason, row.available_version = _classify_row(row, pack_toml)
```

**Phase 2 — Preflight (render/path-jail for `upgrade-available` rows) — body of `_run_preflight`:**

```
for row in rows:
    if row.status != "upgrade-available":
        continue
    # _preflight_render_and_jail sets row._projection, row.allowed_prefixes, row.resolved_adapter
    # (repo) directly on the row — caller only reads error_reason to update status.
    _, error_reason = _preflight_render_and_jail(row, root, user_config)
    if error_reason is not None:
        row.status = "unknown"
        row.status_reason = error_reason  # "render-failed" or "path-jail-violation"
        # row._projection is already None (set by _preflight_render_and_jail on failure)
```

`_preflight_render_and_jail(row, root, user_config)` internally branches on `row.scope`:
- **User scope:** derives `allowed_prefixes = _adapter_allowed_prefixes_user(row.adapter)` first, then calls `_render_for_user_scope(pack_dir, adapter, ..., user_config)` to produce `projection`. Then calls `_resolve_target_adapter(...)` + `_rewrite_user_scope_hook_paths(projection, pack_name, target_adapter)` — mirroring `upgrade.py:434–452` — to rewrite v0.3 user-scope hook paths before the jail check (without this, packs with hooks would falsely fail `path-jail-violation`). Then calls `safety.assert_projection_jailed(root, sorted(projection.keys()), allowed_prefixes, command="upgrade")`. The rewritten `projection` is what gets stored in `row._projection`.
- **Repo scope:** calls `_render_for_repo_scope(pack_dir, adapter, ..., user_config)` first (returns `(resolved_adapter, projection)` — resolved_adapter is the first element, per `install.py:3006` and `upgrade.py:484`), derives `allowed_prefixes = _adapter_allowed_prefixes_repo(resolved_adapter)` from the resolved adapter, then calls `safety.assert_projection_jailed(...)`. This mirrors `run()` order exactly: the resolved adapter, not `row.adapter`, is used for repo prefix derivation. Both helpers (`_adapter_allowed_prefixes_repo`, `_adapter_allowed_prefixes_user`) are imported from `commands/install.py`.
- `pack_dir` is read from `row.pack_dir` (set by Phase 1 after `_locate_pack`; only non-None when `status == "upgrade-available"`).
- Catches `PathJailError` → returns `(None, "path-jail-violation")`; catches any other `Exception` → returns `(None, "render-failed")`.

**Phase 3 — Plan display and confirmation:**

- Sort all rows by (canonical_source, pack, adapter).
- `_assign_pre_apply_outcomes(rows, *, dry_run)` logic:
  - **If any row has `status: unknown`:** set ALL rows' `outcome` to `blocked` (including `upgrade-available`, `up-to-date`, and `ahead` rows). This is required by spec Outcome Semantics ("the full operation is blocked because another row is `unknown`") and the `planned == 0` invariant (a non-dry-run blocked run must have `planned == 0`).
  - **Otherwise (no blocked rows):** `up-to-date`/`ahead` → `skipped`; `upgrade-available` → `planned` (dry-run) or leave as-is for apply.
- If `--dry-run`: print table, exit 0 if no blocked rows, non-zero if any blocked.
- If any blocked (any `status: unknown` row): print table (all outcomes show `blocked`), exit non-zero (no confirmation, no apply).
- If no `upgrade-available` rows: print "Nothing to upgrade"; exit 0.
- Non-dry-run + non-blocked + has `upgrade-available` rows: show table, prompt (unless `--yes`).

**Phase 4 — Apply:**

- Apply order: sorted by (canonical_source, pack, adapter) ascending.
- Call `_apply_single_row(row, state, state_path, root, args)` for each `upgrade-available` row.
  - Uses `row._projection` (pre-rendered); does NOT re-render.
  - Encapsulates: path-jail verify, tier walk + safety.write_jailed, hook-wiring reconciliation, companion writes, state write.
  - On success: `row.outcome = "completed"`.
  - On failure: `row.outcome = "failed"`. Remaining candidates → `not-attempted`. Break.
- Assign final outcomes for non-candidates: `up-to-date`/`ahead` → `skipped`; `unknown` → `blocked`.
- Emit table or JSON. Exit 0 if all `upgrade-available` rows are `completed`; non-zero otherwise.

### Failure and edge cases

- **No rows at scope:** print "Nothing installed at <scope> scope"; exit 0.
- **All rows up-to-date/ahead:** print "Nothing to upgrade"; exit 0.
- **Any `unknown` row:** abort before apply. All `upgrade-available` rows get `outcome: blocked`. Exit non-zero.
- **`render-failed`/`path-jail-violation`:** classified as `status: unknown` in preflight. Blocks the whole operation.
- **`--format json --pack`:** non-zero exit with message "not yet supported; use --format table or use --all".
- **`--format json` non-TTY without `--yes`:** non-zero exit; `sys.stdin.isatty()` evaluated once, used as a local `stdin_is_tty`.
- **Partial completion:** `outcome` field never uses the word "rolled back".
- **Co-owned path:** two `upgrade-available` rows for the same pack/different adapter share projection files. `_apply_single_row()` uses `safety.classify` (which handles co-ownership via `owners_of()`); the second row's apply correctly reconciles shared files via existing hash-safety.

## Tasks

### T1 — Argparse surface

**Mode:** TDD

**Depends on:** none

**Tests:**

```python
def test_all_and_pack_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_args(["upgrade", "--all", "--pack", "core"])

def test_all_or_pack_required():
    with pytest.raises(SystemExit):
        parse_args(["upgrade"])

def test_scope_required_with_all():
    with pytest.raises(SystemExit):
        parse_args(["upgrade", "--all"])  # --scope omitted

def test_format_json_with_pack_unsupported():
    # format is accepted by argparse; rejection happens at the top of run()
    args = parse_args(["upgrade", "--pack", "core", "--format", "json"])
    args.root = str(tmp_root)  # run() derives root from args.root (upgrade.py:113)
    result = run(args)
    assert result != 0
    # stderr contains message about not yet supported

def test_format_table_and_json_accepted():
    args_table = parse_args(["upgrade", "--all", "--scope", "repo", "--format", "table"])
    args_json  = parse_args(["upgrade", "--all", "--scope", "repo", "--format", "json"])
    assert args_table.format == "table"
    assert args_json.format == "json"

def test_yes_flag_accepted():
    args = parse_args(["upgrade", "--all", "--scope", "repo", "--yes"])
    assert args.yes is True
```

**Approach:**

- Add `--all` / `--pack` to a mutually exclusive required group in the `upgrade` subcommand parser.
- Add `--scope repo|user` (required when `--all` used — enforce via a custom check in `run()` at argparse level, not `required=True` on the group member, to avoid argparse ordering issues).
- Add `--format table|json` with default `table`.
- Add `--yes` flag.
- Add `--dry-run` flag (if not already present).
- `--adapter` and `catalogue` positional are rejected in `run()` when `args.all is True`.

**Done when:**

```bash
# All T1 tests pass:
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_all_and_pack_mutually_exclusive -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_all_or_pack_required -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_scope_required_with_all -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_format_table_and_json_accepted -x
```

---

### T2 — `_classify_row` pure function

**Mode:** TDD

**Depends on:** none

**Tests:**

```python
# Tuple: (installed_ver, available_ver, expected_status, expected_reason)
CLASSIFY_CASES = [
    ("0.13.6", "0.13.7", "upgrade-available", None),
    ("0.13.7", "0.13.7", "up-to-date", None),
    ("0.13.8", "0.13.7", "ahead", None),
    # Unequal-length tuples: zero-padding required for correct result
    ("0.13",   "0.13.0",  "up-to-date",       None),   # padding: (0,13)==(0,13,0) after pad
    ("0.9",    "0.10",    "upgrade-available", None),   # 9 < 10 when compared numerically
    ("0.13.6", "not-a-version", "unknown", "unparseable-catalogue-version"),
    ("not-a-version", "0.13.7", "unknown", "unparseable-installed-version"),
    ("not-a-version", "also-not", "unknown", "unparseable-catalogue-version"),
]

@pytest.mark.parametrize("installed,available,expected_status,expected_reason", CLASSIFY_CASES)
def test_classify_row_version_matrix(installed, available, expected_status, expected_reason):
    row = _make_row(installed_version=installed)
    # Omit [pack.adapter-contract] so pack_spec_version() returns None → compatible (any CLI major).
    # Fixes: using a hardcoded major (e.g. "1.0") would break when SPEC_VERSION major != "1".
    pack_toml = {"pack": {"version": available}}
    result_status, result_reason, result_av = _classify_row(row, pack_toml)
    assert result_status == expected_status
    assert result_reason == expected_reason

def test_classify_row_pack_not_found():
    row = _make_row()
    result, reason, _ = _classify_row(row, None)  # None = pack not found
    assert result == "unknown"
    assert reason == "pack-not-found"

def test_classify_row_incompatible_contract():
    # pack_spec_version reads pack_toml["pack"]["adapter-contract"]["version"]
    # Any major != SPEC_VERSION major triggers incompatible-contract.
    # Use a major guaranteed to differ: "9999" cannot equal any real SPEC_VERSION major.
    row = _make_row()
    pack_toml = {"pack": {"version": "0.13.7", "adapter-contract": {"version": "9999.0"}}}
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "unknown"
    assert reason == "incompatible-contract"

def test_classify_row_absent_adapter_contract_is_compatible():
    # pack_spec_version() returns None when [pack.adapter-contract] is absent → compatible
    row = _make_row()
    pack_toml = {"pack": {"version": "0.13.7"}}  # no adapter-contract key
    result, reason, _ = _classify_row(row, pack_toml)
    # absent spec version → compatible → proceeds to version comparison
    assert result == "upgrade-available"  # installed < 0.13.7

def test_classify_row_adapter_no_longer_supported():
    row = _make_row(adapter="kiro")
    pack_toml = {
        "pack": {
            "version": "0.13.7",
            "install": {"allowed-adapters": ["claude-code"]},
        }
    }  # absent adapter-contract → compatible; fails at adapter check
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "unknown"
    assert reason == "adapter-no-longer-supported"

def test_classify_row_adapter_allowed_when_list_absent():
    row = _make_row(adapter="kiro")
    pack_toml = {"pack": {"version": "0.13.7"}}  # absent adapter-contract → compatible
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "upgrade-available"

def test_classify_row_uses_version_key_none_not_exception():
    # _classify_row must check `_version_key(...) is None`, not catch ValueError/TypeError
    row = _make_row(installed_version="not-a-ver")
    pack_toml = {"pack": {"version": "0.13.7"}}  # absent adapter-contract → compatible
    result, reason, _ = _classify_row(row, pack_toml)
    assert reason == "unparseable-installed-version"

def test_classify_row_cross_consistency_with_list_installed_semantics():
    """
    Self-contained cross-consistency check: _classify_row must produce the same
    status as spec/list-installed-update-status defines for the three version-
    comparison cases. Does not import from list_installed.py to avoid a circular
    dependency or a missing-function failure before that spec ships.
    Fixtures omit adapter-contract so pack_spec_version() → None → compatible,
    regardless of CLI SPEC_VERSION major.
    """
    shared_cases = [
        ("0.13.6", "0.13.7", "upgrade-available"),
        ("0.13.7", "0.13.7", "up-to-date"),
        ("0.13.8", "0.13.7", "ahead"),
        # Unequal-length: must be padded before comparison (catches missing zero-pad)
        ("0.13",   "0.13.0",  "up-to-date"),
        ("0.9",    "0.10",    "upgrade-available"),
    ]
    for installed, available, expected in shared_cases:
        row = _make_row(installed_version=installed)
        pack_toml = {"pack": {"version": available}}  # absent adapter-contract → compatible
        bulk_status, _, _ = _classify_row(row, pack_toml)
        assert bulk_status == expected, (
            f"_classify_row({installed!r}, {available!r}) returned {bulk_status!r}, expected {expected!r}"
        )
```

**Approach:**

```python
def _classify_row(
    row: _BulkRow,
    pack_toml: dict | None,
) -> tuple[str, str | None, str | None]:
    """Pure function. Returns (status, status_reason, available_version).
    pack_toml is None when the pack was not found in the catalogue."""
    # 1. Pack presence
    if pack_toml is None:
        return "unknown", "pack-not-found", None

    # 2. Contract compatibility — inline major comparison, NOT check_spec_version_gate()
    # pack_spec_version reads pack_toml["pack"]["adapter-contract"]["version"]; returns None if absent
    raw_spec_version = pack_spec_version(pack_toml)  # from config.py
    if raw_spec_version is not None and _major(raw_spec_version) != _major(SPEC_VERSION):
        return "unknown", "incompatible-contract", None
    # None return (absent [pack.adapter-contract]) is compatible — do NOT raise incompatible-contract

    # 3. Adapter allowed
    allowed = pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters")
    if allowed is not None and row.adapter not in allowed:
        return "unknown", "adapter-no-longer-supported", None

    # 4. Parse catalogue version — check _version_key() is None, not catch exceptions
    # version lives at pack_toml["pack"]["version"], NOT top-level pack_toml["version"]
    available_str = pack_toml.get("pack", {}).get("version", "")
    av_key = _version_key(available_str)
    if av_key is None:
        return "unknown", "unparseable-catalogue-version", None

    # 5. Parse installed version — check _version_key() is None, not catch exceptions
    iv_key = _version_key(row.pack_state.installed_version or "")
    if iv_key is None:
        return "unknown", "unparseable-installed-version", None

    # 6. Zero-pad both tuples to equal length before comparison — mirrors list_installed.py:185-190
    # so that "0.13" vs "0.13.0" compares equal rather than as upgrade-available.
    max_len = max(len(iv_key), len(av_key))
    iv_padded = iv_key + (0,) * (max_len - len(iv_key))
    av_padded = av_key + (0,) * (max_len - len(av_key))

    if iv_padded == av_padded:
        return "up-to-date", None, available_str
    elif iv_padded < av_padded:
        return "upgrade-available", None, available_str
    else:
        return "ahead", None, available_str
```

`_major(version_str)` extracts the first dotted segment (returns a `str`; comparison is string-equal or numeric-equal depending on implementation — verify at EXECUTE time). `pack_spec_version(pack_toml)` reads `pack_toml["pack"]["adapter-contract"]["version"]`; returns `None` when the key path is absent. Absent spec version is compatible (see Blocker-3 fix in the approach).

Note: `_version_key()` returns `None` for non-parseable input rather than raising. The check is `if _version_key(...) is None:`, not a `try/except ValueError`. Verify this contract against the implementation before starting T2; if `_version_key` is not already in scope, check for circular import and copy it into `upgrade.py` if needed.

**Done when:**

```bash
python -m pytest packages/agentbundle/tests/test_classify_row.py -x
# Includes cross-consistency test: test_classify_row_cross_consistency_with_list_installed_semantics
# Includes absent-adapter-contract compatibility test: test_classify_row_absent_adapter_contract_is_compatible
```

---

### T3 — Preflight orchestration (source, version, render, path-jail)

**Mode:** TDD

**Depends on:** T1, T2

**Tests:**

```python
def test_preflight_source_unknown():
    # Row with source="agent-ready-repo" (legacy) → status=unknown, source-unknown
    state = _make_state([("core", "claude-code", "agent-ready-repo", "0.13.6")])
    rows, _ = _run_preflight(state, scope="repo", root=tmp_root, user_config=None)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "source-unknown"
    assert rows[0]._projection is None

def test_preflight_source_unavailable():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_error("git+https://example.test/packs"):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_root, user_config=None)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "source-unavailable"

def test_preflight_blocked_means_no_write():
    state = _make_state([
        ("core", "claude-code", "agent-ready-repo",                    "0.13.6"),  # unknown
        ("ext",  "claude-code", "git+https://example.test/ext-packs",  "1.0.0"),   # upgrade-available
    ])
    with mock_catalogue("git+https://example.test/ext-packs", {"ext": {"pack": {"version": "1.1.0"}}}):
        result = run_all_capture(args_all(scope="repo", yes=True), root=tmp_root)
    assert result.exit_code != 0
    assert all(r.outcome == "blocked" for r in result.rows)
    assert tmp_root_state_mtime_unchanged()

def test_preflight_dist_tree_row_blocks_without_rendering():
    # _was_dist_tree_install returns True → render-failed before render is called
    # Verifies spec Never-do: "upgrade --all does not apply to a dist-tree-installed row"
    # PackState.files is dict[str, dict[str, str]] — keyed by relpath.
    state = _make_state_with_files([
        ("core", "claude-code", "git+https://example.test/packs", "0.13.6",
         {"claude-plugins/core.json": {"sha": "abc123"}}),  # dist-tree path as dict key
    ])
    with mock_catalogue_upgrade_available(), assert_render_not_called():
        rows, _ = _run_preflight(state, scope="repo", root=tmp_root, user_config=None)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "render-failed"
    assert rows[0]._projection is None

def test_preflight_render_failed():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available(), mock_render_raises(ValueError("bad")):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_root, user_config=None)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "render-failed"
    assert rows[0]._projection is None

def test_preflight_path_jail_violation():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available(), mock_path_jail_raises(PathJailError("escape")):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_root, user_config=None)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "path-jail-violation"
    assert rows[0]._projection is None

def test_preflight_stores_projection_for_upgrade_available():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available(), mock_render_returns({"file.md": b"content"}):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_root, user_config=None)
    assert rows[0].status == "upgrade-available"
    assert rows[0]._projection == {"file.md": b"content"}

def test_preflight_adapter_rejected_with_all():
    args = args_all(adapter="kiro")
    result = run_all_capture(args, root=tmp_root)
    assert result.exit_code != 0

def test_preflight_catalogue_rejected_with_all():
    args = args_all(catalogue="/some/path")
    result = run_all_capture(args, root=tmp_root)
    assert result.exit_code != 0

def test_preflight_scope_rejected_missing():
    args = args_all(scope=None)
    result = run_all_capture(args, root=tmp_root)
    assert result.exit_code != 0

def test_preflight_malformed_catalogue():
    # pack.toml raises ConfigError → status=unknown, malformed-catalogue
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_resolved(), mock_load_pack_toml_raises(ConfigError("bad toml")):
        rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_root)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "malformed-catalogue"

def test_preflight_source_conflict_guard_does_not_fire():
    # source="agent-ready-repo" → outcome:blocked (source-unknown), NOT source-conflict exit
    state = _make_state([("core", "claude-code", "agent-ready-repo", "0.13.6")])
    result = run_all_capture(args_all(scope="repo", yes=True), root=tmp_root_with_state(state))
    assert result.exit_code != 0
    assert "source conflict" not in result.stderr

def test_preflight_for_write_true_raises_on_legacy_schema():
    # State with legacy schema version → StateFileLegacy raised (matches single-pack behavior)
    with legacy_state_file(scope="repo"):
        result = run_all_capture(args_all(scope="repo"), root=tmp_root)
    assert result.exit_code != 0
    assert "legacy" in result.stderr.lower() or "schema" in result.stderr.lower()

# AC8: each distinct source resolved at most once; CatalogueError on one source does not suppress other sources
def test_preflight_source_resolved_once_per_invocation():
    # Two rows share the same canonical source → resolve_catalogue called exactly once
    state = _make_state([
        ("core", "claude-code", "git+https://example.test/packs", "0.13.6"),
        ("ext",  "claude-code", "git+https://example.test/packs", "1.0.0"),
    ])
    with mock_catalogue_counting_calls("git+https://example.test/packs") as call_count:
        _run_source_version_preflight(state, scope="repo", root=tmp_root)
    assert call_count.value == 1  # resolved once, reused for second row

def test_preflight_catalogue_error_on_one_source_does_not_suppress_others():
    # Two sources; first raises CatalogueError; second source classifies normally
    state = _make_state([
        ("core", "claude-code", "git+https://example.test/failing",  "0.13.6"),
        ("ext",  "claude-code", "git+https://example.test/working",   "1.0.0"),
    ])
    with mock_catalogue_error("git+https://example.test/failing"), \
         mock_catalogue("git+https://example.test/working", {"ext": {"pack": {"version": "1.1.0"}}}):
        rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_root)
    failing_row = next(r for r in rows if r.pack == "core")
    working_row = next(r for r in rows if r.pack == "ext")
    assert failing_row.status_reason == "source-unavailable"
    assert working_row.status == "upgrade-available"

# AC18: ahead/up-to-date rows get outcome=skipped; ahead rows never downgraded
def test_ahead_row_outcome_skipped_no_mutation():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.8")])
    with mock_catalogue_version("0.13.7"):  # installed > available
        result = run_all_capture(args_all(scope="repo", yes=True), root=tmp_root_with_state(state))
    assert result.exit_code == 0
    row = result.rows[0]
    assert row.status == "ahead"
    assert row.outcome == "skipped"
    assert tmp_root_state_mtime_unchanged()  # no write

def test_up_to_date_row_outcome_skipped_no_mutation():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.7")])
    with mock_catalogue_version("0.13.7"):  # installed == available
        result = run_all_capture(args_all(scope="repo", yes=True), root=tmp_root_with_state(state))
    assert result.exit_code == 0
    row = result.rows[0]
    assert row.status == "up-to-date"
    assert row.outcome == "skipped"
    assert tmp_root_state_mtime_unchanged()  # no write

# AC26: confirmation prompt / --yes bypass
def test_confirmation_prompt_shown_before_write(monkeypatch, capsys):
    # Interactive TTY, upgrade-available rows, no --yes →
    # plan table shown on stdout AND confirmation prompt called (AC26)
    monkeypatch.setattr("sys.stdin", _tty_stdin())
    confirmed = []
    monkeypatch.setattr("agentbundle.commands.upgrade._confirm_or_abort",
                        lambda rows: confirmed.append(True))
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available():
        _run_all(args_all(scope="repo"), root=tmp_root_with_state(state))
    captured = capsys.readouterr()
    assert confirmed  # prompt was called
    # Plan table must appear before the prompt (AC26: "classified plan is shown")
    assert "core" in captured.out or "upgrade-available" in captured.out

def test_yes_flag_bypasses_prompt(monkeypatch):
    # --yes → prompt never called
    monkeypatch.setattr("agentbundle.commands.upgrade._confirm_or_abort",
                        lambda rows: (_ for _ in ()).throw(AssertionError("should not prompt")))
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available():
        result = run_all_capture(args_all(scope="repo", yes=True), root=tmp_root_with_state(state))
    # no assertion error → prompt was not called

# AC27: dry-run exit codes
def test_dry_run_blocked_returns_nonzero():
    state = _make_state([("core", "claude-code", "agent-ready-repo", "0.13.6")])
    result = run_all_capture(args_all(scope="repo", dry_run=True), root=tmp_root_with_state(state))
    assert result.exit_code != 0

def test_dry_run_clean_returns_zero():
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available():
        result = run_all_capture(args_all(scope="repo", dry_run=True), root=tmp_root_with_state(state))
    assert result.exit_code == 0

# User-scope: preflight renders via _render_for_user_scope + _adapter_allowed_prefixes_user
def test_preflight_user_scope_upgrade_available():
    # Seeds user-scope state; confirms _render_for_user_scope is called (not repo render)
    # and that allowed_prefixes is derived via _adapter_allowed_prefixes_user(row.adapter)
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with mock_catalogue_upgrade_available(), mock_user_scope_render_returns({"hooks.json": b"{}"}):
        rows, _ = _run_preflight(state, scope="user", root=user_tmp_root, user_config=None)
    assert rows[0].status == "upgrade-available"
    assert rows[0]._projection is not None
    assert rows[0].allowed_prefixes is not None  # derived from _adapter_allowed_prefixes_user

# AC28: nothing-to-upgrade exits 0 without prompting
def test_nothing_to_upgrade_exits_zero_without_prompt(monkeypatch):
    monkeypatch.setattr("agentbundle.commands.upgrade._confirm_or_abort",
                        lambda rows: (_ for _ in ()).throw(AssertionError("should not prompt")))
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.7")])
    with mock_catalogue_up_to_date("0.13.7"):
        result = run_all_capture(args_all(scope="repo"), root=tmp_root_with_state(state))
    assert result.exit_code == 0
    assert "Nothing to upgrade" in result.stdout or result.stdout.strip() == ""
```

**Test helper notes:**

- `_make_state([(pack, adapter, source, version), ...])` — creates a `State` with `PackState` rows; `PackState.files` defaults to `{}` (matching the declared `dict[str, dict[str, str]]` type).
- `_make_state_with_files([(pack, adapter, source, version, files), ...])` — like `_make_state` but seeds `PackState.files` from the 5th element, which must be a `dict[str, dict[str, str]]` (e.g. `{"claude-plugins/core.json": {"sha": "abc123"}}`). `_was_dist_tree_install` iterates the dict's keys (relpaths), so `startswith`/`==` checks work on string keys. A `list[str]` would be a type violation — `PackState.files.get(relpath)` would `AttributeError`. Used by `test_preflight_dist_tree_row_blocks_without_rendering`.
- `mock_catalogue_error(source, exc=None)` — monkeypatches `resolve_catalogue(source)` to raise `exc` (default: `CatalogueError("connection refused")`).
- `mock_apply_succeeds()` — context manager that stubs the write-path internals (`safety.write_jailed`, `safety.classify`, `dump_state` / `persist_state_locked`, and the user-scope hook-wiring merge) to succeed silently, while leaving `_apply_single_row`'s own body running. This is required for `test_apply_single_row_no_stdout_in_bulk_path`: patching `_apply_single_row` itself would make the stdout assertion vacuous. The stub returns plausible values (`classify` returns `Tier.NEW`, `write_jailed` succeeds, state write succeeds). Companions accumulation and the no-stdout property are exercised against the real body.
- `mock_user_scope_render_returns(projection)` — context manager that patches `_render_for_user_scope` to return `projection` (a `dict[str, bytes]`) and `_rewrite_user_scope_hook_paths` to return it unchanged. Used by `test_preflight_user_scope_upgrade_available` to exercise the user-scope preflight branch without a real user-home directory.
- `user_tmp_root` — a `tmp_path`-based root fixture representing a mock user-home; used for user-scope tests in place of the real `~`.
- **`_Result` and `run_all_capture`** — `_run_all(args, root) -> int` returns a plain integer (the process exit code); it does not return a result object. Tests must use `run_all_capture`:

```python
from dataclasses import dataclass
import io
from contextlib import redirect_stdout, redirect_stderr

@dataclass
class _Result:
    exit_code: int
    rows: list      # list[_BulkRow] via _rows_out side-channel
    stdout: str
    stderr: str

def run_all_capture(args, root) -> _Result:
    rows_out: list = []
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = _run_all(args, root, _rows_out=rows_out)
    return _Result(rc, rows_out, buf_out.getvalue(), buf_err.getvalue())
```

All tests use `result = run_all_capture(args, root)` to get a `_Result` with `exit_code`, `rows`, `stdout`, and `stderr`. Tests that only need the exit code may call `_run_all(args, root)` directly (no capture) to avoid the redirect overhead, but must NOT assign the result to a variable named `result` (which would be an `int`, not a `_Result`).

**Approach:**

```python
def _run_all(args, root: Path, *, _rows_out: list | None = None) -> int:
    """
    Main bulk-upgrade dispatcher. Returns int exit code.

    _rows_out: optional test-only side channel. If provided, _run_all appends
    the final rows_sorted list to it before returning, giving tests access to
    _BulkRow objects without changing the production -> int return type.
    Use run_all_capture() rather than calling this directly from tests.
    """
    # Gate: --adapter and positional catalogue rejected
    if getattr(args, "adapter", None):
        _print_err("--adapter is not compatible with --all")
        return 2
    if getattr(args, "catalogue", None):
        _print_err("positional <catalogue> is not compatible with --all")
        return 2
    if not args.scope:
        _print_err("--scope repo|user is required with --all")
        return 2

    # TTY detection — evaluated once, stored locally
    stdin_is_tty = sys.stdin.isatty()

    # Gate: --format json without --yes (TTY or not) when not dry-run (AC6 / spec §Boundaries).
    # JSON mode has no pre-apply confirmation prompt, so --yes is always required for
    # non-dry-run JSON applies to prevent silent mutation. Dry-run is exempt (read-only).
    if (getattr(args, "format", "table") == "json"
            and not getattr(args, "yes", False)
            and not getattr(args, "dry_run", False)):
        _print_err("--yes is required for --format json (use --dry-run to preview)")
        return 2

    def _return(code: int, rows: list | None = None) -> int:
        """Helper: write rows to _rows_out side-channel, then return code."""
        if _rows_out is not None and rows is not None:
            _rows_out.extend(rows)
        return code

    # User-scope root resolution — mirrors upgrade.py:132-133,162 single-pack path.
    # The caller passes the repo root; user scope requires the user-home root so that
    # resolve_state_path / render / write_jailed target ~/.agentbundle/, not <cwd>/.
    # scope_mod is imported inside run() at upgrade.py:117 (not at module level), so
    # _run_all carries its own local import.
    if args.scope == "user":
        from agentbundle import scope as scope_mod  # noqa: PLC0415
        try:
            root = scope_mod.resolve_user_root()  # mirrors upgrade.py:132-133
        except scope_mod.UserScopeUnresolvable:
            _print_err("Cannot resolve user home directory; --scope user unavailable")
            return 2

    # Load state — mirrors upgrade.py:122-126 (ConfigError catches StateFileLegacy subclass)
    state_path = resolve_state_path(args.scope, root)
    try:
        state = load_state(state_path, for_write=True)
    except ConfigError as exc:
        _print_err(f"upgrade: {exc}")
        return _return(1)
    source_resolution_map: dict[str, tuple[Path | None, str | None, str | None]] = {}
    if not state.packs:
        # In JSON mode, emit a conformant empty doc (AC30 + spec §JSON Contract empty invariant)
        if getattr(args, "format", "table") == "json":
            _print_plan_table([], getattr(args, "format", "table"), args, source_resolution_map)
        else:
            print(f"Nothing installed at {args.scope} scope.")
        return _return(0, [])

    # Phase 1+2: full preflight (source/version + render/path-jail)
    # _run_preflight encapsulates both phases; Phase 2 body = Phase 2 pseudocode below
    user_config = getattr(args, "_user_config", None)  # per upgrade.py:112
    rows, source_resolution_map = _run_preflight(state, args.scope, root, user_config)

    # Phase 3: plan display and confirmation
    rows_sorted = sorted(rows, key=lambda r: (r.canonical_source or "", r.pack, r.adapter))
    _assign_pre_apply_outcomes(rows_sorted, dry_run=getattr(args, "dry_run", False))
    # _assign_pre_apply_outcomes forces ALL rows to outcome=blocked when any status==unknown
    blocked = [r for r in rows_sorted if r.status == "unknown"]
    candidates = [r for r in rows_sorted if r.status == "upgrade-available"]

    if getattr(args, "dry_run", False):
        _print_plan_table(rows_sorted, getattr(args, "format", "table"), args, source_resolution_map)
        return _return(1 if blocked else 0, rows_sorted)

    if blocked:
        # All rows already have outcome=blocked (set by _assign_pre_apply_outcomes above)
        _print_plan_table(rows_sorted, getattr(args, "format", "table"), args, source_resolution_map)
        return _return(1, rows_sorted)

    if not candidates:
        # In JSON mode, emit a conformant doc with all rows skipped (AC30)
        if getattr(args, "format", "table") == "json":
            _print_plan_table(rows_sorted, getattr(args, "format", "table"), args, source_resolution_map)
        else:
            print("Nothing to upgrade.")
        return _return(0, rows_sorted)

    # AC26 + AC30: table mode only — show pre-apply PLAN table and prompt.
    # JSON mode skips both the pre-prompt table and the confirmation prompt;
    # _finalize is the sole JSON emitter. Prompting in JSON mode would write
    # the prompt text to stdout, polluting the JSON document (AC30 violation).
    if getattr(args, "format", "table") == "table":
        _print_plan_table(rows_sorted, "table", args, source_resolution_map)
        if not getattr(args, "yes", False) and stdin_is_tty:
            _confirm_or_abort(rows_sorted)

    # Phase 4: apply — _rows_out written by _apply_all via _return after _finalize
    rc = _apply_all(rows_sorted, state, state_path, root, args, source_resolution_map)
    return _return(rc, rows_sorted)
```

**Done when:**

```bash
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_preflight_blocked_means_no_write -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_preflight_render_failed -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_preflight_path_jail_violation -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_preflight_stores_projection_for_upgrade_available -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_dry_run_blocked_returns_nonzero -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_dry_run_clean_returns_zero -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_nothing_to_upgrade_exits_zero_without_prompt -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py -k "preflight or dry_run or nothing_to_upgrade or confirmation or yes_flag" -x
```

---

### T4 — `_apply_single_row` extraction and apply loop

**Mode:** TDD

**Depends on:** T2, T3

**Tests:**

```python
def test_apply_order_deterministic():
    rows = [
        _make_upgrade_row(pack="zebra", adapter="claude-code"),
        _make_upgrade_row(pack="alpha", adapter="claude-code"),
        _make_upgrade_row(pack="mango", adapter="claude-code"),
    ]
    apply_order = _apply_order(rows)
    assert [r.pack for r in apply_order] == ["alpha", "mango", "zebra"]

def test_stop_on_first_failure():
    rows = [
        _make_upgrade_row(pack="alpha", adapter="claude-code"),
        _make_upgrade_row(pack="beta",  adapter="claude-code"),
        _make_upgrade_row(pack="gamma", adapter="claude-code"),
    ]
    outcomes = _apply_loop_with_mock_results(rows, results=["completed", "failed", None])
    assert outcomes == ["completed", "failed", "not-attempted"]

def test_apply_uses_prerendered_projection():
    row = _make_upgrade_row(pack="core", adapter="claude-code")
    row._projection = {"README.md": b"content"}
    # mock_apply_succeeds stubs write internals; assert_render_not_called verifies no re-render
    with mock_apply_succeeds(), assert_render_not_called():
        _apply_single_row(row, state, state_path, root, args)

def test_coowned_path_both_completed(capsys):
    rows = [
        _make_upgrade_row(pack="core", adapter="claude-code"),
        _make_upgrade_row(pack="core", adapter="kiro"),
    ]
    for r in rows:
        r._projection = {"shared.md": b"content"}
    _apply_all(rows, state, state_path, root, args, source_resolution_map={})
    # Outcomes mutated in place by _apply_all
    assert all(r.outcome == "completed" for r in rows if r.status == "upgrade-available")

def test_apply_single_row_no_stdout_in_bulk_path(capsys):
    # _apply_single_row must not emit to stdout when called from bulk path (row._projection set)
    # (stdout in bulk mode is owned by _print_plan_table/_finalize — no per-row recap)
    row = _make_upgrade_row(pack="core", adapter="claude-code")
    row._projection = {"README.md": b"content"}
    with mock_apply_succeeds():
        _apply_single_row(row, state, state_path, root, args)
    captured = capsys.readouterr()
    assert captured.out == ""  # no stdout from _apply_single_row in bulk path

def test_partial_completion_no_rolled_back_text():
    rows = [
        _make_upgrade_row(pack="alpha", adapter="claude-code"),
        _make_upgrade_row(pack="beta",  adapter="claude-code"),
    ]
    with mock_second_row_fail():
        result = run_all_capture(args_all(scope="repo", yes=True), root=tmp_root_with_rows(rows))
    assert "rolled back" not in result.stdout
    assert "rolled back" not in result.stderr
```

**Approach:**

**Step 1 — Extract `_apply_single_row` from `run()`:**

Identify the per-row apply body in `run()` at lines `568-740`. This range begins at the AC4 path-jail probe and excludes:
- The render + per-primitive filter block at `474-522` (stays in `run()`; passes `work_projection` into `row._projection`).
- The single-pack dry-run block at `534-566` (stays in `run()` ahead of the call; it emits stdout and returns early before the apply body starts).

The extraction range `568-740` includes:
- Path-jail AC4 probe (`safety.assert_projection_jailed`)
- Tier walk + `safety.write_jailed` per file
- Hook-wiring reconciliation (`_compute_new_wiring_rows`, `_unproject_removed_rows`, `_merge_user_scope_hook_wiring`, `_refresh_merge_target_shas`)
- Companion accumulation (local `companions = []`, append during tier walk)
- State write (`safety.write_jailed` for state file)

Extract this body into:

```python
def _apply_single_row(
    row: _BulkRow,
    state: State,
    state_path: Path,
    root: Path,
    args,
) -> tuple[bool, list[str]]:
    """
    Apply one upgrade row. Returns (success, companions) where:
    - success: True on success, False on failure.
    - companions: list of companion file relpaths accumulated during the tier walk
      (mirroring upgrade.py:589, 605 and the recap at upgrade.py:746-769).
      run() (single-pack path) uses this list for the per-upgrade companion notice.
      _apply_all() (bulk path) discards it — bulk output shows the results table,
      not per-row companion notices.

    _apply_single_row NEVER renders. row._projection is ALWAYS pre-populated before
    this call (AC23: does not re-render). The extraction boundary is upgrade.py:568-740
    (the path-jail AC4 probe, tier walk, path-jail verify, write_jailed loop, hook-wiring
    reconciliation, companion accumulation, state write) — it does NOT include the
    render block at upgrade.py:474-501 or the single-pack dry-run block at 534-566.
    The single-pack dry-run block (534-566, emitting stdout) stays in run() ahead of
    the _apply_single_row call.

    Both call sites pre-populate row._projection:
    - Bulk path: _preflight_render_and_jail (Phase 2) sets row._projection.
    - Single-pack path: run() renders at upgrade.py:474-501, filters per-primitive at
      503-522 to produce work_projection, then creates a _BulkRow with
      _projection=work_projection before calling _apply_single_row. The row also has
      allowed_prefixes and (repo) resolved_adapter pre-set from the render.

    Does NOT emit any stdout — stdout in bulk mode is owned by _print_plan_table/
    _finalize, and in single-pack mode the recap at upgrade.py:746-769 is emitted
    by run() after reading the returned companions.
    """
    ...
```

**Step 2 — Update `run()` to call `_apply_single_row`:**

`run()` keeps its render + per-primitive filter at `upgrade.py:474-522` (unchanged). After filtering, `run()` creates a compatibility `_BulkRow` and replaces the inline apply body (lines `568-740`) with a call to `_apply_single_row(row, ...)`. The `_BulkRow` must populate every field the `568-740` body reads:
- `pack`, `adapter` — from `run()`'s existing locals.
- `scope = effective_scope` — must be the resolved scope string (`"repo"` or `"user"`), NOT `args.scope` / `cli_scope` which may be `None` under scope inference (`upgrade.py:104,155`). The extracted body branches on `effective_scope` at `upgrade.py:633` (user hook-wiring) and `728` (state-prefix skip).
- `pack_state` — from `run()`'s existing locals.
- `_projection = work_projection` — the already-filtered projection from `474-522`.
- `allowed_prefixes` — derived from the render output; initialized at `upgrade.py:154`, assigned at `:203` (user scope) and `:496` (repo scope), stays `None` for the dist-tree branch.
- `resolved_adapter` — repo scope only; first return value of `_render_for_repo_scope`.
- `pack_dir` — from `run()`'s `pack_dir` local (used by hook-wiring at `upgrade.py:642/672/684`).
- `pack_toml` — from `run()`'s loaded pack.toml dict (hook-wiring reads `_pack_allowed_adapters` / `_pack_contract_version` derived from it at `647-648/672`).
- `available_version` — the catalogue version string (used in state-update at `606/620/717/719`).
- Per-primitive flags (`is_per_primitive`, `skill_name`, `hook_name`) are accessed from `args` directly inside the body; no new `_BulkRow` field needed.

The returned `(success, companions)` tuple is unpacked; `run()` uses `companions` for the recap at `upgrade.py:746-769` as before.

**Step 3 — Implement `_apply_all` for bulk path:**

```python
def _apply_all(rows_sorted, state, state_path, root, args, source_resolution_map) -> int:
    candidates = [r for r in rows_sorted if r.status == "upgrade-available"]
    for i, row in enumerate(candidates):
        success, _ = _apply_single_row(row, state, state_path, root, args)  # companions discarded in bulk
        if success:
            row.outcome = "completed"
        else:
            row.outcome = "failed"
            for remaining in candidates[i+1:]:
                remaining.outcome = "not-attempted"
            break
    for row in rows_sorted:
        if row.status in ("up-to-date", "ahead"):
            row.outcome = "skipped"
        elif row.status == "unknown":
            row.outcome = "blocked"
    return _finalize(rows_sorted, args, source_resolution_map)
```

**Done when:**

```bash
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_apply_order_deterministic -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_stop_on_first_failure -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py::test_apply_uses_prerendered_projection -x
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py -k "apply" -x
```

---

### T5 — JSON contract output

**Mode:** TDD

**Depends on:** T4

**Tests:**

```python
def test_json_output_parses():
    result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=fixture_root)
    doc = json.loads(result.stdout)
    assert doc["schema_version"] == 1   # int, not str
    assert doc["command"] == "upgrade"
    assert doc["mode"] == "all"

def test_json_output_rows_sorted():
    result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=multi_row_fixture)
    doc = json.loads(result.stdout)
    keys = [(r["source"], r["pack"], r["adapter"]) for r in doc["rows"]]
    assert keys == sorted(keys)

def test_json_summary_invariant_non_dry_run():
    doc = json.loads(run_to_completion_json(scope="repo"))
    s = doc["summary"]
    assert s["completed"] + s["skipped"] + s["blocked"] + s["failed"] + s["not_attempted"] == s["total"]
    assert s["planned"] == 0

def test_json_summary_invariant_dry_run():
    doc = json.loads(run_dry_run_json(scope="repo"))
    s = doc["summary"]
    assert s["planned"] + s["skipped"] + s["blocked"] == s["total"]
    assert s["completed"] == 0
    assert s["failed"] == 0
    assert s["not_attempted"] == 0

def test_json_no_stdout_pollution_in_json_mode():
    result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=fixture_root)
    doc = json.loads(result.stdout)  # must succeed; human text on stdout would break parse
    assert doc is not None

def test_json_mode_non_tty_without_yes():
    # AC6: non-dry-run JSON without --yes fails regardless of TTY state
    with monkeypatch_stdin_not_tty():
        result = run_all_capture(args_all(scope="repo", format="json"), root=fixture_root)
    assert result.exit_code != 0
    assert "--yes" in result.stderr

def test_json_mode_tty_without_yes():
    # AC6: TTY stdin + JSON + no --yes also fails (JSON mode has no prompt)
    with monkeypatch_stdin_tty():
        result = run_all_capture(args_all(scope="repo", format="json"), root=fixture_root)
    assert result.exit_code != 0
    assert "--yes" in result.stderr

def test_json_source_redacted():
    state = _make_state([("core", "claude-code", "git+https://user:token@example.test/packs", "0.13.6")])
    result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=tmp_with_state(state))
    doc = json.loads(result.stdout)
    row_sources = [r["source"] for r in doc["rows"]]
    # canonicalize_source rejects user-info; source is None
    assert all(s is None or ("token" not in (s or "")) for s in row_sources)

def test_json_empty_scope():
    result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=empty_root)
    doc = json.loads(result.stdout)
    assert doc["rows"] == []
    assert doc["sources"] == []
    assert doc["summary"]["total"] == 0

def test_json_source_error_message_redacted():
    # AC33: CatalogueError message containing credentialed URI → redacted in sources[*].error_message
    # Note: canonicalize_source strips user-info, so the stored canonical source is
    # "git+https://example.test/packs" (no credentials). The mock key matches that canonical.
    credentialed_source = "git+https://user:secret@example.test/packs"
    state = _make_state([("core", "claude-code", credentialed_source, "0.13.6")])
    error_msg = f"Cannot reach {credentialed_source}: connection refused"
    with mock_catalogue_error("git+https://example.test/packs", exc=CatalogueError(error_msg)):
        result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=tmp_with_state(state))
    doc = json.loads(result.stdout)
    # Assert at least one source entry has a populated error_message — if this fails,
    # source_resolution_map is not being threaded into _build_json_doc.
    assert any(e.get("error_message") for e in doc.get("sources", [])), (
        "expected at least one sources[] entry with error_message set; "
        "source_resolution_map may not be threaded into _build_json_doc"
    )
    for source_entry in doc.get("sources", []):
        if source_entry.get("error_message"):
            assert "secret" not in source_entry["error_message"]
            assert "user:" not in source_entry["error_message"]

# AC6 dry-run carve-out: non-TTY + --format json + --dry-run does NOT require --yes
def test_json_dry_run_non_tty_no_yes_succeeds():
    with monkeypatch_stdin_not_tty():
        result = run_all_capture(args_all(scope="repo", format="json", dry_run=True), root=fixture_root)
    # No "--yes required" error; exits 0 (or non-zero only from blocked rows — not a usage error)
    assert "--yes" not in result.stderr

# _redact_credentials unit tests (Concern 1: passes 2 and 3)
def test_redact_credentials_query_string_param():
    text = "fetch failed: https://example.test/packs?access_token=mysecret&foo=bar"
    redacted = _redact_credentials(text)
    assert "mysecret" not in redacted
    assert "access_token" not in redacted  # key stripped

def test_redact_credentials_bearer_token():
    text = "Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.payload.sig"
    redacted = _redact_credentials(text)
    assert "eyJhbGciOiJSUzI1NiJ9" not in redacted
    assert "Bearer [REDACTED]" in redacted
```

**Approach:**

`_build_json_doc(rows, scope, dry_run, source_resolution_map)` builds the dict. `json.dumps(doc, indent=2)` to stdout. All `print()` and progress messages inside `_run_all` go to stderr when `args.format == "json"`. The `_print_err` helper always goes to stderr. `source_resolution_map` is used to populate `sources[*].error_code` and `sources[*].error_message`; it is always available (initialized to `{}` before any early return in `_run_all`).

TTY detection in tests: monkeypatch `sys.stdin` with a non-TTY-like object (`isatty()` returns `False`). Do not use an `args.stdin_is_tty` attribute — the production code reads `sys.stdin.isatty()` directly; tests monkeypatch accordingly.

**Done when:**

```bash
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py -k "json or redact_credentials" -x
# Covers: json output, dry-run non-TTY carve-out, _redact_credentials passes 1-3, error_message redaction
```

---

### T6 — D6 layout checks

**Mode:** Goal-based

**Depends on:** T4

**Tests:**

```python
def test_table_output_80col_golden():
    result = run_all_capture(args_all(scope="repo", dry_run=True, format="table"), root=fixture_80col)
    with open("tests/fixtures/upgrade_bulk_80col_golden.txt") as f:
        assert result.stdout == f.read()

def test_table_output_120col_golden():
    result = run_all_capture(args_all(scope="repo", dry_run=True, format="table"), root=fixture_120col)
    with open("tests/fixtures/upgrade_bulk_120col_golden.txt") as f:
        assert result.stdout == f.read()

def test_table_unicode_identifier():
    result = run_all_capture(args_all(scope="repo", dry_run=True, format="table"), root=unicode_fixture)
    assert "núcleo" in result.stdout  # or equivalent Unicode identifier

def test_table_long_source_truncated():
    result = run_all_capture(args_all(scope="repo", dry_run=True, format="table"), root=long_source_fixture)
    lines = result.stdout.splitlines()
    col_widths = [len(line) for line in lines if line.startswith("|")]
    assert len(set(col_widths)) <= 1  # all rows same width — no overflow

def test_json_schema_version_is_integer():
    result = run_all_capture(args_all(scope="repo", yes=True, format="json"), root=fixture_root)
    doc = json.loads(result.stdout)
    assert isinstance(doc["schema_version"], int)
    assert doc["schema_version"] == 1
```

**Approach:**

- Create two fixtures (`fixture_80col`, `fixture_120col`): state files with at least 3 rows at different statuses, one row with a Unicode identifier (`núcleo`), one with a long source URI.
- Run `_run_all` in dry-run table mode against each fixture and capture output.
- **First run:** generate and save golden files `upgrade_bulk_80col_golden.txt` and `upgrade_bulk_120col_golden.txt`. **Subsequent runs:** diff against saved files.
- Column width: use `shutil.get_terminal_size()` defaulting to 80 for the 80col fixture; pass 120 explicitly for the 120col fixture.
- Long source URI: truncate with `...` at column max — `source[:max_width-3] + "..."`.
- Labels match D6 traceability requirement (80col and 120col named explicitly).

**Done when:**

```bash
python -m pytest packages/agentbundle/tests/test_upgrade_bulk.py \
    -k "golden or unicode or truncated or schema_version" -x
# Both 80col and 120col golden tests pass
# Unicode test passes
# Long-source truncation test passes
# schema_version integer test passes
```

---

### T7 — Integration and regression

**Mode:** TDD (integration), Goal-based (regression)

**Depends on:** T4, T5, T6

**Tests:**

```python
def test_integration_happy_path(tmp_path):
    setup_repo_fixture(tmp_path, packs=["core@0.13.6", "ext@1.0.0"],
                       catalogue_versions={"core": "0.13.7", "ext": "1.1.0"})
    result = run_upgrade_all(tmp_path, scope="repo", yes=True)
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.13.7"
    assert state.row("ext", "claude-code").installed_version == "1.1.0"
    assert result.exit_code == 0

def test_integration_partial_failure(tmp_path):
    setup_repo_fixture(tmp_path, packs=["alpha@1.0.0", "beta@1.0.0"],
                       catalogue_versions={"alpha": "1.1.0"},
                       corrupt_pack="beta")
    doc = json.loads(run_upgrade_all_json(tmp_path, scope="repo", yes=True).stdout)
    outcomes = {r["pack"]: r["outcome"] for r in doc["rows"]}
    assert outcomes["alpha"] == "completed"
    assert outcomes["beta"] == "failed"

def test_integration_blocked_preflight_no_write(tmp_path):
    setup_repo_fixture(tmp_path,
        packs=[("core", "claude-code", "agent-ready-repo",               "0.13.6"),
               ("ext",  "claude-code", "git+https://example.test/ext",   "1.0.0")],
        catalogue_versions={"ext": "1.1.0"})
    state_path = tmp_path / ".agentbundle-state.toml"
    mtime_before = state_path.stat().st_mtime
    result = run_upgrade_all(tmp_path, scope="repo", yes=True)
    assert result.exit_code != 0
    assert state_path.stat().st_mtime == mtime_before

def test_integration_coowned_path(tmp_path):
    setup_repo_fixture(tmp_path,
        packs=[("core", "claude-code", "git+https://example.test/packs", "0.13.6"),
               ("core", "kiro",       "git+https://example.test/packs", "0.13.6")],
        catalogue_versions={"core": "0.13.7"})
    result = run_upgrade_all(tmp_path, scope="repo", yes=True)
    assert result.exit_code == 0
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.13.7"
    assert state.row("core", "kiro").installed_version == "0.13.7"

def test_integration_user_scope_happy_path(tmp_path):
    # User-scope: _run_all must resolve user-home root via scope_mod.resolve_user_root()
    # (not the repo root) so state path and render targets are under ~, not cwd.
    setup_user_fixture(tmp_path, packs=["core@0.13.6"],
                       catalogue_versions={"core": "0.13.7"})
    # Monkeypatch scope_mod.resolve_user_root() to return tmp_path (mock user home)
    with mock_user_root(tmp_path):
        result = run_upgrade_all(tmp_path, scope="user", yes=True)
    assert result.exit_code == 0
    # User-scope state lives at .agentbundle/state.toml (resolve_state_path("user", root))
    # NOT .agentbundle-state.toml which is the repo-scope convention.
    state = load_state(tmp_path / ".agentbundle" / "state.toml")
    assert state.row("core", "claude-code").installed_version == "0.13.7"
```

**Done when:**

```bash
# Integration tests pass
python -m pytest packages/agentbundle/tests/test_upgrade_bulk_integration.py -x

# Existing agentbundle tests unmodified and passing
python -m pytest packages/agentbundle/tests/ -x \
    --ignore=tests/test_upgrade_bulk.py \
    --ignore=tests/test_upgrade_bulk_integration.py

# AC36: no credential leak in test output against fixtures
# (Run tests with output capture; grep captured output)
grep -rn "Authorization\|Bearer\|access_token" /tmp/test_upgrade_bulk_output/ \
    && echo "FAIL: credential leak" || echo "PASS: no credential leak"

# AC37: no TLS-ignore or SSL-disable option added
grep -rn "verify=False\|ssl_context.*verify\|disable.*cert\|ignore.*tls\|no.verify\|disable.ssl" \
    packages/agentbundle/agentbundle/commands/upgrade.py \
    && echo "FAIL: TLS bypass found" || echo "PASS: no TLS bypass"

# No new runtime dependency
diff <(git show origin/main:packages/agentbundle/pyproject.toml | grep -A50 '\[project\]') \
     <(cat packages/agentbundle/pyproject.toml | grep -A50 '\[project\]') \
    && echo "PASS: no new dependencies" || echo "REVIEW: check diff above"

# Spec-status lint
python packages/agentbundle/scripts/lint-spec-status.py --root .
```

**Changelog entry (add to `[Unreleased]` in `packages/agentbundle/CHANGELOG.md` with this PR):**

```markdown
### Added
- `upgrade --all --scope repo|user`: scoped bulk upgrade with full preflight (source,
  version, render, path-jail), deterministic apply order, stop-on-first-failure, and
  honest partial-failure disclosure. `--format table|json` (table default). JSON contract
  `schema_version 1, command: "upgrade", mode: "all"`. RFC-0072 D4/D5/D6.
```

---

## Risks

- **`_apply_single_row` extraction may widen the blast radius of upgrade.py.** Mitigation: extract after T2 and T3 integration tests are green; run `git diff --stat` to confirm the extraction is a pure refactor (no logic change).
- **Hook-wiring reconciliation block (upgrade.py:633–709) is complex inline logic.** If extraction is not feasible without risk, the alternative is to call `run()` per row with synthesized args. The spec permits either; check feasibility at T4 start and surface if blocked.
- **Circular import between `upgrade.py` and `list_installed.py` (for `_version_key`).** Mitigation: copy `_version_key` into `upgrade.py` or move it to `commands/_common.py`. Check before starting T2; it's task-zero if blocked.
- **Path-jail preflight adds I/O to what was a pure preflight phase.** Mitigation: mock `_render_for_repo_scope` / `_render_for_user_scope` in all preflight unit tests; integration tests use real fixtures.
