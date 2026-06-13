# Brief: <one-line outcome>

> **This is a template, not a schema.** It shows the *shape* of a received
> product brief — a PRD, a solution handoff, an externally-authored packet of
> work. Copy it to `docs/product/briefs/<slug>.md` and fill in what you have.
> The `receive-brief` skill elicits the load-bearing fields conversationally
> and never rejects a half-formed brief for non-conformance, so an empty
> heading is a prompt, not an error. Keep only the sections that earn their
> place.

- **Slug:** `<slug>` <!-- kebab-case; matches the filename and the `Brief:` back-link on derived specs -->
- **Received:** YYYY-MM-DD
- **Owner:** <who owns delivering this repo's slice>
- **Epic:** <!-- optional: id/link of an external coordinator (a tracker epic, an integration repo) when this repo's work is one slice of a cross-repo effort. Omit when there is none. -->
- **Parent intent:** <!-- optional: when this brief is one per-component slice of a larger product intent, the upstream `intent` it was projected from. Distinct from `Epic:` — `Epic:` names an external *coordinator*; this names the *product intent* upstream. Carried as provenance; never interpreted. Omit when there is none. -->

## Outcome

<!-- LOAD-BEARING. The problem and the user-facing outcome, in the user's
terms. What changes for them when this is delivered? This is the one field
the brief cannot do without. -->

<one paragraph: the problem and the outcome>

## Success metrics

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

## Appetite

<!-- A *constraint*, not an estimate: how much time/effort this outcome is
worth ("a few weeks, not a quarter"). It bounds the decomposition — slices
that don't fit the appetite get cut or flagged, not silently absorbed. -->

<the appetite>

## User stories

<!-- OPTIONAL (Shape B). When product supplies stories, give each an id
(`US-1`, `US-2`, …) and trace it to the satisfying spec's acceptance criteria
with a `Satisfies: US-n` marker on those ACs. Omit this whole section for a
no-stories outcome brief (Shape A); the spec boundaries are then derived from
Outcome + Scope and coverage is spec-granular. -->

- **US-1.** As a <role>, I want <capability>, so that <benefit>.
- **US-2.** …

## Spec map

<!-- Coverage table. The Status column is AUTO-DERIVED from each spec's own
`Status:` field by the coverage lint — do not hand-edit it. Add one row per
derived spec as `receive-brief` scaffolds it; each derived spec carries a
`Brief: <slug>` back-link. A brief is *delivered* only when every mapped spec
is Shipped; an empty map is never delivered. (Shape B adds a `Story` column
linking each row to the `US-n` it satisfies.) -->

| Spec | Status |
| --- | --- |
| `<feature-slug>` | <auto> |
