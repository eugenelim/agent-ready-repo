# agentbundle — Design Document

Living design reference for the `agentbundle` Python package. Records the architecture, module responsibilities, key invariants, and decisions so the reasoning survives beyond individual PRs.

---

## TL;DR

`agentbundle` is a pack installer and catalogue manager. It resolves a catalogue source through a five-layer chain, validates it, fetches pack content, and projects it into the target repo (or user home) for the installed adapter. The resolution chain is stateless, first-match-wins, and fail-closed on malformed config — it never falls back silently.

---

## Module map

| Module | Responsibility |
|---|---|
| `cli.py` / `commands/` | Entry points; thin argument parsing; delegates to handlers |
| `catalogue.py` | Fetches and caches catalogue content; no source resolution |
| `source_defaults.py` | Five-layer source resolution chain (see below) |
| `catalogue_tooling/config.py` | Parses and validates `catalogue.toml` |
| `catalogue_tooling/defaults.py` | Generates `install-defaults.toml` from `catalogue.toml` |
| `catalogue_tooling/self_host.py` | Projects pack content into self-hosted adapter layouts |
| `catalogue_tooling/lint.py` | Structural lint of catalogue layout |
| `catalogue_tooling/verify.py` | Full 18-step pre-package verification |
| `catalogue_tooling/package.py` | Builds gzip archive + channel descriptor for Artifactory |
| `config.py` | User-scope pack config API (`pack_dir`, `load_pack_config`) |
| `oplog.py` | Per-pack operation log (JSONL, append-only) |
| `scope.py` | Adapter contract loading; shipped adapter names |
| `safety.py` | Path-confinement guards used across write paths |
| `_data/` | Bundled data files: schema, adapter contract, install-defaults |

---

## Source resolution chain

`resolve_default_source` in `source_defaults.py` implements a five-layer, first-match-wins chain. Higher layers win; a matched layer returns immediately without consulting lower ones.

```
Layer 1  explicit positional arg          pass-through verbatim, no validation
Layer 2  user [settings].source           validated; skipped if invalid (with stderr warning)
Layer 3  org Artifactory bootstrap        reads install-defaults.toml; fail-closed on malformed
Layer 4  editable-install detection       PEP 610 direct_url.json; stderr diagnostic on hit
Layer 5  packaged default                 [defaults].source in install-defaults.toml; validated
```

**Fail-closed at Layer 3:** if `enabled = true` and any field is malformed, Layer 3 raises `CatalogueError` rather than falling through to Layer 4. This prevents a misconfigured org wheel from silently resolving the public catalogue.

**AGENTBUNDLE_NO_REMOTE:** when this env var is set to any truthy value, Layers 3 and 4 are skipped entirely. Control falls directly to Layer 5 (packaged default) or the explicit argument. Used for offline and air-gapped deployments.

---

## Org bootstrap — how `install-defaults.toml` is generated

`catalogue.toml` declares the org's Artifactory coordinates under `[distribution.agentbundle.artifactory]`:

```toml
enabled    = true
base-url   = "https://artifactory.example.com"
repository = "agentbundle-catalogues"
bundle     = "engineering"
channel    = "stable"
```

`agentbundle catalogue sync-defaults --write` calls `compile_defaults` (in `defaults.py`) which reads the validated `CatalogueConfig` and writes `install-defaults.toml`. That file is committed to the fork and baked into the wheel.

**Invariant:** `load_catalogue_config` validates `channel` is present, non-empty, and matches `[A-Za-z0-9._-]+` when `enabled = true`. `compile_defaults` emits `art.channel or ""` — so the baked file always carries the real channel value, never an empty placeholder.

The URL constructed at runtime is:

```
catalogue+<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json
```

---

## `catalogue.toml` validation model

`load_catalogue_config` (`config.py`) runs two passes:

1. **JSON Schema** — structural validation via `agentbundle.build.validate`. Catches wrong types, unknown keys (`additionalProperties: false`), and missing required fields.
2. **Business rules** — constraints the schema cannot express: credentials in URLs, path traversal, preferred-adapter against the live contract, channel required when enabled, etc.

Both passes raise `CatalogueConfigError` (a subclass of `CatalogueError`). Schema errors list all violations; business rule errors name the specific field and suggest a correction.

---

## Security invariants

- **No credentials in URLs.** `_check_no_credentials` rejects userinfo in netloc and credential-looking query params (`token`, `password`, `key`, `secret`, `api_key`, `apikey`) in any source or base-url field.
- **Path confinement.** `_validate_path` and the `safety.py` guards reject absolute paths, `..` traversal, and symlink escapes outside the catalogue root. Applied to every path field in `catalogue.toml` and every write path in `defaults.py`.
- **Error messages never contain raw credential values.** Errors that reference a base-url with embedded credentials name the field and config path; they do not echo the URL.
- **Segment grammar.** `repository`, `bundle`, and `channel` in the org bootstrap are validated against `[A-Za-z0-9._-]+` and a `..` rejection before use in URL path construction.

---

## Key design decisions

**Resolution is stateless.** `resolve_default_source` never writes config and never reads the filesystem except via injected callables. This makes the precedence and validation logic unit-testable without touching real files or installed metadata.

**Fail-closed over silent fallback.** A misconfigured `enabled = true` block at Layer 3 raises rather than falling through. The invariant: if an operator configured Artifactory, a misconfiguration must surface immediately, not produce a confusing install from the wrong source.

**`compile_defaults` is a pure function.** Given a `CatalogueConfig`, it returns a deterministic TOML string. No filesystem reads, no side effects. `write_defaults` wraps it with path-jail enforcement and an atomic write.

**Schema and business rules are separated.** The JSON schema handles structural constraints that are cheap to express declaratively. Business rules (`channel` required-when-enabled, segment character set, source URL validation) are code — they produce better error messages and are easier to evolve.
