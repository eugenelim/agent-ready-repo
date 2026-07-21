# Spec: author-brief-docs

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
changelog. This applies to the spec body only — `plan.md` keeps its own
changelog of how the approach evolved. -->

## Objective

A user who receives unstructured external input — an email thread, a stakeholder message, a Linear issue, a verbal sketch — can turn it into a DoR-compliant product brief using the `author-brief` skill and immediately queue it for decomposition. This spec closes the documentation gap for that intake path: a how-to guide that walks the user through `author-brief` end to end, a DoR gate section in the existing brief-field reference that defines the four eligibility fields, and a patch to the `receive-brief` how-to's decision table that names `author-brief` as its peer entry point. Together, these let any reader find the right skill for their input and know exactly what "DoR-ready" means without consulting SKILL.md.

## Boundaries

### Always do

- Write every guide in present tense (retcon discipline — the skill already ships).
- Follow Diátaxis conventions: the how-to is task-oriented (what to type, what to expect back); the reference addition is information-oriented (field definitions only, no procedure).
- Link the how-to to the existing `receive-brief` how-to as the explicit handoff for the next step.
- Update `docs/guides/core/README.md` to list the new how-to under the How-to section.

### Ask first

- Any change to the `author-brief` SKILL.md or its procedure — this spec is docs only; SKILL.md is the source of truth, the guides are derived documentation.
- Adding a new Diátaxis bucket or subdirectory under `docs/guides/core/` beyond the existing four.

### Never do

- Change the `author-brief` skill behaviour or procedure (docs must describe the existing skill, not redesign it).
- Add any code, script, or configuration change — this is a docs-only spec.
- Create a new `dor-gate-fields.md` reference doc — DoR gate fields are added as a section to the existing `product-brief-fields.md` (user confirmation 2026-07-21).
- Duplicate the `receive-brief` how-to's content — link to it, don't copy it.

## Testing Strategy

Goal-based checks throughout: each AC resolves to a `grep` or `ls` verifying file existence or named content, with a final manual read-through of the how-to confirming it is followable end-to-end without consulting SKILL.md.

## Acceptance Criteria

- [x] `docs/guides/core/how-to/intake-an-external-brief.md` exists.
- [x] The how-to opens with a "Is `author-brief` the right entry point?" decision table naming `author-brief`, `receive-brief`, and `new-spec` with their respective triggers.
- [x] The how-to covers the full `author-brief` flow: ingest → identify DoR fields present/missing → elicit (insist on Outcome; offer defaults for the rest; surface Rabbit holes gap) → confirm slug → create brief file → queue in `workspace.toml` (including the three `workspace.toml` branch outcomes: happy path queues the brief; no/unparseable `workspace.toml` → file-only + named diagnostic; multiple active initiatives → prompt for selection) → handoff.
- [x] The how-to names the `author-brief` / `receive-brief` boundary explicitly using both halves: "`author-brief` stops at draft" and "decompose into specs" (or equivalent phrasing).
- [x] The how-to ends with a "Next step" sentence linking to `receive-a-product-brief-and-decompose-it-into-specs.md`.
- [x] `docs/guides/core/reference/product-brief-fields.md` body-sections table includes rows for `Rabbit holes` and `Status`; the "DoR gate" section defines the four eligibility fields — Outcome, Appetite, Rabbit holes (≥1), Spec map skeleton (≥1 placeholder row) — frames them as "required to reach `Ready`" (not simply "required"), and states that `author-brief` elicits these fields but sets `Status: Draft` only; `receive-brief` sets `Status: Ready` after decomposition is confirmed.
- [x] `docs/guides/core/reference/product-brief-fields.md` opening paragraph and any callout no longer attribute brief creation/elicitation solely to `receive-brief`; attribution reflects the two-skill split (`author-brief` creates the draft; `receive-brief` decomposes into specs and marks Ready).
- [x] `docs/guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md` decision table includes an `author-brief` row for the "unstructured external input" trigger.
- [x] `docs/guides/core/README.md` lists `intake-an-external-brief.md` under the How-to section.

## Assumptions

- Technical: `docs/guides/core/` has `how-to/`, `reference/`, `explanation/`, `tutorials/` subdirectories following Diátaxis (source: `ls docs/guides/core/`)
- Technical: `reference/product-brief-fields.md` exists and covers Outcome, Appetite, Scope, Spec map — but has no DoR gate section or Rabbit holes definition (source: `docs/guides/core/reference/product-brief-fields.md` read)
- Technical: `how-to/intake-an-external-brief.md` does not yet exist; `README.md` confirms the gap (source: `ls docs/guides/core/how-to/`)
- Technical: `receive-brief` how-to decision table does not name `author-brief` as a peer entry point (source: `docs/guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md` read)
- Process: RFC-0064 P3 phase-slice doctrine — tooling already shipped, this spec delivers the doc slice (source: `workspace.toml` P3 comment)
- Product: DoR gate fields added as a section to existing `product-brief-fields.md`, not a new doc (source: user confirmation 2026-07-21)
- Product: How-to includes a handoff sentence + link to `receive-brief` guide (source: user confirmation 2026-07-21)
- Product: `receive-brief` how-to decision table updated to name `author-brief` (source: user confirmation 2026-07-21)
