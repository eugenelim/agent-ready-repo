---
type: copy-direction
surface-slug: marketing-home
date: 2026-09-04
---

# Copy direction: marketing home

Direction for one surface. No finished copy. The brand register at
`copy/brand-register.md` is the upstream anchor; this document narrows it to the
home page's specific job.

## Reader map

Drawn from the content brief at `content/marketing-home.md`
(`communication_mode: product-copy`, action goal **Understanding**, reader
**Problem-Aware**, arc **StoryBrand**).

| Reader type | Copy JTBD sentence | Rank |
|---|---|---|
| Adoption champion, arriving cold | When I land on this page with a vague sense that our AI-assisted work is unsupervised, I want copy I can repeat almost word for word to my engineers, my platform team, and the person who holds the budget, so that the decision does not rest on how well I improvise. | **Primary** |
| Software engineer, sent a link | When someone on my team sends me this, I want copy that tells me what it will demand of me and where it will slow me down, so that I can decide whether the friction is worth it. | Secondary |
| Platform lead, asked to support it | When I am asked to own this in our repositories, I want copy that states what installs where and what runs without asking me, so that I am not surprised later. | Secondary |
| Budget holder, five minutes in a meeting | When somebody asks me to fund this, I want copy that names the commitment and the limits, so that I can decide without becoming an expert. | Tertiary |

## Named copy goals (ranked)

1. **Sayable in a meeting**
2. **The refusal up front**
3. **One order, one telling**
4. **Checkable or cut**

## What each goal means

- **Sayable in a meeting** — means: the load-bearing lines are written to be spoken
  out loud by a champion, from memory, to somebody who has not read the page. If a
  sentence needs the page around it to make sense, it fails here. Violated by:
  internal notation of any kind, wordplay that depends on the adjacent heading, and
  any claim the champion would have to soften when repeating.
  - *Persona language:* **Directional — third-party, uncited, and not this
    product's audience.** A survey of ten technology companies recorded an
    engineering leader saying *"outside of vanity
    metrics, I have nothing of value to show."* The gap is not belief; it is
    having something sayable.
  - *Copy precedent:* Stripe's developer documentation — taking the absence of
    inflection on a technical claim. Not taking its reference-first structure.
  - *Persuasion standard:* the tweet test. The current headline fails it: shared
    without the page it names a mechanism and an anti-property, and assumes the
    reader knows what a build loop is.

- **The refusal up front** — means: what the system will not do on its own appears
  early, in the same register as what it will, and is treated as a selling point
  rather than a caveat. Violated by: describing autonomy without naming where it
  stops, and relegating a boundary to fine print when it is the reason to trust
  the claim.
  - *Persona language:* **Directional — not backed by VoC research.** The budget
    holder's decisive question and the platform lead's tracker question are both
    the engagement's hypotheses, recorded in the adoption journey as inference.
    The champion interview tests them.
  - *Copy precedent:* good postmortem writing — taking the habit of stating the
    boundary before the reassurance.
  - *Persuasion standard:* the five-second evaluator scan. A skeptic checks the
    limits first, and copy that makes them hunt reads as evasive.

- **One order, one telling** — means: two different things happen in this product —
  a piece of work moves through a sequence, and a team moves through an arc — and
  each gets told once, whole, in order, in the reader's words. Violated by: a
  sentence that describes both at the same time, a stage named by its internal
  identifier, and process rendered as a list of capabilities.
  - *Persona language:* **Directional — our own voice, not the reader's.** The
    existing guide paths already say *"a spec and plan you
    approved before any code was written"* and *"a human ratifying the production
    ship."* That is the target register, already written and reviewed.
  - *Copy precedent:* Julia Evans's zines — taking the rule that one panel answers
    exactly one question. Not taking the informality.
  - *Persuasion standard:* painkiller-first framing. A sequence the reader can
    trace is what turns a claim about supervision into a believable one.

- **Checkable or cut** — means: a number, name, path, or output appears only where a
  reader could go and verify it. Violated by: self-reported counts positioned as
  proof, and adjectives standing in for evidence.
  - *Persona language:* **Directional — not backed by VoC research**, but grounded
    in observed behaviour: readers of this project bypass the published
    documentation to read raw skill source — 12 unique readers on one source file
    in fourteen days against 6 for the repository's docs directory. They trust the
    artifact over the description.
  - *Copy precedent:* Linear's use of real product surfaces rather than
    illustration — taking the preference for the real output over a representation
    of it.
  - *Persuasion standard:* the tweet test inverted — if deleting the number would
    not weaken the sentence, the number was decoration.

## Dominant goal

**Dominant goal:** Sayable in a meeting.

The page's action goal is Understanding, and its primary reader's job is transfer.
A line that is accurate, elegant, and unrepeatable has failed the only reader the
page depends on.

Resolved trade-offs:

| Conflict | Winner | Reason |
|---|---|---|
| Brevity vs. completeness | Sayable in a meeting | Trimmed past the point where a champion can repeat it without hedging is too short, however well it scans. |
| Authority vs. approachability | Sayable in a meeting | Authority that requires the reader to already hold the vocabulary cannot be transferred to three audiences with different vocabularies. |
| Specificity vs. universality | Checkable or cut | Specific and verifiable beats broadly applicable — but an unverifiable number loses to a plain sentence. |
| Completeness vs. the refusal up front | The refusal up front | Where the full truth is too long for the position, the boundary is the part that survives the cut. |
| Urgency vs. warmth | The refusal up front | Neither wins alone; urgency that omits a boundary breaks a higher-ranked goal. |
| A dramatic claim vs. one order, one telling | One order, one telling | Six of nine current sections describe both lifecycles at once and neither whole. That is the diagnosed defect; no headline is worth reinstating it. |
| Any goal vs. the plain-language floor | The floor | Not a trade-off. |

## Brand-register consistency

- Brand-register referent: `docs/design/copy/brand-register.md`
  (`type: tone-of-voice`, `scope: brand-level`, both present and validated).
- Consistency check: **consistent.** The four goals here are the surface-level
  narrowing of the register's four — Repeatable precision becomes *Sayable in a
  meeting*, Named limits becomes *The refusal up front*, Plain sequence becomes
  *One order, one telling*, Earned specificity becomes *Checkable or cut*. The
  dominant goal is preserved rather than reordered.

One deliberate sharpening, recorded rather than silent: the register's *Plain
sequence* is generic across surfaces; here it is narrowed to a prohibition on
describing both lifecycles in one sentence, because that is this surface's
specific failure mode and not a brand-wide one.

## Anti-AI-smell scan

Run against each goal and referent above, per `product-copy` mode.

**Warning-signal words: none present** in the goal names or referents. Two were
considered and rejected during naming — "comprehensive" for what became *One
order, one telling*, and "end-to-end" for the work sequence. Both were
compensating for a lack of specificity: the specific claim is that each lifecycle
is told once and whole, which is what the goal now says.

**Structural signals — one flag, resolved.** Four goals of similar shape is close
to the repeated-triad pattern. Kept because each names a distinct and violable
copy move, and each has a different arbitration outcome in the table above. A goal
that could be merged into another would be the real failure; none can.

**The scan's hardest test applied to this page:** *could this be pasted onto
another company's website with only the name changed?* The current live copy
largely could — "the agentic build loop that cannot approve its own work"
describes a category position rather than this product's specific structure. The
direction above is designed to fail that test in the right direction, by making
the five-station arc and the named refusals the copy's substance.

## Plain-language floor notes

- **Jargon the reader did not bring.** Internal gate identifiers are barred; eleven
  appear on the live page today and this surface is where they are removed. "Loop",
  "gate", and "spec" are vocabulary this audience largely brings. **"Pack" is not**
  — it is product-specific and appears in navigation on this page. It needs one
  plain definition before first use, and nobody owns that yet.
- **Idioms.** No sporting or military metaphor; both travel badly across an
  international engineering audience. The canvas proposes a rail metaphor, and
  while rail vocabulary is broadly legible, "buffer stop" is not — the concept must
  be carried by the drawing and a plain sentence, never by the term.
- **Identity assumptions.** The reader map assumes a champion with a budget holder
  above them. The adoption journey carries an explicit self-serve path where the
  evaluator *is* the installer and there is no such person. Copy must not imply the
  reader needs permission. This is a real tension with the cohort framing and is
  an open question, not a resolved trade-off.
- **Familiarity assumptions.** Assume the reader has used a coding agent. Do not
  assume they have used a supervised operating model — that is the thing being
  introduced.

## Open questions

- **Does the self-serve reader survive this direction?** *Sayable in a meeting*
  optimises for a reader who has a meeting. A solo senior engineer at a small
  company has none. Either the direction needs a second-order rule for them or the
  reader map is drawn too narrowly from the sponsored path.
- **Is "the refusal up front" right for a budget holder?** Leading with what the
  product will not do is unusual in acquisition copy, and it rests on an untested
  hypothesis about what ends these meetings. The champion interview tests it.
- **Who defines "pack" in plain words, and where?** It is unfamiliar
  product-specific vocabulary in navigation on both surfaces, and the floor bars
  it until defined.
- **Two of four goals lack real VoC.** *The refusal up front* and *Checkable or
  cut* are directional. Amend this doc after the interview rather than letting the
  copy drift from it.
- **Should the existing problem statement become the headline?** It passes the
  tweet test the current headline fails. Raised in the design review's director's
  notes and still open — it is a copy decision, so it resolves against *Sayable in
  a meeting*.

## Hand-off

`ux-writing` owns per-screen UI copy states — the install block's copy
confirmation, the canvas transcript's disclosure control, the search placeholder
on the other surface. It does not write marketing headlines, and neither does
this skill: finished home-page copy is drafted directly against the four goals
above.

`conversion-design` reads `communication_mode: product-copy` from the content
brief and runs its own editorial quality gate against the above-fold spec and
scroll story.
