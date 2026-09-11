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

## Boundary

- Includes `shaping-reviewer` first, then a survey of the reviewer and
  adjudication surfaces across the packs — `adversarial-reviewer`,
  `quality-engineer`, `security-reviewer`, `design-reviewer`, the
  experience-design and discovery reviewers, and `finding-adjudicator` — and
  whichever of them the survey shows would change behaviour.
- Excludes re-deriving the protocol. `new-spec`'s review step is where the eight
  responses ship, delivered by `acceptance-criteria-set-construction`; the
  criterion that used to define them is deferred to
  [the authoring protocol measured before shipping](spec-authoring-protocol-measured-before-shipping.md),
  which carries the definitions verbatim. This intent carries them from there
  and never restates them into a second home.
- Excludes any blocking, scoring or refusal behaviour on any surface, **except
  the determinacy grading shipped on 2026-09-11** by
  `acceptance-criteria-set-construction`: `adversarial-reviewer` caps a
  judgement finding at Concern and `finding-adjudicator` sustains one at
  advisory severity at most, on the test of whether the fix is fully determined.
  That exception is recorded rather than re-derived — this intent carries it and
  never restates it — and it narrows what may block rather than adding a new
  block, which is the direction this exclusion was written to guard.
- Excludes `new-spec`, which A6 delivers.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Does a reviewer surface need the response list at all, or only the
  no-relitigation rule? The responses are the author's move; a reviewer that
  enumerates them may be writing the author's answer for them.
- Is the settled-decision boundary a reviewer rule, a brief obligation, or both?
  Today it lives only in whatever the brief's author happens to write.
- Which of the pack reviewers have their own finding-response prose already, and
  would gain a second home rather than a first one?

## Source

- Mode: repo-origin
- Locator: docs/specs/acceptance-criteria-set-construction/spec.md
- Authority: repo-origin
