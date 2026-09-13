---
title: "Start the work"
summary: "Bring a request in through one door and let it be routed, rather than guessing which skill owns it."
pack: core
kind: how-to
order: 1
---

# Start the work

**Step 1 of 4 — Start the work**
<!-- rung: packs/core/JOURNEY.md -->

**What changes:** A raw request becomes a routed one, with the reason for the route recorded.
<!-- rung: packs/core/JOURNEY.md -->

**What you need first:** A request, however vague, and a repository with the pack installed.
<!-- rung: authored -->

*Skipping costs:* You pick the skill yourself, and a wrong guess costs a whole loop before it shows.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The two-room model](../explanation/two-room-model.md) explains why shaping and building are separate rooms.
- [Why work begins with an artifact](../explanation/why-work-begins-with-an-artifact.md) explains why the loop refuses to start from a chat message.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `workspace-status` | Nothing — it reads what exists | The queue: what is ready, active, blocked, and why. | Optional |
| `work-intake` | A request, however vague | The request routed to the skill that owns it. | Required |
| `intake-intent` | An outcome worth recording | A repository intent, at the right level. | Optional |
| `adapt-to-project` | A freshly installed pack | The pack's context adapted to what this repository actually is. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work; it
names the spec directory and stays the same until the work closes.

<!-- rung: packs/core/JOURNEY.md -->

## Run `workspace-status` — what is in flight

**You type:**
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

```
What is in the workspace right now?
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

> **Agent:** Done — I've written the current queue — what is ready to start, what is active, and what is blocked with the reason. Nothing was written to disk.

**You push back:**
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

> **You:** You listed three specs as ready but one has no plan. Re-read the queue and report what actually blocks each.
>
> **Agent:** I re-read it and moved that spec to blocked with its finding code, which is a missing plan.

**Output varies** with what is registered in `workspace.toml` and how much of it is stale.
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Compare one reported ready item against its spec on disk; this surfaces a queue read from membership rather than from state.
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

**Watch out for:** Queue membership and readiness are different things, and a stale entry looks identical to a live one. Notice items reported ready with no finding code and no recent change.
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/core/.apm/skills/workspace-status/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Workspace — <initiative>

Ready:   <slug> — spec approved, plan present
Active:  <slug> — executing
Blocked: <slug> — missing_plan: create and approve the plan before dispatch

What to run next: <skill>
```

*Section shape only. This skill reports in the session rather than writing a file — confirm the shape against what you get back.*

## Run `work-intake` — the front door

**You type:**
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

```
I need to do something about the flaky login test, but I am not sure if it is a bug or a design problem.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

> **Agent:** Done — I've written the request classified and routed to the skill that owns it, with the reason for the route. Nothing was written to disk.

**You push back:**
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

> **You:** You routed this to bug-fix, but we have not established whether the behaviour is wrong or the test is. Route it somewhere that decides that first.
>
> **Agent:** I re-routed it to a diagnosis step first and noted that the bug-fix route stays open once the behaviour is settled.

**Output varies** with how well formed the request is and what already exists in the workspace.
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (sufficient-for-next):** Ask what the route assumed about your request; this surfaces a classification made on wording rather than on substance.
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

**Watch out for:** A confident route can be wrong in a way that costs a whole loop. Notice a route chosen from a keyword in your sentence rather than from the state of the work.
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/core/.apm/skills/work-intake/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Routed: <request>

Classification: <build | shape | research | signal>
Owner: <skill>
Why: <what in the request decided the route>

Next: run <skill>
```

*Section shape only. This skill reports in the session rather than writing a file — confirm the shape against what you get back.*

## Run `intake-intent` — admit an intent

**You type:**
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

```
Admit this as a repository intent: we want new contributors productive without reading the whole architecture.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

> **Agent:** Done — I've written an intent recorded at the level it belongs, with its status and parent if it has one to `docs/product/intents/<slug>.md`.

**You push back:**
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

> **You:** You recorded this at feature level, but it is a capability that several features would serve. Re-level it.
>
> **Agent:** I re-levelled it to capability and left the feature-shaped part as a note for decomposition later.

**Output varies** with how well formed the outcome is and whether a parent intent exists.
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (falsifiable):** Ask what would sit one level above this intent; this surfaces an intent recorded at the wrong altitude.
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

**Watch out for:** Level is easy to get wrong and expensive later, because decomposition inherits it. Notice an intent that names something a single change could deliver but is tagged as a capability, or the reverse.
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

**Where it lands:** `docs/product/intents/<slug>.md`.
<!-- rung: packs/core/.apm/skills/intake-intent/SKILL.md -->

**What it looks like:**
<!-- rung: packs/core/.apm/skills/intake-intent/assets/minimal-intent.md -->

```markdown
# <intent title>

- **Status:** Draft
<optional level>

## Outcome

<bounded outcome>

## Boundary

<bounded boundary>

## Owner

<bounded owner>

## Unresolved questions
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Run `adapt-to-project` — fit the pack to this repo

**You type:**
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

```
Adapt the installed packs to this repository.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

> **Agent:** Done — I've written the pack's context adapted to this repository's actual stack, conventions and layout. Nothing was written to disk.

**You push back:**
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

> **You:** You wrote a reference architecture even though we already have one in `docs/architecture/`. Point at it instead of duplicating it.
>
> **Agent:** I removed the generated one and pointed at the existing source, keeping only the two concerns it does not cover.

**Output varies** with how much architecture documentation already exists and how conventional the repository is.
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask which existing file each adapted claim was read from; this surfaces context invented rather than discovered.
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

**Watch out for:** Adapting can generate a document the repository already has, and the duplicate then drifts. Notice anything created where a source already existed.
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/core/.apm/skills/adapt-to-project/SKILL.md -->

**What it looks like:**
<!-- rung: packs/core/.apm/skills/adapt-to-project/assets/reference.md -->

```markdown
# Optional reference architecture

> Use this only when no existing architecture source covers the concern and the
> repository wants fuller architecture documentation. Preserve an adopter's
> existing architecture source, location, terminology, and authority. Do not
> create this file merely to match the core pack.
>
> Once accepted, this document records the repo's *golden path* — the stack, the
> internal building blocks, the component stereotypes, and the cross-cutting
> standards that new work is expected to **conform to**. A feature's low-level
> design (in its plan) reads this as steering: it names which building blocks it
> reuses and which standards it follows, and it justifies any deviation.
>
> This is the **normative** sibling of `overview.md`. `overview.md` *describes*
> how the code is organized today (a map you read to find things);
> `reference.md` *prescribes* how new code should be shaped (a target you build
> toward). When the two disagree, that gap is either drift to fix or a decision
> to record.
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Where this leads

**Done with this step:** You can move on when the route names a skill and states what in your request decided it.
<!-- rung: authored -->

Stage 1 of four, and the front door for every kind of request. This is the only step you should have to remember — the rest are named for you.

Work often arrives here already shaped. If it came from [Hand it to build](../../product-engineering/how-to/hand-it-to-build.md) in the `product-engineering` guidebook, you already hold a slice and can go straight to [Write the contract](write-the-contract.md) — bring the slug with you.

**Next:** [Write the contract](write-the-contract.md).
<!-- rung: authored -->

**Go deeper:** [the `core` pack reference](../explanation/core-pack.md) — how the loop, the gates and the reviewers fit together.
<!-- rung: authored -->
