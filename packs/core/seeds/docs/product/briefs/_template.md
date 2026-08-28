# Brief: <one-line outcome>

> **This is a template, not a schema.** It shows the *shape* of a received
> product brief — a PRD, a solution handoff, an externally-authored packet of
> work. Copy it to `docs/product/briefs/<slug>.md` and fill in what you have.
> `author-delivery-brief continue` elicits the load-bearing fields conversationally
> and never rejects a half-formed brief for non-conformance, so an empty
> heading is a prompt, not an error. Keep only the sections that earn their
> place.

- **Slug:** `<slug>` <!-- kebab-case; matches the filename. Derived specs back-link this brief by path (`docs/product/briefs/<slug>.md`), not by the bare slug -->
- **Received:** YYYY-MM-DD
- **Owner:** <who owns delivering this repo's slice>
- **Status:** Draft <!-- Draft | Ready | Executing | Shipped -->
- **Source / provenance:** <!-- LOAD-BEARING. A safe, durable reference to the source and, for tracker-origin work, its reviewed revision. Retain a normalized summary; never copy raw external payload. -->
- **Epic:** <!-- optional: id/link of an external coordinator (a tracker epic, an integration repo) when this repo's work is one slice of a cross-repo effort. Omit when there is none. -->
- **Parent intent:** <!-- optional: when this brief is one per-component slice of a larger product intent, the upstream `intent` it was projected from. Distinct from `Epic:` — `Epic:` names an external *coordinator*; this names the *product intent* upstream. Carried as provenance; never interpreted. Omit when there is none. -->

## Outcome

<!-- LOAD-BEARING. The problem and the user-facing outcome, in the user's
terms. What changes for them when this is delivered? This is the one field
the brief cannot do without. -->

<one paragraph: the problem and the outcome>

## Success metrics (optional)

<!-- How will we know the outcome landed? Name observable signals, not
activities. "p95 checkout under 400ms"; "support tickets for password reset
down 50%". Offer your best guess if the brief arrived without them. -->

-
-

## Scope / Non-goals

<!-- The boundary of this repo's slice. Non-goals are as load-bearing as
scope — they stop the decomposition from sprawling. -->

**In scope:**

-

**Non-goals:**

-

## Constraints / Appetite

<!-- A *constraint*, not an estimate: how much time/effort this outcome is
worth ("a few weeks, not a quarter"). It bounds the decomposition — slices
that don't fit the appetite get cut or flagged, not silently absorbed. -->

<the appetite>

## Assumptions / Risks

<!-- LOAD-BEARING. Name known assumptions, risks, design traps, or out-of-bound
explorations. -->

-

## Ready gaps (Draft only)

<!-- Name any missing Outcome, Scope, Non-goals, Constraints / Appetite,
Assumptions / Risks, or Source / provenance detail without inventing it. Remove
this note once the gap is resolved. -->

-

## Rabbit holes (optional)

<!-- Optional prompt for design traps, known uncertainties, and out-of-bound
explorations to skip. -->

-

## Instrumentation (optional)

<!-- How the team will *measure* whether the outcome actually landed — the
telemetry, events, dashboards, or signals that make the Success metrics
observable. Distinct from Success metrics (which state the *target* value;
Instrumentation names the *measurement mechanism*). -->

-

## User stories (optional)

<!-- OPTIONAL (Shape B). When product supplies stories, give each an id
(`US-1`, `US-2`, …) and trace it to the satisfying spec's acceptance criteria
with a `Satisfies: US-n` marker on those ACs. Omit this whole section for a
no-stories outcome brief (Shape A); the spec boundaries are then derived from
Outcome + Scope and coverage is spec-granular. -->

- **US-1.** As a <role>, I want <capability>, so that <benefit>.
- **US-2.** …

## Spec map

<!-- Mechanically present and empty-capable. Add a row only for a confirmed
delivery slice; leave the table with its header only when there are zero such
slices. Only specs belong here; RFCs and ADRs never affect execution or
closure rollups. `author-delivery-brief` owns the coverage and Status-column
mechanics. -->

| Spec | Status |
| --- | --- |
|  |  |

## Governance references (optional)

<!-- RFCs and ADRs that constrain, unlock, or explain delivery. Keep them
separate from the Spec map because governance references do not become
executable slices and do not affect delivery rollups. -->

-

## Design artifacts (optional)

<!-- Links to upstream shaping artifacts (journey maps, screen flows, capability
maps, opportunity assessments) that informed this brief. These are inputs that
shaped what the brief asks for; link them here so the delivery team understands
the design context without re-deriving it. Optional: omit if no upstream shaping
artifacts were produced. -->

-
