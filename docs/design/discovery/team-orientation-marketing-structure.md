---
type: conversion-design
slug: team-orientation-marketing-structure
surface: responsive-web
surface-genre: marketing
communication_mode: product-copy
status: active
gate_approved: approve-aesthetic-direction, 2026-09-04
updated: 2026-09-04
---

# Marketing surface structure and the above-the-fold decision

Structure and placement only. No copy — `copy-direction` owns voice, `ux-writing`
owns strings. No tokens or colour — `design-system` and `creative-direction` own
those.

## A routing tension, named before anything else

This skill's first precondition is that the surface goal is acquisition or
conversion, with the primary measure being whether a visitor takes a defined
next action — and it routes informational surfaces elsewhere.

**This surface is acquisition genre with an action goal of Understanding**, and
its primary measure is an explain-it-back score rather than a conversion rate.
That is an unusual combination and it is the whole diagnosis: the champion cannot
make the decision, so the conversion happens off-surface, made by somebody who
never visits.

`informational-design` is still the wrong route — this surface does have a
conversion objective, does need an above-fold contract, and does need a CTA. So
this skill is the right one, used with its default success measure replaced. That
replacement is recorded rather than silent.

**Gap I, recorded:** no skill in the roster covers an acquisition surface whose
conversion is made off-surface by a third party the page never meets. Both
available routes assume the reader is the decider.

## Hero approach: narrative

Chosen from the five. Argued, because the choice determines everything below.

**Why narrative.** It is the type for complex products where the category is
unfamiliar or the use case requires imagination. All three apply: the product
carries two lifecycles, "an operating model for a team" is not a category the
reader arrives holding, and the champion must picture their own team inside it.
Decisively, **narrative is the only one of the five whose natural centrepiece is
a diagram of a sequence** — which is what the canvas is.

**Why not the other four.**

| Type | Rejected because |
| --- | --- |
| Statement | It is what ships today, and it fails the tweet test — shared alone it names a mechanism and an anti-property and assumes the reader knows what a build loop is. |
| Problem-agitation | Runner-up, and the closest call. The reader is already Problem-Aware, so agitating a pain they concede spends the scarcest space on something they already believe. What they lack is the *shape of the answer*. Its category-creation strength is real but the canvas delivers that better. |
| Demo-first | The interface is not the differentiator, and leading with a demo is precisely the try-one-thing framing this engagement replaces. |
| Social-proof | There is no social proof at any tier. Manufacturing it would violate the evidence principle, and higher-tier proof on a lower-maturity product reads as fabricated. |

**IC-first check.** The reader's situation must appear before the product's name.
The headline names the team's situation; the product is named in the
subheadline at the earliest. The current hero fails this and it is finding 5 in
the heuristic baseline.

## The above-the-fold decision

All six elements, placed. This is the decision the engagement asked to be made
and argued.

| # | Element | The decision | The argument |
| --- | --- | --- | --- |
| 1 | Headline, ≤10 words | Names the team's situation and who this is for. Does not name the mechanism. | The reader is Problem-Aware and the page's job is Understanding. A mechanism headline is unrepeatable, which the dominant copy goal forbids. |
| 2 | Subheadline | Carries the product insight the headline cannot — why the obvious alternatives fail. Conviction-building, not a second problem statement. | Tone-collision check: a situation-framed headline must not be followed by agitation. |
| 3 | Primary CTA | **The install, re-framed as station two of five.** Outcome language names proving it on the reader's own real work, not trying a thing. | The adoption journey records that a champion who has not run it themselves cannot demonstrate it. Station 2 genuinely precedes station 3. What changes is not the action but its meaning: the arc gives the command a place. |
| 4 | Secondary CTA | **The route into the ordered paths** — what adopting this asks of a team. | The primary asks meaningful commitment (installing into a repository), so a lower-commitment option is required. It serves the platform lead and budget holder, who are not the installer. The current secondary points at a pack menu, which is a taxonomy rather than a lower-commitment version of the outcome. |
| 5 | Proof signal | **One specific figure from the most recent merged change — the number of independent reviews that cleared it — linked to that change.** | Must be specific and visible without scrolling, which the band below is not on a phone. **Not a second copy of zone 2's link:** cold review caught that the earlier draft put the same artifact twice, about 200px apart. This is the headline figure; the band carries the full evidence. |
| 6 | Friction microcopy | Names what installing changes in the reader's repository, and that it is reversible. | The dominant objection to the primary CTA is not price or signup — it is *what does this do to my repo, and can I undo it.* The current line lists capabilities instead, which answers a question nobody asked at that moment. |

**The canvas is not one of the six.** It is the hero's content, and it carries
the narrative that elements 1 and 2 open. Two things must complete in five
seconds with no interaction: that this is about a team over time, and that one
station contains the detail.

**A third affordance that is not a CTA.** The canvas is linkable and copyable.
That is a property of the artifact, not an action on the page, and it is why the
link-preview strings matter as much as the drawing — a chat client reads only a
small prefix of the page, so the text payload does the work there.

## Scroll story: the seven jobs, and how eleven zones fill them

The canonical structure is seven zones, one job each. The IA specifies eleven.
They are reconciled here rather than left to contradict.

| Zone | Job | IA zones that fill it |
| --- | --- | --- |
| 1 | Conviction + CTA | 1 — canvas, six elements |
| 2 | Proof | 2 — three checkable proofs |
| 3 | Problem amplification | 3 — the problem |
| 4 | Solution fit | 4 — what changes for a team; 7 — recognise your work |
| 5 | How it works | 5 — what happens to one piece of work; 6 — where a person decides |
| 6 | Objection handling | 8 — works with your agent |
| 7 | Bottom CTA | 9 — install; 10 — roll it out to your team; 11 — own the catalogue |

**One deliberate deviation from the canonical order: proof moves from zone 4 to
zone 2.** Argued, because reordering a default needs a reason.

Two things force it. The aesthetic direction pins this band immediately below the
primary action, continuous with the dark hero, and moving it breaks the
alternating-band model that the whole surface treatment rests on. And the
dominant aesthetic goal already resolves the general case: *when a specific claim
is more trustworthy visible than hidden, surface it.* The reader here is a
skeptic whose first move is to check, so proof-then-problem serves them better
than problem-then-proof.

**One-job-per-zone holds, and two pairs need watching.** Zones 4 and 5 each draw
on two IA zones. In zone 4 that is coherent — both answer "does this fit my
situation." In zone 5 it is coherent too, but only because IA zone 6 is the
*decision points inside* the work sequence rather than a separate topic. **IA
zones 4 and 5 must never merge**: zone 4 is what happens to a team, zone 5 is
what happens to one piece of work, and collapsing them reinstates the diagnosed
defect where six of nine current sections describe both at once and neither
whole.

**Zone 7 carries three IA zones and is the one at risk.** Install, the team
route, and the catalogue closer are three different commitments. They survive as
one zone only because they are three rungs of the same ladder — individual, team,
organisation — in ascending order. If that reading fails review, zone 7 splits
rather than dropping one.

## The three checkable proofs

Zone 2 replaces the self-reported stat strip. The gate decision was to re-task
rather than cut, and the band keeps its pinned position.

| Proof | What it establishes | Why a skeptic can check it |
| --- | --- | --- |
| **One real merged change** | That the loop cannot approve its own work, and that a person makes the merge decision | A public URL with a merge event, review verdicts, and an author who is not the merger |
| **The gate output from that same change** | That lint, typecheck, and tests are mechanical gates rather than advisory | The commands and their results, including that they were red before they were green |
| **The adapter capability matrix, generated from the adapter contracts** | That one install spans every supported agent | It already exists on the page as a hand-maintained table; generating it from the contracts converts a claim into evidence without adding a section |

Proofs one and two are deliberately one real change seen two ways. That is
stronger than three unrelated artifacts, because a skeptic can follow a single
thread end to end instead of taking three separate things on trust.

**Two hard constraints on all three.**

**Generated, never pasted.** A snapshot of real output decays into a false claim
the moment the system changes, and a decayed proof is worse than no proof. Each
of the three must be produced by something that reruns. This is the same
requirement the token verification found for the canvas SVG, and it is the same
pipeline.

**Never invented.** The evidence principle's own tradeoff is explicit: where the
real artifact cannot be shown safely, the surface names the evidence boundary
rather than substituting an example. If any of the three cannot be shown, the
band says so in its place.

## Social proof tier: pre-PMF, and the honest tier is not social

Matched to actual maturity rather than aspiration, because higher-tier proof on a
lower-maturity product reads as fabricated.

There are no customer logos, no quantified customer outcomes, no press, and no
analyst recognition. At the early tier the canonical primary is specific outcomes
from named beta users, and those do not exist either.

**So the tier this product can actually earn is evidence-by-artifact rather than
borrowed credibility** — real output from a real run, which is what the three
proofs are. This is not a workaround. For a skeptical engineering reader it is
stronger than a logo wall, and it is the only tier that satisfies the evidence
principle instead of fighting it.

Recorded so nobody later reads the absence of logos as a gap to fill.

## Numbered product tour spine — zone 5

Zone 5 answers "but how does it actually work" as a process, not a feature list.

1. **Trigger** — a piece of work exists that a team needs to ship, and nobody
   wants an agent deciding on its own that it is done.
2. **First action** — the work becomes a stated outcome, then a human-approved
   engineering contract before any code is written.
3. **Intermediate result** — mechanical gates and three independent cold reviews
   run, and the reader can see them pass or fail. This is the step that confirms
   they are on track, and it is where the proofs from zone 2 come from.
4. **Primary outcome** — a person merges, a throwaway environment validates the
   deployment, and a person ratifies the production ship.

Each step names the capability serving it; none reprints an interface label, and
none uses an internal gate identifier. The decision points from IA zone 6 attach
to steps 2 and 4, which is why they belong inside zone 5 rather than beside it.

## Editorial quality gate

**Deletion pass.** Run against this specification on the assumption it is 30 per
cent too long. Three things were cut: a fourth proof candidate (a real review
transcript, which duplicated proof one's evidence and answered no additional
question); a separate objection-handling zone for the tracker question (it is
answered by the canvas's geometry and does not need prose); and a second above-fold proof signal (two proof signals above the fold is neither, and the band below carries the rest). **A further duplication survived that pass and cold review caught it:** element 5 and zone 2's first proof were the same artifact twice. Element 5 is now the headline figure from that change rather than a duplicate link to it.

One thing survived the pass that looked cuttable: the friction microcopy. It
reads as small, and it is the only element answering the dominant objection to
the one action the page asks for.

**Human copy tests**, run against the above-fold *specification*, since no copy
exists yet.

| Test | Result |
| --- | --- |
| 5-second | **Concern.** *What is this / who is it for / why care / what next* are all answerable from the spec. *Why different* and *why believe* rest on the canvas being legible in five seconds and on one proof link. Both are real answers, but both are load-bearing on execution rather than on structure. |
| Specificity | **Pass.** The five-station arc, the named refusals, and a link to one real merged change cannot be pasted onto another company's page. The current live copy largely could. |
| Point-of-view | **Pass.** The structure has an opinion about the problem (unsupervised loops self-certify), about the status quo (a better prompt is not the answer), and about why current approaches fail (they optimise for one person trying one thing). |
| Distinctiveness | **Concern.** The structure is distinctive; whether it reads as a specific person with something specific to say depends entirely on copy that does not exist yet. Flagged for `ux-writing`, not resolvable here. |

**Gate summary: 2 passed, 2 raised a concern — 5-second and distinctiveness, both
dependent on execution rather than structure.**

## Zero gate codes

The structure removes all eleven rendered internal gate identifiers: five from
the three-loops zone, which zone 5 absorbs, and six from the decision cards,
which zone 5 carries in human phrasing. The decision points are the questions a
person answers. Verified by count at review, not asserted.

## Hand-off

`ux-writing` for every string, including the two tests above that resolve only in
copy. `interaction-design` for the canvas's behaviour and the zone-7 CTA
repetition. The build handoff carries the three proofs' regeneration
requirement, which shares a pipeline with the canvas SVG generator and the
raster export.
