---
title: Review an architecture artifact
summary: Obtain a severity-ranked verdict and independent review for a finished-enough assessment, design, or diagram artifact.
pack: architect
kind: how-to
---

# Review an architecture artifact

**Use this when:** You have a finished-enough artifact — assessment report, design doc, diagram, RFC, or ADR — and want severity-tagged findings rather than a design or assessment conversation.
**Prerequisites:** A concrete artifact to paste or point at; the `architect` pack installed.
**Result:** A verdict (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT), findings ordered by severity with suggested fixes, and strengths to preserve.

:::note
Get a severity-tagged critique of an assessment report, design doc, diagram,
RFC, or ADR out of the `architect-review` skill. Want the repository assessed
rather than the report reviewed? Ask “Assess architecture and provide an action
plan” and follow [Assess a repository](assess-a-repository.md).
:::

You have an artifact and you want to know what's wrong with it. Paste it, ask for a review, and the [`architect-review`](../../../packs/architect/.apm/skills/architect-review) skill walks the right rubric for its type and hands back a verdict plus findings ordered by severity. Reviews render inline; they're throwaway by design.

## Just ask

Paste the artifact, or point at a known path, and ask:

- "Review this design doc."
- "Review this architecture assessment for evidence and action traceability."
- "What's wrong with this RFC?"
- "Is this C4 diagram any good?"

The skill identifies the artifact type and routes to a matching rubric—
assessment report, design doc, C4 container/context diagram, sequence diagram,
state diagram, ER diagram, or a generic rubric. Assessment review checks scope,
evidence, model coherence, heat use, lens coverage, claim calibration, and action
traceability from the artifact; it does not rescan the repository.

For a design doc, the review also runs a reduction pass. It challenges a full
design where a Stage-0 concept would answer the question, a document with no
real choice, and each unnecessary component, service, dependency, boundary, or
custom mechanism. It looks for an ignored existing, standard, native, or
provider capability; speculative scale, configurability, compatibility, or
extensibility; and complexity that lacks a named quality attribute and credible
constraint. The intended fix is to remove unsupported complexity or claims,
not to expand the document to defend them.

```text
  artifact type          rubric                  verdict           review body
  ───────────────────────────────────────────────────────────────────────────
  assessment report →  rubric-assessment    ┐
  design doc        →  rubric-design-doc    │
  C4 diagram        →  rubric-c4-diagram    │
  sequence diagram  →  rubric-sequence...   │   SHIP IT
  state diagram     →  rubric-state...      ├─► SHIP WITH CHANGES   ┐ verdict
  ER diagram        →  rubric-er-diagram    │   MAJOR REWRITE       │ summary
  none of these     →  rubric-generic       ┘   WRONG ARTIFACT      │ findings
                                                                    │ what's
  walk every check first, THEN order findings by severity ─────────┘ working

  each finding ─►  where  (verbatim quote / section)
                   what's wrong  (the rubric check that failed)   + severity:
                   suggested fix (concrete, paste-able)             🟥 blocker
                                                                    🟧 major
                                                                    🟨 minor
                                                                    ⚪ nit
```

## What you get back

The verdict leads. You never scroll past twelve findings to learn the artifact is broken. It's one of four:

- **SHIP IT** — zero blockers, at most a couple of minors. Rare, and the skill says so when it happens.
- **SHIP WITH CHANGES** — the shape is right; majors exist but nothing ship-stopping.
- **MAJOR REWRITE** — two or more blockers, or one that invalidates the structure.
- **WRONG ARTIFACT** — the artifact answers a question you didn't ask (a sequence diagram when you wanted topology, an ADR when you wanted a design doc). The skill names the right artifact and routes you to it.

Under the verdict: a three-sentence executive summary, then the findings. Each finding names **where** (a verbatim quote or section reference), **what's wrong** (the rubric check that failed), and a **suggested fix** that's concrete and paste-able where it can be. Findings carry a severity tag:

| Tag | Meaning |
| --- | --- |
| 🟥 blocker | Ship-stopping. Wrong, misleading, or unsafe to act on. |
| 🟧 major | Materially weakens the artifact, but not ship-stopping. |
| 🟨 minor | Worth fixing; the reviewer won't block on it. |
| ⚪ nit | Style or formatting. Optional. |

It closes with **what's working** — two to four specific strengths to *keep* through a rewrite. Not flattery; the skill won't pad this with "clear writing."

## Reviewing for well-architected

There's a second mode, orthogonal to artifact type: ask whether a *design* is well-architected — by provider, by pillar, or against a named concern or workload-class lens, including GenAI and agentic workloads. The skill walks a well-architected rubric and produces a risk register instead of a flat critique. Each finding is tagged **🔧 mechanical** or **🧭 judgment** and paired with a scenario. It reuses the same verdict and severity scale, and it does not auto-fix — it's a critique, not a build loop.

## An independent review — the `design-reviewer` subagent

`architect-review` runs **inline**, in the thread you're already in. That's the right tool when you're reviewing someone else's artifact. But when you just *authored* the design — especially through [`architect-design`](../../../packs/architect/.apm/skills/architect-design)'s convergence loop — reviewing it in the same thread marks your own homework: the context that wrote the draft is biased toward agreeing with it.

For that case the pack ships a sibling **subagent**, `design-reviewer`. It runs the exact same rubric, verdict, and severity / mechanical-judgment tagging, but in a **forked context that hasn't seen the authoring** — seeded only with the artifact, the agreed concept, and the constraints. It's **read-only** (`Read, Grep, Glob`): it flags, it never rewrites your design, and it returns the findings block with no narration. Reach for it when independence matters more than staying in-thread; it's the *fresh-context (preferred)* rung of the convergence loop, with the inline skill and a disciplined cold re-read as the weaker fallbacks. The subagent is self-contained — installing it doesn't require the skill, though where both are present they share one rubric.

## Grounded claims get checked

When an artifact asserts facts about the current landscape, a mandated standard, an external interface, or in-flight work, the skill treats those as claims a reviewer can't take on faith. It flags any such claim that's stated as fact with neither a cited source nor an "unverified — confirm" marker, and it flags any knowledge surface the design ignored. If an internal retrieval surface is reachable in the session it may spot-check the claims and tell you what it checked against. It flags; it never rewrites your design.

## Steered by your `reference.md`

If your repo has a resolved `current-architecture` golden path, the review
measures the artifact against it — your stack, your patterns, your constraints
— so the findings reflect how this codebase is actually built.
`docs/architecture/reference.md` is only the catalogue fallback. No golden path
yet? [Establish your repo's reference architecture](establish-reference-architecture.md)
first.

## When not to reach for it

The skill pushes back rather than reviewing when:

- **Nothing concrete is attached.** “Review our architecture” with no artifact
  is current-state assessment when the implemented system is the object; route
  to [Assess a repository](assess-a-repository.md). Route to design only when the
  user is choosing a future state.
- **The artifact is too thin to critique.** A two-bullet outline is a discussion; the skill won't critique tumbleweeds.
- **You want a conversation, not findings.** If you're still shaping the idea, switch to a design surface.
- **You wrote it this session.** Reviewing your own fresh draft is marking your own homework. The skill asks you (or another agent) to drive the critique — reach for the [`design-reviewer` subagent](#an-independent-review--the-design-reviewer-subagent) to get that independent pass.

## See also

- [Diagram a system](diagram-a-system.md) — produce the diagram you might later send through review.
- [Establish your repo's reference architecture](establish-reference-architecture.md) — the golden path reviews measure against.
- [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md) — what that golden-path file holds.
