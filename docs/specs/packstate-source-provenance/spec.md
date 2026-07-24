# Spec: PackState Source Provenance

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D3, D5), ADR-0036 (four-layer source chain this extends)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`PackState.source` currently defaults to the hard-coded literal `"agent-ready-repo"` regardless of where a pack was actually installed from, making it indistinguishable from a real provenance record. Every downstream operation that relies on source — conflict detection, upgrade routing, update-status reporting — is therefore unreliable. This spec replaces the hard-coded default with `None` (unknown provenance), introduces a single `canonicalize_source` function that all install and upgrade paths use to record sources, resets the dataclass default at `config.py:118` from the hard-coded literal to `None`, replaces the hard-coded source write at `install.py:1025` with `canonicalize_source(catalogue_uri)`, and updates the read-time parse fallback (`config.py:395`) to stop supplying `"agent-ready-repo"` as a default on read, and adds a `dump_state` None-omission guard so that `None` is serialized as an absent key rather than an empty value. The upgrade path adds an explicit source write (upgrade.py currently preserves whatever source the row had; this spec adds the write so an upgrade from a concrete source canonicalizes it). Legacy state files are read without mutation; the historical `"agent-ready-repo"` literal and `None` are both treated as unknown provenance by the canonicalization function.

## Boundaries

### Always do

- Use `canonicalize_source` at every site that **writes** `PackState.source` in the install and upgrade paths. Read sites (`_parse_adapter_row`) preserve the stored value verbatim — no canonicalization on read.
- Treat the historical literal `"agent-ready-repo"` and `None` as equivalent unknown provenance in canonicalization and comparison.
- Preserve existing state-file content on read — never mutate a row simply because its source is legacy.
- Redact any credentials or bearer tokens from source strings in all error messages, logs, and repr output.
- Use Python 3.11 stdlib only — no new runtime dependencies.
- Apply `canonicalize_source` to local paths (absolute-normalize) and remote URLs (scheme/host lowercase, trailing-slash normalize, reject user-info in netloc, reject query-string credential parameters, reject URI-fragment credential parameters).
- For the profile-install path, ensure the logical catalogue URI (not the resolved temp extraction directory) is what `canonicalize_source` is called with at the source write site.

### Ask first

- Any change to the TOML serialization format (key name, quoting style, field ordering) beyond omitting the `source` key when `None`.
- Any migration step that writes back a canonical source to legacy rows in existing state files without explicit user action (an upgrade or reinstall counts as explicit).
- Adding a `source` column to `list-installed` table output — that belongs to `spec/list-installed-update-status`.

### Never do

- Invent or guess a canonical source for a row whose source is `None` or `"agent-ready-repo"` — unknown is the correct and only answer.
- Write credentials, bearer tokens, `Authorization` header values, or URL user-info into `PackState.source`.
- Persist a temporary extraction path (e.g. a temp directory) as the canonical source — the logical channel URI is the stable identity.
- Add a `--migrate-sources` or similar flag for bulk source migration — the upgrade path is the documented migration mechanism.
- Introduce a new runtime dependency.
- Change the state schema version — the field becomes `str | None = None`; existing state files parse cleanly with no bump required.

## Testing Strategy

- **TDD** for `canonicalize_source`: pure function with compressible invariants (local path normalization, URL normalization, legacy literal detection, user-info rejection, query-string credential rejection, URI-fragment credential rejection). Red-green-refactor; stub before production code.
- **TDD** for `_parse_adapter_row` migration contract: table-driven tests covering absent `source` key → `None`; key present as `"agent-ready-repo"` → preserved as-is; key present as a real URL → preserved as-is. Verifies no mutation on read.
- **TDD** for `dump_state` round-trip: `source = None` omits the key; `source = "agent-ready-repo"` emits the key; `source = "git+https://..."` emits the key. Parsed back via `_parse_adapter_row`, values round-trip correctly.
- **Integration test** for install write path: after the fix, running `agentbundle install` against a local catalogue fixture writes a non-`"agent-ready-repo"` source equal to `canonicalize_source(catalogue_uri)`. Verified by reading the written state file.
- **Integration test** for profile-install write path: after the fix, a profile install records the logical catalogue URI (not a temp dir path) as source in every installed pack row.
- **Integration test** for upgrade write path: an upgrade from a legacy-source row (`"agent-ready-repo"`) updates `PackState.source` to the canonicalized catalogue URI; an upgrade from a concrete-source row preserves or re-canonicalizes to the same value.
- **Goal-based check** for no regression: all existing tests pass after the change. Verifies AC16.
- **Goal-based check** for no new runtime dependency: `pyproject.toml` shows no new dependency additions; `canonicalize_source` imports only stdlib modules (grep-verified). Verifies AC17.

## Acceptance Criteria

- [ ] AC1: `PackState.source` field type is `str | None` with default `None`; existing code that constructs `PackState` with no `source` argument compiles and runs correctly.
- [ ] AC2: `_parse_adapter_row` returns `None` for the `source` field when the TOML row has no `source` key (previously returned `"agent-ready-repo"`).
- [ ] AC3: `_parse_adapter_row` preserves the existing string value (including `"agent-ready-repo"`) when the TOML row has an explicit `source` key — legacy state files are read without mutation.
- [ ] AC4: `dump_state` omits the `source` key when `PackState.source is None`; emits `source = "<value>"` for any non-`None` source including the legacy literal.
- [ ] AC5: `canonicalize_source(value: str | None) -> str | None` exists in `agentbundle/config.py` (or a sibling module imported by it) and is the single canonicalization function used by the install and upgrade paths in this spec. Status and conflict-check paths are wired in later specs (`spec/list-installed-update-status`, `spec/source-conflict-install-guard`) and are out of scope here.
- [ ] AC6: `canonicalize_source(None)` → `None`.
- [ ] AC7: `canonicalize_source("agent-ready-repo")` → `None` (legacy/unknown provenance).
- [ ] AC8: `canonicalize_source(local_path)` → absolute normalized string path, with `.` and `..` resolved, regardless of whether the path exists (path resolution only, not marker validation).
- [ ] AC9: `canonicalize_source(remote_url)` → logical channel URI with scheme and hostname lowercased, trailing slash normalized, user-info in netloc rejected (returns `None` on user-info present).
- [ ] AC9b: Credential-style parameters in query strings or URI fragments are rejected — e.g. `canonicalize_source("git+https://example.test/repo?access_token=SECRET")` → `None` and `canonicalize_source("git+https://example.test/repo#access_token=SECRET")` → `None`. No credential leaks into state TOML via query or fragment.
- [ ] AC10: `canonicalize_source` return value never includes credentials, bearer tokens, URL user-info, or Authorization header content.
- [ ] AC11: The install write path records `canonicalize_source(catalogue_uri)` as `PackState.source` — no hard-coded `"agent-ready-repo"` literal remains in the install write path. (The specific line in `install.py` is an implementation detail named in Assumptions, not part of the observable contract.)
- [ ] AC12: A fresh install of any pack against a local catalogue fixture writes a canonical source equal to `canonicalize_source(catalogue_uri)` where `catalogue_uri` is the logical URI passed to `resolve_catalogue`, not the resolved temp dir path.
- [ ] AC13: A fresh install against a `git+https://` source writes a canonical source equal to `canonicalize_source(that_uri)` — lowercased scheme+host, trailing slash normalized.
- [ ] AC14: The upgrade write path adds an explicit `PackState.source` write for **whole-pack upgrades** (upgrade.py currently preserves the existing row source by not writing it; this spec adds the write to the whole-pack branch). After a whole-pack upgrade, `PackState.source` equals `canonicalize_source(catalogue_uri_used_for_upgrade)` when `canonicalize_source` returns a non-`None` value, or is left as the existing source when `canonicalize_source` returns `None` (legacy catalogue URI). Per-primitive (single-skill) upgrades are out of scope for the source write in this spec.
- [ ] AC14b: A profile install (where the per-pack `catalogue_uri` may be threaded differently through `install.py`) records the logical catalogue URI (not a temp dir path) as `PackState.source` for each installed pack row.
- [ ] AC15: Reading a legacy state file (one with `source = "agent-ready-repo"` rows) neither fails nor mutates the file — the rows are returned with `source = "agent-ready-repo"` and all fields intact.
- [ ] AC16: All existing agentbundle tests pass after the change with no modifications to the tests themselves.
- [ ] AC17: No new runtime dependency is introduced. Verified by: `pyproject.toml` dependency list unchanged after the change; `canonicalize_source` imports no non-stdlib module.

## Assumptions

- Technical: `PackState` is defined at `config.py:114`; the default field value `"agent-ready-repo"` is at `config.py:118`; `_parse_adapter_row` fallback is at `config.py:395`; the install write site is at `install.py:1025`. (source: code inspection)
- Technical: Python 3.11, stdlib-only runtime constraint (source: `pyproject.toml`; RFC-0072)
- Technical: State schema version bump is not required — `str | None = None` is backward-compatible with existing TOML state files that omit the key. (source: RFC-0072 § Key assumptions)
- Technical: `catalogue_uri` (the resolved source string) is in scope at the `install.py:1025` write site. (source: `install.py` — `catalogue_uri` is passed to `resolve_catalogue()` at line 209 and remains in scope through the `PackState` construction)
- Technical: `_is_valid_source` in `source_defaults.py` does not need to change for this spec — it validates sources for layers 2 and 4, not for recording provenance. (source: code inspection; `_is_valid_source` is the scheme gate, not the canonicalization layer)
- Process: RFC-0072 is Accepted; this spec implements its D3 (source conflict semantics rely on canonicalization) and D5 (new CLI surface — source column comes in list-installed spec, not here). (source: user confirmation 2026-07-23)
- Product: No user-visible output changes in this spec — `list-installed` source column is `spec/list-installed-update-status`. (source: user confirmation 2026-07-23)
