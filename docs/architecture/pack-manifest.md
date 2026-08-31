# Pack manifest: source of truth + lossy projection

`pack.toml` is the **single, rich source of truth** for a pack's metadata.
The build derives a smaller, schema-compliant **subset** from it and projects
that into each distribution route's manifest, alongside the pack's `README.md`.

One route has no `pack.toml` at all. A **manifestless** direct install takes a
skill folder or a `skills/` collection from a repository that never declared a
pack, so there is no manifest to be the source of truth for. Such an install
derives its identity from the skill's own directory name and records its
provenance in install state rather than in a manifest. A direct source that
*does* carry a `pack.toml` is validated against a deliberately narrower profile
than a catalogue pack — the fields below still mean what they say, but several
are not admitted on that route.
This page describes that model. The on-disk *shape* of a pack lives in
[`pack-layout.md`](pack-layout.md); the decision record is
[ADR-0021](../adr/0021-pack-manifest-source-of-truth-and-scoped-identity.md).

## Why a source-of-truth + projection split

A pack today is consumed through several routes — `agentbundle install`, the
Claude-plugins `marketplace.json`, and the APM package — and each tool has its
own manifest vocabulary. Rather than hand-maintain per-route metadata (which
drifts), an author declares everything **once** in `pack.toml`, and the build
emits the cleanly-mappable part of it per route. The projection is
**deliberately lossy**: fields a route has no slot for stay in `pack.toml` and
simply aren't emitted there.

## What `pack.toml` carries

Beyond the required `name` / `version` / `description`, `[pack]` accepts the
optional enriched fields:

| Field | Shape | Notes |
| --- | --- | --- |
| `readme` | string | path to the pack's README (conventionally `"README.md"`) |
| `display_name` | string | human-friendly title |
| `license` | string | SPDX expression (e.g. `Apache-2.0 OR MIT`) |
| `categories` | array, ≤5 | **soft** vocabulary — unknown slug warns, never fails |
| `keywords` | array, ≤5 | free-form search terms |
| `catalogue` | string | declare-only identity scope (see below) |
| `[[pack.maintainers]]` | array of `{name, email?, url?}` | `name` required |
| `[pack.links]` | object | `homepage` / `repository` / `documentation` / `changelog` / `issues` / `icon` |
| `[pack.metadata.<tool>]` | object | opaque passthrough — the build reads only namespaces it knows |

Every enriched field is **optional**. A pack that declares none of them emits
no enriched projection fields.

## The projectable subset

`derive_projectable_subset(pack.toml)` (in
[`agentbundle/build/main.py`](../../packages/agentbundle/agentbundle/build/main.py))
is a pure function that maps `pack.toml` to the manifest subset:

| Manifest key | Source | Rule |
| --- | --- | --- |
| `author` | `[[pack.maintainers]][0]` | object `{"name": ..., "email": ...}`; `email` omitted when absent |
| `license` | `[pack].license` | verbatim |
| `homepage` | `[pack.links].homepage` | verbatim |
| `repository` | `[pack.links].repository` | verbatim |
| `keywords` | `[pack].keywords` | string entries, verbatim |
| `category` | `[pack].categories[0]` | first category only |
| `displayName` | `[pack].display_name` | verbatim |
| `source` | `[pack.links].repository` + `[pack].name` | `git-subdir`: `{"source", "url": "https://github.com/<owner>/<name>.git", "path": <pack>, "ref": <dist branch>}`. HTTPS only — an `http://` link raises. Marketplace entries only; stripped from `plugin.json` |

**Emit-only-when-present** is the load-bearing invariant: a key appears in the
output only when its source field is present and non-empty. The subset is
merged into:

- the derived `dist/claude-plugins/<pack>/.claude-plugin/plugin.json` of every
  **user-capable** pack (alongside the synthesised `SessionStart` hook) — a pack
  whose `allowed-scopes` omits `user` reaches neither, since the route installs
  at user scope — as does one with no `[pack.adapter-contract] version`, which
  the resolver gates on first, and
- that pack's entry in the aggregated `.claude-plugin/marketplace.json`
  (built by `_aggregate_marketplace` in
  [`self_host.py`](../../packages/agentbundle/agentbundle/build/self_host.py)).

The two outputs validate against *different* schemas, because one schema
cannot serve both: `plugin.json` must not carry `source` (the build strips it),
while a marketplace entry must require it. `plugin.json` validates against
[`plugin-manifest.derived.schema.json`](../../contracts/plugin-manifest.derived.schema.json);
each `marketplace.json` entry validates against
[`marketplace-entry.schema.json`](../../contracts/marketplace-entry.schema.json)
(the derived schema plus required `source` and permitted `category`). The
source-shape [`plugin-manifest.schema.json`](../../contracts/plugin-manifest.schema.json)
admits the same named subset. Both schemas keep `additionalProperties: false`;
a genuinely unknown key is rejected.

The pack's `README.md` is copied verbatim into both the claude-plugins and APM
route directories, so the `readme = "README.md"` pointer resolves relative to
the route. A pack without a README projects none and does not error. The README
is the **sole portable per-pack doc**; deeper guides live in this repo under
`guides/` and are linked from the README rather than shipped inside the
pack.

## `@catalogue/pack` identity (declare-only)

`agentbundle list-packs` renders a pack's canonical identity as
`@<catalogue>/<pack>` when `[pack].catalogue` is set, and the bare `<pack>`
otherwise. This is **declaration + rendering only** — there is no
multi-catalogue *resolution* path; single-catalogue resolution in `list-packs`
and `install` is unchanged. There is no cross-catalogue resolution.

## What is intentionally *not* here

- No hosted registry, persisted index, or `agentbundle search`.
- No per-tool field routing into the Codex / Copilot / Cursor manifests yet —
  the subset projects only into the claude-plugins + APM `plugin.json` /
  `marketplace.json` surface (a deferred follow-on).
- No `@catalogue/pack` resolution logic (declare-only, as above).
- No URL-scheme allowlist on `[pack.links]` and no length cap on `author` /
  `displayName`. Today these strings come from the **trusted** in-repo `packs/`
  tree, so they are projected verbatim. When the multi-catalogue / aggregation
  follow-on makes `pack.toml` an *untrusted author-controlled* input, that path
  must add a scheme allowlist (`https`/`http` only — reject `javascript:` /
  `data:` / `file:`) for the link fields and a length cap on the free-text
  metadata, in `pack.schema.json`. Tracked as a defense-in-depth item for that
  follow-on, not a gap in the current build-time-over-trusted-content model.
