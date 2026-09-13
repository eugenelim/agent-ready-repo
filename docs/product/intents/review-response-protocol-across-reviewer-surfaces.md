# Review-response protocol across reviewer surfaces

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-review-economics — [Work-loop review economics](work-loop-review-economics.md)

## Outcome

- **Steerable input:** Carry the review-response protocol that
  [`docs/specs/acceptance-criteria-set-construction/`](../../specs/acceptance-criteria-set-construction/spec.md)
  ships into `new-spec` out to the other surfaces that produce or receive review
  findings — the `shaping-reviewer` subagent first, then the reviewer and
  adjudication mechanisms across the packs.
- **Lagging outcome:** A sustained finding is answered with the response that
  fits it, and the answer is recorded with its reason, rather than repaired by
  default because repair is the only move the surface names.
- **Guardrail:** No surface gains authority to block on the protocol. Naming the
  available responses is guidance to an author; it never becomes a gate, a
  score, or a refusal. Blocking on a derived review signal is the
  consequence-bound blocking already measured and killed in
  [work-loop review economics](work-loop-review-economics.md).

## Opportunity

A6 established that the eight responses to a sustained finding — repair, narrow
the claim to what its check reaches, cut the item, dismiss with the reason
recorded and re-present, repair the generator rather than the instance, route to
an existing owner, bound out of scope with a named follow-on, and accept with
the reason it is proportionate — are a protocol an author needs stated, because
a surface that names no alternative leaves repair the default by omission. Two
of A6's own criteria were cut, one was narrowed, and one finding was bounded and
deferred, only because the responses were enumerated.

That protocol lands in `new-spec`, which is the authoring side. The receiving
side is unaddressed. `shaping-reviewer` is the first surface to carry it: it
produces the findings a spec author answers, and it has no statement of what a
legitimate answer is, so a finding it sustains reads as an instruction to edit.

A second, distinct obligation belongs on the reviewer side rather than the
author side. **A reviewer must not relitigate a decision the brief records as
settled.** A late finding against a real pre-existing defect is legitimate and
useful; re-opening an owner decision is neither, and the two must be separated
so the author can refuse one without dismissing the other.

## Second carve-out, 2026-09-10 — grounding probes on the upstream shaping surfaces

The same shape, one stage earlier. `new-spec` runs a discovery grounding pass
over its resolved destinations before it writes a spec body, seeded by the
surfaces the work will touch. The surfaces *upstream* of a spec — an intent, a
delivery brief, a discovery decision record — have no such pass, and they are
where a direction is chosen rather than validated.

The evidence is the same two finds that motivated the `new-spec` pass. An
accepted decision record already named `grounding.toml` as a file not to create,
and a Shipped spec already owned how an adopter's guidance is identified. Both
were reachable from a path search on day one. Both surfaced only after a spec had
been authored, approved and reviewed three times against a design they
contradicted. A brief that had been grounded would have arrived carrying them.

- **Includes** firing the probes at brief and intent authoring, seeded by
  whatever destinations that stage can resolve, and reporting rather than
  gating.
- **Excludes** re-deriving the probes. `new-spec` owns the explorer and its
  calibration; this carries it and never restates it.
- **Excludes** `new-spec` itself, which delivers its own pass.
- **Open question, and the reason this is not obvious:** an intent may resolve no
  destinations at all, which is the difference between this and the `new-spec`
  case. If the seed set is empty the probes have nothing to run on, and the
  honest answer may be that the upstream stage grounds against a *topic* rather
  than a path — a different mechanism, not this one carried further. Settle that
  before building.

## Observed 2026-09-11 — cold dispatch widens a reviewer's area, and that is the cost as well as the value

Five rounds were dispatched the way `work-loop` prescribes — spec path, diff
range, mode, nothing else — after eleven rounds had been dispatched with
hand-built briefs carrying target lists, ranked priorities and the recorded
owner decisions.

**The value is not in dispute.** The first cold round found a pack version a
peer had already released, which no warm round could reach because no warm brief
had named `origin/main` as a surface. Later rounds reached the delivery brief,
the release surface, a subsystem architecture page, the corpus index, the
`/now/` projection, `workspace.toml` and `--help` output — all surfaces the
briefs had fenced off.

**The cost is area sprawl, and it is real.** A cold reviewer treats the whole
diff as its subject, so findings arrive spread across every surface the diff
touches rather than concentrated on the artifact under review. Three
consequences showed up repeatedly:

- **Refutation rates rose sharply** — one per warm round against seven, two,
  three, six and an expected similar count across the five cold ones. Each
  refutation is an adjudication entry rather than a repair, so the reviewer's
  breadth is paid for at the adjudicator.
- **The same finding recurs across rounds on different grounds.** Follow-on
  registration was refuted in one round on the convention's selective-registration
  rule and raised again two rounds later on the different ground that one intent
  receives a non-waivable Boundary's deferral. Both readings are defensible; a
  reviewer with no memory of the earlier verdict cannot know one was taken.
- **Findings land on surfaces no task owns**, which is useful when the surface
  should have an owner and noise when it belongs to another delivery. Two
  rounds raised edits to an intent owned by a different spec's plan.

**What this suggests for the reviewer surfaces.** A cold reviewer needs no brief,
but the *adjudicator* needs the prior verdicts — otherwise a refuted finding
costs a full round again each time it recurs. The asymmetry is the design point:
the reviewer stays stateless and the adjudication record accumulates. Whether an
adjudicator should be handed the previous rounds' refutations, and what that does
to its independence, is the question this intent should settle before carrying
the protocol to the other surfaces.

## Changed 2026-09-13 — the set grew to ten, ordered cut-first, and work-loop went first

Three changes to this intent's subject, on owner authority recorded in
[`docs/specs/finding-response-receptacle/notes/owner-decisions.md`](../../specs/finding-response-receptacle/notes/owner-decisions.md).

**The set is no longer eight.** Two answers were added: `drop-the-claim`, for an
assertion nothing is obliged by, and `demote-the-claim`, for an obligation that is
real but whose only check is that a sentence exists, which leaves the contract for
working material and gains a content pin. The gap they fill is structural — every
prior answer edits the artifact, moves ownership, or holds, so a review round
could only add or hold and never let a contract shrink. That is the mechanism
behind rounds that run long without converging: a finding against unnecessary
prose could only be answered by writing more careful prose.

**The set is an ordered ladder, not a menu.** Four axes — cut, route, fix, hold —
walked until one applies, then stopped. Cut leads because the repository already
governs code changes that way: cut before adding, take the first sufficient option
and stop. The order also pays for itself, because asking whether a claim needs to
exist is cheap while tracing a check's reach or locating a generator is not, and
spending that on a claim about to be deleted is the waste.

**Every answer walks its surfaces before it is taken, and the direction differs.**
Cut walks backwards, asking what referenced the thing that no longer exists — it
reaches furthest, because removing a node orphans the tasks, tests, design prose,
durable-output rows and pins that pointed at it. Route walks outwards to confirm
the named owner covers the whole claim, then back to remove what still states it
locally, or routing creates the second home for one rule the repository forbids.
Fix walks sideways across the other instances, the companions that describe them,
and anything that pins those. Hold walks forwards, because a dismissal or an
acceptance the next round cannot see produces exactly the recurrence this intent
already records.

It is a walk rather than a flat search, for two reasons this work produced. A
companion usually paraphrases, so it shares no string with the repair and no text
search reaches it. And each change opens its own frontier — a narrowed criterion
moves its design prose, which changes what a task asserts, which may sit under a
pin — so one pass closes nothing. The walk terminates on an empty frontier.

The walk also feeds back into the ladder: a claim living on many surfaces is
evidence for repairing its generator, or for dropping it, rather than for
repairing the instance a reviewer happened to cite.

**Work-loop's DECIDE shipped first, not `shaping-reviewer`.** This intent's
Boundary names `shaping-reviewer` as the first surface; it was not. The receptacle
work went to `review-verdict.v1` and the work-loop DECIDE step because that is
where a disposition record already existed to extend. The sequencing deviation is
recorded rather than reframed after the fact.

`shaping-reviewer` went next, and it was not a copy of this work. The section
below records what it took.

## Changed 2026-09-13 — the shaping surfaces carry the ladder by pointer, not by copy

**Decided by:** eugenelim, scope owner. Two of this intent's own unresolved
questions were settled to make this change, and are removed from that list below.

**A reviewer surface gets the settled-decision rule and not the response list.**
The question this intent carried — whether a reviewer needs the responses at all
— is answered no. The responses are the author's move, and a reviewer that
enumerates them writes the author's answer for it. `shaping-reviewer` gains one
rule instead: where the supplied artifact records a decision as settled, do not
raise a finding that reopens it; raise what that record cannot answer. A
pre-existing defect stays in scope however late it is found, and keeping the two
apart is what lets an author refuse a reopened decision without dismissing a real
defect from the same round. This narrows what a reviewer may raise rather than
adding anything it may block on. It is scoped to `delivery-brief` and `spec`
mode; `intent` mode's conditions are mechanical and cannot reopen a choice.

**The settled-decision boundary is a reviewer rule.** The intent's second open
question offered reviewer, brief obligation, or both. Both would have put one
rule in two homes, and a brief obligation alone leaves it to whatever each
brief's author happens to write, which is the gap this intent recorded. It lives
on the reviewer.

**The ladder is not restated upstream.** Its one home stays work-loop's DECIDE
step. Each of the three shaping surfaces gains a short section that points there
and adds only what the pointer cannot carry: what contract and working material
mean for that artifact, which is where `demote-the-claim` moves an assertion.

- **An intent's deciding sections** are `Outcome`, `Boundary`, `Owner`,
  `Projection` and `Source`; its recording sections are `Opportunity`,
  `Unresolved questions` and `Assumptions`. Demotion moves an assertion out of
  `Outcome` or `Boundary`, and the destination follows what the assertion was
  doing: a settled ground for the outcome or the boundary goes to `Opportunity`,
  and a matter the assertion decided without the authority to decide it goes to
  `Unresolved questions`.
- **A brief's deciding sections** are the field set the Ready gate reads; its
  recording sections are every other section. Demotion moves an assertion into a
  section the gate does not read — `Rabbit holes` for a design trap, `Design
  artifacts` for provenance that only informed the brief. `Ready gaps` is not a
  destination, because the brief drops it on leaving `Draft`, so demoting into it
  is deletion with a delay.

**The labels are deliberately not the spec's tiers.** An earlier draft called
these groups contract and working material, borrowing the vocabulary a spec
template uses. Review sustained that as a defect twice over. In prose it implied
a finding against the second group is advisory, which is false upstream: a
missing riskiest assumption blocks `Accepted`, and delivery-brief review blocks
`Ready` on checks reaching outside the Ready field set. Operationally it was
worse — `finding-adjudicator` caps a finding at advisory severity when every
cited surface is working material, so the borrowed label would have graded down
findings that block. The surfaces now use local labels that nothing reads to
grade a finding.
- **A spec's split is already stated** by `new-spec`'s bundled `assets/spec.md`,
  which is its single owner. That surface gains the pointer and nothing else.

**What demotion costs is not restated upstream.** An earlier draft claimed
demotion upstream needs no new pin, on the reasoning that both destinations sit
inside the artifact the review already binds to. Review sustained that as a
contradiction: DECIDE defines `demote-the-claim` as moving an obligation to
working material *with* a content pin, and requires the reason to record the pin
that catches its removal. Guidance that claims to point at DECIDE cannot
redefine one of its answers in passing. The claim was dropped rather than
argued, and each surface now defers to DECIDE for the cost.

Whether DECIDE's pin requirement can be satisfied at all on an artifact with no
machine anywhere is a real question, and it is registered rather than settled
here.

**The cut axis carries most findings here.** An intent has almost no machine
anywhere, so nearly every finding against one is a finding against prose, and
`drop-the-claim` comes before rewording. Answering a finding against unnecessary
prose with more careful prose is the mechanism behind rounds that run long
without converging.

**Nothing here may block.** Naming the answers is a criterion this repository has
deferred, so the guidance ships under a content pin and carries no acceptance
criterion; adding one would re-promote a deferred criterion. The guardrail is
enforced structurally rather than by assertion: the vocabulary is absent from
every section that decides a gate outcome, and the existing gate sentences on all
three surfaces are pinned unchanged.

## Boundary

- Includes `shaping-reviewer` first, then a survey of the reviewer and
  adjudication surfaces across the packs — `adversarial-reviewer`,
  `quality-engineer`, `security-reviewer`, `design-reviewer`, the
  experience-design and discovery reviewers, and `finding-adjudicator` — and
  whichever of them the survey shows would change behaviour.
- **Includes shipping the protocol into `new-spec`'s review step, which no
  longer arrives from elsewhere.** `acceptance-criteria-set-construction` was
  expected to deliver it and did not: on close, 2026-09-11, three of the eight
  responses appeared nowhere in the skill, its criteria were already retired,
  and the task was cut with the rest of the unbuilt work. The definitions are
  carried verbatim in
  [the authoring protocol measured before shipping](spec-authoring-protocol-measured-before-shipping.md);
  this intent takes them from there and never restates them into a second home.
  Whether the authoring side ships before or with the reviewing surfaces is this
  intent's sequencing call, not a dependency on a slice that has closed.
- Excludes any blocking, scoring or refusal behaviour on any surface, **except
  the determinacy grading shipped on 2026-09-11** by
  `acceptance-criteria-set-construction`: `adversarial-reviewer` caps a
  judgement finding at Concern and `finding-adjudicator` sustains one at
  advisory severity at most, on the test of whether the fix is fully determined.
  That exception is recorded rather than re-derived — this intent carries it and
  never restates it — and it narrows what may block rather than adding a new
  block, which is the direction this exclusion was written to guard.
- Excludes `new-spec`'s own checkers, its acceptance-criteria step and its
  templates, which `acceptance-criteria-set-construction` shipped. What is *not*
  excluded is its review step, per the bullet above.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Which of the pack reviewers have their own finding-response prose already, and
  would gain a second home rather than a first one?

## Source

- Mode: repo-origin
- Locator: docs/specs/acceptance-criteria-set-construction/spec.md
- Authority: repo-origin
