---
title: "From idea to a walking skeleton: start a new project"
summary: Create a new governed repository with a recorded foundation and an approved first walking-skeleton spec.
pack: core
kind: tutorial
---

# From idea to a walking skeleton: start a new project

**What you'll build:** A brand-new repo with a recorded foundation (a decision record and a current-architecture golden path at the destinations your repo selects) and a walking-skeleton spec authored and ready to build.
**Prerequisites:** An empty (or nearly empty) repo you can commit to, the `core` pack installed, and a one-paragraph idea or PRD to start from.
**Time:** About 20 minutes.

:::note
At the end of this tutorial you'll have a brand-new repo with a recorded foundation — a decision record and a current-architecture golden path — and a walking-skeleton spec authored and ready to build. `docs/adr/` and `docs/architecture/reference.md` are catalogue fallback candidates; adopter-owned destinations win when policy permits them.
:::

This is a learning walkthrough, not a reference. It uses the `core` pack alone. For the fuller inception — where the `desk-research`, `product-engineering`, and `architect` packs fit around this core spine — see [Run a full inception for a new project](../../_shared/how-to/run-a-full-inception.md). For *why* the skeleton is built this way, read [Why a walking skeleton beats a throwaway prototype](../explanation/walking-skeleton-vs-throwaway.md) afterward; for the foundation step on its own, see [Decide and record your foundation during inception](../how-to/record-your-foundation-during-inception.md).

We'll use one concrete idea throughout: **a URL-shortener service** — an API that takes a long URL and returns a short code, with a datastore behind it. It has real components, so it's a genuine project, not a throwaway.

```text
Start a new project for a URL-shortener service.
```

## Before you begin

You need:

- An empty (or nearly empty) repo you can commit to.
- The `init-project` skill, which ships in the `core` pack. If you haven't installed `core` into this repo yet, do that first:

  ```bash
  python -m pip install agentbundle
  agentbundle install --pack core git+https://github.com/<owner>/<catalogue>
  ```

  Then start a fresh agent session so it picks up the new skill.
- A discovery shape to feed in — for this tutorial, a one-paragraph PRD is enough: *"Users paste a long URL and get back a short link they can share; links resolve fast and never expire. MVP: create a short link and resolve it."* (In real use this comes from the `desk-research` skill, an `intent` shaped by `frame-intent` when the `product-engineering` pack is installed — an optional upstream source — or an `author-delivery-brief` brief; a written PRD works the same way.)

## Step 1 — Start the flow and pass the trigger gate

Run the `init-project` skill and tell it your idea: *"Start a new project — a URL-shortener service."*

The skill runs its **trigger gate** first. Because a shortener has real decisions ahead (an API, a datastore, a transport), the gate continues into the flow rather than sending you to scaffold a one-off script.

You should see the skill confirm there are real structural decisions and move on to ask for your discovery input — not drop you straight into writing code.

:::caution
If you don't see this: if the skill decides to just scaffold and stop, it judged your idea a throwaway. For anything with a datastore and an API, say so explicitly — "this is a maintained service, not a script" — and it will continue.
:::

## Step 2 — Feed in discovery and pass the value gate

Paste your one-paragraph PRD when the skill asks for the discovery input. The skill **consumes** it — it does not go research the idea itself.

**The agent asks:**

```text
What business value does this serve, and what is the smallest MVP?
```

**You answer:**

```text
Users need short links they can share; the MVP creates a short link and resolves it, with no analytics or custom domains.
```

From the PRD it derives the **business value** ("sharable short links that resolve fast") and the **MVP** ("create a short link and resolve it"), and writes the first **brief**.

You should see a new file at `docs/product/briefs/url-shortener.md` capturing the outcome and scope. Open it and confirm the value is stated plainly.

:::caution
If you don't see this: if the skill pauses and asks you to sharpen the idea, the value gate caught a gap — the PRD was too thin to state the value. Add the missing piece (who it's for, what outcome it serves) and continue. That pause is the gate working, not an error.
:::

## Step 3 — Record the foundation

The skill now helps you choose the stack and **record the rationale**. Decide the few load-bearing things (say: a small HTTP service, a key-value store for the code-to-URL mapping). It asks Core to resolve two independent semantic destinations before any directory, ordinal, index, or file is created:

- a `decision-record` stating what you chose, why, the alternatives, and a re-evaluation date;
- a `current-architecture` golden path instantiated from the arc42 template and filled forward from the decision you just made.

You should see both resolved destinations before their existing confirmation
gates. If the repo has no stronger location evidence, you can confirm the
catalogue fallbacks. A mandatory-policy refusal, ambiguity, unsafe path, or
unavailable external destination stops that artifact without a partial write.

## Step 4 — Author the walking skeleton

Now author the **walking skeleton**: the thinnest slice that wires the real components together end to end. For the shortener, that's *one request that creates a short code and stores it, and one that resolves a code back to the URL* — touching the real API and the real datastore, nothing mocked away.

The skill authors this as a single spec via `new-spec` and hands the build to `work-loop`. It does not build the skeleton itself — orchestrating that build is `work-loop`'s job.

You should see a new `docs/specs/walking-skeleton/` (or similarly named) spec with its own acceptance criteria, and the skill handing off to `work-loop` to build it.

## What you built

You now have a brand-new repo with a **recorded foundation** (an ADR plus `reference.md`) and a **walking-skeleton spec** authored and ready to build — not a throwaway you'll later have to clean up. Commit the foundation:

```bash
git add <resolved-decision-record-path> <resolved-current-architecture-path> docs/product/briefs docs/specs
git commit -m "chore: record foundation and author walking skeleton"
```

From here the project runs the ordinary loop.

## What you have now

You have a repository foundation recorded in a decision record and a
current-architecture golden path, plus a walking-skeleton spec ready to build.
Commit those artifacts, then hand the approved spec to `work-loop`.

## Next steps

- To build the skeleton and every feature after it: the [`work-loop` plan-and-execute how-to](../how-to/plan-and-execute-non-trivial-work.md).
- To go deeper on the foundation step alone: [Decide and record your foundation during inception](../how-to/record-your-foundation-during-inception.md).
- To understand *why* the skeleton is kept-and-minimal rather than a throwaway: [Why a walking skeleton beats a throwaway prototype](../explanation/walking-skeleton-vs-throwaway.md).
