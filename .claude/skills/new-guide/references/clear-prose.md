# Clear-prose checklist

Good docs read like one person wrote them for another. Prose that reads
machine-made — even when every fact is right — makes a reader trust the page
less. Run a draft past this list before you ship it. Read it when you're
drafting or editing, not as theory up front.

## Tells to cut

These are the habits that make writing feel generated. Each one is easy to
search for once you know its shape.

- **Hedges.** "It's worth noting that", "it's important to understand",
  "generally speaking", "in most cases". They pad the line and duck the claim.
  Delete the throat-clearing and state the thing.
- **Uniform rhythm.** When every sentence runs the same length, the reader
  glazes over. Vary it. A longer sentence that carries a real idea, then a
  short one that lands.
- **The rule of three, on a loop.** "Fast, reliable, and scalable."
  "Configure, deploy, and monitor." One triad is fine. A page of them reads
  like filler poured in to reach a word count.
- **Em-dash overuse.** One or two per page punctuate well. Ten make every
  sentence sound the same. Reach for a period or a comma first; keep the dash
  for the break that earns it.
- **Throat-clearing openers and closers.** "In this guide, we will explore…",
  "In conclusion…", "Overall, it is clear that…". Cut them. Start with the
  first sentence that does work.
- **Inflated verbs and adjectives.** "Leverage", "utilize", "delve into",
  "robust", "seamless", "powerful". Write "use". Replace the adjective with a
  fact: not "blazingly fast" but "renders in under 50 ms".
- **Restating the heading.** A section called "Rotate a token" that opens
  "This section explains how to rotate a token." The reader already read the
  heading. Start rotating the token.

## Structural tells

These are harder to catch than vocabulary tells because they survive a word-level
pass. A draft can have zero inflated verbs and still read as machine-made if it
falls into these patterns.

- **Treadmill effect.** Each paragraph restates the previous one rather than
  advancing the argument. The text circles the idea without arriving anywhere. Fix:
  read the first and last sentence of each paragraph — the last should move past the
  first, not echo it.
- **Symmetrical lists.** Bullet items of identical length, parallel construction,
  and equal weight — as if generated to fill a template rather than to capture
  genuinely distinct points. A real list of three items is rarely three identical
  sentences. Vary length and depth to match the actual shape of the content.
- **False precision.** Authoritative framing — "research shows", "studies indicate",
  "it's important to note" — without a grounded specific behind it. If you can't
  name the study, the finding, or the number, replace the framing with a concrete
  claim or cut it.
- **Performative thoroughness.** Seven considerations when two drive the decision.
  The extra five exist to signal completeness, not to inform. Cut the padding; leave
  the two that matter.
- **Nice-nice wrap.** Both sides of a conflict hedged to avoid commitment — the text
  names a tension but refuses to land on a position. A reader should be able to
  disagree with a claim in your doc. If there's nothing to push back on, there's
  nothing being said.
- **Subtext vacuum.** Flat, safe-for-any-audience prose with no implied reader.
  Human writing carries a register — a sense of who it's for and what they already
  know. Writing for everyone reads as writing for no one.

## Habits to keep

- **One claim per sentence.** If a sentence has two "and"s and a "which", it's
  two or three sentences wearing a trench coat. Split it.
- **Concrete over abstract.** A number, a command, or an example beats an
  adjective every time. Show the thing instead of praising it.
- **Strong verbs, not noun phrases.** "Decide" beats "make a decision";
  "configure" beats "perform the configuration".
- **Omit needless words.** Read each sentence and cut what carries no meaning.
  "In order to" → "to". "At this point in time" → "now". "Due to the fact
  that" → "because".
- **Second person, active voice, present tense.** "Run the command and you'll
  see the build pass", not "the command should be run, after which it will be
  observed that the build passes".
- **Don't explain your own reasoning mid-sentence.** "We organize it this way
  because…" is your thinking leaking onto the page. State what is. If the *why*
  earns space, give it its own sentence or link to an explanation page.
- **Don't narrate your intent.** "Here we want to show you…", "the goal of this
  section is…". Drop the meta-commentary and show the reader directly.
- **Don't narrate the product's history.** Describe how it works now, not how it
  used to — the *retcon* discipline. "Previously X, now Y", "will be added next
  release", "deprecated in 2.0" belong in release notes or the changelog, not the
  body. The reader wants what's true today; mixed tenses make them guess which
  part still holds.

## A fast self-check

Read the draft cold, ideally out loud. The sentences you stumble over are the
ones to cut or split. If a paragraph could be three bullets, make it three
bullets. If a sentence survives only because it sounds finished, it's filler —
cut it.

Run these four questions on the draft to catch structural tells a vocabulary pass
will miss:

1. Does the argument advance paragraph to paragraph, or restate?
2. Does each list item earn its slot, or pad?
3. Is there a position the text can be disagreed with?
4. Is any specific detail grounded — a name, a date, a count, an observation —
   or is specificity only performed?

When your environment has subagents, the skill's optional copyedit pass hands
the draft and this checklist to a fresh reader so the style read stays off your
main context. The cold self-read is the floor either way.
