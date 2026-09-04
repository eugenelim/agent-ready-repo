---
type: copy-deck
slug: team-orientation-copy-deck
surface: responsive-web
voice_chart: docs/product/voice/agent-ready-repo.md
brand_register: docs/design/copy/brand-register.md
state_matrix: docs/design/screens/team-orientation-flow.md
updated: 2026-09-04
---

# Copy deck — per screen × state

Every string keyed to its cell in the per-screen state matrix. Voice from
`docs/product/voice/agent-ready-repo.md`, derived from the brand register.

## What is deliberately not in this deck

**The marketing headline and subheadline are not here, and no skill writes
them.** `copy-direction` names the goals and stops; `ux-writing` covers product
UI copy states, not positioned marketing copy. Both skills say so explicitly, and
`copy-direction` states that finished marketing copy is drafted directly against
its named goals by a writer.

So the single most important string on the surface has a specification — a
≤10-word contract naming the team's situation before the mechanism, judged
against *Sayable in a meeting* — and no owner in the skill roster.

**Gap J, recorded.** The design thread can fully specify a headline's contract
and cannot produce the headline. For this engagement that is correct and honest:
the hero line should be written by a person against the four copy goals, and the
gate should judge it against the tweet test. It is named so nobody mistakes the
gap for an oversight.

Also excluded: the station-detail zone's cost figures, which must be sourced from
the published guide paths rather than written, and the three proofs' content,
which is generated output rather than copy.

---

## S1 · Marketing home

Matrix: default only.

### default

| Slot | String | Note |
| --- | --- | --- |
| Primary action | **Prove it on your own work** | Verb + object, and the object is the reader's, not ours. Replaces "Try the supervised build loop", which names our mechanism and promises a trial rather than an outcome. |
| Primary action, sub | `pip install agentbundle` | Already exact and already the page's best evidence. Unchanged. |
| Secondary action | **See what adopting this asks of a team** | The lower-commitment route, for the reader who is not the installer. Replaces "Explore use cases", which points at a taxonomy. |
| Friction microcopy | **Installs into one repository. Nothing runs without you. Remove it with one command.** | Answers the actual dominant objection — what this does to my repo, and can I undo it. Three short clauses because a champion has to repeat them. |
| Zone 4 heading | **What changes for a team** | |
| Zone 5 heading | **What happens to one piece of work** | The two headings are the two-lifecycle distinction stated in words as well as in the canvas's axis change. |
| Zone 6 heading | **Where a person decides** | Replaces "Every loop surfaces to you at exactly the right moment", which claims correctness rather than describing. |
| Zone 10 heading | **Roll it out to your team** | |
| Zone 10 action | **Follow the adoption path** | |

### The eleven gate codes, replaced

Each internal identifier becomes the decision a person actually makes. The
right-hand column is what a champion says out loud.

**All eleven, enumerated.** An earlier draft of this table covered nine and still
asserted the count was discharged — cold review caught it.

`HumanGates.astro`, six identifiers on seven cards:

| # | Was | Loop | Becomes |
| --- | --- | --- | --- |
| 1 | G0 | Discovery | **Is this worth exploring?** |
| 2 | G1.5 | Discovery | **Does this shape fit our strategy?** |
| 3 | G2 | Discovery | **Is this brief complete enough to build from?** |
| 4 | G3 | Discovery → Build | **Is this specific enough to spec?** |
| — | Plan | Build | **A spec and plan you approved** — already compliant, no code to remove |
| 5 | G4 | Build | **A pull request you merge** |
| 6 | G5 | Release | **You ratify the production ship** |

`ThreeLoops.astro`, five identifiers:

| # | Was | Where | Becomes |
| --- | --- | --- | --- |
| 7 | G3 | Discovery Loop's human-gate line | **Is this specific enough to spec?** — moves to zone 6 with the card |
| 8 | G4 | Build Loop's human-gate line | **A pull request you merge** — moves to zone 6 |
| 9 | G5 | Release Loop's human-gate line | **You ratify the production ship** — moves to zone 6 |
| 10 | G3 | decorative pipeline chip | **deleted** — the canvas carries the sequence |
| 11 | G4 | decorative pipeline chip | **deleted** — same |

**Eleven identifiers, eleven dispositions, zero remaining.** The zone itself is
absorbed into zone 5, so identifiers 7 through 9 do not need a new home on that
component — their decisions live on zone 6's cards, which is where the seven
questions above are rendered.

The two production-side labels are near-verbatim from the published guide paths,
which is the sourcing rule holding rather than a coincidence.

**Acceptance check:** a count of rendered `G0`/`G1.5`/`G2`/`G3`/`G4`/`G5` strings
on both surfaces, which must be **0**. Baseline 11. This is the check the build
handoff names, and it is mechanical rather than a review opinion.

---

## S2 · Operating-model canvas

Matrix: default, plus error and four rendering states. The three decision labels are adapted from published guide-path copy; the station names and the other five steps are authored — see the composition record for which is which.

### default — the strings inside the graphic

| Slot | String |
| --- | --- |
| Title | **How a team takes this on** |
| Caption | **The common route, in order. Teams skip stations and revisit them, and the spacing shows sequence rather than time.** |
| Stations | Evaluate · Prove it on real work · Win buy-in · Roll out a cohort · Make it the default |
| Enclosure heading | **Prove it on real work** |
| Enclosure sub | **what happens to one piece of work** |
| Scope group, upper | TRAVELS WITH YOU, ACROSS REPOSITORIES |
| Step 1 | A signal arrives |
| Step 2 ◆ | **An outcome you ratified** |
| Step 3 ◆ | **A brief you agreed to build from** |
| Scope group, lower | LIVES IN THIS REPOSITORY |
| Step 4 ◆ | **A spec and plan you approved** |
| Step 5 | Code past the gates and three cold reviews |
| Step 6 ◆ | **A pull request you merge** |
| Step 7 | A deployment validated off production |
| Step 8 ◆ | **You ratify the production ship** |
| Tracker | **Your tracker** · gets a report |
| Tracker terminus | **nothing comes back** |
| Legend | a person decides — some steps carry more than one decision |

**◆ marks the five decision points.** The seven decision questions below map onto
them: two collapse onto step 2 and two onto step 3. The legend says so rather
than letting a reader count and get a different answer from the page.

The caption is required, not decorative. It carries two of the metaphor's stated
limits — that a rail line implies one fixed route, and that even spacing must not
be read as equal duration.

### error — the graphic did not render

No error message. The state resolves to the text alternative, which is present in
the document rather than fetched. An error string here would announce a failure
the reader does not experience.

### narrow viewport, and screen-reader equivalence

The ordered list in the composition record serves both. Its one string that the
drawing does not carry:

> **Your tracker receives a report from this station and sends nothing back —
> there is no path from the tracker into the work.**

A sighted reader gets this from a branch that ends. The text has to say it.

### alt string — the README rendering

Load-bearing, because an SVG loaded through `<img>` exposes no internals and this
is the accessible name:

> **How a team takes this on: five stations — Evaluate, Prove it on real work,
> Win buy-in, Roll out a cohort, Make it the default — with the eight-step work
> sequence nested inside the second station, five of which are points where a
> person decides, and a one-way branch to your tracker.**

**All three of the canvas's accessible names derive from one string.** The visible
title, the SVG's accessible name, and this alt text must all begin "How a team
takes this on" — an earlier draft had three different openings, and the alt string
is the load-bearing one in the README rendering.

### link-preview strings

The observed transfer path. A chat client reads only a small prefix of the page,
so these do more work than the image.

| Slot | String |
| --- | --- |
| Preview title | **Your team's AI-assisted work has no operating model yet** |
| Preview description | **It will not merge its own work, and it will not ship to production without a person saying so. Here is the whole model on one page — and what adopting it asks of a team.** |
| Contextual field | **Read time · <measured>** |

**Reworked after cold review.** The earlier pair led with a category statement —
"the supervised operating model for software teams" — which named no reader
problem, made no claim only this product can make, and would have survived being
pasted onto another company's page unchanged. It failed both painkiller-first and
the specificity check on the one surface the packet establishes as the *only
observed* transfer path.

The replacement leads the title with the recipient's situation and the description
with the two refusals, which are simultaneously the differentiator and the
register's second-ranked goal. A manager who reads only the title and the first
clause has still received the thing that ends a budget-holder meeting.

The read-time field is left as a placeholder because an unmeasured number
violates the fourth copy goal. Measure it or cut the field — see V5.

**Boundary note.** These sit close to positioned marketing copy. They are
included because they are metadata strings keyed to a state, and the content
brief routed them here — but they should be reviewed against
`copy-direction`'s goals rather than only against this deck.

---

## S3 · Guides index

Matrix: default, loading.

### default

| Slot | String |
| --- | --- |
| Start-here heading | **Start here** |
| Start-here promise | **Install it and get one real answer out of it, in under twenty minutes.** — **conditional on build item 3.4** (splitting the on-ramp out of P1). If 3.4 is descoped, this promise is false and must change; today's first path is stated at about an hour. |
| Paths heading | **Follow a path** |
| Paths lede | **A path is an ordered set of guides that ends at a handoff, not at a document.** — existing published copy; unchanged |
| Type entry points | **Learn it by doing it** · **Get a specific thing done** · **Look something up** · **Understand why it works this way** |
| Job groups heading | **Choose what you want to achieve** — existing; unchanged |
| Hierarchy note | **Guides tell you how to do something. Pack reference tells you what a pack contains.** |
| Route to the internal case | **Making the case internally?** |

The four type entry points are named by what the reader accomplishes, never by
the type name. "Tutorials" is our taxonomy; leading with taxonomy is the failure
this engagement exists to fix.

### loading

No string. The layout is preserved and the content arrives. A loading message on
a static page would be noise.

---

## S4 · Path page

Matrix: default, loading, partial.

### default

| Slot | String |
| --- | --- |
| Prerequisite label | **You need first** |
| Audience label | **For** |
| Cost label | **About** |
| First-value label | **You end up with** |
| End-state label | **This path ends at** |
| Hand-over action | **Send this path to someone** |

Labels are front-loaded and scannable. "You end up with" rather than "First
value" — the reader's outcome, not our vocabulary.

### partial — a step is not written yet

| Slot | String |
| --- | --- |
| Step marker | **Not written yet** |
| Path note | **Two of the five steps aren't written yet. The rest of the path works.** |
| Recovery | **See the other paths** |

Blame-free and honest: it names the situation, says what still works, and offers
a way forward. It does not apologise and it does not hide the gap.

### loading

No string.

---

## S5 · Search results

Matrix: empty (two variants), loading, error, default. The one screen with a full
data-state burden.

### empty — first run

| Slot | String |
| --- | --- |
| Placeholder | **Try "install a pack", "run a release", "review a PR"** |
| Orientation | **Search 200-odd guides. Or follow a path below.** |

The placeholder names real queries rather than the word "Search". Each must be
verified against the live index before ship — an example that returns nothing is
worse than a generic placeholder, and that verification is owed.

### empty — no results

| Slot | String |
| --- | --- |
| Statement | **Nothing found for "{query}".** |
| Recovery | **Closest area: {job group}. Or start from one of the six paths.** |

Blame-free: the situation, then two ways forward. Not "no results" as a dead end,
and not "did you mean" without a suggestion.

### loading

| Slot | String |
| --- | --- |
| Skeleton label | **Searching for "{query}"** |

Says what is being answered, not that something is happening.

### error — the index is unreachable

| Slot | String |
| --- | --- |
| Statement | **Search isn't available right now.** |
| Recovery | **Browse by what you want to achieve instead.** |

Names the situation without blaming the reader or the system, and routes to a
navigation that does not depend on the index. Critically, this must never be
rendered as no-results — a slow index reported as "nothing found" teaches readers
to distrust search.

### default

| Slot | String |
| --- | --- |
| Result context | **{job group} · {path}** |
| Count | **{n} results** |

Every result names its containing job group and path. That single string closes
the arrived-from-search-with-no-context edge.

---

## S6 · Internal-case route

Matrix: default only.

| Slot | String |
| --- | --- |
| Heading | **What to hand a budget holder** |
| Refusals heading | **What it will not do on its own** |
| Refusals lede | **No configuration removes these.** |
| Refusal 1 | **It will not merge its own work.** |
| Refusal 2 | **It will not ship to production without a person saying so.** |
| Refusal 3 | **Your tracker never becomes the source of truth. Status does not flow from it into the work.** |
| Share action | **Share this page** |
| Proofs heading | **Things you can check** |

The refusals are the screen's substance and its dominant copy goal. Three short declaratives because a champion has to say them from memory, and each is a falsifiable claim rather than a reassurance.

**One correction found in cold review, and it matters.** An earlier draft of refusal 3 read *"It will not write status back into your tracker."* That is **false**. `guides/_shared/how-to/choose-a-tracker-integration.md` and `guides/atlassian/README.md` both record a narrow **confirmed coordination write-back** path to Jira, where every remote mutation needs its own fresh confirmation. The real invariant is directional, not a prohibition on writing: the repository holds truth, and status does not flow *from* the tracker *into* the work. The corrected line states that. The canvas's own "receives a report · sends nothing back" was already correct — the copy had reversed it.

**Consequence for "No configuration removes these."** It holds for refusals 1 and 2 — the production gate is documented as having no configuration, mode, or flag that removes it. It must not be read as covering refusal 3, which is a statement about direction of authority rather than about an absent capability.

---

## Content checklist

Run over every string above.

| Check | Result |
| --- | --- |
| Voice-consistent with the chart | Pass. Calm, plain, serious, deferential throughout. |
| Blame-free | Pass. No error string faults the reader; the no-results and index-error states both state the situation and route onward. |
| Actionable | Pass. Every error and empty state carries a next step. One deliberate exception — the canvas's error state has no string because it resolves to content already present. |
| Concise | Pass, with one flag: the friction microcopy is three clauses. Kept because each answers a distinct part of the objection and a champion needs all three. |
| Terminology-consistent | Pass. The nine terms in the chart are used identically across all six screens. Verified by reading the deck against the table rather than by assumption. |
| No gate codes | Pass. Zero internal identifiers in any adopter-facing string. |

## Open questions

- **Who writes the headline?** Gap J above. It has a contract and no owner.
- **Who defines "pack" in plain words, and where?** Carried unresolved from the
  register and the copy direction. It is in navigation on both surfaces and the
  plain-language floor bars it until defined.
- **Do the three placeholder queries return results?** Must be checked against
  the live index, not assumed.
- **Is "Read time · 4 minutes" honest?** It is an estimate, and the register's
  fourth goal says a number appears only where a reader could check it. Either
  measure it or cut it.

---

## Appendix — headline candidates, as gate input only

**Why this exists and what it is not.** Gap J stands: no skill in the roster
writes positioned marketing copy, and this appendix does not close that gap. But
cold review was right that the gate cannot judge a hero line against the tweet
test while being handed nothing, and that two of four editorial gates were left
unresolvable as a result. So these are **candidates for the owner to choose from
or reject**, drafted against the contract, not a deck entry and not a skill's
output.

The contract: ≤10 words, names the team's situation before any mechanism,
IC-first, judged against *Sayable in a meeting*.

| | Candidate | Words |
| --- | --- | --- |
| **A** | Your team has agents. It doesn't have an operating model. | 10 |
| **B** | Every engineer is using AI. Nobody agreed how. | 8 |
| **C** | Your agents ship code. Who approved it? | 7 |

Scored against the four tests the structure document left open:

| Test | A | B | C |
| --- | --- | --- | --- |
| Tweet test — stands alone | pass | pass | pass |
| Five-second: who is it for | pass — "your team" | implied | implied |
| Painkiller-first | pass | **strongest** | pass |
| Specificity — survives being pasted elsewhere? | **weakest** — an AI-governance vendor could use it | pass | **strongest** — names the actual gap |
| Sayable in a meeting | pass | **strongest** | pass |

**The trade-off the owner should see, because it is not a matter of taste.**
Candidate C is the sharpest and most specific line, and it foregrounds the
**work** lifecycle — the one the approved dominance decision deliberately
subordinates. Choosing it would put the page's first sentence and its
centrepiece in tension. Candidate A is the only one that names a *team* and an
*operating model*, which is what the canvas then shows, at the cost of being the
least specific. B sits between them and leans hardest on the subheadline to say
what the product is.

**Recommendation: A**, on the grounds that the page's action goal is
Understanding and its primary reader's job is transfer — so the headline's job is
to name the thing the canvas is about, not to win the sharpest exchange. C is the
better line and the worse headline for this page.

None of the three is verified against a reader. The explain-it-back baseline and
the champion interview are still owed.
