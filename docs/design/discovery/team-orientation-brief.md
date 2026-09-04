---
type: discovery-brief
slug: team-orientation
status: active
surface: responsive-web
genres:
  - acquisition
  - documentation
evidence_level: mixed — see "Evidence declaration"
principles: docs/design/principles/tech-site.md
journey_context: docs/product/journeys/team-evaluates-and-adopts.md
updated: 2026-09-04
---

# Discovery brief — cohort orientation to the operating model

No installed skill owns a discovery brief, so this artifact is hand-authored. It
is the contract for the rest of the thread: what the redesign is for, what counts
as success, what evidence it rests on, where our own packs have gaps, and which
decisions are already made.

## The problem

The published surfaces introduce a *tool*. A team adopting this needs to
understand an *operating model*, and the person who has to do that understanding
first is usually a champion who then has to transfer it to engineers, a platform
team, and a budget holder.

The owner's diagnosis: *"it's not obvious from the landing page how everything
maps together on one page… it's bigger than that. it starts from above the fold.
it's the entire lifecycle for adoption rather than the try-one-thing, and this is
how you explain to new cohorts how the whole AI-supervised operating model
works."*

Today the marketing home page hands the reader a pack menu
(`PackCatalogue`), then a problem statement (`TheProblem`), then three loops
(`ThreeLoops`), then seven decision cards (`HumanGates`), and asks them to
assemble the relationships unaided. The relationships are the product.

## Objectives

1. A reader who scans above the fold understands that this is an operating model
   for a team, not an install for an individual.
2. A champion can explain the model to a budget holder from what the page gives
   them, without improvising.
3. Two orthogonal lifecycles — what happens to one piece of work, and what
   happens to a team — coexist on one page without becoming two pages stapled
   together, and without the reader losing which one they are looking at.
4. The documentation surface intercepts a reader who is reaching for executable
   truth, rather than losing them to raw source files.
5. Every meaningful claim on either surface sits beside evidence a skeptical
   engineer can check.

## In scope

- The marketing home page: section order, the above-the-fold decision, and the
  operating-model canvas as its centrepiece.
- The documentation guides index and its information architecture, authored at
  its real source (see "Projection boundary").
- The seam between the two surfaces, in both directions.
- Removal of internal gate codes from adopter copy on both surfaces.
- Amendments to the existing creative direction and design-token set.

## Out of scope

- Implementation. This thread produces specifications and hands off through
  `intake-intent`; nothing reaches the site from the design session.
- `docs/product/journeys/team-evaluates-and-adopts.md` stays where it is and is
  cross-linked, not moved or rewritten.
- The 90-plus existing `--ds-*` tokens and the deliberate separation between the
  two renderers' palettes. Both are amended, never re-established.
- Gate codes in generated pack journey content. Real, recorded below as a
  finding, fixable only at the pack source.

## Success criteria

| Criterion | How it is judged |
| --- | --- |
| Zero internal gate codes in adopter copy | Count of rendered `G0`/`G1.5`/`G2`/`G3`/`G4`/`G5` strings on both surfaces is 0. Baseline is 11 on the marketing home page. |
| Two lifecycles, one page, no ambiguity | A reader can say which lifecycle any element belongs to. Judged by `experience-reviewer` and by the explain-it-back check. |
| Champion can transfer it | Explain-it-back score improves against the pre-redesign baseline captured in the champion interview. |
| Evidence honesty | Every claim either carries a verifiable artifact or is weakened. No invented proof, no assumption presented as grounded. |
| Buildable without another design round | Composition, every label, responsive collapse, all states, and screen-reader equivalence are specified. Judged at `review-experience-designs`. |

## Evidence declaration

The engagement offered three options. **Option 1 plus Option 2** was authorised:
use the real behavioural evidence that exists, and run one champion interview.

| Evidence class | Level | Source |
| --- | --- | --- |
| Arrival, referral, repository-reading behaviour | `observational` | [Traffic evidence review](team-orientation-traffic-evidence.md), 14-day window ending 2026-09-03 |
| The champion's demo experience and transfer mechanism | `observational`, pending | [Champion interview guide](team-orientation-champion-interview.md), one participant, not yet run |
| Stage emotions, pains, and motivations for every other stage | `assumption-based` | Inherited from `team-evaluates-and-adopts.md`, itself `status: planned` |
| Comprehension of the model by any reader | **unmeasured** | No instrument exists. The interview's Part 4 establishes the first baseline. |

**Why this is declared per-class rather than per-map.** The `journey-mapping`
skill requires one `evidence-level` value in frontmatter, chosen from
`observational | survey-backed | assumption-based`. This engagement has three
levels at once. Collapsing them to a single frontmatter value would either
overstate the emotional stages as observed or understate the behavioural data as
assumed. Both are dishonest in the direction that matters.

So each current-state journey map carries the honest floor in frontmatter and a
per-stage evidence tag in the body. That is a deliberate manual override of the
skill's contract, recorded here and as Gap A below.

**What the traffic data changed.** Two findings are load-bearing and were not
visible from the repository alone:

- The README Overview drew 68 unique readers against the published site's 6
  outbound referrals. The marketing page the owner asked us to fix is not where
  most arrivals begin.
- Twelve unique people opened a repository link pasted into Microsoft Teams. The
  measured champion-transfer mechanism is a pasted link, not a site visit. The
  canvas therefore has to survive rendering as a static image inside `README.md`
  on github.com, with no script, no hover, and no external CSS — which is a
  harder constraint than the marketing page imposes and is now a specification
  input.

## Decisions already made

### The adoption lifecycle dominates; work is nested evidence

Rendering the two lifecycles as peer diagrams of equal weight is the stapled-
together failure by construction. One has to dominate.

**Adoption dominates.** The argument, in the order it convinces:

1. The unit of adoption is a cohort, and the dominant reader is a champion. Their
   job is *get my organisation to take this on*, not *get one change through the
   loop*. The first tech-site principle makes the reader's job the opener.
2. The journey's own highest-pain moment is an adoption failure, not a work
   failure. The work lifecycle already functions; the transfer of conviction is
   what breaks.
3. The work lifecycle is the *evidence* that makes the adoption claim credible.
   The second tech-site principle wants evidence placed beside a claim — not
   promoted into a competing narrative.
4. Nesting is the only composition in which the reader cannot lose which
   lifecycle they are in, because one is literally inside the other.

**Composition consequence.** One canvas. The adoption lifecycle is the spine:
evaluate → prove on real work → win buy-in → roll out a cohort → make it the
default. The work lifecycle renders *inside* the second station, at subordinate
visual weight, nested rather than adjacent. The tracker projection hangs off the
work detail as a one-way leaf with no return edge, so *status never comes back*
is readable from the geometry instead of from a caption.

Shaping travels with the person across repositories; build and release belong to
the repository. That boundary is a property of the work detail and is drawn
there, not restated as a separate diagram.

### Both gate-code violations are in scope

The engagement named `ThreeLoops.astro`. The larger violation is
`HumanGates.astro`, which prints `G0`, `G1.5`, `G2`, `G3`, `G4`, and `G5` as the
most prominent element on six of seven cards. Rendered gate codes on the home
page today total **11**: five in `ThreeLoops` and six in `HumanGates`. Both are
removed. The binding constraint decides it, so it was not escalated.

Replacement is human decision phrasing. `HumanGates` already carries usable
phrasing in its `decide` field; the codes are redundant with it.

### Where design artifacts live

`docs/design/` currently holds only `principles/`. The declared convention is
artifact-kind first, then slug, and the declared kinds are spread across
`packages/agentbundle/agentbundle/workspace_mcp.py` and the experience-design
skills:

| Kind | Declared by | Used here for |
| --- | --- | --- |
| `journeys/` | `workspace_mcp.py`, `experience-status` | Current-state maps, future-state map |
| `screens/` | `workspace_mcp.py`, `user-flow` | Screen flow, per-screen briefs, the canvas-as-screen, interaction spec |
| `blueprints/` | `workspace_mcp.py`, `experience-status` | Not used in this engagement |
| `principles/` | existing `tech-site.md`, `design-principles` | Amended only if this work contradicts it |
| `content/` | `content-design`, `copy-direction` | Messaging framework per surface |
| `copy/` | `tone-of-voice`, `copy-direction` | Brand register, marketing copy voice, copy deck |

Two kinds have no declared home, so this engagement adds them and records the
absence as a finding rather than inventing a convention silently:

- `discovery/` — this brief, the content inventory, the traffic review, the
  heuristic baseline, the peer audit, personas, the seam artifact, findings, the
  measurement plan, and the decision log.
- `direction/` — the amended creative direction and the token extension.

### The projection boundary

The documentation guides index is **not** authored where it is served.
`tools/build-site.py` maps `guides/** → docs-site/src/content/docs/guides/**` at
build time. Documentation IA changes are authored in `guides/README.md` and in `site.toml`'s `[[guide_groups]]` table. **Never** in `docs-site/src/sidebar-config.json` — that file is generated by `tools/build-site.py`, gitignored, and untracked; editing it loses the change at the next build. Editing the projected tree loses the work at
the next build.

The same boundary explains why `guides/_shared/explanation/the-three-loops.md`
never reached the site despite containing the prose handoff-chain map this
redesign needs: it projects into the documentation surface correctly, and nothing
on the marketing surface points at it.

## Gaps in our own packs

A gap here is a finding about the pack, not a failure of the work. Gaps A through
D were named in the engagement; E, F, and G were found during discovery.

| Gap | What is missing | How this engagement handles it |
| --- | --- | --- |
| **A** | No skill gathers primary evidence, and `journey-mapping` admits only one `evidence-level` for a whole map. | Traffic data plus one interview, with per-stage evidence tags overriding the single frontmatter value. |
| **B** | No skill owns a cross-surface journey. `journey-mapping` takes one surface and one genre; all seven of its genre scaffolds are per-surface. | Run it twice, then hand-author a seam artifact whose unit of analysis is the transition, not the stage. The two maps stay canonical for their own surface; the seam owns only the edge. |
| **C** | No skill designs an explanatory information graphic. `architect-diagram` is the wrong genre and Mermaid was rejected; `mermaid-renderer` only rasterises; `interaction-design` does screen behaviour; `frontend-engineering` builds but does not design. | Treat the canvas as a screen: specify it with `information-architecture` plus `interaction-design`, hand-author the SVG composition, and file it under `screens/`. |
| **D** | No skill validates comprehension after ship. | A five-question explain-it-back check, with its baseline captured pre-redesign in the interview's Part 4 so the post-ship number has something to compare against. |
| **E** | No design skill knows about build-time projection boundaries. A designer amending the guides index will edit `docs-site/src/content/docs/guides/` and lose it at the next build. | Recorded above under "The projection boundary" and repeated in the handoff spec. |
| **F** | No skill reconciles a stale prior design spec against shipped reality. `docs/specs/platform-site/information-architecture.md` specifies MkDocs for `/docs/`; the repository ships Starlight. Any IA amendment is read against a document that no longer describes the system. | Flag the drift in the IA artifact rather than designing past it. Correcting that spec is separate work. |
| **G** | `[design] output_dir` is unconfigured in this repository — no repo-scope `agentbundle-layout.toml` exists. `experience-status` resolves the config chain read-only and stops at "not configured", so it cannot see `docs/design/principles/tech-site.md`, which already exists. | Surfaced to the owner. Creating the config is a repository settings decision, not a design decision. |

## Recorded findings that are real but out of scope

- **Gate codes reach 9 generated content files** — 12 occurrences — under
  `web/src/content/journeys/` and `web/src/content/packs/`. Those carry
  `generated: true` and are produced from `packs/*/JOURNEY.md` by
  `tools/build-site.py --journeys-only`. They violate the same principle as the
  marketing components. They are fixable only at the pack source; editing the
  projection loses the change.
- **The token baseline is 97, not 90.** `web/src/styles/tokens.css` declares 97
  unique `--ds-*` semantic tokens in its `:root` block, with no duplicates,
  above a separate primitive tier. Two further `--ds-focus-ring` declarations
  sit in scoped `:where(...)` blocks; both are deliberate, documented overrides
  — a white ring for amber-filled controls on a dark carrier, and the accent
  ring for dark zones — with their contrast ratios recorded in the file. They
  are not defects and must not be "cleaned up".
  `docs-site/src/styles/tokens.css` carries 146 separately-named tokens,
  confirming the deliberate split.
- **The gate-code rule is not a fourth principle.** `tech-site.md` has four
  principles; the gate-code rule is a *durable application* of the first. The
  fourth principle is "Preserve each surface's reading mode within one product
  identity", and it is the principle that arbitrates the marketing-to-docs seam.
  It explicitly forbids the easy fix of making both surfaces look alike.

## Thread plan and gates

| Phase | Artifact | Owner |
| --- | --- | --- |
| Discover | This brief; content inventory; traffic review; personas; seam; findings | Hand-authored |
| Discover | Baseline heuristic evaluation, both live surfaces | `design-review` |
| Discover | Comparative audit of how peers teach an operating model | `desk-research`, applied mode |
| Discover | Current-state journey maps, one per surface and genre | `journey-mapping` ×2 |
| **Gate** | **`approve-journey`** — owner approves both maps, the seam, and the derived screen list | Owner |
| Define | Future-state journey | `journey-mapping` |
| Define | Messaging framework per surface | `content-design` |
| Define | Marketing copy voice; brand register | `copy-direction`; `tone-of-voice` |
| Define | Sitemap, IA, navigation model | `information-architecture` |
| Define | User flows, screen inventory, per-screen state matrix | `user-flow` |
| Define | Measurement plan | Hand-authored, inheriting the journey's existing metric definitions |
| Design | Art direction, amended | `creative-direction` |
| Design | Token extension, against the real 97-token baseline | `design-system` |
| **Gate** | **`approve-aesthetic-direction`** — a named direction with precedents and anti-patterns; an adjective is a rejection | Owner |
| Design | Marketing structure and the above-the-fold decision | `conversion-design` |
| Design | Documentation IA and first-value moment per content type | `documentation-design` |
| Design | The operating-model canvas | Hand-authored, per Gap C |
| Design | Interaction spec; accessibility spec | `interaction-design` |
| Design | Copy deck and decision labels | `ux-writing` |
| Design | Annotated redlines and build handoff | Hand-authored |
| Validate | Independent cold design review | `experience-reviewer` |
| Validate | Design QA on the rendered result | `design-review` |
| Validate | Decision log | Hand-authored |
| **Gate** | **`review-experience-designs`** — Blockers acted on before design feeds build | Owner |
| Handover | Build intake | `intake-intent`, per `guides/product-engineering/how-to/hand-an-intent-to-build.md` |

## Working constraints

**Base freshness: skipped — origin is unavailable under workspace policy;
current checkout accepted as the task base.** The checkout at `047bf0192` with a
clean tree is the accepted base. No fetch, pull, or `ls-remote` was used as a
substitute.

Authoritative gate is `make build-check`, with three known pre-existing reds that
no `docs/design/` change causes: an `audit-npm` registry transport error, a
`semgrep --strict` timeout whose file set varies between runs, and two permanent
`catalogue self-host --check` drifts on `.claude/agents/*.md` that must stay at
HEAD state.
