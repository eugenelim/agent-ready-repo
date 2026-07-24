# Spec: Organization Artifactory Bootstrap

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D2), ADR-0036, spec/https-catalogue-channels (catalogue+https:// scheme)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An org's agentbundle fork has no way to ship a default internal catalogue source so developers receive the correct Artifactory channel without manual configuration — every developer must run `agentbundle config set source <url>` after install, and the correct URL lives outside the vetted fork. This spec inserts a new **Layer 3** into the source precedence chain — between user config (Layer 2) and editable-clone detection (now Layer 4) — sourced from an optional `[organization.artifactory]` block in the packaged `_data/install-defaults.toml`. When `enabled = false` (the public default) the layer is a no-op. When `enabled = true`, the layer constructs a `catalogue+https://` URI from four required fields (`base-url`, `repository`, `bundle`, `channel`) and returns it as the resolved source, or fails closed with a named error if any field is malformed. The five-layer chain after this spec:

```
Layer 1: Explicit --catalogue argument (unchanged)
Layer 2: User [settings].source (unchanged)
Layer 3: Package-shipped org Artifactory bootstrap  ← NEW (this spec)
Layer 4: Editable-install detection via PEP 610 (unchanged, renumbered from 3)
Layer 5: Packaged [defaults].source in install-defaults.toml (unchanged, renumbered from 4)
```

The public repo ships `enabled = false`; no real org endpoints are committed to any in-repo file.

## Boundaries

### Always do

- Read `[organization.artifactory]` from the same `_data/install-defaults.toml` file already read by Layer 5 (`read_packaged_default`).
- Treat an absent `[organization.artifactory]` table, an absent `enabled` key, `enabled = false`, or an unparseable TOML file as disabled — return `None` and fall through to Layer 4 silently. (An unparseable file cannot reveal the value of `enabled`, so fail-closed does not apply; see Assumptions.)
- When `enabled = true` (a TOML boolean, not a string), apply all validation rules before constructing the URL; on any failure raise `CatalogueError` naming the malformed field and the path to `install-defaults.toml` — do NOT fall through to Layer 4.
- Type-check that each required field (`base-url`, `repository`, `bundle`, `channel`) is a non-empty `str` before parsing it; a non-string TOML value (int, bool, array) when `enabled = true` must raise `CatalogueError` naming the field, not a bare `TypeError`.
- Validate `base-url` by a case-sensitive string prefix check (`base-url.startswith("https://")`) before `urlsplit`-based validation — reject uppercase schemes (e.g., `HTTPS://`) at the field-validation stage so the constructed URL reliably starts with the lowercase `catalogue+https://` prefix required by `_is_valid_source`.
- Validate `base-url` netloc (from `urlsplit`) is non-empty, contains no user-info (`@` in netloc), and that query and fragment components are both empty.
- Normalize a trailing slash on `base-url` before URL construction (strip any trailing `/` from the raw value before joining path segments).
- Validate `repository`, `bundle`, and `channel` each match `[A-Za-z0-9._-]+` (non-empty; only alphanumeric, dot, underscore, hyphen); additionally reject `..` explicitly before the regex check as defense-in-depth.
- Construct the URL as `catalogue+<normalized_base_url>/<repository>/catalogues/<bundle>/channels/<channel>.json`.
- Evaluate Layer 3 only when Layer 1 (`--catalogue` explicit arg) and Layer 2 (user `[settings].source`) are both absent or empty — Layer 3 is never reached when a higher-priority layer yields a source.
- Error messages from Layer 3 must name the malformed field and the `install-defaults.toml` path; they must never include the raw field value when that value could contain credentials (in particular, a user-info-bearing `base-url` must not be echoed in the error).
- Use Python 3.11 stdlib only — no new runtime dependencies.
- Ship `enabled = false` as the public default in `install-defaults.toml`; never commit real org endpoints, org names, or Artifactory hostnames to the public repository.
- Use `example.test` hostnames in all tests and documentation added by this spec.

### Ask first

- Adding support for HTTP (non-TLS) `base-url` values.
- Allowing `base-url` to contain query parameters.
- Adding any credential field to `[organization.artifactory]` (e.g., `token`, `password`, `api-key`).
- Relaxing the `[A-Za-z0-9._-]+` grammar for `repository`, `bundle`, or `channel`.
- Adding a per-adapter allow-list to restrict which adapters apply the org bootstrap.
- Softening the fail-closed behavior for `enabled = true` with malformed config to a warning + fall-through instead of an error.

### Never do

- Fall through to Layer 4 (editable detection) when `enabled = true` and a validation error is encountered — fail-closed is the only correct behavior for an explicitly-enabled org config.
- Accept `http://` (or any non-`https` scheme) as `base-url`.
- Accept `base-url` values containing user-info (any `@` in the netloc).
- Accept `base-url` values with a non-empty query string or fragment.
- Accept `repository`, `bundle`, or `channel` values containing `/`, `..`, `%`, space, or any character outside `[A-Za-z0-9._-]`.
- Commit any real org endpoint, Artifactory hostname, or `enabled = true` configuration to the public repository.
- Store credentials, bearer tokens, or `Authorization` header content in `install-defaults.toml`.
- Produce a constructed URL containing user-info or credential query params (the `base-url` validation and the path-segment grammar guarantee this structurally).
- Add a certificate-disable or TLS-bypass option.
- Introduce a new runtime dependency.

## Testing Strategy

- **TDD** for `_source_from_org_bootstrap` validation rules: table-driven tests covering each acceptance criterion using minimal inline TOML string fixtures. Each validation failure must produce a `CatalogueError` with the field name and config path. Red-green-refactor; stub before production code.
- **TDD** for URL construction: tests cover trailing-slash normalization on `base-url`, all four required fields, and the fully assembled `catalogue+https://` form.
- **Unit** for disabled cases: absent `[organization.artifactory]` table, absent `enabled` key, and `enabled = false` must each return `None` without inspecting other fields.
- **Unit** for `read_org_bootstrap`: verify that calling it with an injected reader that returns the public default TOML text returns `None`, and that calling it with a valid `enabled = true` TOML returns the constructed URL.
- **Integration** for Layer 3 position in `resolve_default_source`: one test where Layer 1 and Layer 2 are both absent and an injected `read_org` returns a valid URL — asserts the resolved source equals that URL. A second test where a valid Layer 2 `config_source` is present and `read_org` would return a valid URL — asserts Layer 2 wins and the `read_org` callable is never called.
- **Integration** for fail-closed propagation: inject `read_org` as a function that raises `CatalogueError`; call `resolve_default_source` with Layer 1 and Layer 2 absent; assert the `CatalogueError` propagates and Layer 4 is not reached (verify by asserting `dist` detection is never called).
- **Goal-based check** for no real endpoints: `grep -n "enabled = true" packages/agentbundle/agentbundle/_data/install-defaults.toml` returns zero lines.
- **Goal-based check** for no new runtime dependency: `pyproject.toml` dependency list unchanged; `_source_from_org_bootstrap` imports only stdlib modules (`tomllib`, `re`, `urllib.parse`).

## Acceptance Criteria

- [ ] AC1: `install-defaults.toml` ships an `[organization.artifactory]` block with `enabled = false` and no other fields. No real org endpoint, hostname, or `enabled = true` appears in any file committed to the public repository.
- [ ] AC2: When the `[organization.artifactory]` block is absent from `install-defaults.toml`, `_source_from_org_bootstrap` returns `None` (disabled — fall through silently).
- [ ] AC2b: When the TOML content of `install-defaults.toml` is unparseable (a `TOMLDecodeError`), `_source_from_org_bootstrap` returns `None` (fall through silently). This is an explicit exception to the fail-closed rule: fail-closed applies only when `enabled = true` can be positively read; an unreadable file cannot reveal the value of `enabled`.
- [ ] AC3: When the `enabled` key is absent from an otherwise-present `[organization.artifactory]` block, `_source_from_org_bootstrap` returns `None` (missing `enabled` is treated as `enabled = false`; not a validation error).
- [ ] AC3b: When the `enabled` key is present but not a TOML boolean (e.g., the TOML string `"true"` or an integer) → `CatalogueError` naming the `enabled` field and the config path. `enabled` must be the TOML boolean `true`, not a string representation of it.
- [ ] AC4: When `enabled = false` (TOML boolean), `_source_from_org_bootstrap` returns `None` without inspecting any other field.
- [ ] AC5: When `enabled = true` and all required fields are valid, `_source_from_org_bootstrap` returns `catalogue+<normalized_base_url>/<repository>/catalogues/<bundle>/channels/<channel>.json`.
- [ ] AC6: `base-url` trailing slash is normalized before URL construction: both `"https://example.test/art/"` and `"https://example.test/art"` produce `catalogue+https://example.test/art/<repository>/catalogues/<bundle>/channels/<channel>.json` with no double-slash.
- [ ] AC7: `base-url` that does not start with the literal `"https://"` (case-sensitive string prefix) — e.g., `"http://example.test/art"`, `"ftp://example.test"`, or `"HTTPS://example.test"` — → `CatalogueError` naming the `base-url` field and the `install-defaults.toml` path.
- [ ] AC8: `base-url` containing user-info (any `@` in the netloc, e.g., `"https://user:pass@example.test/art"` or `"https://user@example.test/art"`) → `CatalogueError` naming the `base-url` field and the config path. The error message must not include the raw `base-url` value (which contains the credential).
- [ ] AC9: `base-url` containing a non-empty query string (e.g., `"https://example.test/art?repo=x"`) → `CatalogueError` naming the `base-url` field and the config path.
- [ ] AC10: `base-url` containing a non-empty fragment (e.g., `"https://example.test/art#section"`) → `CatalogueError` naming the `base-url` field and the config path.
- [ ] AC11: An empty or whitespace-only `base-url` when `enabled = true` → `CatalogueError` naming the `base-url` field and the config path. An empty netloc (e.g., `"https:///path"`) → `CatalogueError` naming the `base-url` field.
- [ ] AC12: `repository` not matching `[A-Za-z0-9._-]+`, or equal to `".."`, or empty → `CatalogueError` naming the `repository` field and the config path.
- [ ] AC13: `bundle` not matching `[A-Za-z0-9._-]+`, or equal to `".."`, or empty → `CatalogueError` naming the `bundle` field and the config path.
- [ ] AC14: `channel` not matching `[A-Za-z0-9._-]+`, or equal to `".."`, or empty → `CatalogueError` naming the `channel` field and the config path.
- [ ] AC15: A missing required field (`base-url`, `repository`, `bundle`, or `channel` absent from the TOML table) when `enabled = true` → `CatalogueError` naming the absent field and the config path. Does not fall through to Layer 4.
- [ ] AC16: All `CatalogueError` messages from Layer 3 include both the field identifier (e.g., `organization.artifactory.base-url`) and the path string for `install-defaults.toml` as installed in the package.
- [x] AC17: A valid `enabled = true` config produces a `catalogue+https://` URL that `_is_valid_source` accepts (call `_is_valid_source` on the constructed URL and assert `True`). Dependency `spec/https-catalogue-channels` shipped; test is a normal passing assertion.
- [ ] AC18: Layer 3 is evaluated only when Layer 1 and Layer 2 both yield nothing — a test where a valid Layer 2 `config_source` is present and Layer 3 would return a valid URL asserts that `resolve_default_source` returns the Layer 2 value; the injected `read_org` callable is never invoked.
- [ ] AC19: When Layer 3 raises `CatalogueError` (fail-closed), the error propagates immediately from `resolve_default_source`; Layer 4 (editable detection) and Layer 5 (packaged default) are not evaluated. Verified by asserting the injected `dist` is not accessed and `read_packaged` is not called after the Layer 3 failure.
- [ ] AC20: All layer-numbering references in `source_defaults.py` are updated to reflect the five-layer chain. This includes the module docstring (four-layer → five-layer; numbered list), `resolve_default_source` docstring (names Layer 3 as the org Artifactory bootstrap, RFC-0072 D2), and every `# Layer N` section comment or docstring phrase that names a layer number from the old four-layer chain. The T3 Done-when grep verifies this exhaustively — no individual site enumeration is the source of truth; the grep is.
- [ ] AC21: No real org endpoint, org hostname, or `enabled = true` value appears in any test file or documentation added by this spec. All examples use `example.test` placeholders. Verified by: `grep -n "enabled = true" packages/agentbundle/agentbundle/_data/install-defaults.toml` returns zero lines; `grep -rnE "https?://[A-Za-z0-9.-]+" packages/agentbundle/tests/ docs/specs/organization-artifactory-bootstrap/ | grep -v "example\.test"` returns zero lines (any URL in files added by this spec must resolve to `example.test`).
- [ ] AC22: The constructed `catalogue+https://` URL netloc contains no user-info (guaranteed structurally: `base-url` validation rejects `@` in netloc; the path-segment grammar `[A-Za-z0-9._-]+` cannot produce `@` or credential characters in `repository`, `bundle`, or `channel`). The `base-url` path component is org-controlled and is not path-traversal-validated at the agentbundle level; the netloc and path-segment grammar guarantees are limited to those fields.
- [ ] AC23: No new runtime dependency is introduced. Verified by: `pyproject.toml` dependency list unchanged; `_source_from_org_bootstrap` imports only stdlib modules (`tomllib`, `re`, `urllib.parse`).
- [ ] AC24: All existing agentbundle tests pass after the change with no modifications to the tests themselves.

## Assumptions

- Technical: `_data/install-defaults.toml` is already read by `read_packaged_default` via `importlib.resources.files("agentbundle").joinpath("_data/install-defaults.toml")`; the same resource path is used for Layer 3. (source: `source_defaults.py` `read_packaged_default`)
- Technical: `tomllib.loads(text)` parses `[organization.artifactory]` (a dotted-key table header) as a nested dict: `data["organization"]["artifactory"]`. (source: TOML 1.0 spec; Python 3.11 stdlib `tomllib` docs)
- Technical: `[organization.artifactory]` coexists with `[defaults]` in `install-defaults.toml` — TOML tables at distinct top-level keys do not conflict. (source: TOML 1.0 spec)
- Technical: `_is_valid_source` in `source_defaults.py` accepts `catalogue+https://` URLs once `spec/https-catalogue-channels` is implemented (AC1 of that spec); AC17 of this spec depends on it. The dependency is one-way: this spec does not need to land before `spec/https-catalogue-channels`. (source: spec/https-catalogue-channels AC1)
- Technical: Layer 3 is non-functional end-to-end until `spec/https-catalogue-channels` ships. `resolve_catalogue` (`catalogue.py`) has no `catalogue+https://` fetch handler; an org fork setting `enabled = true` before that spec lands receives a confusing `resolve_catalogue` error, not a clean Layer-3 `CatalogueError`. This is a fork-sequencing hazard — org forks must not enable the bootstrap until the resolver ships. The scope of this spec is the bootstrap layer (construction + wiring into the precedence chain); the fetch path is `spec/https-catalogue-channels`'s scope. (source: `catalogue.py` code inspection; RFC-0072 D1/D2 split)
- Technical: `CatalogueError` is importable from `agentbundle.catalogue` and is already used by `resolve_default_source` for the all-layers-empty case. (source: `source_defaults.py` import block)
- Technical: `urlsplit` (from `urllib.parse`) correctly identifies `scheme`, `netloc`, `query`, and `fragment` components for `https://` URLs; `"@" in parsed.netloc` reliably detects user-info including bare `user@host` (where `parsed.username` may be an empty string). (source: Python 3.11 stdlib; same approach as `canonicalize_source` in `spec/packstate-source-provenance`)
- Technical: The `config_path` string supplied to `_source_from_org_bootstrap` is obtained from `str(resource)` where `resource` is the `Traversable` returned by `importlib.resources.files`. On zipimport-backed packages `str()` may not yield a filesystem path; the resulting label is still more informative than no path. (source: Python importlib.resources docs; packaging edge cases)
- Technical: `re.fullmatch(r"[A-Za-z0-9._-]+", val)` returns `None` for empty strings (the `+` quantifier requires at least one character), for values containing `/`, `%`, space, or other out-of-grammar characters. An explicit `..` check before the regex call handles the case where both `.` characters are individually in-grammar but the combination is a path-traversal pattern. (source: Python `re` docs; design decision in Behavior & rules)
- Technical: Fail-closed semantics apply only when `enabled = true` can be positively read. An unparseable `install-defaults.toml` (a `TOMLDecodeError`) does not allow reading `enabled`; returning `None` (disabled) is the only correct behavior. This is documented in AC2b and is a deliberate exception to the general fail-closed rule. (source: RFC-0072 D2 — "fail-closed on malformed `enabled = true` config" implies the value must be readable; an unreadable file is a different failure mode)
- Technical: The `base-url` path component (the URL path beyond the netloc, e.g., `/artifactory` in `https://example.test/artifactory`) is org-controlled content in a vetted fork. Path-traversal validation is not applied to the `base-url` path; it is applied to `repository`, `bundle`, and `channel` (the path segments appended by agentbundle's URL construction). AC22 is scoped to netloc and appended segment guarantees only. (source: RFC-0072 D2; design decision)
- Technical: Python 3.11 stdlib-only runtime constraint. (source: `pyproject.toml`; RFC-0072)
- Process: RFC-0072 is Accepted; this spec implements D2 (org Artifactory bootstrap). (source: RFC-0072 status: Accepted)
- Product: No user-visible CLI surface change — the org bootstrap fires silently when enabled and no higher layer is active. The only user-visible output is the `CatalogueError` on fail-closed, which names the config path. (source: RFC-0072 D2)
