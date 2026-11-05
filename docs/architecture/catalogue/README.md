# The catalogue

> A catalogue is a directory that holds `catalogue.toml` and a `packs/` tree.
> `agentbundle` reads packs from it, validates it, builds it, packages it, and
> derives new catalogues from it. `packs/` in this repository is one catalogue;
> nothing in the tool binds to it.

The catalogue subsystem answers five questions. Each has one owner in the
`agentbundle` package, and no registry service sits behind any of them.[^1]

| Question | Answer in one line | Section |
| --- | --- | --- |
| What makes a directory a catalogue? | `catalogue.toml` plus a literal root `packs/` | [Identity](#identity) |
| Which catalogue does a verb read? | A five-layer, first-match-wins resolver | [Resolution](#resolution) |
| How is a catalogue checked, built and released? | Ten `agentbundle catalogue` verbs | [Engine verbs](#engine-verbs) |
| What may an adopter rely on? | A versioned, published specification | [Specification](specification.md) |
| How does an adopter get their own? | Derive one, then sync upstream changes | [Derivation](#derivation) |

## Identity

A catalogue is the pair `catalogue.toml` and a root `packs/` directory. A
directory missing either is refused.[^2]

```
<catalogue-root>/
├── catalogue.toml                  # name, paths, build and distribution config
├── packs/<pack>/…                  # one directory per shippable pack
├── profiles/<profile>.toml         # named pack sets
└── .claude-plugin/marketplace.json # generated, only when claude-code is enabled
```

`marketplace.json` lists every pack whose `allowed-scopes` admits `user` and
that declares `[pack.adapter-contract] version`. The resolver gates on the
contract version first, so a pack without one resolves to `repo` whatever its
`allowed-scopes` says.

Repo-scoped packs are absent from the listing because the Claude-plugin route
installs at user scope.[^3] How `pack.toml` projects into an entry is in
[`pack-manifest.md`](../pack-manifest.md).

`install` also accepts a **direct source**: a skill folder, a `skills/`
collection, or one pack taken from a repository with no catalogue around it.
Such an install is **manifestless**: it takes its identity from the skill's
directory name and records provenance in install state. Direct sources have their
own admission rules.

A repository that carries catalogue markers takes the
catalogue route, and the direct route refuses it with a message saying so.[^4]

## Resolution

Every source verb takes an optional trailing catalogue argument. When it is
omitted, `resolve_default_source` walks five layers and returns the first
match.[^5]

| Layer | Source | Set by |
| --- | --- | --- |
| 1 | The explicit trailing argument, passed through verbatim | `agentbundle install core <catalogue>` |
| 2 | User config `[settings].source`, validated | `agentbundle config set source <catalogue>` |
| 3 | Org Artifactory bootstrap | `[distribution.agentbundle.artifactory]` in `catalogue.toml`, baked into `_data/install-defaults.toml` |
| 4 | Editable-install detection | `pip install -e <clone>` |
| 5 | Packaged default, validated | `default-source` in `catalogue.toml`, baked into `_data/install-defaults.toml` |

- **Layer 4** reads the package's PEP 610 `direct_url.json` and walks up from
  the package directory, bounded by the enclosing `.git` root, to the first
  ancestor holding both markers. A developer inside a clone gets that clone with
  no configuration.
- **`AGENTBUNDLE_NO_REMOTE=1`** skips layers 3 and 4.
- **Layer 3 fails closed.** An enabled bootstrap with a malformed field raises
  instead of falling through to layer 4.
- **No layer yields a source:** the CLI refuses with a message naming the
  recovery paths. It never falls back to the current directory.
- **Layer 5 tracks a mutable tip.** The packaged `git+https://` default names no
  ref, so it resolves the default branch at install time.
  STATUS: PLANNED — [`convenient-install-defaults-followons`](../../product/intents/convenient-install-defaults-followons.md)
  owns a post-acquisition integrity check.

A source is a local path holding both markers or a `git+https://` URL. A
`git+https://` value is accepted as written. A local path is validated at
resolution time, so a stale path fails with a diagnostic.

Remote
`catalogue+https://` and `archive+https://` sources authenticate through
[`portable-catalogue-authentication.md`](../portable-catalogue-authentication.md).

`~/.agentbundle/` is an install destination, never a source.

## Engine verbs

The engine is the public `agentbundle catalogue` command group. Verbs that read a
catalogue take its directory and use the confined-file helpers in `catalogue_tooling/file_safety.py`. `lint`, `verify`,
`build`, `self-host`, `package`, and `sync-defaults` take `--root`.

`init`,
`sync`, and `index` take a positional directory. `contracts` reads only bundled
files.[^6]

| Verb | Output | Notes |
| --- | --- | --- |
| `lint` | Diagnostics | Source-identity and pack-structure checks |
| `verify` | Diagnostics | Nineteen ordered steps over a source tree, or a packaged archive with `--archive` |
| `build` | `dist/` tree | Runs the declared distribution-route recipes |
| `self-host` | The repository's own projections | `--check` is read-only, `--write` projects |
| `package` | Release archive and `catalogue-manifest.json` | `--flavor runtime` or `source`, `--force`, `--compare <prior archive>` |
| `sync-defaults` | `_data/install-defaults.toml` | Derived from `catalogue.toml` |
| `index` | `catalogue-index.json` | Deterministic, adapter-neutral index of packs, profiles, effects, journeys and integrations |
| `contracts` | Bundled contract files | `list`, `show`, `export` |
| `init` | A scaffold catalogue, or a derived one with `--preset self-hosted` | See [Derivation](#derivation) |
| `sync` | Upstream changes in a derived catalogue | See [Derivation](#derivation) |

**Release integrity.** `package` records per-pack and per-profile SHA-256
digests in `catalogue-manifest.json`, refuses to overwrite an existing release
archive without `--force` (exit 2), and `--compare` reports differences against
a prior runtime archive. A unit digest proves that an archive agrees with its own
manifest.

It does not prove who published it.[^7]

**Index.** `index` reads `pack.toml` and `JOURNEY.md` files and writes one JSON
document validated against `catalogue-index.schema.json`. Optional descriptive
fields may be absent from a conforming index.[^8]

### Verify steps

`verify` runs these steps in order and returns one diagnostic list:
configuration, lint, pack schema, plugin validation, version parity, profiles,
dependencies, adapter compatibility, primitive layout, build output, agent
artifacts, marketplace, generated plugin manifests, output drift, self-host
drift, sync-defaults check, package preflight, deterministic fixture checks, pack
integration validation.[^9]

Two steps return clean when their input cannot be examined:

- the pack-schema step returns no diagnostics when the build validator cannot be
  imported;
- the version-parity step skips a pack whose `pack.toml` or `plugin.json` is
  absent or lacks a name or version.

STATUS: PLANNED — [`agentbundle-verify-fail-open-closure`](../../product/intents/agentbundle-verify-fail-open-closure.md)
closes both with bounded diagnostics.

## Specification

The contracts an adopter needs to build a catalogue are published as a versioned
specification on the docs site. [`specification.md`](specification.md) owns its
membership, release, and drift checks.

## Derivation

A derived catalogue is a copy of an upstream one under a new name, edited by its
adopter. Two commands own its life cycle:

- `catalogue init --preset self-hosted` copies a filtered subset and records the
  recipe. [`derived-catalogue.md`](derived-catalogue.md) owns what it copies and
  how white-label identity is kept out.
- `catalogue sync` takes later upstream changes without overwriting adopter
  edits. [`upstream-sync.md`](upstream-sync.md) owns it.
- [`state.md`](state.md) owns the two state files a catalogue tree can carry.

The adopter recipe for standing up an organisation catalogue is
[Build an org stack pack](../../../guides/_shared/how-to/build-an-org-stack-pack.md).

## Planned

| Capability | Boundary | Governing record |
| --- | --- | --- |
| `catalogue search` | A read-only query over `catalogue-index.json` facts only. It adds no index field and reads no source manifest. | [`catalogue-search-verb`](../../product/intents/catalogue-search-verb.md); no decision record exists yet |
| Rules primitive | One authored rule projected to each adapter's native rule surface, authored under a proposed `.apm/rules/` area. | [`catalogue-rules-primitive`](../../product/intents/catalogue-rules-primitive.md) |
| Adopter test command | One command that runs a catalogue's pack and conformance suites, one process per skill. No `test` verb exists. | [`adopter-catalogue-test-command`](../../product/intents/adopter-catalogue-test-command.md), [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md) |
| macOS Never Trust filtering | The corporate trust-store fallback skips certificates an administrator marked Never Trust. | [`catalogue-trust-store-trust-settings`](../../product/intents/catalogue-trust-store-trust-settings.md), [RFC-0086](../../rfc/0086-corporate-network-trust.md) |

Each row is STATUS: PLANNED. The adopter test command and the Never Trust filter
change `packages/agentbundle/**`, so each landing commit carries an
`Engine-Change-RFC:` trailer.

## Where to read next

- [`pack-layout.md`](../pack-layout.md) — the on-disk shape of one pack.
- [`pack-manifest.md`](../pack-manifest.md) — how `pack.toml` projects into
  manifests.
- [`skill-and-pack-format.md`](../skill-and-pack-format.md) — the format map from
  skill to pack to projection.
- [`../agentbundle.md`](../agentbundle.md) — build, install and upgrade.

[^1]: `packages/agentbundle/agentbundle/source_defaults.py` (`resolve_default_source`); `catalogue_tooling/` (engine verbs).

[^2]: `source_defaults._has_catalogue_markers`; lint validates configuration and configured paths.

[^3]: `contracts/distribution-routes.toml` (`claude-plugins` route); `docs/specs/claude-plugin-route-scope`.

[^4]: `direct_source.py`, `direct_install.py`; install-state schema `0.5` in `config.DIRECT_STATE_SCHEMA_VERSION`.

[^5]: `source_defaults.resolve_default_source`, `_detect_editable_source`, `read_org_bootstrap`, `read_packaged_default`; `catalogue.toml` `[distribution.agentbundle]`.

[^6]: `packages/agentbundle/agentbundle/cli.py` (`catalogue` subparsers); `catalogue_tooling/file_safety.py`.

[^7]: `commands/catalogue_package.py`, `catalogue_tooling/package.py`, `catalogue_tooling/archive.py`; `docs/guides/reference/catalogue-archive.md`.

[^8]: `catalogue_tooling/index_generator.py`, `contracts/catalogue-index.schema.json`.

[^9]: `catalogue_tooling/verify.py` (`_step_*` functions, in step order); `_step_pack_schema` and `_step_version_parity` carry the two clean-on-skip paths.
