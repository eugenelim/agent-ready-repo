---
type: build-handoff
slug: team-orientation-build-handoff
status: active
routes_through: intake-intent
gates_passed:
  - approve-journey (2026-09-04)
  - approve-aesthetic-direction (2026-09-04)
updated: 2026-09-04
---

# Build handoff — what to build, and what must not be assumed

No skill owns a build handoff, so this is hand-authored. It is the single document
`intake-intent` should read, and it points at the others rather than repeating
them.

**Nothing here has been implemented.** No file under `web/`, `docs-site/`,
`guides/`, `site.toml`, or `packs/` was changed by the design session. Everything
below is a specification.

## The one-sentence intent

Replace the marketing home page's structure with a two-level operating-model
canvas that makes the team's adoption arc dominant and the work lifecycle nested
inside it, remove all eleven internal gate codes from adopter copy, and give the
documentation surface a job-grouped navigation and a promoted set of ordered
paths — so that a champion can explain the model to an engineer, a platform team,
and a budget holder without improvising.

## Work items, in dependency order

Ordered so nothing waits on something later. Sizes are relative, not estimates.

### Tier 0 — governance, before any code

| # | Item | Why it blocks |
| --- | --- | --- |
| 0.1 | **Amend `docs/specs/guides-sidebar-generation/spec.md`** — add an optional `job` field to each `[[guide_groups]]` entry so pack directories can nest inside a job group. Backward compatible: entries without `job` keep today's behaviour, and the existing "an entry is required for every directory" rule is untouched. | The spec is **Status: Shipped** and its data model has no job tier. Items 3.1 and 3.2 cannot be built without it. This is a contract change, not a data edit. |
| 0.2 | **Confirm ADR-0020's scope** — it mandates the per-pack Diátaxis hierarchy *within* an area. Job-grouping areas above themselves appears not to engage it, but that reading needs the ADR owner, not a designer. | If it does engage, 3.1 needs a different shape. |
| 0.3 | **Correct the same spec's stale premise** while it is open — it justifies a directory-fallback relaxation with "162 files carry none, 157 of them nav-eligible". Measured today: 5 files carry no `kind:`, and all five are the pages the same spec defines as not reader-facing. Zero nav-eligible files now fall through. | Cheap to fix while the spec is being touched; misleading if left. |

### Tier 1 — the canvas and its pipeline

| # | Item | Notes |
| --- | --- | --- |
| 1.1 | **SVG generator** — emit the canvas from the token source rather than hand-maintaining literals. | The canvas's binding rendering is a sanitised README where `var()` cannot resolve, so it needs literal values. A hand-authored snapshot silently diverges from the palette and **nothing fails**. See the token verification's finding 1. |
| 1.2 | **Raster export** — 1200×630 PNG under ~300 KB from the same source. | SVG is not a valid link-preview image on any platform. The SVG's aspect is already exactly 1200×630, so this is a direct render with no reframing. |
| 1.3 | **Marketing-palette contrast check** — extend or mirror `tools/check-docs-contrast.py` to the `--ds-*` palette, including the canvas's text-on-ground and meaningful-graphic pairs. | Pre-existing gap: only the docs palette is checked. The design pass found **three non-text contrast failures** in the canvas's first draft by hand. Owner approved this as in scope. |
| 1.4 | **Build the canvas** from `docs/design/screens/team-orientation/operating-model-canvas.svg` as the reference composition, plus its brief and composition record. | The SVG is a **reference, not the asset** — 1.1 produces the asset. |

### Tier 2 — the marketing surface

| # | Item | Source of truth |
| --- | --- | --- |
| 2.1 | Restructure `web/src/pages/index.astro` to the eleven-zone order | `team-orientation-ia.md` § Scroll order |
| 2.2 | New above-the-fold zone: canvas, six-element contract, one action | `team-orientation-marketing-structure.md` |
| 2.3 | **Remove all six gate codes from `HumanGates.astro`** and substitute the decision phrasing | `copy-deck.md` § The eleven gate codes, replaced |
| 2.4 | **Remove all five gate codes from `ThreeLoops.astro`**; the zone is absorbed into zone 5 | same |
| 2.5 | Re-task `StatStrip.astro` as the three checkable proofs, keeping its band position | `team-orientation-marketing-structure.md` § The three checkable proofs |
| 2.6 | Relocate `TheProblem.astro` above `PackCatalogue.astro` | `team-orientation-ia.md` |
| 2.7 | New zone 4: the five stations and what each asks of a team | **Only station 2 carries durations**, cited to the on-ramp and P3. The other four state a commitment shape — no published cost exists for them and inventing one is barred. |
| 2.8 | New zone 10: the route into the ordered paths — the seam fix | `team-orientation-seam.md` Crossing A |
| 2.9 | New page: the internal-case route (S6) — the Crossing B fix | `screens/team-orientation/internal-case-route.md` |
| 2.10 | Link-preview metadata for the canvas and S6 | `copy-deck.md` § link-preview strings |

**Do not touch** `AdapterMatrix.astro`, `InstallTerminal.astro`, or
`BuildYourOrg.astro`. The adapter matrix is the best-built element on the page and
the design review recorded five working controls that must not regress — most
importantly the reduced-motion guard, the accent-on-dark contrast discipline, and
the two documented scoped focus-ring overrides. **Leave the focus-ring overrides
alone**; an early count in this engagement misread them as a defect and they are
not one.

### Tier 3 — the documentation surface

| # | Item | Source of truth |
| --- | --- | --- |
| 3.1 | Re-group `site.toml [[guide_groups]]` into the seven existing job names plus a start-here group | `team-orientation-ia.md` § Navigation tree, with the 21-row nav-label migration table |
| 3.2 | Update `generate_sidebar_config` to emit job groups containing pack groups | requires 0.1 |
| 3.3 | Restructure `guides/README.md`: start-here promise first, then the six paths, then search, then the four accomplishment-named type entry points | `team-orientation-docs-structure.md` § Landing page |
| 3.4 | Split the P1 on-ramp out as a ≤20-minute first-value path | same § TTFV. **No new content** — a boundary through existing steps. |
| 3.5 | Raise search to a first-class element of the index, with a real example query | placeholder queries **must be verified against the live index** |
| 3.6 | Per-path page pattern, six instances, including the partial state | `screens/team-orientation/path-page.md` |
| 3.7 | Search results carry their containing job group and path | `screens/team-orientation/search-results.md` — this closes the arrived-from-search-with-no-context edge |

**Never edit `docs-site/src/content/docs/guides/`** — it is a build projection of
`guides/`. **Never edit `docs-site/src/sidebar-config.json`** — it is generated by
`tools/build-site.py` and gitignored. Both traps are recorded because the design
packet itself fell into the second one before cold review caught it.

**Verify after 3.1 and 3.2:** the 17 frozen `(slug, label)` pairs in
`guide-nav-baseline.toml` must all survive generation. They pin *pages*, not
groups, so they should — but that is a check, not an assumption.

## Verification owed before this ships

Five things the design asserts and could not prove.

| # | Claim | How to prove it |
| --- | --- | --- |
| V1 | The canvas survives GitHub's Markdown sanitiser | Render a probe SVG in a real README and inspect the result. Read from documentation, never tested. |
| V2 | Re-grouping changes no URL | Diff the generated sidebar's slugs before and after. Note that a page's `slug:` frontmatter overrides the derived path — `guides/atlassian/review-your-team-backlog.md` is a live example. |
| V3 | The three search placeholder queries return results | Query the live index. An example that returns nothing is worse than a generic placeholder. |
| V4 | The three proofs can be generated, not pasted | Name the regenerator for each. If any cannot be shown, the band **names the evidence boundary** rather than substituting an example. |
| V5 | "Read time · 4 minutes" is true | Measure it or cut it. An unverifiable number violates the fourth copy goal. |

## Pinned constraints — the things that will get lost if not restated

1. **Interaction adds emphasis, never information.** The canvas's binding
   rendering has no script and no stylesheet. If deleting a behaviour loses
   meaning, it is out of contract.
2. **Zero gate codes in adopter copy on the marketing surface.** Eleven render
   there today; the acceptance check is a count, not a review opinion. **Scoped
   to marketing:** the documentation surface publishes 94 occurrences across 14
   files in `guides/`, out of scope here and recorded in the discovery brief.
3. **The two lifecycles must not merge.** Zones 4 and 5 stay separate; the
   canvas's text alternative keeps the work steps as a *nested* list. A flat list
   of thirteen items is the failure in text form.
4. **Amend the token set; never re-establish it.** 97 semantic tokens over 50
   primitives, three tiers, component CSS references semantic only. **Zero new
   semantic tokens are needed.**
5. **The two renderers stay separate.** No shared CSS, component, palette,
   breakpoint, focus implementation, or navigation pattern between `web/` and
   `docs-site/`. The fourth principle requires it.
6. **The documentation surface acquires no persuasion register.** The
   internal-case route is a destination it points at, not an argument it makes.
7. **The aesthetic amendment is the operative document**, not the frozen original.
   Cite `docs/design/direction/tech-site-amendment.md` alongside
   `docs/specs/platform-site/aesthetic-direction.md` — the owner chose Route 1, so
   the frozen file carries no pointer to the amendment.

## Known pre-existing reds, so a red gate is not misread

`make build-check` has three reds unrelated to any `docs/design/` change: an
`audit-npm` registry transport error returning an empty payload; a
`semgrep --strict` timeout whose file set varies between runs; and two permanent
`catalogue self-host --check` drifts on `.claude/agents/*.md` that
`catalogue-verify` rejects as CAT-V-011 and which must stay at HEAD state.

Any change under `packages/agentbundle/**` needs an `Engine-Change-RFC:` commit
trailer, and that path-gate **silently skips locally** without a resolvable diff
base — a green local run proves nothing there. None of the work above touches
that path, but 0.1 through 0.3 touch `docs/specs/` and `tools/`.

## Out of scope, recorded so it is not silently absorbed

- **`README.md` itself.** It is the highest-traffic surface — 68 unique readers
  against the site's 6 outbound referrals — and the canvas will render there, but
  restructuring it is separate work.
- **Nine generated content files carrying 12 gate-code occurrences** under
  `web/src/content/`. Same violation, fixable only at `packs/*/JOURNEY.md`.
- **The pack catalogue, journey pages, and `/now/`.** Each needs its own review
  pass.
- **Writing tutorials for the ten guide areas that have none.** A content
  programme. The six ordered paths are the design's answer to the missing
  first-value layer.
- **`agent-skill-engineering` is named in the job taxonomy with no guide
  directory.** Taxonomy drift; the owner of the taxonomy decides.
- **Moving the job taxonomy into `site.toml`.** Recommended in the IA, since it
  currently lives in a marketing-only TypeScript module and a Markdown table
  whose pack membership has already drifted in three of seven rows. A good change
  and a separate one.

## Open questions the build cannot resolve

1. **Who writes the marketing headline?** It has a full contract — ≤10 words,
   the team's situation before the mechanism, judged against *Sayable in a
   meeting* — and no owner in the skill roster. This is Gap J.
2. **Who defines "pack" in plain words, and where?** Unfamiliar
   product-specific vocabulary in navigation on both surfaces; the
   plain-language floor bars it until defined.
3. **The champion interview has not run.** Every stage emotion and pain stays
   assumption-based until it does, and the measurement plan's baseline depends on
   it.

## Reading order for whoever picks this up

1. This document.
2. `docs/design/discovery/team-orientation-decision-log.md` — every decision and
   what decided it, including the corrections this engagement made to itself.
3. `docs/design/screens/team-orientation-flow.md` — six screens, transitions,
   error edges, and the per-screen state matrix.
4. `docs/design/screens/team-orientation/` — the six briefs, the canvas
   composition record, and the reference SVG.
5. `docs/design/discovery/team-orientation-ia.md` and the two structure
   documents for the surface-level decisions.
6. `docs/design/copy/copy-deck.md` for every string.
7. `docs/design/discovery/team-orientation-measurement-plan.md` for how we will
   know whether it worked — and its twelve kill conditions for how we would know
   it did not.
