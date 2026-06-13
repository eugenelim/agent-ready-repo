# Spec: enriched-pack-manifest

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
  <!-- Manifest layer shipped in #300. Guide-migration layer (AC9, AC10, and the
  good-enough-guide-home AC — ADR-0020) shipped in the per-pack-guide-migration PR,
  which also authored net-new guides for every pack per user direction. -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0031 (package-manager posture for the pack catalogue), RFC-0001 (bundle distribution by adapter — contract lives in `docs/contracts/`), RFC-0011 (optional `pack.toml` field under a contract bump, no legacy migration), ADR-0021 (`pack.toml` source-of-truth + lossy projection + `@catalogue/pack` identity — RFC-0031 D2/D7), ADR-0020 (per-pack Diátaxis hierarchy for `docs/guides/` — the `documentation` link target)
- **Contract:** `docs/contracts/pack.schema.json`, `docs/contracts/adapter.toml`, `docs/contracts/plugin-manifest.schema.json`, `docs/contracts/plugin-manifest.derived.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A pack today is described by only `name`, `version`, and `description` — far less than our own PyPI wheels or the tools' own marketplace formats carry. This feature makes **`pack.toml` the rich source of truth for pack metadata** and **projects a schema-compliant, lossy subset into each distribution route**, per RFC-0031. Two users benefit: the **pack author**, who declares author/license/links/categories/keywords and a rendered README once, in one file; and the **catalogue consumer**, who sees a pack described richly in the `marketplace.json` entry and the projected README rather than a single sentence. Success = every pack can declare the enriched metadata, **all 12 shipped packs** do (including `product-engineering`, RFC-0030, now landed on `main`), the build projects the cleanly-projectable subset (plus each pack's README) into the dist routes as schema-valid output, and legacy packs that omit the fields build and validate exactly as before. Scope is **declaration + projection only**: the `@catalogue/pack` identity is *declared* (field + canonical rendering), not *resolved*; no search command, no persisted index, no hosted infrastructure. The richer design also lands its **documentation surface**: the **projected README is the sole portable per-pack doc** and carries a *link-out* to deeper guides (we do **not** install guides into the pack payload or adopter repos); each pack's `documentation` link points at its **per-pack guide home** `docs/guides/<pack>/` (Diátaxis *within* each pack) in this repo; the PyPI-facing wheel READMEs are refreshed; and a `docs/architecture/` entry records the manifest-as-source-of-truth + lossy-projection model. The per-pack `docs/guides/` layout is **decided in ADR-0020** (amending ADR-0001) and **performed by this spec** — it migrates the existing guides into `docs/guides/<pack>/{quadrant}/`, adapts the `new-guide` skill, and amends `CONVENTIONS.md §5c`, so the `documentation` links resolve to real homes.

## Boundaries

### Always do

- Keep every new manifest field **optional** — a pack that omits them must validate and build unchanged.
- Gate the enriched schema behind an **adapter-contract bump `0.13 → 0.14`** (`docs/contracts/adapter.toml` + its `packages/agentbundle/agentbundle/_data/adapter.toml` mirror), and run the **full `agentbundle` package pytest** by hand (a contract bump trips version-pinned assertions across CI-ungated test roots).
- Assert behavior as **what we emit/project** — schema-compliant `pack.toml`, `plugin.json`/`marketplace.json` entries, and projected README files — never how a third-party tool renders them.
- Bump each modified pack's `version` (non-cosmetic pack change) and add a `docs/product/changelog.md` `[Unreleased]` entry.

### Ask first

- Any change to the **canonical contract location** (`docs/contracts/`) or the `marketplace.json` aggregation **shape** (owner/plugins envelope) beyond additively surfacing the projectable fields.
- Adding any **new runtime dependency** (the manifest parse path is stdlib `tomllib`/`json` today).
- Trimming or extending the ~16-slug default `categories` vocabulary away from the RFC-0031 list.
- Authoring **substantial net-new guide content** per pack — this spec *relocates and reorganizes* the existing guides into the per-pack layout (and fixes cross-links); writing new deep guides for thin packs is doc-debt follow-up.

### Never do

- **No `@catalogue/pack` resolution logic** — declare-only; single-catalogue resolution in `list-packs`/`install` stays exactly as is (multi-catalogue resolution belongs to the index-contract / virtual-catalogue follow-on RFC).
- **No new top-level directory and no new runtime dependency** (structural).
- No hosted-registry / server / persisted-index / `agentbundle search` code — all out of scope per RFC-0031.
- No **breaking change** to legacy (`< 0.14`) packs; no relocation of the `docs/contracts/` schema files.
- Project the enriched subset **only into the claude-plugins + apm routes** (the `plugin.json` / `marketplace.json` surface). Per-tool **Codex / Copilot / Cursor field routing is deferred** to a follow-on (RFC-0031 D2 flagged their unknown-field handling unverified).
- (structural) **Do not install guides into the pack payload or adopter repos** — the README is the only portable per-pack doc and it *links out*; deeper guides are repo-internal under `docs/guides/`. (Installing guides isn't viable anyway: 8/12 packs are user-scope and the seeds-rail blocks them, and it isn't spec-compliant.)
- **Do not change the adopter-facing `user-guide-diataxis` seed scaffold's type-at-top layout** — per ADR-0020 only the repo-internal `docs/guides/` reorganizes to per-pack; the seed an adopter installs stays Diátaxis-by-quadrant.
- Don't make an unknown `categories` slug a hard error — it is a **warning** (soft vocabulary).

## Testing Strategy

- **Schema acceptance/rejection rules** (new fields accepted; types enforced; `[pack.metadata.<tool>]` passthrough; optional `catalogue`) — **TDD** (logic with a compressible invariant: valid manifests pass, malformed ones fail).
- **Soft `categories` validation** (unknown slug → warning, exit 0; known slug → silent) — **TDD**.
- **`@catalogue/pack` canonical rendering** in `list-packs` output (scoped when `catalogue` set, bare otherwise; no resolution change) — **TDD**.
- **Projection of the projectable subset** from `pack.toml` into `plugin.json`/`marketplace.json` entries, valid against the relaxed `plugin-manifest.derived.schema.json` — **TDD** on the projector + **goal-based** (`make build-check` green; `jsonschema` validate of the output).
- **README projection** into the claude-plugins and apm dist routes, referenced via the `readme` field — **goal-based** (build, then file-exists / `grep`).
- **Contract-bump cascade** (version-gated schema + pinned assertions updated) — **goal-based** (full package pytest green).
- **All 12 packs populated + clean** — **goal-based** (`agentbundle validate <pack>` exits 0 for each).
- **Legacy-pack invariance** (a manifest omitting the new fields, on `< 0.14`, builds + validates unchanged) — **goal-based**, exercised as an **integration** test over the build pipeline.

## Acceptance Criteria

- [x] `docs/contracts/pack.schema.json` accepts the new **optional** first-class fields — `readme` (string path), `display_name` (string), `license` (string), `[[pack.maintainers]]` (`{name, email?, url?}`), `[pack.links]` (`homepage`/`repository`/`documentation`/`changelog`/`issues`/`icon`, all string), `categories` (array, ≤5), `keywords` (array, ≤5) — both capped at 5 per RFC-0031 D3 / Cargo's max-5 convention — and an arbitrary `[pack.metadata.<tool>]` table; a manifest omitting all of them still validates.
- [x] An optional `[pack].catalogue` field is accepted (**declare-only**, nested under `[pack]` to match every other new field and RFC-0031 D7); `list-packs` renders identity as `@<catalogue>/<pack>` when `catalogue` is set and as the bare `<pack>` otherwise; no multi-catalogue resolution path is added or changed.
- [x] adapter-contract is bumped `0.13 → 0.14` in `docs/contracts/adapter.toml` and the `_data` mirror; all version-pinned assertions and any version-gated schema branch are updated; the **full `agentbundle` package pytest is green**.
- [x] Both `docs/contracts/plugin-manifest.schema.json` and `docs/contracts/plugin-manifest.derived.schema.json` admit the projectable subset (`author`, `license`, `homepage`, `repository`, `keywords`, `category`, and `displayName`); `make build-check` is green.
- [x] The build derives the projectable subset from each pack's `pack.toml` into its `plugin.json` / aggregated `marketplace.json` entry — with the fixed mapping `author` ← first `[[pack.maintainers]]` rendered as `"Name <email>"` (name alone when no email), `category` ← `categories[0]`, `displayName` ← `display_name`, and `license`/`keywords`/`homepage`/`repository` carried verbatim — and the output validates against `plugin-manifest.derived.schema.json`.
- [x] Each pack's `README.md` is projected into the `dist/claude-plugins/<pack>/` and `dist/apm/<pack>/` routes and is referenced by the **route-level `pack.toml` manifest's** `readme` field (the `pack.toml` is projected verbatim alongside the README, so its `readme = "README.md"` pointer resolves within the route; the `readme` pointer is intentionally *not* part of the lossy `plugin.json` subset).
- [x] An unknown `categories` slug produces a **warning and exit 0** during `agentbundle validate`; the ~16 default slugs (`code-review`, `testing`, `documentation`, `architecture`, `security`, `research`, `product-management`, `project-management`, `integrations`, `file-conversion`, `api-design`, `governance`, `credentials`, `devops`, `data`, `ai-agent`) are documented.
- [x] **All 12 shipped packs** (`architect`, `atlassian`, `contracts`, `converters`, `core`, `credential-brokers`, `figma`, `governance-extras`, `monorepo-extras`, `product-engineering`, `research`, `user-guide-diataxis`) declare the enriched metadata appropriate to each (at minimum `readme`, `license`, `[pack.links].repository`, `categories`, `keywords`) and bump their `version`; `agentbundle validate <pack>` exits 0 for each. (`product-engineering` had a pre-existing user-scope-seeds rail failure — it shipped `seeds/` while declaring `user` ∈ allowed-scopes; resolved in this PR by relocating its intent/rollup templates from `seeds/` into the owning skills' `assets/`, so the pack ships no `seeds/` and validates clean. See the `product-engineering-pack` / `value-stream-meta-repo` spec updates and the RFC-0030 / ADR-0022 errata.)
- [x] Legacy invariance: a pack omitting the new fields and pinned below `0.14` builds and validates byte-for-byte as before (no projected-output diff attributable to this change).
- [x] The existing `docs/guides/` content is migrated into the per-pack layout `docs/guides/<pack>/{quadrant}/` (pack-specific) and `docs/guides/_shared/{quadrant}/` (cross-cutting; the four per-quadrant writing-rule READMEs land under `_shared/<quadrant>/`), with the `new-guide` skill made **layout-aware** (per-pack when the repo is organized that way, by-quadrant otherwise) and this repo's per-pack convention recorded in `AGENTS.local.md`; every internal cross-link to a moved guide (root `README.md`, `CONTRIBUTING.md`, `docs/**`, skills, packs) is rewritten and resolves; the adopter `user-guide-diataxis` seed scaffold is unchanged. (`CONVENTIONS.md §5c` is **projected from the adopter seed**, so it stays by-quadrant rather than describing the repo-internal per-pack layout — recorded as an **ADR-0020 erratum**, diverging from that ADR's "amend §5c" instruction.)
- [x] Each pack's `[pack.links].documentation` points to its **per-pack guide home** `docs/guides/<pack>/` (Diátaxis within the pack) as an absolute repo URL on `main`, and the projected README links out to it ("go deeper →").
- [x] **Every pack has a real, good-enough guide home.** Each of the 12 packs has a `docs/guides/<pack>/README.md` index; the 7 previously-undocumented packs (`atlassian`, `contracts`, `converters`, `figma`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`) gain net-new Diátaxis guides (standard depth — a home/explanation + the key how-to(s) + a reference per pack), and clear gaps in already-documented packs are filled (`architect` gains diagram + review how-tos). Guides are authored in the **adopter-facing developer-evangelist voice** (human, usage- and understanding-focused, matching the repo `README.md`). `new-rfc`/`new-adr`/`update-conventions` guides live under `governance-extras/` (the pack that ships those skills), not `_shared/`. *(Per user direction 2026-06-13, which lifts this spec's earlier "Ask first → authoring substantial net-new guide content per pack" deferral for the guide-migration layer.)*
- [x] The PyPI-facing `packages/agentbundle/README.md` is updated to reflect the enriched-manifest design (the `long_description` rendered on PyPI); `packages/credbroker/README.md` is reviewed and updated only if the design touches it (else left unchanged with a noted reason — it is left unchanged: the design does not touch the credential-resolver domain).
- [x] A `docs/architecture/pack-manifest.md` entry documents the manifest-as-source-of-truth + lossy-per-tool-projection model and links from `docs/architecture/overview.md`; `docs/architecture/pack-layout.md`'s `[pack]` field list + contract-version mention are updated. (overview.md's § The catalogue lists every pack; per maintainer direction it does **not** carry a hardcoded count — diverges from the AC13 "states the count (12)" wording below, which is superseded by that direction.)
- [x] `docs/product/changelog.md` `[Unreleased]` carries an entry.

## Assumptions

- Technical: `pack.toml`/`pack.schema.json` is ours and the `[pack]` object has no `additionalProperties:false` → extensible without a structural rewrite (source: `docs/contracts/pack.schema.json`, grep 2026-06-13).
- Technical: adapter-contract is currently `0.13`, mirrored in `_data/adapter.toml`; a bump touches ~7 files incl. `build/tests/test_contract.py` and per-adapter tests (source: `docs/contracts/adapter.toml:66` + grep `0.13`).
- Technical: both `plugin-manifest.schema.json` and `plugin-manifest.derived.schema.json` set `additionalProperties:false`; the derived schema validates projected output in `build/main.py` + `build/tests/test_plugin_manifest_schema.py` — it is the binding gate (source: grep 2026-06-13).
- Technical: `marketplace.json` is aggregated from each pack's `.claude-plugin/plugin.json` by `_aggregate_marketplace` (source: `self_host.py:494-521`).
- Technical: no top-level `catalogue` field exists today (only inside `[[pack.dependencies.*]]`); per-pack `README.md` is not yet projected into dist routes (source: grep `pack.schema.json`; `self_host.py:295-398`).
- Technical: `validate.py` already has a warn-and-exit-0 channel (`_drop_warning`) → precedent for soft-category warnings (source: `commands/validate.py`).
- Process: user-visible changes need a `docs/product/changelog.md` entry (source: `CONVENTIONS.md:466,603`).
- Product: `@catalogue/pack` is **declare-only** this spec; resolution defers to the index-contract/virtual-catalogue follow-on RFC (source: user confirmation 2026-06-13).
- Product: **all 12 shipped packs** are populated in the implementation — "that's the whole point". `product-engineering` (RFC-0030) landed on `main` 2026-06-13, bringing the count to **12** (verified by `find packs -name pack.toml`); it is enriched in the same sweep as the rest (source: user confirmation 2026-06-13).
- Product: `agentbundle search` and any persisted pack index are **out** — basic search needs no RFC (it runs over the live scan) but is sequenced after these fields; the persisted index is the RFC-gated follow-on (source: user confirmation 2026-06-13).
- Product: acceptance asserts **projected, schema-compliant output**, not third-party rendering (source: user confirmation 2026-06-13).
- Product/Process: **decided** — the projected README is the sole portable per-pack doc and *links out*; we do not install guides into packs (not viable: 8/12 packs are user-scope and the seeds-rail `scope_rails.py:87` blocks them; and not spec-compliant). Per-pack guides are repo-internal, and `docs/guides/` is **reorganized to a per-pack Diátaxis hierarchy** `docs/guides/<pack>/{quadrant}/` (Diátaxis explicitly permits a per-segment dimension — diataxis.fr/complex-hierarchies). That layout is **decided in ADR-0020** (amending ADR-0001, since the convention was defined there — an ADR, not an RFC, so the vehicle is a superseding/amending ADR, not an RFC erratum) and **implemented by this spec** (T12 migrates the guides; T13 amends `CONVENTIONS.md §5c` + the `new-guide` write path, co-landed so the Living doc matches reality). The adopter-facing seed scaffold stays by-quadrant (an adopter is one product; we are many packs). (source: ADR-0020; user direction 2026-06-13; research 2026-06-13; `scope_rails.py:87`).
- Product: the doc surface also covers the **PyPI wheel READMEs** and a **`docs/architecture/` entry** (source: user direction 2026-06-13).
- Technical: the repo's user docs already follow Diátaxis quadrants with a per-pack `explanation/core-pack.md` precedent (source: `find docs/guides` 2026-06-13).
