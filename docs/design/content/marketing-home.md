---
type: content-brief
surface-type: acquisition
communication_mode: product-copy
persona: adoption-champion — docs/design/discovery/team-orientation-personas.md
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

**One deliberate adaptation.** In the standard arc the hero is the reader. Here
the reader is a hero who must go on to guide three other people. So the arc's
"plan" element does double duty: it is both the champion's plan and the thing
they hand over. That is why the plan section is the adoption arc rather than a
list of steps to install.

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
