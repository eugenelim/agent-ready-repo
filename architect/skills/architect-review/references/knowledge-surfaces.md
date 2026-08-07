# Knowledge surfaces — checking the design was grounded

A review is only as honest as the facts it lets stand. Inside an enterprise,
the most expensive review misses are the *factual* ones — a design that
duplicates a service that already exists, violates a mandated standard, or
collides with work already in flight, asserted as settled fact and waved
through because the rubric only checked the artifact's *shape*. This reference
is loaded **only when** the artifact under review asserts grounding-relevant
claims (see *Detection* below); when it makes no such claims, this file is never
loaded.

This is the **verification lens**: the eight areas below are the kinds of claim
a review checks for *grounding*. The review does **not** consult these surfaces
to *build* a design and does **not** redesign — that is `architect-design`'s
job. It checks that the design under review *was* grounded, and flags any claim
asserted as fact without a cited surface and without an "unverified — confirm"
marker, plus any available surface the design ignored. **This taxonomy is the
verification-lens reuse of `architect-design`'s knowledge-surfaces core: the
eight areas and the modality×space axis are the shared canonical core — only the
trigger column, this lens paragraph, and the detection/degrade framing change.**

## The eight knowledge areas (MECE)

Each area answers one question. Check the ones the artifact's claims turn on —
not all eight on every review.

**What "grounded" means.** A claim is grounded when it **cites a knowledge
surface** (the catalogue, the standard, the ADR, the in-flight ticket) **or**
carries an explicit **"unverified — confirm"** marker that hands the check to
the reader. A claim asserted as bare fact with *neither* is the flaggable
failure — not because it's necessarily wrong, but because the design gives the
reader no way to tell. (Read the trigger column below against this definition.)

| # | Area | The question it answers | Flag when the artifact… |
|---|---|---|---|
| 1 | Business domain & meaning | What do the terms, capabilities, and business rules *mean*? | uses an ambiguous domain term or business rule as settled fact where its meaning is contestable and ungrounded |
| 2 | Current landscape | What systems, services, data, and ownership *exist* today? | asserts a system, service, or ownership *exists* (or doesn't) as fact with no cited surface and no "unverified" marker |
| 3 | Interfaces & contracts | What can I integrate with, and on what *terms*? | states an integration's availability or contract *terms* as fact without grounding |
| 4 | Operational reality | How does it *behave* in production (SLOs, incidents, failure modes)? | claims production behaviour (SLOs, capacity, failure modes) as fact without grounding |
| 5 | Constraints & standards | What *must / must-not* I do (policies, approved tech, security rules)? | asserts a mandated standard, policy, or approved-tech — or claims *compliance* with one — without grounding |
| 6 | Patterns & references | How is this *done well* here (reference architectures, golden paths)? | claims an approved reference pattern or golden path exists (or that none does) without grounding |
| 7 | Decisions & rationale | *Why* is it this way; what's *deprecated*? | relitigates or contradicts a settled decision, or revives a deprecated approach, as though the question were open |
| 8 | In-flight & roadmap | What's *changing* or being built in parallel? | asserts what parallel or roadmap work is (or isn't) happening as fact without grounding |

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

## Detection — find surfaces to check against, name no tools

A knowledge surface can take **any form** — an MCP knowledge tool, an internal
CLI, an in-repo doc set, a search API. The review therefore reasons about
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

**Detection serves only the optional spot-check path.** Unlike the design lens,
the review does **not** need a surface to do its job: it flags ungrounded
load-bearing claims **whether or not** any surface is reachable. If a surface
*is* reachable, you **may** spot-check the load-bearing claims against it — to
confirm or refute them, never to supply a better design. A spot-check that a
surface actually **refutes** is a *stronger* finding than "unverified": name the
surface, and raise the severity accordingly (a refuted load-bearing claim is at
least major, blocker if acting on it would be unsafe). A spot-check that merely
**fails to confirm** is not a refutation — it stays an "unverified — author to
confirm" flag. If none is reachable, you still flag the unverified claims for
the author to confirm. So detection is never the primary action, and no "consult
the areas to author a design" framing belongs in a review.

- **Internal only.** A general **public web search / fetch** tool is *not* an
  internal knowledge surface — it can't confirm claims about *your* organisation.
  Don't count it, and don't treat a web hit as enterprise grounding.

### Three honesty rails

- **Name what you checked against.** State in the review which surface you
  verified a claim against, or **"none"**. A grounding finding that doesn't say
  what it was (or wasn't) checked against is self-attested, not auditable.
- **Never fabricate a "ground truth."** Do not invent a contradicting fact to
  declare a claim *wrong*. When you can't verify a claim, flag it as **unverified
  — author to confirm**, not as false. A confident wrong correction is worse
  than an honest "this needs grounding." (This is the review-side inversion of
  the design lens's never-fabricate rule.)
- **One source is weak corroboration.** A single surface can be stale or wrong
  (the area-7 failure mode). Confirming a claim against one unconfirmed surface
  is not proof — note the residual uncertainty rather than marking the claim
  settled.

## When no surface is reachable — flag, don't fabricate

When you cannot reach a surface to check a claim, the review does **not** pass
the claim by default, and does **not** invent a verdict on its truth. It flags
each ungrounded load-bearing claim as **"unverified — author must confirm
against \<the relevant area's surface\>"** and moves on. The author, who has the
enterprise context, closes the gap; the review's job is to make the gap visible,
not to guess across it.

## What to flag, and how hard

Two conditions are flaggable:

- **(a) An ungrounded load-bearing claim** — a landscape / standards / in-flight
  / interface fact (areas 2–5, 7–8 most often) asserted as fact with neither a
  cited surface nor an "unverified — confirm" marker.
- **(b) An available surface the design ignored** — a relevant knowledge surface
  was reachable and the design didn't reconcile a load-bearing claim against it.

Map the finding's severity onto the skill's existing glossary:

- 🟥 **blocker** — the verdict turns on the claim *and* acting on it as fact
  would be unsafe or misleading (e.g. "reuse service X" when X's existence is
  unverified, or "TLS 1.3 is mandated" driving a security posture).
- 🟧 **major** — a load-bearing claim the proposal leans on is ungrounded, but
  acting on it isn't unsafe so much as unverified.
- 🟨 **minor** — an ungrounded claim the design doesn't actually lean on, or a
  citation that should be tightened.

Grounding findings flow into the verdict and the findings list (or the
risk register in well-architected lens mode) like any other finding — tagged,
ordered by severity, each with a concrete fix ("cite the source, or mark it
unverified and route it to Open Questions"). The review flags; it does not
rewrite the design.
