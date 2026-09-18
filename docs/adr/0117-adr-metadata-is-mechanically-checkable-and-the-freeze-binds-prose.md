# ADR-0117: ADR metadata is mechanically checkable, and the freeze binds prose, not metadata

- **Status:** Accepted
- **Date:** 2026-09-17
- **Areas:** governance, tooling
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0102 (the proposal this records); ADR-0027 (the deferred
  lint this discharges, recorded on that ADR's own Errata)

## Decision summary

- **Decision:** We will adopt a mechanically checkable ADR metadata block — bounded `Areas`, `Reversibility`, a bare-token `Status`, four supersession fields, and numbered `D1..Dn` constraints — and split acceptance's freeze so it binds an ADR's prose, not its metadata.
- **Because:** a claim records a judgement made at a moment and should stay fixed; a connection (a supersession discovered later, an area added later) is found after the fact and needs to stay writable, and one freeze rule cannot hold both without either falsifying history or blocking a correction.
- **Applies to:** every ADR's metadata block and its `## Errata` section, going forward and over the existing corpus alike — there is no grandfathered set and no format threshold.
- **Tradeoff accepted:** the tier boundary between what the shape lint checks and what it leaves as untouched prose is itself a design choice, and a fact drawn on the wrong side of it needs a new criterion, not a lint tweak, to move.
- **Revisit if:** a corpus regression needs bulk remediation before merging is possible again, the fifteen check classes prove too strict against a legitimate record shape they do not yet cover, or adopters report the T2/T3 tier boundary misclassifies a fact worth checking.

## Context

ADR-0027 adopted a MADR-4.0-aligned-but-lean ADR format and, in its own
`## Confirmation` section, recorded the gap this ADR closes: "There is **no
mechanical ADR-status lint** today … adding one is a separate, RFC-gated
convention and is deferred — until then, conformance is reviewer-checked."
That left every ADR's metadata — `Status`, supersession, the numbered
constraints a later record might cite — as convention-only prose: nothing
enforced its shape, and a correction discovered after acceptance (a
supersession found later, an area realized in hindsight) had nowhere licensed
to go under the old Status-only mutability rule, so records that needed one
improvised it.

RFC-0102 ("An ADR's metadata is checkable, and the freeze binds its prose")
was accepted 2026-09-17 to close that gap. It draws a line a program can act
on: a **claim** (Context, the Decision narrative, Consequences prose) records
what was believed and decided at a moment, so rewriting it later falsifies the
record rather than correcting it. A **connection** (a supersession, an area,
a status change) records how the decision sits in a graph that keeps growing,
so it is discovered after the fact by definition and freezing it alongside
the prose would make a real, later-discovered fact unrecordable. RFC-0102 §§
2–5 states the field set, the parse tiers, the supersession grammar, and the
four mutability zones this ADR adopts; § 6 adds the enforcing lint; and its
own Follow-on artifacts list names exactly this record: "An ADR recording this
format decision, authored in the new format, shipping with the lint as its
first fixture."

## Decision

We adopt RFC-0102's metadata block and its mutability split, and ship a shape
lint that enforces the metadata block. The split is stated in the authoring
surfaces and is not yet mechanically enforced: checking it needs a check on how
a record *changed*, which the shape lint — a check on how a record *reads right
now* — cannot perform. Rewriting `check-adr-immutability` to do that is
recorded as follow-on work.

- **D1:** A record's metadata is layered by what a program can check.
  `Status`, `Date`, `Areas`, `Reversibility`, and the four supersession fields
  (`Supersedes`, `Supersedes in part`, `Superseded by`, `Superseded in part`)
  are checked for value and shape. `Decision-makers`, `Consulted`, `Informed`,
  and `Related` are deliberately left unvalidated — human names and
  cross-artifact pointers have no checkable domain here. `D1..Dn`, `Decision
  drivers`, `Alternatives considered`, and `Confirmation`'s `Mode` / `Signal`
  / `Owner` are checked for presence and layout only, wording never; every
  other prose section, including `Context` and the `Decision` and
  `Consequences` narratives, is untouched.
- **D2:** Supersession is the one edge type this format enforces, because it
  is the only edge that changes whether a decision binds — every other
  cross-reference stays in the unchecked `Related:` field. It is always
  written as a mirrored pair on both records: whole-record via `Supersedes` /
  `Superseded by`, or partial via D-ID-scoped `Supersedes in part` /
  `Superseded in part`, so either record can be read alone.
- **D3:** Acceptance freezes a record's prose (every section except
  `## Errata`) and its `Attested` metadata (`Date`, `Decision-makers`,
  `Reversibility` — a judgement made at the time, so rewriting it falsifies
  rather than corrects). It leaves `Live` metadata writable after
  acceptance — `Status` (replaced in place, being a state rather than a
  list), the four supersession fields, and `Areas` (both append-only, keeping
  every entry already present) — and adds an `Append-only` `## Errata`
  section, whose entries may be added but never removed or rewritten, for
  corrections that clarify what a decision means without changing what was
  decided.
- **D4:** A shape lint mechanically enforces every checked and layout-checked
  fact from D1 over every ADR in the corpus, with no legacy set carved out and
  no format threshold — the corpus is migrated to the new field set rather
  than left partially exempt.

This delivery ships that lint blocking over the whole corpus from the outset,
rather than the advisory-then-blocking rollout RFC-0102 § 6 originally
specified; see Consequences for why, and Alternatives considered for the
rollout this narrows.

## Decision drivers

- **Checkability needs a stated boundary.** A line the lint does not check
  still looks checkable if left unlabeled, and RFC-0102 § 1 names the failure
  chain that follows: a check quietly claims to validate a fact it cannot, so
  it produces false positives, so someone turns it off. The four-tier split
  states the boundary instead of leaving it implicit.
- **A connection is discovered after the fact; a claim is not.** Freezing
  both alike either falsifies a rediscovered connection (by refusing to
  record it) or lets history rewrite itself (by allowing the claim to move).
  Splitting the freeze at prose-versus-metadata is what lets both properties
  hold at once.
- **Supersession is the one edge that changes whether a decision binds.**
  An unenforced graph in Markdown rots, and there is no service here keeping
  one consistent, so this is the one edge type worth a mirrored, checked
  pair; everything navigational stays in `Related:`.
- **A guarantee has to be enforced, not merely asserted.** Once the corpus
  was already migrated clean, an advisory phase over it would be a check that
  can never fail — this is the driver behind shipping the lint blocking from
  the outset rather than in two phases.

## Consequences

**Positive:**

- ADR metadata is now a checkable contract rather than convention-only prose.
  The fifteen check classes are the durable definition of "shape-conformant,"
  discharging the Confirmation gap ADR-0027 recorded and deferred.
- A supersession or area realized after acceptance is now recorded without
  touching frozen prose — the `Live` zone and `## Errata` close exactly the
  lifecycle hole the old Status-only rule left open, where a record had no
  legal place to put a correction and improvised one.
- The lint ships blocking over the whole corpus from the outset: the corpus
  had already been migrated to a clean pass — against every one of the
  fifteen check classes, including both mirror rules — before the lint
  shipped, so there is no separate advisory phase and no follow-on task to
  later flip a warn flag to block.

**Negative:**

- The tier boundary is a design choice, not a discovered fact. A fact
  classified untouched prose today may later prove worth checking, and
  promoting it needs a new criterion — RFC-0102 § 1 warns against blurring the
  layout-checked and untouched tiers for tidiness, because that is exactly how
  a lint starts judging prose and produces false positives.
- Because the lint ships blocking rather than advisory, there is no grace
  period: an undetected defect in a record that no check class covers reds a
  merge the moment it is found, rather than surfacing as advisory noise
  first, and the remedy is a record fix under time pressure rather than a
  scheduled cleanup.
- A record still carrying the legacy `Deciders` key has it renamed to
  `Decision-makers` with its value preserved exactly, so mixed frontmatter
  history persists across old- and new-format records — unchanged from
  ADR-0027's own `D4`.

**Revisit if:** a corpus regression needs bulk remediation before merging is
possible again, the fifteen check classes prove too strict against a
legitimate record shape they do not yet cover, or adopters report the T2/T3
tier boundary misclassifies a fact worth checking.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `.github/workflows/build-check.yml`'s `check-adr-shape` step
  invokes `lint-adr-shape.py docs/adr`, and the aggregator's `Require every
  gate` step fails the run unless that step succeeds — so enforcement cannot
  be dropped by an omitted step.
- **Owner:** eugenelim

## Alternatives considered

- **Keep the Status-only mutability rule as stated** — rejected: it cannot
  express a supersession that carries a machine-readable target and a
  constraint list, and it left a correction with nowhere legal to go, so
  records improvised one anyway (RFC-0102 § "Options considered").
- **Whole record mutable, with git history as the audit trail** — rejected by
  the `Attested` zone: rewriting who decided what and when, and how it was
  judged at the time, falsifies the record rather than correcting it.
- **Ship the lint advisory-then-blocking, per the rollout RFC-0102 § 6
  originally specified** — rejected: the corpus was already migrated to a
  clean pass before the lint shipped, so shipping the advisory phase would add
  a phase with nothing to be advisory about — an unenforced check
  masquerading as a safety net.

## References

- [RFC-0102](../rfc/0102-mechanically-checkable-adrs.md) §§ 2–5 — the field
  set, the parse tiers, the supersession grammar, and the mutability zones
  this ADR adopts; § 6 — the shape lint and the advisory-then-blocking
  rollout this ADR narrows to blocking-only; Follow-on artifacts — names this
  record by role.
- [ADR-0027](0027-adr-format-is-madr-aligned-but-lean.md) — deferred "There is
  **no mechanical ADR-status lint** today … adding one is a separate,
  RFC-gated convention"; this is that convention, discharged, and recorded on
  that ADR's own `## Errata` entry.
