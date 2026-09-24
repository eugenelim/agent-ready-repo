# Plan: tracker projection profile table

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
  (the table, its four columns and its `What v1 ships` statement);
  `docs/adr/0125-managed-unit-floor-and-projected-range.md` (D1 through D4a).
  Named deviation: the table has no machine-readable form today, so the
  classification is new structure rather than a reformat.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

Classify first, reconcile second. The clause check cannot be written against
the table as it stands: a probe over the shipped file found 19 distinct
free-text object tokens across four columns, including `sub-issue` beside
`sub-issues` and a name carrying bold markup, and nothing anywhere records
whether a Linear sub-issue is schedulable. A runner reading those cells would
be exercising judgement and calling it a check.

So each cell gains one value from a closed set, each object token is given one
spelling, and only then does the runner resolve rows against ADR-0125. The
reconciliation the brief's audit found — below-floor rows naming managed
objects, and a canonical column with no cross-repository brief rung — falls
out of the classification rather than being a separate hand pass.

## Constraints

- **ADR-0125** D1 through D4a decide every row. This slice applies them and
  does not reopen the floor.
- **ADR-0033 D2** makes `Level` an open set, so a rung with no row is named
  rather than derived.
- The table is a reference other packs read by hand today. The classification
  is additive: a human reader still gets the object name in the same cell.

## Construction tests

- A coverage check: every cell parses to a value from the closed set.
- A consistency check: one spelling and one classification per object token.
- A clause runner over the table, plus a fixture table carrying a below-floor
  `managed` that it must reject.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Classified table | T1 | coverage and consistency checks clean |
| Reconciled rows and the Jira Software column | T2 | clause runner clean |
| `product-engineering` changelog entry | T2 | the pack leads its own entry |

## Design (LLD)

### Design decisions

- **The classification is a closed set of three.** `managed`, `trace` and
  `none` are the distinctions ADR-0125 D4 actually draws. A fourth value would
  be a distinction no clause reads.
- **The classification lives in the cell, not in a sidecar.** A separate
  machine-readable file would drift from the table a person reads, and the
  drift would be invisible because nothing compares them.

### Data & schema

Each cell carries its object name and one classification. A row maps one
canonical rung across the provider columns.

### Interfaces & contracts

The table is the interface. Its consumers read it by hand today and by runner
after this slice.

### Component / module decomposition

One reference file and one runner, both in `packs/product-engineering/`.

### State & control flow

The runner is invoked over the file and exits zero or non-zero. No state.

### Behavior & rules

A cell with no classification fails. A token with two spellings fails. A
below-floor `managed` fails.

### Failure, edge cases & resilience

A column added by a later slice with unclassified cells fails the coverage
check rather than being skipped, which is what keeps the check honest as the
table grows.

### Quality attributes (NFRs)

The clause runner is the pass/fail bar and reads no free text.

### Dependencies & integration

No new dependency.

## Tasks

### T1: every cell is classified and every object token has one spelling

**Depends on:** none

**Tests:**
- Every cell parses to a value from the closed set. Verifies *an explicit
  classification from the closed set*.
- Each object token has one spelling and one classification table-wide.
  Verifies *exactly one spelling and one classification*.

**Approach:**
- Classification precedes reconciliation, because the clause check has nothing
  to read until the cells carry values.

**Done when:** both checks are clean over the whole table.

**Touches:** packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md

### T2: every row resolves against ADR-0125 from its classifications

**Depends on:** T1

**Tests:**
- The runner resolves each row against D1 through D4a and exits non-zero on a
  below-floor `managed`. Verifies *every row resolves ... by reading those
  classifications* and *no table cell maps a rung below the floor*.
- A cross-repository delivery brief resolves to a canonical rung. Verifies
  *the table carries a canonical rung for a cross-repository delivery brief*.
- The Jira Software column is present and classified. Verifies *the table
  carries a Jira Software column*.
- The runner reads the table file rather than a fixed column list. Verifies
  *a column a later slice adds is covered*.

**Done when:** the runner exits clean over the table and non-zero over a
fixture table carrying a below-floor `managed`, and
`packs/product-engineering/CHANGELOG.md` leads an entry.

**Touches:** packs/product-engineering/**, packs/product-engineering/CHANGELOG.md

## Rollout

Both tasks land together or not at all: a classified table with no runner has
nothing enforcing it, and a runner with no classifications has nothing to read.

## Risks

- **A later column ships unclassified.** The coverage check fails on it rather
  than skipping it.
- **The classification and the prose name disagree.** Mitigated by both living
  in the same cell, so a change touches one place.

## Changelog

- 2026-09-24 — plan drafted.
