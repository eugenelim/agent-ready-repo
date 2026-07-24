# Plan: List-Installed Update Status

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Changes are confined to `commands/list_installed.py` (primary) and the `cli.py` argument parser block for `list-installed`. A one-line erratum note is added to `docs/specs/install-state-visibility/spec.md` recording the sort-order supersession. No new modules, no new dependencies.

Six tasks:

1. Extend status computation — replace `_status_for` with `_compute_status_pair` returning `(status, status_reason)`.
2. Replace single-source resolution with multi-source resolution — new `_resolve_per_source` that groups rows by canonical source and resolves each once.
3. Wire `--format table|json` and `--updates-only` into `cli.py`.
4. Implement JSON output renderer.
5. Update table output — add conditional SOURCE column (OQ1), apply `--updates-only` filter, display four-value status.
6. Add D6 layout/snapshot tests, subprocess tests, and run the full suite.

`canonicalize_source` from `spec/packstate-source-provenance` is used, not reimplemented.

## Design Decisions

- **Multi-source grouping replaces single-default-source resolution.** `_resolve_latest(args)` resolved one catalogue via the four-layer default chain for all rows. The new `_resolve_per_source(rows)` resolves each unique canonical source independently. Rows whose `canonicalize_source(PackState.source)` returns `None` are not resolved and get `source-unknown` immediately. This breaks with current behavior for legacy-provenance rows; the documented recovery is `agentbundle upgrade` (RFC-0072 D3). Alternative considered: fall back to default source for unknown-provenance rows; rejected because it conflates "installed from X" with "currently pointing at default" and obscures the upgrade path.

- **`--updates-only` does not affect summary counts.** Summary always counts the pre-filter set. This makes `--updates-only | wc -l` vs. `summary.total` a meaningful comparison for CI. Alternative: filter the summary too; rejected because the summary would not reflect reality.

- **The `catalogue` positional is deprecated as a no-op for `list-installed`.** `_resolve_per_source(rows)` uses each row's `PackState.source` for resolution; it does not consult `args.catalogue`. The `catalogue` positional remains in the CLI parser (no shape change) but is ignored by `list-installed` specifically. When provided, a deprecation warning is emitted to stderr: `"agentbundle list-installed: the catalogue positional is ignored; rows are resolved against their recorded provenance. Use --no-check to skip resolution entirely."`. The previous behavior (single-catalogue resolution against `args.catalogue`) is superseded by per-source resolution. This is an intentional consequence of the multi-source grouping design and is recorded here per spec.md § Boundaries "Ask first". Three existing command-level tests must be migrated to supply `PackState.source` pointing to the fixture catalogue (see T2 migration steps below).

- **OQ1 resolved — SOURCE column when 2+ distinct sources only.** Omitting the source column in the common single-source case reduces noise. The column is essential in multi-source cases. Source strings are at most 40 visible characters total (≤39 content + `…`). The source count is computed over the full result set before `--updates-only` filtering, so the column decision is stable. Null-source rows display `—` in the SOURCE cell.

- **Sort order changes from `(pack, adapter, scope)` to `(scope, pack, adapter)`.** RFC-0072 D5 specifies `(scope, pack, adapter)`. This supersedes the install-state-visibility "Always do" boundary. The erratum note in `docs/specs/install-state-visibility/spec.md` is added **in this spec PR** as a "pending implementation of `spec/list-installed-update-status`" marker (it is already present in the working tree at line 54). The implementing (code) PR does not re-add it; instead, the implementing PR removes the "pending implementation of `spec/list-installed-update-status`" qualifier from the marker text (leaving the erratum in place, but without the pending caveat) once the code ships.

- **`_compute_status_pair` is a pure function.** Takes `(installed, available_version, reason_ctx)` — no I/O. All I/O stays in `_resolve_per_source`. Clean separation makes the status logic exhaustively testable.

- **Reason code precedence is stable and fixed.** The eight reason codes are evaluated in a fixed ladder in `_resolve_per_source`; `_compute_status_pair` receives an already-resolved `reason_ctx`. This keeps `_compute_status_pair` simple and makes the precedence testable in isolation.

- **`sources[*].error_message` must be redacted.** `CatalogueError` messages may embed raw URIs. The JSON renderer passes them through a simple redaction step (strip credential fragments) before writing. `canonicalize_source` already rejects user-info, so canonical sources themselves are safe; the redaction step is belt-and-suspenders for future source schemes.

- **`drift_count` in the JSON contract is `null` unless `--check-drift` is active.** Maintains compatibility with the existing flag; the field is always present in JSON rows.

- **`--updates-only` + `--no-check` interaction.** When both are active, `--no-check` sets all statuses to `null`; the filter has no effect and all rows are shown. No special-case code needed — a null status matches none of the filter values.

## Tasks

### T1: Replace `_status_for` with `_compute_status_pair`

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/commands/list_installed.py`

**Tests (TDD — red stubs before production code):**
- `test_compute_status_pair_up_to_date`: installed = `"1.2.0"`, available = `"1.2.0"`, `reason_ctx=None` → `("up-to-date", None)`. Verifies AC4, AC5.
- `test_compute_status_pair_upgrade_available`: installed = `"1.1.0"`, available = `"1.2.0"` → `("upgrade-available", None)`. Verifies AC4.
- `test_compute_status_pair_ahead`: installed = `"1.3.0"`, available = `"1.2.0"` → `("ahead", None)`. Verifies AC5.
- `test_compute_status_pair_ahead_zero_padded`: installed = `"1.2.1"`, available = `"1.2"` → `("ahead", None)` — `(1,2,1) > (1,2,0)` after zero-padding. Verifies AC5.
- `test_compute_status_pair_equal_zero_padded`: installed = `"1.2"`, available = `"1.2.0"` → `("up-to-date", None)`. Verifies AC5.
- `test_compute_status_pair_reason_ctx_wins`: `reason_ctx="source-unknown"` → `("unknown", "source-unknown")` regardless of version values. Verifies AC6, AC7.
- `test_compute_status_pair_each_reason_code`: parametrize over all eight reason codes; each returns `("unknown", <code>)`. Verifies AC6.
- `test_compute_status_pair_unparseable_installed`: installed = `"1.2.0-rc1"`, available = `"1.2.0"`, `reason_ctx=None` → `("unknown", "unparseable-installed-version")`. Verifies AC6.
- `test_compute_status_pair_unparseable_available`: installed = `"1.2.0"`, available = `"1.2.0-rc1"`, `reason_ctx=None` → `("unknown", "unparseable-catalogue-version")`. Verifies AC6.
- `test_compute_status_pair_both_unparseable`: installed = `"1.2.0-rc1"`, available = `"1.2.0-beta"`, `reason_ctx=None` → `("unknown", "unparseable-catalogue-version")` (catalogue version checked first; takes precedence). Verifies AC6 and spec ordering note.
- `test_compute_status_pair_null_available_version`: installed = `"1.2.0"`, available = `None`, `reason_ctx=None` → `("unknown", "pack-not-found")`. Verifies AC6 (defensive branch; in practice T2 always sets reason_ctx when available_version is None).

**Approach:**
- Add `_compute_status_pair(installed: str, available_version: str | None, *, reason_ctx: str | None) -> tuple[str, str | None]`.
- Logic:
  1. `if reason_ctx is not None: return ("unknown", reason_ctx)`
  2. `if available_version is None: return ("unknown", "pack-not-found")` — defensive guard; in practice T2 always supplies a reason_ctx when available_version is None.
  3. `b = _version_key(available_version)` — if `None`: return `("unknown", "unparseable-catalogue-version")` (catalogue version checked **before** installed version, per spec ordering).
  4. `a = _version_key(installed)` — if `None`: return `("unknown", "unparseable-installed-version")`
  5. Zero-pad to `max(len(a), len(b))`; compare: `a > b` → `"ahead"`; `b > a` → `"upgrade-available"`; else → `"up-to-date"`.
- Keep `_status_for` in place during T1; callers switch in T2 and T5. Delete `_status_for` once all callers are migrated.
- **Rewrite the module docstring** (`list_installed.py:7-10`): the current docstring states the command "resolves the catalogue once" and lists only three statuses (`up-to-date / upgrade-available / unknown`). After T2 the resolution is per-source; after T1 there are four statuses (`ahead` added) plus a `--format table|json` mode. Update the docstring in T2 (as part of the per-source wiring).
- **Remove or migrate the six existing `_status_for` unit tests** at `packages/agentbundle/tests/unit/test_list_installed_cmd.py:27-52` (they call `li._status_for(...)` directly and will raise `AttributeError` after `_status_for` is deleted). In particular, `test_status_installed_ahead_is_up_to_date` must be rewritten: the old semantics returned `up-to-date` when installed > latest; the new semantics return `("ahead", None)`. Migrate the six tests to call `_compute_status_pair` with equivalent inputs and assert the new expected tuples.

**Done when:** all T1 tests pass; the six legacy `_status_for` tests have been replaced with equivalent `_compute_status_pair` tests; `pytest packages/agentbundle/tests/unit/test_list_installed_cmd.py -x` exits 0.

---

### T2: Multi-source catalogue resolution

**Depends on:** T1 (the `run()` integration step calls `_compute_status_pair`; `_resolve_per_source` itself has no dependency on T1 and can be developed in parallel, but the wiring in `run()` requires T1 to be present)

**Touches:** `packages/agentbundle/agentbundle/commands/list_installed.py`

**Tests (TDD — red stubs before production code):**
- `test_resolve_per_source_all_unknown_provenance`: all rows have `source=None`; assert `sources` list is empty; every row tagged `reason="source-unknown"`. Verifies AC7, AC10.
- `test_resolve_per_source_legacy_literal`: rows with `source="agent-ready-repo"`; same result as `source=None`. Verifies AC7.
- `test_resolve_per_source_single_ok`: rows from one canonical source; mock `resolve_catalogue` succeeds once; assert called exactly once; rows receive pack data from the catalogue. Verifies AC9.
- `test_resolve_per_source_single_failed`: rows from one canonical source; mock `resolve_catalogue` raises `CatalogueError`; rows tagged `reason="source-unavailable"`; `sources` entry has `resolved=False` and non-null `error_code` and `error_message`. Verifies AC8, AC9, AC10.
- `test_resolve_per_source_two_sources_independence`: rows from source A (ok) and source B (`CatalogueError`); source A rows receive real catalogue data; source B rows get `source-unavailable`; each source resolved exactly once. Verifies AC9.
- `test_resolve_per_source_pack_not_found`: source ok; pack absent from catalogue; row tagged `reason="pack-not-found"`, `available_version=None`. Verifies AC6.
- `test_resolve_per_source_pack_absent_version`: source ok; pack present in catalogue dir; `pack.toml` parses but has no `version` key; row tagged `reason="unparseable-catalogue-version"` (not `pack-not-found`). Verifies AC6 and the absent-version ladder rule.
- `test_resolve_per_source_malformed_catalogue`: source ok; pack `pack.toml` raises `ConfigError`; row tagged `reason="malformed-catalogue"`. Verifies AC6.
- `test_resolve_per_source_incompatible_contract`: source ok; pack present; `pack_spec_version` major != `_major(SPEC_VERSION)`; row tagged `reason="incompatible-contract"`. Verifies AC6.
- `test_resolve_per_source_adapter_not_supported`: source ok; pack present, contract ok; row adapter absent from `[pack.install].allowed-adapters` (fixture pack.toml has `[pack.install]\nallowed-adapters = ["some-other-adapter"]`; row adapter is absent from this list); row tagged `reason="adapter-no-longer-supported"`. Verifies AC6.
- `test_resolve_per_source_no_adapter_contract_is_compatible`: source ok; pack present; `pack_spec_version(toml)` returns `None` (no `[pack.adapter-contract].version` field in pack.toml); row is NOT tagged `incompatible-contract` — the `None` case is vacuously compatible and the walk continues to the version step. Verifies AC6 and prevents `_major(None)` crash.
- `test_resolve_per_source_resolve_once_per_source`: two rows with the same canonical source; `resolve_catalogue` mock called exactly once. Verifies AC9.
- `test_resolve_per_source_error_message_redacts_user_info`: mock `CatalogueError` with a message containing `user:pass@host`; assert `sources[*].error_message` does not contain `"user:pass@"`. Verifies AC12 (URL user-info redaction).
- `test_resolve_per_source_error_message_redacts_query_token`: mock `CatalogueError` with a message containing `?access_token=SECRET`; assert `sources[*].error_message` does not contain `"SECRET"`. Verifies AC12 (query-string token redaction).
- `test_resolve_per_source_error_message_redacts_bearer`: mock `CatalogueError` with a message containing `Bearer abc123token`; assert `sources[*].error_message` does not contain `"abc123token"`. Verifies AC12 (bearer-token redaction).
- `test_resolve_per_source_ok_row_no_reason`: source ok, pack found, contract ok, adapter allowed, version present; row has `reason=None`, `available_version="<version>"`. Verifies AC6 (reason is null for non-unknown rows).
- `test_catalogue_positional_ignored_with_deprecation_warning`: invoke `run(args)` with `args.catalogue=str(tmp_path / "other-cat")` (a different path than the one in `PackState.source`) and a row whose `PackState.source` points to a real fixture catalogue containing the pack at a known version; capture stdout and stderr. Assert: (a) the deprecation string `"the catalogue positional is ignored"` appears on stderr; (b) the row resolves against `PackState.source` (the real catalogue — not the positional) and shows the expected `available_version`; (c) `args.catalogue` content plays no role in the output. Verifies that the no-op deprecation behavior is genuine.

**Approach:**
- Define internal `_RowCtx(reason: str | None, available_version: str | None)` (NamedTuple) to carry per-row resolution results.
- Implement `_resolve_per_source(rows: list[dict]) -> tuple[list[dict], dict[tuple[str, str, str], _RowCtx]]`:
  - `row_ctx_map` keyed by `(scope, pack, adapter)` — three fields — not `(pack, adapter)`, because the same `(pack, adapter)` pair can be installed at both user and repo scope with different provenance (AC9 requires per-row correctness).
  - Group rows by `canonicalize_source(row["_pack_state"].source)`.
  - Rows where `canonicalize_source` returns `None` → immediately tagged `_RowCtx(reason="source-unknown", available_version=None)`; not added to `sources` list.
  - For each unique non-None canonical source:
    - Try `resolve_catalogue(source)`.
    - On `CatalogueError`: all rows in this group get `_RowCtx(reason="source-unavailable", available_version=None)`; append `{"source": source, "resolved": False, "error_code": "catalogue-error", "error_message": _redact_error(str(exc))}` to sources list.
    - On success: walk catalogue with `_discover_pack_dirs` + `load_pack_toml`; build `{pack_name: _RowCtx}` using the reason-code ladder; per-row: apply adapter check.
    - Append `{"source": source, "resolved": True, "error_code": None, "error_message": None}` to sources list.
  - Reason-code ladder (applied per pack in the catalogue walk, then per row):
    1. `ConfigError` loading `pack.toml` → `reason="malformed-catalogue"`
    2. Pack name absent from catalogue → `reason="pack-not-found"`
    3. `pack_spec_version(toml)` returns non-`None` **and** its major differs from CLI major → `reason="incompatible-contract"`. When `pack_spec_version` returns `None` (adapter-contract version absent from pack.toml), the check is skipped — vacuously compatible; guard: `if declared is not None and _major(declared) != cli_major`. This matches the existing guard in `_resolve_latest` and prevents `_major(None)` from crashing.
    4. Per-row: adapter absent from `[pack.install].allowed-adapters` (accessed as `pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters")`; list present) → `reason="adapter-no-longer-supported"`
    5. `pack.get("version")` is absent or not a string → `reason="unparseable-catalogue-version"`, `available_version=None`
    6. Otherwise → `reason=None`, `available_version=pack.get("version")`
  - `_redact_error(msg: str) -> str`: (1) replace URL user-info patterns (`[^/@]+:[^/@]+@`) with `***@`; (2) replace query-string credential tokens (`[?&]<key>=<val>` where key contains `token`, `key`, `secret`, `password`, or `auth`, case-insensitive) with `?<key>=***`; (3) replace any `Bearer\s+\S+` occurrence (with or without a preceding `Authorization:` prefix) with `Bearer ***`. Uses only `re.sub`; no full URI parser. Credential-free messages pass through unchanged.
  - Return `(sources_list, row_ctx_map)` where `row_ctx_map` is keyed by `(scope, pack, adapter)`.
  - `sources_list` is sorted ascending by canonical source string before returning (satisfies AC14 sources[] ordering).
- **Delete `_resolve_latest`** (`list_installed.py:119-156`) once `_resolve_per_source` is wired in — it becomes dead code after T2 and must not remain.
- **`catalogue` positional deprecation warning:** at the top of `run()`, after reading `check`, add: `if getattr(args, "catalogue", None) is not None: print("agentbundle list-installed: the catalogue positional is ignored; rows are resolved against their recorded provenance. Use --no-check to skip resolution entirely.", file=sys.stderr)`. This is the only code change relating to `args.catalogue` in this spec.
- **Import `re`** at the module top alongside `json` (needed for `_redact_error`). Add `import re` to `list_installed.py`.
- **Migrate three existing command-level tests** that currently use `args.catalogue` to supply catalogue data and `PackState` with no `source` (after this change, `canonicalize_source(None)` → `None` → `source-unknown`):
  1. `test_lists_repo_rows_with_columns` (`test_list_installed_cmd.py:154`): give the `PackState` `source=str(cat)` (the fixture catalogue path); remove `catalogue=str(cat)` from `_make_args`. The test will exercise the `upgrade-available` path via per-source resolution.
  2. `test_unresolvable_catalogue_degrades_to_unknown` (`test_list_installed_cmd.py:183`): give the `PackState` `source="git+ssh://example.test/repo"` (raises `CatalogueError` immediately via the SSH-deferred guard in `catalogue.py:63-66` — no network required); remove `catalogue=str(tmp_path / "nope")` from `_make_args`. Note: a non-existent local path does NOT raise `CatalogueError` — `resolve_catalogue` returns `Path(uri)` unconditionally for local paths and `_discover_pack_dirs` returns `[]`, so the row degrades via `pack-not-found` not `source-unavailable`. The SSH URI gives a genuine `source-unavailable`. The test still asserts `"unknown" in out` and `"—" in out`.
  3. `test_resolved_catalogue_missing_pack_is_unknown` (`test_list_installed_cmd.py:199`): give the `PackState` `source=str(cat)` (the fixture catalogue that contains `some-other-pack` but not `architect`); remove `catalogue=str(cat)` from `_make_args`. The test still asserts `"architect" in out and "unknown" in out` — now via `pack-not-found` rather than the old lookup semantics.
- In `run()`: replace the `_resolve_latest` call block with `_resolve_per_source` **only when `check is True`** (i.e., `--no-check` is not active). When `check is False`: skip `_resolve_per_source`, set `sources_list = []`, set all row ctx to `_RowCtx(reason=None, available_version=None)`, and pass `check=False` downstream to suppress status computation. This preserves the existing `--no-check` gate.
- **Row enrichment step** (run() wiring, after `_resolve_per_source`): iterate all rows and write back per-row computed fields into the row dict:
  ```
  for row in rows:
      key = (row["scope"], row["pack"], row["adapter"])
      ctx = row_ctx_map[key]
      row["canonical_source"] = canonicalize_source(row["_pack_state"].source)
      row["available_version"] = ctx.available_version
      status, reason = _compute_status_pair(row["installed"], ctx.available_version, reason_ctx=ctx.reason) if check else (None, None)
      row["status"] = status
      row["status_reason"] = reason
  ```
  This ensures both `_render_json` and `_print_table` read `available_version`, `canonical_source`, `status`, `status_reason` directly from the row dict, with no separate parameter. `per_row_status` as a separate dict is eliminated.

**Done when:** all T2 tests pass; `resolve_catalogue` called at most once per unique canonical source in an invocation.

---

### T3: Add `--format` and `--updates-only` to argument parser

**Depends on:** none (parallel-safe with T1 and T2)

**Touches:** `packages/agentbundle/agentbundle/cli.py`

**Tests (TDD):**
- `test_format_default_is_table`: parse args with no `--format`; assert `args.format == "table"`. Verifies AC1.
- `test_format_json_accepted`: parse `["--format", "json"]`; assert `args.format == "json"`. Verifies AC2.
- `test_format_invalid_rejected`: `["--format", "xml"]`; assert argparse error. Verifies no accidental acceptance.
- `test_updates_only_default_false`: no flag; assert `args.updates_only is False`. Verifies AC11.
- `test_updates_only_flag_sets_true`: `["--updates-only"]`; assert `args.updates_only is True`. Verifies AC11.

**Approach:**
- Add to the `list-installed` subparser in `cli.py` (after the existing `--check-drift` argument):
  ```python
  sp.add_argument(
      "--format",
      choices=["table", "json"],
      default="table",
      help="Output format: table (default) or json.",
  )
  sp.add_argument(
      "--updates-only",
      action="store_true",
      default=False,
      help=(
          "Show only rows needing attention (upgrade-available, ahead, unknown). "
          "Summary counts always reflect the full set. No effect under --no-check."
      ),
  )
  ```
- In `run()`, read with `getattr(args, "format", "table")` and `getattr(args, "updates_only", False)`.
- Update the `catalogue` positional's `help=` string in `cli.py:245-249` to reflect that it is now deprecated and ignored: `"[Deprecated] Catalogue URI — now ignored; rows are resolved against their recorded provenance. Use --no-check to skip catalogue resolution entirely."`

**Done when:** all T3 tests pass; `agentbundle list-installed --help` shows both new flags with accurate descriptions including the `--updates-only` summary and `--no-check` interaction note. `pyproject.toml` + `CLI_VERSION` bumped; `packages/agentbundle/README.md` and `docs/product/changelog.md` updated. `grep "--format"` in help output and `grep "ahead" docs/product/changelog.md` both hit. Verifies AC20.

---

### T4: JSON output renderer

**Depends on:** T1, T2, T3

**Touches:** `packages/agentbundle/agentbundle/commands/list_installed.py`

**Tests (TDD):**
- `test_json_schema_version_is_int_1`: parse stdout JSON; assert `result["schema_version"] == 1` and `isinstance(result["schema_version"], int)`. Verifies AC3.
- `test_json_all_top_level_fields_present`: assert all fields present: `schema_version`, `command`, `scope`, `updates_only`, `sources`, `rows`, `summary`. Verifies AC3.
- `test_json_row_all_fields_present`: each row has `pack`, `adapter`, `scope`, `source`, `installed_version`, `available_version`, `status`, `status_reason`, `drift_count`. Verifies AC3.
- `test_json_rows_sorted_by_scope_pack_adapter`: three rows in non-sorted order; assert `[(r["scope"], r["pack"], r["adapter"]) for r in result["rows"]]` is sorted ascending. Verifies AC3, AC14.
- `test_json_sources_sorted_by_canonical_source`: two resolved sources with names out-of-alphabetical-order; assert `[s["source"] for s in result["sources"]]` is sorted ascending. Verifies AC14.
- `test_json_status_reason_null_for_non_unknown`: row with `status="up-to-date"`; assert `status_reason is None`. Verifies AC4.
- `test_json_status_reason_set_for_unknown`: row with `status="unknown"`; assert `status_reason` is one of the eight codes. Verifies AC4, AC6.
- `test_json_updates_only_filter`: one `up-to-date` row + one `upgrade-available` row + `--updates-only`; assert only `upgrade-available` in `rows`; assert `summary["total"] == 2`. Verifies AC11.
- `test_json_updates_only_no_check_shows_all`: `--updates-only --no-check`; all rows shown (status is null, filter has no effect). Verifies AC11 interaction.
- `test_json_summary_counts`: two rows — one `up-to-date` + one `ahead`; assert `summary == {"total": 2, "up_to_date": 1, "upgrade_available": 0, "ahead": 1, "unknown": 0}`. Verifies AC11.
- `test_json_diagnostics_on_stderr_only`: capture stdout and stderr; assert all warning text on stderr, none on stdout. Verifies AC2.
- `test_json_stdout_is_valid_json`: assert `json.loads(stdout)` succeeds. Verifies AC2, AC3.
- `test_json_no_table_chars_in_stdout`: assert stdout does not contain table separator patterns from `render_table`. Verifies AC2.
- `test_json_source_null_for_unknown_provenance`: row with `PackState.source=None`; assert `rows[0]["source"] is None`. Verifies AC12.
- `test_json_sources_array_resolved_and_failed`: one resolved source + one `CatalogueError` source; assert two entries: first with `resolved=True, error_code=None, error_message=None`; second with `resolved=False` and non-null `error_code` and `error_message`. Verifies AC10.
- `test_json_unknown_source_not_in_sources_array`: all rows with `PackState.source=None`; assert `sources == []`. Verifies AC10.
- `test_json_drift_count_null_without_flag`: no `--check-drift`; every row's `drift_count is None`. Verifies contract.
- `test_json_drift_count_integer_with_flag`: `--check-drift --format json`; one row with a locally edited file; assert that row's `drift_count` is an integer `>= 1`; all other rows have `drift_count == 0`. Verifies AC3 (`drift_count` populated path) and Boundary (--check-drift works in JSON mode).
- `test_json_no_check_nulls_status_fields`: `--no-check --format json`; every row has `available_version=null`, `status=null`, `status_reason=null`; `sources == []`. Verifies AC15.
- `test_json_no_check_summary_total_equals_row_count`: `--no-check --format json`; two rows installed; assert `summary.total == 2` and `summary.up_to_date == 0` and `summary.upgrade_available == 0` and `summary.ahead == 0` and `summary.unknown == 0`. Verifies --no-check summary contract.
- `test_json_row_exact_key_set`: each row in JSON output has exactly the nine contract keys: `pack`, `adapter`, `scope`, `source`, `installed_version`, `available_version`, `status`, `status_reason`, `drift_count` — no internal keys (e.g. `_pack_state`, `canonical_source`, `installed`) and no unlisted fields. Verifies AC3 (contract field fidelity).
- `test_json_scope_all_when_no_scope_arg`: no `--scope`; assert `result["scope"] == "all"`. Verifies AC3.
- `test_json_empty_result`: no packs installed; assert valid JSON with `rows=[]`, `sources=[]`, `summary.total==0`; also assert stdout does not contain `"no packs installed"` (the prose path must be suppressed). Verifies § "JSON Contract" empty-result note and AC2 (no prose on stdout in json mode).

**Approach:**
- Add `_render_json(rows: list[dict], sources: list[dict], *, scope_val: str, updates_only: bool, check: bool) -> str` (no `want_drift` parameter — the function reads `row.get("drift")` directly; `None` signals `--check-drift` was inactive and `want_drift` is redundant):
  - Rows carry enriched fields (`available_version`, `canonical_source`, `status`, `status_reason`) written by the run() wiring step; no separate `per_row_status` parameter.
  - Build the full result dict. **Construct per-row JSON dicts explicitly** (do not serialize raw row dicts): map `row["installed"]` → `installed_version`, `row["canonical_source"]` → `source`, `row.get("drift")` → `drift_count` (this key is written by the existing `--check-drift` computation, not the T2 enrichment step; `None` when `--check-drift` is not active), etc. Emit exactly the nine contract keys per row — no internal keys (`_pack_state`, `canonical_source`, `installed`, etc.) and no extra fields. This avoids serialization crashes (`PackState` is not JSON-serializable) and prevents contract violations.
  - Apply `--updates-only` filter: skip rows where `row["status"] == "up-to-date"`. Skip filter entirely when `check is False` (--no-check active — all statuses are None, filter has no effect).
  - Under `--no-check`: `summary.total` equals the full row count; status buckets `up_to_date/upgrade_available/ahead/unknown` are all `0`.
  - `json.dumps(result, indent=2)` — deterministic because rows are pre-sorted.
  - All `print(..., file=sys.stderr)` warnings remain unchanged.
- Import `json` from stdlib at module top.
- **`fmt`, `updates_only`, and `scope_val` must be read at the very top of `run()`, before the empty-result check at line 65.** Read them as: `fmt = getattr(args, "format", "table")`, `updates_only = getattr(args, "updates_only", False)`, and `scope_val = getattr(args, "scope", None) or "all"`. These reads must precede the `_collect_rows` call and the empty-row guard.
- In `run()`: if `fmt == "json"`: call `_render_json` and `print(json_str)` to stdout; skip `_print_table`.
- **In `run()`: the existing empty-result early return at `list_installed.py:65-68` unconditionally prints `"no packs installed at …"` to stdout and returns before any format branching.** This must be made format-aware: when `not rows` and `fmt == "json"`, call `_render_json([], [], scope_val=scope_val, updates_only=updates_only, check=check)` and `print(json_str)` to stdout (emitting the empty JSON contract document per spec § "JSON Contract" empty-result note) instead of printing prose. When `fmt == "table"`, the existing prose path is retained.

**Done when:** all T4 tests pass; `agentbundle list-installed --format json` produces valid JSON with all contract fields.

---

### T5: Update table output — SOURCE column, four-value status, `--updates-only`

**Depends on:** T1, T2, T3

**Touches:** `packages/agentbundle/agentbundle/commands/list_installed.py`

**Tests (TDD):**
- `test_table_no_source_column_single_source`: all rows share one canonical source; assert `"SOURCE"` not in captured stdout. Verifies AC13 (OQ1).
- `test_table_source_column_multi_source`: rows from two distinct canonical sources; assert `"SOURCE"` in stdout. Verifies AC13.
- `test_table_source_truncated_to_40_visible_chars`: source URI of 60 chars; assert displayed value is at most 40 visible chars (including `…`). Verifies AC13.
- `test_table_null_source_shows_dash_in_source_column`: multi-source result where one row has `PackState.source=None`; assert that row's SOURCE cell displays `—`. Verifies AC13.
- `test_table_user_info_source_shows_dash`: row with a user-info source (`canonicalize_source` returns `None`); multi-source context; assert no user-info substring in stdout. Verifies AC12.
- `test_table_source_column_count_pre_filter`: result has three rows — two from source A (`up-to-date`), one from source B; `--updates-only` hides source A rows; assert SOURCE column is still shown (source count computed pre-filter, two distinct sources). Verifies AC13, AC1.
- `test_table_ahead_status_displayed`: row with installed > available; assert `"ahead"` in stdout. Verifies AC1.
- `test_table_updates_only_excludes_up_to_date`: `--updates-only` with one `up-to-date` row + one `upgrade-available` row; assert `up-to-date` row absent from stdout. Verifies AC11.
- `test_table_updates_only_includes_unknown`: `--updates-only` with an `unknown` row; assert it is present in stdout. Verifies AC11.
- `test_table_sort_order_scope_pack_adapter`: three rows in non-sorted order; assert stdout order matches (scope, pack, adapter) sort. Verifies AC14.
- `test_table_updates_only_no_check_shows_all`: `--updates-only --no-check`; result with one row that would be `up-to-date` under normal resolution; assert the row is present in stdout (status is null, filter has no effect). Verifies AC11 interaction.
- `test_table_drift_column_rendered_with_flag`: `--check-drift --format table`; one row with a locally edited file; assert `"DRIFT"` header in stdout and that row's drift count is `>= 1`; all other rows show `0`. Verifies the DRIFT column survives the `_print_table` signature refactor.

**Approach:**
- Update `_collect_rows` sort key from `(r["pack"], r["adapter"], r["scope"])` to `(r["scope"], r["pack"], r["adapter"])`; also update the `_collect_rows` docstring from `"Sorted by (pack, adapter, scope)"` to `"Sorted by (scope, pack, adapter)"`.
- Update `_print_table` to read enriched fields (`available_version`, `canonical_source`, `status`, `status_reason`) directly from row dicts. Remove the separate `latest_by_pack` and `catalogue_resolved` parameters — all data lives in the row dicts after the run() enrichment step. No `per_row_status` parameter.
- SOURCE column: count distinct canonical sources across the full pre-filter rows; `len(set(r["canonical_source"] for r in all_rows if r["canonical_source"])) >= 2` → add column. Truncate to 40 visible chars (`val[:39] + "…"` when `len(val) > 40`). Null-source rows display `—`.
- STATUS cell: use `row["status"]`; display the status string (reason code is available in JSON; table shows status only).
- LATEST cell: use `row["available_version"] or "—"`.
- When `check is False` (`--no-check`): omit LATEST, STATUS, and SOURCE columns from the table — preserving the state-only column set from install-state-visibility AC.
- Apply `--updates-only` filter: skip rows where `row["status"] == "up-to-date"` when `updates_only=True`; no filter when `check is False`.
- **DRIFT column is preserved.** The existing DRIFT column (enabled by `--check-drift`) is not removed by this refactor. The drift count is sourced from `row.get("drift")` — written by the existing drift computation before `_print_table` is called — not from the T2 enrichment step. The refactored `_print_table` must continue to read and render this key when `want_drift=True`.
- Update existing test `test_collect_rows_sorted_across_scopes` (in `packages/agentbundle/tests/unit/test_list_installed_cmd.py`) to reflect the new `(scope, pack, adapter)` sort order. This is an existing shipped test that will fail on the sort-order change.
- Add T5 test `test_table_no_check_omits_status_columns`: `--no-check --format table`; assert stdout does not contain "STATUS" or "LATEST" or "SOURCE" column headers. Verifies --no-check column suppression.

**Done when:** all T5 tests pass; the updated `test_collect_rows_sorted_across_scopes` passes; `_status_for` is deleted from `list_installed.py` (T5 is the last caller's migration; deletion is owned here). Visual inspection of output is deferred to T6 golden files.

---

### T6: D6 layout checks, snapshot tests, and suite regression

**Depends on:** T4, T5

**Touches:** `packages/agentbundle/tests/` (new fixtures and tests)

**Tests (goal-based):**
- `test_table_golden_80col`: invoke `list-installed --format table` against a known three-row fixture (including a Unicode adapter name); compare stdout to golden file at `packages/agentbundle/tests/fixtures/list-installed/golden_80col.txt`. Note: `render_table` is content-sized (no width-dependent behavior in non-TTY capture), so `golden_80col.txt` and `golden_120col.txt` are expected to be byte-identical — both exist for RFC-0072 D6 traceability, serving as determinism snapshots.
- `test_table_golden_120col`: same invocation; compare to `golden_120col.txt` (expected identical to `golden_80col.txt`).
- `test_table_column_alignment_mixed_lengths_and_unicode`: fixture has rows with very short, very long ASCII names, and a Unicode pack/adapter identifier (e.g., `"análysis"`); assert column separator character offsets are identical across all data rows. Verifies AC16.
- `test_json_schema_version_all_fixtures`: parametrize over all JSON-producing test fixtures; assert `json.loads(stdout)` succeeds and `result["schema_version"] == 1`. Verifies AC16.
- `test_table_long_pack_name_no_broken_structure`: pack name of 40 characters; assert no misaligned separators or broken table structure (the column widens to accommodate — no truncation or spillover). Verifies AC16 D6 layout assertion for long pack/adapter names.
- `test_subprocess_exit_0_on_catalogue_failure`: subprocess invocation against a fixture where a row has `PackState.source="git+ssh://example.test/repo"` — `resolve_catalogue` raises `CatalogueError` ("SSH git URLs deferred") immediately without network; assert process exit code 0; assert the affected row has `status="unknown"`, `status_reason="source-unavailable"` in JSON output. Note: a non-existent local path does NOT raise `CatalogueError` — `resolve_catalogue` returns `Path(uri)` for all local paths (`catalogue.py:71-72`); only SSH/malformed-HTTPS URIs raise reliably without network. Verifies AC17.
- `test_no_state_mutation`: record state file mtime; invoke `list-installed --format table` and `--format json`; assert mtime unchanged. Verifies AC18.
- `pytest packages/agentbundle/ -x` exits 0; `git diff pyproject.toml` shows no new dependency entries. Verifies AC19.
- `grep -r '"agent-ready-repo"' packages/agentbundle/agentbundle/commands/list_installed.py` returns zero lines.

**Approach:**
- Record golden files AFTER T5 is complete and visually verified. Do not record from any erroneous baseline (per RFC-0072 D6 risk). The two golden files (`golden_80col.txt`, `golden_120col.txt`) are expected to be identical since `render_table` is content-sized and non-TTY capture never invokes width-responsive behavior; both are committed for RFC-0072 D6 traceability.
- Store golden files in `packages/agentbundle/tests/fixtures/list-installed/`.
- Column alignment assertion: strip all leading/trailing whitespace from each line; measure character offset of each column separator; assert identical offsets across all data rows.

**Done when:** all D6 tests pass; golden files committed from verified correct output; subprocess exit-0 test passes; `pytest packages/agentbundle/ -x` exits 0; AC18 and AC19 verified.

## Risks

- **`adapter-no-longer-supported` check requires `[pack].allowed-adapters` to be populated.** If current packs do not declare this field, the check is vacuously "adapter always allowed" and the reason code never triggers. Mitigation: confirm field presence in actual pack.tomls before implementing T2; if absent everywhere, the check is correct by vacuity.
- **`canonicalize_source` dependency.** If `spec/packstate-source-provenance` is not merged when this spec is implemented, `canonicalize_source` is unavailable. Mitigation: require packstate-source-provenance to land first, or co-land both specs. Stated in Assumptions.
- **Column-width mock for D6 tests.** `render_table` may call `shutil.get_terminal_size()` to determine column widths; if not overridable by environment variable, tests require patching. Mitigation: inspect `render_table` implementation before writing T6; patch as needed.
- **Multi-source resolution performance for `git+https://` sources.** Resolving multiple remote sources in one invocation can be slow. Mitigation: per-invocation deduplication (one resolve per unique canonical source) is the only caching layer; document that `--no-check` skips all resolution.
- **Sort order change.** Changing from `(pack, adapter, scope)` to `(scope, pack, adapter)` changes the table row ordering for existing users. Deliberate per RFC-0072 D5; golden files in T6 capture the new order; erratum note added to install-state-visibility spec.

## Changelog

- 2026-07-24: initial plan
- 2026-07-24: adversarial review pass 1 — aligned JSON field names to RFC-0072 D5 (`available_version`, `resolved/error_code/error_message`) (Blocker 1); added erratum approach for install-state-visibility sort order (Concern 2); added T4 JSON sort order test (Concern 4); added T5 credential redaction test and null-source cell test (Concerns 5, Nit 13); added T2 error redaction test and helper (Concern 6); specified --updates-only+--no-check interaction (Concern 7); fixed T2 ladder: absent version → unparseable-catalogue-version (Concern 8); added T4 empty-result test (Concern 9); fixed T2 Depends on (Concern 10); fixed 40-char rule to 40 visible chars total (Concern 11); added Unicode fixture to T6 (Concern 12); added subprocess exit-0 test for AC17 (Concern 3); added pre-filter source count for OQ1 (Concern from AC1/AC13 gap)
- 2026-07-24: adversarial review pass 2 — tightened _redact_error to cover URL user-info, query-string tokens; added T2 bearer-token test (Blocker 1); reordered _compute_status_pair to check catalogue version before installed version; added both-unparseable T1 test (Concern 2); specified sources[] sorted by canonical source + T4 test (Concern 3); added T6 long-pack-name truncation test (Concern 4); added T5 update for existing test + fixed erratum wording (Concern 5); added T5 --updates-only+--no-check table test (Concern 6); deferred T5 Done-when visual check to T6 golden files (Nit 7); clarified Unicode scope to Latin width-1 (Nit 8); noted _compute_status_pair step 2 as defensive (Nit 9)
- 2026-07-24: adversarial review pass 3 — extended _redact_error + T2 to cover Bearer tokens (Blocker 1); added AC20 for release plumbing (Blocker 2); added second erratum note to install-state-visibility covering STATUS values and column set (Concern 3); added --no-check gate to run() wiring in T2 Approach (Nit 4)
- 2026-07-24: adversarial review pass 4 — fixed bearer regex to `Bearer\s+\S+` without mandatory Authorization prefix; fixed row_ctx_map key to (scope, pack, adapter) to avoid cross-scope collisions; tightened AC20 to same-PR delivery + grep verification artifacts; updated T3 Done-when to remove escape-hatch (Blockers 1-2, Concern 3)
- 2026-07-24: adversarial review pass 5 — added row enrichment step in run() to write available_version/canonical_source/status/status_reason into row dicts; removed per_row_status parameter from renderers (Blocker 1); sources_list now sorted in _resolve_per_source before return (Concern 2); T5 now specifies --no-check column suppression for LATEST/STATUS/SOURCE + adds test (Concern 3)
- 2026-07-24: adversarial review pass 6 — qualified install-state-visibility erratum as "pending implementation" (Concern 1); specified summary under --no-check in contract + added T4 test (Concern 2); specified _render_json constructs explicit per-row dicts with exactly nine contract keys + added T4 test (Concern 3)
- 2026-07-24: adversarial review pass 7 — named `row.get("drift")` as the drift_count source key in T4 _render_json approach (Nit 2); added T4 test for --check-drift --format json path (Concern 1); added T5 test for DRIFT column survival after signature refactor + DRIFT preservation note in T5 Approach (Concern 1)
- 2026-07-24: adversarial review pass 8 — added T4 Approach step for empty-result JSON path (Blocker 1); added T1 step to remove/migrate six legacy _status_for tests (Blocker 2); clarified T6 golden files are expected identical (content-sized table, Concern 3) + dropped column-width-control note; corrected spec.md § OQ1 render_table-truncates claim and AC16 (Concern 4); added T2 step to delete _resolve_latest (Nit 5)
- 2026-07-24: adversarial review pass 9 — added module docstring update step to T2 (Concern 1); added _collect_rows docstring update to T5 Approach (Concern 2); specified that fmt/updates_only must be read at top of run() before empty-result check + enumerated _render_json kwargs in empty-path call (Nit 3); added prose-absence assertion to test_json_empty_result (Nit 4)
- 2026-07-24: adversarial review pass 10 — added Design Decision recording catalogue positional as deprecated no-op + T2 deprecation warning step + migration of three existing command-level tests (Blocker 1); preserved declared-is-not-None guard in T2 ladder step 3 + added T2 no-adapter-contract test (Concern 2); added scope_val read to top-of-run() note (Nit 3); added re import note to T2 (Nit 4); assigned _status_for deletion to T5 Done-when (Nit 5)
- 2026-07-24: adversarial review pass 11 — changed T6 subprocess test to use git+ssh:// URI for reliable CatalogueError (Blocker 1); corrected T2 migration step 2 rationale (non-existent local path → pack-not-found not source-unavailable; use git+ssh:// for source-unavailable, Concern 2); added T3 step to update catalogue positional help text to deprecated (Concern 3)
- 2026-07-24: adversarial review pass 12 — added T2 test for catalogue positional deprecation warning (asserts warning on stderr + positional genuinely ignored, Concern 1)
- 2026-07-24: adversarial review pass 13 — corrected allowed-adapters TOML path from [pack] to [pack.install] in spec.md × 2 and plan.md T2 ladder + test (Blocker 1); dropped want_drift from _render_json signature and both call sites (Nit 2)
- 2026-07-24: adversarial review pass 14 — clarified erratum lifecycle in plan.md Design Decisions + spec.md Assumption (spec PR adds pending marker; implementing PR drops the qualifier, Concern 1); pinned git+ssh canonicalization as non-None as explicit Assumption in spec.md (Concern 2)
