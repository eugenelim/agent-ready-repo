# ADR-0027: ADR format is MADR-aligned but lean, not full MADR

- **Status:** Accepted
- **Date:** 2026-06-21
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0038](../rfc/0038-align-adr-template-with-madr.md); [ADR-0001](0001-adopt-agents-md-and-doc-hierarchy.md) — adopted the ADR format without recording its rationale; this ADR records it but does not supersede 0001

## Context

ADR-0001 adopted ADRs into the doc hierarchy but never recorded *why* the ADR
template has the shape it does. The `new-adr` skill was authored against a
Nygard base with MADR ~3.x frontmatter and has since drifted from
[MADR 4.0](https://adr.github.io/madr/) (released 2024-09-17). A review of the
shipped skill — judged the way an adopter who installs `governance-extras`
receives it, not against this repo's internal conventions — found one genuine
lifecycle defect and several smaller gaps:

- A proposal declined at sign-off has no status, so it gets deleted, destroying
  the "we considered and declined X" record ADRs exist to preserve.
- Frontmatter is MADR 3.x (`Deciders` only; no consulted/informed split).
- MADR 4.0's optional `Decision drivers` and `Confirmation` sections are absent.
- The post-acceptance lifecycle discipline (bidirectional supersession,
  backfilling) lived only in this repo's how-to guide, which adopters never get.

The choice in front of us was *how far to track MADR*.

## Decision

We adopt a Nygard-based, MADR-4.0-aligned-but-lean ADR format.

That format **includes**, from MADR 4.0:

- the `Rejected` status;
- the `Decision-makers`/`Consulted`/`Informed` frontmatter;
- the optional `Decision drivers` and `Confirmation` sections.

And it **excludes**, from MADR-full:

- per-option pros/cons tables;
- options-first ordering — the decision stays answer-first in the body.

Concretely this is the template and skill change specified in RFC-0038
(findings F1–F6 and the title half of F8). The optional sections are deletable
per-ADR; the only non-optional changes are the status enum and the
`Deciders` → `Decision-makers` field rename. Migration is forward-only —
existing ADRs keep `Deciders` and are not rewritten, because ADRs are immutable.

## Decision drivers

- **Close the lifecycle hole** — a declined proposal must have a home
  (`Rejected`) so the record survives. This is the load-bearing driver, and the
  main reason to track MADR over plain Nygard at all.
- **Adopt only MADR's value-adds, not its ceremony** — the consulted/informed
  split and the Confirmation section close real gaps; per-option pros/cons
  tables are ceremony the light process doesn't want. This is the driver that
  separates lean from full.
- **Stay lean** — the ADR process is deliberately light; ceremony per ADR loses.
- **Keep answer-first** — the repo's house style (RFC-0014) leads with the
  decision; options-first ordering fights it.
- **Adopter self-containment** — the shipped skill must stand alone; discipline
  can't live only in a repo-owned guide adopters don't receive.
- **Minimal migration cost** — forward-only, no conversion of existing records.

## Consequences

**Positive:**
- Declined decisions are now preserved, not lost.
- The format tracks a current, recognised standard (MADR 4.0).
- Adopters get the full lifecycle discipline in the skill they install.
- The format choice is now on the record (this ADR), so a future maintainer
  weighing MADR-full has the rationale instead of re-deriving it.

**Negative:**
- One breaking template-field rename (`Deciders` → `Decision-makers`) leaves
  mixed frontmatter across existing vs. new ADRs.
- `Decision drivers` and `Confirmation` add surface a hurried author may skip;
  they are optional precisely so they don't become ceremony.

**Neutral / to revisit:**
- If adopters report that the optional sections rot or that answer-first
  ordering hurts, revisit toward (or away from) MADR-full in a new ADR.

## Confirmation

The `new-adr` skill and its `assets/adr.md` template are the enforcement
surface — every new ADR is scaffolded from them, and the skill pushes back on
hand-wavy sections. `docs/CONVENTIONS.md § 2` and the how-to guide document the
status vocabulary and lifecycle. There is **no mechanical ADR-status lint**
today (the existing `lint-spec-status` covers spec metadata, not ADRs); adding
one is a separate, RFC-gated convention and is deferred — until then,
conformance is reviewer-checked.

## Alternatives considered

- **Full MADR** (per-option pros/cons, mandatory Decision Drivers, options-first
  "Decision Outcome: chose X because Y"). Rejected against the *adopt only MADR's
  value-adds, not its ceremony*, *stay lean*, and *keep answer-first* drivers: it
  is the heaviest option, its per-option pros/cons are ceremony, and its
  options-first ordering fights the repo's answer-first house style.
- **Plain Nygard / do nothing** (keep the current shape). Rejected against the
  *close the lifecycle hole* driver: the declined-proposal record stays lost and
  the skill keeps drifting from the standard it claims kinship with.

## References

- [RFC-0038](../rfc/0038-align-adr-template-with-madr.md) — the proposal this ADR records.
- [MADR 4.0](https://adr.github.io/madr/) — the reference conventions.
