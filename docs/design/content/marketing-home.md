---
type: content-brief
surface-type: acquisition
communication_mode: product-copy
persona: first-time-user — see the 2026-09-10 amendment; supersedes adoption-champion for this surface
date: 2026-09-04
---

# Content brief: marketing home

Content direction only. No finished copy, no design values. `copy-direction` owns
the voice, `ux-writing` owns the strings.

## Surface objective

**Surface type:** acquisition

**Primary reader:** An adoption champion. Has used a coding agent for months; has
not used a supervised operating model. Cannot authorise adoption and cannot
install it at scale. Arrives cold — 61 percent of arrivals carry no referrer, and the README is the single largest destination at 68 of 149 unique visitors, which is 46 percent rather than a majority.

**Objective:** Make the champion able to re-explain the operating model to
someone who has not seen this page.

## The action goal, and why it reframes the surface

The four action goals are Decision, Understanding, Execution, and Belief shift.
For this surface the goal is **Understanding**, with Belief shift secondary.

That is unusual for an acquisition surface and it is the whole diagnosis. The
champion cannot make the Decision — a budget holder does. They can perform the
Execution — install it — but performing it does not advance their actual job. What
they need to carry away is understanding transferable to three other people.

The current page optimises for Execution. Its strongest, most trustworthy moment
is a runnable command, and its weakest are the four claims a champion would have
to repeat. That inversion is the defect, stated in content terms.

## Audience awareness level

**Level:** Problem-Aware, edging into Solution-Aware.

**Rationale:** The champion already feels the pain — ad-hoc AI-assisted work that
nobody supervises — but does not know that "an operating model for a team" is the
category of answer, so they are not yet Solution-Aware in the sense that matters.

## Narrative arc selection

**Selected arc:** StoryBrand.

**Applicability rationale:** StoryBrand fits cold and warm audiences at awareness
levels one to three, and this reader is at two. Conversion-Centered Design
targets bottom-of-funnel readers who already know they want the product, which
describes almost nobody arriving here.

**One deliberate adaptation — revised 2026-09-10.** The hero is the reader, and
only the reader. The arc's "plan" element is this reader's own path through
stages 1-3: see whether this is real, prove it on one real task, and reach a
result worth showing someone. It is not a hand-over artifact, and it is not
anyone else's plan.

*What it was, and why it changed.* This previously read: "the reader is a hero
who must go on to guide three other people", so the plan element did double duty
as both their plan and the thing they hand over. That was written when this
surface carried all five stages. It no longer does — stages 1-3 are this
surface and stages 4-5 are `docs-site/` — so the double duty described a job
this page cannot do. A first-time user who has not yet run anything cannot be
handed an enablement artifact, and asking them to plan for three colleagues
before they have a result of their own inverts the arc's own order.

*The adaptation that replaces it.* The standard arc establishes the guide's
authority with social proof — testimonials, logos, customer counts. This page
has none and should not manufacture any. It substitutes **proof by runnable
artifact**: the strongest element on the page is a command the reader can run,
and the self-host check that fails on drift is evidence the reader can verify
rather than be told about. That substitution is the adaptation, and it fits the
reader better than testimony would, because the stated blocker is suspicion
that the thing is not real.

## The information hierarchy this mode requires, mapped to the page

The mode's order is user problem, then product insight, then outcome, then proof,
then mechanism, then technical detail — and its named anti-pattern is feature,
feature, feature, architecture, explanation, summary.

**The current page is close to the anti-pattern.** Hero states a mechanism, the
strip states technical detail, the menu lists features, and the problem arrives
fourth. The reordering below is what fixes it.

## Scroll sections

Eleven zones from the IA. Each has one job, expressed here as its content
direction.

| # | Section | Job | Content direction |
|---|---|---|---|
| 1 | Above the fold | problem + plan | Name the reader and their problem in the first sentence. The canvas beneath carries the outcome and the mechanism at a glance — the reader should grasp *shape and coherence*, not detail. Do not lead with what the system is. |
| 2 | Three proofs | guide proof | Three things a skeptic can check, adjacent to the biggest claim. See below. |
| 3 | The problem | problem | Expand the product insight: why a better prompt, or one more tool, does not solve this. This is the page's best-written existing content; it moves up, it does not get rewritten. |
| 4 | What changes for a team | plan | The five stations and **what each asks of a team**. Only station 2 carries durations, with their provenance cited; the other four name the commitment shape, because no published cost exists for them and inventing one is barred. |
| 5 | What happens to one piece of work | plan (nested) | The work sequence end to end. Must read as *inside* station 2, not as a second plan. No gate codes. |
| 6 | Where a person decides | stakes | What each handoff asks of a human, phrased as the question they answer. The stakes are what the system will not do alone. |
| 7 | Recognise your work | guide proof | Route by outcome before pack names. Existing content, relocated below the problem so the reason precedes the menu. |
| 8 | Works with your agent | guide proof | Removes the "will it work with my setup" objection. Unchanged. |
| 9 | Start in one command | CTA | The one runnable thing. Framed as station 2 of five, not as the whole product. |
| 10 | Roll it out to your team | CTA (transitional) | The route into the ordered paths — the artifact the champion hands over. New. |
| 11 | Own the catalogue | stakes | The end state for an organisation, not an individual. Unchanged. |

**Zones 4 and 5 must stay separate.** Zone 4 is what happens to a team; zone 5 is
what happens to one piece of work. Six of the nine current sections describe both
at once and neither whole; that is the failure being fixed, and merging them
reinstates it.

## Above-fold structure

**Headline contract:** Answers *who this is for* and *what problem it solves*, in
the reader's words, in one sentence. It must not name the mechanism. The current
headline names a mechanism and an anti-property, which is why it fails the tweet
test — shared alone it describes a component and requires the reader to already
know what a build loop is.

**Subheadline contract:** Carries the product insight the headline cannot — why
the obvious alternatives do not work. Not a second problem statement, and not a
feature list.

**What the canvas carries above the fold:** outcome and mechanism at low
resolution. Two things must complete within five seconds and without interaction:
that this is about a team over time, and that one station contains the detail. The
rest of the canvas may reward reading; none of it may require interacting.

## The three checkable proofs

Zone 2 keeps the position the aesthetic direction assigns it — immediately below
the primary action, continuous with the dark band — and replaces its content. The
current three numbers are accurate, self-reported, and unverifiable, so they read
as scale rather than proof.

Each replacement must be a real artifact, command, route, or output. The
repository already contains all three candidates:

| Proof | What it establishes | Why it is checkable |
| --- | --- | --- |
| One real merged change | That the loop cannot approve its own work, and that a person makes the merge decision | A public URL with a merge event, the review verdicts, and an author who is not the merger |
| The gate output from that same change | That lint, typecheck, and tests are mechanical gates rather than advisory | The commands and their results, including that they were red before green |
| The adapter capability matrix, generated from the adapter contracts | That one install spans every supported agent | It is already on the page as a hand-maintained table; generating it from the contracts converts a claim into evidence |

Proofs one and two are deliberately one real change seen two ways, so a skeptic can follow a single thread end to end. This set is authoritative and supersedes an earlier draft here that named a standalone review transcript as the third proof — that duplicated proof one and answered no additional question.

Two hard constraints on how these are produced:

- **Generated, not pasted.** A snapshot of real output decays into a false claim
  the moment the system changes. These must be produced by something that
  reruns, or they become the opposite of proof.
- **Never invented.** Principle 2's own tradeoff is explicit: where the real
  artifact cannot be shown safely, the surface names the evidence boundary rather
  than substituting an example. If any of the three cannot be shown, say so in
  place of it.

`conversion-design` decides how many of the three fit the band.

## CTAs

| Type | Label direction | Next state |
| --- | --- | --- |
| Primary | Communicates *prove it on your own real work*, not *try a thing*. The install stays primary because personal fluency is a genuine prerequisite — the adoption journey records that a champion who has not run it themselves cannot demonstrate it. What changes is that the arc now gives the command a meaning: it is station two of five. | Install and run on a real pending task |
| Transitional | Communicates *see what adopting this asks of a team*. For the platform lead and the budget holder, who are not the installer. | The ordered paths on the documentation surface |

The current secondary action sends the reader to the pack menu, which is a
taxonomy rather than a lower-commitment version of the primary outcome.

## The link-unfurl surface

The observed transfer mechanism is a pasted link — 12 unique people opened one
through Microsoft Teams in 14 days, double what the whole published site
referred. So the unfurl is a content surface, not a technical detail.

Naming the literal tag values is out of this skill's scope and belongs to
`ux-writing`. What the unfurl must communicate, in priority order:

1. **What this is**, in one line that stands alone in a channel where nobody has
   context.
2. **Who it is for** — a team, not an individual. This is the single thing most
   likely to make a manager click.
3. **What it costs to engage** — a time signal, so a recipient can decide whether
   to open it now.

The constraint that shapes all three: a chat client fetches only a small prefix
of the page, so the text payload does the work and the image is secondary. We had
assumed the opposite.

## Success metric

**Primary signal:** the explain-it-back score, out of five, for a reader who has
seen only this page. Baseline captured pre-redesign in the champion interview.

**Secondary signal:** five-second-scan completeness — can a first-time reader
answer what this is, who it is for, and whether they should care, from visible
content alone? Two of the three are currently unanswerable.

**Explicitly not install conversion.** That metric measures the try-one-thing
outcome this engagement exists to move past.

## Open questions

- **Can one surface carry Understanding for four audiences?** Practitioner
  sales-enablement literature holds that generic collateral fails and each
  stakeholder needs its own proof type. Our position is that the canvas is the
  shared model and the per-audience answers are entry points into it. Untested,
  and every source arguing the other way has a client-acquisition incentive.
  Owner decision at the aesthetic-direction gate.
- **Which of the three proofs can actually be shown, and by what regenerator?**
  Needs an engineering answer, not a content one.
- **Does the primary CTA stay the install?** The reasoning above says yes because
  fluency is a prerequisite. It is worth one challenge, because it is also what
  the current page does.
- **Is the problem statement good enough to be the headline?** It passes the tweet
  test that the current headline fails. Raised in the design review's director's
  notes and unresolved.

## Hand-off

`communication_mode: product-copy`, so: `copy-direction` next for per-surface copy
voice and register grounding, referencing the brand register once
`tone-of-voice` has produced one. `conversion-design` reads this mode and runs
its editorial quality gate. `user-flow` consumes the scroll sections as copy
slots. `ux-writing` owns the strings, including the unfurl.

---

## Amendment — 2026-09-10: the reader is a first-time user, not a champion

**This amendment changes the surface's audience and therefore its action goal.
Where it conflicts with the body above, this section governs.** The body's
analysis of the *page* remains accurate; its analysis of the *reader* does not.

### The change

People who land here are looking to **use the system for the first time**.

**Corrected against the standing journey.** An earlier version of this
amendment said the champion "arrives on the tech site instead". That is wrong,
and the gate-approved
[team-orientation future-state map](../journeys/team-orientation-future-state.md)
says why: it maps *one person across five stages*, not two personas. Stages 1-3
— evaluate, prove on real work, win buy-in — are all set on this surface; only
stages 4-5, rolling out a cohort and making it the default, move to the
documentation guides index.

So the reader here is the same person who later becomes a champion, met at the
stages where they are using the system for the first time. Their action goal on
this surface is Execution because the journey's Stage 2 has them installing and
running it on a real pending task — not because a different reader replaced
them. [The guides index brief](docs-guides-index.md) owns their stages 4-5 job,
which is why the hand-off work belongs there.

### What this retires

The body's central diagnosis — that the page "optimises for Execution" and that
"that inversion is the defect" — **no longer holds**. For a first-time user,
optimising for Execution is correct.

The specific criticism survives in a sharper form. The defect is not that the
page's strongest moment is a runnable command. It is that the page offers
**exactly one door**, and readers who cannot use that door read it as a
statement about who the product is for. One door, not the wrong kind of door.

Consequently the resolution in the previous version of this amendment — serving
the no-terminal reader through a transitional CTA so the fold could stay
Understanding — is withdrawn. There is no longer a competing goal to protect the
fold for.

### The new frame

| Field | Value |
| --- | --- |
| Primary reader | Someone evaluating whether to use this on their own work, today. Technical or not. |
| Action goal | **Execution**, with Belief shift secondary — they must believe it is real enough to be worth starting. |
| Objective | Get them to a first result on their own work, by whichever door fits them. |
| Awareness level | Solution-Aware, edging Product-Aware. They arrive with intent, not to be convinced a category exists. |

**Arc: StoryBrand stands. Checked 2026-09-10 against the closed set.**

An earlier version of this amendment said the audience change routes the
surface to Conversion-Centred Design. That was wrong, and it conflated two
axes. Acquisition arcs are selected by **awareness level**; what changed here
is the **action goal**. Wanting to use something for the first time is intent
to act, not awareness of this product. CCD's applicability test is a reader who
already knows the product and needs friction removed — and the journey says
this one "arrives cold", triggered "mostly not the marketing page" but by a
link pasted into a work chat, a search result, a package page, or the README.
That is levels two to three, which is StoryBrand's range.

The action-goal change reweights the CTA, not the narrative structure. No new
arc is needed, and none of the three in the closed set fits better.

**What needed revising was the adaptation, not the arc. Done 2026-09-10.** The
body recorded one: the reader is "a hero who must go on to guide three other
people", so the plan element did double duty as the thing they hand over. That
was written when this surface carried all five stages. Stages 4-5 now belong to
the documentation guides index, so the plan element is the reader's own path
through stages 1-3, and the hand-over artifact is not this page's to produce.

The rewrite is in § "One deliberate adaptation" above. It does two things:
withdraws the double duty, and names the adaptation that is actually in force —
proof by runnable artifact standing in for the social proof the standard arc
uses and this page does not have. **This open item is closed**; the arc was
already settled.

**How the two arcs meet.** StoryBrand here carries stages 1-3, problem-first,
because the reader does not yet recognise their situation. Pyramid Principle on
[the guides index](docs-guides-index.md) carries stages 4-5, conclusion-first,
because by then they have proved it and are equipping other people. The arc
hand-off is the same seam as the journey's surface hand-off, which is why
neither surface needs the other's arc.

### Zone 9 is now the page's business, with two equal doors

Starting is no longer station two of five reached partway down the page; it is
what the reader came for.

| Zone | Change |
| --- | --- |
| 9 — Start | Promoted in emphasis. Carries **two equal doors** — a terminal route and a Claude-apps route — presented as one section with two entrances, not a primary and a fallback. |
| 10b | **Withdrawn.** The no-terminal route is no longer transitional; it is half of the primary. |
| 10 — Roll it out to your team | Retained but demoted to transitional. It serves the champion, who is now a secondary reader here and a primary reader on the tech site. |

Neither door may be framed as the lesser one. A reader who cannot use the
terminal and is offered the other route as a fallback has had their original
suspicion confirmed rather than answered.

### What carries over unchanged

- **The proofs.** Still the right mechanism, now answering "is this real enough
  to start" rather than "can I re-explain this". The self-hosting proof — that
  `make build-self` runs a self-host check that fails on drift — remains the
  strongest, and is the one that substantiates the lifecycle position without a
  number.
- **No inventory.** No counts of reviewers, security modules, scanners, stages,
  or feedback loops. The body already established why for the three current
  numbers, and the reasoning is unchanged by the audience.
- **The honest limit in zone 6.** Complete from intake to merge, deliberately
  thin after it; observability and cost accounting named as later roadmap
  initiatives rather than claimed. This matters *more* for a first-time user
  than it did for a champion, because they are about to depend on it.
- **Governance and orchestration as texture**, not headline: depth routed by
  what a change touches, and a work loop that is resumable and auditable rather
  than a prompt chain. No numbers.

### Open questions this amendment leaves

- Whether the arc moves from StoryBrand to Conversion-Centred Design. It
  follows from the awareness change by this brief's own stated rule, and it
  rewrites the section-by-section jobs above.
- Whether the champion retains any presence on this surface at all, or whether
  zone 10 should point at the tech site and stop. The journeys for both readers
  exist; the question is one of emphasis, not evidence.
- Whether the two doors in zone 9 read as one choice or as a fork the reader
  must evaluate before acting. `conversion-design` owns it.

---

**Delivery ownership:** `claude-apps-first-value-entry`. This brief specifies
composition and content constraints only; it does not own delivery of the
first-value doors or the route copy.
