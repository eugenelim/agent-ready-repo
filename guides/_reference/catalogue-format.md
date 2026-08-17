# Catalogue format

:::note
Version: 1 (the `schema = 1` field in `catalogue.toml`).
:::

## Required markers

Two markers make a directory a valid agentbundle catalogue:
- `catalogue.toml` at the catalogue root
- literal root `packs/` directory

Both are checked by `source_defaults._has_catalogue_markers`.

## Required files

- `catalogue.toml` — catalogue configuration. Must pass `contracts/catalogue.schema.json`.
- `packs/<name>/pack.toml` per pack — must pass `contracts/pack.schema.json`.

## Adapter artifacts

`.claude-plugin/marketplace.json` is generated and required when the effective
self-host adapter set includes `claude-code`. It is not catalogue identity;
catalogues that project only a non-Claude adapter may omit it.

## Schema contracts

All schemas live in `contracts/`:
- [`catalogue.schema.json`](../../contracts/catalogue.schema.json)
- [`pack.schema.json`](../../contracts/pack.schema.json)
- [`skill.schema.json`](../../contracts/skill.schema.json)
- [`skill-manifest.schema.json`](../../contracts/skill-manifest.schema.json)
- [`profile.schema.json`](../../contracts/profile.schema.json)
- [`adapter.schema.json`](../../contracts/adapter.schema.json)

## Format version

`catalogue.toml` carries `schema = 1`. This is the format version contract.
Tooling that implements the agentbundle catalogue format checks this field.
The contracts above define what `schema = 1` means.

## Validation

```bash
agentbundle catalogue verify --root .
```
Runs the full 19-step pipeline including schema validation, pack lint,
post-build artifact checks, and self-host drift detection.

For CI pipeline patterns using `verify`, `lint`, and `package` — including
publication ordering, exit codes, and JSON output shapes — see the
[Catalogue CI contract](../_shared/reference/catalogue-ci-contract.md).
