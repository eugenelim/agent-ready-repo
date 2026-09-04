---
type: customer-journey
slug: team-orientation-future-state
persona: adoption-champion
outcome: my-team-runs-this-by-default
surface: cross-platform
genre: crossing — marketing (acquisition) into documentation
state: future
evidence-level: assumption-based
evidence_note: >-
  A future-state map is a hypothesis by construction. Tagged assumption-based
  without qualification. Where an observed behaviour constrains the design it is
  marked [observed] inline and cited to the 14-day traffic window
  2026-08-21 to 2026-09-03. Where independent research supports a mechanism it is
  marked [researched] and cited to docs/design/discovery/team-orientation-peer-audit.md.
  Validation hooks are named per stage; this map is not a plan of record until
  they fire.
gate_approved: approve-journey, 2026-09-04
updated: 2026-09-04
---

# Journey: future state — the champion makes it the team's default

**Why this map is cross-surface when the two current-state maps are not.**
`journey-mapping` takes one surface and one genre, and Discover ran it twice
because the two surfaces fail separately today. In the future state they
cooperate, and the crossing is the thing being designed. Splitting the future
state per surface would hide the only property that matters. So this map is
declared `surface: cross-platform` and spans both, with each stage naming which
surface serves it. That is the second manual handling of Gap B, and the seam
artifact's four crossing invariants are the acceptance criteria for it.

**Persona:** The adoption champion, unchanged from Discover. Primary because they
are the only reader who has to carry the other three — the engineer, the platform
lead, and the budget holder.

**Outcome:** Their team runs this by default, and the champion is no longer the
only person who can explain it.

**Trigger:** Unchanged, and mostly not the marketing page. A link pasted into a
work chat, a search result, a package page, or the README. `[observed]` — the
README drew 68 unique readers to the published site's 6 outbound referrals, and
a repository link pasted into Microsoft Teams drew 12.

**End state:** Engineers open sessions with `workspace status` without being
told. The champion's understanding exists in an artifact rather than only in
their head.

**Stage spine.** The five stages are the adoption lifecycle, in the order the
approved dominance decision fixed. They deliberately mirror the canvas's five
stations, so the journey and the artifact cannot drift apart.

---

## Stage 1: Evaluate `[assumption-based]`

**Surface:** marketing home, above the fold.

| Row | Content |
|-----|---------|
| **Actions** | Arrives cold. Sees the whole operating model at low resolution in one screen, with the reader named. Recognises that this is about how a team works, not a command to run. Reads one sentence about the problem. Decides whether to keep going. |
| **Emotions** | Oriented, then interested. Neutral to positive. The relief of a page that shows its shape before it asks for anything. |
| **Pains addressed** | "It says it's a build loop and I don't know what that is." "I now know there are packs and I still don't know what happens to my team." |
| **Residual pain** | The model is genuinely large. A reader in a hurry still leaves knowing only that it is coherent, not what it contains. That is an acceptable outcome for five seconds and is the reason the canvas has a second level rather than more density in the first. |

**What is new.** The canvas replaces the hero's single mechanism claim. The
problem statement moves above the outcome router, so the reason precedes the
menu. The three self-reported numbers are re-tasked into something a skeptic can
check.

**Validation hook.** Five-second scan: can a first-time reader answer *what is
this / who is it for / should I care* from the visible content alone? All three
must be answerable. The baseline is that two of the three are currently absent.

## Stage 2: Prove on real work `[assumption-based]` — **the nested station**

**Surface:** marketing home, canvas second level, then install.

| Row | Content |
|-----|---------|
| **Actions** | Opens the one station that has detail inside it and follows what happens to a single piece of work: a signal becomes an intent, an intent becomes a human-approved spec and plan, code passes mechanical gates and three cold reviews, a person merges the pull request, a throwaway environment validates the deployment, and a person ratifies the production ship. Sees where their tracker attaches and that nothing comes back from it. Copies the install command. Runs it on a real pending task, not a toy. |
| **Emotions** | Convinced, in the specific way engineers get convinced. Positive. This is where a claim becomes a mechanism. |
| **Pains addressed** | "There are three loops and seven gates and I can't tell which gate belongs to which loop." "I can install it. I still can't explain it." |
| **Residual pain** | The work lifecycle has eight steps and a five-second reader will not absorb them. It is not meant to be absorbed here — it is meant to be *available* here and absorbable in the documentation paths. |

**Why the work lifecycle lives inside this station and nowhere else.** It is the
evidence for the adoption claim, not a second narrative. Nesting is also the
disclosure ceiling: `[researched]` NN/g finds designs beyond two disclosure
levels typically unusable because readers get lost between them. Adoption spine
plus this one nested detail is exactly two.

**The platform lead's question gets answered here.** *Does this write back to
Jira?* The tracker is drawn as a one-way outbound leaf with no return edge, so
the answer is readable from the geometry. Shaping travels with the person across
repositories; build and release belong to the repository — a property of this
station, drawn here rather than restated as a third diagram.

**Validation hook.** Explain-it-back question 4: *if your team uses Jira or
Linear, which one is the source of truth?* A reader who cannot answer this has
not received the one-way property, and the geometry has failed.

## Stage 3: Win buy-in `[assumption-based]` — **the stage with no current surface**

**Surface:** marketing home, and the artifact the champion takes away.

| Row | Content |
|-----|---------|
| **Actions** | Needs to convince a budget holder. Takes the canvas — the same artifact, not a summary they rebuild — and pastes a link into a work chat or drops the image into a document. The link explains itself before anyone clicks. In the room, they trace the five stations, name the costs, and answer the question that ends most of these meetings: what does this refuse to do on its own. |
| **Emotions** | Prepared. Positive, and this is the largest single change in the journey. The champion stops improvising. |
| **Pains addressed** | "I've done three live demos and every one felt like I was improvising." "There is no single artifact I can hand to a budget holder." "Decision makers want to see it on our code, not a toy example." |
| **Residual pain** | The canvas cannot show the budget holder the model running on *their* code. Only the champion's own Stage 2 run does that, which is why Stage 2 must precede Stage 3 rather than being optional. |

**What makes this stage work is a constraint, not a feature.** `[observed]` a chat-client referral path carries real traffic — twelve unique visitors in a fortnight; the attribution of that path to champion transfer is an assumption, not an observation. `[researched]` Slack fetches only 32 kB of a
page, so `og:title` and `og:description` are the payload that does the work and
the image is secondary; SVG is not a valid preview image on any major platform,
so a raster export is required. `[researched]` GitHub's Markdown sanitiser strips
`<style>` blocks, `class`, `id`, `<script>`, and all animation, so the canvas's
meaning must live in element-level attributes.

**The open tension, carried forward honestly.** `[researched]` practitioner
sales-enablement literature holds that generic collateral fails and each
stakeholder needs different proof types. Our decision is one canvas with four
entry points, on the reasoning that the canvas is the shared *model* while the
per-audience answers are entry points into it rather than separate collateral.
That reconciliation is plausible and untested, and every source arguing the other
way has a client-acquisition incentive. It is an open question at the next gate,
not a settled point.

**Validation hook.** Explain-it-back question 5: *what does this system refuse to
do on its own, no matter how it is configured?* This is the budget holder's
decisive question and no current surface answers it.

## Stage 4: Roll out a cohort `[assumption-based]`

**Surface:** the documentation guides index and its ordered paths.

| Row | Content |
|-----|---------|
| **Actions** | Follows the route from marketing into the ordered paths — which exists now, where today there is nothing. Lands on an index that leads with one "Start here" and one promise. Picks a path for someone else: the platform team gets the adopt-the-catalogue path, an engineer gets the build path. Hands over a named, time-costed sequence rather than a folder. |
| **Emotions** | Capable, and slightly surprised at how ready it was. Positive. |
| **Pains addressed** | "I know there are guides and I can't get to them from the page that told me about them." "The nav wants me to pick a pack — I don't know which pack my problem is in." "Every engineer asks the same setup questions I already answered." "The platform team wants a rollout plan and I don't have one." |
| **Residual pain** | The first path costs about an hour, which is three times the twenty-minute budget a first-value tutorial should carry. Splitting a short on-ramp out of it is a documentation-design decision, not a journey one. |

**What is new.** A route from marketing into the paths. The paths promoted above
the pack-choosing copy. Search raised to a first-class element, because 207 guide
files plus 22 pack pages is roughly 229 published pages and that is the
search-first tier. The sidebar re-grouped by job rather than by pack — approved at
the gate **with a route-migration table owed**, since this changes destinations
for 21 groups and principle 3 permits that only as a deliberate amendment.

`[researched]` This stage is where the independent evidence is strongest: usage
clusters *within* teams, indicating collective sensemaking, and peer usage in the
skip-level peer group raised the odds of trying a tool by 216 percent. Champions'
measured contribution is step-by-step contextualisation into team-specific
workflows, not demonstration. The documentation paths are the contextualisation
made portable.

**Validation hook.** Can a platform lead who has never spoken to the champion
complete the adopt path from the index alone? If not, the champion is still the
dependency.

## Stage 5: Make it the default `[assumption-based]`

**Surface:** documentation, and the route back out to the internal case.

| Row | Content |
|-----|---------|
| **Actions** | Engineers open sessions with `workspace status` unprompted. New joiners are onboarded to the path, not to the champion. When the champion needs to renew the internal case — a second team, a budget cycle — they go from "I understand this" back to "help me sell this", which is a route that exists now. |
| **Emotions** | Unremarkable, which is the goal. Neutral and stable. Adoption has stopped being a project. |
| **Pains addressed** | "It works when I know what spec to run. When I don't, I go back to winging it." "New engineers discover `workspace status` weeks in." "I know where everything is and nobody I onboard does." |
| **Residual pain** | `[researched]` reversion under deadline pressure — the Productivity Pressure Paradox — is an organisational condition, not a page defect. No surface fixes it. Naming it in the rollout path is the most either surface can do. |

**The failure mode this stage is designed against.** `[researched]` the champion
is a single point of failure, and the documented mitigations are procedural and
admittedly weak; no post-mortem of a cohort adoption lost this way was found,
which is a survivorship gap rather than absence. Making mastery transferable is
the structural mitigation available to a documentation surface, and it is exactly
what current-state Stage 5 says is missing.

**Validation hook.** Explain-it-back, administered to somebody the champion
onboarded rather than to the champion. If only the champion can pass it, Stage 5
has not happened.

---

## Frontstage actions

- **Action:** see-the-whole-model-in-one-screen
- **Action:** read-the-reason-before-the-menu
- **Action:** open-the-nested-work-detail
- **Action:** trace-one-piece-of-work-end-to-end
- **Action:** see-where-the-tracker-attaches
- **Action:** copy-the-install-command
- **Action:** run-it-on-real-pending-work
- **Action:** paste-the-canvas-link-into-work-chat
- **Action:** trace-the-stations-for-a-budget-holder
- **Action:** answer-what-it-refuses-to-do
- **Action:** follow-the-route-into-the-paths
- **Action:** pick-a-path-for-someone-else
- **Action:** hand-over-a-named-sequence
- **Action:** onboard-a-joiner-to-the-path
- **Action:** return-to-the-internal-case

---

## Emotional arc

The current-state arc dips hardest where the page tries to explain the model and
recovers only where it stops explaining and offers a command. The future-state
arc inverts that: explanation becomes the strongest moment.

Lowest point: Stage 1, and only mildly — a reader in a hurry still leaves with
shape rather than content. That is the designed cost of the two-level ceiling.

Highest point: Stage 3, win buy-in. It is the current journey's worst moment and
the one stage no surface serves today, which is why it carries the largest
designed change and the largest risk.

Peak-end reasoning puts the design weight on Stage 3 first and Stage 1 second.
Stages 4 and 5 are largely promotion and re-grouping of content that already
exists and already works.

---

## What this map does not claim

It is `assumption-based`. Every emotion above is designed intent, not observed
behaviour. Three specific things could falsify it:

1. **If the champion interview shows the real blocker is commercial** — pricing,
   procurement, security review — rather than explanatory, then Stage 3's design
   is answering the wrong question and the canvas is secondary.
2. **If one canvas cannot serve four audiences**, the practitioner literature on
   per-stakeholder collateral is right and Stage 3 needs four artifacts.
3. **If the two lifecycles are not genuinely orthogonal**, Stripe's
   collapse-the-duality route is better evidenced than subordination and the
   whole spine is wrong.

None is settled. All three are recorded in the decision log.

---

## Handoff notes

**For `information-architecture`:** the five stations are the marketing spine.
They are **not** the source of the documentation job groups — an earlier draft
said they were and that was wrong. The sidebar groups by the seven existing job
names, which already appear on both surfaces. Crossing invariant 1 covers the
work-lifecycle decision phrasings and those seven job names; the five stations
are marketing-side only.

**For `content-design`:** Stage 1 owns the above-the-fold message; Stage 3 owns
the message that has to survive being pasted into a chat window. Those are
different jobs for the same artifact.

**For `user-flow`:** the canvas is one screen with two levels and six states.
Stage 3's actions impose the static constraint; Stage 2's impose the nesting.

**For `conversion-design`:** the commitment this page should earn is the Stage 3
cohort decision, not the Stage 2 individual install. The current primary action
optimises for the latter.

**For `documentation-design`:** Stages 4 and 5. The content exists; the wayfinding
does not.

**For the measurement plan:** every validation hook above is a candidate measure,
and `[researched]` adoption predictors are not retention predictors — so Stage 1
through 3 and Stage 4 through 5 need separate instruments rather than one funnel.
