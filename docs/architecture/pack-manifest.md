# Pack manifest: source of truth and lossy projection

> `pack.toml` is the single source of truth for a pack's metadata. The build
> derives a smaller subset from it and projects that subset into each
> distribution route's manifest. The projection is lossy by design: a field a
> route has no slot for stays in `pack.toml` and is not emitted there.

An author declares everything once. Hand-maintained per-route metadata would
drift, so the build emits only the cleanly mappable part per route. The decision
record is [ADR-0021](../adr/0021-pack-manifest-source-of-truth-and-scoped-identity.md).

The on-disk shape of a pack is in [`pack-layout.md`](pack-layout.md).

## What `pack.toml` declares

`[pack]` requires `name` and `version`. Every other field is optional in the
schema, and every shipped pack also declares `description`.[^1]

| Group | Fields | Consumer |
| --- | --- | --- |
| Identity and display | `name`, `version`, `description`, `display_name`, `readme`, `license`, `catalogue` | Projection, `list-packs` |
| Discovery | `categories` (≤5, soft vocabulary: an unknown slug warns), `keywords` (≤5), `[[pack.maintainers]]`, `[pack.links]`, `[pack.metadata.<tool>]` (opaque passthrough) | Projection, catalogue index |
| Install contract | `[pack.adapter-contract]`, `[pack.install]`, `layout`, `adaptation`, `runtime-dependencies`, `lint-seeds` | Resolver, installer, lint |
| Composition | `[pack.dependencies]` (`required`, `recommended`, `conflicts`), `integrations`, `recipes` | Verify, sync, catalogue index |
| Adoption and verification | `first-value`, `evals`, `seeds` | Guides, eval runner, installer |

A pack with no `[pack.adapter-contract]` or with contract `0.1` resolves to
repo scope and ignores any `[pack.install]` table.[^2]

A direct source that carries a `pack.toml` is validated against a narrower
profile than a catalogue pack, and several fields above are not admitted on that
route. A manifestless direct install is described in
[`catalogue/README.md`](catalogue/README.md#identity).

## The projectable subset

`derive_projectable_subset(pack_toml)` is a pure function from `pack.toml` to the
manifest subset.[^3] A key appears in the output only when its source field is
present and non-empty.

| Manifest key | Source | Rule |
| --- | --- | --- |
| `author` | `[[pack.maintainers]][0]` | `{"name", "email"}`; `email` omitted when absent |
| `license` | `[pack].license` | verbatim |
| `homepage` | `[pack.links].homepage` | verbatim |
| `repository` | `[pack.links].repository` | verbatim |
| `keywords` | `[pack].keywords` | string entries, verbatim |
| `category` | `[pack].categories[0]` | first category only |
| `displayName` | `[pack].display_name` | verbatim |
| `source` | `[pack.links].repository` + `[pack].name` | `git-subdir`: `{"source", "url": "https://github.com/<owner>/<repo>.git", "path": <pack>, "ref": <dist branch>}`. Emitted only for an `https://github.com/<owner>/<repo>` link: a link on another host emits no `source`, and an `http://` GitHub link raises. Marketplace entries only, stripped from `plugin.json` |

A pack that declares none of these emits no enriched fields.

## Where the subset lands

The subset merges into two outputs:

- the derived `dist/claude-plugins/<pack>/.claude-plugin/plugin.json` of every
  **user-capable** pack, beside the synthesised `SessionStart` hook. A pack whose
  `allowed-scopes` omits `user`, or that declares no
  `[pack.adapter-contract] version`, reaches neither output, because the route
  installs at user scope and the resolver gates on the contract version first;
- the pack's entry in the aggregated `.claude-plugin/marketplace.json`, built by
  `_aggregate_marketplace`.[^4]

The two outputs validate against different schemas because one schema cannot
serve both. `plugin.json` must not carry `source`, and a marketplace entry must
require it.

| Output | Schema |
| --- | --- |
| `plugin.json` | [`plugin-manifest.derived.schema.json`](../../contracts/plugin-manifest.derived.schema.json) |
| Each `marketplace.json` entry | [`marketplace-entry.schema.json`](../../contracts/marketplace-entry.schema.json): the derived schema plus required `source` and permitted `category` |
| Source-shape `plugin.json` | [`plugin-manifest.schema.json`](../../contracts/plugin-manifest.schema.json), admitting the same named subset |

All three keep `additionalProperties: false`, so a genuinely unknown key is
rejected.

The pack's `README.md` is copied verbatim into the claude-plugins and APM route
directories, so `readme = "README.md"` resolves relative to the route. A pack
without a README projects none and does not error. The README is the only
portable per-pack document.

Deeper guides live under `guides/` and the README
links to them.

## Identity: `@catalogue/pack`

`agentbundle list-packs` renders a pack as `@<catalogue>/<pack>` when
`[pack].catalogue` is set, and as the bare `<pack>` otherwise. This is
declaration and rendering only. Resolution is single-catalogue in `list-packs`
and `install`, and no cross-catalogue resolution exists.

## Limits

- **No hosted registry or persisted search.** The generated catalogue index is
  the only discovery document. A read-only `catalogue search` verb over it is
  STATUS: PLANNED, owned by [`catalogue-search-verb`](../product/intents/catalogue-search-verb.md).
- **No per-tool routing into other manifests.** The subset projects into the
  claude-plugins and APM `plugin.json` and `marketplace.json` surface only.
- **No URL-scheme allowlist on `[pack.links]` and no length cap on `author` or
  `displayName`.** These strings come from the trusted in-repo `packs/` tree and
  are projected verbatim. `pack.toml` is treated as trusted input; an untrusted
  `pack.toml` is out of scope.

[^1]: `contracts/pack.schema.json` (`properties.pack.required`); `packages/agentbundle/agentbundle/_data/pack.schema.json` is its byte-identical bundled copy.

[^2]: `packages/agentbundle/agentbundle/commands/validate.py` (`_allowed_scopes`).

[^3]: `packages/agentbundle/agentbundle/build/main.py` (`derive_projectable_subset`).

[^4]: `packages/agentbundle/agentbundle/build/self_host.py` (`_aggregate_marketplace`); `contracts/distribution-routes.toml` (`claude-plugins` route).
