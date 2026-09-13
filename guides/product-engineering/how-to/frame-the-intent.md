---
title: "Frame the intent"
summary: "State the outcome and the opportunity behind it before any solution is proposed."
pack: product-engineering
kind: how-to
order: 1
---

# Frame the intent

**Step 1 of 4 — Frame the intent**
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What changes:** A problem becomes a level-tagged intent with a slug that every later artifact traces back to.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What you need first:** A problem worth solving, and whoever can say what a good outcome looks like.
<!-- rung: authored -->

*Skipping costs:* Discovery runs against a solution someone already picked, and nothing can be traced back to a stated outcome.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The discovery loop](../explanation/the-discovery-loop.md) explains how a raw idea becomes a build-ready brief.
- [The intent tree](../explanation/the-intent-tree.md) explains why a vision, a strategy, a capability and a feature are the same shape at different levels.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `frame-intent` | A problem worth solving | A level-tagged statement of the outcome and the opportunity behind it. | Required |
| `frame-domain` | An approved intent | The real-world activity the product sits in, and the MVP boundary. | Optional |
| `frame-situation` | An approved intent | What is true now, and what is forcing a change. | Optional |
| `lean-canvas` | An approved intent | Problem, solution, metrics and unfair advantage on one page. | Optional |
| `discovery-loop` | An approved intent | The loop itself — the plan tree, the lens roster, and the gates. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work, and it
stays the same from the intent through to the brief, which is how the
traceability lint follows one thread.

<!-- rung: packs/product-engineering/JOURNEY.md -->

## Run `frame-intent` — the outcome, written down

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

```
Frame this as a product intent: our onboarding drops half of new accounts before they connect a data source.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

> **Agent:** Done — I've written an intent naming the outcome, its level, and the opportunity behind it to `docs/product/intents/<slug>.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

> **You:** You wrote the solution as the outcome. State what changes for the customer, and leave how we get there for later.
>
> **Agent:** I rewrote the outcome as the customer change and moved the proposed approach into the opportunity section.

**Output varies** with how well formed the problem is and whether a parent intent already exists.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

**You decide:** Approve the intent before discovery runs against it — the pack's `approve-intent` gate. Everything downstream is traced back to this slug.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**Check (falsifiable):** Ask what would have to be true for this outcome to be the wrong one to pursue; this surfaces an intent nothing could argue with.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

**Watch out for:** An intent that names a solution reads as decisive and forecloses discovery before it starts. Notice an outcome you could implement directly — that is a solution wearing an outcome's clothes.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

**Where it lands:** `docs/product/intents/<slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

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

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Run `frame-domain` — what the domain actually is

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

```
Frame the domain for this intent — what is the real-world activity, and where does the MVP boundary sit?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

> **Agent:** Done — I've written a domain framing of the real-world activity, with an explicit scope boundary to `docs/discovery/<initiative>/domain-framing.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

> **You:** The boundary includes billing, which nobody asked for. Cut it and say why it is out, so it stays out.
>
> **Agent:** I moved billing out of scope and recorded the reason in the boundary section rather than deleting it silently.

**Output varies** with how familiar the domain is and how much real-world evidence you hold.
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (grounded):** Ask which practitioner would recognise this description of their work; this surfaces a domain modelled from the product rather than from the activity.
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

**Watch out for:** A confident domain model can describe the software rather than the work. Notice entities that only exist because the current product has a screen for them.
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

**Where it lands:** `docs/discovery/<initiative>/domain-framing.md`.
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: domain-framing
---
# Domain framing — <initiative>

## The real-world activity

<What practitioners actually do, in their words, independent of our product.>

## Entities and their relationships

## Scope boundary

- **In:** <what the MVP covers>
- **Out:** <what it does not, and why it stays out>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `frame-situation` — the current state

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

```
Frame the current situation — what is true today, and what is forcing this to change now?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

> **Agent:** Done — I've written an account of the current situation and the forces making it untenable. Nothing was written to disk.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

> **You:** This reads as a list of complaints. Say what has changed recently to make this urgent now rather than last year.
>
> **Agent:** I named the two changes that moved this from tolerable to urgent and dropped the standing complaints.

**Output varies** with how much is known about the current state and how recent the pressure is.
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask what changed recently; this surfaces a standing annoyance presented as a new opportunity.
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

**Watch out for:** A situation with no timing argument justifies doing this whenever, which means never. Notice framing that would have read identically two years ago.
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Situation — <initiative>

What is true today: <current state>
What changed recently: <the force making this urgent now>
What it costs to leave alone: <consequence>
```

*Section shape only. This skill reports in the session rather than writing a file — confirm the shape against what you get back.*

## Run `lean-canvas` — the one-page bet

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

```
Draft the lean canvas for this initiative.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

> **Agent:** Done — I've written a lean canvas with the problem, the solution sketch, the key metrics and the unfair advantage to `docs/product/initiatives/<ini-slug>.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

> **You:** The unfair advantage is our team. Name something a competitor could not copy in a quarter, or leave it empty.
>
> **Agent:** I emptied the unfair advantage and noted that it is unestablished, rather than filling it with something copyable.

**Output varies** with how much is known and how many boxes can be answered honestly.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Ask which box would change first if the riskiest assumption were wrong; this surfaces a canvas filled in for completeness.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**Watch out for:** Nine boxes invite nine answers. An honestly empty box is more useful than a plausible one — notice any box you could not defend to a sceptic.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**Where it lands:** `docs/product/initiatives/<ini-slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: initiative
---
# <initiative>

## Problem
## Existing alternatives
## Solution
## Key metrics
## Unique value proposition
## Unfair advantage
## Channels
## Customer segments
## Cost structure / Revenue streams
```

*Section shape only, following the Lean Canvas (Maurya, adapted from the Business Model Canvas). An honestly empty box is the point — confirm the shape against what you get back.*

## Run `discovery-loop` — run the whole loop

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

```
Run the discovery loop for this intent.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

> **Agent:** Done — I've written the discovery loop scaffolded — the plan tree, the roster of lenses, and the gates it will pause at. Nothing was written to disk.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

> **You:** You skipped straight to candidates without the plan tree. Scaffold the tree first so the traceability holds.
>
> **Agent:** I scaffolded the plan tree from the intent and re-entered the loop at the point it expects.

**Output varies** with how large the intent is and how many lenses the roster needs.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (sufficient-for-next):** Ask which gate the loop will pause at next and what it needs to get there; this surfaces a loop running without its state.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

**Watch out for:** The loop can appear to run while its state file is absent, which loses the traceability the gates depend on. Notice progress reported with no plan tree behind it.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Discovery loop — <initiative>

Phase: <phase>
Plan tree: `_state/plan-tree.json`
Lenses run: <n of m>

Next gate: <gate id> — needs <what>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when the outcome names a customer change rather than something you could build.
<!-- rung: authored -->

Stage 1 of four, and the pack's first gate. The slug set here follows the work to the end — through decomposition, into the spec directory the `core` guidebook creates, and out again at closeout.

If this intent arrived from [Route it to work](../../product-strategy/how-to/route-it-to-work.md) in the `product-strategy` guidebook, it is already a queued gap entry: reuse its slug rather than minting a new one, or the thread breaks at the pack boundary.

**Next:** [Find the opportunities](find-the-opportunities.md).
<!-- rung: authored -->

**Go deeper:** [the `product-engineering` intent-fields reference](../reference/intent-fields-and-modes.md) — the fields, modes and projection profiles these skills read and write.
<!-- rung: authored -->
