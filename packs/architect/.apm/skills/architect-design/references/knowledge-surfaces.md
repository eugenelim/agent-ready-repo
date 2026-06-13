# Knowledge surfaces — consulting the enterprise's own knowledge

A design is only as good as the context it's built on. Inside an enterprise,
the most expensive errors come from designing against the architect's *recall*
instead of the organisation's *reality* — duplicating a service that already
exists, violating a mandated standard, colliding with work already in flight.
This reference is loaded **only when** the skill detects that the environment
exposes a knowledge-retrieval surface (see *Detection* below); when none is
present, the skill degrades gracefully and never loads this file.

This is the **design lens**: the eight areas below are the questions a designer
asks of the organisation. (A problem-framing lens — business domain first —
belongs to the product-engineering skills, not here.) **When this taxonomy is
reused under another lens, the eight areas and the modality×space axis are the
shared canonical core — only the per-area triggers, this lens paragraph, and the
detection/degrade framing change (as the `architect-review` verification-lens
reuse does).**

## The eight knowledge areas (MECE)

Each area answers one question. Consult the ones your current design decision
turns on — not all eight on every run.

| # | Area | The question it answers | Consult it when… |
|---|---|---|---|
| 1 | Business domain & meaning | What do the terms, capabilities, and business rules *mean*? | a term or rule in the design is ambiguous and you'd otherwise guess |
| 2 | Current landscape | What systems, services, data, and ownership *exist* today? | the design must fit, reuse, or avoid duplicating something that exists |
| 3 | Interfaces & contracts | What can I integrate with, and on what *terms*? | the design calls or is called by another system |
| 4 | Operational reality | How does it *behave* in production (SLOs, incidents, failure modes)? | the design's resilience/NFRs depend on how the real system runs |
| 5 | Constraints & standards | What *must / must-not* I do (policies, approved tech, security rules)? | choosing tech, naming, integration, or a security posture |
| 6 | Patterns & references | How is this *done well* here (reference architectures, golden paths)? | an approved shape probably exists for what you're about to invent |
| 7 | Decisions & rationale | *Why* is it this way; what's *deprecated*? | the design risks relitigating a settled decision or reviving a banned approach |
| 8 | In-flight & roadmap | What's *changing* or being built in parallel? | the design might collide with, depend on, or duplicate active work |

### Why these eight don't overlap (MECE)

The set is mutually exclusive along two axes — **modality** (what kind of
statement) × **space** (problem vs solution):

- **Descriptive** — area 1 (problem space) and areas 2/3/4 (solution space).
- **Normative** — area 5 (what must).
- **Advisory** — area 6 (what's recommended).
- **Historical** — area 7 (why it's so).
- **Anticipatory** — area 8 (what's coming).

**The one adjacency seam:** areas 2, 3, and 4 are three *facets of the current
system*, not duplicates — *what exists* (a service catalogue), *how to call it*
(an API/schema registry), and *how it runs* (runbooks, SLOs, incident history).
They come from different sources and answer different questions; keep them
distinct rather than collapsing them into "the landscape."

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
- An in-repo knowledge set (`docs/`, an architecture index) is a surface too —
  you can already read it.

This mirrors how the `research` skill enumerates "retrieval-shaped tools
registered in the session." If a surface is found, consult the areas above that
your design decision turns on. If a found surface returns nothing useful, treat
that as *absent* for that area.

Three honesty rails on detection:

- **Internal only.** A general **public web search / fetch** tool is *not* an
  internal knowledge surface — it can't answer these areas about *your*
  organisation. Don't count it, and don't claim enterprise grounding from it.
- **Name what you detected.** State in the concept which surface you used (or
  "none detected"), so detection is auditable rather than self-attested. This
  closes the "claim a surface to skip the ask" path: declaring "none" *is* the
  trigger for the degrade rule below.
- **One source is not confirmation.** A single surface can be stale or wrong
  (the area-7 failure mode). Carry a fact from one unconfirmed source at
  **lowered confidence** until corroborated — the same discipline as the
  absent path, applied to the present path — and route that marker into the
  concept and the design doc's Open Questions, as in degrade rule (a) below.

## Degrade gracefully when a surface is absent

Behave exactly as the skill already does when `research` is absent — **compose
if present, degrade if absent** — only more honestly:

- **(a) Ask, and lower confidence.** Ask the user for the missing landscape /
  standards / in-flight context, and lower the confidence of any proposal that
  leaned on knowledge you couldn't verify (carry the lowered-confidence marker
  into the concept and the design doc's Open Questions).
- **(b) Never fabricate.** Do not invent landscape facts, standards, reference
  architectures, or in-flight context. An honest "unverified — confirm with your
  architecture team" beats a confident guess.
- **(c) Respect sensitivity.** Treat any source marked sensitive or read-only as
  **ask-before-quoting**: cite that it exists and ask whether to pull it in,
  rather than reproducing its content verbatim.
