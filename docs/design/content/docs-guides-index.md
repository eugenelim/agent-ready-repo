---
type: content-brief
surface-type: product-or-reference
communication_mode: technical-editorial
persona: adoption-champion — docs/design/discovery/team-orientation-personas.md
date: 2026-09-04
---

# Content brief: documentation guides index

Content direction only. A separate brief from the marketing home, because a
single brief across two surfaces serves neither precisely.

## Surface objective

**Surface type:** product-or-reference. Mode `technical-editorial` — this is
wayfinding and conceptual explanation, not API, CLI, configuration, installation,
or troubleshooting reference.

**Primary reader:** The same adoption champion, in a different mode. On the
marketing surface they were deciding whether to care. Here they have decided and
need something to hand to other people: a platform team who will install it, an
engineer who will use it daily.

**Secondary readers:** those other people, arriving on a link the champion sent —
and, importantly, arriving via search with no context at all.

**Objective:** Get the reader to a followable sequence they can hand to someone
else.

## User task

**Task:** Choose a path for somebody else and hand it over.

**Completion definition:** The reader has a named, ordered sequence with a stated
prerequisite, a rough time cost, and a first result — and they can send it to a
colleague without adding an explanation of their own.

This is a **Decision** task at **high prior knowledge**. The reader is not
learning what the product is; they are selecting between paths for a known
purpose.

## Content structure arc

**Selected arc:** Pyramid Principle.

**Applicability rationale:** The Pyramid Principle applies when the action goal is
Decision or Understanding at high prior knowledge, which is exactly this reader.
Conclusion first, top-down.

**What that means concretely, and it is the whole fix.** The page currently opens
with *"Choose the pack and guide that matches your outcome"* — an instruction to
navigate — and puts the six ordered paths below it. Pyramid Principle inverts
that: lead with the answer. The paths *are* the answer. The pack-choosing
material is supporting detail and belongs below them.

The content already exists and is good. This brief moves it, it does not
commission it.

## Content format

**Selected format:** mixed.

**Format rationale:** the paths are a true sequence, so numbered steps. The
choose-by-outcome material is a comparison across parallel options, so a table.
The framing that a path ends at a handoff rather than a document is a
relationship the reader must grasp before scanning, so short prose. Forcing any
one of the three into another's form is what makes reference pages unreadable.

## Content hierarchy

Must-say, probably-say, might-say.

| Content item | Tier | Placement notes |
| --- | --- | --- |
| One "start here" promise — a single link and a single stated outcome | **must-say** | Above the fold. Does not exist today; the nearest thing is the first path, several screens down. |
| The six ordered paths, each with prerequisite, audience, time cost, first value, and end state | **must-say** | Immediately below. Currently present and correctly written; currently below a nav instruction. |
| That a path ends at a handoff, not at a document | **must-say** | With the paths. This is the sentence that makes the paths handover-able rather than reading lists. |
| Prominent search with a placeholder naming a real example query | **must-say** | At 229 published pages this surface is in the search-first tier. Today search is a header widget with a generic placeholder. |
| Which of the two generated hierarchies — guides or pack reference — answers which kind of question | **must-say** | At the point the reader chooses between them. Currently unstated, and they appear as peers. |
| Choose-what-you-want-to-achieve table | probably-say | Below the paths. Already carries the seven job names the sidebar should adopt. |
| Choose-by-role list | probably-say | Below the outcome table. A second way in for readers who think in roles. |
| A route back to the internal-case material | probably-say | The docs-to-marketing crossing. Does not exist today and this skill's own wayfinding check calls its absence a blocker. |
| Cross-cutting shared guidance list | probably-say | Grouped, not enumerated inline. |
| "Writing a guide" | might-say | Contributor-facing, not reader-facing. Lowest position. |
| The note that the site generates pack and guide navigation from this tree | might-say | Useful to a maintainer, invisible in value to a champion. |

## What this surface must not become

Principle 4 governs the seam: each surface keeps its own reading mode within one
product identity. The obvious way to fix this page is to make it more like the
marketing page. That is a violation, not a repair.

So: **no persuasion register here.** No claims, no CTAs framed as conversion, no
above-fold headline making an argument. What crosses the seam from marketing is vocabulary — the seven job names, which
already appear here, and the human decision phrasing — plus destinations. The
five adoption station names are marketing-side only and must not be forced into
this surface's navigation. What does not cross is register, density, palette, or navigation
pattern.

The route back to the internal case is a *destination*, not a pitch. It points at
the marketing surface; it does not import it.

## Completion metric

**Primary signal:** task completion rate — can a platform lead who has never
spoken to the champion complete the adopt path from this index alone? If not, the
champion is still the dependency, which is the failure mode this surface exists
to remove.

**Secondary signal:** search resolution rate, and the proportion of guide-area
arrivals that come through this index rather than through raw repository source.
That ratio is currently inverted: one raw skill file drew 12 unique readers in 14
days against 6 for the repository's docs directory.

## Open questions

- **Does the first path need splitting?** It is stated at about an hour, and a
  first-value on-ramp should be closer to twenty minutes of active work.
  Splitting a short on-ramp out of it is `documentation-design`'s call.
- **What is the real example search query?** It has to be a query that actually
  returns something useful, which needs checking against the index rather than
  inventing.
- **Are several pack area index pages typed wrongly?** Several carry an
  explanation kind while functioning as navigation hubs. Either they retype or
  the type set needs a hub kind. Owner: the guide source model.
- **`agent-skill-engineering` is named in the job taxonomy and has no guide
  area.** The taxonomy points at a destination with no content here. Not a
  content decision.

## Hand-off

`communication_mode: technical-editorial` and this is not an onboarding surface,
so `copy-direction` does **not** apply — that route is reserved for acquisition
surfaces and for onboarding, which converts an evaluator into an active user.
`ux-writing` owns UI-state copy only: the search placeholder, the no-results
recovery, and the partial-path marker.

`documentation-design` is the next substantive step: the Diátaxis type map, the
first-value target per content type, and the on-ramp split.
`information-architecture` has already fixed the navigation model and the job
grouping.
