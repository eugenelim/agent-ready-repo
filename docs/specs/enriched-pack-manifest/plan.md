# Plan: enriched-pack-manifest

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->
  <!-- All tasks shipped: manifest layer (T1–T8, T11, manifest part of T9) in
  #300; guide-migration layer (T12, T13, T10) plus net-new per-pack guides in
  the per-pack-guide-migration PR. T13's §5c amendment landed as an ADR-0020
  erratum (the projected seed forces §5c to stay by-quadrant). -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three layers, in order: **schema** (declare the fields), **projection** (carry the subset + READMEs into the dist routes), **population** (fill all 12 shipped packs, including `product-engineering`, RFC-0030, now on `main`). The schema work (T1) and the two contract-surface changes (T2 contract bump, T3 relax the plugin-manifest schemas) are independent and parallelizable; the projector (T4), README wiring (T5), categories warn (T6), and `@catalogue/pack` rendering (T7) each depend only on the schema; population (T8) depends on the projection + categories being in place so every pack validates and projects cleanly; the per-pack `docs/guides/` migration (T12) and its convention/skill adaptation (T13) precede the `documentation`-link wiring (T10); docs (T9) closes. The riskiest part is **not** the additive schema — it's the **contract bump's blast radius** (version-pinned assertions across CI-ungated test roots) and keeping **legacy projected output byte-identical** so the change is provably additive. Every field is optional and the projector emits new keys only when present, which is what makes legacy invariance testable.

## Constraints

- **RFC-0031** — the eight accepted decisions; this spec implements the "first spec" row of its Decision 6 roadmap.
- **RFC-0001** — contracts live in `docs/contracts/`; do not relocate.
- **RFC-0011** — new `pack.toml` fields are optional and gated by a contract bump; legacy packs need no migration (the precedent followed by T1+T2).
- **ADR-0021** — `pack.toml` is the metadata source of truth, projected lossily per tool; `@catalogue/pack` identity (declare-only here). The decision record for RFC-0031 D2/D7; T1/T3/T4/T7 implement it.
- **ADR-0020** — the `documentation` link target is the per-pack `docs/guides/<pack>/` home; the guide migration that creates it is **performed by this plan** (T12 migrate + T13 convention/skill) and consumed by T10.
- **RFC-0030** — `product-engineering` landed on `main` (2026-06-13); T8's sweep enriches it as a normal pack.
- **CONVENTIONS.md** — changelog entry for user-visible change; non-cosmetic pack edits bump the pack version.

## Construction tests

Per-task `Tests:` below carry the unit/edge coverage. Cross-cutting:

**Integration / invariant tests:**
- **Legacy invariance** — verified at the projector/merge-site level rather than via a committed fixture-golden (as implemented in `build/tests/test_projectable_subset.py`): `derive_projectable_subset` on a manifest with none of the new fields returns `{}`, and `derived.update({})` is asserted byte-identical (`json.dumps(sort_keys=True)` before vs after). Because the projector emits keys *only when present*, an empty subset cannot perturb the projected `plugin.json` / `marketplace.json` entry — which is the additive guarantee, proven without an `origin/main` diff at test time. (Earlier draft proposed a `fixtures/legacy_pack/` golden run twice in-process; the unit-level invariant covers the same property more directly and is what shipped.)
- **Full build-check** — `make build-check` green after projection + population (covers drift gates + self-host projection of `core`/`governance-extras`).

**Manual verification:** none beyond the goal-based gates.

## Design (LLD)

Stack: Python 3.11/3.12, stdlib `tomllib` (parse) + `json` (emit) + `jsonschema` (validate), inside the `agentbundle` build pipeline (`packages/agentbundle/agentbundle/build/`). No `docs/architecture/reference.md` governs the build pipeline; stack derived from the module the feature touches.

### Design decisions
- **Optional-everywhere + emit-only-when-present.** The only design that makes legacy invariance provable; rejected "require fields at 0.14" because it would force-migrate every shipped pack to satisfy the schema. Traces to: legacy-invariance AC · `pack.schema.json`.
- **`[pack.metadata.<tool>]` is opaque passthrough.** Schema accepts an arbitrary sub-table, validated only as "object"; the projector reads only the namespaces it knows. Traces to: field-set AC · `pack.schema.json`.
- **Soft categories via the existing `_drop_warning`-style channel**, not a new error path. Traces to: soft-category AC · `commands/validate.py`.
- **`@catalogue/pack` is a rendering concern only** — a display helper in `list-packs`, zero change to `catalogue.py` resolution. Traces to: identity AC · `commands/list_packs.py`.

### Data & schema
- `pack.toml [pack]` gains optional `readme`, `display_name`, `license`, `categories`, `keywords`, `[pack].catalogue` (nested, like every other new field); `[[pack.maintainers]]` (`{name, email?, url?}`); `[pack.links]` (`homepage`/`repository`/`documentation`/`changelog`/`issues`/`icon`); `[pack.metadata.<tool>]` (opaque). `categories`/`keywords` capped at 5. Traces to: field-set + catalogue ACs · `pack.schema.json`.
- The projectable **subset** (`author`←maintainers[0], `license`, `homepage`/`repository`←links, `keywords`, `category`←categories[0], `displayName`←display_name) is added to `plugin-manifest.schema.json` + `plugin-manifest.derived.schema.json`. Traces to: schema-relax + projection ACs.

### Interfaces & contracts
- Contracts touched: `pack.schema.json` (author surface), `adapter.toml` (0.13→0.14), both `plugin-manifest*.schema.json` (projected surface). All four under `docs/contracts/`. Traces to: every schema AC.

### Dependencies & integration
- README projection integrates with `self_host.py`'s projected-README handling (`PROJECTED_README_OVERRIDES` / exclude patterns, ~lines 295–398) and the per-pack dist routes (`dist/claude-plugins/<pack>/`, `dist/apm/<pack>/`). The marketplace aggregation is `_aggregate_marketplace` (`self_host.py:499`). No new external dependency. Traces to: README + projection ACs.

## Tasks

### T1: `pack.schema.json` accepts the enriched optional fields

**Depends on:** none
**Touches:** `docs/contracts/pack.schema.json`, `packages/agentbundle/tests/integration/test_install_pack_metadata_shape.py`

**Tests:** (TDD)
- A manifest with all new fields (`readme`, `display_name`, `license`, `[[pack.maintainers]]`, `[pack.links].*`, `categories`, `keywords`, `[pack].catalogue`, `[pack.metadata.foo]`) validates.
- A manifest with **none** of them validates (optionality).
- `categories`/`keywords` with >5 items fails; a `maintainers` entry missing `name` fails; wrong types fail.
- `[pack.metadata.anything]` passes as an opaque object.

**Approach:**
- Add the field definitions under `[pack].properties`; keep `[pack]` free of `additionalProperties:false` (it already is) so unknown future keys don't break; constrain `categories`/`keywords` with `maxItems: 5`.
- Add `maintainers` array-of-object (`name` required), `links` object (string URLs), `metadata` object (no inner constraint).

**Done when:** the new schema-shape tests pass and existing `validate`/`lint-packs` stay green on current packs.

### T2: adapter-contract bump `0.13 → 0.14`

**Depends on:** none
**Touches:** `docs/contracts/adapter.toml`, `packages/agentbundle/agentbundle/_data/adapter.toml`, `packages/agentbundle/agentbundle/build/tests/test_contract.py`, `build/tests/test_adapter_kiro_ide.py`, `build/tests/test_adapter_gemini.py`, `build/tests/test_adapter_cursor.py`, `packages/agentbundle/tests/unit/test_contract_v0_3_schema.py` (the 7 files grep `0.13` finds)

**Tests:** (goal-based)
- `agentbundle --version` reports the bumped spec version.
- **Full `agentbundle` package pytest green** (`python -m pytest packages/agentbundle`), confirming every version-pinned assertion updated.

**Approach:**
- Bump `version` in `adapter.toml` and its `_data` mirror (keep byte-parity).
- Grep `0.13` across `packages/agentbundle/` + `docs/contracts/` (~7 files) and update each pinned assertion; assess whether `pack.schema.json`'s version-gate `if` enum needs `0.14` (it currently lists `["0.2","0.3","0.6"]` for *requiring* `install` — likely untouched, but confirm).
- Watch the lexical-version-compare trap (`scope.py` tuple compare already handles it; verify no string-compare assertion regressed).

**Done when:** full package pytest is green and `--version` shows `0.14`.

### T3: Relax `additionalProperties:false` on both plugin-manifest schemas

**Depends on:** none
**Touches:** `docs/contracts/plugin-manifest.schema.json`, `docs/contracts/plugin-manifest.derived.schema.json`, `packages/agentbundle/agentbundle/build/tests/test_plugin_manifest_schema.py`

**Tests:** (TDD)
- A plugin manifest carrying `author`/`license`/`homepage`/`repository`/`keywords`/`category`/`displayName` validates against **both** schemas.
- A manifest carrying a genuinely unknown key still fails (we admit a *named* subset, not arbitrary keys — keep `additionalProperties:false` but enumerate the new properties).

**Approach:**
- Add the projectable-subset properties to both schemas' `properties` (keep `additionalProperties:false`, just widen the allow-list — safer than removing the gate).
- Mirror to `_data/` copies if a build-bundled copy exists; run the drift gate.

**Done when:** `make build-check` green and the schema tests pass.

### T4: Derive the projectable subset into `plugin.json` / `marketplace.json`

**Depends on:** T1, T3
**Touches:** `packages/agentbundle/agentbundle/build/self_host.py` (`_aggregate_marketplace`, plugin.json derivation), `build/main.py`

**Tests:** (TDD)
- Given a `pack.toml` with the enriched fields, the derived `plugin.json` entry carries the mapped subset (`author`←`maintainers[0]`, `license`, `homepage`/`repository`←`links`, `keywords`, `category`←`categories[0]`, `displayName`←`display_name`).
- A `pack.toml` without them yields an entry with **no** new keys (emit-only-when-present).
- The derived output validates against `plugin-manifest.derived.schema.json`.

**Approach:**
- Add a pure mapping helper `pack.toml dict → projectable subset dict`; call it where the derived `plugin.json` is built and in `_aggregate_marketplace`.
- Preserve key ordering / `sort_keys` to keep diffs deterministic.

**Done when:** projector tests pass, derived output is schema-valid, and the legacy-invariance integration test is byte-identical for a no-fields pack.

### T5: Project each pack's `README.md` into the dist routes + `readme` reference

**Depends on:** T1
**Touches:** `packages/agentbundle/agentbundle/build/self_host.py` (README projection / `PROJECTED_README_OVERRIDES`), per-pack dist routes

**Tests:** (goal-based)
- After build, `dist/claude-plugins/<pack>/README.md` and `dist/apm/<pack>/README.md` exist for a pack that ships one.
- The derived manifest's `readme` field references the projected path; a pack with no `README.md` projects no `readme` key and does not error.

**Approach:**
- Copy `packs/<pack>/README.md` into each route's pack dir during projection; set `readme` from the `pack.toml` pointer (default-detect `README.md` when the field is omitted, per the Cargo model).
- Integrate with the existing projected-README allow-list rather than fighting the exclude patterns.

**Done when:** the projected READMEs appear in both routes and `make build-check` (incl. drift gates) is green.

### T6: Soft `categories` vocabulary + warn-not-error validation

**Depends on:** T1
**Touches:** `packages/agentbundle/agentbundle/commands/validate.py`, a default-vocabulary constant (new small module under `agentbundle/`), a standalone validate test

**Tests:** (TDD)
- A known slug → no warning, exit 0.
- An unknown slug → a warning on stderr, **exit 0**.
- The default vocabulary contains the 16 RFC-0031 slugs.

**Approach:**
- Define the default slug list as a module constant; in `validate`, compare declared `categories` against it and emit via the existing warn channel (`_drop_warning`-style), never raising.

**Done when:** the three validate tests pass; `validate` exit code stays 0 for unknown slugs.

### T7: `@catalogue/pack` canonical rendering in `list-packs` (declare-only)

**Depends on:** T1
**Touches:** `packages/agentbundle/agentbundle/commands/list_packs.py`

**Tests:** (TDD)
- A pack with `catalogue = "acme"` renders identity `@acme/<name>`; a pack without renders the bare `<name>`.
- No call into `catalogue.py` resolution is added (assert the resolver path is unchanged — e.g. the test exercises rendering only).

**Approach:**
- Add a small identity-rendering helper in `list_packs.py`; read the optional `[pack].catalogue` from the parsed `pack.toml`; use it only for display.

**Done when:** the rendering tests pass and `list-packs` output shows scoped/bare identities correctly with no resolution change.

### T8: Populate every shipped pack + bump each pack version

**Depends on:** T1, T4, T5, T6
**Touches:** `packs/*/pack.toml` (all 12 shipped packs, including `product-engineering`), and any hand-authored `packs/*/.claude-plugin/plugin.json` left in place

**Tests:** (goal-based)
- `agentbundle validate <pack>` exits 0 for each shipped pack.
- `make build-check` green (covers self-host reprojection of `core` + `governance-extras`).
- Each of the 12 packs' `[pack].version` **differs from its value at the branch merge-base** (diff each `pack.toml` version against `git show $(git merge-base origin/main HEAD):packs/<pack>/pack.toml` — merge-base, not live `origin/main`, so a later rebase past another pack-version bump doesn't false-pass/false-fail) — proves the bump actually happened per pack, not just "is present".

**Approach:**
- For each pack add `readme`, `license` (SPDX), `[pack.links].repository`, `categories` (from the default vocab), `keywords`, and `[[pack.maintainers]]` where known (the `documentation` link + README link-out are T10's job, since they depend on the docs-reorg); pick categories matching each pack's purpose (e.g. `core`→`governance`/`testing`; `research`→`research`; `contracts`→`api-design`; `converters`→`file-conversion`; `credential-brokers`→`credentials`; `monorepo-extras`→`devops`).
- **Version-bump rule:** a **patch** bump for these metadata-only additions (e.g. `0.4.0 → 0.4.1`); a pack opts its `pack.adapter-contract.version` to `0.14` only if it actually uses a `0.14`-gated behavior (none required here, since all new fields are optional).
- Re-run `make build-self` so `core`/`governance-extras` projections refresh; check `git status` for unexpected projection-only reverts (the known build-self drift trap).

**Done when:** all 12 packs validate clean, each version differs from the merge-base, build-check green.

### T12: Migrate `docs/guides/` to the per-pack Diátaxis layout (ADR-0020)

**Depends on:** none
**Touches:** `docs/guides/<quadrant>/*` → `docs/guides/<pack>/<quadrant>/*` (the ~30 existing guides, incl. the `product-engineering` guides main just added), `docs/guides/_shared/<quadrant>/*` (cross-cutting), `docs/guides/README.md` + per-quadrant `README.md`s

**Tests:** (goal-based)
- Every existing guide lands under either `docs/guides/<pack>/<quadrant>/` (pack-specific) or `docs/guides/_shared/<quadrant>/` (cross-cutting) — no doc left at the old `docs/guides/<quadrant>/` top level.
- All internal cross-links between guides still resolve (link-check); `make build-check` doc-drift gates green.

**Approach:**
- Classify each of the ~30 guides: pack-specific (e.g. `core-pack.md`→`core/`, `research-methodology.md`→`research/`, the intent guides→`product-engineering/`) vs cross-cutting repo-workflow (`new-rfc`, `new-adr`, `author-a-skill`→`_shared/`).
- Move files with `git mv` so they render as **renames** (cheap to review); isolate the cross-link rewrites + README refreshes into a separate commit. Land into `docs/guides/<pack>/{tutorials,how-to,reference,explanation}/`; preserve the four-type discipline *within* each pack.
- **PR-sizing:** the guides migration (T12 + T13 + T10) is separable from the manifest work (ADR-0020 vs ADR-0021) — if the combined diff exceeds the split threshold, land it as its own PR stacked on the manifest PR.

**Done when:** all guides relocated, links resolve, build-check green.

### T13: Adapt `CONVENTIONS.md §5c` + the `new-guide` skill to the per-pack layout

**Depends on:** T12 (co-lands so the Living `CONVENTIONS.md` matches the moved reality)
**Touches:** `docs/CONVENTIONS.md` §5c, `.claude/skills/new-guide/SKILL.md` (+ its assets/templates and the `docs/guides/<quadrant>/<slug>` write-path references), the Source-of-truth table row in `AGENTS.md`/`CLAUDE.md` if it pins the guides path

**Tests:** (goal-based)
- `CONVENTIONS.md §5c` describes the per-pack hierarchy (pack-at-top, four types within, `_shared/` for cross-cutting; adopter seed scaffold stays type-at-top); `conventions-check` / lint green.
- The `new-guide` skill's documented write path is `docs/guides/<pack>/<quadrant>/<slug>.md`; a dry-run/inspection confirms it (no doc written).

**Approach:**
- Amend §5c prose; update the `new-guide` SKILL.md write-path + quadrant logic; update the Source-of-truth table reference. Per ADR-0020, the adopter-facing `user-guide-diataxis` seed scaffold is **unchanged** (stays type-at-top).

**Done when:** §5c + `new-guide` reflect the per-pack layout and the convention lints clean.

### T10: Wire `documentation` links + README link-out to each pack's guide home

**Depends on:** T1, T5, T12
**Touches:** `packs/*/pack.toml` (`[pack.links].documentation`), `packs/*/README.md` (the link-out line)

**Tests:** (goal-based)
- Each pack's `[pack.links].documentation` resolves to an existing `docs/guides/<pack>/` home (absolute repo URL on `main`).
- Each pack's projected README contains a "go deeper →" link-out to that home.

**Approach:**
- Set `documentation` to the absolute repo URL of `docs/guides/<pack>/` (created by T12); add the link-out line to each README.

**Done when:** every shipped pack's `documentation` link + README link-out resolves to its per-pack guide home.

### T11: Refresh the PyPI-facing wheel READMEs

**Depends on:** T1, T3, T4
**Touches:** `packages/agentbundle/README.md`, `packages/credbroker/README.md`

**Tests:** (goal-based)
- `packages/agentbundle/README.md` accurately describes rich `pack.toml` metadata + lossy marketplace projection (the `long_description` rendered on PyPI); no claim contradicts the shipped behavior.
- Both wheels still build with a valid `long_description` (`python -m build` for each package, or the existing packaging check).

**Approach:**
- Update `agentbundle`'s README (the "npm for your coding agent" pitch) to surface the enriched manifest + projection.
- Review `credbroker`'s README; update only if the design touches it (credbroker is the credential library — likely a light cross-reference at most). If unchanged, note why in the PR.

**Done when:** the agentbundle README reflects the design, credbroker is reviewed (updated or noted-unchanged), and both packages build.

### T9: Docs — changelog + architecture entry

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T10, T11, T12, T13
**Touches:** `docs/product/changelog.md`, `docs/architecture/pack-layout.md`, `docs/architecture/pack-manifest.md` (new), `docs/architecture/overview.md`

**Tests:** (goal-based)
- `docs/product/changelog.md` has an `[Unreleased]` entry describing the enriched manifest + contract bump.
- `pack-layout.md`'s `[pack]` field list and contract-version mention reflect the new fields and `0.14`.
- New `docs/architecture/pack-manifest.md` exists and is linked from `overview.md`; doc-drift gates green.
- `overview.md` § The catalogue states the correct pack count (12) and lists all packs.

**Approach:**
- Add the changelog entry; update the `pack-layout.md` `### pack.toml` field list and the "contract vX today" line.
- Author `docs/architecture/pack-manifest.md` describing `pack.toml` as the source of truth, the projectable-subset mapping, and the lossy per-tool projection model; link it from `overview.md` (§ The catalogue).
- **Bundled fix:** while editing § The catalogue, correct its stale count ("eight reference packs") and pack table to the shipped 12 (same-area ride-along; note in the PR's deferred/bundled-fixes line).

**Done when:** all docs updated, `pack-manifest.md` linked, count corrected, and `make build-check` (incl. doc-drift gates) is green.

## Rollout

Pure catalogue/build change — no infra, no external systems, no runtime flag. **Delivery:** one PR; reversible (additive schema + optional fields; revert restores prior projections). **Deployment sequencing:** schema (T1) and contract bump (T2) before population (T8); projection (T4/T5) before population so the populated packs project cleanly; docs (T9) last. No published-event or data-migration irreversibility.

## Risks

- **Contract-bump blast radius** — the `0.13→0.14` bump trips version-pinned assertions in CI-ungated test roots; mitigated by running the full package pytest by hand (T2) rather than relying on `make build-check`.
- **Self-host reprojection drift** — populating `core`/`governance-extras` reprojects under `make build-self`; a projection-only edit could be silently reverted. Mitigated by editing pack sources and re-running build-self in T8, then checking `git status` for unexpected reverts.
- **README projection vs. exclude patterns** — the self-host README allow-list could swallow or duplicate per-pack READMEs; mitigated by integrating with `PROJECTED_README_OVERRIDES` rather than adding a parallel path (T5).
- **Legacy invariance** — if the projector emits empty keys for absent fields, legacy output diffs; mitigated by emit-only-when-present + the byte-identity integration test.

## Changelog

- 2026-06-13: initial plan (follows RFC-0031 Decision 6 "first spec").
- 2026-06-13: doc-surface added (README link-out, PyPI READMEs, `docs/architecture/pack-manifest.md`); per-pack `docs/guides/` layout decided in ADR-0020 and **migrated in-plan** (T12 migrate + T13 convention/`new-guide` adaptation), consumed by T10; `product-engineering` (RFC-0030, landed) folded into the 12-pack population sweep.
- 2026-06-13: **guide-migration layer scope expanded by user direction.** The earlier "Ask first → don't author substantial net-new guide content per pack" boundary is **lifted for this layer**: T12 now (a) migrates the ~38 existing guides, (b) authors net-new good-enough Diátaxis guides for the 7 previously-undocumented packs and fills clear gaps in `architect`, (c) gives every pack a `README.md` home, and (d) sweeps every repo-wide cross-link to a moved guide. Voice = adopter-facing developer-evangelist (matches the repo `README.md`). **Classification correction:** `new-rfc`/`new-adr` (+ a new `update-conventions` how-to) land under `governance-extras/` — the pack that *ships* those skills — not `_shared/` (an earlier illustrative example); `_shared/` holds only guides that document no single pack (install routes, adapter-support, `agentbundle` CLI, pack-catalogue, upgrade, file-safety, `author-a-skill`). The four per-quadrant writing-rule READMEs move to `_shared/<quadrant>/README.md` and the `new-guide` skill is repointed there.
- 2026-06-13: **manifest layer implemented** (T1–T8, T11, manifest portion of T9) and split from the guide-migration layer (T12/T13/T10) per the PR-sizing note — guide migration is a follow-on PR stacked on this one (backlog `per-pack-guide-home-documentation-links`). Build learnings: (1) the in-house JSON-Schema validator lacked `maxItems` — added it (the ≤5 cap on categories/keywords needed it). (2) `_aggregate_marketplace` reads the *source* `plugin.json`, so the subset is merged at aggregation time from `pack.toml` (not stored in source `plugin.json`, which stays minimal). (3) `make build-self` regenerates the committed `.claude-plugin/marketplace.json`; it refused a dirty tree, so the `self --force` form regenerated it mid-work. (4) `agentbundle validate product-engineering` had a pre-existing user-scope-seeds rail failure (it shipped `seeds/` while declaring `user` scope, RFC-0004 Rail A); **resolved in this PR** by relocating its intent/rollup templates from `seeds/` into the owning skills' `assets/` (per the AGENTS.local.md skill-template convention) so the pack ships no `seeds/` and validates clean — all 12 packs now pass. The `product-engineering-pack` / `value-stream-meta-repo` specs + plans were updated and RFC-0030 / ADR-0022 carry errata. (5) overview.md ships **no** hardcoded pack count (maintainer direction — brittle), diverging from the AC13 count clause. (6) AGENTS.local.md is the canonical source for this repo's skill-template-in-`assets/` convention — read it up front.
