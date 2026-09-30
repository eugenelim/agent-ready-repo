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
| `lean-canvas` | An approved intent | The initiative's five core boxes on one page. | Optional |
| `discovery-loop` | An approved intent | The loop itself — the plan tree, the lens roster, the gates, and the initiative directory holding them. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In the paths below, `<slug>` is this piece of work's short
kebab-case name, fixed at step 1 so every later artifact traces back to it; `<initiative>` is the discovery initiative's kebab-case directory slug;
`<ini-slug>` is the initiative slug a Lean Canvas asks you for, such as
`ini-002`; `<output_dir>` is where this repository keeps product
artifacts, and the agent asks when it is not configured; `<discovery_dir>` is
where the discovery loop keeps its initiative directories, defaulting to
`docs/discovery/`. The agent tells you which path it wrote to.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md -->
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/references/agentbundle-layout.md -->

<!-- rung: packs/product-engineering/JOURNEY.md -->

## Run `frame-intent` — the outcome, written down

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

```
Frame this as a product intent: our onboarding drops half of new accounts before they connect a data source.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

> **Agent:** Done — I've written to `<output_dir>/intents/<slug>.md` an intent naming the outcome, its level, and the opportunity behind it.

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

**Where it lands:** `<output_dir>/intents/<slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md -->

```markdown
- **Slug:** `<slug>` <!-- kebab-case; matches the filename -->
- **Level:** `<product-vision | product-strategy | capability | feature>` <!-- the altitude this intent sits at; an open recognized set, not a closed enum — name an intervening altitude if your org has one -->
- **Owner:** `<who is accountable for this outcome>` <!-- required: a person or a role, declared rather than inferred from git history -->
- **Status:** `<Draft | Accepted | Fulfilled | Withdrawn | Cancelled | Superseded>` <!-- required; one bare word. Withdrawn and Cancelled are peers of Fulfilled, not flavours of it — a rollup that counts them as delivered is the failure this vocabulary prevents -->
- **Superseded by:** <!-- required when Status is Superseded, and refused otherwise; the Slug of the live intent that replaced this bet -->
- **Kind:** `<outcome | opportunity>` <!-- optional, additive: the discovery-traceability chain rung this intent occupies on the opportunity-solution tree (outcome = the North Star / chain root; opportunity = a need in the OST). The structural-orphan lint reads this bold-body field to place the intent on the chain. Distinct from Level: (the altitude) — a `Level: capability` intent is placed by Level instead, and a feature intent maps downstream to a brief/spec. Omit it when not running the discovery-traceability chain; an intent still carries both an Outcome and an Opportunity section regardless. -->
- **Scale:** `<app | business-unit>` <!-- resolved at intake by frame-intent -->
- **Maturity:** `<greenfield | brownfield>` <!-- brownfield unlocks current-state inputs -->
- **Parent intent:** `<kind>:<slug>` <!-- optional: the higher-level intent this was decomposed from, e.g. `capability:<slug>` or `intent:<slug>`; omit at the top of the tree -->
- **Outcome co-owner:** <!-- optional: another intent that shares this outcome, as a typed pointer such as `intent:<slug>`; omit when this intent owns the outcome alone -->
- **De-risked:** <!-- optional: the ISO 8601 date the riskiest assumption was tested, or the literal `no`. Absent means nobody recorded it; `no` means someone decided against de-risking -->
- **Shaping-reviewed:** <!-- optional: the ISO 8601 date a cold reviewer read this, or the literal `no` -->
- **Decomposed:** <!-- optional: the literal `no`, or an ISO 8601 date followed by exactly one of children | brief | spec | direct-light | closed-empty. `closed-empty` means decomposition is deliberately complete with no child work; `direct-light` requires each item under ## Decomposition to state its requested outcome -->

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

> **Agent:** Done — I've written to `<discovery_dir>/<initiative>/` a domain framing of the real-world activity, in `domain-framing.md`, with its MVP scope boundary in `scope-boundary.md`.

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

**Where it lands:** `<discovery_dir>/<initiative>/domain-framing.md`, with `scope-boundary.md` beside it.
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/frame-domain/examples/example-assistant.md -->

```markdown
---
type: domain-framing
initiative: example-assistant
brownfield: false
---

# Domain framing — example-assistant

## Real-world activity
- **How the activity is really done.** It runs on a cadence/horizon (e.g.
  weekly); the high-deliberation slice is a subset — the MVP anchors on that
  slice, not everything. The plan is **not followed exactly**: substitutions,
  skips, carry-overs. "Planned" and "actually done" diverge, so the plan must be
  editable and "mark what you did" is a first-class action. Carry-over is
  first-class (do once, benefit twice) and affects both next-cycle planning and
  resource decrement. Quantities scale to the owner's context.
```

*An excerpt of the example the skill ships. Best practice, the naive-design failure modes, any current-system notes and the residual assumptions follow in the same shape, with the MVP boundary in `scope-boundary.md` beside it.*

## Run `frame-situation` — the current state

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

```
Frame the current situation — what is true today, and what is forcing this to change now?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

> **Agent:** Done — I've written to `<output_dir>/shaping/<slug>/situation-framing.md` an account of the current situation and the forces making it untenable.

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

**Where it lands:** `<output_dir>/shaping/<slug>/situation-framing.md`.
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/frame-situation/examples/signal-to-finding.md -->

```markdown
---
type: situation-framing
slug: agent-skill-discovery-gap
signal: "Three hand-rolled skill discovery mechanisms found; no standard emerging; growing coordination overhead"
finding-type: gap
date: 2026-07-20
shaping-entry: identify-opportunities
---

## Signal
Engineering reported that every team hand-rolls its own agent skill discovery
mechanism — three implementations found across two squads, no standard emerging.
Symptoms: onboarding friction, duplicate maintenance, subtle incompatibilities.

## Finding
**Type:** gap · **Rationale:** A convergence gap — the org is spending
custom-build budget where a shared standard would serve it better. The problem
is confirmed; the solution space is open.
```

*An excerpt of the example the skill ships. The Wardley assessment, recommended entry point and `workspace.toml` suggestion continue below it.*

## Run `lean-canvas` — the one-page bet

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

```
Draft the lean canvas for this initiative.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

> **Agent:** Done — I've written to `docs/product/initiatives/<ini-slug>.md` a lean canvas with the problem, the unique value proposition, the solution sketch, the customer segments and the key metrics.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

> **You:** The customer segment is "engineering teams". Name the specific segment whose problem this solves first, or mark it `TBD` with the reason.
>
> **Agent:** I narrowed it to the segment whose problem the canvas actually describes, and marked the rest `TBD` with the reason rather than guessing.

**Output varies** with how much is known and how many boxes can be answered honestly.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Ask which box would change first if the riskiest assumption were wrong; this surfaces a canvas filled in for completeness.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**Watch out for:** Five boxes invite five answers. An honest `TBD` with its reason is more useful than a plausible guess — notice any box you could not defend to a sceptic.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**Where it lands:** `docs/product/initiatives/<ini-slug>.md`.
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/lean-canvas/examples/ini-003-ai-developer-brief.md -->

```markdown
# Initiative: AI-Assisted Developer Workflows

- **ID:** `INI-003`
- **Name:** AI-Assisted Developer Workflows
- **Status:** Active
- **Appetite:** 2–3 quarters
- **Owner:** engineering-lead
- **workspace.toml section:** `["ini-003"]` in `workspace.toml`

## Outcome

Engineers across all product squads spend less time on routine code-review
coordination and first-pass code quality triage. By end of initiative, the
median PR cycle time for non-urgent changes drops by 30%, and first-pass
review coverage reaches 100% of opened PRs — with AI-generated review comments
serving as the first filter before human reviewers engage.
```

*An excerpt of the example the skill ships. Simple mode's five boxes — problem, unique value proposition, solution, customer segments and key metrics — follow under Value Proposition.*

## Run `discovery-loop` — run the whole loop

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

```
Run the discovery loop for this intent.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/SKILL.md -->

> **Agent:** Done — I've scaffolded the discovery loop under `<discovery_dir>/<initiative>/`: the plan tree, the roster of lenses, and the gates it will pause at.

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

**Where it lands:** `<discovery_dir>/<initiative>/` — the initiative directory, holding the loop's `_state/` working files and its durable artifacts.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/references/agentbundle-layout.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/assets/plan-tree.md -->

```json
{
  "initiative": "<initiative-slug>",
  "schema_version": "0.1",
  "root_id": "intent:vision",
  "sub_idea_index": {
    "open": [],
    "parked": [],
    "done": []
  },
  "nodes": [
    {
      "id": "intent:vision",
      "type": "intent",
      "altitude": "product-vision",
      "parent_id": null,
      "lifecycle": "draft",
      "validation_status": "hypothesis",
      "round": 0,
      "round_cap": 12,
      "cost_spent": 0.0,
      "candidates": [],
      "selection": null,
      "validation_hook": null
    }
  ]
}
```

*The plan-tree template the loop copies per initiative. Each node carries its altitude, lifecycle and validation status, which is how the loop keeps `converged` and `validated` separate.*

## Where this leads

**Done with this step:** You can move on when the outcome names a customer change rather than something you could build.

`frame-domain` grounds its real-world-activity half by wrapping `desk-research` in applied mode, so you do not run that yourself. If the domain is unfamiliar, the [`desk-research` guidebook](../../desk-research/how-to/scope-the-question.md) is the same evidence pass run deliberately, and its output is a better input than an inline one.
<!-- rung: authored -->

Stage 1 of four, and the pack's first gate. The slug set here follows the work through decomposition and into the spec the `core` guidebook writes. A spec reached through a delivery brief carries that brief stamped on it; one authored directly carries no such stamp and stays valid. Either way the link is the stamp, not the directory name.

If this intent arrived from [Route it to work](../../product-strategy/how-to/route-it-to-work.md) in the `product-strategy` guidebook, it is already a queued gap entry: reuse its slug rather than minting a new one, or the thread breaks at the pack boundary.

**Next:** [Find the opportunities](find-the-opportunities.md).
<!-- rung: authored -->

**Go deeper:** [the `product-engineering` intent-fields reference](../reference/intent-fields-and-modes.md) — the fields, modes and projection profiles these skills read and write.
<!-- rung: authored -->
