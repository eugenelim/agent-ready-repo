# Owner decisions

Recorded so the amendment that follows cites a repository reference rather than a
conversation.

## 2026-09-13 — expand the response set from eight to ten

**Decided by:** eugenelim, scope owner.

The eight answers to a sustained finding name no move for a finding whose target
is prose rather than contract. Two moves are added.

### `demote-the-claim`

The obligation is real but has no machine: its only check is that a sentence
exists. It moves to the surface that owns it and is protected by a content pin
instead of a checkbox.

**Demotion always changes home**: an obligation leaves the contract and lands in
working material. There are no tiers. An earlier draft carved out a free
"working material" tier, which was incoherent — if the target was never contract
there is nothing to demote, and the answer is an ordinary in-place correction to
working material, which needed no new response and which the adjudicator already
caps at advisory.

So demotion always removes an accepted obligation, and therefore always needs
owner authority through the amendment path. It blocks until granted. That is
correct behaviour, not a defect to design around.

**The pin lands in the same change that removes the criterion.** Demotion without
its protection is deletion, and the requirement is checkable.

### `drop-the-claim`

The claim should not exist. Nothing is obliged by it, and removing it changes
nothing about the accepted outcome. The test is the spec's Objective: a claim
serving no stated outcome is decoration whether or not it is true.

Distinct from `cut-the-item`, which removes the thing the finding is about, and
from `narrow-the-claim`, which reduces a claim's reach. Here the claim is deleted
and the surrounding obligation is untouched.

## 2026-09-13 — order the set cut-first

**Decided by:** eugenelim, scope owner.

The responses are grouped into four axes and stated in this order:

| # | Axis | Responses |
| --- | --- | --- |
| 1 | Cut | `drop-the-claim`, `cut-the-item`, `demote-the-claim`, `narrow-the-claim` |
| 2 | Route | `route-to-owner`, `bound-out-of-scope` |
| 3 | Fix | `repair-the-generator`, `repair-the-artifact` |
| 4 | Hold | `dismiss-and-re-present`, `accept-as-proportionate` |

Ordering is not an efficiency claim. It is the same philosophy the repository
already applies to code changes — cut before adding, take the first sufficient
option and stop, whose first rung is skipping an addition that is not genuinely
needed. A response set that led with repair contradicted the rule the rest of the
repository follows.

`narrow-the-claim` joins the cut axis because it is a reduction. Grouping it with
repair is part of why it gets reached for when the situation calls for dropping a
claim outright.

**The order is a stop rule, not a preference.** Take the first response that
applies and stop; do not evaluate the rest. If the claim is not needed, drop it
and the answer is complete — its reach, its owner, its generator and its wording
are all questions about a claim that will not exist.

That is where the ordering pays for itself. Rung 1 is cheap to test: does any
stated outcome depend on this? Everything below it is expensive — tracing a
check's reach, resolving an existing owner, locating a generator. Spending that
analysis on a claim about to be deleted is the waste, and answering findings
against unnecessary prose by rewording it is what makes review rounds run long
without converging.

Repair sits in the third axis rather than last. Displacing it as the default is
the point of the reordering; making an author walk nine options before a
determined contract-tier contradiction is not.

### Why the set was incomplete

Every prior response either edits the artifact, moves ownership, or holds. None
lets the contract shrink, so a review round could only add or hold. That is the
mechanism behind non-converging rounds: a finding against unnecessary prose could
only be answered by writing more careful prose.

### Trigger, and the link to repair origin

The canonical trigger is a finding marked `prior-round-repair` against an
obligation that is still contract but whose only check is that a sentence exists.
The existing origin rule already says such a finding means the repair became the
defect source; until now the response set offered nothing but another repair, so
the answer was always to reword the sentence the next round would find again.

A `prior-round-repair` finding against material that is *already* working
material is not a demotion trigger — there is nothing to demote. It is an
ordinary in-place correction, and the origin mark's value there is telling the
author to stop rewording and consider `drop-the-claim` instead.

## 2026-09-13 — every answer walks its surfaces, and the direction differs

**Decided by:** eugenelim, scope owner.

Traversal is not a repair concern. Every answer leaves surfaces behind; what
changes per axis is which way the walk runs.

| Axis | Direction | What the walk asks |
| --- | --- | --- |
| Cut | backwards | What referenced the thing that no longer exists? |
| Route | outwards, then back | Does the owner cover the whole claim, and what still states it locally? |
| Fix | sideways | What else asserts this, describes it, or pins it? |
| Hold | forwards | Who must see this decision next round for it not to recur? |

**Cut walks backwards, and reaches furthest.** Removing a node orphans every edge
into it: the tasks that implement a criterion, the tests that assert it, the
design prose that explains it, the durable-output row that owns it, the follow-on
that references it, and any pin over its text. This spec cut one criterion and
still shipped a dangling reference that review had to find.

`drop-the-claim` walks the same way at assertion granularity: an assertion dropped
in one place and left standing in another is the exact defect this spec produced
with a count removed from a spec while it survived in a shipped reference.

`narrow-the-claim` walks backwards too, and is the easiest to under-walk, because
nothing is deleted — everything that restated or relied on the old reach is still
present and still reads plausibly.

**Route walks outwards then back.** First confirm the named owner actually covers
the whole claim rather than most of it; a partial owner leaves an unowned
remainder. Then remove what still states it locally, or routing has created the
second home for one rule that the repository forbids.

**Hold walks forwards.** A dismissal or an acceptance is worthless where the next
round cannot see it. This is recorded upstream as an observed failure: the same
finding recurring across rounds on different grounds because a stateless reviewer
cannot know an earlier verdict was taken. The walk for a hold answer is therefore
about reachability rather than cleanup — the reason has to land where the next
adjudication reads.

## 2026-09-13 — the fix axis resolves its surfaces before it repairs

**Decided by:** eugenelim, scope owner.

Before repairing, walk the surfaces the repair reaches. Repair them in one
action. A reviewer cites the instance it happened to look at; repairing only that
leaves the class, and the next round finds what was left.

**A walk, not a flat sweep.** Two reasons, and both are failures this spec's own
history produced.

*Follow relationships, not strings.* A companion statement usually paraphrases
rather than quotes. A narrowed criterion left a design paragraph describing the
behaviour before the narrowing; it shared no token with the new wording, so no
search for the new text could find it, and a search for the old text only works
for someone who still remembers the old wording. The edges to follow are the ones
the repository already carries: a criterion to the tasks that implement it, a task
to the tests that assert it, an artifact to the pins over it, a claim to the prose
that explains it.

*The frontier reopens.* Each repair is itself a change with its own surfaces. A
criterion is narrowed, so its design prose moves; the moved design prose changes
what a task's `Tests` should assert; the changed assertion may sit under a pin.
One pass closes none of that. Walk until the frontier is empty, not until the
obvious places are checked.

Four orders, which are the first frontier rather than the whole walk:

1. **The cited location.** What the finding names.
2. **Every other instance of the same claim.** The class, not the instance. A
   sweep, not a reading.
3. **Companion statements that describe it** — design prose, task text,
   docstrings, guide pages, a header naming a set the artifact no longer has.
   These are not copies of the claim; they are assertions *about* it, and they go
   stale silently because nothing reads them.
4. **Anything that pins any of those** — a content assertion, a hash, a name-set
   or count pin. This order is the one that turns a prose edit into a red gate in
   a file the author never opened. The repository already applies this discipline
   to code before implementation begins; the same sweep belongs to a repair
   decided during review.

**Where the walk ends, and what it cannot reach.** It terminates on an empty
frontier. A paraphrase with no structural edge to anything changed is reachable
only by reading, which is why the walk reduces companion drift rather than
eliminating it — and why a round that still finds one is not evidence the walk was
skipped.

**The enumeration feeds back into the ladder.** If a claim turns out to live on
many surfaces, that is evidence against repairing it: a claim with many homes has
no owner, and the answer is more likely `repair-the-generator` when one source
emits them all, or `drop-the-claim` when nothing is obliged by any of them. Doing
the sweep first is therefore not overhead on the repair — it is what tells you
whether repair was the right rung.

### Why this is on the fix axis rather than left to care

Three repairs in this spec's own history left a companion behind: a narrowed
criterion whose design prose still described the pre-narrowing behaviour, a
two-artifact requirement whose task still read one, and a count removed from a
spec while it stayed in a shipped reference under a test that pinned it. Each was
found by the next review round, and each round spent on rediscovering them is a
round not spent on the artifact.

The three divide exactly along the walk-versus-sweep line. The count was found by
a flat text search, because the token was literal. The other two shared no token
with their repairs and were found only by a reviewer reading the neighbouring
prose — which is the work the walk is meant to do first.

## What a demotion records

Four facts, carried in the `reason` beside the `response`:

- the destination surface that now owns the obligation;
- the pin that will catch its removal;
- the owner authority that permits removing the obligation from the contract;
- why the target is prose no gate consumes, or which prior repair became the
  defect source.

## Demotion blocks, and that is correct

An earlier statement that demotion never blocks was wrong and is corrected here.
Demotion removes an accepted obligation, so it stays `unresolved` until the
owner-authorized amendment lands — which is what an unremoved obligation should
be. There is no pending-relocation state to invent.

## Telling the cut-axis answers apart

Each has one decision predicate, and they do not overlap:

- `drop-the-claim` — removes an assertion nothing is obliged by. The surrounding
  obligation is untouched, and no stated outcome depends on the assertion. It
  operates on an assertion, not a sentence or an item: one sentence can carry
  several, and only the unnecessary ones go.

  Worked example, from this spec's own review. The verdict reference said the
  `response` value is "one of the **eight** answers". That sentence asserts two
  things — that the value is one of the stated answers, and that there are eight.
  Only the first is obliged by anything. Repair was available and easy, changing
  eight to ten; drop is correct anyway, because a count nothing reads is true
  today and false at the next amendment, and must be maintained forever to stay
  true. **When both repair and drop apply, drop wins for that reason.**
- `cut-the-item` — removes the obligation itself: the criterion, scope item, or
  demanded artifact the finding is about stops existing.
- `demote-the-claim` — the obligation survives but stops being contract, because
  its only check is that a sentence exists. It leaves the criterion set for
  working material and gains a content pin. **Inapplicable when an adequate owner
  already exists** — that case is `route-to-owner`, and demoting instead would
  create a second home for one rule, which the repository forbids. Also
  inapplicable when the target was never contract: correcting working material in
  place is an ordinary repair and needs no ceremony.
- `narrow-the-claim` — the obligation stays contract and stays where it is; only
  its stated reach shrinks to what a check can reach.

The pair that is easiest to confuse is demotion and narrowing, and one question
separates them: **should this still be an obligation a completion gate reads?**
If yes and only its reach is wrong, narrow. If no, demote.
