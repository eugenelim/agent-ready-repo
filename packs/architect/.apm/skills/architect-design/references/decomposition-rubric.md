# Decomposition rubric — which parts earn their own architecture document

A subsystem's design doc describes its own elements in an element catalogue.
As those elements grow, some of them start behaving like systems in their
own right — with their own decisions, their own boundaries, their own
reviewers — and the question this rubric answers is when that shift is real
rather than a container for growing prose: given a subsystem, which of its
parts earn a document of their own, which stay rows in this one's element
catalogue, and which belong above this document entirely?

## The six criteria

| ID | Criterion |
| --- | --- |
| `D1` | A live architectural decision of its own. Mandatory, and also the recursion's stopping rule. |
| `D2` | Crosses a trust, identity, data-ownership, or deployment boundary that differs from the parent's. |
| `D3` | An independent release or failure unit. |
| `D4` | A different system shape or workload class, so a different overlay applies. |
| `D5` | Different owners or reviewers. |
| `D6` | Its own quality scenarios, rather than inherited ones. |

## The qualifying rule

A child earns its own document when it meets `D1` plus at least one other
criterion. `D1` alone names a decision worth writing down, not a subsystem
worth splitting out; one of `D2` through `D6` is what makes that decision
belong to a document the parent shouldn't carry.

The rule decides that the decision deserves a document. It does not decide
that this document is the one to hang it under, so meeting it settles less
than it appears to; the dispositions below settle the rest.

## The three dispositions

A candidate lands in one of three places, not two. Decide which before
writing anything.

- **A document of its own.** It meets `D1` plus at least one other
  criterion, and the decision is this subsystem's to make.
- **A row in this document's element catalogue.** `D1` is unmet, so there is
  no decision to home — only detail to record.
- **Above this document.** It meets `D1` plus at least one other criterion,
  and the decision is not this subsystem's to make. Route it upward.

The third is the one authors miss, because the qualifying rule is satisfied
and a child document then looks like the answer. `D5` is usually what
decides it: when the owners or reviewers who would have to accept the
decision sit above this document, a child of this document is the wrong
home for it, and so is a row. A document whose reviewer has no standing to
accept its largest block is misfiled by construction.

The clearest case is a subsystem document that carries the changes it is
asking of a ratified parent. Each change is a live decision of its own, each
crosses a boundary the parent owns, and the parent's reviewer — not this
document's — is the only one who can accept it. Leaving the block inline
does more than misfile it: ratifying this document then accepts changes to a
ratified parent by implication, which is the opposite of what writing those
changes down was for.

**How to record an upward route.** Take the block out of this document and
raise it through the parent's own review, as a change to the parent. Leave
behind a link naming what was raised and where it is being decided, so a
reader can follow it and so ratifying this document accepts nothing on the
parent's behalf. An upward route is neither a deletion nor a deferral: the
decision still has to be made, by whoever has standing to make it.

## The stopping rule

`D1` is mandatory for a second reason: it is also the recursion's stopping
rule. Apply this rubric to every child, then to every grandchild, and so on.
The descent terminates when no remaining child has a live architectural
decision of its own — at that depth there is nothing left to decide, only
detail left to record, and detail belongs in the parent's element catalogue.

## The three refusals

Reject a split for any of these reasons standing alone. None of them is a
criterion above, and each one dresses up as a decomposition without being
one.

- **`D1` is unmet.** No live decision means no document, no matter how many
  of `D2` through `D6` a child also satisfies. Those five describe why a
  decision, once made, deserves its own home — they don't manufacture the
  decision in the first place.
- **A split that gives one contract two homes.** Describing the same
  interface once in the parent and again in the child duplicates it instead
  of decomposing it. The two copies drift the first time either one changes,
  and the reader can no longer tell which one is current.
- **A child that is only large.** Length is a symptom, not a decision. A
  large element with no live decision of its own is a candidate for a
  shorter description, not a separate document.

## Size alone never justifies a split

Size alone never justifies a split. A page count, a line count, or a section
count gives an author a number to write to, and an author who owes a number
will cut a boundary that satisfies it rather than one the system actually
has. The boundary invented to get under a threshold is worse architecture
than the large document it replaced: it is arbitrary where the document was
merely long, and an arbitrary boundary still has to be lived with by whoever
inherits it. If a document is large without any child meeting `D1` plus one
other criterion, the right response is to tighten the prose, not to invent a
child.

## The architecture-set index — what a parent keeps

Once a subsystem's children earn documents of their own, the parent doesn't
disappear — it becomes the index for the set. A parent retains:

- the scope table;
- the structural model, with the children as named elements;
- the contracts between children;
- the cross-child invariants that no single child owns; and
- the links to each child document.

The parent does not restate child internals. Restating them is the main
fuel of the oversized single document this rubric exists to prevent: every
detail copied into the parent is a detail that will drift from its child the
first time either one is revised, and the size this rubric just refused to
gate on comes back in through this door instead.
