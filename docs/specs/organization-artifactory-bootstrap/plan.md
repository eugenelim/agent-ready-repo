# Plan: Organization Artifactory Bootstrap

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two files change, with docstring-only updates to a third. First, `_data/install-defaults.toml` gains a `[organization.artifactory]` block with `enabled = false`. Second, `source_defaults.py` gains two new functions — `_source_from_org_bootstrap` (private parser/validator) and `read_org_bootstrap` (file reader) — and `resolve_default_source` inserts a Layer 3 call between the Layer 2 user-config check and the existing editable detection (now Layer 4). Third, the module docstring and `resolve_default_source` docstring in `source_defaults.py` are updated to describe the five-layer chain. No existing function signatures change; no logic outside the targeted insertion point is touched.

## Constraints

- RFC-0072 D2: fail-closed on `enabled = true` with malformed config — raise `CatalogueError`, do not fall through to Layer 4.
- RFC-0072 D2: Layer 3 only fires when Layer 1 and Layer 2 both yield nothing.
- ADR-0036 D3: no repo-scoped source; no cwd fallback — this spec adds Layer 3 but does not relax D3.
- RFC-0031 Principle 3: stdlib-only, no new runtime dependency.
- Security: no credentials in TOML; no user-info in constructed URL; no TLS bypass; `example.test` in tests only.

## Construction tests

**Unit tests:** `_source_from_org_bootstrap` is a pure function of TOML text and a config-path string, making it fully unit-testable with inline fixtures. All AC2–AC16 tests target this function directly without touching the filesystem.

**Integration tests:** Two tests exercise the full `resolve_default_source` interface via keyword-argument injection (`read_org` parameter): one for the Layer-3-wins path, one for the Layer-2-wins path.

**TDD stub note (light mode):** Tasks T2 and T3 are TDD. At EXECUTE PLAN, write red-failing stub implementations before filling in production code. The test descriptions are the stubs' specification — each test must fail for the right reason (missing behavior), not for a syntax error or import failure. Per CONVENTIONS §4 light-mode exemption, per-test `stub: true` markers are omitted; the "TDD" label on the task is the handoff marker.

**End-to-end dependency:** Layer 3 returns a `catalogue+https://` URL but the fetch path (`catalogue.py`) does not yet handle that scheme; `spec/https-catalogue-channels` delivers the handler. An org fork enabling Layer 3 before that spec ships gets a confusing `resolve_catalogue` error. All integration tests in this spec inject `read_org` directly and do not exercise the full install flow — that is intentional; the full-path integration test belongs in `spec/https-catalogue-channels`.

**Manual verification:** none beyond the tests above.

## Design

### Design decisions

- `_source_from_org_bootstrap(text: str, *, config_path: str) -> str | None` is a module-level private function in `source_defaults.py`, consistent with the existing `_source_from_install_defaults` pattern. It raises `CatalogueError` for fail-closed cases rather than returning a sentinel — this makes the call site in `resolve_default_source` a simple two-branch pattern without any error-sentinel check, and `CatalogueError` propagates naturally through the chain. Traces to: AC15, AC19.
- `read_org_bootstrap()` is the public file reader, following the `read_packaged_default` pattern exactly: reads the same `_data/install-defaults.toml` via `importlib.resources`; returns `None` on file absent or unreadable; passes `config_path=str(resource)` for error messages; raises if `_source_from_org_bootstrap` raises. Traces to: AC16, Assumptions.
- `resolve_default_source` gains a new keyword-only parameter `read_org: Callable[[], str | None] | None = None` (defaulting to `read_org_bootstrap`). This matches the existing `read_packaged` injection point and keeps the function unit-testable without filesystem access. The call is inserted after the Layer 2 validity check and before the `dist = _load_distribution()` call (editable detection). Traces to: AC18, AC19.
- TOML access uses `data.get("organization", {}).get("artifactory", {})` — double-nested `.get` with empty-dict defaults, returning an empty dict when either key is absent. An empty dict is treated as disabled (`enabled` absent → `None`). Traces to: AC2, AC3.
- URL construction order: (1) validate `base-url` fully, (2) normalize trailing slash, (3) validate `repository`/`bundle`/`channel`, (4) assemble. Validating before normalizing prevents accepting a URL that only looks valid after slash-stripping. Traces to: AC6.
- The `..` check for path segments is placed before the `re.fullmatch` check so the error message says "must not be '..'" rather than "contains invalid characters". Both checks cover overlapping ground; the explicit `..` reject is defense-in-depth per spec. Traces to: AC12–AC14.
- Field type-checking (`isinstance(val, str)`) is applied to each required field before parsing — `urlsplit`, `re.fullmatch`, and `.startswith` raise unguarded `TypeError`/`AttributeError` on non-string values. The type check raises `CatalogueError` naming the field. Traces to: AC16, Concern 2.
- Error messages include the field identifier and config path but never the raw field value. For user-info-bearing `base-url`, only the field name (`organization.artifactory.base-url`) and config path appear in the message. Traces to: AC8, AC16, Always-do.
- Scheme validation uses a case-sensitive string prefix check (`base_url.startswith("https://")`) before any `urlsplit` call, so uppercase `HTTPS://` is rejected at the field-validation step. This ensures the constructed `catalogue+https://` URI always starts with the lowercase prefix required by `_is_valid_source`. Traces to: AC7, spec Always-do.

### Data & schema

`install-defaults.toml` is extended:

```toml
# Optional organisation Artifactory bootstrap — layer 3 of the catalogue-source
# resolution chain (RFC-0072 D2 / ADR-0036). When enabled = true, agentbundle
# constructs catalogue+<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json
# as the default source for developers installing from this fork.
# Public default ships enabled = false; no real org endpoints are stored here.
[organization.artifactory]
enabled = false

[defaults]
source = "git+https://github.com/eugenelim/agent-ready-repo"
```

No state schema version bump. The `[organization.artifactory]` table is purely additive; `tomllib` parses it alongside the existing `[defaults]` table without conflict.

### Interfaces & contracts

**`_source_from_org_bootstrap(text: str, *, config_path: str) -> str | None`**
- `text`: full TOML content of `install-defaults.toml`
- `config_path`: display string for the config file location (used in error messages; may be a filesystem path or a descriptive label)
- Returns `None` when disabled (absent table, absent/false `enabled`)
- Returns a `catalogue+https://…` URI string when `enabled = true` and all fields valid
- Raises `CatalogueError` when `enabled = true` and any field is malformed (fail-closed)

**`read_org_bootstrap(read_text: Callable[[], tuple[str, str] | None] | None = None) -> str | None`**
- When `read_text` is `None` (production path): reads the packaged `_data/install-defaults.toml` via `importlib.resources`; absorbs `(FileNotFoundError, ModuleNotFoundError, OSError)` as `return None`; sets `config_path = str(resource)`. Returns `None` on file absent, unreadable, or `enabled` disabled. Raises `CatalogueError` on `enabled = true` + invalid config.
- When `read_text` is provided (test path): calls `read_text()`; if it returns `None`, returns `None`; otherwise unpacks `(text, config_path)` and calls `_source_from_org_bootstrap(text, config_path=config_path)`.
- `resolve_default_source` injects it via the `read_org` keyword argument for tests.

**`resolve_default_source` signature change (additive):**
```python
def resolve_default_source(
    explicit: str | None,
    *,
    config_source: str | None = None,
    dist: object = _UNSET,
    read_packaged: Callable[[], str | None] | None = None,
    read_org: Callable[[], str | None] | None = None,  # NEW — layer 3
    stream: TextIO | None = None,
) -> str:
```

### Behavior & rules

**`_source_from_org_bootstrap` parsing logic:**

1. Parse `text` with `tomllib.loads(text)`; on `TOMLDecodeError` return `None` (malformed file → disabled silently; consistent with `_source_from_install_defaults`; AC2b).
2. Type-guarded nesting access (mirrors `_source_from_install_defaults`'s `isinstance(defaults, dict)` pattern):
   a. `org = data.get("organization")`. If `org` is `None` or not a `dict` → return `None` (absent or scalar-typed `organization` key; AC2).
   b. `org_block = org.get("artifactory")`. If `org_block` is `None` or not a `dict` → return `None` (absent or scalar-typed `artifactory` key; AC2).
   (Using chained `.get({}).get({})` is unsafe when an intermediate key is a non-dict value — it would raise `AttributeError`; the explicit `isinstance` guard is required.)
3. `enabled = org_block.get("enabled")`. If `enabled is None` (key absent) or `enabled is False` → return `None` (AC3, AC4).
4. If `enabled is not True` (e.g., a TOML string `"true"` or an integer) → raise `CatalogueError(f"organization.artifactory.enabled: must be a boolean (true/false) in {config_path}")` (AC3b).
5. Read and type-check `base_url = org_block.get("base-url")`. If absent → raise naming `base-url` as required (AC15). If not a `str` or is empty/blank → raise naming `base-url` (AC11, type-check).
6. Validate `base_url` in order:
   a. `not base_url.startswith("https://")` → raise naming `base-url` (AC7; case-sensitive prefix check rejects uppercase schemes before `urlsplit`).
   b. `parsed = urlsplit(base_url)`. `not parsed.netloc or not parsed.netloc.strip()` → raise naming `base-url` (AC11 empty netloc).
   c. `"@" in parsed.netloc` → raise naming `base-url`, error message must NOT include the raw `base_url` value (AC8).
   d. `parsed.query` → raise naming `base-url` (AC9).
   e. `parsed.fragment` → raise naming `base-url` (AC10).
7. Normalize: `base_url = base_url.rstrip("/")`.
8. For each field name `fname` in `("repository", "bundle", "channel")`:
   a. `val = org_block.get(fname)`. If absent → raise naming field (AC15).
   b. If not a `str` or is empty/blank → raise naming field (AC12–AC14, type-check).
   c. If `val == ".."` → raise naming field (defense-in-depth, AC12–AC14).
   d. If not `_ORG_SEGMENT_RE.fullmatch(val)` → raise naming field (AC12–AC14).
9. Construct and return: `f"catalogue+{base_url}/{repository}/catalogues/{bundle}/channels/{channel}.json"` (AC5).

**Error message pattern:** `f"organization.artifactory.{field}: {reason} in {config_path}"` — the raw field value is never included in the message (AC8, AC16).

**`resolve_default_source` insertion point** (between Layer 2 and Layer 4/editable detection):

```python
# Layer 3 — org Artifactory bootstrap (RFC-0072 D2)
if read_org is None:
    read_org = read_org_bootstrap
org = read_org()  # returns None (disabled) or raises CatalogueError (fail-closed)
if org is not None:
    return org
```

The `CatalogueError` from `read_org()` propagates naturally through `resolve_default_source` — no catch, no fall-through to Layer 4.

### Failure, edge cases & resilience

- TOML parse error in the file → step 1 returns `None` silently. This mirrors `_source_from_install_defaults` and avoids a fatal error when the file is partially malformed (e.g., bad `[defaults]` section unrelated to the org block).
- `enabled = true` with a non-boolean value (e.g., TOML string `"true"`) → step 4 raises. TOML is typed; `tomllib` preserves the TOML boolean vs. string distinction.
- `base-url = "https:///path"` (empty netloc) → step 6b raises with a `base-url` error. `urlsplit("https:///path").netloc` is `""`.
- `repository = ".."` → step 8b raises before the regex check. Both `.` characters are individually in `[A-Za-z0-9._-]`, so the regex alone would not catch `..`.
- `repository = "a/b"` → step 8c raises because `/` is outside the grammar. No explicit check needed.
- `repository = "my%20repo"` → step 8c raises because `%` is outside the grammar.
- File absent or unreadable → `read_org_bootstrap` returns `None` silently (same as `read_packaged_default`).

## Tasks

### T1: Extend `install-defaults.toml` with `[organization.artifactory]` block

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/_data/install-defaults.toml`

**Tests:**
- `test_install_defaults_org_bootstrap_disabled_by_default`: parse the file content via `tomllib.loads`; assert `data["organization"]["artifactory"]["enabled"] is False` and `set(data["organization"]["artifactory"].keys()) == {"enabled"}` (no stray real fields in the public default). Verifies AC1.
- **Goal-based check:** `grep -n "enabled = true" packages/agentbundle/agentbundle/_data/install-defaults.toml` returns zero lines. Verifies AC1.

**Approach:**
- Insert the `[organization.artifactory]` block with `enabled = false` and the explanatory comment block above the existing `[defaults]` section.

**Done when:** both checks above pass; `tomllib.loads(text)["organization"]["artifactory"]["enabled"]` evaluates to `False`.

---

### T2: Implement `_source_from_org_bootstrap` and `read_org_bootstrap`

**Depends on:** T1

**Touches:** `packages/agentbundle/agentbundle/source_defaults.py`

**Tests (TDD — all tests below require red stubs materialized at EXECUTE PLAN):**

- `test_org_bootstrap_absent_table_returns_none`: TOML text with no `[organization]` section → `None`. Verifies AC2.
- `test_org_bootstrap_absent_artifactory_key_returns_none`: TOML text with `[organization]` but no `[organization.artifactory]` → `None`. Verifies AC2.
- `test_org_bootstrap_organization_scalar_returns_none`: TOML text with `organization = "typo"` (valid TOML, non-table `organization` key) → `None` (not an `AttributeError`). Verifies AC2; guards against the `str.get("artifactory")` crash.
- `test_org_bootstrap_artifactory_scalar_returns_none`: TOML text with `[organization]` and `artifactory = true` (non-table `artifactory` key) → `None`. Verifies AC2.
- `test_org_bootstrap_toml_decode_error_returns_none`: pass syntactically invalid TOML text → `None` (not a `CatalogueError`). Verifies AC2b.
- `test_org_bootstrap_absent_enabled_returns_none`: `[organization.artifactory]` block with no `enabled` key → `None`. Verifies AC3.
- `test_org_bootstrap_enabled_false_returns_none`: `enabled = false` → `None`. Other fields are not inspected. Verifies AC4.
- `test_org_bootstrap_enabled_string_nontrue_raises`: `enabled = "true"` (TOML string, not boolean) → `CatalogueError` naming `enabled` and config path. Verifies AC3b.
- `test_org_bootstrap_enabled_integer_raises`: `enabled = 1` (TOML integer) → `CatalogueError` naming `enabled`. Verifies AC3b.
- `test_org_bootstrap_valid_config_constructs_url`: `enabled = true`, `base-url = "https://example.test/art"`, `repository = "repo-local"`, `bundle = "engineering"`, `channel = "stable"` → `"catalogue+https://example.test/art/repo-local/catalogues/engineering/channels/stable.json"`. Verifies AC5.
- `test_org_bootstrap_trailing_slash_on_base_url_normalized`: `base-url = "https://example.test/art/"` → URL does not double-slash: `catalogue+https://example.test/art/repo-local/...`. Verifies AC6.
- `test_org_bootstrap_no_trailing_slash_on_base_url_unchanged`: `base-url = "https://example.test/art"` → same URL as trailing-slash variant. Verifies AC6.
- `test_org_bootstrap_http_base_url_raises`: `base-url = "http://example.test/art"` → `CatalogueError` naming `base-url` and config path. Verifies AC7.
- `test_org_bootstrap_ftp_base_url_raises`: `base-url = "ftp://example.test/art"` → `CatalogueError` naming `base-url`. Verifies AC7.
- `test_org_bootstrap_uppercase_https_base_url_raises`: `base-url = "HTTPS://example.test/art"` → `CatalogueError` naming `base-url` (case-sensitive prefix check rejects uppercase scheme). Verifies AC7.
- `test_org_bootstrap_user_info_colon_in_base_url_raises`: `base-url = "https://user:pass@example.test/art"` → `CatalogueError` naming `base-url`; assert error message does NOT contain `"user"` or `"pass"`. Verifies AC8.
- `test_org_bootstrap_bare_user_in_base_url_raises`: `base-url = "https://user@example.test/art"` → `CatalogueError` naming `base-url`; assert error message does NOT contain the raw username. Verifies AC8.
- `test_org_bootstrap_query_string_in_base_url_raises`: `base-url = "https://example.test/art?foo=bar"` → `CatalogueError` naming `base-url`. Verifies AC9.
- `test_org_bootstrap_fragment_in_base_url_raises`: `base-url = "https://example.test/art#section"` → `CatalogueError` naming `base-url`. Verifies AC10.
- `test_org_bootstrap_empty_base_url_raises`: `base-url = ""` → `CatalogueError` naming `base-url`. Verifies AC11.
- `test_org_bootstrap_empty_netloc_in_base_url_raises`: `base-url = "https:///path"` → `CatalogueError` naming `base-url`. Verifies AC11.
- `test_org_bootstrap_integer_base_url_raises`: `base-url = 123` (TOML integer) → `CatalogueError` naming `base-url` (type-check). Verifies field type-checking, Concern 2.
- `test_org_bootstrap_missing_base_url_key_raises`: `enabled = true` with no `base-url` key → `CatalogueError` naming `base-url`. Verifies AC15.
- `test_org_bootstrap_repository_slash_raises`: `repository = "my/repo"` → `CatalogueError` naming `repository`. Verifies AC12.
- `test_org_bootstrap_repository_dotdot_raises`: `repository = ".."` → `CatalogueError` naming `repository`. Verifies AC12 defense-in-depth.
- `test_org_bootstrap_repository_percent_raises`: `repository = "my%20repo"` → `CatalogueError` naming `repository`. Verifies AC12.
- `test_org_bootstrap_repository_space_raises`: `repository = "my repo"` → `CatalogueError` naming `repository`. Verifies AC12.
- `test_org_bootstrap_repository_empty_raises`: `repository = ""` → `CatalogueError` naming `repository`. Verifies AC12, AC15.
- `test_org_bootstrap_repository_integer_raises`: `repository = 42` (TOML integer) → `CatalogueError` naming `repository` (type-check). Verifies Concern 2.
- `test_org_bootstrap_bundle_invalid_raises`: `bundle = "my bundle"` → `CatalogueError` naming `bundle`. Verifies AC13.
- `test_org_bootstrap_bundle_dotdot_raises`: `bundle = ".."` → `CatalogueError` naming `bundle`. Verifies AC13.
- `test_org_bootstrap_channel_slash_raises`: `channel = "my/channel"` → `CatalogueError` naming `channel`. Verifies AC14.
- `test_org_bootstrap_channel_dotdot_raises`: `channel = ".."` → `CatalogueError` naming `channel`. Verifies AC14.
- `test_org_bootstrap_missing_repository_raises`: `enabled = true`, valid `base-url`, no `repository` key → `CatalogueError` naming `repository`. Verifies AC15.
- `test_org_bootstrap_missing_bundle_raises`: valid except no `bundle` key → `CatalogueError` naming `bundle`. Verifies AC15.
- `test_org_bootstrap_missing_channel_raises`: valid except no `channel` key → `CatalogueError` naming `channel`. Verifies AC15.
- `test_org_bootstrap_error_message_contains_field_and_config_path`: trigger a validation failure with `config_path="sentinel-path"`; assert raised `CatalogueError` message contains `"base-url"` (or whichever field) and `"sentinel-path"`. Verifies AC16.
- `test_org_bootstrap_error_message_never_contains_raw_value`: trigger an AC8 rejection with `base-url = "https://user:pass@example.test/art"`; assert raised `CatalogueError` message does not contain `"user"`, `"pass"`, or `"user:pass"`. Verifies AC8, AC16, Always-do.
- `test_org_bootstrap_valid_chars_accepted`: parametrize `repository`, `bundle`, `channel` with representative valid values `"my-repo"`, `"my.bundle"`, `"my_channel"`, `"Repo123"`, `"a"` → no error; URL is returned. Verifies the grammar accepts the full character set.
- `test_org_bootstrap_single_dot_component_accepted`: `repository = "."` → accepted by regex (`.` alone is in `[A-Za-z0-9._-]+` and is not `".."`, so it passes). Verifies the explicit `..` check does not over-reach.
- `test_org_bootstrap_constructed_url_has_no_user_info`: valid config with `base-url = "https://example.test/art"` → assert constructed URL does not contain `@`. Verifies AC22.
- `test_org_bootstrap_is_valid_source_accepts_constructed_url` (`pytest.mark.xfail(reason="backlog:https-catalogue-channels-ac17-gate — spec/https-catalogue-channels AC1 not yet implemented", strict=True)`): call `_is_valid_source` on a URL returned by `_source_from_org_bootstrap`; assert `True`. Verifies AC17. Marked `xfail(strict=True)` — becomes a hard failure once `spec/https-catalogue-channels` lands; remove the mark at that point.
- `test_read_org_bootstrap_disabled_returns_none`: call `read_org_bootstrap` with an injected reader returning `(text, "mock-path")` where `text` has `enabled = false` → returns `None`. Verifies AC4 via public API.
- `test_read_org_bootstrap_valid_returns_url`: call `read_org_bootstrap` with an injected reader returning valid `enabled = true` TOML → returns the constructed URL. Verifies AC5 via public API.
- `test_read_org_bootstrap_invalid_raises`: call `read_org_bootstrap` with an injected reader returning `enabled = true` with invalid `base-url` → `CatalogueError` propagates. Verifies AC19 prerequisite.

**Approach:**
1. Add `_ORG_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")` as a module-level constant.
2. Implement `_source_from_org_bootstrap(text: str, *, config_path: str) -> str | None` per the Behavior & rules section.
3. Implement `read_org_bootstrap(read_text: Callable[[], tuple[str, str] | None] | None = None) -> str | None`:
   - When `read_text` is `None`: read via `importlib.resources.files("agentbundle").joinpath("_data/install-defaults.toml")`; absorb `(FileNotFoundError, ModuleNotFoundError, OSError)` as `return None`; set `config_path = str(resource)`.
   - When `read_text` is provided (tests): call it; if returns `None` return `None`; unpack `(text, config_path)`.
   - Call `_source_from_org_bootstrap(text, config_path=config_path)` and return (or propagate raises).
4. Add `from urllib.parse import urlsplit` to the import block (it may already be imported; confirm before adding a duplicate).
5. Add `import re` if not already present (check existing imports).

**Done when:** all T2 tests above pass; `_source_from_org_bootstrap` and `read_org_bootstrap` are importable from `agentbundle.source_defaults`; `grep -n "^import\|^from" packages/agentbundle/agentbundle/source_defaults.py` confirms no non-stdlib import was added.

---

### T3: Wire Layer 3 into `resolve_default_source`; update docstrings

**Depends on:** T2

**Touches:** `packages/agentbundle/agentbundle/source_defaults.py`

**Tests (TDD — all tests require red stubs at EXECUTE PLAN):**

- `test_resolve_layer3_fires_when_layers1_and_2_absent` (integration): call `resolve_default_source(None, config_source=None, dist=None, read_org=lambda: "catalogue+https://example.test/art/r/catalogues/b/channels/stable.json", read_packaged=lambda: None)` → returns the Layer 3 URL. Verifies AC18 (Layer 3 wins when higher layers absent), AC5.
- `test_resolve_layer2_beats_layer3` (integration): call `resolve_default_source(None, config_source="git+https://example.test/user-config", dist=None, read_org=lambda: (_ for _ in ()).throw(AssertionError("read_org must not be called")), read_packaged=lambda: None)` → returns `"git+https://example.test/user-config"` and the injected `read_org` is never called. Verifies AC18 (Layer 2 wins).
- `test_resolve_layer3_fail_closed_does_not_fall_through` (integration): define a sentinel `dist` object `sentinel_dist` with a `__getattr__` that raises `AssertionError("Layer 4 editable detection reached")`; call `resolve_default_source(None, config_source=None, dist=sentinel_dist, read_org=lambda: (_ for _ in ()).throw(CatalogueError("org config invalid")), read_packaged=lambda: (_ for _ in ()).throw(AssertionError("Layer 5 reached")))` and assert `CatalogueError` is raised — neither the `dist` attribute access nor `read_packaged` are invoked, proving Layers 4 and 5 are not reached. Verifies AC19.
- `test_resolve_layer1_beats_layer3` (integration): call `resolve_default_source("explicit-arg", config_source=None, dist=None, read_org=lambda: (_ for _ in ()).throw(AssertionError("must not call")))` → returns `"explicit-arg"` (Layer 1 wins; Layer 3 not reached). Verifies AC18 extension to Layer 1.

**Approach:**
1. Add `read_org: Callable[[], str | None] | None = None` as a new keyword-only parameter to `resolve_default_source`, inserted after `dist` and before `read_packaged` (or after `read_packaged` — either is fine; keep consistent with alphabetical or functional grouping).
2. Insert the Layer 3 call block between the Layer 2 block (the `config_source` branch) and the existing Layer 3 (`dist is _UNSET` → `_load_distribution()`) block:
   ```python
   # Layer 3 — org Artifactory bootstrap (RFC-0072 D2)
   if read_org is None:
       read_org = read_org_bootstrap
   org = read_org()  # None when disabled; raises CatalogueError on fail-closed
   if org is not None:
       return org
   ```
3. Update the module-level docstring to list five layers (replacing "four-layer" and the numbered list). When rewriting the docstring, do NOT use `(layer N)` parenthetical suffixes on the numbered list items — the current four-layer docstring uses that style, and the Done-when grep intentionally omits `\(layer [34]\)` from its alternations (it would over-match the new legitimate Layer 3 and Layer 4 entries). Use plain numbered-list form without layer-number parentheticals in the rewrite to avoid the ambiguity.
4. Update the `resolve_default_source` docstring to describe five layers (Layer 1–5) with the new Layer 3 description.
5. Update all stale layer-numbering references in `source_defaults.py` (AC20). Run the Done-when grep first to enumerate every hit; update every hit. Known sites at time of authoring (the grep is the authoritative check, not this list):
   a. `# Validation gate (layers 2 and 4)` (~line 56) → `# Validation gate (layers 2 and 5)`
   b. `_is_valid_source` docstring "layer-2 and layer-4 sources" (~line 77) → "layer-2 and layer-5 sources"
   c. `# Layer 3 — editable-install detection` (~line 102) → `# Layer 4 — editable-install detection`
   d. `# Layer 4 — packaged default` (~line 204) → `# Layer 5 — packaged default`
   e. `read_packaged_default` docstring "no layer-4 default" (~line 232) → "no layer-5 default"
   f. `_load_distribution` docstring "layer 3 exists for" (~line 254) → "layer 4 exists for"
   g. `# Layer 3 — editable detection.` inline comment inside `resolve_default_source` (~line 327) → "Layer 4"
   h. `# Layer 4 — packaged default, validated.` inline comment inside `resolve_default_source` (~line 334) → "Layer 5"
   i. `_UNSET` sentinel comment "skip layer 3" (~line 51) → "skip layer 4" (the consumer at the editable-detection branch is now Layer 4). Note: the Done-when grep catches `skip layer 3` (the stale form) and explicitly does not use `[34]` — so `skip layer 4` (the corrected form) passes the gate.
   (Additional sites may exist if the file has changed since spec authoring; the Done-when grep finds them all.)

**Done when:** all four integration tests above pass; `grep -niE "four-layer|layer 3.*editable|layer 4.*packaged|layers 2 and 4|layer-2 and layer-4|no layer-4|layer 3 exists|skip layer 3" packages/agentbundle/agentbundle/source_defaults.py` returns zero hits (catches every stale old-numbering form without matching legitimately corrected new-layer references: `skip layer 3` targets only the stale form; the corrected `skip layer 4` does not match; `layer [34]` char-class alternations are intentionally absent because they over-match the new Layer 3 and Layer 4 entries); `grep -n "Layer 3.*Artifactory\|org Artifactory bootstrap" packages/agentbundle/agentbundle/source_defaults.py` returns at least one hit confirming the new docstring text is present (AC20); `grep -n "read_org" packages/agentbundle/agentbundle/source_defaults.py` confirms the parameter exists and is wired.

---

### T4: Run existing test suite; confirm no regression

**Depends on:** T1, T2, T3

**Touches:** none (read-only verification)

**Tests:**
- Run full agentbundle test suite: `python -m pytest packages/agentbundle/ -x`.
- **Goal-based check — no real endpoint in TOML:** `grep -n "enabled = true" packages/agentbundle/agentbundle/_data/install-defaults.toml` returns zero lines. Verifies AC1.
- **Goal-based check — no real hostnames in new test/doc files:** `grep -rnE "https?://[A-Za-z0-9.-]+" packages/agentbundle/tests/ docs/specs/organization-artifactory-bootstrap/ | grep -v "example\.test"` returns zero lines — any URL in files added by this spec must resolve to `example.test`. Verifies AC21.
- **Goal-based check — no new dependency:** `git diff pyproject.toml` shows no new dependency entries; `grep -n "^import\|^from" packages/agentbundle/agentbundle/source_defaults.py | grep -v "^.*#"` shows no non-stdlib import added (the only new imports, if any, are from `re`, `urllib.parse`, or `tomllib` — all already present or stdlib). Verifies AC23.

**Approach:**
- Run the test suite.
- If failures arise: distinguish pre-existing failures from regressions caused by this change. Pre-existing failures are documented in the backlog; any new failure caused by this change is a blocker.
- All existing tests call `resolve_default_source` without the `read_org` parameter; the default `None → read_org_bootstrap` path reads the packaged TOML with `enabled = false`, returns `None`, and falls through to the existing layers — behavior is unchanged for all existing callers.

**Done when:** pytest exits 0 (or all failures are pre-existing and documented) and all goal-based checks above pass. Verifies AC24.

## Rollout

Pure-logic change — no infrastructure, no new dependency, no deployment sequencing. Backward-compatible for all existing callers of `resolve_default_source` (`read_org` defaults to `None`). The packaged `enabled = false` default means no behavior change for public wheel installs. Ships as part of the broader ini-004 agentbundle release (minor version bump in `spec/agentbundle-enterprise-distribution-release`).

## Risks

- **`urlsplit` already imported:** `source_defaults.py` already imports `urlsplit`; confirm before adding a duplicate import in T2. If not present, add it.
- **`re` already imported:** `source_defaults.py` already imports `re` (for `_WIN_DRIVE_RE`); adding `_ORG_SEGMENT_RE` requires no new import.
- **`tomllib.loads` on a file with both tables:** `_source_from_org_bootstrap` re-parses `text` (the whole file), which includes the `[defaults]` block. This is harmless — `tomllib` parses the whole file and the function only accesses `data["organization"]["artifactory"]`. The existing `_source_from_install_defaults` also parses the whole file; two parsings per invocation is the accepted cost of keeping the functions independent.
- **`read_org_bootstrap` injected reader shape:** The test-injection pattern uses `read_text: Callable[[], tuple[str, str] | None]` (returns `(text, config_path)` or `None`). This differs from `read_packaged`'s `Callable[[], str | None]` (returns just the text). The difference is necessary: `read_org_bootstrap` needs both text and config path for error messages. If this shape causes friction, a two-parameter injection (`read_text: Callable[[], str | None]`, `config_path: str = "…"`) is an alternative — note in changelog if changed.

## Changelog

- 2026-07-24: initial plan
- 2026-07-24: second draft — addressed first adversarial review: added AC17 xfail test with strict=True and deferred marker (Blocker 1); added isinstance type-check for all fields before parsing, plus tests for integer/bool TOML values (Concern 2); documented TOMLDecodeError fall-through as explicit AC2b exception to fail-closed (Concern 3); elevated non-boolean `enabled` to AC3b with test (Concern 4); replaced urlsplit-only scheme check with case-sensitive startswith("https://") prefix pre-check, added uppercase-HTTPS test (Concern 5); narrowed AC22 claim to netloc/segment guarantees only, documented base-url path as org-controlled (Concern 6); added no-raw-value requirement to AC8 and error message rule, added test asserting error does not contain credential text (Concern 7); added goal-based hostname grep to T4 (Nit 8); added positive Layer-3 docstring grep to T3 Done-when (Nit 9); strengthened AC19 test to use sentinel dist object with attribute-access raise (Nit 10)
- 2026-07-24: third draft — addressed second adversarial review: replaced positive/negative-example hostname grep with negation-based URL grep (Concern 1); added end-to-end dependency note on https-catalogue-channels to Construction tests and spec Assumptions (Concern 2); added deferred slug marker to AC17 in spec and backlog-registration instruction (Concern 3); corrected read_org_bootstrap signature in Interfaces to include optional read_text parameter (Concern 4); added TDD stub note with light-mode exemption to Construction tests (Nit 5)
- 2026-07-24: fourth draft — addressed third adversarial review: aligned AC17 deferred slug to `https-catalogue-channels-ac17-gate` in both spec marker and xfail reason string; registered slug in workspace.toml [backlog].open (Blockers 1+2); expanded AC20 and T3 Approach to cover section-comment renumbering at source_defaults.py:56/102/204; updated T3 Done-when grep to catch "layers 2 and 4" (Concern 3); T1 test now asserts set of keys == {"enabled"} to verify no stray fields (Nit 4)
- 2026-07-24: fifth draft — addressed fourth adversarial review: replaced chained `.get({}).get({})` with isinstance-guarded two-step nesting access to avoid AttributeError on scalar `organization`/`artifactory` TOML values; added tests for both non-table shapes (Blocker 1); aligned xfail reason string in spec AC17 to match plan (Concern 2); made T3 Done-when grep case-insensitive with `-niE` and added `\(layer [34]\)` alternation for lowercase numbered-list forms (Nit 3)
- 2026-07-24: sixth draft — addressed fifth adversarial review: enumerated all six stale layer-numbering sites in source_defaults.py in both AC20 (spec) and T3 Approach step 5 (plan); extended T3 Done-when grep to catch hyphenated `layer-4`, `no layer-4`, and `layer 3 exists` forms — all old-numbering variants now covered (Blocker 1)
- 2026-07-24: seventh draft — addressed sixth adversarial review: replaced fixed-count enumeration in AC20 (spec) with grep-as-source-of-truth form; added two in-body inline comments (lines ~327,334) as sites (g) and (h) in T3 step 5 with caveat that the grep is authoritative; fixes "five" count discrepancy (Concern 1, Nit 2)
- 2026-07-24: eighth draft — addressed seventh adversarial review: added `_UNSET` sentinel comment at ~line 51 ("skip layer 3") as site (i) to T3 step 5; extended Done-when grep with `skip layer [34]` alternation to catch this form (Blocker 1)
- 2026-07-24: ninth draft — addressed eighth adversarial review: replaced `skip layer [34]` with literal `skip layer 3` in Done-when grep (the corrected form "skip layer 4" must not match); removed `\(layer [34]\)` alternation (over-matches new Layer 3/4 entries); added T3 step 3 note to omit `(layer N)` parentheticals in the docstring rewrite to avoid the ambiguity; site (i) notes that Done-when grep intentionally does not catch the corrected form (Blocker 1)
