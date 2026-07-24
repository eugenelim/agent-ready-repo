# Spec: List-Installed Update Status

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D5, D6), spec/packstate-source-provenance (canonicalize_source for source display), spec/install-state-visibility (existing list-installed behavior being extended)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`agentbundle list-installed` currently produces a human-readable table only. It has no machine-readable output, no `ahead` status (when an installed version is newer than the catalogue), no actionable reason codes for unknown rows, and resolves a single default catalogue regardless of each row's recorded provenance. CI automation of upgrade decisions is not possible.

This spec delivers: a `--format table|json` flag (table default; backward-compatible); four status values (`up-to-date`, `upgrade-available`, `ahead`, `unknown`); machine-readable reason codes for every `unknown` row; a `--updates-only` filter flag; per-source catalogue resolution so one source failure does not hide rows from other sources; a stable JSON contract at schema_version 1 (per RFC-0072 D5); credential-redacted source strings in both table and JSON output; and clean JSON-only stdout in `--format json` mode with all diagnostics on stderr. The command remains read-only on every path.

## Boundaries

### Always do

- Read all state files read-only — `list-installed` never writes.
- Apply `canonicalize_source()` (from `spec/packstate-source-provenance`) to every source string before it appears in table or JSON output; this redacts credentials and normalizes the URI.
- Group rows by canonical source; resolve each unique canonical source exactly once per invocation.
- Degrade gracefully when a source fails to resolve: report the source as `resolved: false` in the `sources` array; assign the affected rows status `unknown` / `source-unavailable`; continue listing rows from all other sources uninterrupted.
- Route all diagnostics (progress, warnings, errors) to stderr in `--format json` mode; stdout carries exactly one valid JSON document.
- Sort rows deterministically by (scope, pack, adapter) in both table and JSON output.
- Compute `summary` counts over the full unfiltered row set regardless of `--updates-only`.
- Redact credentials from `sources[*].error_message` before writing to JSON — no URL user-info (`user:pass@`), query-string credential tokens (`?access_token=…`, `?api_key=…`, etc.), or bearer-token values in any output. `_redact_error` must cover all three forms.
- Use Python 3.11 stdlib only — no new runtime dependencies.
- Preserve backward compatibility: `--format table` (the default) produces the same column layout as today plus the new status values and a conditional SOURCE column (OQ1); `--no-check` and `--check-drift` continue to work in both table and JSON modes.

### Ask first

- Any change to the exit codes or argument shapes of the existing flags (`--no-check`, `--check-drift`, `--scope`, `catalogue` positional).
- Adding any runtime dependency.
- Changing `schema_version` from the integer `1`.
- Omitting any field from the JSON contract below, or adding a non-null field not listed there.
- Changing the `--updates-only` summary behavior (summary is always pre-filter; rows are post-filter).

### Never do

- Write to state files or project the catalogue — this command is always read-only.
- Emit credentials, bearer tokens, URL user-info, or Authorization header content to stdout or stderr.
- Include source strings not passed through `canonicalize_source()` in any output.
- Include raw error strings from `CatalogueError` in `sources[*].error_message` without redacting credential-carrying content (URL user-info, query-string tokens such as `access_token`/`api_key`, or bearer-token values).
- Mix human prose or table content into stdout in `--format json` mode.
- Return a non-zero exit code for catalogue resolution failures — degrade to `unknown` rows and exit 0.
- Introduce a new runtime dependency.
- Introduce a state schema version bump.

## JSON Contract

Schema version 1, per RFC-0072 D5. The following is the canonical shape; all string fields are non-null unless otherwise stated.

```json
{
  "schema_version": 1,
  "command": "list-installed",
  "scope": "repo|user|all",
  "updates_only": false,
  "sources": [
    {
      "source": "<credential-redacted canonical URI>",
      "resolved": true,
      "error_code": null,
      "error_message": null
    }
  ],
  "rows": [
    {
      "pack": "core",
      "adapter": "claude-code",
      "scope": "repo|user",
      "source": "<credential-redacted canonical URI, or null>",
      "installed_version": "0.13.6",
      "available_version": "0.13.7",
      "status": "upgrade-available",
      "status_reason": null,
      "drift_count": null
    }
  ],
  "summary": {
    "total": 1,
    "up_to_date": 0,
    "upgrade_available": 1,
    "ahead": 0,
    "unknown": 0
  }
}
```

Field notes:

- `schema_version`: integer `1`, not a string.
- `scope`: the value passed to `--scope`, or `"all"` when `--scope` is omitted.
- `updates_only`: reflects the `--updates-only` flag; rows are filtered but summary counts are not.
- `sources[*].resolved`: `true` when the source resolved successfully; `false` when resolution errored. Rows with unknown provenance (reason `source-unknown`) are not listed in the `sources` array.
- `sources[*].error_code`: `null` on success; a machine-readable error token (e.g. `"catalogue-error"`) on failure.
- `sources[*].error_message`: `null` on success; a human-readable, credential-redacted error string on failure.
- `rows[*].source`: `canonicalize_source(PackState.source)` — the normalized, credential-redacted canonical URI; `null` when source is unknown (i.e., `canonicalize_source` returns `None`).
- `rows[*].available_version`: the version string from the source catalogue's `pack.toml`; `null` when status is `unknown`, or when `--no-check` suppresses catalogue resolution.
- `sources[]` ordering: sorted ascending by canonical source string. Deterministic regardless of the order in which sources are resolved.
- `rows[*].status`: one of `up-to-date|upgrade-available|ahead|unknown`. `null` when `--no-check` is active.
- `rows[*].status_reason`: `null` when status is not `unknown`; a reason code string (from the closed set below) when status is `unknown`. `null` when `--no-check` is active.
- `rows[*].drift_count`: `null` unless `--check-drift` is also active, in which case it is an integer count of locally edited files.
- When no rows are installed, `"rows": []`, `"sources": []`, `"summary": {"total": 0, "up_to_date": 0, "upgrade_available": 0, "ahead": 0, "unknown": 0}` — the document is still valid JSON with all fields present.
- Under `--no-check`: `summary.total` equals the row count; the four status buckets (`up_to_date`, `upgrade_available`, `ahead`, `unknown`) are all `0` (no statuses were computed). `total` may differ from the sum of status buckets in this mode.
- Summary counts always reflect the full pre-filter set, even when `--updates-only` is active.

## Status Semantics

| Status | Condition | status_reason |
|--------|-----------|---------------|
| `up-to-date` | installed_version == available_version (dotted numeric, zero-padded) | null |
| `upgrade-available` | available_version > installed_version | null |
| `ahead` | installed_version > available_version | null |
| `unknown` | any condition below | see reason code |

`unknown` reason codes — evaluated in order; first applicable wins:

| Reason code | Condition |
|-------------|-----------|
| `source-unknown` | `canonicalize_source(PackState.source)` returns `None` (covers `None`, `"agent-ready-repo"`, and any other uncanonicalizable source value) |
| `source-unavailable` | canonical source is non-null but `resolve_catalogue()` raises `CatalogueError` |
| `malformed-catalogue` | catalogue resolved but the pack's `pack.toml` raises `ConfigError` on load |
| `pack-not-found` | catalogue resolved, all `pack.toml` files parse cleanly, but this pack name is absent from the catalogue directory |
| `incompatible-contract` | pack present; `pack_spec_version` major does not match the CLI's `SPEC_VERSION` major |
| `adapter-no-longer-supported` | pack present, contract compatible; the row's adapter is absent from `[pack.install].allowed-adapters` (only checked when the list is explicitly declared; matches the location used by `upgrade.py:399`) |
| `unparseable-catalogue-version` | pack found, adapter allowed; the catalogue `version` field is absent or cannot be parsed into a dotted numeric tuple |
| `unparseable-installed-version` | catalogue version is parseable; `PackState.installed_version` cannot be parsed into a dotted numeric tuple |

**Absent `version` field in `pack.toml`:** if a pack is found in the catalogue but its `pack.toml` has no `version` key (or its value is not a string), the reason code is `unparseable-catalogue-version`, not `pack-not-found`. The pack was found; its version is the missing element.

**Ordering in `_compute_status_pair`:** the check for catalogue-version parseability (step 7 in the spec ladder) must occur before the check for installed-version parseability (step 8). When both versions are unparseable, the result is `unparseable-catalogue-version`.

## OQ1 Resolution — Source Column in Table Output

The RFC-0072 open question OQ1 ("Should `list-installed` show a source identity column in the default table output?") is resolved here:

**Show the SOURCE column only when 2+ distinct canonical sources are present in the result set.** The source count is computed over the full result set before any `--updates-only` filtering, so the SOURCE column decision is stable even when all matching rows share one source. When all rows share one source, the column is omitted to reduce noise. Source strings are displayed as at most 40 visible characters total (including the trailing `…` when truncated, so the content portion is at most 39 characters). Rows with unknown provenance (`source: null`) display `—` in the SOURCE cell when the column is present. The JSON contract always includes `rows[*].source` regardless of source count.

**Pack/adapter name truncation:** `render_table` is content-sized — it widens each column to accommodate its longest value; it does not truncate PACK, ADAPTER, or version cells or wrap them with `…`. Long values expand the column rather than causing spillover. The D6 layout assertion for long pack/adapter names therefore verifies that table structure remains valid (no broken separators, no misaligned columns), not that values are truncated.

## `--updates-only` and `--no-check` Interaction

When both `--updates-only` and `--no-check` are active simultaneously, `--no-check` suppresses catalogue resolution and sets all row statuses to `null`. Because the filter is defined over status values (`upgrade-available`, `ahead`, `unknown`) and `null` matches none of these, `--updates-only` has no effect: all rows are shown. This is the correct behavior — with no status information, no row can be classified as `up-to-date`, so none should be excluded.

## Testing Strategy

- **TDD** for `_compute_status_pair(installed, available_version, reason_ctx) -> tuple[str, str | None]`: pure function over the four statuses and all eight reason codes. Red stubs before production code.
- **TDD** for multi-source grouping: given rows with mixed sources (canonical, `None`, `"agent-ready-repo"`), assert each unique canonical source is resolved exactly once via a mock `resolve_catalogue`; rows with unknown provenance get `source-unknown`; rows from a failed source get `source-unavailable`; rows from a successful source get a real status.
- **TDD** for JSON output structure: `json.loads(stdout)` succeeds; all required fields present; `schema_version == 1` as integer; summary counts match unfiltered row set; `rows[]` are sorted by (scope, pack, adapter).
- **TDD** for `--updates-only`: `up-to-date` rows absent from output; summary counts include them.
- **TDD** for credential redaction: a `PackState.source` containing URL user-info is `null` in JSON `rows[*].source`; a `CatalogueError` carrying a URI is redacted in `sources[*].error_message`; no user-info string appears in table SOURCE column.
- **TDD** for OQ1 source column: single-source result set → no SOURCE column in table; multi-source result set → SOURCE column present, ≤40 visible chars per cell; `null`-source rows show `—` in the SOURCE cell.
- **Goal-based** for existing flags (`--no-check`, `--check-drift`, `--scope`): subprocess invocation confirms these work in both `--format table` and `--format json` modes.
- **Goal-based** for AC17 exit code: subprocess against a fixture with an unresolvable source exits 0; affected rows have `status: "unknown"`, `status_reason: "source-unavailable"`.
- **Goal-based** for D6 layout checks: golden-file tests at 80 and 120 column widths; Unicode identifier in fixture rows; JSON schema validation on all JSON-output tests (assert `schema_version == 1`).
- **Goal-based** for no state mutation: compare state file mtime before and after invocation — no write occurs on any path.

## Acceptance Criteria

- [ ] AC1: `--format table` (default) produces a table with the same column layout and ordering as today, except: STATUS now carries four values (`up-to-date`, `upgrade-available`, `ahead`, `unknown`); the SOURCE column appears when and only when 2+ distinct canonical sources are present in the result set (counted before `--updates-only` filtering).
- [ ] AC2: `--format json` writes exactly one valid JSON document to stdout; all diagnostics go to stderr; no table or human prose appears on stdout.
- [ ] AC3: JSON document matches the contract in § "JSON Contract": `schema_version` is the integer `1`; all required fields are present on every row; `rows[]` are ordered by (scope, pack, adapter).
- [ ] AC4: `status` takes exactly four values: `up-to-date`, `upgrade-available`, `ahead`, `unknown`. `status_reason` is non-null when and only when `status` is `unknown`.
- [ ] AC5: `ahead` status is returned when `_version_key(installed) > _version_key(available_version)` after zero-padding both tuples to equal length.
- [ ] AC6: `unknown` status includes a `status_reason` drawn from the closed set: `source-unknown`, `source-unavailable`, `malformed-catalogue`, `pack-not-found`, `incompatible-contract`, `adapter-no-longer-supported`, `unparseable-catalogue-version`, `unparseable-installed-version`. No other values are emitted.
- [ ] AC7: `source-unknown` is the reason when `canonicalize_source(PackState.source)` returns `None`; this covers `PackState.source == None`, `PackState.source == "agent-ready-repo"`, and any other value for which `canonicalize_source` returns `None`.
- [ ] AC8: `source-unavailable` is the reason when the canonical source is non-null but `resolve_catalogue()` raises `CatalogueError`.
- [ ] AC9: Each unique canonical source in the result set is resolved at most once per invocation. A `CatalogueError` from one source does not suppress rows from other sources.
- [ ] AC10: The `sources` array in JSON output lists only sources that were resolved or attempted; rows with reason `source-unknown` contribute no entry. Each entry carries `resolved: true|false`; on failure, `error_code` is a non-null machine-readable token and `error_message` is a credential-redacted human-readable string.
- [ ] AC11: `--updates-only` includes rows with status `upgrade-available`, `ahead`, or `unknown`; excludes rows with status `up-to-date`. The `summary` object always counts the full pre-filter set. When both `--updates-only` and `--no-check` are active, all rows are shown (status is null; filter has no effect).
- [ ] AC12: All source strings in table and JSON output are the output of `canonicalize_source()`; a source containing URL user-info is `null` in JSON and renders as `—` in the table SOURCE column. All `error_message` fields in the `sources` array are free of URL user-info, query-string credential tokens (e.g. `access_token`, `api_key`), and `Bearer <token>` values. Each of these three redaction forms is covered by a T2 test.
- [ ] AC13: OQ1 — SOURCE column appears in table output when and only when 2+ distinct canonical sources are present (counted pre-filter). Source strings in the table are displayed as at most 40 visible characters total (≤39 content characters + `…` when truncated). Rows with `null` source display `—` in the SOURCE cell.
- [ ] AC14: Rows output is sorted by (scope, pack, adapter) in both table and JSON output. `sources[]` in JSON output is sorted ascending by canonical source string.
- [ ] AC15: When `--no-check` / `--offline` is active, catalogue resolution is skipped in both table and JSON modes; `status`, `status_reason`, and `available_version` are `null` in JSON rows; the `sources` array is empty.
- [ ] AC16: D6 layout checks — two determinism golden-file snapshots (labeled 80col and 120col for RFC-0072 D6 traceability; the table is content-sized so both snapshots are identical and serve as a determinism check, not a width-behavior check); fixture includes at least one row with a Latin-Unicode pack or adapter identifier (width-1 chars; CJK wide glyphs are out of scope); column alignment assertions with mixed-length names; a long pack/adapter name expands the column without breaking table structure (no misaligned separators); all JSON-output tests assert `json.loads(stdout)` succeeds and `schema_version == 1`.
- [ ] AC17: Exit code is 0 when catalogue resolution fails — the command degrades to `unknown` rows and exits 0. Verified by subprocess test.
- [ ] AC18: No state mutation on any path. State file modification timestamps are unchanged after any invocation of `list-installed`.
- [ ] AC19: No new runtime dependency. `pyproject.toml` dependency list is unchanged; all new imports in `list_installed.py` are stdlib-only.
- [ ] AC20: Delivered in the same implementing PR — `agentbundle list-installed --help` documents `--format` (with valid choices `table`, `json`) and `--updates-only` (with a note about summary behavior and no-check interaction). `pyproject.toml` and `agentbundle/version.py CLI_VERSION` are bumped together. `packages/agentbundle/README.md` (PyPI README) and `docs/product/changelog.md` record `--format json`, `--updates-only`, and the `ahead` status value. Verified by: `grep "--format" <agentbundle list-installed --help output>` and `grep "ahead" docs/product/changelog.md`.

## Assumptions

- Technical: `spec/packstate-source-provenance` is implemented before or co-landed with this spec; `PackState.source` is `str | None = None` and `canonicalize_source(value: str | None) -> str | None` exists in `agentbundle.config`. (source: spec/packstate-source-provenance AC5)
- Technical: `canonicalize_source("git+ssh://example.test/repo")` returns a non-`None` value — the URI is well-formed (valid scheme, no user-info, no credential query-string or fragment) and AC9 of spec/packstate-source-provenance normalizes it as a remote URL rather than rejecting it. This property is relied upon by the T2 and T6 fixtures that produce `source-unavailable` via the SSH-deferred `CatalogueError`. The co-landing packstate implementation must honor this; if its remote-URL canonicalization rejects deferred schemes (returning `None`), those fixtures degrade to `source-unknown` instead and the source-unavailable path is untested.
- Technical: Rows with legacy provenance (`PackState.source == None` or `== "agent-ready-repo"`) get reason code `source-unknown`; `canonicalize_source` maps both to `None`. The user's recovery path is `agentbundle upgrade`, which migrates the source per RFC-0072 D3. (source: spec/packstate-source-provenance § Boundaries; RFC-0072 D3)
- Technical: `_version_key` (existing dotted-numeric parser in `list_installed.py`) is reused; `ahead` is the case `installed_key > available_key` after zero-padding. (source: `list_installed.py:159–190`)
- Technical: `resolve_catalogue(uri: str) -> Path` raises `CatalogueError` on resolution failure. (source: `catalogue.py:51–72`)
- Technical: The `[pack.install].allowed-adapters` list in `pack.toml` is checked for `adapter-no-longer-supported`; when the list is absent the check is vacuously "adapter is allowed" and the reason code is never triggered. Accessed as `pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters")`. (source: `upgrade.py:396-401`)
- Technical: `pack_spec_version(toml)` returns the declared `[pack.adapter-contract].version`; `_major(v)` extracts the major segment. (source: `config.py:99–105`; `commands/_common.py:213–216`)
- Technical: The sort order changes from the existing `(pack, adapter, scope)` (spec/install-state-visibility § Always do) to `(scope, pack, adapter)` as specified by RFC-0072 D5. The `install-state-visibility/spec.md` "Always do" boundary mandating `(pack, adapter, scope)` is superseded by this spec for all output modes. An erratum note is added to `install-state-visibility/spec.md` in **this spec PR** (already present as a "pending implementation" marker at line 54); the implementing (code) PR removes the "pending implementation" qualifier once the code ships. (source: RFC-0072 D5 "Deterministic output ordering"; install-state-visibility spec.md:54)
- Technical: JSON field names follow RFC-0072 D5 exactly: `available_version` (not `catalogue_version`); `sources[*]` uses `resolved`, `error_code`, `error_message` (not `status`, `error`). This is the wire format ratified as "costly-to-reverse" in RFC-0072. (source: RFC-0072 D5:277–303)
- Process: RFC-0072 is Accepted; D5 ratifies the CLI surfaces and JSON contract; D6 ratifies layout/usability checks. (source: RFC-0072 status 2026-07-23)
- Process: OQ1 from RFC-0072 ("Should `list-installed` show a source identity column?") is resolved in this spec: show SOURCE column only when 2+ distinct sources. The implementing PR must mark OQ1 resolved in RFC-0072 pointing at this spec. (source: RFC-0072 § Open questions OQ1)
- Product: `drift_count` in the JSON contract is `null` unless `--check-drift` is also active, maintaining compatibility with the existing flag. (source: RFC-0072 D5 JSON contract; spec/install-state-visibility)
