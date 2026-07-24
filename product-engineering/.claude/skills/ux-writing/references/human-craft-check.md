# Human-craft check — structural and vocabulary tells

Machine-made copy fails at two levels: shape and word choice. Structural tells
survive a vocabulary pass because they are pattern problems, not term problems.
Vocabulary tells survive a structural pass because each sentence looks fine in
isolation. Catching both requires two separate sweeps.

Run this check on longer copy: onboarding text, empty-state explanations, feature
descriptions, help text. Short strings — button labels, single-line error messages —
are caught by the items in `content-checklist.md`; this check is for the paragraphs.

*The equivalent checklist for documentation prose is `clear-prose.md` in the
`new-guide` skill. The vocabulary and structural tells overlap — the context
(product UI copy vs. docs) differs, not the patterns.*

## Structural tells

- **Treadmill effect.** Each sentence restates the previous one rather than
  advancing. The copy circles an idea without arriving anywhere. Fix: read the first
  and last sentence of each paragraph — the last should move past the first, not
  echo it.

- **Symmetrical lists.** Bullet items of identical length, parallel construction,
  and equal weight — as if generated to fill a template rather than to capture
  genuinely distinct points. A real list of three features is rarely three identical
  sentences. Vary length and depth to match the actual shape of the content.

- **False precision.** Authoritative framing — "research shows", "studies indicate"
  — without a grounded specific behind it. If you can't name the study, the finding,
  or the number, replace the framing with a concrete claim or cut it.

- **Performative thoroughness.** Seven benefit bullets when two drive the decision.
  The extra five exist to signal completeness, not to inform. Cut the padding; leave
  the two that matter.

- **Nice-nice wrap.** Both sides of a tension hedged to avoid commitment — the copy
  names a tradeoff but refuses to land on a position. A reader should be able to
  disagree with a claim in your copy. If there's nothing to push back on, there's
  nothing being said.

- **Subtext vacuum.** Flat, safe-for-any-audience prose with no implied reader.
  Human writing carries a register — a sense of who it's for and what they already
  know. Copy written for everyone reads as copy written for no one.

## Four-question self-check

Run these on any copy longer than a sentence to catch structural tells a word-level
pass will miss:

1. Does the argument advance sentence to sentence, or restate?
2. Does each list item earn its slot, or pad?
3. Is there a position the copy can be disagreed with?
4. Is any specific detail grounded — a name, a date, a count, an observation —
   or is specificity only performed?

## Vocabulary tells

These survive the structural check because each sentence looks fine in isolation.
They flag to any reader who's encountered a lot of generated output. They share
one defect: they gesture at a concept without carrying it.

**Hollow verbs:** leverage, harness, foster, streamline, empower, underscore,
elevate, unleash. Replace with the actual action. "Lets you connect" not "empowers
you to connect"; "maps" not "streamlines the process of mapping".

**Inflated adjectives:** seamless, robust, cutting-edge, pivotal, transformative,
unprecedented. They reach for authority without earning it. Replace with a specific
quality. "Works without a separate login" not "seamless integration"; "handles a
thousand rows without slowing" not "robust performance".

**Abstract container nouns:** ecosystem, landscape, realm, tapestry, paradigm.
These name the category a thing belongs to instead of naming the thing. Name the
thing. "The skills directory" not "the skills ecosystem"; "how the agents hand off
work" not "the agentic landscape".

**Hedging openers:** "It is important to note that", "It is worth remembering",
"Generally speaking". These delay the claim. Cut the opener; start with the claim.

**Em-dash overuse.** One em-dash per paragraph is punctuation. A pattern of them
in every sentence is a tell. Reach for a period or a comma first; keep the dash
for the break that earns it.

## Editorial methodology

Three passes, run in order. Each catches what the previous misses.

**Pass 1 — vocabulary scan.** Search for the flagged terms above and replace each
with the concrete word it's standing in for. If the replacement doesn't come, the
claim isn't grounded enough to make.

**Pass 2 — delete the opening.** Cut the first paragraph of each section, or the
first sentence of a short block. Generated copy front-loads context that delays the
real point. The writing almost always starts better at the second paragraph. Restore
only when removing it loses something specific: a named constraint, a reference, an
orienting fact.

**Pass 3 — specificity audit.** Run the False-precision tell as a dedicated sweep:
every broad claim gets a grounding detail or becomes a direct claim. If it can't be
grounded, cut it.

## Voice authenticity tests

Run these after the three passes. A "no" is a rewrite.

- **Pub test.** Read the sentence aloud. Would you say this to a person in
  conversation? If the phrasing would make someone glance at you sideways, rewrite
  it.

- **Founder test.** Would the person who built this product actually say this
  sentence? Not "would they approve it" — would they *say* it? Inflated product
  descriptions almost always fail this test.

- **One-person test.** Is this addressed to one specific person, or to "users" and
  "teams" generically? Pick one reader. The copy changes when the address is
  specific.
