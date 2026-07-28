# Artifact model

## Artifact types

### Pack README — `packs/<pack>/README.md`

The pack's canonical landing and discovery document. Owned by the pack
maintainer. Explains what the pack helps a user accomplish, the first useful
request, major jobs, install and trust information, and links to deeper
documentation. Machine facts (version, scope, dependencies) should be generated
or validated against `pack.toml`.

**Authored by default:** yes, when asked to improve or create a pack README.
**Audience:** external catalogue users installing or evaluating the pack.

### Journey — `packs/<pack>/JOURNEY.md`

The proposed optional canonical first-value journey for a pack. Walks one
complete user flow from first request to final outcome. Each stage has a "you
say / agent does / you get / decision" block.

**Authored by default:** yes, when asked to write or improve a pack journey.
**Audience:** external users following their first complete use of the pack.
**Status:** reserved as the proposed canonical location; do not migrate existing
journey files from other locations in Phase 1.

### Guide — `guides/<pack>/<kind>/<slug>.md`

Catalogue-facing product documentation. Tutorials, how-to guides, reference
pages, and explanation pages intended for users of the catalogue and its packs.
Lives in the top-level `guides/` tree, organized by pack.

**Authored by default:** yes, for all four Diátaxis kinds.
**Audience:** external catalogue users.

### Guide index — `guides/<pack>/README.md`

The landing page for a pack's guide section. Lists available guides organized
by kind. Update only when the new work materially changes what the reader needs
to discover first.

**Authored by default:** conditional — update when a new artifact materially
changes the pack's discovery entry or canonical flow.

### Maintainer DESIGN input — `packs/<pack>/DESIGN.md`

Maintainer-facing design and architecture. May be read to verify facts when
authoring product documentation; do not author it by default as a product-
documentation output.

**Authored by default:** no. Read-only input for fact verification.

---

## Mandatory versus conditional artifacts

| Situation | Mandatory | Conditional |
|---|---|---|
| New pack in catalogue | Pack README | Journey, first guide |
| New user-facing feature | How-to or tutorial (pick by reader posture) | Reference, explanation |
| Breaking behavior change | Update all affected docs | Update journey if flow changes |
| Audit or retrofit request | Findings report (Audit) / restructured pages (Retrofit) | Updated index/landing |

## When to update related entry surfaces

Update a README, index, or journey when **all three** of these are true:
1. The new artifact changes what a reader should discover first.
2. The current entry surface does not name or link the new artifact.
3. Adding the link is not a build-system or renderer concern (do not edit
   generated outputs — link to source).

If only one or two are true, note the potential update as a follow-on in the
report rather than making it part of the current change.
