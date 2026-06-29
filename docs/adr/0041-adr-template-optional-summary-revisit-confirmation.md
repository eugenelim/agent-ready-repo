# ADR-0041: ADR template gains optional first-screen summary, revisit trigger, and structured Confirmation

- **Status:** Accepted
- **Date:** 2026-06-28
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [ADR-0027](0027-adr-format-is-madr-aligned-but-lean.md) — the lean-vs-full thesis this *extends* (read the two together; not superseded); [RFC-0056](../rfc/0056-right-size-adr-template-decision-summary-revisit-confirmation.md) — the proposal this records; [RFC-0038](../rfc/0038-align-adr-template-with-madr.md) — the template decision ADR-0027 recorded, now amended by RFC-0056

## Decision summary

- **Decision:** We will add three optional, lean-compatible fields to the `new-adr` template — a first-screen `## Decision summary`, a structured `Revisit if:` trigger, and a `Mode / Signal / Owner` sub-structure for the existing Confirmation section.
- **Because:** they close the three highest-value retrieval/lifecycle gaps the track-1 critique named without crossing the lean-vs-full line ADR-0027 drew.
- **Applies to:** the `governance-extras` `new-adr` skill, template, evals, and how-to guide; forward-only, no existing ADR is converted.
- **Tradeoff accepted:** more template surface to read and maintain, against the empirical pull toward concise templates.
- **Revisit if:** adopters report the optional fields are noise (routinely deleted, never filled), or "optional" proves to mean "always skipped" on the heavy ADRs that need the summary.

## Context

ADR-0027 froze the ADR format as *MADR-aligned but lean* and deliberately excluded MADR-full (per-option pros/cons, options-first ordering). That thesis is sound and is not reopened. But the format it produced left three residual gaps that track 1 of the `new-adr` critique (PR #441) named and could not close without touching the template — so track 1 shipped the guidance and the format-*independent* evals and deferred these three to a track-2 RFC:

- The decision is not first on the screen. The template orders Context → Decision; on the repo's heavy ADRs (ADR-0031, ADR-0037) a multi-line title plus a paragraph of metadata push the actual decision below the fold.
- There is no named revisit trigger. An ADR records *why we got here* but not *when to question it*; this lived only in an ad-hoc `Neutral / to revisit` bullet. MADR 4.0 has no such field either.
- Confirmation is unstructured, so it reads as aspirational, and a decision with no confirmation simply omits the section — hiding the non-checkable residual.

RFC-0056 (Accepted, heavy, Approver-signed) decided to close all three as optional additions. This ADR records that decision and extends ADR-0027.

## Decision

We will extend the `new-adr` template with three fields, all on the lean side of the line ADR-0027 drew:

- A `## Decision summary` first-screen block (Decision / Because / Applies to / Tradeoff accepted / Revisit if), **optional-deletable**, included once an ADR is long enough that the decision isn't visible on the first screen and deleted on a short one.
- A named `Revisit if:` trigger whose **canonical home is Consequences** (always present, so it survives deletion of the optional summary), mirrored verbatim into the summary when that block is present, with `stable — no foreseeable trigger` as a valid explicit value.
- A `Mode / Signal / Owner` sub-structure for the optional Confirmation section, where `Mode` is one of `reviewer-checked | lint/CI | architecture fitness test | periodic audit | none` and an explicit `Mode: none` (with a reason) is preferred over silent deletion where a reader would expect a check.

This **extends** ADR-0027 — it adds lean-compatible fields on the same side of the line — and does **not** supersede it; ADR-0027's MADR-aligned-but-lean thesis stands unchanged. None of the three fields is mandatory, and none introduces per-option pros/cons or options-first ordering.

## Decision drivers

- **Close the deferred-but-high-value gaps** — these are the critique's top retrieval/lifecycle asks (the revisit trigger was called "the biggest missing ADR-specific field"), and three foreclosed track-1 evals can only be authored once the fields exist.
- **Stay strictly lean** — each field must source to a lean precedent (Y-statement for the summary, Nygard's revisit warning for the trigger, MADR 4.0's existing Confirmation for the sub-structure) and add no MADR-full ceremony.
- **Don't tax the short ADR** — the empirical finding is that conciseness wins on comprehension, so the fields must be optional and length/aging-keyed, never mandatory.
- **Preserve ADR-0027's thesis** — extend, don't reverse; the lean-vs-full line is not being moved.

## Consequences

**Positive:**
- Heavy ADRs put the decision on the first screen; short ADRs stay terse.
- A decision can name its own expiry condition, and Confirmation becomes a checkable claim with an honest `none` value.
- The three foreclosed track-1 usability evals are now authorable and authored.

**Negative:**
- More template surface to read and more skill prose to maintain.
- A hurried author can still skip the summary on a heavy ADR that needed it (mitigated by length-keyed skill guidance and the eval, which make the omission visible rather than silent).

**Revisit if:** adopters report the optional fields are noise (routinely deleted, never filled), or "optional" proves to mean "always skipped" on the heavy ADRs that need the summary.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** new ADRs scaffolded from the template carry a `## Decision summary` when long, a `Revisit if:` in Consequences, and a concrete-or-explicit-`none` Confirmation; the three behavioral evals in `evals/evals.json` assert the same. There is no mechanical ADR-section lint (ADR-0027 settled that conformance stays reviewer-checked; a lint remains separately RFC-gated).
- **Owner:** the `new-adr` skill maintainer.

## Alternatives considered

- **Do nothing** — keep ADR-0027's format unchanged. Rejected against the *close the deferred-but-high-value gaps* driver: the three gaps persist and the foreclosed evals stay un-wireable, leaving track 1 visibly half-finished.
- **Add the fields as mandatory** — required on every ADR. Rejected against *don't tax the short ADR* and *stay strictly lean*: five redundant lines on every short ADR is the exact ceremony the lean position and the conciseness evidence both argue against — the boundary case ADR-0027 was drawn to avoid.
- **Supersede ADR-0027** rather than extend it. Rejected: ADR-0027's thesis is unchanged, so superseding would misrepresent the relationship; these are lean-compatible additions on the same side of the line (the ADR-0037-extends-ADR-0034 precedent).

## References

- [RFC-0056](../rfc/0056-right-size-adr-template-decision-summary-revisit-confirmation.md) — the proposal this ADR records (D1–D5).
- [ADR-0027](0027-adr-format-is-madr-aligned-but-lean.md) — the lean-vs-full decision this extends.
- [RFC-0038](../rfc/0038-align-adr-template-with-madr.md) — the original MADR-alignment decision, amended by RFC-0056 (see its `## Errata`).
