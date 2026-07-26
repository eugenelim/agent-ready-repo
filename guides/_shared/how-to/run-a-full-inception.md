# Run a full inception for a new project

**Use this when:** You are starting a greenfield project and need to know which packs and skills to apply at each stage — from raw idea to a first buildable slice — before the build loop takes over.
**Prerequisites:** An idea and the `core` pack installed; optionally the `inception` profile (`desk-research`, `product-engineering`, `architect`); see "Before you start".
**Result:** A sequenced map of which packs and skills to apply at each uncertain stage, ending in a walking-skeleton spec ready for `work-loop`.

This guide is for someone starting a greenfield project who wants to know which
packs to reach for, and in what order, before the build loop takes over.
Inception is the stretch from a raw idea to a recorded foundation and a first
buildable slice.

It points you at the packs and skills each stage needs; the linked per-pack
guides carry the actual procedure. If you only want the shortest path — feed an
idea to `init-project` and get a walking skeleton — walk
[From idea to a walking skeleton](../../core/tutorials/start-a-new-project.md)
instead; that one uses `core` alone. This guide is the fuller flow: where
research, product shaping, and system design fit around that core spine.

## Before you start

You need:

- An idea, even a rough one.
- The `core` pack, for `init-project`, `new-spec`, and `work-loop`.

The three upstream packs — `desk-research`, `product-engineering`, `architect` —
are the user-scope `inception` profile, so one command carries the whole
toolkit across every venture:

```bash
agentbundle install --profile inception <catalogue>
```

You don't have to use all of it. Inception is a spine with optional stages in
front of it. You reach for a stage only when you're carrying the uncertainty it
removes — the profile just means the pack is already there when you do. For the
install routes themselves see [Install routes](../explanation/install-routes.md),
or [Install a curated set of packs](install-a-profile.md).

## The spine

Every inception ends the same way: `init-project` records a foundation and
authors a walking-skeleton spec, then `work-loop` builds it. What changes is
how much you do *before* `init-project`, and that depends on what you're
unsure about.

| What you're unsure about | Bring in | It produces |
| --- | --- | --- |
| Is this true? What's been built before? What's best practice? | `desk-research` | a cited `<topic-slug>-survey.md` |
| Is this worth building? Does the bet hold? What exactly ships? | `product-engineering` | a `core` **brief** |
| How should it be built? What's the system shape? | `architect` | a design doc and ADR-worthy decisions |
| — always — | `core` (`init-project`) | an ADR, a `reference.md`, a skeleton spec |
| — always — | `core` (`work-loop`) | shipped slices |

Read it top to bottom and skip any row whose uncertainty you don't carry.

## The packs and skills you reach for

### `desk-research` — when the space is unfamiliar or contested

- **Skills:** `desk-research` (run it in `applied` mode for prior art, best
  practice, and known anti-patterns), plus `source-map`, `compare-hypotheses`,
  and `devils-advocate` for contested choices.
- **Install:** in the `inception` profile, or on its own with
  `agentbundle install --pack desk-research <catalogue>`.
- **How:** [Run the research pipelines](../../desk-research/how-to/desk-research-pipelines.md),
  or [your first research session](../../desk-research/tutorials/desk-research-first-session.md)
  if the pack is new to you.

### `product-engineering` — when the bet is uncertain

- **Skills:** `frame-intent` (idea → outcome plus opportunity),
  `de-risk-intent` (test the riskiest assumption against a predeclared kill
  condition), `decompose-intent` (cut it into a `core` brief). At app scale the
  leaf intent *is* the brief. The `frame → de-risk → decompose` loop hands its
  leaf into `init-project`'s value gate — an `intent` from `frame-intent` is one
  of `init-project`'s four recognized discovery sources (alongside `desk-research`, a
  PRD, and a `receive-brief` brief), named as **optional upstream**: present when
  this pack is installed.
- **Install:** in the `inception` profile, or on its own with
  `agentbundle install --pack product-engineering <catalogue>`.
- **How:** [Shape a feature intent](../../product-engineering/how-to/shape-a-feature-intent.md).

### `architect` — when the system shape is uncertain

- **Skills:** `architect-design` (concept → design doc, converged against
  review), `architect-diagram`, `architect-review`. The decisions it surfaces
  become the rationale `init-project` records.
- **Install:** in the `inception` profile, or on its own with
  `agentbundle install --pack architect <catalogue>`.
- **How:** [Establish your reference architecture](../../architect/how-to/establish-reference-architecture.md).

### `core` — always (you already have it)

- **Skills:** `init-project` (runs the trigger and value gates, records the
  foundation — an ADR plus `reference.md` — and authors the walking-skeleton
  spec via `new-spec`), then `work-loop` builds it. `receive-brief` is the
  entry point when someone hands you a multi-feature brief instead of an idea.
- **How:** [Decide and record your foundation](../../core/how-to/record-your-foundation-during-inception.md)
  and [Plan and execute non-trivial work](../../core/how-to/plan-and-execute-non-trivial-work.md).

`init-project` orchestrates the foundation and skeleton; it does not build the
skeleton itself, and it consumes discovery rather than performing it. If the
`architect` stage already established `reference.md`, the foundation step points
at it rather than redoing it.

## The lightest inception

Clear idea, obvious value, familiar stack: skip the upstream packs entirely.
Feed `init-project` a one-paragraph PRD and go straight to a walking skeleton.
This is exactly the [core tutorial](../../core/tutorials/start-a-new-project.md).
The upstream stages earn their place only against real uncertainty.

## Common pitfalls

- **Asking `init-project` to do the research.** It consumes discovery; it never
  performs it. If you reach the value gate and can't state the business value,
  the gate stops you. That's the signal to go back to `desk-research` or
  `product-engineering`, not to push through.
- **No home for early notes.** There's no first-class inbox for thinking that
  predates research. The durable options today are a `desk-research` artifact (a
  `<topic-slug>-survey.md` from `standard`/`applied` mode) or
  `docs/product/intents/<slug>.md` once you've framed an
  intent. `.context/` is session scratch: it's gitignored and doesn't survive a
  fresh workspace, so keep nothing load-bearing there.
- **Treating the stages as mandatory gates.** They're optional stages keyed to
  uncertainty, not a waterfall. Running all three upstream packs for a project
  whose value and shape are already clear is ceremony.

## See also

- [Shaping a new engagement](../explanation/shaping-a-new-engagement.md) — the
  *why*: how the product vision, the product strategy, and the architecture
  concept co-shape each other across the stages this guide sequences.
- [From idea to a walking skeleton](../../core/tutorials/start-a-new-project.md)
  — the `core`-only walkthrough this guide wraps.
- [Receive a product brief](../../core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md)
  — when you start from someone else's multi-feature brief.
- [Run a capability across a value stream](../../product-engineering/how-to/run-a-capability-across-a-value-stream.md)
  — inception at business-unit scale, across many component repos.
- [Install a curated set of packs](install-a-profile.md) — take the upstream
  packs in one command.
