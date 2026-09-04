---
type: tone-of-voice
scope: brand-level
persona: adoption-champion — docs/design/discovery/team-orientation-personas.md
date: 2026-09-04
---

# Brand register: agent-ready-repo

The cross-surface copy register. Per-surface copy direction lives in
`copy/<surface-slug>.md`; brand-level conflicts resolve here rather than against
fresh opinion.

**Evidence status.** All four groundings are **directional — not backed by VoC
research**, and an earlier draft of this line claimed two rested on real audience
language. Cold review was right to reject that: one cites an uncited third-party
survey quoting *someone else's* audience, and the other cites this project's own
published copy, which is the team's voice rather than the reader's. Neither is
Voice of Customer for this product. Read the per-goal referents, not this summary. No support
tickets, sales transcripts, or community posts were available. The champion
interview will supply real audience vocabulary and this register should be
amended when it does.

## Reader map

| Reader type | Copy JTBD sentence | Rank |
|---|---|---|
| Adoption champion — evaluates for a team, cannot authorise or install at scale | When I have found something I think would make my team better, I want copy I can repeat almost verbatim to three different audiences, so that the decision does not depend on my improvising. | **Primary** |
| Software engineer — will run this daily, decides silently whether adoption survives | When someone proposes a new workflow, I want copy that tells me exactly what it demands and where it will get in my way, so that I can judge the friction honestly. | Secondary |
| Platform lead — owns the repositories, CI, and the support burden | When somebody proposes a system for my repositories, I want copy that states plainly what I will own and what runs without asking me, so that I can support it without being surprised. | Secondary |
| Budget holder — CTO, director, or AI-programme lead, reading for under five minutes | When I am asked to fund a change to how my engineers work, I want copy that names the commitment and the worst realistic outcome, so that I can decide without becoming an expert. | Tertiary |

The champion is primary not because they matter most, but because they are the
only reader who has to carry the other three. Copy that the champion cannot
repeat has failed regardless of how well it reads.

## Named copy goals (ranked)

1. **Repeatable precision**
2. **Named limits**
3. **Plain sequence**
4. **Earned specificity**

## What each goal means

- **Repeatable precision** — means: every load-bearing sentence is exact enough to
  survive being repeated by someone who did not write it, to someone who has not
  read the page. Prefer the sentence a champion can say out loud in a meeting over
  the sentence that reads best on screen. Violated by: internal notation in
  adopter copy, cleverness that depends on surrounding context, and any claim a
  reader would have to hedge when repeating.
  - *Persona language:* **Directional — third-party, uncited, and not this
    product's audience.** A survey of ten
    technology companies recorded an engineering leader saying *"outside of vanity
    metrics, I have nothing of value to show."* The champion's problem is not
    enthusiasm; it is the absence of something credible and repeatable.
  - *Copy precedent:* Stripe's developer documentation — taking the total
    accuracy and the absence of inflection on technical claims. Not taking its
    reference-first structure, which suits an API and not an operating model.
  - *Persuasion standard:* the tweet test. A line that cannot stand alone cannot
    be repeated, and the current home page headline fails it — shared without the
    page it describes a component and assumes the reader knows what a build loop
    is.

- **Named limits** — means: say what the system will not do, in the same voice and
  at the same prominence as what it will. The refusals are the product. Violated
  by: describing autonomy without naming where it stops, implying completeness the
  system does not have, and burying a boundary in a caveat when it is the reason a
  reader should trust the claim.
  - *Persona language:* **Directional — not backed by VoC research.** The platform
    lead's decisive question is recorded in the adoption journey as an inference,
    not an observation: whether this writes back to their tracker. The budget
    holder's decisive question — what it refuses to do on its own — is the
    engagement's own hypothesis.
  - *Copy precedent:* good incident and postmortem writing — taking the habit of
    stating the boundary before the reassurance.
  - *Persuasion standard:* the five-second evaluator scan. A skeptical reader
    checks the limits first; copy that makes them hunt reads as evasive.

- **Plain sequence** — means: when something happens in an order, say the order.
  Numbered when it is a true sequence, and in the reader's terms rather than the
  system's. Violated by: describing a process as a set of capabilities, naming a
  stage by its internal identifier, and abstract nouns where a verb and an actor
  would do.
  - *Persona language:* **Directional — our own voice, not the reader's.** This is
    the strongest referent available and it is still not Voice of Customer: the
    existing guide paths already say *"a spec and plan you
    approved before any code was written"* and *"a human ratifying the production
    ship."* That is the register, already written and already reviewed. It is the
    reference, not an aspiration.
  - *Copy precedent:* Julia Evans's zines — taking the discipline that one panel
    answers exactly one question. Not taking the hand-drawn informality.
  - *Persuasion standard:* painkiller-first framing. A sequence the reader can
    trace is what converts a claim about supervision into a believable one.

- **Earned specificity** — means: a number, name, path, or output appears only when
  a reader could check it. Specificity that cannot be verified is decoration wearing
  precision's clothes. Violated by: self-reported counts presented as proof,
  round numbers with no source, and adjectives standing in for evidence.
  - *Persona language:* **Directional — not backed by VoC research.** Grounded
    instead in observed behaviour: readers of this project bypass the published
    documentation to read raw skill source — 12 unique readers on one source file
    in fourteen days. They trust the artifact over the description of it.
  - *Copy precedent:* Linear's use of real product surfaces rather than
    illustration — taking the preference for the real output over a
    representation of it.
  - *Persuasion standard:* the tweet test again, inverted — if removing the number
    would not weaken the sentence, the number was decoration.

## Dominant goal

**Dominant goal:** Repeatable precision.

It wins because the primary reader's job is transfer. A sentence that is elegant,
accurate, and unrepeatable has failed the one reader the brand depends on.

Resolved trade-offs:

| Conflict | Winner | Reason |
|---|---|---|
| Brevity vs. completeness | Repeatable precision | A sentence trimmed past the point where it can be repeated without hedging is too short, even if it scans better. |
| Authority vs. approachability | Repeatable precision | Authority that requires the reader to already know the vocabulary cannot be transferred; the champion is talking to three audiences with different vocabularies. |
| Specificity vs. universality | Earned specificity | Specific and checkable beats broadly applicable. But a number nobody can verify loses to a plain sentence. |
| Urgency vs. warmth | Named limits | Neither wins on its own. Urgency that omits a boundary breaks the second goal, which outranks both. |
| Completeness vs. named limits | Named limits | Where the whole truth is too long, the boundary is the part that survives the cut. |
| Any goal vs. the plain-language floor | The floor | Not a trade-off. |

## Plain-language floor notes

- **Jargon the reader did not bring.** Internal gate identifiers are machine
  contracts and are barred from adopter copy by the governing principle. Eleven
  currently appear on the live home page. "Loop", "gate", "pack", and "spec" are
  vocabulary this audience largely does bring — but "pack" is product-specific and
  needs its plain meaning given once before it is used as a noun.
- **Idioms.** The register avoids sporting and military metaphor, which travel
  badly across an international engineering audience. One deliberate exception is
  under review: the canvas design proposes a rail metaphor with signals and a
  buffer stop. Rail vocabulary is broadly legible, but "buffer stop" is not, so
  the concept must be carried by the drawing and by a plain sentence rather than
  by the term.
- **Identity assumptions.** The reader map assumes a champion inside an
  organisation with a budget holder above them. A solo engineer at a small
  company has no such reader above them and the copy must not imply they need
  permission. This is a genuine tension with the cohort framing and is recorded as
  an open question rather than resolved in the register.
- **Familiarity assumptions.** Copy must not assume the reader has used a
  supervised operating model, only that they have used a coding agent.

## Open questions

- **The register has partial VoC at best.** Two goals cite real audience language;
  two are directional. The champion interview supplies the missing half. Amend
  this doc, do not let per-surface copy quietly drift away from it.
- **Does the cohort framing exclude the solo reader?** The adoption journey
  carries an explicit self-serve path where the evaluator is the installer and
  there is no budget holder. The primary-reader ranking here is drawn from the
  sponsored path. If a material share of readers are solo, "Repeatable precision"
  is still right but the reader map is wrong.
- **How is "pack" introduced?** It is product-specific vocabulary in a register
  that bars unfamiliar jargon, and it appears in navigation on both surfaces.
  Needs one plain definition placed before first use, and nobody owns that yet.
- **Does "Named limits" survive a budget-holder reading?** Leading with refusals
  is unusual in acquisition copy and is being asserted as a strength on the basis
  of an untested hypothesis about what ends these meetings.

## Hand-off

`copy-direction` — per-surface copy positioning; each per-surface goal checks
against the four goals above. `ux-writing` — product UI strings and states. This
register is the upstream referent for both, and is amended deliberately rather
than re-derived.
