---
title: Create and use your `reference.md`
summary: Commit one real architecture standard and use it immediately to steer a design decision.
pack: architect
kind: tutorial
---

# Create and use your `reference.md`

This tutorial creates a normative foundation. It is separate from a descriptive
architecture assessment: first ask “Assess architecture and provide an action
plan” when you need evidence and hotspots; use this journey when you are ready
to confirm a standard future work must follow.

**What you'll build:** A committed `current-architecture` golden path at your repository's resolved destination, with one real architecture standard used to steer one design decision.
**Prerequisites:** A repo with at least one settled architecture decision and the `adapt-to-project` skill available — see [Prerequisites](#prerequisites) below.
**Time:** 20–30 minutes.

:::note
At the end of this tutorial you'll have a committed golden path with one real section filled in, and you'll have used it to steer one design decision. `docs/architecture/reference.md` is the catalogue fallback, but your adopter-owned destination wins when policy permits it.
:::

This is a learning walkthrough, not a reference. For *why* `reference.md` exists, read [Foundation vs. map](../../core/explanation/foundation-vs-map.md) afterward; for the full section list, see [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md).

```text
How should we establish a reference architecture for our payments platform?
```

## Prerequisites

- A repo with at least one real, settled architecture decision — something your team would hold a pull request to. (If your repo is too early for that, this tutorial won't have anything true to write; come back later.)
- The `adapt-to-project` skill available in your repo.

## Step 1 — Instantiate the template

Run the `adapt-to-project` skill and ask it to propose a reference architecture.
It classifies the implemented-system artifact as `current-architecture`, asks
Core to resolve the destination, then reads your codebase and presents a draft
`reference.md`, section by section, built from the arc42 template it carries.

You should see a proposal with four sections — **Constraints**, **Solution strategy**, **Building-block view / component catalogue**, and **Crosscutting concepts / standards** — each pre-filled with what the skill detected.

## Step 2 — Fill one section for real

You'll fill exactly one section now: **Crosscutting concepts / standards**, with your repo's real error-handling rule. Find that section in the proposal and make the error-handling line state what your code actually does. For example, if every component wraps failures in one shared error type and logs at the boundary, write that:

```markdown
## Crosscutting concepts / standards

- **Error handling.** Every component wraps failures in the shared error type
  and logs once, at the outermost boundary. No component logs-and-rethrows.
```

Accept that section. **Decline** any other section the skill guessed at for now — you can fill the rest later. Declining keeps the foundation honest: it records only decisions you've actually confirmed.

You should see the skill confirm the accepted section and record the declines.

## Step 3 — Write it and commit

Confirm the proposal. The skill writes the accepted section to the resolved,
confined repository destination. If this tutorial's repo has no stronger
destination evidence, you may explicitly accept the offered
`docs/architecture/reference.md` fallback.

Verify and commit:

```bash
cat <resolved-current-architecture-path>
git add <resolved-current-architecture-path>
git commit -m "docs(architecture): add reference.md with error-handling standard"
```

You should see your error-handling rule in the committed file. You now have a foundation — small, but real.

## Step 4 — Use it to steer one decision

Now use what you wrote. The next time you design a feature, its plan's low-level design reads `reference.md` and conforms to it. Try it on a tiny scale: in your next change that can fail, follow the rule you wrote — wrap the failure in the shared error type and log once at the boundary — instead of inventing a new pattern.

That's the whole point of the foundation: the decision was made once, written once, and every later change inherits it instead of re-deciding. For how a feature's design formally reads `reference.md`, see [Spec `Shape:` and the plan's `## Design (LLD)`](../../core/reference/spec-shape-and-lld.md).

## What you did

You instantiated the arc42 template, filled one section with a real standard, committed it, and steered a decision by it. To fill the remaining sections and handle the brownfield and stack-pack routes, continue with [Establish your repo's reference architecture](../how-to/establish-reference-architecture.md).

To check whether the implemented repository actually follows the standard—and
whether that matters for the decision—continue with [Assess a repository and
turn evidence into action](../how-to/assess-a-repository.md).

## What you have now

You have a committed `current-architecture` artifact containing a real standard
your next design decision can follow. Continue by filling the remaining
sections, or assess whether the implemented system conforms to that standard.

## See also

- [Foundation vs. map](../../core/explanation/foundation-vs-map.md) — why `reference.md` and `overview.md` are separate.
- [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md) — the authoritative section list.
- [Establish your repo's reference architecture](../how-to/establish-reference-architecture.md) — the task recipe with all three routes.
- [Assess a repository and turn evidence into action](../how-to/assess-a-repository.md) — compare the normative foundation with implemented and operational evidence.
