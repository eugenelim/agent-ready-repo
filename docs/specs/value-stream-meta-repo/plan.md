# Plan: value-stream-meta-repo (product-engineering phase 2)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. When it changes
> substantially, note why in the changelog at the bottom.

## Approach

A pure-markdown extension of the existing `product-engineering` pack — no code,
no infra. Add the business-unit cross-component layer: one **new skill**
(`align-value-stream`, which owns the meta-repo's shared artifacts), a
**business-unit branch** on the existing `decompose-intent` skill (per-component
slicing that feeds and is fed by `align-value-stream`), one **markdown rollup
seed**, one **additive optional field** on `core`'s brief (`parent-intent:`), and
**guide/changelog/version** housekeeping. `frame-intent`/`de-risk-intent` are
unchanged — Scale is resolved once at intake and carries through, and at BU scale
they simply operate at the capability altitude.

The work parallelizes after the seed lands: the new skill (T3), the
`decompose-intent` branch (T4), and the `core` brief field (T5) touch disjoint
files. **The riskiest part is *restraint*** — the cross-component layer is exactly
where the pack would balloon into a runtime hub / live API / validator; the
Boundaries `Never do`, the `<100`-line gate, and the structural grep in T7 are the
guard. The testing story is goal-based (linters + file presence + line counts +
cross-reference greps + a `core`-untouched-beyond-one-field grep) plus manual-QA of
a worked example. `marketplace.json` re-aggregates from the version bump via
`make build-self FORCE=1` (T7); for a user-scope-default pack the only build-self
diff is `marketplace.json`.

## Constraints

- **RFC-0030** (Accepted) — decision #9 + Appendix A (§A.1–A.7) accepted and
  researched this layer; v1 deferred it to phase 2.
- **ADR-0022** — the phase-2 decisions: the meta-repo, per-component slicing with
  `parent-intent:`, referenced-not-forked shared contract, the markdown rollup
  snapshot (no runtime hub), `reference.md` in the meta-repo, unchanged maturity +
  `monorepo-extras` seam.
- **ADR-0019** — corollary 2 (refined 2026-06-13): `parent-intent:` is the one
  additive `core` brief field, deferred from v1 to here.
- **ADR-0008 / RFC-0017 / RFC-0018** — the contract seam is reused at the spec
  stage, not extended here (no contract machinery in this pack).
- **RFC-0016** — the doc-drift discipline the meta-repo's currency relies on.
- **docs/CHARTER.md** — opt-in pack; habits not infra; 3-reviewer ceiling (no new
  subagent); no new top-level directory; no runtime hub / live API.

## Construction tests

**Integration tests:** none beyond per-task tests (no code).
**Manual verification:** walk a worked example end-to-end — a `business-unit`
capability intent → `decompose-intent` slices it into per-component briefs (each
with `parent-intent:` + a version-pinned contract reference + courier snapshot) →
`align-value-stream` catalogs the components, settles the contract-authority home,
and seeds + reads the rollup ("delivered across all components?"). Confirm the
hard limits are stated and no live API / hub appears. Record the walk in the PR.

## Design (LLD)

This is a content/skill pack; there is no code architecture. The only "design" is
the file layout, the rollup seed schema, and the cross-skill handoff.

### Component / module decomposition
*Traces to: AC1, AC2, AC5.* The pack gains one skill dir
`.apm/skills/align-value-stream/` (`SKILL.md` + `references/`) and extends
`.apm/skills/decompose-intent/` (the BU branch in `SKILL.md` +
`references/recursive-decomposition.md`/`tracker-projection.md` un-stubbed). The
two skills cross-reference: `decompose-intent` BU branch → reads catalog/contract
refs from `align-value-stream`, seeds the rollup; `align-value-stream` → names
`decompose-intent` as the slice source. `references/` for `align-value-stream`:
`backstage-ontology.md` (Domain/System/Component/API + federation + a sample
`catalog-info.yaml`), `shared-contract-handoff.md` (reference-by-version, courier
snapshot, provider-contract-first + CDC override, `providesApi`/`consumesApi`,
compatibility direction), `cross-component-rollup.md` (snapshot + pointer, AND
across rows, no hub), `catalog-currency.md` (the RFC-0016 drift discipline; the
`monorepo-extras` seam referenced, not restated).

### Data & schema
*Traces to: AC4.* The rollup template (the `align-value-stream` skill's
`assets/rollup-template.md`; relocated from a `seeds/` seed by
enriched-pack-manifest so the pack stays user-scope)
is a markdown table: columns `Component | Brief (repo + slug) | Contract@version |
Status (snapshot) | Last synced`, placeholder-shaped. `core`'s brief gains one
optional comment-guided field `**Parent intent:**` mirroring the `**Epic:**`
line's shape. No required field anywhere; never a gate.

## Tasks

### T1: Pack version bump + README update

**Depends on:** none
**Touches:** packs/product-engineering/pack.toml, packs/product-engineering/.claude-plugin/plugin.json, packs/product-engineering/README.md

**Tests:**
- Goal-based: `make lint-packs` and `make validate` pass with the bumped pack (AC8).
- Goal-based: `pack.toml` + `plugin.json` read `0.2.0`; the README "What's NOT in
  this pack" no longer lists the BU cross-component layer under "Phase 2" (AC8).

**Approach:**
- Bump `version` to `0.2.0` in `pack.toml` and `.claude-plugin/plugin.json`.
- README: update the skills table (add `align-value-stream`; note the
  `decompose-intent` BU branch), and move the BU cross-component layer out of
  "What's NOT in this pack" into what ships; keep live-API + wire-contract +
  subagents in the "NOT" list. Update the Layout block for the new skill dir.

**Done when:** `lint-packs`, `validate` green; version is `0.2.0`; README reflects
the shipped layer.

### T2: Cross-component rollup seed + lint-seeds registration

> **Superseded 2026-06-13 (enriched-pack-manifest):** the rollup template was
> relocated from this `seeds/` seed into the `align-value-stream` skill's
> `assets/rollup-template.md` and de-registered from `tools/lint-seeds.py`, so
> `product-engineering` ships no `seeds/` and stays user-scope (RFC-0004 Rail A).
> The task below records the original (seed-based) implementation.

**Depends on:** none
**Touches:** packs/product-engineering/seeds/docs/product/rollups/_template.md, tools/lint-seeds.py

**Tests:**
- Goal-based: `tools/lint-seeds.py` passes — the new seed is registered in
  `REQUIRED_PLACEHOLDERS` and is placeholder-shaped (no `RFC-NNNN`, no
  `agent-ready-repo`) (AC4).

**Approach:**
- Author `_template.md`: a markdown table (one row per component slice → its brief
  → status snapshot + pointer), with a header note framing it as a snapshot, not a
  live feed, and pointing each row at the component repo's own auto-derived coverage.
  Document the **absent-source** case: a row whose component repo has no
  `catalog-info.yaml` / no coverage yet shows `unknown / not-yet-catalogued`, never
  silently delivered (so the "AND across rows" answer is never falsely green).
- Register `docs/product/rollups/_template.md` in
  `tools/lint-seeds.py:REQUIRED_PLACEHOLDERS` with its placeholder tuple
  (the lint fails-loud on unregistered seeds).

**Done when:** `lint-seeds` green; the rollup template is present and registered.

### T3: `align-value-stream` skill + references

**Depends on:** T2
**Touches:** packs/product-engineering/.apm/skills/align-value-stream/**

**Tests:**
- Goal-based: `tools/lint-skill-spec.py` passes; `SKILL.md` < 100 lines (AC1).
- Goal-based: a grep confirms `SKILL.md`/anti-patterns name the refusals — runtime
  hub / live API, re-authoring federated data, attach-as-authority (AC1, AC9).
- Goal-based: the four `references/` files exist with the documented depth, incl. the
  `catalog-info.yaml` sample in `backstage-ontology.md`; `SKILL.md` names
  `decompose-intent` as the slice source (the align-value-stream→decompose direction
  of the cross-reference) (AC5, AC6).
- Manual QA: walking the skill stands up a meta-repo (catalog + contract-authority
  elicitation + architecture seam) and seeds/reads a rollup; recorded in the PR (AC1).

**Approach:**
- `SKILL.md` (< 100 lines): when-to-invoke (`business-unit` Scale, a coordinating
  repo with no app code); the five procedure steps (confirm meta-repo + Scale;
  catalog federated; settle contract-authority — explain → default meta-repo →
  alternatives → elicit → reference + courier; anchor architecture `reference.md`;
  keep the rollup current); anti-patterns (no hub/live API; federate don't
  re-author; reference don't fork; don't let the map go stale). Name
  `decompose-intent` as the slice source.
- `references/`: `backstage-ontology.md`, `shared-contract-handoff.md`,
  `cross-component-rollup.md`, `catalog-currency.md` (per Design §module
  decomposition); the `monorepo-extras` seam referenced, not restated.

**Done when:** `lint-skill-spec` green, `< 100` lines, anti-pattern grep clean,
manual-QA walk recorded.

### T4: `decompose-intent` business-unit slicing branch

**Depends on:** T2, T3
**Touches:** packs/product-engineering/.apm/skills/decompose-intent/SKILL.md, packs/product-engineering/.apm/skills/decompose-intent/references/recursive-decomposition.md, packs/product-engineering/.apm/skills/frame-intent/references/scale-intake.md

**Tests:**
- Goal-based: `lint-skill-spec` passes; `SKILL.md` < 100 lines (AC2).
- Goal-based: a grep confirms the BU branch names `align-value-stream` (catalog +
  contract read, rollup seed) — the decompose→align-value-stream direction of the
  cross-reference (AC2, AC6).
- Goal-based (pack-wide de-stub sweep): `grep -rniE "phase.?2|out of scope|deferred"`
  over the pack shows **no** "phase 2 / out of scope / deferred" wording left on the
  **BU path** — specifically the known stale lines in `decompose-intent/SKILL.md`,
  `recursive-decomposition.md`, and `frame-intent/references/scale-intake.md` are
  gone. `tracker-projection.md`'s *live-API* deferral is **excluded** (it is correct
  and stays); the `prototype-approach.md` "detail deferred" line is unrelated (AC2).
- Manual QA: slicing the worked example's feature intent yields one `core` brief
  per component, each with `parent-intent:` + a version-pinned contract reference +
  courier snapshot + a provider/consumer role; app-scale path unchanged (AC2).

**Approach:**
- Extend `SKILL.md`'s procedure: at `business-unit` Scale the feature leaf is
  **sliced per component** (read the affected components + their `providesApi`/
  `consumesApi` edges + the contract references from `align-value-stream`'s
  catalog), emitting one `core` brief per repo, each stamped `parent-intent:`, a
  `contract@version` reference + courier snapshot, and a provider/consumer role;
  seed the rollup rows in the meta-repo. Keep the app-scale branch byte-identical
  in behavior; keep < 100 lines (push slicing depth to the reference).
- **De-stub the now-shipped BU references** (do **not** touch `tracker-projection.md`,
  whose only deferral is the still-correct live-API one): `decompose-intent/SKILL.md`
  (lines that say "business-unit — phase 2, out of scope for v1" / "per repo —
  phase 2"); `references/recursive-decomposition.md` (the "phase 2, out of scope for
  v1" parenthetical — now the shipped BU slice projection with `parent-intent:` +
  contract reference); and `frame-intent/references/scale-intake.md` (the
  "per-component briefs (phase 2)" cell and the "specified but deferred" / "v1 of the
  pack serves the app + single-component path end to end" lines).

**Done when:** `lint-skill-spec` green, `< 100` lines, cross-reference + pack-wide
de-stub greps clean, manual-QA walk recorded.

### T5: `core` brief gains the optional `parent-intent:` field

**Depends on:** none
**Touches:** packs/core/seeds/docs/product/briefs/_template.md, packs/core/.apm/skills/receive-brief/SKILL.md

**Tests:**
- Goal-based: `lint-seeds` + `lint-skill-spec` pass; a grep proves the only
  `packs/core/` diff is the additive `parent-intent:` field + a one-line
  `receive-brief` note, and that no pack file makes `core` import/depend on
  `product-engineering` (AC3).

**Approach:**
- Add an optional `**Parent intent:**` line to the brief template right after
  `**Epic:**`, with a comment distinguishing it (the product-pack intent this slice
  was projected from, at BU scale) from `Epic:` (an external coordinator); keep it
  placeholder-shaped.
- Add one line to `receive-brief`'s Elicit step noting it carries `parent-intent:`
  as an optional upward pointer it never interprets (mirroring the `Epic:` note).
  No behavioral change.

**Done when:** linters green; the `core`-untouched-beyond-one-field grep is clean.

### T6: Diátaxis guides

**Depends on:** T3, T4, T5
**Touches:** docs/guides/how-to/ (new BU how-to page), docs/guides/product-engineering/how-to/shape-a-feature-intent.md, docs/guides/product-engineering/reference/intent-fields-and-modes.md

**Tests:**
- Goal-based: the new phase-2 how-to page exists at its quadrant path; the reference
  guide is updated; a grep confirms the stale "phase 2" / "not yet shipped — see
  RFC-0030 Appendix A" wording is **gone** from **both** the header blurb (line ~7)
  and the footer note (lines ~58-61) of `shape-a-feature-intent.md`, each replaced by
  a pointer to the new page (AC7).
- Manual QA: each reads accurately against the shipped skills (recorded in the PR)
  (AC7).

**Approach:**
- Author a **new** `docs/guides/how-to/` page ("run a capability across a value
  stream / many component repos"): stand up the meta-repo via `align-value-stream`,
  slice via `decompose-intent`, read the rollup; state the hard limits. Land it at
  the current **type-at-top** path (`docs/guides/how-to/<slug>.md`), consistent with
  the sibling product-engineering guides — the per-pack `docs/guides/<pack>/<quadrant>/`
  migration (ADR-0020-on-main) is **deferred to the `enriched-pack-manifest` spec**
  (its T12 sweeps all ~30 guides, including this one); not this spec's job.
- **Update both v1 forward references** in `docs/guides/product-engineering/how-to/shape-a-feature-intent.md`
  — the header blurb ("that path is phase 2") and the footer "Business-unit /
  cross-component (phase 2)" paragraph ("specified but not yet shipped") — to point at
  the new page; remove the stale "phase 2" / "not yet shipped" wording from both.
- Update `docs/guides/product-engineering/reference/intent-fields-and-modes.md` with the BU-scale fields
  (`parent-intent:`, the rollup, the catalog, the contract reference).

**Done when:** the new how-to + the updated forward note + the reference are at their
Diátaxis paths; the stale-wording grep is clean; accuracy review recorded.

### T7: Changelog, spec index, marketplace re-aggregation, full gate sweep

**Depends on:** T1, T2, T3, T4, T5, T6
**Touches:** docs/product/changelog.md, docs/specs/README.md, .claude-plugin/marketplace.json

**Tests:**
- Goal-based: `make lint-packs`, `make validate`, `make build`,
  `tools/lint-seeds.py`, `tools/lint-skill-spec.py`, the package `pytest` suite
  (incl. `packages/agentbundle/agentbundle/build/tests/`), and
  `make build-self FORCE=1` are all green (AC11).
- Goal-based (structural Never): a grep of the pack tree confirms **no `hooks/`,
  no `agents/`, no `*.py` validator/poller**, and that the diff adds **no new
  top-level directory** (AC9).
- Goal-based: `docs/product/changelog.md` carries an `[Unreleased]` entry for the
  phase-2 layer (AC10); `marketplace.json` shows `product-engineering` at `0.2.0`
  (AC8).

**Approach:**
- Add a `docs/product/changelog.md` `[Unreleased]` entry for the BU cross-component
  layer (pack 0.2.0).
- Add a `value-stream-meta-repo` row to `docs/specs/README.md` matching the table's
  column shape — `| [`value-stream-meta-repo/`](...) | Shipped | RFC-0030, ADR-0022,
  ADR-0019 | <synopsis> |`. In the implementing PR flip the metadata to its final
  state — spec `Status: Draft → Shipped`, plan `Status: Drafting → Done`, and all
  spec ACs `[ ] → [x]` (spec + code land atomically, so this is not a forward-claim).
- Run `make build-self FORCE=1` to re-aggregate `marketplace.json` (the only diff
  for a user-scope-default pack). Run the full local gate sweep including the inner
  test root (`cd packages/agentbundle && python -m pytest agentbundle/build/tests/`)
  to catch any count-dependent adapter assertions; fix findings.

**Done when:** all gates green; changelog + spec index updated; `marketplace.json`
at `0.2.0`; structural greps clean.

## Rollout

- **Delivery:** additive, opt-in pack extension. No flag, no migration, fully
  reversible (revert the skill dir, the `decompose-intent` branch, the seed, the
  brief field, the version bump). Nothing irreversible.
- **Infrastructure:** none.
- **External-system integration:** none — the catalog references Backstage entities
  and the rollup references per-repo coverage by pointer; no live API, no hub.
- **Deployment sequencing:** none beyond the task DAG.

## Risks

- **Scope creep into infra** (the dominant risk for *this* layer) — the temptation
  is a runtime hub, a live coverage API, or a YAML-that-needs-a-validator rollup.
  Guarded by Boundaries `Never do` + the structural grep in T7.
- **`SKILL.md` over the line ceiling** — `align-value-stream` covers five concerns;
  mitigated by pushing all depth into `references/` from the first draft (T3).
- **`decompose-intent` over 100 lines** once the BU branch lands — mitigated by
  keeping the slicing depth in `references/recursive-decomposition.md` (T4).
- **Guide drift** — guides authored before skills stabilize go stale; T6 depends on
  T3–T5.
- **`core` over-touched** — the temptation to add more than `parent-intent:`;
  guarded by the T5 grep (one field + one note only).

## Changelog

- 2026-06-13: initial plan. Seed scope settled to the rollup template only; the
  federated `catalog-info.yaml` is a reference sample (Backstage-native, lives at
  component-repo roots, outside the `docs/product/` seed convention), not a
  projected seed. New skill named `align-value-stream` (rollup folded in, not a 5th
  skill) per owner direction.
