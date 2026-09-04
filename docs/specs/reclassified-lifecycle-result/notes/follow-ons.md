# Follow-ons this delivery carries forward

One item, inherited rather than discovered. It is not part of this delivery's
accepted contract. This document is the artifact of the canonical
`[backlog].open` entry
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
