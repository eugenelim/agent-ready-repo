# Prose discipline

Advisory guidance, never a gate. Nothing here is checked, scored, or counted,
and no completion gate reads it. That is deliberate: the property is a
judgement over prose whose author chose the wording, which
[`spec-authoring-rubric.md`](spec-authoring-rubric.md) class 6 says to ship as
advice or convert to a mechanical proxy, never to gate on. Treat every item
below as a prompt to look again at one sentence, not a rule to comply with.

**What this does not cover.** The managed output-rendering block near the top
of this skill's `SKILL.md` already owns the *form* rules — lead with the useful
outcome, one fact per sentence, bullets for separate items, short resumable
sections, no repeated summary. Work those from there. This reference covers
only what the block does not: how to notice that a passage reads as generated,
and what to do about it.

Use it on your own draft, before review. Handed to a reviewer it becomes a
source of nits, which is the cost it exists to reduce.

## The signal-word scan

Each word below earns one question: **is it carrying a specific meaning, or
standing in for a claim I have not made?** If it is standing in, replace it
with the claim.

These are the words contract prose attracts. A marketing-copy list — `unlock`,
`best-in-class`, `game-changing` — scans clean against a spec and tells you
nothing.

| Kind | Words |
| --- | --- |
| Inflation | `robust`, `comprehensive`, `seamless`, `powerful`, `rich`, `first-class`, `elegant` |
| Hedging | `should generally`, `typically`, `in most cases`, `as appropriate`, `where possible` |
| Filler verbs | `leverage`, `utilise`, `facilitate`, `enable`, `ensure that`, `serve to` |
| Throat-clearing | `it is worth noting`, `it is important to`, `note that`, `in order to`, `simply`, `just`, `of course` |
| Empty intensifier | `significantly`, `dramatically`, `fundamentally`, `critically`, `truly` |

A word on this list is not banned. `robust` is the right word in "robust
against a truncated read"; it is filler in "a robust implementation". The scan
asks which one you wrote.

## The structural tells

Shapes, not words. Each is a sentence pattern that arrives when prose is being
produced rather than decided:

- **`not just X, but Y`** and its variants — `isn't merely A, it's B`,
  `more than a C — it's a D`. The construction promises a distinction and
  usually delivers a synonym.
- **The reflexive triad.** Three bullets, three adjectives, three examples,
  where the third exists because the pattern wanted a third. Ask what the last
  member adds; if nothing, there were two.
- **The framing opener** — `Let's be clear:`, `At its core,`,
  `The key insight here is`. It announces significance instead of stating
  something significant.
- **The echo close.** A paragraph whose last sentence restates its first. The
  reader has just read it. (Section-level repetition is the managed block's
  `no repeated summary`, not this list's.)
- **The interchangeable sentence.** A sentence that would sit equally well in
  any other spec in the repository. It is describing a category, not this work.
- **Balanced-clause padding** — `X while also Y`, `both A and B`, `not only P
  but also Q` — where the second half is the first half restated.

## Restructure, do not word-swap

This is the repair, and it is the item most often got wrong.

Swapping `leverage` for `use` leaves a generated sentence generated: the
problem was rarely the word. Consider *"This approach leverages the existing
validation layer to ensure that malformed input is handled robustly."*
Word-swapped, it becomes *"This approach uses the existing validation layer to
make sure malformed input is handled well"* — which is the same sentence, still
saying nothing a reader can act on.

Restructured, it becomes *"Malformed input is rejected by `validate_payload`
before it reaches the parser."* Named subject, named mechanism, an outcome a
test can observe. The sentence is shorter because the vagueness went, not
because words were traded.

So when the scan or a tell fires, ask what the sentence is *for*, and write
that. If the honest answer is "nothing the reader needs", the repair is
deletion. A passage that resists restructuring is usually a passage with no
content, and cutting it is the correct outcome rather than a
shortfall in rewriting.

**One carve-out.** None of this licenses shortening a comparison value. A byte
layout, an exact key order, an enumerated channel set, a stated bar — these
stay long, and they stay exact. The root `AGENTS.md` already says a readability
score is a clue and never a reason to cut needed facts; that applies here
first, because a criterion is the one place where length is load-bearing.

## The distinctiveness test

Two questions over the finished draft.

**Could this section be pasted into another spec in this repository with only
the nouns changed?** If yes, it is describing the genre rather than the work.
Rewrite until it could not.

**Does a specific person who understands this system sound like they wrote
it?** A spec authored by someone who made decisions reads differently from one
that explains a category: it names the thing that was hard, says which option
lost, and states a constraint that cost something. Prose with no such marks is
usually prose where no decision was recorded.
