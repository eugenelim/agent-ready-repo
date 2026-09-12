# Decomposition proposal for AC-0009

**Recorded 2026-09-11, cold review round 3.** AC-0016 obliges an independently
shippable cluster to become a decomposition proposal rather than a compound
criterion. This is that proposal. It is a proposal and not an executed split:
authoring it is the obligation AC-0016 states, and the pair is at `Draft` /
`Drafting`, so an executed split needs no further sign-off if the owner directs
one.

## Why the criterion is compound

AC-0009 is 399 words, the largest in the set, and carries **thirteen separately
remediable predicates**. The shape owner's split test is the one that breaks:
`assets/spec.md` says a criterion is more than one "when its parts have separate
failure modes with separate remedies", and stays one only if the predicate "is
checkable as written at every member rather than expanding into a different
check per member".

It expands. The plan already has to assert the three plan-reading members by
name and then assert *no* plan-side operation for the remaining members — a
different check per member, which is the E4 split condition stated literally.

Two consequences are already live:

- **One checkbox over thirteen predicates.** At ship the `- [x]` invariant
  cannot express that twelve hold and one does not, so the criterion has no
  partial state.
- **Its own propagation obligation cannot name what moved.** AC-0009 defines the
  propagation member; a reword of any of its thirteen predicates reports as
  "AC-0009 changed", which the shipped rule 9 cannot resolve further. The
  over-report residue the rule already states is worse here than anywhere else
  in the set.

## The predicates, and the proposed disposition of each

| Predicate | Disposition |
| --- | --- |
| The pass runs over the spec-and-plan pair as one set | **stays** — this is AC-0009's subject and the reason it exists |
| The member set is named | **stays** — naming the set is the same predicate as having one |
| Consistency reads the body's own prose against the criteria | **splits** — its own failure mode: a body claim contradicting a criterion |
| Consistency tests the body for narrated delivery history | **splits** — remedied by moving prose to the changelog |
| Consistency tests the body for a count beside its set | **splits** — remedied by replacing a numeral with its set |
| Consistency re-reads each criterion against the shape rules | **splits** — remedied by re-reading against `assets/spec.md` |
| A pinned name the pack does not define is unusable | **grafts onto** the shape re-read: same failure, same remedy |
| Three members carry a stated plan-side question | **stays** — a property of the member set |
| Propagation cites the rubric's sibling check rather than restating it | **splits** — remedied by a citation |
| Propagation re-reads a touched criterion's test and entry | **splits** — remedied by updating an assertion |
| Propagation re-reads every sentence citing a criterion | **grafts onto** the scope predicate: same remedy, opposite direction |
| Propagation completes in the same round | **splits** — remedied by timing, not by content |
| Residual freshness re-tests each recorded residual | **splits** — its own failure mode and remedy |

Eight split candidates, three that stay with the subject, two that graft onto a
sibling split.

## What the split costs

Eight new criteria take fresh append-only identifiers — AC-0041 onward — and
AC-0009 narrows to the subject, the member set and the plan-side-question
property. Nothing is renumbered and nothing is retired, so no `## Retired
identifiers` entry arises.

The propagation is not small, and it is the reason this is a proposal rather
than a completed edit:

- the Testing Strategy group that names AC-0009 gains eight entries;
- T1's assertion block splits from ten assertions with five constraint riders
  into one per criterion, which is the point;
- every sentence citing AC-0009 is re-read against whichever successor now
  carries the predicate it meant — AC-0018, AC-0026 and AC-0040 all cite it;
- the shipped sweep prose in `SKILL.md` names the members, so T1's span-scoped
  assertion has to iterate the new enumeration.

## The honest argument against splitting

The seven sweep members are a *set* an author runs as one pass. Splitting the
sub-predicates of consistency and propagation into peer criteria makes the
member set harder to read as a set, and the set is the thing the procedure
teaches. A reader scanning for "what does the sweep do" would find eleven
criteria where they now find one.

That argument favours keeping the member enumeration in AC-0009 and splitting
only the sub-predicates that carry their own remedy — which is what the table
above proposes, rather than a flat eleven-way split.

## Owner decision needed

Execute the split as proposed, narrow it to fewer sub-predicates, or record an
exemption with its reason. All three are available at `Draft`; none is available
once approval re-pins the pair.
