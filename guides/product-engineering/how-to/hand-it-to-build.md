---
title: "Hand it to build"
summary: "Slice the work so each piece ships something a customer would notice, and carry the voice with it."
pack: product-engineering
kind: how-to
order: 4
---

# Hand it to build

**Step 4 of 4 — Hand it to build**
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What changes:** A ratified decision becomes slices the build loop can pick up, each traceable to the parent intent.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What you need first:** A ratified decision brief.
<!-- rung: authored -->

*Skipping costs:* Engineering receives layers rather than outcomes, and the first shippable thing is months away.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The discovery loop](../explanation/the-discovery-loop.md) explains how a raw idea becomes a build-ready brief.
- [The intent tree](../explanation/the-intent-tree.md) explains why a vision, a strategy, a capability and a feature are the same shape at different levels.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `decompose-intent` | A ratified decision | Child intents or slices, each traceable to the parent. | Required |
| `align-value-stream` | Slices spanning components | A snapshot of one intent's delivery across every component it touches. | Optional |
| `ux-writing` | A product to characterise | Where the product sits on its voice axes, and the words it prefers. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work, and it
stays the same from the intent through to the brief, which is how the
traceability lint follows one thread.

<!-- rung: packs/product-engineering/JOURNEY.md -->

## Run `decompose-intent` — break it into work

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

```
Decompose this intent into deliverable slices, each traceable back to the parent.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

> **Agent:** Done — I've written child intents, each naming its parent and the part of the outcome it carries to `docs/product/intents/<slug>.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

> **You:** These slices are layers — one is the database, one is the API. Slice so that each one delivers something a customer would notice.
>
> **Agent:** I re-sliced along customer-visible outcomes; there are now three slices, each thinner but each shippable.

**Output varies** with how large the intent is and how separable the outcome is.
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

**You decide:** Commit to build — the pack's `commit-to-build` gate. After this the build loop owns the work.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**Check (sufficient-for-next):** Ask what a customer would notice after the first slice ships; this surfaces horizontal slicing dressed as decomposition.
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

**Watch out for:** Technical layers are the easiest slices to write and the least useful to ship. Notice a slice whose completion no customer could observe.
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

**Where it lands:** `docs/product/intents/<slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/decompose-intent/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md -->

```markdown
- **Slug:** `<slug>` <!-- kebab-case; matches the filename -->
- **Level:** `<product-vision | product-strategy | capability | feature>` <!-- the altitude this intent sits at; an open recognized set, not a closed enum — name an intervening altitude if your org has one -->
- **Kind:** `<outcome | opportunity>` <!-- optional, additive: the discovery-traceability chain rung this intent occupies on the opportunity-solution tree (outcome = the North Star / chain root; opportunity = a need in the OST). The structural-orphan lint reads this bold-body field to place the intent on the chain. Distinct from Level: (the altitude) — a `Level: capability` intent is placed by Level instead, and a feature intent maps downstream to a brief/spec. Omit it when not running the discovery-traceability chain; an intent still carries both an Outcome and an Opportunity section regardless. -->
- **Scale:** `<app | business-unit>` <!-- resolved at intake by frame-intent -->
- **Maturity:** `<greenfield | brownfield>` <!-- brownfield unlocks current-state inputs -->
- **Parent intent:** <!-- optional: the higher-level intent this was decomposed from; omit at the top of the tree -->

## Outcome

<!-- LOAD-BEARING. What changes, and how you'll know. Name a *steerable input
metric* you can directly move, the *lagging outcome* it should drive, and a
*guardrail* that must not get worse. A qualitative-but-falsifiable outcome is
fine in 0-to-1 — name the signal you'd accept as proof. -->

- **Input (steerable):** <the metric you can move directly>
- **Outcome (lagging):** <the result it should drive>
- **Guardrail:** <what must not get worse>

```

*The agent replaces every `<…>`. A child intent is the same shape as its parent — the `Level:` field and the parent pointer are what differ — so this is the template it writes from.*

## Run `align-value-stream` — across many repos

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

```
Roll up this intent across the component repos it was sliced into.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

> **Agent:** Done — I've written a cross-component rollup with one row per component slice and its current state to `docs/product/rollups/<slug>.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

> **You:** Three rows say in progress with no date. A snapshot with no reviewed date cannot be trusted next week.
>
> **Agent:** I dated each row against its source and marked two as stale rather than reporting them as current.

**Output varies** with how many components the intent spans and how current each source is.
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask when each row was last reconciled against its source; this surfaces a snapshot read as a live feed.
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

**Watch out for:** This is a snapshot, not a tracker, and it looks identical to one. Notice undated rows — they are the ones most likely to be wrong.
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

**Where it lands:** `docs/product/rollups/<slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/align-value-stream/assets/rollup-template.md -->

```markdown
- **Parent intent:** `<slug>` <!-- the capability/feature intent this fans out from (docs/product/intents/<slug>.md) -->
- **Last reviewed:** YYYY-MM-DD <!-- when the snapshot below was last reconciled against each component repo -->

## Why this is a snapshot, not a live feed

This rollup is a **markdown snapshot**, not a running tracker. Each row points at
the component repo's **own** auto-derived brief coverage (the authoritative
source); the status here is a **cached snapshot** of that, reconciled by hand
when you review the rollup — mirroring how the shared contract is *referenced*,
never forked. There is **no runtime hub** reaching into the component repos, and
the polyrepo hard limits apply: **no atomic cross-repo commit, no shared release
train**. Currency is the discipline that keeps the snapshot honest — a stale row
is the failure mode, so review the rollup whenever a slice's status changes.

## Delivery rollup

<!-- One row per component the parent intent was sliced into. The whole feature
is delivered only when EVERY row is delivered (the AND across rows). A row whose
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Run `ux-writing` — the product's voice

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

```
Characterise our product's voice — where does it sit on each axis, and how does tone flex by context?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

> **Agent:** Done — I've written a voice chart placing the product on each axis with a justification, plus its preferred and avoided words to `docs/product/voice/<slug>.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

> **You:** Every axis is in the middle, which says nothing. Commit to a position on each and justify it in one line.
>
> **Agent:** I moved every axis off centre and justified each; two were genuinely contested so I noted the tension rather than averaging it.

**Output varies** with how established the brand is and how much existing copy there is to read.
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Write one sentence two ways and ask which the chart chooses; this surfaces a chart that cannot decide anything.
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

**Watch out for:** A voice chart parked in the middle of every axis is a chart that permits all copy. Notice centred positions and make them commit.
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

**Where it lands:** `docs/product/voice/<slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/ux-writing/assets/voice-chart-template.md -->

```markdown
- **Slug:** `<slug>` <!-- kebab-case; matches the filename -->
- **Product:** `<what this voice belongs to>`

## Voice axes

<!-- Place the product on each axis — not always the middle. Justify in one line
from who the user is and what they came to do, and write one real sample line in
that voice. Add or drop an axis if the product needs it. See
references/voice-axes.md. -->

| Axis | Position (one end ↔ other) | Why | Sample line |
| --- | --- | --- | --- |
| Humor | `<serious ↔ playful>` | <one line> | <a real string> |
| Formality | `<formal ↔ casual>` | <one line> | <a real string> |
| Respect | `<deferential ↔ irreverent>` | <one line> | <a real string> |
| Enthusiasm | `<calm ↔ enthusiastic>` | <one line> | <a real string> |

## Tone flex by context
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Where this leads

**Done with this step:** You are done when a customer would notice something after the first slice ships.
<!-- rung: authored -->

Stage 4 of four, and the pack's last gate. After this the build loop owns the work.

**Next:** [the guides hub](../../README.md#p3--build-it--2-hours) — the slices are picked up by the build loop.
<!-- rung: authored -->

**Go deeper:** [the `product-engineering` intent-fields reference](../reference/intent-fields-and-modes.md) — the fields, modes and projection profiles these skills read and write.
<!-- rung: authored -->
