---
title: Catalogue format
summary: Use the authoritative directory, marker, schema, adapter-artifact, and validation contract when creating or checking a catalogue.
pack: _shared
kind: reference
slug: guides/_reference/catalogue-format
---

# Catalogue format

`catalogue.toml` tells `agentbundle` what a catalogue (a folder of packs and profiles) contains and where it is published. This page lists its markers, files, and checks for version 1, the `schema = 1` field in `catalogue.toml`.

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
- [`catalogue.schema.json`](../../../contracts/catalogue.schema.json)
- [`pack.schema.json`](../../../contracts/pack.schema.json)
- [`skill.schema.json`](../../../contracts/skill.schema.json)
- [`skill-manifest.schema.json`](../../../contracts/skill-manifest.schema.json)
- [`profile.schema.json`](../../../contracts/profile.schema.json)
- [`adapter.schema.json`](../../../contracts/adapter.schema.json)
- [`okf-pack-profile-v1.schema.json`](../../../contracts/jsonschema/okf-pack-profile-v1.schema.json)
- [`okf-agentbundle-extension-v1.schema.json`](../../../contracts/jsonschema/okf-agentbundle-extension-v1.schema.json)

## Optional OKF knowledge

A pack may declare one or more pack-local OKF 0.2 knowledge bundles:

```toml
[pack.metadata.okf]
profile = "agentbundle-okf/v1"

[[pack.metadata.okf.bundles]]
id = "delivery-practices"
path = "okf/delivery-practices"
"router-skill" = "delivery-practices-reference"
```

The declaration and `packs/<pack>/okf/<bundle>/` tree are the source of truth,
including the bundle-root `index.md`, which is hand-authored and must carry
`okf_version` and `license`. `compile-okf` owns the generated `index.md` files
beneath `.apm/skills/<router>/references/okf/`, the portable Skills beneath the
same pack's `.apm/skills/`, and `.okf-generated.json`. Maintainers edit source
and regenerate; they do not edit managed output as source.

`compile-okf` and the OKF fields `agentbundle show --format json` reports are
pre-release and repository-scoped. The authoring path is offline and
reference-only: bundle content stays inert, generated routers gain no execution
or network authority, and compilation is not part of install or
`agentbundle show`. See
[Author and compile an OKF bundle](../../catalogue-curation/how-to/author-an-okf-bundle.md)
for the complete write, check, recovery, and discovery workflow.

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
[Catalogue CI contract](catalogue-ci-contract.md).

## Scaffold options

`agentbundle catalogue init <dir>` takes these metadata flags. A fresh scaffold writes `catalogue.toml`, `.claude-plugin/marketplace.json`, a root `AGENTS.md` and `CLAUDE.md` (which contains `@AGENTS.md`), `packs/` and `profiles/` with an `_example` entry each, and the CI contract and authoring standards under `guides/_shared/reference/`. It never overwrites an existing file, so a second run reports each file as `SKIP (already-present)`. An existing root `AGENTS.md` or `CLAUDE.md` is kept and reported already-present with its on-disk hash. Any other existing file that differs is a conflict that blocks init.

| Flag | Default |
|------|---------|
| `--name NAME` | Derived from the directory name; letters, digits, hyphens, and underscores, starting with a letter or digit |
| `--display-name NAME` | Title-cased from `--name` |
| `--description TEXT` | Generated from `--name` |
| `--owner-name NAME` | Same as `--display-name` |
| `--preferred-adapter ADAPTER` | From `install-defaults.toml`, or `claude-code` |
| `--dry-run` | Off; lists the files it would create without writing |

## Troubleshooting

**Init reports `CONFLICT` for one or more files.** The target already holds those files with different content. Remove or rename the conflicting file and run init again, or use a new directory.

**`--name` fails validation.** Catalogue names must match `[A-Za-z0-9][A-Za-z0-9_\-]*`, so avoid spaces, dots, and slashes.

**`agentbundle catalogue verify` reports `CAT-V-016 install-defaults drift`.** Run `agentbundle catalogue sync-defaults --write --root <dir>` to regenerate the defaults file from `catalogue.toml`.
