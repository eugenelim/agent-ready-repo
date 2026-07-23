# Per-Pack Journey Page Template

Defines the content schema and section structure for `/journeys/[pack]/` pages.
These pages are the platform site's primary differentiator — they show what it's like to *use* a pack, not just what it contains.
Reference: `.context/site-information-architecture.md`, `site/aesthetic-direction.md`, `docs/specs/journey-template-revamp/spec.md`

The template is **fixed and learnable**: structure never varies, only content does. A reader who learns to read one journey can read all of them (grounded in NN/g consistency + recognition heuristics; see `.context/doc-template-learnability-survey.md`).

---

## What a journey page is (and is not)

**Is:** A narrative walkthrough of a real usage session. Shows the human's role at every stage — what they provide, what the agent does, what they decide, and what each stage produces.

**Is not:** A skills reference (that's `/docs/`). Not a pack catalogue card (that's `/packs/`). Not marketing copy.

**Reader:** An IC (individual contributor) who has decided to try the pack and wants to know what to expect before they start.

---

## Frontmatter schema

```yaml
---
# Required
pack: core                        # slug — matches /packs/[pack] and /docs/packs/[pack]
scope: repo                       # "user" | "repo"
tagline: "Spec → shipped code. Supervised."
prerequisitePacks: []             # slugs of packs that must be installed first

# The compact above-the-fold contract — four fixed lines, rendered by
# JourneyContract.astro directly under the hero. Required (enforced by the
# zod schema and lint-journey-contract.py).
contract:
  useItWhen: "You're implementing a feature, fixing a bug, or changing an existing repo."
  youProvide: "The task and its important constraints."
  youReceive: "An agreed plan, a checked implementation, review findings, and a merge decision."
  yourDecisions:                  # one entry per human gate; mirrors humanGates[].label
    - "Approve the plan"
    - "Approve the final change"

whatChanges: "One paragraph: what the reader can now do that they couldn't before."

# Skills listed in usage order (not alphabetical)
skills:
  - name: work-loop
    description: "The build loop. Plans, executes, verifies, and reviews."
    humanTouches: 2               # number of human gates in a typical session

# Human gates — in sequence order (unchanged shape)
humanGates:
  - id: G-plan
    globalGate: null              # "G3" | "G4" | "G5" | null (loop-internal gates)
    label: "Approve the plan"
    trigger: "Before work-loop begins execution"
    duration: "5–10 minutes"
    whatToCheck: [ … ]
    whatGoodLooksLike: "…"
    whatBadLooksLike: "…"
    consequence: "…"

typicalSession:
  agentTurns: "8–12"
  humanTouches: 2
  wallClockMinutes: "25–45"

docsUrl: /docs/guides/core/
packUrl: /packs/core/
relatedJourneys:
  - release
---
```

**`contract` authoring rules:**

- `useItWhen` / `youProvide` / `youReceive` are one line each.
- `youReceive` states concrete **artifacts** ("an agreed plan, a checked diff, review findings") — **never** "you will learn X". (Diátaxis's objection to outcome-promising applies to learning claims, not artifact claims.)
- `yourDecisions` is an array with **one entry per human gate**, and the entries mirror the `humanGates[].label` values.

---

## Section structure

Every journey page renders these sections in this **fixed order** (`[journey].astro`). Content varies; order does not. Tones alternate light `surface` / `surface-alt`.

1. **Pack hero** — `JourneyHero.astro`. Pack name (display, amber), scope chip, tagline, stat strip (skills · human touches · session time), two CTAs.
2. **The contract** — `JourneyContract.astro`. The four fixed lines above. This is the above-the-fold summary — the first thing after the hero.
3. **What changes when you install this** — one specific paragraph (`whatChanges`), plus the `Requires:` prerequisite chips.
4. **The journey** — the staged narrative from the markdown body (`<Content />`). **This is the primary content**; everything below is scaffolding for it.
5. **What good output looks like** — a real transcript or artifact (`goodOutputDescription`, conditional).
6. **Human gates** — `GateDetail.astro` per gate: the detailed approval checklist.
7. **Typical session** — the timing stats (`typicalSession`).
8. **Install** — the derived install command.
9. **Skills in this pack** — one row per skill (name chip, description, human-touch indicator). Demoted below the narrative.
10. **Technical reference & next steps** — the docs link, related journeys, catalogue link.

The ordering enacts progressive disclosure: contract + narrative lead; catalogue/reference material follows.

---

## The staged narrative (fixed stage cards)

The markdown body is a sequence of stages. Each stage is:

```markdown
## N. <imperative outcome title>

- **You provide:** <what the human feeds in — only on stages where they do>
- **<Actor> does:** <what the agent / reviewer / loop does>
- **You do:** <the human's active, non-decision role, incl. anything they check>
- **You decide:** <the decision — only at a gate stage>
- **Output:** <what the stage produces — ALWAYS present>
```

**The label contract (fixed, and lint-enforced by `lint-journey-contract.py`):**

- The label set is exactly: **`You provide` · `<Actor> does` · `You do` · `You decide` · `Output`**.
- Each stage uses only the **applicable subset**, in that **order**; `Output` is **always** present.
- The **actor token** in `<Actor> does` is one of the closed set `Agent` / `Reviewer` / `Loop` — `Agent` for whatever the AI does (regardless of which named skill or subagent), `Reviewer` for a review/critique step, `Loop` for the iterate-to-clean mechanism.
- Headings are `## N. <title>` (numbered, imperative). No `## Stage N —` prose-narrative format.

Worked exemplar: `web/src/content/journeys/core.md`.

---

## Writing guide for journey content

- **Fixed labels, never improvised.** Do not invent a label (`You check`, `You watch`, `Agent will`). A human verification action folds into `You do`; a decision is `You decide`.
- **Name the skill, not just the loop:** "The loop runs `adversarial-reviewer` in a fresh session" — not "the loop reviews the diff."
- **Be specific about time:** "5–10 minutes to read the plan" beats "a few minutes."
- **Name the failure mode at every gate:** what does a bad plan look like? A bad PR? The reader needs to recognize a bad outcome, not just a good one. (This is Carroll's error-recovery principle — keep it first-class.)
- **Do not soften the agent's limitations.** Earned authority requires honesty about the limits.

---

## Content authoring priority

Journey content is authored in this priority order:

| Journey | Priority | Rationale |
|---|---|---|
| `core` | 1 | Every adopter installs this; it's the entry point |
| `discovery` | 1 | The discovery loop is the product's conceptual differentiator |
| `release` | 1 | Completes the full SDLC story |
| `desk-research` | 2 | High independent utility |
| `architect` | 2 | Common in engineering-lead audiences |
| `experience-design` | 2 | Differentiates for product-engineering teams |
| All others | 3 | Content follows once the P1/P2 journeys are live |
