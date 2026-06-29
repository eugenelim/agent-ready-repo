# RFC-0038: Align the ADR template with MADR conventions

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-21
- **Date closed:** 2026-06-21
- **Related:** [ADR-0027](../adr/0027-adr-format-is-madr-aligned-but-lean.md), [ADR-0001](../adr/0001-adopt-agents-md-and-doc-hierarchy.md) (adopted the ADR format), `docs/CONVENTIONS.md` § 2

## The ask

- **Recommendation (BLUF):** Bring the `new-adr` skill and its ADR template
  up to current [MADR 4.0](https://adr.github.io/madr/) conventions — add a
  `Rejected` status, the decision-roles frontmatter split
  (`Decision-makers`/`Consulted`/`Informed`), and optional `Decision drivers`
  and `Confirmation` sections; keep the template deliberately lean (no
  MADR-full per-option pros/cons, decision stays first).
- **Why now (SCQA):** The `new-adr` skill was authored against MADR ~3.x and
  has drifted from MADR 4.0. A review of the shipped skill (judged as adopters
  install it) found a genuine lifecycle hole — a declined proposal has no
  status and gets deleted, destroying the record — plus stale frontmatter and
  two missing optional sections. Nothing recorded *why* the format was chosen,
  so there's no register that weighed MADR against the current shape.
- **Decision requested:** Adopt the MADR-aligned-but-lean changes (F1–F6,
  F8-title); this entails *not* adopting MADR-full (per-option pros/cons,
  options-first ordering) and keeping the decision answer-first, per the repo's
  answer-first house style (RFC-0014). · Recommended · closes a real lifecycle
  hole and tracks the current standard while staying lean · default if no
  objection.

## Problem & goals

The shipped `new-adr` skill follows the classic Nygard shape with MADR ~3.x
frontmatter. Against MADR 4.0 it has drifted:

- **No `Rejected` status.** The enum is `Proposed → Accepted → (Deprecated |
  Superseded)`. A proposal declined at sign-off has nowhere to go, so it gets
  deleted — destroying exactly the "we considered and declined X" record ADRs
  exist to keep. This is the one true defect, repo-independent.
- **Frontmatter is MADR 3.x.** Only `Deciders` exists; MADR 4.0 renamed it
  `decision-makers` and added `consulted`/`informed` (a RACI-style split).
- **Two MADR sections are absent.** `Decision drivers` (the criteria options
  are judged against) and `Confirmation` (how conformance is verified).
- **Title is index-opaque** and **lifecycle discipline lives only in the
  repo's how-to guide**, which adopters don't receive — so the shipped skill
  is thinner than it reads.

**Goals.** Close the lifecycle hole; track MADR 4.0 where it adds value; make
the shipped skill self-contained for adopters.

**Non-goals.** Adopting MADR-full (per-option pros/cons, Decision Drivers as a
mandatory section, options-first ordering) — this is finding F7 (keep options
*after* the decision), left as-is by design. Rewriting existing ADRs. Adding a
mechanical ADR-status lint (a separate convention, separately RFC-gated). The
non-title parts of finding F8 (ambiguous `Date` semantics, parallel-branch
numbering collisions) are also out of scope here.

## Proposal

Applied to `packs/governance-extras/.apm/skills/new-adr/` (`SKILL.md` +
`assets/adr.md`), the repo how-to guide, and `docs/CONVENTIONS.md § 2`:

- **F1 — `Rejected` status.** Add to the enum; a declined proposal is marked
  `Rejected` and kept. (CONVENTIONS § 2 status-values line updated to match —
  this is the RFC-gated part.)
- **F2 — MADR 4.0 frontmatter.** `Deciders` → `Decision-makers`; add optional
  `Consulted` and `Informed`. *Breaking for the template only* — new ADRs use
  the new field; existing ADRs keep `Deciders` and are not rewritten
  (immutable). No tooling reads the field — a grep for `Deciders` consumers
  across `tools/`, `packages/`, and lint came back clean — so there is no data
  migration, only the forward-only template change.
- **F3 — lift lifecycle discipline into the shipped `SKILL.md`** (bidirectional
  supersession, `Deprecated`-vs-`Superseded`, backfilling), self-contained with
  no internal-governance citations (per `AGENTS.local.md`).
- **F4 / F5 — optional `Decision drivers` and `Confirmation` sections**,
  included when they earn their place, deleted otherwise (MADR marks both
  optional).
- **F6 — `Deprecated` vs `Superseded` distinction** stated in the template,
  skill, guide, and CONVENTIONS § 2.
- **F8 (title) — H1 names problem + solution**, keeping the `ADR-NNNN` ordinal.

The decision stays the first body section (answer-first); alternatives stay
after it. Migration: forward-only; no conversion of existing records.

## Options considered

Axis: *how far to track MADR*, which exhausts the space from "ignore it" to
"adopt it wholesale".

| Option | What | Trade-off |
| --- | --- | --- |
| Do nothing | Keep Nygard + MADR 3.x | Lifecycle hole persists (declined proposals lost); silent drift from the standard the skill claims kinship with |
| **MADR-aligned-but-lean** ★ | F1–F6, F8-title; keep answer-first; sections optional | Closes the hole, tracks MADR 4.0's value-adds, stays lean; one breaking template-field rename |
| MADR-full | Also per-option pros/cons, mandatory Decision Drivers, options-first ordering | Heaviest; fights the repo's answer-first house style (RFC-0014); more ceremony per ADR than the lean process wants |

Prior art: MADR 4.0.0 (2024-09-17) is the reference; the `Confirmation` section
and the `decision-makers`/`consulted`/`informed` split are its signature 4.x
additions. Nygard is the base both share.

## Risks & what would make this wrong

- **Pre-mortem — mixed frontmatter confuses readers.** New ADRs say
  `Decision-makers`, old ones say `Deciders`. Mitigation: this is normal
  template evolution; immutability forbids rewriting old records, and both
  field names are self-explanatory.
- **Key assumption (falsifiable):** adopters want MADR-shaped ADRs. Falsified if
  adopters file requests for strict-Nygard scaffolding or routinely strip the
  MADR sections — revisit toward plain Nygard in a follow-on ADR. Until that
  signal, the optional sections are deletable, so the only forced change is the
  status enum and the field rename.
- **Drawback:** one breaking template-field rename. Accepted because the value
  (RACI split) outweighs a one-time field-name change with no data migration.

## Evidence & prior art

- **External:** [MADR 4.0](https://adr.github.io/madr/) — status enum
  (`proposed | rejected | accepted | deprecated | superseded`), the
  `decision-makers`/`consulted`/`informed` frontmatter, and the optional
  `Decision Drivers` / `Confirmation` sections. Fetched and confirmed.
- **Repo precedent:** ADR-0001 adopted the doc hierarchy but recorded no ADR
  *format* rationale (this RFC + ADR-0027 close that gap); RFC-0014 establishes
  the answer-first house style that grounds keeping the decision first.

## Follow-on artifacts

- ADR-0027: ADR format is MADR-aligned-but-lean (records this decision;
  dogfoods the new template).
- Convention change: `docs/CONVENTIONS.md § 2` status-values line.
- Pack change: `governance-extras` `new-adr` skill + template, bumped to
  `0.2.0`.

## Errata

This RFC is Accepted: the body above is preserved as the original decision
record. Corrections and extensions found after acceptance are appended here,
Approver-signed.

- **2026-06-28 (Approver: eugenelim) — the template decision is extended by
  RFC-0056.** This RFC set the ADR template as MADR-aligned-but-lean (recorded in
  ADR-0027). [RFC-0056](0056-right-size-adr-template-decision-summary-revisit-confirmation.md)
  extends that template — staying on the same lean side of the line — with three
  optional fields: a first-screen `## Decision summary`, a structured `Revisit if:`
  trigger in Consequences, and a `Mode / Signal / Owner` sub-structure for
  Confirmation. The decision recorded in this RFC's body stands unchanged; the
  extension is recorded in [ADR-0041](../adr/0041-adr-template-optional-summary-revisit-confirmation.md),
  which extends (does not supersede) ADR-0027.
