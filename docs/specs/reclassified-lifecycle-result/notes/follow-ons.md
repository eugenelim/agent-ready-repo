# Follow-ons this delivery carries forward

Two items: one inherited rather than discovered, one caused by this delivery.
Neither is part of its accepted contract. This document is the artifact of the
canonical `[backlog].open` entry
`docs/specs/reclassified-lifecycle-result/notes/follow-ons.md`
(`kind = "defect"`), which is its register — RFC-0096 names the slice at
`docs/rfc/0096-portable-delivery-artifact-lifecycle.md:380` but the queue
carried no entry for it, so this file gives that slug a home.

Status and ownership live in the register, not here. This file is history.

## `rfc0096-wave7c-pruning` — the entry-removal precondition

**Owner:** RFC-0096 Wave 7c (the pruning slice).

Reassigned here from `lifecycle-record-entry-removal-fact`, which was registered
against `docs/specs/dependency-scoped-completion-receipts/notes/follow-ons.md`
and assigned to Wave 7c by the 2026-09-03 Errata as a *schema* follow-on. It is
not a schema follow-on. The reassignment and its reasoning are recorded in
[`docs/product/design/rfc0096-wave7c-lifecycle-record-decisions.md`](../../../product/design/rfc0096-wave7c-lifecycle-record-decisions.md).

### What was refuted

The original follow-on said an orphaned entry "silently strands every dependant
the receipt exists to protect, with every criterion green". Measured, the two
states diverge and nothing is silent:

| State | Result |
| --- | --- |
| Correct prune — entry removed, file removed | The dependant resolves through its completion receipt, carrying no finding code |
| Orphaned entry — entry kept, file removed | The dependant carries `unsatisfied_dependency`; the entry itself carries `missing_artifact` |

The dependant fails closed, so the receipt's protection is not lost silently.
That evidence is snapshot-scoped and shape-scoped — it exercises a canonical
`spec` entry in an active initiative on the `status` surface, and does not pin
aliases, paused or closed initiatives, non-spec kinds, or the repair surfaces.

### What survives, and why it stays open

Detection after the fact is not a pruning session proving its own precondition.
Nothing makes the two removals atomic: `cooling.py` is the only lifecycle-record
writer and has no prune path at all, and its single `os.unlink` is temp-file
cleanup inside the atomic write.

A record field would not supply atomicity. It would store a claim the pruning
session makes about itself, which is weaker than the invariant needed. The
requirement is an atomic prune, or a mandatory post-mutation invariant, defined
and verified by the pruning slice.

**Refuting the stated harm did not close the item.** It removed the wrong
repair — a `delivery-lifecycle-record.schema.json` field — and left the real one
unbuilt. The 2026-09-03 Errata's framing of this as one of Wave 7c's "two schema
follow-ons" is the part that no longer holds; the obligation does.

### What this delivery did and did not settle

`docs/specs/reclassified-lifecycle-result/` closed the *other* follow-on the
same Errata assigned to Wave 7c, `lifecycle-record-reclassified-gap`, by adding
`Reclassified` to the record contract. It deliberately added no entry-removal
field, and its `Never do` list forbids deleting or relocating a lifecycle record
or an artifact. So nothing here was made worse, and nothing here was made
easier: the pruning slice starts where the decision record leaves it.

## `cooling-scope-closure-pin-statements` — two statements the digest grant does not cover

**Owner:** `cooling-scope-closure`, restated by its own owner.

**Caused by:** this delivery, and `cooling-brief-child-scope-closure` (RFC-0096
Wave 7b). Raised by that delivery's spec review, confirmed here against the file
on 2026-09-08.

AC23 of `docs/specs/cooling-scope-closure/spec.md` grants a digest table, and
this delivery moved four of its six rows. Two *statements* in that spec go false
when any pinned file moves, and neither is the digest row:

| Statement | Where | Status |
| --- | --- | --- |
| "Every pinned file is byte-unchanged" | AC23's title, `:281` | Title falsified, body intact |
| "two frozen spec directories are depended on and neither may change" | Durable Outputs, `:62` | Falsified |

The distinction on the first decides the repair. AC23's *body* reads "The
SHA-256 of each file below equals the value beside it" — a digest-agreement
test, which this delivery satisfies by moving both recorded sites. Only the
*title* asserts immutability. The repair is to retitle, not to re-scope a
criterion that still holds.

The second is falsified by this delivery alone. The two directories are Wave 5's
`thirty-day-cooling-and-retirement` and Wave 6's
`status-projection-and-context-exclusion`. This delivery changes **both files**
of the Wave 5 directory — `spec.md` and `plan.md` each took the ADR-0105
supersession parenthetical — so "neither may change" is already false before
Wave 7b moves the other.

### Why it is recorded rather than repaired here

`cooling-scope-closure` is `Status: Implementing`, so its prose is editable and
this is not a frozen-document problem. It is a scope problem. This delivery's
AC15 grants the digest *values* in that table and nothing else; editing a live
sibling delivery's criterion title and its Durable Outputs row is wider than the
grant, and neither delivery could make the repair complete alone — each
falsifies a different half. Both sessions independently declined to widen.

Recorded here rather than in Wave 7b's tree because this delivery lands first,
so the cause and its record land together.
