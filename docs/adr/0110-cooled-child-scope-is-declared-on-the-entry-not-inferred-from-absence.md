# ADR-0110: A cooled child's parent scope is declared on its workspace entry, and an undeclared value fails closed rather than reading as "no parent"

- **Status:** Accepted
- **Date:** 2026-09-03
- **Renumbered:** issued as ADR-0106 and moved to ADR-0110 on 2026-09-12. Two records had been accepted under 0106 independently; the one that reached the default branch first keeps the ordinal. Only this record's identifier changed — its decision text is unaltered.
- **Decision-makers:** eugenelim
- **Related:** [RFC-0096](../rfc/0096-portable-delivery-artifact-lifecycle.md) §6 and §7 and its 2026-09-03 Errata (Wave 7b's mechanism half). This record supersedes in part the `status-projection-and-context-exclusion` spec's AC59, and is governed by the `workspace-routing-invariants` spec's § *Ask first* and § *Canonical findings*; both are named rather than linked, because `docs/CONVENTIONS.md` § *Cite upward, never downward* holds that ADRs do not link to specs.

## Decision summary

- **Decision:** for a cooled spec, `source.parent` on its `workspace.toml` entry answers one of three ways, not two. A declared value **resolving to a brief membership** attributes the child to that brief. A declared **empty** value attributes nothing. Anything else — an **absent key, or a declared value that resolves to no brief membership** — means the child's scope is unknown: the run names the entry in a `cooled_child_scope_unknown` finding and refuses every **local** `kind = "brief"` dependency until a resolving value or an empty one is declared. A `cross-repo` brief dependency is decided by its four-field receipt, which is a precedence that already ran before this refusal and which this decision leaves in place.
- **Because:** absence carried two incompatible meanings — "this spec has no parent" and "nobody recorded whether it has one" — and the projection cannot tell them apart without opening a body that cooling forbids. Reading absence as the first meaning is what let a cooled child's brief silently release its dependants.
- **Applies to:** every cooled `kind = "spec"` entry read by `workspace-status` reconciliation, and every **local** `kind = "brief"` dependency evaluated against it. A `cross-repo` brief dependency is out of scope: its receipt decides it first.
- **Tradeoff accepted:** the fail-closed floor is repository-wide, because an unattributed cooled child could belong to any brief and no narrower attribution is sound. Its cost is bounded by being escapable in one token, and measured at zero refusals on this checkout.
- **Revisit if:** (1) `close-work` gains the ability to stamp the parent link at closeout, making a hand-declared value unnecessary; (2) a read-free brief→child index appears, allowing exact attribution instead of a floor; or (3) the refusal is observed to fire on work whose entry cannot be corrected.

## Context

RFC-0096 §7 removes a cooled artifact's body from ordinary orientation: "status
and default orientation must not load its contents." Wave 6 built the child-state
set on that constraint. A brief's children are collected from each spec
membership, and for a cooled child the only readable source of its parent is
`source.parent` on the workspace entry, because the `- **Brief:**` preamble in
the artifact body may not be opened.

Wave 6 closed the attributed half: a cooled child that declares `source.parent`
puts its brief into a fail-closed set, and every `kind = "brief"` dependency on
that brief refuses. It deliberately left the undeclared half open, recorded as
the follow-on `cooling-brief-child-scope`, and pinned the gap with a test whose
assertion message reads "the residual is closed — update AC59 and remove the
Follow-ons row", so that closing it would have to be deliberate.

Two conservative repairs were tried in Wave 6 and withdrawn — attributing every
undeclared cooled child to every brief in the workspace, then to every brief in
the initiative. Both refused brief dependencies whenever any ordinary parentless
spec cooled. Measured then at 81 of 92 specs in `ini-002`, and re-measured on
2026-09-03 at 99 of 115 workspace spec entries (86%), the trigger was the common
case rather than the exception. RFC-0096's 2026-09-03 Errata states the same
proportion as 99 of 114 *work* entries: 114 is the `work.shipped` subset of the
115 spec memberships measured here, the difference being the single
`work.active` entry. Both figures are correct at their own denominator.

## What changed since Wave 6 withdrew those repairs

The withdrawn repairs and this decision differ in one respect that the earlier
measurement could not express: **absence was the only representable state**, so a
maintainer had no way to clear a refusal and no way to learn which entry caused
it. Three facts measured on 2026-09-03 (recorded in the closing spec's
`notes/probes.md`) change that:

1. A parsed workspace entry retains `source.parent`'s **raw** value. A declared
   `"none"` yields the string `none`; an absent key yields `None`. The
   distinction is already available and simply unused.
2. `contracts/jsonschema/workspace-entry.schema.json` already admits
   `parent = "none"`, so expressing a positive "this spec has no parent" needs no
   schema change and no contract-version move.
3. `docs/lifecycle/` holds no records, so nothing has cooled. The floor costs
   zero refusals today, and its worst case is bounded by the 5 live
   `kind = "brief"` dependencies.

So the refusal is now **escapable and attributed** rather than unconditional and
anonymous, which is what the earlier cost measurement was really objecting to.

## The decision, stated as the three answers

| `source.parent` on a cooled spec entry | Reading | Consequence |
| --- | --- | --- |
| Declared, resolving to a `kind = "brief"` membership | This child belongs to that brief | That brief's `kind = "brief"` dependencies refuse — Wave 6's shipped behaviour, unchanged |
| Declared empty (`none`, or any value the shipped normalizer folds to nothing) | This spec has no parent | Nothing is attributed; dependants dispatch |
| **Absent** | Nobody recorded whether it has a parent | `cooled_child_scope_unknown` names the entry; every local `kind = "brief"` dependency refuses until a resolving or empty value is declared |
| **Declared, resolving to no brief membership** | Something was recorded, but it does not identify a brief this workspace knows | Same as absent. A typo and a brief that has left the register are indistinguishable read-free, and both leave the scope unestablished |

**What counts as a brief membership.** Any workspace entry whose `kind` is
`brief`, in whichever collection it is registered — a `brief_queue` collection,
`[backlog].open`, or a retained legacy bare-string entry. Resolution is by entry
kind, never by collection name. Both alternatives were measured and rejected:
keying on the collection admitted a mis-collected `kind = "spec"` entry sitting
in a brief queue, which resolved a declared value that names no brief at all;
and it missed a brief legitimately registered in `[backlog].open`, which
refused a correctly declared child with **no repair available** — declaring a
resolving path was already done, and declaring empty would be false. A refusal
with no valid escape is the one property this decision cannot have, because it
is what licenses the floor at all.

The legacy bare-string case is included on narrower grounds. A repair does exist
there: `legacy_entry` already fires on such an entry and its next action is to
register a canonical one, which resolves the declaration as a side effect. It is
included because reporting a correct declaration as unestablished is a
misdiagnosis regardless of whether some other repair happens to clear it, and
because the maintainer who must act is the brief's owner, not the child's.

Reading a legacy entry here decides attribution only. It dispatches nothing,
which is the line the routing contract draws around legacy compatibility.

Only the first two answers establish scope. The unknown class is therefore
absence *or* unresolvability, not absence alone — a distinction that matters
because a one-character case change is the cheapest way to reach it.

Resolving a declared value against a brief **membership** rather than trusting the
string is part of the decision, not an implementation detail: measured on
2026-09-03, a one-character case change (`Brief-1.md` for `brief-1.md`) or a
dangling brief path left the dependant dispatchable with an empty findings list —
reproducing the exact defect being closed. Membership resolution reads
`workspace.toml` only and opens no body, so it costs nothing against the
read-free constraint.

## What this supersedes in AC59, and what still stands

`status-projection-and-context-exclusion` AC59's final paragraph states, in full:

> The fail-closed set is exactly the briefs named by a cooled child's
> `source.parent`. A cooled spec that declares no `source.parent` marks nothing:
> with such a spec cooled, an unrelated healthy brief in the same initiative
> keeps its dependant in `canonical.ready` and carries no finding. Attributing
> those conservatively would refuse every brief dependency whenever any ordinary
> spec cooled — 81 of 92 specs in this repository's main initiative declare no
> `source.parent` — so the gap is left open and recorded as
> `cooling-brief-child-scope` rather than closed at that cost.

**Sentences one and two are superseded.** The fail-closed set is no longer
exactly the briefs a cooled child names, and a cooled spec that establishes no
scope no longer marks nothing: every `kind = "brief"` dependency refuses until
its entry declares a resolving or empty value.

**Sentence three is not superseded — it is discharged.** Its cost measurement
still holds, and this record does not dispute it. What changed is that the
refusal is now escapable in one token and names the entry to repair, so the
"at that cost" the sentence declines is no longer the cost being paid. The
sentence's conclusion, that the gap stays open, is what this record ends.

**The rest of AC59 stands unchanged**, including its first half — a cooled child
that declares `source.parent` fails its parent brief's dependency closed — and
its prohibition on fabricating a cooled child's state from its collection.
AC13, AC14, AC20, AC55, AC56 and AC57 are untouched: this record does not
license reading a cooled body, does not block a non-brief dependency on a cooled
child, and does not widen `invalid_receipt`, whose single-emitter property
remains a shipped test oracle.

Recorded as an ADR because `docs/CONVENTIONS.md` § *Superseding a frozen document*
licenses exactly one edit to a frozen spec — a `Status`-field parenthetical — and
requires it to point at an ADR rather than at the spec or RFC that implemented
the change. RFC-0096's errata are Approver-signed and carry the wave scoping, but
an erratum is not one of the two licensed pointer shapes.

## Alternatives considered

**Read each brief's own `## Spec map` to build a reverse index.** A brief is
never cooled, so reading *it* would be a read-free route to its children and
would attribute exactly, with no floor at all. Rejected on measurement: 2 of 15
briefs carry no `## Spec map` section, and of the 13 that do, 3 have parseable
rows. The formats disagree — backticked slugs, bare slugs, the prose "None.",
and an empty table row. A brief-coverage lint does read that section and does
enforce a Shipped brief's children being non-empty and all shipped, so the
section is not unchecked — but it checks the brief's own prose, not the
workspace entries this projection reads.

Measured at base `3e0e58150`: of 16 non-template briefs, 2 carry no `## Spec
map` section at all, and of the 14 that do, only 5 have parseable rows — the
other 9 hold an empty table, a prose "None.", or rows in a shape no parser
reads. Parsing this section here would therefore find nothing to attribute for
11 of 16 briefs and would fail silently into under-attribution, which is the
same defect class being closed. Where both sides are non-empty they agree, so
the objection is coverage, not conflict. The lint's existence neither supports
nor weakens the rejection.

**Add a field to `workspace-entry.schema.json` recording that the parent link was
resolved.** Rejected as unnecessary once the raw value proved to carry the
distinction, and because it would widen a published contract to express something
an existing field already expresses.

**Keep absence permissive and record the residual again.** Rejected because the
residual has now been carried through three waves, and the measurement that
justified carrying it — the cost of a blanket refusal — no longer applies to a
refusal that names its entry and lifts on one token.

## Consequences

- A maintainer who cools an artifact must declare `source.parent` on its entry —
  a brief path, or `none`. Until `close-work` can stamp it at closeout, that is a
  hand-authored step, and the finding names the entry that needs it.
- A declaration made *after* the artifact cooled is never validated against the
  body, because `provenance_mismatch` is suppressed for a cooled entry. **Every**
  declared answer is therefore trusted rather than verified in that window, not
  only the empty one. Two consequences follow, and both are accepted: a declared
  empty value on a child that does have a parent releases every dependant; and a
  declared value naming a *different* registered brief attributes the child
  there, so the true parent is left out of the fail-closed set and its dependants
  release with no finding at all. What the decision closes is the case nobody
  asserted anything about. What it does not close is a wrong assertion, which is
  why the closing spec records the closeout-time writer as its follow-on and why
  that follow-on covers misattribution as well as omission.
- `cooled_child_scope_unknown` joins the public refusal contract, so a consumer
  must preserve its code, repository-relative path, dispatchability, and next
  action. Admitting it was reviewed under `workspace-routing-invariants`
  § *Ask first* on 2026-09-03.
