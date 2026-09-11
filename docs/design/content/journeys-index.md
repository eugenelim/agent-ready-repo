---
type: content-brief
surface-type: acquisition
communication_mode: technical-editorial
persona: first-time-user — see docs/design/content/marketing-home.md, 2026-09-10 amendment
date: 2026-09-11
---

# Content brief: the journeys index

Content direction only. A separate brief from the marketing home and the guides
index, because this surface has a different job from both.

**Why this brief exists at all.** The journeys index was **never in the
team-orientation design packet's scope**. That packet briefs the marketing home,
the guides index, a path page, search results, the internal-case route and the
canvas. This surface is absent from all of them. Slice S6 then redesigned it
with nothing to anchor on, which is the direct cause of the design review's
finding that its groups "feel added above an existing catalogue grid". This
brief supplies the missing anchor, after the fact.

## Surface objective

**Surface type:** acquisition — it sits on the marketing site at `/journeys/`.

**Mode:** `technical-editorial`, not `product-copy`. The page's content is
*descriptive*: what a real session with a pack looks like, stage by stage. It
carries no conversion goal of its own and must not acquire one. The seam with
the marketing home is that the home *claims* and this page *shows*.

**Primary reader:** the same first-time user the marketing home now names. They
have read a claim and are asking the sceptic's question: **"show me what using
this actually looks like."** The marketing brief's 2026-09-11 amendment routes
them here for exactly that, and records that journeys is *proof-shaped* for this
reader rather than navigation-shaped.

**Secondary reader:** someone who has decided to adopt and is choosing which
pack to start with.

**Objective:** let the reader see the shape of real work with these packs, and
leave knowing which one they would start with.

## User task

**Task:** Recognise the work, then pick an entry point.

**Completion definition:** The reader can say what a session looks like in at
least one discipline, and name the one they would start with and why.

This is **Understanding** at low prior knowledge, with **Decision** secondary.
That ordering is the whole structural constraint: a reader who cannot yet
picture the work cannot choose between twenty options, so recognition must
precede the menu.

## Content structure arc

**Selected arc:** none of the three acquisition arcs. This is an
**inverted-pyramid listing**: the relationship between the items is the content,
and the items are the detail.

**Applicability rationale.** StoryBrand and Conversion-Centered Design both
assume a persuasion goal this surface does not have, and the marketing home
already owns the arc for this reader. What this page must do instead is make
**three different relationships legible at a glance** — a sequence you walk in
order, loops that run underneath everything, and additions you reach for. A
reader who cannot tell those apart is looking at a grid of twenty equivalent
things, which is what the page was before S6 and what it reverts to if the
grouping signal is lost.

## Content hierarchy

| Content item | Tier | Placement notes |
| --- | --- | --- |
| What a journey *is* — a staged walkthrough of a real session, including the human gates | **must-say** | Above the fold. Present today in the hero. |
| The four disciplines as one ordered sequence, in the packs' declared order | **must-say** | First group. Ordered markup, not visual order alone. |
| What each discipline hands the next, and what the last one leaves you with | **must-say** | On the sequence cards. This is what makes it a sequence rather than four adjacent cards. |
| The three relationships distinguishable **without** their headings | **must-say** | Card treatment carries it. The design review found all three groups sharing one treatment, which collapsed them. |
| Every journey in the collection reachable from this page | **must-say** | Membership derived, never enumerated. A hardcoded list previously dropped five journeys, including `product-strategy`. |
| The supervised loops, named as running underneath rather than alongside | probably-say | Second group. |
| Optional additions, named as a relationship rather than as leftovers | probably-say | Third group. "Everything else" is not a relationship. |
| A route onward to the guides path that walks the sequence | probably-say | **Does not exist today.** The page shows the shape and then strands the reader; `guides/README.md` P2b is where they would go next. |
| Per-pack install or capability detail | might-say | Belongs to `/packs/`. Duplicating it here is the failure below. |

## Genre routing

The craft sequence's IA step is served by a **genre-direct skill**, and
`packs/experience-design/DESIGN.md` is explicit that this replaces
`information-architecture` only — the rest of the sequence still runs.

**Selected: `marketplace-design`.** The dominant structural questions here are
listing-card IA — what one card must carry, how twenty of them group, and how a
reader scans across them — which is that skill's subject. `conversion-design`
was considered and rejected: its above-fold contract and social-proof
architecture assume the persuasion goal this surface explicitly does not have.
`documentation-design` was rejected because this is not a Diátaxis-typed
reference tree.

**What that routing does not license.** `marketplace-design`'s filter and facet
architecture and its transaction bridge do not apply: there is no transaction,
and twenty items do not warrant faceting. Taking the genre wholesale is as wrong
as taking none of it.

## What this surface must not become

- **A second pack catalogue.** `/packs/` owns capability, install and adapter
  detail. This page owns *what the work looks like*. Every time per-pack detail
  migrates here the distinction erodes and both pages get longer.
- **A persuasion surface.** No claims, no CTA framed as conversion. The page's
  persuasive force is that the walkthroughs are real; adding copy that says so
  weakens it.
- **A first-value claim.** No assertion that a reader who follows a journey
  reaches a working artifact. The Claude-apps install-to-first-value probe is
  still unrun, and `claude-apps-route-docs` AC12 fences the same claim.
- **A place where the sequence is asserted rather than shown.** The order is the
  packs' own declared order; if a pack's `DESIGN.md` changes, this page is wrong
  and must follow, not the reverse.

## Completion metric

A first-time reader who arrives from the marketing home can, without leaving the
page, describe one discipline's session shape and name the discipline they would
start with. Untested: no reader has been asked. The S6 cold read established
that the *sequence and its handoffs* are statable from this page, which is a
necessary part of this metric and not the whole of it.

## Open questions

1. **Does the four-discipline sequence belong on this page at all, or on its
   own?** It is currently one group among three on a listing page. A dedicated
   surface would let it carry the literal requests and worked handoffs that S7
   needs, which twenty cards cannot. Not decided here.
2. **Should the marketing home's `ThreeLoops` reconcile with this page?** The
   home surfaces `core`, `product-engineering` and `release-engineering` as the
   three loops; this page leads with four disciplines. The design review warned
   that folding the disciplines into `ThreeLoops` "would blur two distinct
   models". Recorded, not resolved.
3. **Who owns this brief?** The marketing home's structure belongs to
   `cohort-orientation-surfaces`, but that intent puts journey pages explicitly
   out of its Boundary — and this surface was in no packet. It has no owner
   today.
