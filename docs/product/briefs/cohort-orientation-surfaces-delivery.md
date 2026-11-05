# Brief: an adoption champion can explain the operating model from one published artifact

- **Slug:** `cohort-orientation-surfaces-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/cohort-orientation-surfaces.md`](../intents/cohort-orientation-surfaces.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** intent:cohort-orientation-surfaces

## Outcome

One token-backed operating-model canvas is published on the marketing site and the README, the documentation hub groups guides by job, and the hub and marketing home route to each other, without translating internal gate codes. The documentation hub also carries prominent search over a static build-time index (owner decision, 2026-11-05).

## Success metrics

- One generator produces every canvas rendering from the paper-first tokens, and a test reproduces the output byte for byte.
- The README embed passes an exact-markup test and has a full text alternative.
- Canvas text pairs meet 4.5:1 and non-text pairs meet 3:1 (WCAG 1.4.11), the floors `docs/design/direction/marketing-site.md` applies in its section "The press state is a ground shift", checked by script.

## Scope / Non-goals

**In scope:**

- Carrier decision (recommended: one paper-first SVG, no dark variant) and the generator.
- Marketing route and README embed.
- Documentation search over a static build-time index.
- Job membership authority and generated hub groups.
- Hub-to-artifact and home-to-journeys routes.

**Non-goals:**

- Raster and unfurl export of the canvas (deferred; see the follow-ups below).
- Marketing home structure and copy, which shipped.
- Gatekeeper evidence (TCO, SOC 2, SBOM and similar).
- README restructuring, the pack catalogue and `/now/`.
- Terminal and Claude-app first-value doors.

## Proposed slices

Every slice is checked by an agent with no live service or credential. Two owner approvals are named steps in the Gating cells: the drafted headline (C1) and the plain sentence for "pack" (C2).

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| C1 | Carrier decision (one paper-first SVG, no dark variant), token-backed generator, generated canvas on the marketing route and in the README with a text alternative. The asset ships with its visible surfaces. | Generator reproducible in a test; contrast script passes; `web` build and rendered-output test; exact sanitised-markup regression test | none | Owner approves the drafted headline before ship (named step) | 
| C2 | The guide hub role table is the one authority for job membership; amend `guides-sidebar-generation` to add a `job` field; project the sidebar groups and `web/src/lib/catalogue-navigation.ts` from it; add the plain "pack" sentence to the hub. | Generation test; guide-index check; a test that the generated slugs match the committed slugs; the hub's measured read time within 3 minutes at 238 words per minute (about 710 words) from the top to the first job link (Decisions) | none | Owner approves the wording of the "pack" sentence before ship (named step) |
| C3 | Cross-surface routes: hub to artifact, home to journeys index. | `web` build and rendered-output test; generated-slug diff; the hub's measured read time within 3 minutes at 238 words per minute (about 710 words) from the top to the first job link (Decisions) | C1, C2 | none; C3 is the single `site.toml` header editor (Decisions) |
| C4 | Prominent documentation search with a real example query. | Build-time index produced by the site build; a test finds the example query | C2 | none; mechanism is a static build-time index, no hosted service |

### Manual or live residue, split off as non-blocking follow-ups

- Live documentation-index query (needs a network): non-blocking, owner eugenelim.
- Visual review of the canvas on a real browser and in the GitHub rendering; owner: eugenelim, non-blocking.
- Raster and unfurl export: deferred, owner eugenelim, built from the same generator source when a rasteriser dependency is recorded.
- Parent acceptance check that influencer-tier readers recover all five relationships: a reader test with real readers cannot be run by an agent; owner eugenelim runs it after C1 ships. Agent-side proxy: the rendered-output test asserts the five relationships appear in the text alternative.

## Decisions

- Decided 2026-11-05 by eugenelim: C3 is the single editor of the `site.toml` header during this brief, limited to adding the journeys link; `catalogue-wave7-marketing-evaluator` rebases onto it.
- Decided 2026-11-05 by eugenelim: the hub read-time bound is at most 3 minutes at 238 words per minute (about 710 words) from the top to the first job link; C2 and C3 fail above it.
Decided 2026-11-05 by eugenelim:

- The guide hub table (the `guides/README.md` role table) owns job membership; ADR-0020 governs structure within a pack's guide area, not this grouping.
- An agent drafts the marketing headline; the owner approves it before ship.
- Parent question 4: the generated-slug diff and the measured read time are scripted and gate C2 and C3. The live-index query needs a network and is the non-blocking follow-up.
- Parent question 5: C2 adds one plain sentence ("a pack is one installable bundle of skills for a single job") to the guide hub. The owner approves the wording before ship, with the headline.
- Parent question 6: ADR-0020 does not engage the job grouping, which sits above areas, so C2 proceeds.
- Parent question 7: no new `hub` kind; the 21 area index pages keep their declared kinds and the job grouping reads the `job` field.

## Constraints / Appetite

Four sessions; C1 and C2 are parallel once their decisions are made.

## Assumptions / Risks

- Riskiest assumption: the README sanitiser keeps the chosen markup. C1 tests the exact markup.
- Risk: the search index adds a build dependency; record it in the owning package instructions before use.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Parent intent: [`cohort-orientation-surfaces.md`](../intents/cohort-orientation-surfaces.md).
