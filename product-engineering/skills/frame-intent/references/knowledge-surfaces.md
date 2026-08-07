# Knowledge surfaces — framing an intent on the enterprise's own knowledge

A product intent is only as good as the context it's framed on. Inside an
enterprise, the most expensive framing errors come from shaping an intent
against the framer's *recall* instead of the organisation's *reality* — betting
on an outcome a team is already delivering, framing an opportunity on a misread
of what a domain term means, missing the operational pain that is the real job.
This reference is loaded **only when** the skill detects that the environment
exposes a knowledge-retrieval surface (see *Detection* below); when none is
present, the skill degrades gracefully and never loads this file.

This is the **problem-framing lens**: the four areas below are the questions a
*framer* asks of the organisation while shaping an intent — what the outcome and
the opportunity must be grounded in. The *design* questions — interfaces,
standards, reference patterns, prior decisions — belong to the
`architect-design` skill's reference, not here (see *Shared canonical core*).

## The four problem-framing areas

A **strict subset** of the eight-area knowledge taxonomy, selected for the
problem-framing lens. Each area answers one question. Consult the ones your
intent turns on — not all four on every run.

| # | Area | The question it answers | Weight | Consult it when… |
|---|---|---|---|---|
| 1 | Business domain & meaning | What do the terms, capabilities, and business rules *mean*? | **primary** | you're naming the outcome or the opportunity and a domain term or rule could be read more than one way — frame on the org's meaning, not your guess |
| 8 | In-flight & roadmap | What's *changing* or being built in parallel? | **primary** | before you commit to an outcome, to check the same bet isn't already in flight — so you don't frame a duplicate or miss a dependency |
| 2 | Current landscape | What systems, services, data, and ownership *exist* today? | brownfield-only | the intent is **brownfield** and the opportunity must account for the existing experience or process (this is the area the maturity gate routes to — see `current-state-inputs.md`) |
| 4 | Operational reality | How does it *behave* in production (SLOs, incidents, failure modes)? | light | the opportunity is driven by an operational pain — a guardrail metric that's slipping, a recurring incident — and you need to ground it in how the real system runs |

Areas 1 and 8 are the load-bearing pair for framing: *meaning* keeps the
opportunity honest, *in-flight* keeps the bet non-duplicative. Area 2 is gated
on brownfield maturity; area 4 is a light touch, used only when the job itself
is operational.

### Why the other four areas are deliberately omitted

The full taxonomy has eight areas. This reference omits four — **(3) interfaces
& contracts, (5) constraints & standards, (6) patterns & references, (7)
decisions & rationale** — on purpose. They are *solution-design* knowledge: how
to integrate, what tech is mandated, which reference architecture to follow, why
a past design went the way it did. Those are the questions the `architect-design`
skill asks, and pulling them in here would drift product-engineering out of
problem space and into solution space — exactly the slide the pack's
opportunity-stays-solution-independent discipline exists to prevent. If a framing
conversation starts needing them, that's the signal the work has moved past
framing and into design; hand it to the architect lens.

### Shared canonical core — keep the two copies aligned

The full eight-area taxonomy and its **modality × space** organising axis are
the **shared canonical core**, defined canonically in the architect reference
(`architect-design/references/knowledge-surfaces.md`). This file is the
**problem-framing projection** of that core: it carries the four problem-relevant
areas under a problem-framing lens and omits the four solution-design areas. Each
area's name, the question it answers, and its place on the axis are **unchanged**
from the core; only (a) which areas appear, (b) their consult triggers, and (c)
this lens paragraph differ. **When the canonical core changes, update both
copies** so they don't diverge.

Where the four selected areas sit on the axis:

- **Descriptive** — area 1 (problem space) and areas 2 / 4 (solution space:
  facets of the current system).
- **Anticipatory** — area 8 (what's coming).

The omitted modalities — **normative** (area 5), **advisory** (area 6), and
**historical** (area 7) — and the third current-system facet, **interfaces**
(area 3), are all the design lens; that's why the subset has no normative,
advisory, or historical row.

**The one adjacency seam this subset keeps:** areas 2 and 4 are two *facets of
the current system*, not duplicates — *what exists* (a service/data catalogue,
ownership) and *how it runs* (SLOs, incidents, failure modes). They come from
different sources and answer different questions; keep them distinct rather than
collapsing them into "the landscape." (The canonical core has a third facet here
— area 3, *how to call it* — which this problem-framing subset omits.)

## Detection — find surfaces, name no tools

A knowledge surface can take **any form** — an MCP knowledge tool, an internal
CLI, an in-repo doc set, a search API. The skill therefore reasons about
*capabilities*, never specific tools. **Hardcode no tool or CLI name here or in
the skill body.**

Discover what's reachable from the session itself:

- If your harness **defers tools** behind a search/registry, issue a search for
  retrieval-shaped capabilities (a tool that *searches / queries / looks up /
  retrieves* over internal knowledge, or a knowledge CLI on `PATH`).
- If your harness **loads tools eagerly**, read your available tool list for the
  same shape.
- An in-repo knowledge set (`docs/`, a domain glossary, a product wiki export)
  is a surface too — you can already read it.

If a surface is found, consult the areas above that your intent turns on. If a
found surface returns nothing useful, treat that as *absent* for that area.

Three honesty rails on detection:

- **Internal only.** A general **public web search / fetch** tool is *not* an
  internal knowledge surface — it can't answer these areas about *your*
  organisation. Don't count it, and don't claim enterprise grounding from it.
- **Name what you detected.** State in the intent's `Assumptions` which surface
  you used (or "none detected"), so detection is auditable rather than
  self-attested. This
  closes the "claim a surface to skip the ask" path: declaring "none" *is* the
  trigger for the degrade rule below.
- **One source is not confirmation.** A single surface can be stale or wrong.
  Carry a fact from one unconfirmed source at **lowered confidence** until
  corroborated — the same discipline as the absent path, applied to the present
  path — and route that marker into the intent's `Assumptions`, as in degrade
  rule (a) below.

## Degrade gracefully when a surface is absent

Behave **compose-if-present, degrade-if-absent** — only more honestly. (Unlike
the architect skill, `frame-intent` does not compose with a `desk-research` step
today; this is the generic compose/degrade discipline, not a reuse of that one.)

- **(a) Ask, and lower confidence.** Ask the user for the missing domain /
  landscape / in-flight context, and lower the confidence of any part of the
  intent — the outcome or the opportunity — that leaned on knowledge you
  couldn't verify. Carry the lowered-confidence marker into the intent's
  `Assumptions`, where `de-risk-intent` will pick the riskiest and test it.
- **(b) Never fabricate.** Do not invent domain meanings, landscape facts, or
  in-flight context. An honest "unverified — confirm with your domain / product
  team" beats a confident guess.
- **(c) Respect sensitivity.** Treat any source marked sensitive or read-only as
  **ask-before-quoting**: cite that it exists and ask whether to pull it in,
  rather than reproducing its content verbatim.
