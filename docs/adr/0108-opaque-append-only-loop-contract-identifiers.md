# ADR-0108: Identity for loop-contract items — opaque and append-only, not positional

- **Status:** Accepted
- **Date:** 2026-09-10
- **Decision-makers:** eugenelim
- **Related:** [`loop-contract.md`](../architecture/loop-contract.md) § 3 (the standard as stated); [identifier comparison matrix](../product/research/item-id-management-comparison-matrix.md) (the evidence and the rejected alternatives)

## Decision summary

- **Decision:** an acceptance criterion and a verification item each carry an opaque, append-only identifier scoped to its own spec directory — assigned once, never renumbered on insertion or reorder, never reused after removal, with removals recorded in the artifact's retired list. A verification item's identifier is independent of the criterion and the task it serves. Cross-spec citation uses the existing `spec:<slug>/` marker.
- **Because:** a positional number makes identity a function of position, so an insertion silently invalidates every reference to everything after it.
- **Applies to:** loop-contract artifacts authored from this decision onward. Forward-only; the existing corpus is not renumbered, on the same basis ADR numbering itself was introduced.
- **Tradeoff accepted:** permanent gaps in the sequence, and a retired list this repository maintains itself because nothing off-the-shelf enforces no-reuse for inline Markdown.
- **Revisit if:** worktree coordination becomes reliable enough that a repository-global registry is safe. The other trigger — a tool that enforces no-reuse for inline-Markdown items — fired on 2026-09-10 and was answered by building one here rather than adopting one; the decision was re-read against it and stands unchanged.

## Decision drivers

1. A reference written today still resolves after an insertion elsewhere.
2. The scheme is checkable inside a git repository without adopting a requirements-management tool.
3. It needs no counter shared across concurrent worktrees.
4. Adoption is forward-only; 442 existing spec directories are not migrated.

## Context

Identity and position were the same thing in our criteria, written `AC1`…`AC23`
and cited positionally from the testing strategy and the plan. During one spec's
review, three insertions forced three renumberings, and the resulting stale
cross-references were raised as defects in rounds 2, 9 and 15 — three of the
thirty sustained findings on that spec.

Two facts from this repository bear on the scope of the fix rather than its
shape. **ADR ordinals 0055 and 0106 each have two files**, under a convention
whose own rule is that numbers are sequential and never reused; a max-plus-one
helper cannot see an unpushed sibling. And two peer sessions collided on the
released pack version twice in a single day. A repository-global identifier
counter is a shared mutable resource across concurrent worktrees, and this
repository has demonstrated twice that it cannot coordinate one. That is why the
scope is the spec directory, which is also the unit that freezes together.

The external evidence is unanimous on stability and silent on format.
ISO/IEC/IEEE 29148 clause 5.2.8.1 requires that an assigned identifier is never
changed and never reused, while explicitly leaving hierarchical encoding
optional. IBM DOORS ships both an absolute number and a positional heading
number and resolves links against the absolute one, leaving permanent gaps
rather than reusing a deleted number — a product that implements both schemes
and had to choose. Two independent requirements-tool vendors describe positional
numbering as unsuitable where immutable numbers are needed. Three
test-management tools keep a test's identifier independent of the requirement it
verifies, which is the argument against deriving a verification identifier from
its task.

## Consequences

Gaps in the sequence are permanent and expected; a reader who notices `AC-0009`
missing is seeing the convention work. The retired list is machinery this
repository owns, because no surveyed tool enforces no-reuse-after-deletion for
items held inline in Markdown. Cross-references become stable enough to cite
from a plan, a durable-output map or a review finding without a renumbering
invalidating them.

The cost is that a criterion's identifier stops encoding its reading order, so a
reader cannot infer sequence from the number. That is the same trade DOORS
makes, and the ordering a reader wants is the document order, which is unchanged.

**The honest limit: no empirical study compares opaque with positional schemes
on defect or staleness rates.** The consensus is practitioner- and
standards-derived, and no datable post-mortem of renumbering breaking
traceability was found in the open literature. This decision rests on convergent
practice across independent vendors and standards, plus one measured failure in
this repository — good ground, not measured ground.

**Revisit if:** worktree coordination becomes reliable enough that a
repository-global registry is safe. The other trigger — a tool that enforces
no-reuse for inline-Markdown items — fired on 2026-09-10 and was answered by
building one here rather than adopting one; the decision was re-read against it
and stands unchanged.

## Alternatives considered

- **Keep positional numbering.** Rejected: it is the defect. Judged against
  driver 1, an insertion invalidates every later reference by construction.
- **Semantic identifiers** (`AUTH-LOGIN-03`). Rejected against driver 1: the
  prefix goes stale the moment scope moves, and renaming an identifier is
  delete-plus-reissue, which orphans every existing reference.
- **Per-file items** via Doorstop or StrictDoc. Rejected against driver 2: both
  deliver the property, and both require every criterion to become its own file,
  abandoning the single-file `spec.md` the whole corpus uses. The cost is not
  proportionate to the defect.
- **Version-in-identifier** (`req~name~1`, OpenFastTrace). Rejected against
  driver 2: its benefit — a version bump deliberately invalidating downstream
  coverage so it must be re-confirmed — presumes a coverage-tag ecosystem this
  repository does not have.
- **A repository-global counter.** Rejected against driver 3, on the two
  observed collisions recorded in Context.

## Confirmation

- **Mode:** lint/CI.
- **Signal:** the contract-item alignment check in the `new-spec` skill's own
  `scripts/`, which decides every item identified, identifiers unique, none
  reused against the artifact's retired list, and every criterion-class reference
  resolving.
- **Owner:** the spec author, with the reviewer at the shaping gate covering what
  the check cannot reach.

**Amended 2026-09-10, before this record was ever released.** It previously said
no lint enforced the decision, which was true when written and false by the time
it shipped: the check and this record land in the same change. The decision text
above is unchanged — only the confirmation state moved, which is what this
section is for.

**What the check still does not reach.** It decides identity and resolution, not
meaning: a criterion labelled correctly and worded wrongly passes, and a
reference that resolves to the wrong criterion passes. Those remain
reviewer-checked.

## References

- [Identifier comparison matrix](../product/research/item-id-management-comparison-matrix.md)
  — full evidence, scheme comparison, and the four named gaps in the research.
- [`loop-contract.md`](../architecture/loop-contract.md) § 3 — the normative
  statement of the standard.
- [`CONVENTIONS.md`](../CONVENTIONS.md) § 2 — ADR numbering, whose own
  never-reuse rule this decision generalises to items inside an artifact.
