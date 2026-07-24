# Spec: Upgrade Bulk All

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D4, D5, D6), spec/packstate-source-provenance, spec/list-installed-update-status
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`agentbundle upgrade` requires a single named pack. There is no way to upgrade all installed packs at a scope in one operation, and multiple adapter rows for one pack — a pack can be installed for several IDE targets simultaneously — do not independently track their upgrade state. CI pipelines must run one `upgrade` per pack, with no machine-readable output and no preflight visibility before mutation.

This spec delivers `upgrade --all --scope repo|user`: a scoped bulk-upgrade operation that enumerates every `(pack, adapter)` row at the target scope, runs a full preflight phase — source resolution, version comparison, manifest validation, render, path-jail — that classifies all rows without writing anything, blocks all writes when any row cannot be safely upgraded, then applies upgrades to rows classified as `upgrade-available` in a deterministic order with honest partial-failure disclosure. `--format table|json` (table default) is added to `upgrade --all`. The JSON contract (`schema_version: 1`, `command: "upgrade"`, `mode: "all"`) is a stable wire format for CI pipelines, ratified by RFC-0072 D5.

Each `(pack, adapter)` row is an independent upgrade unit. The bulk operation is preflighted but not transactionally atomic: a partial failure is disclosed honestly, re-running the command is safe (completed rows are `up-to-date`), and the operation is never described as rolled back.

## Boundaries

### Always do

- Complete the full preflight phase before any write: resolve all row sources, classify all rows (source, version, manifest, render, path-jail), detect all blocked rows — preflight never returns a partial plan and never writes.
- Block all writes when any row is `unknown` (any reason). There is no skip-errors option.
- Store each `upgrade-available` row's rendered projection in preflight (pre-rendered for apply); the apply phase uses the stored projection and does not re-render.
- Apply in deterministic order: canonical source string → pack name → adapter name (all ascending, lexicographic).
- Stop on the first apply failure. Mark the failing row `failed`; mark remaining `upgrade-available` candidates `not-attempted`. Do not retry.
- Disclose partial completion honestly in both table and JSON output. Never use the word "rolled back."
- Require `--yes` when `--format json` and `--dry-run` is not set. JSON mode skips the confirmation prompt (which is table-mode only), so `--yes` is required for any non-dry-run JSON apply regardless of TTY state. This check does not apply to `--dry-run`.
- Route all diagnostics (warnings, progress, errors) to stderr in `--format json` mode; stdout carries exactly one valid JSON document.
- Pass every source string through `canonicalize_source()` before it appears in table or JSON output.
- Use each row's `canonicalize_source(PackState.source)` as the source to resolve for that row. `--all` does not accept a `--catalogue` override; it resolves from recorded row provenance.
- Extract the per-row apply body from `run()` into a shared `_apply_single_row()` helper that both `run()` (for single-pack) and `_run_all()` (for bulk) call. This ensures hook-wiring reconciliation, companion writes, merge-target SHA refresh, and all other per-row state writes are identical between the two paths.
- Use each row's `_projection` (pre-rendered in preflight) in the apply phase. The apply loop does not render again.
- Redact Authorization headers, bearer tokens, and URL user-info from all output and error messages.
- Use Python 3.11 stdlib only — no new runtime dependencies.

### Ask first

- Any `--scope all` or dual-scope inference — this spec has no `--scope all`.
- Any retry or partial-apply-then-continue behavior — stop-on-first-failure is an explicit RFC-0072 D4 decision.
- Adding `--force-upgrade-blocked`, `--skip-errors`, or any option that bypasses blocked rows.
- Any cross-scope transaction.
- Any downgrade behavior — `ahead` rows are always skipped; RFC-0072 D4 explicitly does not downgrade.
- Any change to `--format json` with `--pack` (deferred to a future spec).

### Never do

- Write any row when any other row is blocked.
- Use the word "rolled back" in any user-facing output.
- Mutate state during preflight — preflight is read-only.
- Allow a non-dry-run `--format json` apply without `--yes`. JSON mode has no confirmation prompt (table mode only), so `--yes` is always required for any non-dry-run JSON apply regardless of TTY state. Dry-run JSON is exempt (read-only, no writes).
- Emit credentials, bearer tokens, URL user-info, or Authorization header content to stdout or stderr.
- Emit any source string not passed through `canonicalize_source()`.
- Mix human prose or table content into stdout in `--format json` mode.
- Introduce a new runtime dependency.
- Add an ignore-TLS-errors or disable-SSL-verification option.
- Accept `--catalogue` with `--all` — row provenance governs source resolution in bulk mode.
- Accept `--adapter` with `--all` — each row's adapter is known from the installed state.
- Downgrade a row whose installed version is ahead of the source version.
- Re-render a row's projection in the apply phase if preflight already rendered and stored it.
- Apply `upgrade --all` to a dist-tree-installed row (a row whose `PackState.files` contain dist-tree-shaped paths such as `apm/`, `claude-plugins/`, or `marketplace.json`). Dist-tree installs use a different render path (`render_pack` with `allowed_prefixes=None`) that `_run_all`'s preflight does not replicate; attempting to upgrade them via bulk path would silently produce a wrong projection. Preflight must detect dist-tree rows (via `_was_dist_tree_install(row.pack_state)` — a module-level helper extracted from the inline expression at `upgrade.py:469-473`) and classify them `status: unknown` / `status_reason: render-failed` so the whole operation is blocked rather than silently corrupted.

## JSON Contract

Schema version 1, per RFC-0072 D5. The following is the canonical shape; all string fields are non-null unless otherwise stated.

```json
{
  "schema_version": 1,
  "command": "upgrade",
  "mode": "all",
  "scope": "repo|user",
  "dry_run": false,
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
      "scope": "repo",
      "source": "<credential-redacted canonical URI, or null>",
      "installed_version": "0.13.6",
      "available_version": "0.13.7",
      "status": "upgrade-available",
      "status_reason": null,
      "outcome": "completed"
    }
  ],
  "summary": {
    "total": 5,
    "upgrade_available": 2,
    "up_to_date": 2,
    "ahead": 1,
    "unknown": 0,
    "planned": 0,
    "completed": 1,
    "skipped": 3,
    "blocked": 0,
    "failed": 1,
    "not_attempted": 0
  }
}
```

Field notes:

- `schema_version`: integer `1`, not a string.
- `command`: always `"upgrade"`.
- `mode`: always `"all"` in this spec; distinguishes bulk output from future single-pack JSON.
- `scope`: the value of `--scope` (`"repo"` or `"user"`).
- `dry_run`: `true` when `--dry-run` was passed; `false` otherwise.
- `sources[*].resolved`: `true` when the source resolved successfully. Rows with unknown provenance (`status_reason: "source-unknown"`) contribute no entry to `sources`.
- `sources[*].error_code`: `null` on success; a machine-readable token (e.g. `"catalogue-error"`) on failure.
- `sources[*].error_message`: `null` on success; a human-readable, credential-redacted error string on failure.
- `rows[*].source`: `canonicalize_source(PackState.source)` — normalized, credential-redacted; `null` when provenance is unknown.
- `rows[*].available_version`: version string from the source's `pack.toml`; `null` when `status` is `unknown`.
- `rows[*].status`: one of `up-to-date|upgrade-available|ahead|unknown`. Always set after preflight.
- `rows[*].status_reason`: `null` when status is not `unknown`; a reason code from the closed set in §"Status Semantics" when status is `unknown`.
- `rows[*].outcome`: one of `planned|completed|skipped|blocked|failed|not-attempted`.
- `sources[]` ordering: sorted ascending by canonical source string.
- `rows[]` ordering: sorted by (canonical source string, pack name, adapter name) — same as apply order.
- `summary.total` = `upgrade_available + up_to_date + ahead + unknown` (status counts, pre-apply).
- `summary.planned`: non-zero only in `--dry-run`; equals the count of `upgrade-available` rows that would be mutated (i.e., those not blocked).
- Non-dry-run invariant: `completed + skipped + blocked + failed + not_attempted == total`; `planned == 0`.
- Dry-run invariant: `planned + skipped + blocked == total`; `completed == 0`, `failed == 0`, `not_attempted == 0`.
- When no rows are installed at the scope: `"rows": []`, `"sources": []`, all summary counts `0`.

## Status Semantics

Consistent with spec/list-installed-update-status for the first eight reason codes. The last two (`render-failed`, `path-jail-violation`) are specific to this spec's preflight render phase.

| Status | Condition | status_reason |
|--------|-----------|---------------|
| `up-to-date` | installed_version == available_version (compared as int-tuple via `_version_key()`; both tuples are zero-padded to equal length before comparison so `"0.13"` and `"0.13.0"` are equal — matches `list_installed._status_for` at `list_installed.py:185-190`) | null |
| `upgrade-available` | available_version > installed_version (after zero-padding) | null |
| `ahead` | installed_version > available_version (after zero-padding) | null |
| `unknown` | any condition below | see reason code |

`unknown` reason codes (evaluated in order; first applicable wins):

| Reason code | Condition |
|-------------|-----------|
| `source-unknown` | `canonicalize_source(PackState.source)` returns `None` (covers `None`, `"agent-ready-repo"`, any uncanonicalizable source) |
| `source-unavailable` | canonical source is non-null but `resolve_catalogue()` raises `CatalogueError` |
| `malformed-catalogue` | catalogue resolved but the pack's `pack.toml` raises `ConfigError` on load |
| `pack-not-found` | catalogue resolved, manifest parseable, but this pack name is absent |
| `incompatible-contract` | pack found; `pack_spec_version()` returns a non-null value whose major does not match the CLI's `SPEC_VERSION` major. An absent spec version (`None` return) is compatible — not a mismatch. |
| `adapter-no-longer-supported` | pack found, contract compatible; the row's adapter is absent from the declared `[pack.install].allowed-adapters` list (vacuously "allowed" when the list is absent) |
| `unparseable-catalogue-version` | pack found, adapter allowed; catalogue `version` field is absent or non-parseable as dotted numeric |
| `unparseable-installed-version` | catalogue version parseable; `PackState.installed_version` cannot be parsed as dotted numeric |
| `render-failed` | version comparison passed (`upgrade-available`); either (a) the row is a dist-tree-installed pack that `upgrade --all` does not support (detected before render via `_was_dist_tree_install`), or (b) the projection render raised an exception |
| `path-jail-violation` | version comparison passed, render succeeded; `safety.assert_projection_jailed` raised `PathJailError` |

**Ordering in `_classify_row`:** catalogue-version parseability is checked before installed-version parseability. When both are unparseable, the result is `unparseable-catalogue-version`. Render and path-jail checks are only performed on rows that reach `status: upgrade-available` after version comparison — they are not relevant to `up-to-date`, `ahead`, or source/manifest blocked rows.

**Blocked-means-no-write:** any row with `status: unknown` — regardless of reason code — blocks the entire mutating operation.

## Outcome Semantics

| Outcome | When assigned |
|---------|---------------|
| `planned` | Row is `upgrade-available` and scheduled but not yet written. Appears in dry-run output (the final result) and also in the pre-apply plan table shown before the confirmation prompt in non-dry-run table mode (a transient display, replaced by the post-apply results). Never appears in the final non-dry-run results (JSON or table) — `_finalize` always shows `completed`/`failed`/`not-attempted` after writes complete. `summary.planned == 0` is enforced by `_build_json_doc` in non-dry-run mode. |
| `completed` | Row was `upgrade-available` and `_apply_single_row()` succeeded |
| `skipped` | Row is `up-to-date` or `ahead` (not a mutation candidate) |
| `blocked` | Row is `unknown`, OR the full operation is blocked because another row is `unknown` — no write occurs |
| `failed` | Row was `upgrade-available`, was the next to be attempted, and `_apply_single_row()` returned `False` |
| `not-attempted` | Row is `upgrade-available` and was a candidate, but execution stopped at a prior `failed` row |

In a blocked-preflight scenario (any `unknown` row), all rows — including `upgrade-available` rows — have `outcome: blocked`.

## Testing Strategy

- **TDD** for `_classify_row(row: _BulkRow, pack_toml: dict | None) -> tuple[str, str | None, str | None]`: pure function receiving an already-loaded `pack_toml` (or `None` for pack-not-found) and returning `(status, status_reason, available_version)`. Covers the four statuses and the five version/contract/adapter reason codes (the source-resolution, pack-location, and malformed-catalogue reason codes are handled by the caller `_run_source_version_preflight`). Red stubs before production code.
- **TDD** for preflight render/path-jail: an `upgrade-available` row whose projection render raises an exception has `status: unknown`, `status_reason: render-failed`; one whose render succeeds but `assert_projection_jailed` raises has `status_reason: path-jail-violation`.
- **TDD** for blocked-preflight gate: a state with one `upgrade-available` row and one `unknown` row must result in zero writes and all rows having `outcome: blocked`.
- **TDD** for apply order: three `upgrade-available` rows with identical sources but different pack names; assert apply order is pack-name ascending.
- **TDD** for stop-on-first-failure: first row succeeds (mocked, `_apply_single_row` returns `True`), second row fails (mocked, returns `False`); assert third row has `outcome: not-attempted`.
- **TDD** for JSON output structure: `json.loads(stdout)` succeeds; `schema_version == 1` as integer; `"command": "upgrade"`; `"mode": "all"`; `rows[]` sorted by (source, pack, adapter); all required fields present.
- **TDD** for JSON summary invariants: dry-run: `planned + skipped + blocked == total`; non-dry-run: `completed + skipped + blocked + failed + not_attempted == total`.
- **TDD** for `--format json` without `--yes` (non-dry-run): TTY and non-TTY stdin variants; assert non-zero exit and message naming `--yes` in both cases.
- **TDD** for credential redaction: source containing URL user-info → `null` in `rows[*].source`; `CatalogueError` message with URI → redacted in `sources[*].error_message`.
- **TDD** for `--adapter` rejected with `--all`: non-zero exit, error message.
- **TDD** for `--scope` required with `--all`: non-zero exit when `--scope` omitted.
- **TDD** for `--catalogue` rejected with `--all`: non-zero exit, error message.
- **TDD** for `--format json` with `--pack` (unsupported): non-zero exit, message stating not yet supported.
- **TDD** for `ahead` rows not downgraded: row with installed > available has `outcome: skipped`, `status: ahead`; no mutation.
- **TDD** for `up-to-date` rows skipped: row with installed == available has `outcome: skipped`; no files mutated.
- **TDD** for source-conflict guard bypass: a row with `source = "agent-ready-repo"` (legacy, `source-unknown`) shows `outcome: blocked` in the plan; the source-conflict install guard (which fires only in `install`) does NOT cause a separate non-zero exit — the `blocked` outcome is entirely due to `source-unknown`.
- **TDD** for cross-consistency with list-installed status semantics: a self-contained fixture matrix of (installed_version, available_version, expected_status) triples — no import from `list_installed.py` — asserts `_classify_row` produces the same status as spec/list-installed-update-status defines for the three shared version-comparison outcomes (`upgrade-available`, `up-to-date`, `ahead`). This test does not depend on `_compute_status_pair` existing; it documents the cross-spec contract through direct assertion.
- **Integration** for full happy-path: `upgrade --all --scope repo --yes` against a local catalogue fixture with multiple packs; all `upgrade-available` rows are `completed`, state file updated with correct versions.
- **Integration** for partial failure: first row succeeds, second row fails (corrupt catalogue entry); third row has `outcome: not-attempted`.
- **Integration** for blocked preflight: one row has `source = "agent-ready-repo"` (legacy); all rows have `outcome: blocked`; state file mtime unchanged.
- **Integration** for co-owned path: two adapter rows of the same pack both `upgrade-available`; after apply both rows are `completed`; no file classified as unmanaged.
- **Goal-based** for D6 layout: two snapshot/golden-file tests at 80 and 120 columns for `upgrade --all --dry-run` table output; fixture includes at least one row with a Latin-Unicode pack or adapter identifier; a long source URI is truncated gracefully (no broken table structure); all JSON-output tests assert `json.loads(stdout)` succeeds and `schema_version == 1`.
- **Goal-based** for no state mutation when blocked: compare state file mtime before and after a blocked-preflight run — no write occurs.
- **Goal-based** for no new runtime dependency: `pyproject.toml` unchanged; all new imports are stdlib-only.

## Acceptance Criteria

### CLI shape

- [ ] AC1: `--all` and `--pack` are mutually exclusive; exactly one is required. Providing both, or neither, is a usage error (non-zero exit, clear message on stderr).
- [ ] AC2: `--scope repo|user` is required when `--all` is passed. Omitting `--scope` with `--all` is a usage error.
- [ ] AC3: `--adapter` is rejected (usage error, non-zero exit, clear message) when `--all` is passed. `--adapter` continues to work normally with `--pack`.
- [ ] AC4: `--catalogue` (the positional catalogue argument) is rejected (usage error, non-zero exit) when `--all` is passed. Bulk mode uses each row's recorded provenance for source resolution.
- [ ] AC5: `--format table|json` is accepted by `upgrade` in both `--pack` and `--all` modes (argparse level). `--format json` with `--all` produces the JSON contract defined in this spec. `--format json` with `--pack` is not supported in this spec: it exits with a non-zero exit code and a message stating the flag is not yet supported with `--pack` (the user should use `--format table` or use `--all`).
- [ ] AC6: Any non-dry-run `--format json` apply requires `--yes`; omitting `--yes` returns a non-zero exit code with a message naming `--yes`. This applies regardless of whether stdin is a TTY — JSON mode has no confirmation prompt (which is table-mode only), so the only safeguard is `--yes`. `--dry-run` is exempt (read-only, no writes).

### Preflight

- [ ] AC7: All `(pack, adapter)` rows in the state at the requested scope are enumerated before any write. The state file is loaded with `for_write=True` (retained for call-site parity; the legacy-state refusal is unconditional regardless of this flag per `config.py:304-305`). A `ConfigError` (including its `StateFileLegacy` subclass) from `load_state` produces a non-zero exit and an error message — matching the single-pack path's behavior. The preflight classifies every row — it does not stop on the first blocked row.
- [ ] AC8: Each distinct canonical source in the row set is resolved at most once per invocation. A `CatalogueError` from one source does not suppress rows from other sources; those rows receive `status_reason: source-unavailable`. Rows from successfully-resolved sources continue to be classified.
- [ ] AC9: A row whose `canonicalize_source(PackState.source)` returns `None` receives `status: unknown`, `status_reason: source-unknown`, `available_version: null`.
- [ ] AC10: A `CatalogueError` from `resolve_catalogue()` assigns `status: unknown`, `status_reason: source-unavailable`, `available_version: null` to all rows with that canonical source.
- [ ] AC11: A `ConfigError` loading the pack's `pack.toml` assigns `status: unknown`, `status_reason: malformed-catalogue`.
- [ ] AC12: A pack absent from the resolved catalogue assigns `status: unknown`, `status_reason: pack-not-found`.
- [ ] AC13: When `pack_spec_version()` returns a non-null value whose major differs from the CLI's `SPEC_VERSION` major, the row is assigned `status: unknown`, `status_reason: incompatible-contract`. When `pack_spec_version()` returns `None` (absent `[pack.adapter-contract]`), the row is treated as compatible and continues to version comparison. The check uses `pack_spec_version()` + inline major comparison, not the exit-code gate helper `check_spec_version_gate()`.
- [ ] AC14: An adapter absent from the declared `[pack.install].allowed-adapters` list assigns `status: unknown`, `status_reason: adapter-no-longer-supported`. When the list is absent, the check is vacuously "allowed."
- [ ] AC15: An unparseable catalogue `version` field assigns `status: unknown`, `status_reason: unparseable-catalogue-version`. An unparseable `PackState.installed_version` assigns `status: unknown`, `status_reason: unparseable-installed-version`. When both are unparseable, `unparseable-catalogue-version` wins. Parseability is tested by inspecting the return value of `_version_key()` (returns `None` for non-parseable), not by catching exceptions.
- [ ] AC16: For each row that reaches `status: upgrade-available` after version comparison, the preflight first checks `_was_dist_tree_install(row.pack_state)`. If True, assigns `status: unknown`, `status_reason: render-failed` immediately without rendering. Otherwise renders the projection and runs `safety.assert_projection_jailed`, using `_adapter_allowed_prefixes_user(row.adapter)` for user-scope rows and `_adapter_allowed_prefixes_repo(resolved_adapter)` for repo-scope rows where `resolved_adapter` is obtained from the render's return value — matching the derivation order in `run()`. A render exception also assigns `status: unknown`, `status_reason: render-failed`. A `PathJailError` from `safety.assert_projection_jailed(root, sorted_paths, allowed_prefixes, command="upgrade")` assigns `status: unknown`, `status_reason: path-jail-violation`. The rendered projection is stored in `row._projection` for use in the apply phase.
- [ ] AC17: Any row with `status: unknown` (any reason) blocks all writes. No projection file, state write, hook-wiring change, or any other mutation occurs when any row is blocked. Exit code is non-zero.
- [ ] AC18: `status: up-to-date` rows have `outcome: skipped` and are not mutated. `status: ahead` rows have `outcome: skipped` and are never downgraded.
- [ ] AC19: Preflight does not write, migrate, or mutate state — it is read-only except for rendering projections in memory.

### Apply phase

- [ ] AC20: Apply order is deterministic: sorted ascending by canonical source string, then pack name, then adapter name (all lexicographic). Rows with `status: unknown` never reach the apply phase.
- [ ] AC21: The first apply failure stops the operation. The failing row is marked `outcome: failed`. All remaining `upgrade-available` rows not yet attempted are marked `outcome: not-attempted`. Previously `completed` rows retain their applied state. Exit code is non-zero.
- [ ] AC22: Partial completion is never described as "rolled back" in any output — table or JSON.
- [ ] AC23: A shared `_apply_single_row()` helper is extracted from `run()` and called by both the single-pack path and `_run_all()`'s apply loop. The helper encapsulates render (using the pre-rendered `_projection` from preflight), path-jail, tier walk, hook-wiring reconciliation, companion writes, and state write — making both paths identical for per-row apply behavior. The apply loop does not re-render; it uses `row._projection`.
- [ ] AC24: The source-conflict install guard (spec/source-conflict-install-guard) does not fire during `upgrade --all`. Upgrade is the sanctioned migration path for legacy source rows; the guard is an install-only gate.
- [ ] AC25: Each row's state write uses `safety.write_jailed` directly (matching the single-pack upgrade path). The known concurrency gap between concurrent uninstall and `upgrade --all` is acknowledged and deferred (deferred: backlog:multi-adapter-state-lock-uninstall-upgrade).

### Confirmation and plan display

- [ ] AC26: Before any write, a classified plan is shown (in `--format table`) listing all rows with their STATUS and planned OUTCOME. A single confirmation prompt covers the whole operation in interactive mode. `--yes` bypasses the prompt. `--dry-run` shows the plan and exits without prompting or writing.
- [ ] AC27: A dry run with any blocked row returns non-zero exit code. A dry run with no blocked rows returns exit code 0. Both show the full classified plan.
- [ ] AC28: When no rows are `upgrade-available` and no rows are `unknown`, the operation exits 0 with a "Nothing to upgrade" message (or equivalent) without prompting.

### Output

- [ ] AC29: `--format table` lists all rows with at minimum: PACK, ADAPTER, STATUS, and OUTCOME. Row order follows AC20.
- [ ] AC30: `--format json` emits exactly one valid JSON document to stdout; all diagnostics go to stderr; no table or human prose appears on stdout.
- [ ] AC31: The JSON document matches the contract in §"JSON Contract": `schema_version` is integer `1`; `command` is `"upgrade"`; `mode` is `"all"`; all required top-level fields present; `rows[]` sorted by (canonical source, pack, adapter); `sources[]` sorted ascending by canonical source.
- [ ] AC32: Row `outcome` values are from the closed set: `planned`, `completed`, `skipped`, `blocked`, `failed`, `not-attempted`. `status` and `outcome` are always separate fields on each row.
- [ ] AC33: In JSON output, `rows[*].source` is `canonicalize_source(PackState.source)` — normalized, credential-redacted; `null` when provenance is unknown. `sources[*].error_message` is credential-redacted (no URL user-info, query-string credential tokens, or bearer-token values).
- [ ] AC34: `summary` counts are consistent: `total == upgrade_available + up_to_date + ahead + unknown`. Non-dry-run: `completed + skipped + blocked + failed + not_attempted == total`; `planned == 0`. Dry-run: `planned + skipped + blocked == total`; `completed == 0`, `failed == 0`, `not_attempted == 0`.
- [ ] AC35: D6 layout checks — `upgrade --all --dry-run` table output has two snapshot/golden-file tests (labeled 80col and 120col for D6 traceability); fixture includes at least one row with a Latin-Unicode pack or adapter identifier; a long source URI (longer than the source column maximum) is truncated gracefully without breaking table structure; all JSON-output tests assert `json.loads(stdout)` succeeds and `schema_version == 1` as integer.

### Security

- [ ] AC36: Bearer tokens are never persisted, printed, or included in exception repr or log lines. Authorization headers are redacted in all output. Verified by: no `Authorization`, `Bearer`, or `access_token` literal appears in `stdout` or `stderr` in any test run against a fixture.
- [ ] AC37: No TLS-certificate-ignore or SSL-disable option is added. Verified by: `grep -rn "verify=False\|ssl_context.*verify\|disable.*cert\|ignore.*tls" packages/agentbundle/agentbundle/commands/upgrade.py` returns zero hits after the change.

### Dependencies and regression

- [ ] AC38: No new runtime dependency is introduced. `pyproject.toml` dependency list is unchanged; all new code in `upgrade.py` imports only stdlib modules beyond what it already imports.
- [ ] AC39: All existing agentbundle tests pass after the change with no modifications to the tests themselves.

## Assumptions

- Technical: `spec/packstate-source-provenance` is implemented before or co-landed; `canonicalize_source(value: str | None) -> str | None` exists in `agentbundle.config`. Maps `None`, `"agent-ready-repo"`, and blank to `None`. (source: spec/packstate-source-provenance AC5–AC7)
- Technical: `spec/list-installed-update-status` defines the canonical status semantics and the first eight reason codes. `_classify_row` implements equivalent logic for those eight; `render-failed` and `path-jail-violation` are additions specific to this spec's preflight render phase. The cross-consistency test (Testing Strategy) mechanically verifies agreement for the shared version-comparison outcomes without importing from `list_installed.py` — the test is self-contained and does not depend on `_compute_status_pair` landing first. However, `spec/list-installed-update-status` must be shipped before or simultaneously with this spec (landing prerequisite for the semantic contract it defines). (source: spec/list-installed-update-status §Status Semantics)
- Technical: `_version_key(v: str) -> tuple[int, ...] | None` is available in `list_installed.py` or `commands/_common.py`; it returns `None` for non-parseable input rather than raising. The spec's `_classify_row` tests `_version_key(...) is None`, not a `try/except`. Check for circular import at EXECUTE time; duplicate the small function in `upgrade.py` if needed. (source: list_installed.py:159–170)
- Technical: `pack_spec_version(pack_toml) -> str | None` reads `pack_toml["pack"]["adapter-contract"]["version"]`; returns `None` when the `[pack.adapter-contract]` table or its `version` key is absent. `_major(version_str) -> str` extracts the first dotted segment. `SPEC_VERSION` is imported from `agentbundle.version` (canonical source; `list_installed.py:132` uses the same import). The inline check is: `if raw_spec_version is not None and _major(raw_spec_version) != _major(SPEC_VERSION): return incompatible-contract`. A `None` return (absent spec version) is compatible — do not return `incompatible-contract` in that case. `check_spec_version_gate()` is NOT used in `_classify_row` because it prints to stderr and returns an exit-code sentinel. (source: config.py:99–105; agentbundle/version.py; commands/_common.py)
- Technical: `_locate_pack(catalogue_dir, pack_name) -> Path | None` in `upgrade.py` returns `None` for an absent pack. (source: upgrade.py:935–948)
- Technical: `load_pack_toml(path)` raises `ConfigError` on TOML failure. (source: config.py:81–96)
- Technical: `[pack.install].allowed-adapters` accessed as `pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters")`; vacuously "allowed" when absent. (source: upgrade.py:399–401)
- Technical: The render path (`_render_for_repo_scope`, `_render_for_user_scope`, `_rewrite_user_scope_hook_paths`, `_resolve_target_adapter`) is imported from `commands/install.py` by `upgrade.py`. The shared `_apply_single_row()` helper uses these same imports. (source: upgrade.py:408–495)
- Technical: `safety.assert_projection_jailed(root, sorted_paths, allowed_prefixes, command="upgrade")` — `command` is a keyword argument — raises `PathJailError` on violation; this is called in preflight for each `upgrade-available` row with `allowed_prefixes` derived per-row. `safety.write_jailed` is used per-file in the apply phase. (source: upgrade.py:575, 616; safety.py:169–171)
- Technical: The hook-wiring reconciliation block (upgrade.py:633–709) — including `_compute_new_wiring_rows`, `_unproject_removed_rows`, `_merge_user_scope_hook_wiring`, `_refresh_merge_target_shas` — must be encapsulated in the shared `_apply_single_row()` so user-scope kiro-cli adapter rows are reconciled identically in bulk and single-pack mode. (source: upgrade.py:633–709)
- Technical: The existing upgrade `run()` does not use `statelock.persist_state_locked`; it writes state directly via `safety.write_jailed`. `_apply_single_row()` matches this behavior. (source: upgrade.py:720–738)
- Technical: `resolve_state_path("repo"|"user", root)` and `load_state(state_path, for_write=True)` resolve and load the scope's state file. `for_write=True` is retained for call-site parity; `config.py:304-305` documents the legacy-state refusal is now unconditional (read and write). (source: commands/_common.py; config.py:286–307)
- Technical: `sys.stdin.isatty()` is evaluated once per `_run_all()` invocation and threaded through as a local variable. Tests mock by monkeypatching `sys.stdin` (not via an `args` attribute). (source: upgrade.py:352)
- Technical: Python 3.11 stdlib-only runtime constraint. (source: pyproject.toml; RFC-0072 §Non-goals)
- Process: RFC-0072 is Accepted. D4 ratifies preflight-then-apply (including render and path-jail in preflight), stop-on-first-failure, and disclosed non-atomicity. D5 ratifies CLI surfaces and JSON contract. D6 ratifies layout/usability checks. (source: RFC-0072 status 2026-07-23)
- Product: Explicitly deferred to backlog: (a) multi-adapter-state-lock-uninstall-upgrade concurrency gap (deferred: backlog:multi-adapter-state-lock-uninstall-upgrade); (b) upgrade orphan removal on projection shape change (deferred: backlog:upgrade-orphan-removal-on-projection-shape-change); (c) `--format json` with `--pack` single-pack JSON contract (deferred to a future spec).
